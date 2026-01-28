#main.py
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.routers import (
    user,
    post,
    chat,
    auth_front,
    home_front,
    profile,
    password_reset,
    email_verify,
)
import os

app = FastAPI()

# ============================
# Directorio para uploads
# ============================
os.makedirs("uploads", exist_ok=True)

# Servir imágenes subidas (avatars, posts, etc.)
app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)

# Archivos estáticos del frontend
app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)

# Templates HTML
templates = Jinja2Templates(directory="app/templates")


# ============================
# ROOT
# ============================
@app.get("/")
async def root():
    return {"message": "Backend funcionando correctamente!"}


# ============================
# Routers
# ============================
app.include_router(user.router)
app.include_router(post.router)
app.include_router(chat.router)
app.include_router(auth_front.router)
app.include_router(home_front.router)
app.include_router(profile.router)
app.include_router(password_reset.router)
app.include_router(email_verify.router) 

