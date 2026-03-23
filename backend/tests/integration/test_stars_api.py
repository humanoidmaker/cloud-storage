import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.file import File
from app.models.user import User
from app.utils.hashing import hash_password
from tests.conftest import TestingSessionLocal, auth_headers


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def user():
    async with TestingSessionLocal() as session:
        u = User(id=uuid.uuid4(), email="stars@example.com", name="Stars",
                 password_hash=hash_password("pass"), role="user", storage_used=0, storage_quota=5368709120, is_active=True)
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return u


@pytest_asyncio.fixture
async def test_file(user):
    async with TestingSessionLocal() as session:
        f = File(id=uuid.uuid4(), name="star.txt", owner_id=user.id, is_folder=False, size=100, storage_key="k")
        session.add(f)
        await session.commit()
        await session.refresh(f)
        return f


@pytest.mark.asyncio
async def test_star_file(client, user, test_file):
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.post(f"/api/stars/{test_file.id}", headers=h)
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_unstar_file(client, user, test_file):
    h = auth_headers(user.id, user.email, user.role)
    await client.post(f"/api/stars/{test_file.id}", headers=h)
    resp = await client.delete(f"/api/stars/{test_file.id}", headers=h)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_list_starred(client, user, test_file):
    h = auth_headers(user.id, user.email, user.role)
    await client.post(f"/api/stars/{test_file.id}", headers=h)
    resp = await client.get("/api/stars", headers=h)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_star_idempotent(client, user, test_file):
    h = auth_headers(user.id, user.email, user.role)
    await client.post(f"/api/stars/{test_file.id}", headers=h)
    resp = await client.post(f"/api/stars/{test_file.id}", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_unstar_not_starred(client, user, test_file):
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.delete(f"/api/stars/{test_file.id}", headers=h)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_star_inaccessible(client, user):
    async with TestingSessionLocal() as session:
        other = User(id=uuid.uuid4(), email="other_star@example.com", name="Other",
                     password_hash=hash_password("p"), role="user", storage_used=0, storage_quota=5368709120, is_active=True)
        session.add(other)
        f = File(id=uuid.uuid4(), name="private.txt", owner_id=other.id, is_folder=False, size=10, storage_key="k")
        session.add(f)
        await session.commit()
        fid = f.id
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.post(f"/api/stars/{fid}", headers=h)
    assert resp.status_code == 403
