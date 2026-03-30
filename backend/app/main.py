"""FastAPI application main entry."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.auth import router as auth_router
from app.api.v1.projects import router as projects_router
from app.api.v1.stats.global_stats import router as global_stats_router
from app.api.v1.stats.personal import router as personal_stats_router
from app.api.v1.stats.projects import router as project_stats_router
from app.api.v1.sync import router as sync_router
from app.api.v1.users import router as users_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.response import StandardResponseMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    setup_logging()
    yield
    # Shutdown


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan,
)

# Standard response middleware (must be before CORS)
app.add_middleware(StandardResponseMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(global_stats_router, prefix="/api/v1/stats/global")
app.include_router(project_stats_router, prefix="/api/v1/stats/projects")
app.include_router(personal_stats_router, prefix="/api/v1/stats/personal")
app.include_router(sync_router, prefix="/api/v1/sync")


# Exception handlers for standardized error responses
@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc):
    """Handle 401 unauthorized errors."""
    return JSONResponse(
        status_code=401,
        content={
            "code": 401,
            "message": "Unauthorized",
            "data": None,
        },
    )


@app.exception_handler(403)
async def forbidden_handler(request: Request, exc):
    """Handle 403 forbidden errors."""
    return JSONResponse(
        status_code=403,
        content={
            "code": 403,
            "message": "Forbidden",
            "data": None,
        },
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 not found errors."""
    return JSONResponse(
        status_code=404,
        content={
            "code": 404,
            "message": "Not found",
            "data": None,
        },
    )


@app.exception_handler(422)
async def validation_error_handler(request: Request, exc):
    """Handle 422 validation errors."""
    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "message": "Validation error",
            "data": getattr(exc, 'detail', None),
        },
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    """Handle 500 server errors."""
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "Internal server error",
            "data": None,
        },
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.VERSION}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
    }
