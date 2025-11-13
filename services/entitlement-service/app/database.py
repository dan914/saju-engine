# -*- coding: utf-8 -*-
"""
Database configuration and session management
SQLAlchemy 2.0 async with PostgreSQL
"""

import os

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from .config import settings


db_url = make_url(settings.database_url)
engine_kwargs = {
    "pool_pre_ping": True,
    "echo": False,
}
disable_pool = os.getenv("ENTITLEMENT_TEST_DISABLE_POOL") == "1"
if db_url.drivername.startswith("sqlite") or disable_pool:
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

# Create async engine
engine = create_async_engine(settings.database_url, **engine_kwargs)

# Create async session factory
SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""
    pass
