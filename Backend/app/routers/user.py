#routers/user.py
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from bson import ObjectId
import uuid
import shutil
from fastapi import Form

from app.schemas.user import UserRegister, UserLogin, UserResponse
from app.services.users import (
    create_user,
    login_user,
    update_profile_image
)
from app.core.auth import get_current_user
from app.db.init_db import db


router = APIRouter(prefix="/users", tags=["Users"])


# ============================
# REGISTER (API)
# ============================
@router.post("/register", response_model=UserResponse)
async def register_user(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    file: UploadFile | None = File(None)
):
    profile_image_url = None

    if file:
        if not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail="El archivo debe ser una imagen"
            )

        ext = file.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        file_path = f"uploads/{filename}"

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        profile_image_url = f"http://localhost:8000/uploads/{filename}"

    user_data = UserRegister(
        name=name,
        email=email,
        password=password
    )

    user = await create_user(user_data, profile_image_url)

    if not user:
        raise HTTPException(
            status_code=400,
            detail="El usuario ya existe"
        )

    return user


# ============================
# LOGIN (API – usado solo si fuera API pura)
# ============================
@router.post("/login")
async def login(data: UserLogin):
    result = await login_user(data)
    if not result:
        raise HTTPException(
            status_code=401,
            detail="Credenciales inválidas"
        )
    return result


# ============================
# USUARIO ACTUAL
# ============================
@router.get("/me")
async def get_me(user_id: str = Depends(get_current_user)):
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "profile_image": user.get("profile_image")
    }


# ============================
# SUBIR / ACTUALIZAR AVATAR
# ============================
@router.post("/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):
    # Validar tipo simple (opcional pero recomendado)
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser una imagen"
        )

    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = f"uploads/{filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    image_url = f"http://localhost:8000/uploads/{filename}"

    await update_profile_image(user_id, image_url)

    return {
        "profile_image": image_url
    }
