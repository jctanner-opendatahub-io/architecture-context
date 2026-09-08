"""Tests for replaying the recorded analyzer-refresh audit."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVALUATION_DIR = PROJECT_ROOT / "evaluations/architecture-surface-coverage"
SCRIPT_PATH = EVALUATION_DIR / "audit_refreshed.py"
sys.path.insert(0, str(EVALUATION_DIR))
SPEC = importlib.util.spec_from_file_location("surface_refreshed_audit", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
refreshed_audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(refreshed_audit)
sys.path.pop(0)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(tmp_path: Path) -> tuple[dict[str, object], Path]:
    architecture = tmp_path / "architecture"
    document = architecture / "source-platform/example.md"
    document.parent.mkdir(parents=True)
    document.write_text("# Example\n")
    analyzer = tmp_path / "recorded/example.json"
    analyzer.parent.mkdir()
    analyzer.write_text(
        json.dumps(
            {
                "component": "example",
                "repo": "https://example.test/example.git",
                "commit_sha": "1" * 40,
                "analyzer_version": "current",
                "behavioral_evidence": [],
            }
        )
    )
    result: dict[str, object] = {
        "schema_version": refreshed_audit.RESULT_SCHEMA_VERSION,
        "configuration": {"platform": "refreshed-platform"},
        "summary": {"behavioral_evidence_states": {"present-empty": 1}},
        "cohort": [
            {
                "component": "example",
                "comparison_document": {
                    "path": "source-platform/example.md",
                    "sha256": _sha256(document),
                },
                "refreshed_analyzer": {
                    "path": "recorded/example.json",
                    "sha256": _sha256(analyzer),
                },
            }
        ],
    }
    return result, architecture


def test_refreshed_audit_replays_recorded_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result, architecture = _fixture(tmp_path)
    monkeypatch.setattr(refreshed_audit, "PROJECT_ROOT", tmp_path)

    report = refreshed_audit.build_refreshed_audit(result, architecture)

    assert report["input"]["architecture_root"] == (
        refreshed_audit.RECORDED_ROOT_LABEL
    )
    assert report["summary"]["eligible_pairs"] == 1
    assert report["summary"]["behavioral_evidence"]["field_states"] == {
        "present-empty": 1
    }
    assert "refresh-stored-behavioral-evidence" not in {
        item["id"] for item in report["follow_up_priorities"]
    }


def test_refreshed_audit_rejects_changed_recorded_analyzer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result, architecture = _fixture(tmp_path)
    monkeypatch.setattr(refreshed_audit, "PROJECT_ROOT", tmp_path)
    (tmp_path / "recorded/example.json").write_text("{}\n")

    with pytest.raises(refreshed_audit.RefreshedAuditError, match="hash mismatch"):
        refreshed_audit.build_refreshed_audit(result, architecture)
