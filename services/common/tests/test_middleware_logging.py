"""Tests for proxy-aware client identity in RequestLoggingMiddleware."""

import logging

import ipaddress

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from saju_common.client_identity import ProxyConfig
from saju_common.middleware import RequestLoggingMiddleware


def _make_app(proxy_config: ProxyConfig | None):
    app = FastAPI()

    @app.get("/echo")
    def echo():
        return JSONResponse({"ok": True})

    app.add_middleware(
        RequestLoggingMiddleware,
        exclude_paths=[],
        proxy_config=proxy_config,
    )

    return app


def test_request_logging_uses_forwarded_header(caplog):
    config = ProxyConfig(
        headers=("X-Forwarded-For",),
        trusted_cidrs=(ipaddress.ip_network('10.0.0.0/8'),),
    )

    app = _make_app(config)

    with caplog.at_level(logging.INFO, logger="saju_common.middleware"):
        client = TestClient(app)
        client.get(
            "/echo",
            headers={"X-Forwarded-For": "198.51.100.77, 10.0.0.1"},
        )

    start_log = next(entry for entry in caplog.records if entry.event == "request_start")
    assert start_log.client_host == "198.51.100.77"


def test_request_logging_defaults_to_client_host(caplog):
    app = _make_app(None)

    with caplog.at_level(logging.INFO, logger="saju_common.middleware"):
        client = TestClient(app)
        client.get("/echo")

    start_log = next(entry for entry in caplog.records if entry.event == "request_start")
    assert start_log.client_host.startswith("testclient")
