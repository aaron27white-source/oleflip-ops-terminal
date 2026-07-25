"""main.py — FastAPI app. Bootstraps + migrates the DB once at startup, then
serves the routers."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents.scheduler import shutdown_scheduler, start_scheduler
from app.config import settings
from app.db import init_database
from app.errors import install_error_handlers
from app.routers import (
    agents,
    bid,
    catalog,
    dashboard,
    health,
    inventory,
    itad,
    leads,
    notifications,
    photos,
    products,
    scanner,
    sources,
    voice,
    watchlist,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    status = init_database()
    health.STATUS.update(status)
    start_scheduler()  # registers cron jobs from the agents table (no-op if disabled)
    try:
        yield
    finally:
        shutdown_scheduler()


app = FastAPI(title="Oleflip API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

install_error_handlers(app)

for r in (health, bid, catalog, products, inventory, sources, leads, scanner, dashboard,
          itad, agents, watchlist, voice, notifications, photos):
    app.include_router(r.router)

# Tier 4 — serve uploaded photos as static files (created on first boot).
from pathlib import Path  # noqa: E402

from fastapi.staticfiles import StaticFiles  # noqa: E402

_uploads = Path(settings.upload_dir)
_uploads.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_uploads)), name="uploads")
