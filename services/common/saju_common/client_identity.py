"""Utilities for deriving the real client identity behind trusted proxies."""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ProxyConfig:
    headers: tuple[str, ...]
    trusted_cidrs: tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...]

    @classmethod
    def from_settings(cls, settings) -> "ProxyConfig":
        header_names = tuple(
            h.strip() for h in getattr(settings, "forwarded_for_headers", ["X-Forwarded-For"])
        )
        cidrs: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
        for cidr in getattr(settings, "trusted_proxy_cidrs", []):
            cidrs.append(ipaddress.ip_network(cidr, strict=False))
        return cls(header_names, tuple(cidrs))


def _is_trusted(address: str, trusted_cidrs: Iterable[ipaddress.IPv4Network | ipaddress.IPv6Network]) -> bool:
    try:
        parsed = ipaddress.ip_address(address)
    except ValueError:
        return False

    for network in trusted_cidrs:
        if parsed in network:
            return True
    return False


def extract_client_ip(headers, client_host: str | None, config: ProxyConfig) -> str | None:
    for header in config.headers:
        raw = headers.get(header)
        if not raw:
            continue

        # X-Forwarded-For lists are comma separated; take left-most untrusted IP
        parts = [part.strip() for part in raw.split(",") if part.strip()]
        for candidate in parts:
            # Validate that candidate is a valid IP address
            try:
                ipaddress.ip_address(candidate)
            except ValueError:
                # Invalid IP address, skip to next candidate
                continue

            if not _is_trusted(candidate, config.trusted_cidrs):
                return candidate
        # All entries trusted or invalid; fall back to downstream host

    return client_host

