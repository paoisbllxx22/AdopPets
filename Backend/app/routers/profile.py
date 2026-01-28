#routers/profile.py
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.auth import get_current_user

router = APIRouter(tags=["Profile"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/perfil", response_class=HTMLResponse)
async def my_profile(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    # ✅ user_id YA ES un string
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user_id": user_id
        }
    )
