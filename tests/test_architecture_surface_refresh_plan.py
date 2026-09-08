"""Tests for the stored-input analyzer refresh plan."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PLANNER_PATH = (
    PROJECT_ROOT / "evaluations/architecture-surface-coverage/plan_refresh.py"
)
SPEC = importlib.util.spec_from_file_location("surface_refresh_plan", PLANNER_PATH)
assert SPEC is not None and SPEC.loader is not None
planner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(planner)


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _add_component(
    root: Path,
    role: str,
    name: str,
    commit: str,
    *,
    behavioral_evidence: object = None,
) -> tuple[dict[str, object], dict[str, object]]:
    platform = "rhoai-3.6"
    key = f"{platform}/{name}"
    repository = f"https://example.test/{name}.git"
    analyzer_relative = f"{key}/.analyzer/component-architecture.json"
    document_relative = f"{key}.md"
    analyzer_path = root / analyzer_relative
    analyzer_path.parent.mkdir(parents=True, exist_ok=True)
    analyzer: dict[str, object] = {
        "schema_version": "1",
        "component": name,
        "repo": repository,
        "commit_sha": commit,
        "analyzer_version": "test-v1",
    }
    if behavioral_evidence is not None:
        analyzer["behavioral_evidence"] = behavioral_evidence
    analyzer_bytes = (json.dumps(analyzer, sort_keys=True) + "\n").encode()
    analyzer_path.write_bytes(analyzer_bytes)
    (analyzer_path.parent / "analyzer_architecture.md").write_text("# Analyzer\n")
    document_path = root / document_relative
    document_bytes = f"# {name}\n".encode()
    document_path.write_bytes(document_bytes)
    component = {
        "artifact_key": key,
        "platform": platform,
        "component": name,
        "primary_role": role,
        "repository": repository,
        "commit_sha": commit,
        "analyzer": analyzer_relative,
        "analyzer_sha256": _sha256(analyzer_bytes),
        "document": document_relative,
        "document_sha256": _sha256(document_bytes),
    }
    representative = {
        "artifact_key": key,
        "primary_role": role,
        "repository": repository,
        "commit_sha": commit,
        "analyzer": analyzer_relative,
        "document": document_relative,
    }
    return component, representative


def _fixture(tmp_path: Path) -> tuple[Path, dict[str, object]]:
    root = tmp_path / "architecture"
    root.mkdir()
    specs = [
        ("operator", "another-operator", "1" * 40, []),
        ("service", "api", "2" * 40, [{"kind": "route"}]),
        ("operator", "rhods-operator", "3" * 40, None),
        ("manifest", "manifests", "4" * 40, None),
        ("unknown", "unknown", "5" * 40, None),
    ]
    components = []
    representatives = []
    for role, name, commit, evidence in specs:
        component, representative = _add_component(
            root, role, name, commit, behavioral_evidence=evidence
        )
        components.append(component)
        representatives.append(representative)
    audit: dict[str, object] = {
        "schema_version": planner.AUDIT_SCHEMA_VERSION,
        "input": {"fingerprint_sha256": "a" * 64},
        "components": components,
        "representative_review_set": representatives,
    }
    return root, audit


def test_plan_pins_rhods_first_and_records_unavailable_inputs(tmp_path: Path) -> None:
    root, audit = _fixture(tmp_path)

    report = planner.build_refresh_plan(root, audit)

    assert [item["component"] for item in report["cohort"]] == [
        "rhods-operator",
        "another-operator",
        "api",
        "manifests",
    ]
    assert report["summary"]["roles"] == {
        "manifest": 1,
        "operator": 2,
        "service": 1,
    }
    assert report["summary"]["source_inputs"] == {
        "unavailable-under-architecture-only-constraint": 4
    }
    assert report["boundary"]["generated_architecture_modified"] is False
    assert report["boundary"]["revision_substitution_allowed"] is False
    assert report["selection"]["excluded_representatives"] == [
        {
            "artifact_key": "rhoai-3.6/unknown",
            "primary_role": "unknown",
            "reason": "outside-requested-operator-service-manifest-cohort",
        }
    ]
    assert all(
        item["regeneration"]["status"] == "not-run-source-input-unavailable"
        for item in report["cohort"]
    )
    assert (
        report["cohort"][0]["stored_analyzer"]["revision_status"]
        == "unavailable-in-stored-artifact"
    )


def test_plan_is_deterministic_and_fingerprints_all_stored_outputs(
    tmp_path: Path,
) -> None:
    root, audit = _fixture(tmp_path)

    first = planner.build_refresh_plan(root, audit)
    second = planner.build_refresh_plan(root, audit)

    assert first == second
    first_item = first["cohort"][0]
    assert [item["kind"] for item in first_item["stored_outputs"]] == [
        "rendered-analyzer-baseline",
        "structured-analyzer-output",
    ]
    assert all(len(item["sha256"]) == 64 for item in first_item["stored_outputs"])
    assert len(first_item["comparison_input_fingerprint_sha256"]) == 64
    assert len(first["input"]["selected_comparison_input_fingerprint_sha256"]) == 64


def test_plan_rejects_stale_audit_hash(tmp_path: Path) -> None:
    root, audit = _fixture(tmp_path)
    document = root / "rhoai-3.6/rhods-operator.md"
    document.write_text("changed\n")

    with pytest.raises(planner.RefreshPlanError, match="document hash"):
        planner.build_refresh_plan(root, audit)


def test_plan_rejects_revision_or_repository_substitution(tmp_path: Path) -> None:
    root, audit = _fixture(tmp_path)
    component = next(
        item for item in audit["components"] if item["component"] == "rhods-operator"
    )
    component["commit_sha"] = "main"
    representative = next(
        item
        for item in audit["representative_review_set"]
        if item["artifact_key"].endswith("/rhods-operator")
    )
    representative["commit_sha"] = "main"

    with pytest.raises(planner.RefreshPlanError, match="exact SHA"):
        planner.build_refresh_plan(root, audit)


def test_markdown_states_measurement_limit(tmp_path: Path) -> None:
    root, audit = _fixture(tmp_path)

    rendered = planner.render_markdown(planner.build_refresh_plan(root, audit))

    assert "regeneration was not run" in rendered
    assert "rhods-operator-first" in rendered
    assert "cannot be reconstructed from these files" in rendered


def test_cli_rejects_outputs_inside_architecture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, audit = _fixture(tmp_path)
    audit_path = tmp_path / "audit.json"
    audit_path.write_text(json.dumps(audit))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(PLANNER_PATH),
            "--architecture-root",
            str(root),
            "--rollout-audit",
            str(audit_path),
            "--output-json",
            str(root / "plan.json"),
            "--output-markdown",
            str(tmp_path / "plan.md"),
        ],
    )

    with pytest.raises(SystemExit, match="2"):
        planner.main()
    assert not (root / "plan.json").exists()
