"""
Vigilant application entry point.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import get_settings
from app.database.session import Base, engine
from app.routes import auth_routes, dashboard_routes, sub_routes

settings = get_settings()

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(name)-28s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("vigilant")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup (dev convenience). In prod use Alembic."""
    logger.info("Starting Vigilant v%s", settings.APP_VERSION)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured.")
    yield
    logger.info("Shutting down Vigilant.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Routers
app.include_router(dashboard_routes.router)
app.include_router(auth_routes.router)
app.include_router(sub_routes.router)
