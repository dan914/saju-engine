"""Tests for Pydantic Settings module."""

import os
from pathlib import Path

import pytest

from saju_common.settings import SajuSettings, get_repo_root


def test_get_repo_root():
    """Test repository root detection."""
    root = get_repo_root()

    assert isinstance(root, Path)
    assert root.exists()
    assert (root / ".git").exists() or (root / "saju_codex_batch_all_v2_6_signed").exists()


def test_settings_default_values():
    """Test default settings values."""
    settings = SajuSettings()

    assert isinstance(settings.policy_root, Path)
    assert settings.policy_root.exists()
    assert len(settings.policy_dirs) > 0
    assert "saju_codex_batch_all_v2_6_signed/policies" in settings.policy_dirs
    assert settings.log_level == "INFO"
    assert settings.enable_tracing is False


def test_resolve_policy_path_success():
    """Test successful policy file resolution."""
    settings = SajuSettings()

    # Test known policy files
    test_files = [
        "strength_policy_v2.json",
        "relation_policy.json",
        "shensha_v2_policy.json",
        "climate_map_v1.json",
    ]

    for filename in test_files:
        path = settings.resolve_policy_path(filename)
        assert path.exists(), f"Policy file should exist: {filename}"
        assert path.is_file(), f"Policy should be a file: {filename}"
        assert filename in path.name, f"Path should contain filename: {filename}"


def test_resolve_policy_path_not_found():
    """Test policy file not found error."""
    settings = SajuSettings()

    with pytest.raises(FileNotFoundError, match="Policy file not found"):
        settings.resolve_policy_path("nonexistent_policy.json")


def test_resolve_policy_path_priority():
    """Test policy directory search priority."""
    settings = SajuSettings()

    # If a file exists in multiple dirs, should return first match
    path = settings.resolve_policy_path("strength_policy_v2.json")
    assert path.exists()

    # Path should contain one of the configured policy directories
    path_str = str(path)
    assert any(policy_dir in path_str for policy_dir in settings.policy_dirs)


def test_settings_env_override(monkeypatch):
    """Test settings can be overridden via environment variables."""
    # Create temporary directory for testing
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set environment variable
        monkeypatch.setenv("SAJU_POLICY_ROOT", tmpdir)

        # Create new settings instance
        settings = SajuSettings()

        assert settings.policy_root == Path(tmpdir)


def test_settings_log_level_override(monkeypatch):
    """Test log level can be overridden."""
    monkeypatch.setenv("SAJU_LOG_LEVEL", "DEBUG")

    settings = SajuSettings()

    assert settings.log_level == "DEBUG"


def test_settings_enable_tracing_override(monkeypatch):
    """Test tracing can be enabled via environment."""
    monkeypatch.setenv("SAJU_ENABLE_TRACING", "true")

    settings = SajuSettings()

    assert settings.enable_tracing is True


def test_settings_service_name_override(monkeypatch):
    """Test service name can be set via environment."""
    monkeypatch.setenv("SAJU_SERVICE_NAME", "test-service")

    settings = SajuSettings()

    assert settings.service_name == "test-service"


def test_settings_case_insensitive(monkeypatch):
    """Test environment variables are case insensitive."""
    monkeypatch.setenv("saju_log_level", "warning")  # lowercase

    settings = SajuSettings()

    # Pydantic Settings preserves the case provided
    assert settings.log_level == "warning"


def test_resolve_policy_path_relative_to_root():
    """Test resolved paths are relative to policy root."""
    settings = SajuSettings()

    path = settings.resolve_policy_path("strength_policy_v2.json")

    # Path should be under policy_root
    assert path.is_relative_to(settings.policy_root)


def test_policy_dirs_order():
    """Test policy directories are searched in order."""
    settings = SajuSettings()

    # First directory should be "policy" (canonical location)
    assert settings.policy_dirs[0] == "policy"

    # Legacy directories should be after canonical
    assert "saju_codex_batch_all_v2_6_signed/policies" in settings.policy_dirs


def test_settings_immutable():
    """Test settings can be reused without side effects."""
    settings1 = SajuSettings()
    settings2 = SajuSettings()

    # Both should resolve to same paths
    path1 = settings1.resolve_policy_path("strength_policy_v2.json")
    path2 = settings2.resolve_policy_path("strength_policy_v2.json")

    assert path1 == path2
