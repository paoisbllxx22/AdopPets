#routers/post.py
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.auth import get_current_user
from app.services.posts import (
    create_post,
    get_post_by_id,
    get_posts_feed,
    get_user_posts,
    update_post,
    delete_post
)
import shutil
import uuid

router = APIRouter(prefix="/posts", tags=["Posts"])
templates = Jinja2Templates(directory="app/templates")





# ============================
# CREAR PUBLICACIÓN (POST)
# ============================
@router.post("/")
async def create_new_post(
    title: str = Form(...),
    description: str = Form(...),
    details: str = Form(None),
    file: UploadFile = File(None),
    user_id: str = Depends(get_current_user)
):
    image_url = None

    if file:
        ext = file.filename.split(".")[-1]
        unique_name = f"{uuid.uuid4()}.{ext}"
        file_path = f"uploads/{unique_name}"

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        image_url = f"http://localhost:8000/uploads/{unique_name}"

    data = {
        "title": title,
        "description": description,
        "details": details,
        "image_url": image_url,
        "user_id": user_id,
    }

    post = await create_post(data)
    # Devolvemos JSON para que el Frontend maneje la redirección
    return {"message": "ok", "post": post}


# ============================
# FEED
# ============================
@router.get("/feed/all")
async def feed_posts():
    return await get_posts_feed()


# ============================
# POSTS DE USUARIO
# ============================
@router.get("/user/me")
async def my_posts(user_id: str = Depends(get_current_user)):
    return await get_user_posts(user_id)



# ============================
# POST POR ID (SIEMPRE AL FINAL)
# ============================
@router.get("/{post_id}")
async def get_post(post_id: str):
    post = await get_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")
    return post


# ============================
# UPDATE
# ============================
@router.put("/{post_id}")
async def update_existing_post(
    post_id: str,
    title: str = Form(None),
    description: str = Form(None),
    details: str = Form(None),
    file: UploadFile = File(None),
    user_id: str = Depends(get_current_user)
):
    update_data = {}

    if title:
        update_data["title"] = title
    if description:
        update_data["description"] = description
    if details:
        update_data["details"] = details

    if file:
        ext = file.filename.split(".")[-1]
        unique_name = f"{uuid.uuid4()}.{ext}"
        file_path = f"uploads/{unique_name}"

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        update_data["image_url"] = f"http://localhost:8000/uploads/{unique_name}"

    updated = await update_post(post_id, update_data, user_id)

    if not updated:
        raise HTTPException(status_code=404, detail="No autorizado")

    return {"message": "Publicación actualizada"}


# ============================
# DELETE
# ============================
@router.delete("/{post_id}")
async def delete_existing_post(
    post_id: str,
    user_id: str = Depends(get_current_user)
):
    deleted = await delete_post(post_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="No autorizado")

    return {"message": "Publicación eliminada"}
