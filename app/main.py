from fastapi import FastAPI

from app.api.routes import health, anime


def create_app() -> FastAPI:
    app = FastAPI(title="anime-db", version="0.1.0")

    app.include_router(health.router)
    app.include_router(anime.router)

    return app
