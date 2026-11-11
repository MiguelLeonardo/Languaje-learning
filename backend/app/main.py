import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import catalog, practice, roleplay, system
from app.content.repository import get_repository
from app.core.config import get_settings
from app.db.session import init_db

logging.basicConfig(level=logging.INFO, format='{"level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}')


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    get_repository()  # fail fast on invalid content
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Languaje-learning API",
        version="0.1.0",
        description="Speaking-first English learning: shadowing, common phrases, staged exercises, "
                    "spaced repetition and scripted AI roleplay. Every answer is submitted as audio.",
        lifespan=lifespan,
        docs_url="/docs" if settings.env != "production" else None,
        redoc_url=None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-OpenAI-Key", "X-ElevenLabs-Key", "X-Anthropic-Key"],
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response

    for r in (system.router, catalog.router, practice.router, roleplay.router):
        app.include_router(r)
    return app


app = create_app()
