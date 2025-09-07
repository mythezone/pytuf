from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import connect, disconnect
from routers import actresses, movies, graph
from routers import media


def create_app() -> FastAPI:
    app = FastAPI(title="Publisher Graph API", version="0.1.0")

    # CORS for local dev and web app
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(actresses.router)
    app.include_router(movies.router)
    app.include_router(graph.router)
    app.include_router(media.router)

    @app.on_event("startup")
    async def _startup():
        await connect()

    @app.on_event("shutdown")
    async def _shutdown():
        await disconnect()

    return app


app = create_app()

# MEDIA_ROOT=/Volumes/images/jdb uvicorn app:app --reload --workers 4 --host 0.0.0.0 --port 8000
