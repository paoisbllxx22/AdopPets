from fastapi import (
    APIRouter,
    Request,
    Form,
    UploadFile,
    File,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import uuid
import shutil
import httpx

from app.core.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# ============================
# LOGIN (GET)
# ============================
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None}
    )


# ============================
# LOGIN (POST)
# ============================
# ============================
# LOGIN (POST)
# ============================
@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    async with httpx.AsyncClient() as client:
        # Backend espera JSON para Login (UserLogin logic)
        resp = await client.post(
            f"{settings.BACKEND_URL}/users/login",
            json={"email": email, "password": password},
            timeout=10
        )

    # ✅ Si el auth_service dice "no verificado" -> ir a pantalla de verificación
    # (Adaptar si el backend devuelve un código específico para esto)
    if resp.status_code == 403:
        return RedirectResponse(url=f"/email-verify?email={email}", status_code=302)

    if resp.status_code != 200:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Correo o contraseña incorrectos."},
            status_code=400
        )

    token = resp.json()["token"]

    response = RedirectResponse(url="/home", status_code=302)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax"
    )
    return response


# ============================
# REGISTER (GET)
# ============================
@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "error": None}
    )


# ============================
# REGISTER (POST)
# ============================
@router.post("/register")
async def register_submit(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    file: UploadFile | None = File(None)
):
    # 1️⃣ Validar contraseñas
    if password != confirm_password:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Las contraseñas no coinciden."},
            status_code=400
        )

    # 2️⃣ Preparar datos para enviar al Backend
    # Backend espera Form Data para /users/register
    data_payload = {
        "name": name,
        "email": email,
        "password": password
    }
    
    files_payload = None
    if file and file.filename:
        # Leemos el archivo para re-enviarlo
        file_content = await file.read()
        files_payload = {
            "file": (file.filename, file_content, file.content_type)
        }
        await file.seek(0) # Resetear puntero por si acaso se necesitara leer de nuevo (aunque aquí terminamos)

    # 3️⃣ Registrar en Backend Service
    async with httpx.AsyncClient() as client:
        if files_payload:
            resp = await client.post(
                f"{settings.BACKEND_URL}/users/register",
                data=data_payload,
                files=files_payload,
                timeout=10
            ) 
        else:
            resp = await client.post(
                f"{settings.BACKEND_URL}/users/register",
                data=data_payload,
                timeout=10
            )

    if resp.status_code != 200:
        # Intentar obtener detalle del error del backend
        try:
            detail = resp.json().get("detail", "Error en el registro.")
        except:
            detail = "Ya existe un usuario con ese correo o hubo un error."
            
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": detail},
            status_code=400
        )

    # ✅ 4️⃣ Al finalizar registro, ir a login (o home si login automático)
    # Backend devuelve el usuario creado, pero no un token en register. 
    # Lo mandamos a Login para que inicie sesión.
    return RedirectResponse(url="/login", status_code=302)


# ============================
# LOGOUT
# ============================
@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="access_token", path="/")
    return response


# ============================
# FORGOT PASSWORD (GET)
# ============================
@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse(
        "forgot_password.html",
        {"request": request, "error": None}
    )
