from pathlib import Path
import json

import pytest

from scripts.audit_policy_files import _resolve_audit_date, generate_audit_report


def _create_policy_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path
    policy_dir = repo_root / "policy"
    policy_dir.mkdir()
    (policy_dir / "sample.json").write_text("{}", encoding="utf-8")
    return repo_root


def test_generate_audit_report_uses_iso_date(tmp_path):
    repo_root = _create_policy_repo(tmp_path)

    report = generate_audit_report(repo_root, output_file=None)

    assert report["audit_date"].count("-") == 2
    year, month, day = report["audit_date"].split("-")
    assert len(year) == 4 and len(month) == 2 and len(day) == 2


def test_generate_audit_report_accepts_override(tmp_path):
    repo_root = _create_policy_repo(tmp_path)

    report = generate_audit_report(repo_root, output_file=None, audit_date="2024-01-02")

    assert report["audit_date"] == "2024-01-02"


def test_resolve_audit_date_rejects_invalid_format():
    with pytest.raises(ValueError):
        _resolve_audit_date("invalid-date")
