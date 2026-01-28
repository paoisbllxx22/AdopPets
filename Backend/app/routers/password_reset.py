# Backend/app/routers/password_reset.py
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import httpx

from app.core.config import settings

router = APIRouter(prefix="/password-reset", tags=["Password Reset"])
templates = Jinja2Templates(directory="app/templates")


# 1️⃣ Mostrar pantalla "Olvidé mi contraseña" (si no la tienes ya)
@router.get("/forgot", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse(
        "forgot_password.html",
        {"request": request, "error": None, "message": None}
    )


# 2️⃣ Solicitar reset (envía correo desde Auth Service)
@router.post("/request", response_class=HTMLResponse)
async def request_reset(request: Request, email: str = Form(...)):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.AUTH_SERVICE_URL}/auth/forgot-password",
            data={"email": email},
            timeout=10
        )

    # El Auth service siempre responde genérico (aunque no exista) -> buena práctica
    # Si DEBUG_EMAIL=true, el link/token saldrá en la consola del auth_service
    return templates.TemplateResponse(
        "forgot_password.html",
        {
            "request": request,
            "error": None,
            "message": "Si el correo existe, te enviamos un enlace/código para resetear tu contraseña. Revisa tu correo."
        }
    )


# 3️⃣ Mostrar pantalla de reset (aquí el usuario pega el token que le llegó)
@router.get("/reset", response_class=HTMLResponse)
async def reset_password_page(
    request: Request,
    email: str | None = None,
    token: str | None = None
):
    # email y token vienen opcionalmente por query params si el link del correo los trae
    return templates.TemplateResponse(
        "reset_password.html",
        {"request": request, "email": email or "", "token": token or "", "error": None}
    )


# 4️⃣ Ejecutar reset (cambia la contraseña en Auth Service)
@router.post("/reset", response_class=HTMLResponse)
async def reset_password(
    request: Request,
    email: str = Form(...),
    token: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    if password != confirm_password:
        return templates.TemplateResponse(
            "reset_password.html",
            {"request": request, "email": email, "token": token, "error": "Las contraseñas no coinciden."},
            status_code=400
        )

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.AUTH_SERVICE_URL}/auth/reset-password",
            data={"email": email, "token": token, "new_password": password},
            timeout=10
        )

    if resp.status_code != 200:
        return templates.TemplateResponse(
            "reset_password.html",
            {"request": request, "email": email, "token": token, "error": "Token inválido o expirado."},
            status_code=400
        )

    return RedirectResponse(url="/login", status_code=302)
