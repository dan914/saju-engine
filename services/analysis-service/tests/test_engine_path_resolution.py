"""Regression tests for filesystem-agnostic engine bootstrapping."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core import AnalysisEngine
from tests.helpers import build_sample_request


@pytest.mark.parametrize("chdir_target", ["repo_root", "temp_dir"])
def test_analysis_engine_initializes_independent_of_cwd(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    chdir_target: str,
) -> None:
    """Ensure policy/data loading resolves correctly without cwd assumptions."""
    repo_root = Path(__file__).resolve().parents[5]
    target = repo_root if chdir_target == "repo_root" else tmp_path
    monkeypatch.chdir(target)

    engine = AnalysisEngine()
    request = build_sample_request()
    response = engine.analyze(request)

    assert response.status == "success"
    assert response.ten_gods.policy_version is not None
