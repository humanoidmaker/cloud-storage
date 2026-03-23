import io
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.utils.hashing import hash_password
from app.utils.tokens import create_access_token, create_refresh_token

# In-memory async SQLite for testing
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


async def override_get_db():
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def mock_minio():
    mock = MagicMock()
    mock.put_object.return_value = None
    mock.get_object.return_value = MagicMock(read=lambda: b"file content", close=lambda: None, release_conn=lambda: None)
    mock.remove_object.return_value = None
    mock.presigned_get_object.return_value = "https://minio.local/bucket/file?signature=abc"
    mock.presigned_put_object.return_value = "https://minio.local/bucket/upload?signature=abc"
    mock.stat_object.return_value = MagicMock(size=1024, content_type="application/octet-stream", etag="abc", last_modified=None)
    mock.copy_object.return_value = None
    mock.bucket_exists.return_value = True
    mock.list_buckets.return_value = []
    mock.list_objects.return_value = []
    return mock


@pytest.fixture
def mock_storage(mock_minio):
    with patch("app.services.storage_service.get_minio_client", return_value=mock_minio):
        from app.services.storage_service import StorageService
        svc = StorageService(client=mock_minio)
        yield svc


@pytest.fixture
def test_app():
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def test_user(test_db_session: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        email="testuser@example.com",
        name="Test User",
        password_hash=hash_password("testpass123"),
        role="user",
        storage_used=0,
        storage_quota=5368709120,
        is_active=True,
    )
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(test_db_session: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        name="Admin User",
        password_hash=hash_password("adminpass123"),
        role="superadmin",
        storage_used=0,
        storage_quota=0,
        is_active=True,
    )
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    return user


def auth_headers(user_id: uuid.UUID, email: str = "test@example.com", role: str = "user") -> dict:
    token = create_access_token(user_id, email, role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_headers(test_user):
    return auth_headers(test_user.id, test_user.email, test_user.role)


@pytest.fixture
def admin_headers(admin_user):
    return auth_headers(admin_user.id, admin_user.email, admin_user.role)


@pytest.fixture
def sample_file() -> tuple[io.BytesIO, dict]:
    content = io.BytesIO(b"Hello, this is test file content!")
    content.seek(0)
    headers = {"content-type": "text/plain"}
    return content, headers


@pytest.fixture
def sample_image() -> io.BytesIO:
    # Create a minimal valid JPEG
    import struct
    # Minimal JPEG: SOI + APP0 + SOF + SOS + EOI
    jpeg = bytes([
        0xFF, 0xD8,  # SOI
        0xFF, 0xE0,  # APP0
        0x00, 0x10,  # Length
        0x4A, 0x46, 0x49, 0x46, 0x00,  # JFIF\0
        0x01, 0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00,
        0xFF, 0xD9,  # EOI
    ])
    return io.BytesIO(jpeg)
