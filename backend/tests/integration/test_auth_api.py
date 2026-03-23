import uuid
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.user import User
from app.utils.hashing import hash_password
from app.utils.tokens import create_access_token, create_refresh_token
from tests.conftest import TestingSessionLocal, auth_headers


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def existing_user():
    async with TestingSessionLocal() as session:
        u = User(id=uuid.uuid4(), email="existing@example.com", name="Existing",
                 password_hash=hash_password("password123"), role="user",
                 storage_used=0, storage_quota=5368709120, is_active=True)
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return u


@pytest.mark.asyncio
async def test_register_success(client):
    resp = await client.post("/api/auth/register", json={
        "email": "new@example.com", "name": "New User", "password": "password123"
    })
    assert resp.status_code == 201
    assert resp.json()["email"] == "new@example.com"


@pytest.mark.asyncio
async def test_register_duplicate_email(client, existing_user):
    resp = await client.post("/api/auth/register", json={
        "email": existing_user.email, "name": "Dupe", "password": "password123"
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_register_invalid_email(client):
    resp = await client.post("/api/auth/register", json={
        "email": "not-an-email", "name": "Bad", "password": "password123"
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_weak_password(client):
    resp = await client.post("/api/auth/register", json={
        "email": "weak@example.com", "name": "Weak", "password": "short"
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client, existing_user):
    resp = await client.post("/api/auth/login", json={
        "email": existing_user.email, "password": "password123"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client, existing_user):
    resp = await client.post("/api/auth/login", json={
        "email": existing_user.email, "password": "wrongpass"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent(client):
    resp = await client.post("/api/auth/login", json={
        "email": "nobody@example.com", "password": "pass123"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_deactivated(client):
    async with TestingSessionLocal() as session:
        u = User(id=uuid.uuid4(), email="deactivated@example.com", name="Deactivated",
                 password_hash=hash_password("password123"), role="user",
                 storage_used=0, storage_quota=5368709120, is_active=False)
        session.add(u)
        await session.commit()
    resp = await client.post("/api/auth/login", json={
        "email": "deactivated@example.com", "password": "password123"
    })
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_refresh_token(client, existing_user):
    refresh = create_refresh_token(existing_user.id)
    resp = await client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_refresh_expired(client):
    resp = await client.post("/api/auth/refresh", json={"refresh_token": "invalid.token.here"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_success(client, existing_user):
    headers = auth_headers(existing_user.id, existing_user.email, existing_user.role)
    resp = await client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == existing_user.email


@pytest.mark.asyncio
async def test_me_no_token(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_change_password_success(client, existing_user):
    headers = auth_headers(existing_user.id, existing_user.email, existing_user.role)
    resp = await client.post("/api/auth/change-password", json={
        "current_password": "password123", "new_password": "newpass12345"
    }, headers=headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_current(client, existing_user):
    headers = auth_headers(existing_user.id, existing_user.email, existing_user.role)
    resp = await client.post("/api/auth/change-password", json={
        "current_password": "wrongcurrent", "new_password": "newpass12345"
    }, headers=headers)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_expired_access_token(client):
    from jose import jwt
    from app.config import settings
    from datetime import datetime, timedelta, timezone
    payload = {"sub": str(uuid.uuid4()), "email": "e@e.com", "role": "user", "type": "access",
               "exp": datetime.now(timezone.utc) - timedelta(hours=1)}
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
