from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import evaluations, health, memory, research, uploads
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger, set_request_id
from app.services.container import build_container

LOGGER = get_logger(__name__)
settings = get_settings()
configure_logging(settings)


@asynccontextmanager
async def lifespan(application: FastAPI):
    container = build_container(settings)
    application.state.container = container
    LOGGER.info("Application startup complete")
    yield
    await container.aclose()
    LOGGER.info("Application shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id", f"req-{uuid.uuid4().hex[:10]}")
    set_request_id(request_id)
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response


app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(uploads.router, prefix=settings.api_prefix)
app.include_router(research.router, prefix=settings.api_prefix)
app.include_router(memory.router, prefix=settings.api_prefix)
app.include_router(evaluations.router, prefix=settings.api_prefix)
