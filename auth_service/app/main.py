from fastapi import FastAPI
from app.routers.auth_api import router as auth_router

app = FastAPI(title="AdopPets Auth Service")
app.include_router(auth_router)

@app.get("/")
async def health():
    return {"status": "ok", "service": "auth"}
