from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import httpx
import os

app = FastAPI()

# Configuración de URLs de servicios
# En Kubernetes: http://backend-service:8000
# En local: http://localhost:8000
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend-service:8000")
AUTH_URL = os.getenv("AUTH_URL", "http://auth-service:80")

# Montar estáticos y templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
# Montar uploads (para ver las fotos que se suben)
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

templates = Jinja2Templates(directory="app/templates")

from app.routers import auth, home, email_verify, profile

app.include_router(auth.router)
app.include_router(home.router)
app.include_router(email_verify.router)
app.include_router(profile.router)

@app.get("/")
async def root():
    return RedirectResponse(url="/login", status_code=302)
