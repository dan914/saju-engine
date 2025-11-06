"""Pydantic Settings for saju-common package.

This module provides centralized configuration management using Pydantic Settings.
Environment variables can be used to override defaults using SAJU_ prefix.

Example:
    >>> from saju_common.settings import settings
    >>> print(settings.policy_root)  # Uses default or SAJU_POLICY_ROOT env var
    PosixPath('/path/to/repo')

    >>> # Override via environment
    >>> import os
    >>> os.environ['SAJU_POLICY_ROOT'] = '/custom/path'
    >>> settings = SajuSettings()  # Create new instance
    >>> print(settings.policy_root)
    PosixPath('/custom/path')
"""

from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_repo_root() -> Path:
    """Find repository root by looking for known markers.

    Searches upward from current file location for:
    - .git directory
    - pyproject.toml at repo root
    - saju_codex_batch_all_v2_6_signed directory

    Returns:
        Path to repository root

    Raises:
        FileNotFoundError: If repo root cannot be determined
    """
    current = Path(__file__).resolve()

    # Start from saju_common package directory
    # Go up: saju_common/ -> common/ -> services/ -> repo_root/
    candidate = current.parent.parent.parent.parent

    # Validate this is the repo root
    if (candidate / ".git").exists():
        return candidate
    if (candidate / "saju_codex_batch_all_v2_6_signed").exists():
        return candidate
    if (candidate / "pyproject.toml").exists() and (candidate / "services").exists():
        return candidate

    # Fallback: search upward
    for parent in current.parents:
        if (parent / ".git").exists():
            return parent
        if (parent / "saju_codex_batch_all_v2_6_signed").exists():
            return parent

    raise FileNotFoundError(
        "Could not determine repository root. "
        "Ensure this package is installed within the saju-engine repository."
    )


class SajuSettings(BaseSettings):
    """Global settings for saju-engine services.

    Configuration can be provided via:
    - Environment variables (SAJU_POLICY_ROOT, SAJU_LOG_LEVEL, etc.)
    - .env file in repository root
    - Programmatic override in code

    Attributes:
        policy_root: Base directory for policy files
        policy_dirs: List of policy subdirectories to search
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log message format string
        enable_tracing: Enable OpenTelemetry tracing
        service_name: Name of the current service (auto-detected if None)
    """

    model_config = SettingsConfigDict(
        env_prefix='SAJU_',
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
    )

    # Policy file configuration
    policy_root: Path = Field(
        default_factory=get_repo_root,
        description="Base directory for policy files (default: auto-detected repo root)"
    )

    policy_dirs: List[str] = Field(
        default=[
            "policy",
            "saju_codex_batch_all_v2_6_signed/policies",
            "saju_codex_addendum_v2/policies",
            "saju_codex_addendum_v2_1/policies",
            "saju_codex_blueprint_v2_6_SIGNED/policies",
            "saju_codex_v2_5_bundle/policies",
        ],
        description="Policy subdirectories to search (in order of priority)"
    )

    # Logging configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format string"
    )

    # Observability configuration
    enable_tracing: bool = Field(
        default=False,
        description="Enable OpenTelemetry distributed tracing"
    )

    service_name: Optional[str] = Field(
        default=None,
        description="Service name for tracing (auto-detected if None)"
    )

    # Rate limiting configuration
    enable_rate_limiting: bool = Field(
        default=False,
        description="Enable API rate limiting"
    )

    redis_url: Optional[str] = Field(
        default=None,
        description="Redis URL for distributed rate limiting (e.g., redis://localhost:6379)"
    )

    enable_atomic_rate_limiter: bool = Field(
        default=False,
        description="Enable Lua-based atomic operations for Redis-backed rate limiting",
    )

    forwarded_for_headers: List[str] = Field(
        default_factory=lambda: ["X-Forwarded-For"],
        description="Headers to inspect for proxied client IPs",
    )

    trusted_proxy_cidrs: List[str] = Field(
        default_factory=list,
        description="CIDR ranges representing trusted proxy hops",
    )

    # Service-specific overrides (can be extended by individual services)
    analysis_service_enabled: bool = Field(
        default=True,
        description="Enable analysis-service features"
    )

    def resolve_policy_path(self, filename: str) -> Path:
        """Resolve policy file path by searching configured directories.

        Args:
            filename: Policy filename to search for

        Returns:
            Full path to policy file

        Raises:
            FileNotFoundError: If policy file not found in any directory

        Example:
            >>> settings = SajuSettings()
            >>> path = settings.resolve_policy_path("strength_policy_v2.json")
            >>> print(path.exists())
            True
        """
        for policy_dir in self.policy_dirs:
            candidate = self.policy_root / policy_dir / filename
            if candidate.exists():
                return candidate

        # Build error message with all searched paths
        searched = [
            str(self.policy_root / policy_dir) for policy_dir in self.policy_dirs
        ]
        raise FileNotFoundError(
            f"Policy file not found: {filename}\n"
            f"Searched in:\n" +
            "\n".join(f"- {path}" for path in searched)
        )


# Global settings instance
# Can be imported and used throughout the application
settings = SajuSettings()
