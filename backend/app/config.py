from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Cloud Storage"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://cloudstorage:cloudstorage@localhost:5432/cloudstorage"
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_FILES_BUCKET: str = "cloud_storage-files"
    MINIO_THUMBNAILS_BUCKET: str = "cloud_storage-thumbnails"

    # JWT
    JWT_SECRET_KEY: str = "jwt-secret-change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Storage
    DEFAULT_STORAGE_QUOTA_BYTES: int = 5 * 1024 * 1024 * 1024  # 5GB
    MAX_UPLOAD_SIZE_BYTES: int = 5 * 1024 * 1024 * 1024  # 5GB
    ALLOWED_EXTENSIONS: str = ""  # empty = allow all
    CHUNK_SIZE_BYTES: int = 100 * 1024 * 1024  # 100MB threshold for chunked upload
    PRESIGNED_URL_EXPIRY_SECONDS: int = 3600

    # Trash
    TRASH_AUTO_PURGE_DAYS: int = 30

    # Versioning
    MAX_FILE_VERSIONS: int = 10

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_UPLOAD_PER_MINUTE: int = 20

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Registration
    REGISTRATION_ENABLED: bool = True

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def allowed_extensions_list(self) -> list[str]:
        if not self.ALLOWED_EXTENSIONS:
            return []
        return [ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",") if ext.strip()]

    model_config = {"env_prefix": "VAULTBOX_", "env_file": ".env", "extra": "ignore"}


settings = Settings()
