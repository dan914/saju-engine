"""Dialect-aware SQLAlchemy type shims for cross-database testing."""

from __future__ import annotations

import uuid

from sqlalchemy.dialects.postgresql import INET as PGInet
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.types import CHAR, String, TypeDecorator


class GUID(TypeDecorator):
    """Platform-independent GUID/UUID type."""

    impl = PGUUID
    cache_ok = True

    def __init__(self, *, as_uuid: bool = True) -> None:
        self.as_uuid = as_uuid
        super().__init__()

    def load_dialect_impl(self, dialect):  # type: ignore[override]
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PGUUID(as_uuid=self.as_uuid))
        length = 36 if self.as_uuid else 32
        return dialect.type_descriptor(CHAR(length))

    def process_bind_param(self, value, dialect):  # type: ignore[override]
        if value is None:
            return value
        if self.as_uuid and isinstance(value, uuid.UUID):
            return str(value)
        return value

    def process_result_value(self, value, dialect):  # type: ignore[override]
        if value is None or not self.as_uuid:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


class Inet(TypeDecorator):
    """INET that degrades to VARCHAR for SQLite-based tests."""

    impl = PGInet
    cache_ok = True

    def load_dialect_impl(self, dialect):  # type: ignore[override]
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PGInet())
        # Enough to store IPv6 addresses
        return dialect.type_descriptor(String(64))
