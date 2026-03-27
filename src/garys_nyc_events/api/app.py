from __future__ import annotations

from fastapi import FastAPI

from ..config import PipelineConfig
from .routers import events_router, health_router, mcp_router, runs_router


def create_app(_config: PipelineConfig | None = None) -> FastAPI:
    app = FastAPI(
        title="Gary's NYC AI Events API",
        version="1.0.0",
        description="Upcoming NYC AI events scraped from Gary's Guide.",
    )
    app.include_router(health_router)
    app.include_router(events_router, prefix="/events", tags=["events"])
    app.include_router(mcp_router, prefix="/mcp", tags=["mcp"])
    app.include_router(runs_router, prefix="/runs", tags=["runs"])
    return app


app = create_app()
