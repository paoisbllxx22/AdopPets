from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import HTTPException

from app.core.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/home", response_class=HTMLResponse)
async def home_page(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    # Si llega aquí, ya está autenticado (token validado por auth_service)
    return templates.TemplateResponse(
        "home.html",
        {"request": request}
    )
