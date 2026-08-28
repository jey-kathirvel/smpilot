from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", include_in_schema=False)
async def home() -> RedirectResponse:
    return RedirectResponse(url="/login", status_code=307)


@router.get("/login", include_in_schema=False)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"page_title": "Log in"})


@router.get("/signup", include_in_schema=False)
async def signup_page(request: Request):
    return templates.TemplateResponse(request, "signup.html", {"page_title": "Sign up"})


@router.get("/today", include_in_schema=False)
async def today_page(request: Request):
    return templates.TemplateResponse(
        request, "today.html", {"page_title": "Today", "show_nav": True}
    )
