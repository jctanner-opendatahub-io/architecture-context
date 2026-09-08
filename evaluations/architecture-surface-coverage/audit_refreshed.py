#!/usr/bin/env python3
"""Reproduce the rollout audit from recorded refreshed analyzer artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from audit_tree import audit_architecture_tree, render_markdown

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULT_SCHEMA_VERSION = "architecture-surface-analyzer-refresh-result/v1"
RECORDED_ROOT_LABEL = "refreshed-analyzer-cohort"


class RefreshedAuditError(ValueError):
    """Raised when recorded refresh inputs fail integrity checks."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _recorded_path(relative_path: object, expected_sha256: object) -> Path:
    if not isinstance(relative_path, str) or not relative_path:
        raise RefreshedAuditError("recorded analyzer path is missing")
    path = PROJECT_ROOT / relative_path
    try:
        path.resolve().relative_to(PROJECT_ROOT.resolve())
    except ValueError as error:
        raise RefreshedAuditError(
            f"recorded analyzer path escapes project root: {relative_path}"
        ) from error
    if not path.is_file() or path.is_symlink():
        raise RefreshedAuditError(
            f"recorded analyzer is not a regular file: {relative_path}"
        )
    if _sha256(path) != expected_sha256:
        raise RefreshedAuditError(f"recorded analyzer hash mismatch: {relative_path}")
    return path


def _comparison_path(
    architecture_root: Path, relative_path: object, expected_sha256: object
) -> Path:
    if not isinstance(relative_path, str) or not relative_path:
        raise RefreshedAuditError("comparison document path is missing")
    path = architecture_root / relative_path
    try:
        path.resolve().relative_to(architecture_root.resolve())
    except ValueError as error:
        raise RefreshedAuditError(
            f"comparison document path escapes architecture root: {relative_path}"
        ) from error
    if not path.is_file() or path.is_symlink():
        raise RefreshedAuditError(
            f"comparison document is not a regular file: {relative_path}"
        )
    if _sha256(path) != expected_sha256:
        raise RefreshedAuditError(
            f"comparison document hash mismatch: {relative_path}"
        )
    return path


def build_refreshed_audit(
    result: dict[str, Any], architecture_root: Path
) -> dict[str, Any]:
    if result.get("schema_version") != RESULT_SCHEMA_VERSION:
        raise RefreshedAuditError("refresh result schema is missing or unsupported")
    cohort = result.get("cohort")
    if not isinstance(cohort, list) or not cohort:
        raise RefreshedAuditError("refresh result cohort is missing or empty")
    platform = result.get("configuration", {}).get("platform")
    if not isinstance(platform, str) or not platform:
        raise RefreshedAuditError("refresh result platform is missing")

    names: set[str] = set()
    with tempfile.TemporaryDirectory(
        prefix="architecture-surface-refreshed-audit-"
    ) as directory:
        root = Path(directory) / "architecture"
        platform_root = root / platform
        platform_root.mkdir(parents=True)
        for item in cohort:
            component = item.get("component")
            if (
                not isinstance(component, str)
                or not component
                or component in names
                or Path(component).name != component
            ):
                raise RefreshedAuditError(
                    f"invalid or duplicate refresh component: {component!r}"
                )
            names.add(component)
            refreshed = item.get("refreshed_analyzer", {})
            analyzer = _recorded_path(
                refreshed.get("path"), refreshed.get("sha256")
            )
            comparison = item.get("comparison_document", {})
            document = _comparison_path(
                architecture_root,
                comparison.get("path"),
                comparison.get("sha256"),
            )
            destination = platform_root / component / ".analyzer"
            destination.mkdir(parents=True)
            shutil.copyfile(analyzer, destination / "component-architecture.json")
            shutil.copyfile(document, platform_root / f"{component}.md")

        report = audit_architecture_tree(root)
    report["input"]["architecture_root"] = RECORDED_ROOT_LABEL
    expected_states = result.get("summary", {}).get("behavioral_evidence_states")
    actual_states = report["summary"]["behavioral_evidence"]["field_states"]
    if actual_states != expected_states:
        raise RefreshedAuditError(
            "refreshed audit behavioral states do not match the result manifest: "
            f"{actual_states} != {expected_states}"
        )
    if report["summary"]["eligible_pairs"] != len(cohort):
        raise RefreshedAuditError("refreshed audit did not pair every cohort artifact")
    return report


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-result", type=Path, required=True)
    parser.add_argument("--architecture-root", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args()
    for output in (args.output_json, args.output_markdown):
        if _is_within(output, args.architecture_root):
            parser.error("audit outputs must remain outside the architecture tree")
    try:
        result = json.loads(args.refresh_result.read_text())
        report = build_refreshed_audit(result, args.architecture_root.resolve())
    except (OSError, json.JSONDecodeError, RefreshedAuditError) as error:
        parser.error(str(error))
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.output_markdown.write_text(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
