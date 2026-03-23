import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, files, folders, sharing, stars, tags, trash, search, versions, preview
from app.api.admin import dashboard, users, storage, files as admin_files, activity, system, settings
from app.config import settings as app_settings
from app.middleware.request_logger import RequestLoggerMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title=app_settings.APP_NAME,
    version=app_settings.APP_VERSION,
    description="Cloud Storage - Self-hosted Cloud Storage Service",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging
app.add_middleware(RequestLoggerMiddleware)

# User API routes
app.include_router(auth.router)
app.include_router(files.router)
app.include_router(folders.router)
app.include_router(sharing.router)
app.include_router(stars.router)
app.include_router(tags.router)
app.include_router(trash.router)
app.include_router(search.router)
app.include_router(versions.router)
app.include_router(preview.router)

# Admin API routes
app.include_router(dashboard.router)
app.include_router(users.router)
app.include_router(storage.router)
app.include_router(admin_files.router)
app.include_router(activity.router)
app.include_router(system.router)
app.include_router(settings.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": app_settings.APP_NAME, "version": app_settings.APP_VERSION}


@app.get("/api/health")
async def api_health_check():
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    logging.info("Cloud Storage API starting up...")
    # Initialize MinIO buckets (best effort)
    try:
        from app.utils.minio_client import init_buckets
        init_buckets()
        logging.info("MinIO buckets initialized")
    except Exception as e:
        logging.warning(f"Could not initialize MinIO buckets: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    logging.info("Cloud Storage API shutting down...")
