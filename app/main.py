import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.logging import configure_logging
from app.routers.auth import router as auth_router
from app.routers.pages import router as pages_router
from app.routers.organization import router as organization_router
from app.routers.backlog import router as backlog_router
from app.routers.sprint import router as sprint_router
from app.routers.aria_planner import router as aria_planner_router
from app.routers.standup import router as standup_router
from app.routers.aria_actions import router as aria_actions_router
from app.routers.aria_chat import router as aria_chat_router
from app.routers.retro import router as retro_router
from app.routers.insights import router as insights_router
from app.routers.notifications import router as notifications_router

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()
settings.validate_production_security()
templates = Jinja2Templates(directory="app/templates")

app = FastAPI(title=settings.app_name, debug=settings.app_debug and not settings.is_production)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    session_cookie=settings.session_cookie_name,
    max_age=settings.session_max_age,
    same_site="lax",
    https_only=settings.is_production,
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/service-worker.js", include_in_schema=False)
def service_worker():
    return FileResponse(
        "app/static/service-worker.js",
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"},
    )

app.include_router(auth_router)
app.include_router(organization_router)
app.include_router(backlog_router)
app.include_router(sprint_router)
app.include_router(aria_planner_router)
app.include_router(standup_router)
app.include_router(aria_actions_router)
app.include_router(aria_chat_router)
app.include_router(retro_router)
app.include_router(insights_router)
app.include_router(notifications_router)
app.include_router(pages_router)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    try:
        content_length = int(request.headers.get("content-length", "0") or 0)
    except ValueError:
        return JSONResponse({"detail": "Invalid Content-Length"}, status_code=400)
    if content_length > 1_048_576:
        return JSONResponse({"detail": "Request body too large"}, status_code=413)
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    logger.info(
        "request_completed",
        extra={"request_id": request_id},
    )
    return response


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "application": settings.app_name,
        "environment": settings.app_env,
    }


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        return RedirectResponse("/login", status_code=303)
    if exc.status_code in {403, 404}:
        return templates.TemplateResponse(
            request,
            f"errors/{exc.status_code}.html",
            {"page_title": str(exc.status_code)},
            status_code=exc.status_code,
        )
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


@app.exception_handler(Exception)
async def server_error(request: Request, exc: Exception):
    logger.exception("unhandled_application_error")
    return templates.TemplateResponse(
        request,
        "errors/500.html",
        {"page_title": "500"},
        status_code=500,
    )
