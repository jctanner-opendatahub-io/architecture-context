"""Tests for the read-only architecture surface rollout audit."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUDIT_PATH = (
    PROJECT_ROOT / "evaluations/architecture-surface-coverage/audit_tree.py"
)
SPEC = importlib.util.spec_from_file_location("surface_rollout_audit", AUDIT_PATH)
assert SPEC is not None and SPEC.loader is not None
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def _write_component(
    platform: Path,
    name: str,
    analyzer: dict[str, object],
    *,
    document: str = "# Component\n",
) -> None:
    (platform / f"{name}.md").write_text(document)
    analyzer_path = platform / name / ".analyzer/component-architecture.json"
    analyzer_path.parent.mkdir(parents=True)
    analyzer_path.write_text(json.dumps(analyzer))


def _audit_fixture(tmp_path: Path) -> Path:
    root = tmp_path / "architecture"
    platform = root / "p1"
    platform.mkdir(parents=True)

    common = {
        "repo": "https://example.test/operator.git",
        "analyzer_version": "test-v1",
        "entrypoints": [
            {
                "name": "manager",
                "type": "controller-runtime operator",
                "source": "cmd/main.go:10",
            }
        ],
        "behavioral_evidence": [
            {
                "kind": "conditional-metrics-enforcement",
                "identity": "controller-runtime metrics",
                "status": "observed",
                "source": "cmd/main.go:10",
            },
            {
                "kind": "named-watch-predicate",
                "watched_gvk": "/v1/Namespace",
                "status": "unresolved",
                "source": "internal/watch.go:20",
            },
        ],
        "gap_evidence_index": {
            "authentication": [
                {
                    "status": "candidate",
                    "question": "Where is auth enforced?",
                    "source": "cmd/main.go",
                    "line_range": "10-20",
                }
            ]
        },
    }
    _write_component(
        platform,
        "operator",
        common,
        document="# Component\n\nEvidence at cmd/main.go.\n",
    )
    _write_component(
        platform,
        "service",
        {
            "repo": "https://example.test/service.git",
            "http_endpoints": [
                {"path": "/ready", "source": "internal/server.go:22"}
            ],
        },
    )
    _write_component(
        platform,
        "manifest",
        {
            "repo": "https://example.test/manifest.git",
            "deployments": [
                {"name": "worker", "source": "config/deployment.yaml:1"}
            ],
        },
    )
    _write_component(
        platform,
        "unknown",
        {
            "repo": "https://example.test/unknown.git",
            "category_coverage": {
                "fips_compliance": {"fact_count": 0, "status": "none"}
            },
        },
    )

    sidecar = platform / "service/.generation/SURFACE_COVERAGE.json"
    sidecar.parent.mkdir(parents=True)
    sidecar.write_text(json.dumps({"schema_version": audit.COVERAGE_SCHEMA_VERSION}))

    (platform / "without-analyzer.md").write_text("# Missing analyzer\n")
    orphan = platform / "without-document/.analyzer/component-architecture.json"
    orphan.parent.mkdir(parents=True)
    orphan.write_text("{}")
    (platform / "invalid.md").write_text("# Invalid analyzer\n")
    invalid = platform / "invalid/.analyzer/component-architecture.json"
    invalid.parent.mkdir(parents=True)
    invalid.write_text("[]")
    legacy = root / "rhoai-3.5"
    legacy.mkdir()
    (legacy / "legacy.md").write_text("# Legacy full-control summary\n")
    (root / "alias").symlink_to("p1", target_is_directory=True)
    return root


def test_audit_classifies_physical_corpus_without_alias_duplication(
    tmp_path: Path,
) -> None:
    root = _audit_fixture(tmp_path)

    report = audit.audit_architecture_tree(root)

    assert report["summary"] == {
        "canonical_component_documents": 7,
        "project_arch_analyzer_artifacts": 6,
        "eligible_pairs": 4,
        "unique_repository_identities": 4,
        "duplicate_repository_artifacts": 0,
        "documents_without_project_arch_analyzer": 2,
        "project_arch_analyzers_without_document": 1,
        "invalid_analyzers": 1,
        "platform_aliases_excluded": 1,
        "surface_occurrences": 6,
        "roles": {
            "manifest": 1,
            "operator": 1,
            "service": 1,
            "unknown": 1,
        },
        "primary_roles": {
            "manifest": 1,
            "operator": 1,
            "service": 1,
            "unknown": 1,
        },
        "priorities": {"high": 1, "required": 5},
        "sidecars": {
            "missing-legacy-telemetry": 3,
            "present-unvalidated": 1,
        },
        "behavioral_evidence": {
            "field_states": {"field-absent": 3, "present-records": 1},
            "record_count": 2,
            "kinds": {
                "conditional-metrics-enforcement": 1,
                "named-watch-predicate": 1,
            },
            "statuses": {"observed": 1, "unresolved": 1},
        },
        "generic_gap_candidate_count": 1,
        "generation_cohorts": {
            "external-architecture-analyzer-full-llm": 1,
            "no-project-arch-analyzer-artifact-unclassified": 1,
            "project-arch-analyzer-invalid-pairs": 1,
            "project-arch-analyzer-valid-pairs": 4,
        },
    }
    assert report["excluded_inputs"]["platform_aliases"] == [
        {
            "path": "alias",
            "target": "p1",
            "reason": "platform-symlink-alias-excluded",
        }
    ]
    assert [
        item["primary_role"] for item in report["representative_review_set"]
    ] == ["operator", "service", "manifest", "unknown"]
    assert next(
        platform
        for platform in report["platforms"]
        if platform["platform"] == "rhoai-3.5"
    )["generation_cohort"] == "legacy-external-analyzer-full-llm"


def test_structural_document_signal_is_not_reported_as_coverage(
    tmp_path: Path,
) -> None:
    report = audit.audit_architecture_tree(_audit_fixture(tmp_path))
    operator = next(
        component
        for component in report["components"]
        if component["component"] == "operator"
    )
    metrics = next(
        surface
        for surface in operator["surfaces"]
        if surface["surface_id"] == "authentication.metrics-enforcement"
    )

    assert metrics["document_reference_signal"] == "present"
    assert "disposition" not in metrics
    assert report["surface_inventory"]["structural_signal_only"] is True
    assert report["policy"]["missing_sidecar_interpretation"] == (
        "legacy-telemetry-unavailable"
    )
    assert report["policy"]["generation_history_source"] == (
        "project-owner-provided"
    )
    assert report["analyzer_evidence"]["behavioral_evidence"]["statuses"] == {
        "observed": 1,
        "unresolved": 1,
    }


def test_input_fingerprint_is_deterministic_and_content_sensitive(
    tmp_path: Path,
) -> None:
    root = _audit_fixture(tmp_path)
    first = audit.audit_architecture_tree(root)
    second = audit.audit_architecture_tree(root)

    assert first["input"] == second["input"]

    document = root / "p1/unknown.md"
    document.write_text(document.read_text() + "changed\n")
    changed = audit.audit_architecture_tree(root)
    assert changed["input"]["fingerprint_sha256"] != first["input"][
        "fingerprint_sha256"
    ]


def test_cli_rejects_outputs_inside_architecture_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _audit_fixture(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(AUDIT_PATH),
            "--architecture-root",
            str(root),
            "--output-json",
            str(root / "audit.json"),
            "--output-markdown",
            str(tmp_path / "audit.md"),
        ],
    )

    with pytest.raises(SystemExit, match="2"):
        audit.main()
    assert not (root / "audit.json").exists()


def test_markdown_renders_auditable_boundary(tmp_path: Path) -> None:
    report = audit.audit_architecture_tree(_audit_fixture(tmp_path))

    rendered = audit.render_markdown(report)

    assert "Missing legacy sidecars" in rendered
    assert "incomparable legacy cohort" in rendered
    assert "not semantic coverage" in rendered
    assert "## Interpretation limits" in rendered
