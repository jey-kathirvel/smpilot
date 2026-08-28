from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth.dependencies import csrf_token, require_user
from app.models.user import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", include_in_schema=False)
async def home() -> RedirectResponse:
    return RedirectResponse(url="/login", status_code=307)


@router.get("/today", include_in_schema=False)
async def today_page(request: Request, user: User = Depends(require_user)):
    return templates.TemplateResponse(
        request,
        "today.html",
        {"page_title": "Today", "show_nav": True, "user": user, "csrf_token": csrf_token(request)},
    )
