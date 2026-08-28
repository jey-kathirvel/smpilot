import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException

from app.config import get_settings
from app.logging import configure_logging
from app.routers.pages import router as pages_router

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()
templates = Jinja2Templates(directory="app/templates")

app = FastAPI(title=settings.app_name, debug=settings.app_debug and not settings.is_production)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(pages_router)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
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
