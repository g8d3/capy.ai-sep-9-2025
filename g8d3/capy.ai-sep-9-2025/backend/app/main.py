from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.core.config import settings
from app.api.v1.endpoints import auth, assets, backtests


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, default_response_class=ORJSONResponse)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(o) for o in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(assets.router, prefix="/api/v1/assets", tags=["assets"])
    app.include_router(backtests.router, prefix="/api/v1/backtests", tags=["backtests"])

    return app


app = create_app()
