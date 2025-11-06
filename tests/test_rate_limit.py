import logging
import sys
import types

from saju_common.rate_limit import (
    TokenBucketRateLimiter,
    setup_rate_limiting,
)


class _ExplodingRedisClient:
    """Redis client stub that raises with a secret-bearing message."""

    def pipeline(self):
        raise RuntimeError("redis failure redis://user:secret@host:6379/0")


def test_setup_rate_limiting_redacts_credentials(caplog, monkeypatch):
    """Connected-to-Redis log lines should not leak credentials."""

    class DummyRedisClient:
        def ping(self):
            return True

    def fake_from_url(url, decode_responses=True):  # noqa: D401 - simple stub
        assert decode_responses is True
        return DummyRedisClient()

    stub_module = types.SimpleNamespace(from_url=fake_from_url)
    monkeypatch.setitem(sys.modules, "redis", stub_module)

    with caplog.at_level(logging.INFO, logger="saju_common.rate_limit"):
        setup_rate_limiting("redis://admin:supersecret@localhost:6379/0")

    assert "supersecret" not in caplog.text
    assert "redis://***@localhost:6379/0" in caplog.text


def test_rate_limit_error_logs_mask_credentials(caplog):
    """Error logs produced by limiter failures must redact Redis secrets."""

    limiter = TokenBucketRateLimiter(
        capacity=1,
        refill_rate=1.0,
        redis_client=_ExplodingRedisClient(),
    )

    with caplog.at_level(logging.ERROR, logger="saju_common.rate_limit"):
        allowed, retry_after = limiter.check_rate_limit("user:123")

    assert allowed is True
    assert retry_after == 0
    assert "host:6379/0" in caplog.text
    assert "redis://***@host:6379/0" in caplog.text
    assert "user:secret" not in caplog.text
