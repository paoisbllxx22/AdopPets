from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import (
    user,
    post,
    chat,
    profile, # Profile API might be useful, keep it for now if it has logic
)
import os

app = FastAPI()

# ============================
# Directorio para uploads (Necesario para gaurdar imagenes)
# ============================
os.makedirs("uploads", exist_ok=True)

# Servir imágenes subidas (avatars, posts, etc.)
app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)

# ============================
# ROOT
# ============================
@app.get("/")
async def root():
    return {"message": "AdopPets API Backend v2.0"}


# ============================
# Routers API
# ============================
app.include_router(user.router)
app.include_router(post.router)
app.include_router(chat.router)
app.include_router(profile.router) 

