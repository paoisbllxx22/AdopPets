#services/users.py
from app.db.init_db import db
from app.core.security import hash_password, verify_password, create_access_token
from bson import ObjectId
import secrets

# -----------------------------------------
# Crear usuario
# -----------------------------------------
async def create_user(data, profile_image: str | None = None):
    existing = await db.users.find_one({"email": data.email})
    if existing:
        return None

    hashed = hash_password(data.password)
    
    # Generar código de verificación simple (6 dígitos)
    verification_code = str(secrets.randbelow(1000000)).zfill(6)

    # Imprimir el código en logs para que el usuario pueda verlo sin SMTP por ahora
    print(f"📧 [MOCK EMAIL] Código para {data.email}: {verification_code}")

    new_user = {
        "name": data.name,
        "email": data.email,
        "hashed_password": hashed,
        "profile_image": profile_image,
        "is_verified": False,
        "verification_code": verification_code
    }

    new_user["id"] = str(result.inserted_id)

    return new_user


# -----------------------------------------
# Reenviar Código de Verificación
# -----------------------------------------
async def resend_verification_code(email: str):
    user = await db.users.find_one({"email": email})
    if not user:
        return False
        
    if user.get("is_verified", False):
        return False # Ya verificado, no reenviamos

    # Generar nuevo código
    code = str(secrets.randbelow(1000000)).zfill(6)
    print(f"📧 [MOCK EMAIL RESEND] Nuevo código para {email}: {code}")

    await db.users.update_one(
        {"email": email},
        {"$set": {"verification_code": code}}
    )
    return True



# -----------------------------------------
# Login
# -----------------------------------------
async def login_user(data):
    user = await db.users.find_one({"email": data.email})
    if not user:
        return None

    if not verify_password(data.password, user["hashed_password"]):
        return None
        
    # Validar si está verificado
    if not user.get("is_verified", False):
        # Retornamos un dict especial para indicar "no verificado"
        # El router deberá encargarse de lanzar la HTTPException 403
        return {"error": "not_verified", "email": user["email"]}

    token = create_access_token({"sub": str(user["_id"])})

    return {
        "token": token,
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "profile_image": user.get("profile_image")
        }
    }


# -----------------------------------------
# Verificar Email
# -----------------------------------------
async def verify_email_code(email: str, code: str):
    user = await db.users.find_one({"email": email})
    if not user:
        return False
        
    # Verificar código (asumiendo que guardamos el código tal cual)
    # En producción deberíamos tener expiración, pero para MVP está bien.
    stored_code = user.get("verification_code")
    
    if stored_code and stored_code == code:
        await db.users.update_one(
            {"email": email},
            {"$set": {"is_verified": True}, "$unset": {"verification_code": ""}}
        )
        return True
        
    return False


# -----------------------------------------
# Obtener usuario por ID (para /users/me)
# -----------------------------------------
async def get_user_by_id(user_id: str):
    user = await db.users.find_one({"_id": ObjectId(user_id)})

    if not user:
        return None

    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "profile_image": user.get("profile_image")
    }


# -----------------------------------------
# Guardar imagen de perfil
# -----------------------------------------
async def update_profile_image(user_id: str, image_url: str):
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"profile_image": image_url}}
    )
    return True
