from fastapi import APIRouter, HTTPException, Depends, Form
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordRequestForm
import secrets
import hashlib

from app.db.init_db import db
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.core.auth_deps import get_current_user
from app.core.config import settings
from app.core.email import send_email

router = APIRouter(prefix="/auth", tags=["auth"])


# -----------------------------
# Helpers
# -----------------------------
def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def _gen_6digit_code() -> str:
    # 000000 - 999999
    return f"{secrets.randbelow(1_000_000):06d}"


# -----------------------------
# REGISTER (crea usuario + envía código)
# -----------------------------
@router.post("/register", response_model=TokenResponse)
async def register(data: RegisterRequest):
    existing = await db.auth_users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un usuario con ese correo")

    now = datetime.utcnow()  # ✅ naive UTC (Mongo friendly)
    hashed = hash_password(data.password)

    # Código de verificación email
    code = _gen_6digit_code()
    code_hash = _sha256(code)
    exp = datetime.utcnow() + timedelta(minutes=10)  # ✅ naive UTC

    user_doc = {
        "name": data.name,
        "email": data.email,
        "hashed_password": hashed,

        # email verification
        "is_email_verified": False,
        "status": "PENDING_VERIFY",
        "email_verify_code_hash": code_hash,
        "email_verify_expires_at": exp,

        # meta
        "created_at": now,

        # password reset
        "reset_token_hash": None,
        "reset_token_exp": None,
    }

    result = await db.auth_users.insert_one(user_doc)
    user_id = str(result.inserted_id)

    # Enviar email (código)
    try:
        send_email(
            to=data.email,
            subject="Verificación de correo | AdopPets",
            body=f"Tu código de verificación es: {code}\nEste código expira en 10 minutos."
        )
    except Exception:
        # Si el correo falla, igual creamos el usuario (pero quedará en pending)
        # Puedes decidir si aquí prefieres borrar el user y lanzar error.
        pass

    # OJO: puedes devolver token, pero el monolito NO debería dejar loguear hasta verificar.
    token = create_access_token(sub=user_id, email=data.email)
    return {"token": token, "user_id": user_id}


# -----------------------------
# VERIFY EMAIL
# -----------------------------
@router.post("/verify-email")
async def verify_email(email: str = Form(...), code: str = Form(...)):
    record = await db.email_verifications.find_one({
        "email": email,
        "code": code,
        "used": False
    })

    if not record:
        raise HTTPException(status_code=400, detail="Código inválido")

    if record["expires_at"] < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Código expirado")

    # ✅ MARCAR USUARIO COMO VERIFICADO
    await db.auth_users.update_one(
        {"email": email},
        {
            "$set": {
                "is_email_verified": True,
                "status": "ACTIVE"
            }
        }
    )

    # ✅ Marcar código como usado
    await db.email_verifications.update_one(
        {"_id": record["_id"]},
        {"$set": {"used": True}}
    )

    return {"message": "Email verificado correctamente"}


# -----------------------------
# RESEND VERIFICATION
# -----------------------------
@router.post("/resend-verification")
async def resend_verification(email: str = Form(...)):
    user = await db.auth_users.find_one({"email": email})
    if not user:
        # no revelar si existe o no
        return {"message": "Si el correo existe, se reenviará un código."}

    if user.get("is_email_verified") is True:
        return {"message": "Correo ya verificado"}

    code = _gen_6digit_code()
    code_hash = _sha256(code)
    exp = datetime.utcnow() + timedelta(minutes=10)

    await db.auth_users.update_one(
        {"_id": user["_id"]},
        {"$set": {"email_verify_code_hash": code_hash, "email_verify_expires_at": exp}}
    )

    try:
        send_email(
            to=email,
            subject="Reenvío de código | AdopPets",
            body=f"Tu nuevo código de verificación es: {code}\nEste código expira en 10 minutos."
        )
    except Exception:
        pass

    return {"message": "Si el correo existe, se reenviará un código."}


# -----------------------------
# LOGIN (bloquear si no verificó)
# -----------------------------
@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    user = await db.auth_users.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if not verify_password(data.password, user.get("hashed_password", "")):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # ✅ Importante: no permitir login si no verificó
    if user.get("is_email_verified") is not True:
        raise HTTPException(status_code=403, detail="Debes verificar tu correo antes de iniciar sesión")

    user_id = str(user["_id"])
    token = create_access_token(sub=user_id, email=data.email)
    return {"token": token, "user_id": user_id}


# -----------------------------
# OAuth2 Password Flow (Swagger)
# -----------------------------
@router.post("/token")
async def token(form_data: OAuth2PasswordRequestForm = Depends()):
    email = form_data.username
    password = form_data.password

    user = await db.auth_users.find_one({"email": email})
    if not user or not verify_password(password, user.get("hashed_password", "")):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if user.get("is_email_verified") is not True:
        raise HTTPException(status_code=403, detail="Debes verificar tu correo antes de iniciar sesión")

    user_id = str(user["_id"])
    access_token = create_access_token(sub=user_id, email=email)
    return {"access_token": access_token, "token_type": "bearer"}


# -----------------------------
# ME
# -----------------------------
@router.get("/me")
async def me(payload: dict = Depends(get_current_user)):
    return {"sub": payload.get("sub"), "email": payload.get("email")}


# -----------------------------
# Forgot password (envía token por email)
# -----------------------------
@router.post("/forgot-password")
async def forgot_password(email: str = Form(...)):
    user = await db.auth_users.find_one({"email": email})

    # No revelar si el correo existe o no (buena práctica)
    if not user:
        return {"message": "Si el correo existe, se enviará un enlace de recuperación."}

    raw_token = secrets.token_urlsafe(32)
    token_hash = _sha256(raw_token)
    exp = datetime.utcnow() + timedelta(minutes=15)

    await db.auth_users.update_one(
        {"_id": user["_id"]},
        {"$set": {"reset_token_hash": token_hash, "reset_token_exp": exp}}
    )

    # ✅ LINK CORRECTO AL MONOLITO
    reset_link = (
        f"{settings.FRONTEND_BASE_URL}"
        f"/password-reset/reset?token={raw_token}&email={email}"
    )

    send_email(
        to=email,
        subject="Recuperación de contraseña | AdopPet",
        body=(
            "Solicitaste restablecer tu contraseña.\n\n"
            f"Usa este enlace (válido por 15 minutos):\n{reset_link}\n\n"
            "Si no fuiste tú, ignora este mensaje."
        )
    )

    return {"message": "Si el correo existe, se enviará un enlace de recuperación."}


# -----------------------------
# Reset password (consume token)
# -----------------------------
@router.post("/reset-password")
async def reset_password(email: str = Form(...), token: str = Form(...), new_password: str = Form(...)):
    user = await db.auth_users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=400, detail="Token inválido")

    token_hash = _sha256(token)
    saved_hash = user.get("reset_token_hash")
    exp = user.get("reset_token_exp")

    if not saved_hash or saved_hash != token_hash:
        raise HTTPException(status_code=400, detail="Token inválido")

    if not exp or exp < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expirado")

    new_hashed = hash_password(new_password)

    await db.auth_users.update_one(
        {"_id": user["_id"]},
        {"$set": {"hashed_password": new_hashed, "reset_token_hash": None, "reset_token_exp": None}}
    )

    return {"message": "Contraseña actualizada correctamente"}
