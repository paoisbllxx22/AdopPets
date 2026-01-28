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
@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.AUTH_SERVICE_URL}/auth/login",
            json={"email": email, "password": password},
            timeout=10
        )

    # ✅ Si el auth_service dice "no verificado" -> ir a pantalla de verificación
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

    # 2️⃣ Guardar imagen (si existe) - NO rompe lo que ya tienes
    profile_image_url = None
    if file and file.filename:
        if not file.content_type.startswith("image/"):
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "error": "El archivo debe ser una imagen."},
                status_code=400
            )

        ext = file.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        path = f"uploads/{filename}"

        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        profile_image_url = f"http://localhost:8000/uploads/{filename}"

    # 3️⃣ Registrar en Auth Service (ahora manda código)
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.AUTH_SERVICE_URL}/auth/register",
            json={"name": name, "email": email, "password": password},
            timeout=10
        )

    if resp.status_code != 200:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Ya existe un usuario con ese correo."},
            status_code=400
        )

    # ✅ 4️⃣ En vez de /login, ir a verificar email
    return RedirectResponse(url=f"/email-verify?email={email}", status_code=302)


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
