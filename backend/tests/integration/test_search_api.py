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
        u = User(id=uuid.uuid4(), email="search_api@example.com", name="Search",
                 password_hash=hash_password("pass"), role="user", storage_used=0, storage_quota=5368709120, is_active=True)
        session.add(u)
        for name, mime in [("report_annual.pdf", "application/pdf"), ("photo_vacation.jpg", "image/jpeg"), ("notes_meeting.txt", "text/plain")]:
            f = File(id=uuid.uuid4(), name=name, mime_type=mime, size=1024, owner_id=u.id, is_folder=False, storage_key=f"k/{name}")
            session.add(f)
        await session.commit()
        await session.refresh(u)
        return u


@pytest.mark.asyncio
async def test_search_basic(client, user):
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.get("/api/search?q=report", headers=h)
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


@pytest.mark.asyncio
async def test_search_with_type(client, user):
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.get("/api/search?q=photo&type=image", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_search_in_folder(client, user):
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.get(f"/api/search?q=report&folder_id={uuid.uuid4()}", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_search_empty_query(client, user):
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.get("/api/search?q=", headers=h)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_search_starred(client, user):
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.get("/api/search?q=notes&starred=true", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_search_sorted(client, user):
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.get("/api/search?q=report&sort=size", headers=h)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_search_no_trashed(client, user):
    from datetime import datetime, timezone
    async with TestingSessionLocal() as session:
        f = File(id=uuid.uuid4(), name="trashed_searchable.txt", owner_id=user.id, is_folder=False,
                 size=100, storage_key="k", is_trashed=True, trashed_at=datetime.now(timezone.utc))
        session.add(f)
        await session.commit()
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.get("/api/search?q=trashed_searchable", headers=h)
    assert resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_search_no_other_user(client, user):
    async with TestingSessionLocal() as session:
        other = User(id=uuid.uuid4(), email="other_search@example.com", name="Other",
                     password_hash=hash_password("p"), role="user", storage_used=0, storage_quota=5368709120, is_active=True)
        session.add(other)
        f = File(id=uuid.uuid4(), name="private_doc.txt", owner_id=other.id, is_folder=False,
                 size=100, storage_key="k")
        session.add(f)
        await session.commit()
    h = auth_headers(user.id, user.email, user.role)
    resp = await client.get("/api/search?q=private_doc", headers=h)
    assert resp.json()["total"] == 0
