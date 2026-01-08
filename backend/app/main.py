from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.features import router as features_router
from app.api.webhooks import router as webhooks_router
from app.api.brainstorms import router as brainstorms_router
from app.api.ideas import router as ideas_router
from app.tasks.polling_task import start_polling_scheduler, stop_polling_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Handles startup and shutdown events for background tasks.
    """
    # Startup: Start polling scheduler
    start_polling_scheduler()
    yield
    # Shutdown: Stop polling scheduler
    stop_polling_scheduler()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(features_router)
app.include_router(webhooks_router)
app.include_router(brainstorms_router)
app.include_router(ideas_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_name}
