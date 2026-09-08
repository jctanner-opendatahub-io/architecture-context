"""Tests for recording an isolated analyzer refresh."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = (
    PROJECT_ROOT / "evaluations/architecture-surface-coverage/record_refresh.py"
)
SPEC = importlib.util.spec_from_file_location("surface_refresh_result", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
recorder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(recorder)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(tmp_path: Path) -> dict[str, object]:
    architecture = tmp_path / "architecture"
    document = architecture / "old/example.md"
    document.parent.mkdir(parents=True)
    document.write_text("# Example\n")
    component_map = architecture / "rhoai-3.6-ea.2/component-map.json"
    component_map.parent.mkdir(parents=True)
    component_map.write_text("{}\n")

    refreshed = tmp_path / "isolated/rhoai-3.6-ea.2/example/.analyzer"
    refreshed.mkdir(parents=True)
    analyzer = refreshed / "component-architecture.json"
    analyzer.write_text(
        json.dumps(
            {
                "component": "example",
                "repo": "https://example.test/example.git",
                "commit_sha": "1" * 40,
                "extracted_at": "2026-09-05T00:00:00Z",
                "analyzer_version": "current",
                "behavioral_evidence": [],
            }
        )
    )
    (refreshed / "analyzer_architecture.md").write_text("# Analyzer\n")
    (refreshed / "analyzer_synthesis_context.md").write_text("# Context\n")
    (refreshed / ".render_meta.json").write_text("{}\n")
    schemas = refreshed / "contracts/schemas"
    schemas.mkdir(parents=True)
    (schemas / "example.json").write_text("{}\n")

    plan_path = tmp_path / "refresh-input-plan.json"
    plan = {
        "cohort": [
            {
                "sequence": 1,
                "component": "example",
                "primary_role": "service",
                "source_identity": {
                    "repository": "https://example.test/example.git",
                    "commit_sha": "1" * 40,
                    "status": "pinned-from-stored-analyzer",
                },
                "comparison_document": {
                    "path": "old/example.md",
                    "sha256": _sha256(document),
                },
            }
        ]
    }
    plan_path.write_text(json.dumps(plan))
    binary = tmp_path / "arch-analyzer"
    binary.write_bytes(b"binary")
    source = tmp_path / "src/arch-analyzer/main.go"
    source.parent.mkdir(parents=True)
    source.write_text("package main\n")
    return {
        "architecture": architecture,
        "refreshed": tmp_path / "isolated",
        "plan": plan,
        "plan_path": plan_path,
        "binary": binary,
        "source": source,
    }


def _stub_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(recorder, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        recorder,
        "_find_checkout",
        lambda roots, repository, commit: {
            "path": "checkouts/example",
            "origin": repository,
            "head": commit,
            "clean": True,
        },
    )

    def fake_git(path: Path, *args: str) -> str:
        if args[:2] == ("rev-parse", "HEAD"):
            return "2" * 40
        if args and args[0] == "ls-files":
            return "src/arch-analyzer/main.go"
        if args[:2] == ("diff", "--name-only"):
            return ""
        raise AssertionError(args)

    monkeypatch.setattr(recorder, "_run_git", fake_git)
    monkeypatch.setattr(
        recorder,
        "_run_git_lines",
        lambda path, *args: [" M src/arch-analyzer/main.go"],
    )

    def fake_run(args, **kwargs):
        if args[0] == "git":
            return SimpleNamespace(stdout=b"diff")
        if args[:2] == ["go", "version"]:
            return SimpleNamespace(stdout="go version test\n")
        raise AssertionError(args)

    monkeypatch.setattr(subprocess, "run", fake_run)


def test_record_refresh_validates_and_copies_current_empty_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _fixture(tmp_path)
    _stub_environment(monkeypatch, tmp_path)
    output_dir = tmp_path / "recorded"

    report = recorder.build_refresh_result(
        input_plan=fixture["plan"],
        input_plan_path=fixture["plan_path"],
        architecture_root=fixture["architecture"],
        refreshed_root=fixture["refreshed"],
        checkout_roots=[tmp_path / "checkouts"],
        output_dir=output_dir,
        analyzer_binary=fixture["binary"],
        platform="rhoai-3.6-ea.2",
        distribution="rhoai",
    )

    assert report["summary"] == {
        "artifacts": 1,
        "behavioral_evidence_states": {"present-empty": 1},
        "behavioral_evidence_records": 0,
        "schemas": 1,
    }
    assert report["analyzer"]["source_file_count"] == 1
    assert report["analyzer"]["source_tree_clean"] is False
    assert (output_dir / "example.json").is_file()


def test_record_refresh_rejects_refreshed_commit_substitution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _fixture(tmp_path)
    _stub_environment(monkeypatch, tmp_path)
    analyzer = (
        fixture["refreshed"]
        / "rhoai-3.6-ea.2/example/.analyzer/component-architecture.json"
    )
    payload = json.loads(analyzer.read_text())
    payload["commit_sha"] = "3" * 40
    analyzer.write_text(json.dumps(payload))

    with pytest.raises(recorder.RefreshResultError, match="commit mismatch"):
        recorder.build_refresh_result(
            input_plan=fixture["plan"],
            input_plan_path=fixture["plan_path"],
            architecture_root=fixture["architecture"],
            refreshed_root=fixture["refreshed"],
            checkout_roots=[tmp_path / "checkouts"],
            output_dir=tmp_path / "recorded",
            analyzer_binary=fixture["binary"],
            platform="rhoai-3.6-ea.2",
            distribution="rhoai",
        )
