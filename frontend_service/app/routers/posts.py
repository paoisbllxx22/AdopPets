from fastapi import APIRouter, Request, Form, UploadFile, File, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import httpx
from app.core.config import settings
from app.core.auth import get_current_user

router = APIRouter(prefix="/posts", tags=["Posts"])
templates = Jinja2Templates(directory="app/templates")


# ============================
# MOSTRAR FORMULARIO (GET)
# ============================
@router.get("/create", response_class=HTMLResponse)
async def create_post_page(
    request: Request, 
    user_id: str = Depends(get_current_user)
):
    return templates.TemplateResponse(
        "create_post.html",
        {"request": request, "error": None}
    )


# ============================
# ENVIAR POST AL BACKEND (POST)
# ============================
@router.post("/")
async def create_post_submit(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    details: str = Form(None),
    file: UploadFile = File(None),
    user_id: str = Depends(get_current_user)
):
    # Preparamos los datos
    data_payload = {
        "title": title,
        "description": description,
        "details": details or ""
    }
    
    files_payload = None
    file_content = None
    
    if file and file.filename:
        file_content = await file.read()
        files_payload = {
            "file": (file.filename, file_content, file.content_type)
        }
    
    token = request.cookies.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            if files_payload:
                resp = await client.post(
                    f"{settings.BACKEND_URL}/posts/",
                    data=data_payload,
                    files=files_payload,
                    headers=headers,
                    timeout=20
                )
            else:
                resp = await client.post(
                    f"{settings.BACKEND_URL}/posts/",
                    data=data_payload,
                    headers=headers,
                    timeout=20
                )
        except Exception as e:
            return templates.TemplateResponse(
                "create_post.html",
                {"request": request, "error": f"Error de conexión: {e}"},
                status_code=500
            )

    if resp.status_code != 200:
        return templates.TemplateResponse(
            "create_post.html",
            {"request": request, "error": "Error al crear la publicación."},
            status_code=400
        )
        
    # Éxito -> Redirigir a Home
    return RedirectResponse(url="/home", status_code=302)
