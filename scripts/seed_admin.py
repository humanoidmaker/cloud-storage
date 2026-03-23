#!/usr/bin/env python3
"""Seed the default superadmin user."""
import asyncio
import uuid
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.database import async_session_factory, init_db
from app.models.user import User
from app.utils.hashing import hash_password
from sqlalchemy import select


async def seed():
    await init_db()
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.email == "admin@cloud_storage.local"))
        if result.scalar_one_or_none():
            print("Admin user already exists.")
            return

        admin = User(
            id=uuid.uuid4(),
            email="admin@cloud_storage.local",
            name="System Admin",
            password_hash=hash_password("admin123"),
            role="superadmin",
            storage_quota=0,  # unlimited
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        print(f"Admin user created: admin@cloud_storage.local / admin123")


if __name__ == "__main__":
    asyncio.run(seed())
