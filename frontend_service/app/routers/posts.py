from fastapi import APIRouter, Request, Form, UploadFile, File, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
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


# ============================
# FEED (PROXY) - GET /posts/feed/all
# ============================
@router.get("/feed/all")
async def get_feed_proxy(request: Request):
    token = request.cookies.get("access_token")
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    async with httpx.AsyncClient() as client:
        try:
            # Llamamos al backend: /posts/feed/all
            resp = await client.get(f"{settings.BACKEND_URL}/posts/feed/all", headers=headers, timeout=10)
            if resp.status_code == 200:
                posts = resp.json()
                # CORRECCIÓN DE URLs DE IMÁGENES AL VUELO
                # Reemplazamos localhost:8000 por la IP pública del backend (Puerto 30000)
                PUBLIC_BACKEND_URL = "http://34.51.71.65:30000"
                
                for post in posts:
                    # Fix Post Image
                    if post.get("image_url") and "localhost:8000" in post["image_url"]:
                        post["image_url"] = post["image_url"].replace("http://localhost:8000", PUBLIC_BACKEND_URL)
                    
                    # Fix User Avatar in Feed
                    if post.get("user_profile_image") and "localhost:8000" in post["user_profile_image"]:
                        post["user_profile_image"] = post["user_profile_image"].replace("http://localhost:8000", PUBLIC_BACKEND_URL)
                
                return posts
            else:
                return []
        except Exception as e:
            print(f"Error fetching feed: {e}")
            return []


# ============================
# MIS POSTS (PROXY) - GET /posts/user/me
# ============================
@router.get("/user/me")
async def get_my_posts_proxy(request: Request):
    token = request.cookies.get("access_token")
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    async with httpx.AsyncClient() as client:
        try:
            # Llamamos al backend: /posts/user/me
            resp = await client.get(f"{settings.BACKEND_URL}/posts/user/me", headers=headers, timeout=10)
            if resp.status_code == 200:
                posts = resp.json()
                # CORRECCIÓN DE URLs DE IMÁGENES
                PUBLIC_BACKEND_URL = "http://34.51.71.65:30000"
                
                for post in posts:
                    if post.get("image_url") and "localhost:8000" in post["image_url"]:
                        post["image_url"] = post["image_url"].replace("http://localhost:8000", PUBLIC_BACKEND_URL)
                
                return posts
            else:
                return []
        except Exception as e:
            print(f"Error fetching my posts: {e}")
            return []


# ============================
# ELIMINAR POST (PROXY) - DELETE /posts/{post_id}
# ============================
@router.delete("/{post_id}")
async def delete_post_proxy(request: Request, post_id: str):
    token = request.cookies.get("access_token")
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.delete(f"{settings.BACKEND_URL}/posts/{post_id}", headers=headers, timeout=10)
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


# ============================
# EDITAR POST (PROXY) - PUT /posts/{post_id}
# ============================
@router.put("/{post_id}")
async def update_post_proxy(
    request: Request,
    post_id: str,
    title: str = Form(None),
    description: str = Form(None),
    details: str = Form(None),
    file: UploadFile = File(None)
):
    token = request.cookies.get("access_token")
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    data_payload = {}
    if title: data_payload["title"] = title
    if description: data_payload["description"] = description
    if details: data_payload["details"] = details
    
    files_payload = None
    if file and file.filename:
        file_content = await file.read()
        files_payload = {
            "file": (file.filename, file_content, file.content_type)
        }
    
    async with httpx.AsyncClient() as client:
        try:
            if files_payload:
                resp = await client.put(
                    f"{settings.BACKEND_URL}/posts/{post_id}",
                    data=data_payload,
                    files=files_payload,
                    headers=headers,
                    timeout=10
                )
            else:
                resp = await client.put(
                    f"{settings.BACKEND_URL}/posts/{post_id}",
                    data=data_payload,
                    headers=headers,
                    timeout=10
                )
            
            if resp.status_code == 200:
                return resp.json()
            else:
                # Retornamos el error del back
                return JSONResponse(status_code=resp.status_code, content=resp.json())
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
