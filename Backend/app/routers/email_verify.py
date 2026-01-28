# Backend/app/routers/email_verify.py

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import httpx

from app.core.config import settings

router = APIRouter(prefix="/email-verify", tags=["Email Verify"])
templates = Jinja2Templates(directory="app/templates")


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _normalize_code(code: str) -> str:
    return (code or "").strip()


async def _post_verify_email(client: httpx.AsyncClient, email: str, code: str) -> httpx.Response:
    """
    Intenta verificar enviando primero JSON y si el auth_service responde 422,
    reintenta con FORM (data=...).
    Esto te evita el típico problema de "Auth espera JSON pero yo envío FORM" (o al revés).
    """
    url = f"{settings.AUTH_SERVICE_URL.rstrip('/')}/auth/verify-email"

    # 1) Primero JSON
    resp = await client.post(url, json={"email": email, "code": code}, timeout=10)

    # Si el auth_service está hecho con Form(...) a veces te devuelve 422
    if resp.status_code == 422:
        resp = await client.post(url, data={"email": email, "code": code}, timeout=10)

    return resp


async def _post_resend_verification(client: httpx.AsyncClient, email: str) -> httpx.Response:
    """
    Reenvía código de verificación (requiere endpoint en auth_service).
    Igual que arriba: intenta JSON y si 422, reintenta con FORM.
    """
    url = f"{settings.AUTH_SERVICE_URL.rstrip('/')}/auth/resend-verification"

    resp = await client.post(url, json={"email": email}, timeout=10)
    if resp.status_code == 422:
        resp = await client.post(url, data={"email": email}, timeout=10)

    return resp


# ✅ Mostrar pantalla para ingresar código
@router.get("", response_class=HTMLResponse)
async def email_verify_page(request: Request, email: str = ""):
    email = _normalize_email(email)
    return templates.TemplateResponse(
        "verify_code.html",
        {"request": request, "email": email, "flow": "email_verify", "error": None, "message": None}
    )


# ✅ Verificar código (llama al Auth Service)
@router.post("/verify", response_class=HTMLResponse)
async def verify_email_code(
    request: Request,
    email: str = Form(...),
    code: str = Form(...),
    flow: str = Form("email_verify"),
):
    email_n = _normalize_email(email)
    code_n = _normalize_code(code)

    # Validaciones rápidas antes de llamar al microservicio
    if not email_n or "@" not in email_n:
        return templates.TemplateResponse(
            "verify_code.html",
            {"request": request, "email": email_n, "flow": "email_verify", "error": "Email inválido.", "message": None},
            status_code=400
        )

    if not code_n:
        return templates.TemplateResponse(
            "verify_code.html",
            {"request": request, "email": email_n, "flow": "email_verify", "error": "Debes ingresar el código.", "message": None},
            status_code=400
        )

    try:
        async with httpx.AsyncClient() as client:
            resp = await _post_verify_email(client, email_n, code_n)
    except Exception:
        return templates.TemplateResponse(
            "verify_code.html",
            {
                "request": request,
                "email": email_n,
                "flow": "email_verify",
                "error": "No se pudo contactar al Auth Service (8001). Verifica que esté levantado.",
                "message": None,
            },
            status_code=503
        )

    if resp.status_code != 200:
        # ✅ Mostrar error real del Auth Service (si viene)
        detail_msg = "Código inválido o expirado."
        try:
            data = resp.json()
            if isinstance(data, dict) and "detail" in data:
                # Puede ser string o lista (422)
                if isinstance(data["detail"], str):
                    detail_msg = data["detail"]
                else:
                    detail_msg = str(data["detail"])
        except Exception:
            # Si no es JSON
            if resp.text:
                detail_msg = resp.text

        return templates.TemplateResponse(
            "verify_code.html",
            {
                "request": request,
                "email": email_n,
                "flow": "email_verify",
                "error": detail_msg,
                "message": None,
            },
            status_code=400
        )

    # ✅ Verificado OK -> login
    return RedirectResponse(url="/login", status_code=302)


# ✅ Reenviar código (requiere endpoint /auth/resend-verification en auth_service)
@router.post("/resend", response_class=HTMLResponse)
async def resend_email_code(
    request: Request,
    email: str = Form(...),
    flow: str = Form("email_verify"),
):
    email_n = _normalize_email(email)

    if not email_n or "@" not in email_n:
        return templates.TemplateResponse(
            "verify_code.html",
            {"request": request, "email": email_n, "flow": "email_verify", "error": "Email inválido.", "message": None},
            status_code=400
        )

    try:
        async with httpx.AsyncClient() as client:
            resp = await _post_resend_verification(client, email_n)
    except Exception:
        return templates.TemplateResponse(
            "verify_code.html",
            {
                "request": request,
                "email": email_n,
                "flow": "email_verify",
                "error": "No se pudo contactar al Auth Service (8001).",
                "message": None,
            },
            status_code=503
        )

    if resp.status_code != 200:
        # si aún no existe endpoint, normalmente será 404
        msg = "No se pudo reenviar el código. "
        if resp.status_code == 404:
            msg += "Aún no está implementado /auth/resend-verification en el Auth Service."
        else:
            try:
                data = resp.json()
                if isinstance(data, dict) and "detail" in data:
                    msg += str(data["detail"])
                else:
                    msg += resp.text
            except Exception:
                msg += resp.text or f"HTTP {resp.status_code}"

        return templates.TemplateResponse(
            "verify_code.html",
            {"request": request, "email": email_n, "flow": "email_verify", "error": msg, "message": None},
            status_code=400
        )

    # OK reenviado
    return templates.TemplateResponse(
        "verify_code.html",
        {
            "request": request,
            "email": email_n,
            "flow": "email_verify",
            "error": None,
            "message": "Código reenviado. Revisa tu correo (y carpeta spam).",
        }
    )
