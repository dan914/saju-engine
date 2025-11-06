"""Unit tests for proxy-aware client identity utilities."""

import ipaddress

import pytest

from saju_common.client_identity import ProxyConfig, extract_client_ip


class DummySettings:
    forwarded_for_headers = ["X-Forwarded-For", "X-Real-IP"]
    trusted_proxy_cidrs = ["10.0.0.0/8", "192.168.0.0/16"]


def test_proxy_config_from_settings_parses_headers_and_cidrs():
    config = ProxyConfig.from_settings(DummySettings())

    assert config.headers == ("X-Forwarded-For", "X-Real-IP")
    assert any(isinstance(net, ipaddress.IPv4Network) for net in config.trusted_cidrs)


def test_extract_client_ip_prefers_first_untrusted_hop():
    config = ProxyConfig.from_settings(DummySettings())
    headers = {
        "X-Forwarded-For": "198.51.100.23, 10.0.0.5",
    }

    assert extract_client_ip(headers, "203.0.113.8", config) == "198.51.100.23"


def test_extract_client_ip_falls_back_when_all_trusted():
    config = ProxyConfig.from_settings(DummySettings())
    headers = {
        "X-Forwarded-For": "10.10.10.1, 192.168.1.4",
    }

    assert extract_client_ip(headers, "203.0.113.8", config) == "203.0.113.8"


@pytest.mark.parametrize(
    "raw_header",
    [
        "",  # empty header
        "garbage",
        "  ",
    ],
)
def test_extract_client_ip_handles_invalid_entries(raw_header):
    config = ProxyConfig(headers=("X-Forwarded-For",), trusted_cidrs=())
    headers = {"X-Forwarded-For": raw_header}

    assert extract_client_ip(headers, "198.51.100.1", config) == "198.51.100.1"


def test_extract_client_ip_checks_multiple_headers():
    config = ProxyConfig.from_settings(DummySettings())
    headers = {
        "X-Forwarded-For": "10.0.0.1",
        "X-Real-IP": "198.51.100.99",
    }

    assert extract_client_ip(headers, None, config) == "198.51.100.99"
