#!/usr/bin/env python3
"""Build a deterministic analyzer-refresh manifest from stored architecture data.

The manifest records the exact comparison inputs that can be established from
``architecture/``. It deliberately does not look for source checkouts, fetch a
replacement revision, run the analyzer, or write into the generated tree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "architecture-surface-analyzer-refresh-plan/v1"
AUDIT_SCHEMA_VERSION = "architecture-surface-rollout-audit/v1"
PRIMARY_COMPONENT = "rhods-operator"
SELECTED_ROLES = ("operator", "service", "manifest")
COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class RefreshPlanError(ValueError):
    """Raised when stored inputs cannot support an exact refresh plan."""


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _fingerprint(entries: list[tuple[str, bytes]]) -> str:
    digest = hashlib.sha256()
    for name, content in sorted(entries, key=lambda item: item[0]):
        digest.update(name.encode())
        digest.update(b"\0")
        digest.update(content)
        digest.update(b"\0")
    return digest.hexdigest()


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _resolve_stored_path(root: Path, relative_path: object) -> Path:
    if not isinstance(relative_path, str) or not relative_path:
        raise RefreshPlanError("stored artifact path must be a non-empty string")
    candidate = root / relative_path
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError as error:
        raise RefreshPlanError(
            f"stored artifact path escapes architecture root: {relative_path}"
        ) from error
    if not candidate.is_file() or candidate.is_symlink():
        raise RefreshPlanError(
            f"stored artifact must be a regular, non-symlink file: {relative_path}"
        )
    return candidate


def _behavioral_evidence_state(analyzer: dict[str, Any]) -> str:
    if "behavioral_evidence" not in analyzer:
        return "field-absent"
    evidence = analyzer["behavioral_evidence"]
    if not isinstance(evidence, list):
        return "field-invalid"
    if not evidence:
        return "present-empty"
    return "present-records"


def _metadata_value(
    analyzer: dict[str, Any], keys: tuple[str, ...]
) -> tuple[object | None, str]:
    for key in keys:
        if key in analyzer and analyzer[key] not in (None, "", {}, []):
            return analyzer[key], "recorded"
    return None, "unavailable-in-stored-artifact"


def _artifact_kind(path: Path) -> str:
    return {
        "component-architecture.json": "structured-analyzer-output",
        "analyzer_architecture.md": "rendered-analyzer-baseline",
        "analyzer_synthesis_context.md": "compact-analyzer-context",
        ".render_meta.json": "analyzer-render-metadata",
    }.get(path.name, "analyzer-output")


def _validate_audit(audit: dict[str, Any]) -> None:
    if audit.get("schema_version") != AUDIT_SCHEMA_VERSION:
        raise RefreshPlanError("rollout audit schema is missing or unsupported")
    audit_input = audit.get("input")
    if not isinstance(audit_input, dict) or not isinstance(
        audit_input.get("fingerprint_sha256"), str
    ):
        raise RefreshPlanError("rollout audit input fingerprint is missing")
    if not isinstance(audit.get("representative_review_set"), list):
        raise RefreshPlanError("rollout audit representative review set is missing")
    if not isinstance(audit.get("components"), list):
        raise RefreshPlanError("rollout audit component inventory is missing")


def _selected_representatives(
    audit: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    representatives = audit["representative_review_set"]
    selected = [
        item
        for role in SELECTED_ROLES
        for item in representatives
        if isinstance(item, dict) and item.get("primary_role") == role
    ]
    primary = [item for item in selected if item.get("component") == PRIMARY_COMPONENT]
    if not primary:
        primary = [
            item
            for item in selected
            if str(item.get("artifact_key", "")).rsplit("/", 1)[-1] == PRIMARY_COMPONENT
        ]
    if len(primary) != 1:
        raise RefreshPlanError(
            "representative review set must contain exactly one rhods-operator input"
        )
    first = primary[0]
    selected = [first, *(item for item in selected if item is not first)]
    excluded = [
        {
            "artifact_key": str(item.get("artifact_key", "")),
            "primary_role": str(item.get("primary_role", "")),
            "reason": "outside-requested-operator-service-manifest-cohort",
        }
        for item in representatives
        if isinstance(item, dict) and item.get("primary_role") not in SELECTED_ROLES
    ]
    return selected, excluded


def _component_index(audit: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for component in audit["components"]:
        if not isinstance(component, dict):
            continue
        key = component.get("artifact_key")
        if not isinstance(key, str) or not key:
            continue
        if key in result:
            raise RefreshPlanError(f"duplicate component artifact key in audit: {key}")
        result[key] = component
    return result


def _cohort_item(
    architecture_root: Path,
    representative: dict[str, Any],
    component: dict[str, Any],
    sequence: int,
) -> tuple[dict[str, Any], list[tuple[str, bytes]]]:
    artifact_key = representative.get("artifact_key")
    if not isinstance(artifact_key, str) or not artifact_key:
        raise RefreshPlanError("representative artifact key is missing")
    for field in ("repository", "commit_sha", "primary_role", "analyzer", "document"):
        expected = representative.get(field)
        if expected is None:
            expected = component.get(field)
        if field in representative and representative[field] != component.get(field):
            raise RefreshPlanError(
                f"representative/component {field} mismatch for {artifact_key}"
            )
        if expected in (None, ""):
            raise RefreshPlanError(f"{field} is missing for {artifact_key}")

    analyzer_path = _resolve_stored_path(architecture_root, component["analyzer"])
    document_path = _resolve_stored_path(architecture_root, component["document"])
    analyzer_bytes = analyzer_path.read_bytes()
    document_bytes = document_path.read_bytes()
    if _sha256(analyzer_bytes) != component.get("analyzer_sha256"):
        raise RefreshPlanError(
            f"stored analyzer hash no longer matches audit: {artifact_key}"
        )
    if _sha256(document_bytes) != component.get("document_sha256"):
        raise RefreshPlanError(
            f"stored document hash no longer matches audit: {artifact_key}"
        )

    try:
        analyzer = json.loads(analyzer_bytes)
    except json.JSONDecodeError as error:
        raise RefreshPlanError(
            f"stored analyzer JSON is invalid: {artifact_key}"
        ) from error
    if not isinstance(analyzer, dict):
        raise RefreshPlanError(f"stored analyzer root is not an object: {artifact_key}")

    repository = component["repository"]
    commit_sha = component["commit_sha"]
    if analyzer.get("repo") != repository:
        raise RefreshPlanError(f"stored analyzer repository mismatch: {artifact_key}")
    if analyzer.get("commit_sha") != commit_sha or not COMMIT_SHA_RE.fullmatch(
        str(commit_sha)
    ):
        raise RefreshPlanError(
            f"stored analyzer commit is not an exact SHA: {artifact_key}"
        )

    analyzer_dir = analyzer_path.parent
    analyzer_entries: list[tuple[str, bytes]] = []
    artifacts: list[dict[str, Any]] = []
    for path in sorted(analyzer_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.is_symlink():
            raise RefreshPlanError(f"analyzer output must not be a symlink: {path}")
        relative = _relative(architecture_root, path)
        content = path.read_bytes()
        analyzer_entries.append((relative, content))
        artifacts.append(
            {
                "kind": _artifact_kind(path),
                "path": relative,
                "sha256": _sha256(content),
                "size_bytes": len(content),
            }
        )
    if not analyzer_entries:
        raise RefreshPlanError(f"stored analyzer output set is empty: {artifact_key}")

    document_relative = _relative(architecture_root, document_path)
    all_entries = [*analyzer_entries, (document_relative, document_bytes)]
    analyzer_revision, analyzer_revision_status = _metadata_value(
        analyzer, ("analyzer_revision", "analyzer_commit_sha")
    )
    configuration, configuration_status = _metadata_value(
        analyzer, ("analyzer_configuration", "configuration")
    )
    return (
        {
            "sequence": sequence,
            "stage": "rhods-operator-first"
            if sequence == 1
            else "representative-cohort",
            "artifact_key": artifact_key,
            "platform": component["platform"],
            "component": component["component"],
            "primary_role": component["primary_role"],
            "source_identity": {
                "repository": repository,
                "commit_sha": commit_sha,
                "status": "pinned-from-stored-analyzer",
            },
            "source_input": {
                "status": "unavailable-under-architecture-only-constraint",
                "reason": (
                    "The stored architecture artifact pins source identity but does "
                    "not contain the source checkout required by arch-analyzer."
                ),
            },
            "stored_analyzer": {
                "schema_version": analyzer.get("schema_version"),
                "version": analyzer.get("analyzer_version"),
                "revision": analyzer_revision,
                "revision_status": analyzer_revision_status,
                "configuration": configuration,
                "configuration_status": configuration_status,
                "behavioral_evidence_state": _behavioral_evidence_state(analyzer),
                "output_fingerprint_sha256": _fingerprint(analyzer_entries),
            },
            "stored_outputs": artifacts,
            "comparison_document": {
                "path": document_relative,
                "sha256": _sha256(document_bytes),
                "size_bytes": len(document_bytes),
            },
            "comparison_input_fingerprint_sha256": _fingerprint(all_entries),
            "regeneration": {
                "status": "not-run-source-input-unavailable",
                "revision_substitution": "prohibited",
                "output_location": None,
            },
        },
        all_entries,
    )


def build_refresh_plan(
    architecture_root: Path,
    audit: dict[str, Any],
    *,
    audit_bytes: bytes | None = None,
) -> dict[str, Any]:
    """Return the exact refresh cohort that on-disk evidence can support."""

    _validate_audit(audit)
    selected, excluded = _selected_representatives(audit)
    components = _component_index(audit)
    cohort: list[dict[str, Any]] = []
    fingerprint_entries: list[tuple[str, bytes]] = []
    for sequence, representative in enumerate(selected, start=1):
        key = representative.get("artifact_key")
        component = components.get(str(key))
        if component is None:
            raise RefreshPlanError(
                f"representative missing from component audit: {key}"
            )
        item, entries = _cohort_item(
            architecture_root, representative, component, sequence
        )
        cohort.append(item)
        fingerprint_entries.extend(entries)

    role_counts = Counter(item["primary_role"] for item in cohort)
    evidence_counts = Counter(
        item["stored_analyzer"]["behavioral_evidence_state"] for item in cohort
    )
    revision_counts = Counter(
        item["stored_analyzer"]["revision_status"] for item in cohort
    )
    configuration_counts = Counter(
        item["stored_analyzer"]["configuration_status"] for item in cohort
    )
    audit_content = (
        audit_bytes or (json.dumps(audit, indent=2, sort_keys=True) + "\n").encode()
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "input": {
            "architecture_root": architecture_root.name,
            "rollout_audit_sha256": _sha256(audit_content),
            "rollout_audit_input_fingerprint_sha256": audit["input"][
                "fingerprint_sha256"
            ],
            "selected_comparison_input_fingerprint_sha256": _fingerprint(
                fingerprint_entries
            ),
        },
        "boundary": {
            "source": "stored-architecture-only",
            "source_checkouts_read": False,
            "pipeline_logs_read": False,
            "network_accessed": False,
            "live_agents_run": False,
            "generated_architecture_modified": False,
            "revision_substitution_allowed": False,
        },
        "selection": {
            "policy": (
                "rhods-operator first, followed by the rollout audit's deterministic "
                "operator, service, and manifest representatives"
            ),
            "roles": list(SELECTED_ROLES),
            "excluded_representatives": excluded,
        },
        "summary": {
            "selected_artifacts": len(cohort),
            "roles": {key: role_counts[key] for key in sorted(role_counts)},
            "source_inputs": {
                "unavailable-under-architecture-only-constraint": len(cohort)
            },
            "regeneration": {"not-run-source-input-unavailable": len(cohort)},
            "behavioral_evidence_states": {
                key: evidence_counts[key] for key in sorted(evidence_counts)
            },
            "analyzer_revision_states": {
                key: revision_counts[key] for key in sorted(revision_counts)
            },
            "analyzer_configuration_states": {
                key: configuration_counts[key] for key in sorted(configuration_counts)
            },
        },
        "cohort": cohort,
        "next_requirements": [
            (
                "Provide each repository at its exact pinned commit; do not replace "
                "a missing commit with a branch, tag, or newer release."
            ),
            (
                "Record the rebuilt arch-analyzer revision and configuration before "
                "creating isolated refreshed outputs."
            ),
            (
                "Review conditional metrics enforcement and named watch predicates "
                "in rhods-operator before expanding beyond the first stage."
            ),
            (
                "Rerun the rollout audit against an explicitly selected refreshed "
                "input root while preserving these historical comparison files."
            ),
        ],
        "interpretation": (
            "This manifest establishes identity and reproducibility for a future "
            "refresh. It is not a refreshed analyzer result and supplies no new "
            "behavioral-recall or generated-document-quality evidence."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Architecture Surface Analyzer Refresh Inputs",
        "",
        report["interpretation"],
        "",
        "## Boundary and status",
        "",
        f"Selected artifacts: **{summary['selected_artifacts']}**.",
        "",
        (
            "All selected source inputs are "
            "`unavailable-under-architecture-only-constraint`; regeneration was "
            "not run. No source checkout, pipeline log, network service, or live "
            "agent was used, and generated architecture was not modified."
        ),
        "",
        (
            "Rollout-audit architecture fingerprint: "
            f"`{report['input']['rollout_audit_input_fingerprint_sha256']}`."
        ),
        (
            "Selected comparison-input fingerprint: "
            f"`{report['input']['selected_comparison_input_fingerprint_sha256']}`."
        ),
        "",
        "## Pinned cohort",
        "",
        "| Stage | Role | Artifact | Source commit | Evidence | Refresh |",
        "|---|---|---|---|---|---|",
    ]
    for item in report["cohort"]:
        lines.append(
            f"| {item['stage']} | {item['primary_role']} | "
            f"`{item['artifact_key']}` | `{item['source_identity']['commit_sha']}` | "
            f"{item['stored_analyzer']['behavioral_evidence_state']} | "
            f"{item['regeneration']['status']} |"
        )
    lines.extend(["", "## Unavailable metadata", ""])
    lines.append(
        "The stored artifacts record analyzer version but do not record an exact "
        "analyzer source revision or configuration. Those values must be captured "
        "from the future rebuild and cannot be reconstructed from these files."
    )
    excluded = report["selection"]["excluded_representatives"]
    if excluded:
        lines.extend(["", "## Representatives outside this cohort", ""])
        for item in excluded:
            lines.append(
                f"- `{item['artifact_key']}` ({item['primary_role']}): "
                f"{item['reason']}."
            )
    lines.extend(["", "## Requirements before regeneration", ""])
    lines.extend(f"- {requirement}" for requirement in report["next_requirements"])
    lines.append("")
    return "\n".join(lines)


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--architecture-root", type=Path, default=PROJECT_ROOT / "architecture"
    )
    parser.add_argument(
        "--rollout-audit",
        type=Path,
        default=(
            PROJECT_ROOT
            / "evaluations/architecture-surface-coverage/rollout-audit.json"
        ),
    )
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args()
    for output in (args.output_json, args.output_markdown):
        if _is_within(output, args.architecture_root):
            parser.error("refresh-plan outputs must remain outside architecture")
    try:
        audit_bytes = args.rollout_audit.read_bytes()
        audit = json.loads(audit_bytes)
        if not isinstance(audit, dict):
            raise RefreshPlanError("rollout audit root must be an object")
        report = build_refresh_plan(
            args.architecture_root, audit, audit_bytes=audit_bytes
        )
    except (OSError, json.JSONDecodeError, RefreshPlanError) as error:
        parser.error(str(error))
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.output_markdown.write_text(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
