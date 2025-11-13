"""Shared pytest fixtures for entitlement service tests."""

from __future__ import annotations

import os
import sys
import asyncio
import time
import warnings
from pathlib import Path
from typing import AsyncIterator

import httpx
import pytest
import pytest_asyncio
try:  # pragma: no cover - optional dependency during tests
    from fakeredis.aioredis import FakeRedis
except ModuleNotFoundError:  # pragma: no cover - fallback when fakeredis unavailable
    class FakeRedis:  # type: ignore[too-few-public-methods]
        """Minimal async Redis stub for offline tests."""

        def __init__(self) -> None:
            self._data: dict[str, bytes] = {}
            self._expiry: dict[str, float] = {}

        async def flushall(self) -> None:
            self._data.clear()
            self._expiry.clear()

        async def incr(self, key: str) -> int:
            self._expire_if_needed(key)
            value = int(self._data.get(key, b"0")) + 1
            self._data[key] = str(value).encode()
            return value

        async def expire(self, key: str, seconds: int) -> None:
            self._expiry[key] = time.time() + seconds

        async def ttl(self, key: str) -> int:
            self._expire_if_needed(key)
            expires = self._expiry.get(key)
            if expires is None:
                return -1
            return max(int(expires - time.time()), 0)

        async def get(self, key: str) -> bytes | None:
            self._expire_if_needed(key)
            return self._data.get(key)

        async def set(self, key: str, value, ex: int | None = None) -> None:
            if isinstance(value, (bytes, bytearray)):
                payload = bytes(value)
            else:
                payload = str(value).encode()
            self._data[key] = payload
            if ex:
                self._expiry[key] = time.time() + ex

        def _expire_if_needed(self, key: str) -> None:
            expires = self._expiry.get(key)
            if expires and expires <= time.time():
                self._data.pop(key, None)
                self._expiry.pop(key, None)

from fastapi import Request
from httpx import ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.exc import SQLAlchemyError

# Configure test database/redis URLs before importing app modules
SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

TEST_DB_PATH = Path(__file__).with_suffix(".sqlite")
DEFAULT_POSTGRES_TEST_URL = "postgresql+asyncpg://entitlements:entitlements@localhost:5432/entitlements_test"
SQLITE_FALLBACK_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("ENTITLEMENT_TEST_DISABLE_POOL", "1")
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

USING_SQLITE_FALLBACK = False


async def _ping_database(url: str) -> None:
    """Ensure the target database is reachable before importing app modules."""

    engine = create_async_engine(url)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    finally:
        await engine.dispose()


def _configure_database_url() -> str:
    global USING_SQLITE_FALLBACK

    target_url = os.getenv("ENTITLEMENT_TEST_DATABASE_URL", DEFAULT_POSTGRES_TEST_URL)
    force_sqlite = os.getenv("ENTITLEMENT_TEST_FORCE_SQLITE") == "1"

    if not force_sqlite and target_url.startswith("postgresql"):
        try:
            asyncio.run(asyncio.wait_for(_ping_database(target_url), timeout=2.0))
            os.environ["DATABASE_URL"] = target_url
            return target_url
        except (SQLAlchemyError, OSError, RuntimeError, asyncio.TimeoutError) as exc:
            warnings.warn(
                f"Entitlement tests: Postgres DSN {target_url} unavailable ({exc}); "
                "falling back to SQLite for local execution.",
                RuntimeWarning,
            )
    USING_SQLITE_FALLBACK = True
    fallback = os.getenv("ENTITLEMENT_TEST_SQLITE_URL", SQLITE_FALLBACK_URL)
    os.environ["DATABASE_URL"] = fallback
    return fallback


DATABASE_URL = _configure_database_url()

from app.database import Base, engine  # noqa: E402  (after env vars)
from app.main import (
    AuthenticatedUser,
    SessionLocal,
    app,
    get_admin_user,
    get_current_user,
    get_db,
    get_redis,
)
from .utils import create_user_with_entitlement  # noqa: E402

# Use valid UUID for default test user (middleware expects UUID format)
DEFAULT_TEST_USER = "00000000-0000-0000-0000-000000000001"


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database() -> AsyncIterator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(autouse=True)
async def clean_database() -> AsyncIterator[None]:
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    yield


@pytest.fixture(scope="function")
def fake_redis() -> FakeRedis:
    """Create a new FakeRedis instance for each test to avoid event loop conflicts."""
    redis = FakeRedis()
    return redis


@pytest_asyncio.fixture(autouse=True)
async def reset_fake_redis(fake_redis: FakeRedis) -> AsyncIterator[None]:
    """Reset FakeRedis before each test (no-op since we create fresh instance per test)."""
    # Since we now create a fresh instance per test, flushall is redundant
    # but kept for backward compatibility in case tests rely on explicit reset
    await fake_redis.flushall()
    yield


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def test_user_id(db_session: AsyncSession) -> AsyncIterator[str]:
    user_id = await create_user_with_entitlement(db_session)
    yield user_id


def _build_user(user_id: str) -> AuthenticatedUser:
    return AuthenticatedUser(user_id=user_id, claims={"roles": ["admin"]}, token="debug")


@pytest.fixture(autouse=True)
def override_dependencies(fake_redis: FakeRedis) -> AsyncIterator[None]:
    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with SessionLocal() as session:
            yield session

    async def override_get_redis() -> FakeRedis:
        return fake_redis

    async def override_current_user(
        request: Request,
        authorization: str | None = None,
        x_debug_user: str | None = None,
    ) -> AuthenticatedUser:
        user_id = request.headers.get("x-test-user") or x_debug_user or DEFAULT_TEST_USER
        request.state.user_id = user_id
        return _build_user(user_id)

    async def override_admin_user(
        request: Request,
        authorization: str | None = None,
        x_debug_user: str | None = None,
    ) -> AuthenticatedUser:
        user_id = request.headers.get("x-test-user") or DEFAULT_TEST_USER
        request.state.user_id = user_id
        return _build_user(user_id)

    app.state.db = SessionLocal
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis
    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_admin_user] = override_admin_user
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def api_client(fake_redis: FakeRedis) -> AsyncIterator[httpx.AsyncClient]:
    # Note: lifespan parameter requires httpx>=0.28.0, omitted for compatibility
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
