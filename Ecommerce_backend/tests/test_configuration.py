import logging

import pytest
from pydantic import ValidationError
from sqlalchemy.pool import NullPool, QueuePool

from app.core.config import Settings, settings
from app.core.logging import configure_logging
from app.db.database import create_database_engine


def test_debug_setting_controls_logging_threshold(monkeypatch):
    monkeypatch.setattr(settings, "DEBUG", True)
    configure_logging()
    assert logging.getLogger().getEffectiveLevel() == logging.DEBUG

    monkeypatch.setattr(settings, "DEBUG", False)
    configure_logging()
    assert logging.getLogger().getEffectiveLevel() == logging.INFO


def test_queue_pool_uses_configured_limits(monkeypatch):
    monkeypatch.setattr(settings, "DB_POOL_MODE", "queue")
    monkeypatch.setattr(settings, "DB_POOL_SIZE", 3)
    monkeypatch.setattr(settings, "DB_MAX_OVERFLOW", 4)
    engine = create_database_engine("postgresql://user:pass@localhost/test")

    assert isinstance(engine.pool, QueuePool)
    assert engine.pool.size() == 3
    assert engine.pool._max_overflow == 4
    engine.dispose()


def test_null_pool_can_be_selected(monkeypatch):
    monkeypatch.setattr(settings, "DB_POOL_MODE", "null")
    engine = create_database_engine("postgresql://user:pass@localhost/test")

    assert isinstance(engine.pool, NullPool)
    engine.dispose()


def test_queue_pool_size_cannot_be_unbounded():
    with pytest.raises(ValidationError):
        Settings(
            DATABASE_URL="postgresql://user:pass@localhost/test",
            REDIS_URL="redis://localhost:6379/15",
            SECRET_KEY="test-secret-key-with-at-least-32-bytes",
            DB_POOL_SIZE=0,
        )