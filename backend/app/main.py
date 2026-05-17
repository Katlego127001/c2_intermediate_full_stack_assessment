"""FastAPI application entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.dependencies.rate_limit import limiter
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.middleware.request_context import RequestContextMiddleware

configure_logging()
log = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("app.startup", env=settings.APP_ENV, app=settings.APP_NAME)
    yield
    log.info("app.shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(o) for o in settings.BACKEND_CORS_ORIGINS] or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # Rate limit
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # Structured logging context
    app.add_middleware(RequestContextMiddleware)

    @app.get("/health", tags=["meta"])
    async def health():
        return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}

    @app.get("/", tags=["meta"])
    async def root():
        return {"name": settings.APP_NAME, "docs": "/docs", "version": "1.0.0"}

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    return app


app = create_app()
