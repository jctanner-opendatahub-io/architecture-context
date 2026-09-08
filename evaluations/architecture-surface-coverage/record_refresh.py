#!/usr/bin/env python3
"""Validate and record an isolated architecture-surface analyzer refresh."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "architecture-surface-analyzer-refresh-result/v1"


class RefreshResultError(ValueError):
    """Raised when refreshed outputs do not match their pinned inputs."""


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _file_sha256(path: Path) -> str:
    return _sha256(path.read_bytes())


def _fingerprint_files(root: Path, paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _run_git(path: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(path), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _run_git_lines(path: Path, *args: str) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(path), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.rstrip("\n").splitlines() if result.stdout else []


def _normalized_repository(value: str) -> str:
    return value.removesuffix("/").removesuffix(".git")


def _find_checkout(
    roots: list[Path], repository: str, commit_sha: str
) -> dict[str, Any]:
    repo_name = Path(_normalized_repository(repository)).name
    matches: list[Path] = []
    for root in roots:
        candidate = root / repo_name
        if not (candidate / ".git").is_dir():
            continue
        try:
            origin = _run_git(candidate, "remote", "get-url", "origin")
        except subprocess.CalledProcessError:
            continue
        if _normalized_repository(origin) == _normalized_repository(repository):
            matches.append(candidate)
    if len(matches) != 1:
        raise RefreshResultError(
            f"expected one checkout for {repository}, found {len(matches)}"
        )
    checkout = matches[0]
    head = _run_git(checkout, "rev-parse", "HEAD")
    if head != commit_sha:
        raise RefreshResultError(
            f"checkout HEAD mismatch for {repository}: {head} != {commit_sha}"
        )
    status = _run_git(checkout, "status", "--porcelain")
    if status:
        raise RefreshResultError(f"checkout is dirty: {checkout}")
    return {
        "path": checkout.relative_to(PROJECT_ROOT).as_posix(),
        "origin": _run_git(checkout, "remote", "get-url", "origin"),
        "head": head,
        "clean": True,
    }


def _behavioral_state(analyzer: dict[str, Any]) -> tuple[str, int]:
    if "behavioral_evidence" not in analyzer:
        return "field-absent", 0
    value = analyzer["behavioral_evidence"]
    if not isinstance(value, list):
        return "field-invalid", 0
    return ("present-records" if value else "present-empty"), len(value)


def _copy_atomic(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    shutil.copyfile(source, temporary)
    temporary.replace(destination)


def build_refresh_result(
    *,
    input_plan: dict[str, Any],
    input_plan_path: Path,
    architecture_root: Path,
    refreshed_root: Path,
    checkout_roots: list[Path],
    output_dir: Path,
    analyzer_binary: Path,
    platform: str,
    distribution: str,
) -> dict[str, Any]:
    cohort = input_plan.get("cohort")
    if not isinstance(cohort, list) or not cohort:
        raise RefreshResultError("input plan cohort is missing or empty")
    if not analyzer_binary.is_file():
        raise RefreshResultError(f"analyzer binary is missing: {analyzer_binary}")
    component_map = architecture_root / platform / "component-map.json"
    if not component_map.is_file():
        raise RefreshResultError(f"component map is missing: {component_map}")

    project_revision = _run_git(PROJECT_ROOT, "rev-parse", "HEAD")
    analyzer_diff = subprocess.run(
        ["git", "-C", str(PROJECT_ROOT), "diff", "--binary", "--", "src/arch-analyzer"],
        check=True,
        capture_output=True,
    ).stdout
    analyzer_source_paths = [
        PROJECT_ROOT / relative
        for relative in _run_git(
            PROJECT_ROOT,
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            "src/arch-analyzer",
        ).splitlines()
        if relative
    ]
    analyzer_source_status = _run_git_lines(
        PROJECT_ROOT,
        "status",
        "--short",
        "--untracked-files=all",
        "--",
        "src/arch-analyzer",
    )
    tracked_architecture_diff = _run_git(
        PROJECT_ROOT, "diff", "--name-only", "--", "architecture"
    )
    if tracked_architecture_diff:
        raise RefreshResultError("tracked architecture files changed during refresh")

    output_dir.mkdir(parents=True, exist_ok=True)
    recorded: list[dict[str, Any]] = []
    analyzer_versions: set[str] = set()
    for expected in cohort:
        component = expected["component"]
        source_identity = expected["source_identity"]
        repository = source_identity["repository"]
        commit_sha = source_identity["commit_sha"]
        checkout = _find_checkout(checkout_roots, repository, commit_sha)

        analyzer_dir = refreshed_root / platform / component / ".analyzer"
        analyzer_path = analyzer_dir / "component-architecture.json"
        render_path = analyzer_dir / "analyzer_architecture.md"
        context_path = analyzer_dir / "analyzer_synthesis_context.md"
        render_meta_path = analyzer_dir / ".render_meta.json"
        for required in (analyzer_path, render_path, context_path, render_meta_path):
            if not required.is_file():
                raise RefreshResultError(f"refreshed output is missing: {required}")
        analyzer = json.loads(analyzer_path.read_text())
        if analyzer.get("repo") != repository:
            raise RefreshResultError(f"refreshed repository mismatch: {component}")
        if analyzer.get("commit_sha") != commit_sha:
            raise RefreshResultError(f"refreshed commit mismatch: {component}")
        state, record_count = _behavioral_state(analyzer)
        if state not in {"present-empty", "present-records"}:
            raise RefreshResultError(
                f"refreshed behavioral evidence is unusable for {component}: {state}"
            )
        analyzer_versions.add(str(analyzer.get("analyzer_version", "")))

        comparison = expected["comparison_document"]
        comparison_path = architecture_root / comparison["path"]
        if _file_sha256(comparison_path) != comparison["sha256"]:
            raise RefreshResultError(f"comparison document hash mismatch: {component}")

        recorded_path = output_dir / f"{component}.json"
        _copy_atomic(analyzer_path, recorded_path)
        schema_root = analyzer_dir / "contracts" / "schemas"
        schema_paths = list(schema_root.rglob("*.json")) if schema_root.is_dir() else []
        recorded.append(
            {
                "sequence": expected["sequence"],
                "component": component,
                "primary_role": expected["primary_role"],
                "source_identity": source_identity,
                "checkout": checkout,
                "comparison_document": comparison,
                "refreshed_analyzer": {
                    "path": recorded_path.relative_to(PROJECT_ROOT).as_posix(),
                    "sha256": _file_sha256(recorded_path),
                    "size_bytes": recorded_path.stat().st_size,
                    "extracted_at": analyzer.get("extracted_at"),
                    "behavioral_evidence_state": state,
                    "behavioral_evidence_records": record_count,
                },
                "rendered_outputs": {
                    "analyzer_architecture_sha256": _file_sha256(render_path),
                    "analyzer_synthesis_context_sha256": _file_sha256(context_path),
                    "render_meta_sha256": _file_sha256(render_meta_path),
                },
                "schemas": {
                    "count": len(schema_paths),
                    "fingerprint_sha256": _fingerprint_files(schema_root, schema_paths)
                    if schema_paths
                    else _sha256(b""),
                },
            }
        )
    if len(analyzer_versions) != 1 or "" in analyzer_versions:
        raise RefreshResultError(
            f"refreshed analyzer versions are inconsistent: {sorted(analyzer_versions)}"
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "complete",
        "input": {
            "refresh_plan": input_plan_path.relative_to(PROJECT_ROOT).as_posix(),
            "refresh_plan_sha256": _file_sha256(input_plan_path),
            "architecture_root": architecture_root.name,
            "selected_artifacts": len(recorded),
        },
        "analyzer": {
            "base_repository_revision": project_revision,
            "source_diff_sha256": _sha256(analyzer_diff),
            "source_tree_fingerprint_sha256": _fingerprint_files(
                PROJECT_ROOT, analyzer_source_paths
            ),
            "source_file_count": len(analyzer_source_paths),
            "source_status": analyzer_source_status,
            "source_tree_clean": not bool(analyzer_source_status),
            "binary_sha256": _file_sha256(analyzer_binary),
            "version": next(iter(analyzer_versions)),
            "go_version": subprocess.run(
                ["go", "version"], check=True, capture_output=True, text=True
            ).stdout.strip(),
        },
        "configuration": {
            "platform": platform,
            "distribution": distribution,
            "force": True,
            "skip_schemas": False,
            "supplemental_authentication": "none-for-selected-cohort",
            "component_map_sha256": _file_sha256(component_map),
            "output_isolation": "outside-architecture",
            "reproduction_command": (
                "uv run main.py static-analysis --platform rhoai-3.6-ea.2 "
                "--architecture-dir <isolated-root> --component <component> --force"
            ),
        },
        "summary": {
            "artifacts": len(recorded),
            "behavioral_evidence_states": dict(
                sorted(
                    {
                        state: sum(
                            item["refreshed_analyzer"]["behavioral_evidence_state"]
                            == state
                            for item in recorded
                        )
                        for state in {
                            item["refreshed_analyzer"]["behavioral_evidence_state"]
                            for item in recorded
                        }
                    }.items()
                )
            ),
            "behavioral_evidence_records": sum(
                item["refreshed_analyzer"]["behavioral_evidence_records"]
                for item in recorded
            ),
            "schemas": sum(item["schemas"]["count"] for item in recorded),
        },
        "cohort": sorted(recorded, key=lambda item: item["sequence"]),
        "boundary": {
            "generated_architecture_modified": False,
            "historical_comparison_documents_copied_for_audit_only": True,
            "live_agents_run": False,
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Architecture Surface Analyzer Refresh Result",
        "",
        f"Status: **{report['status']}**.",
        "",
        f"Analyzer base revision: `{report['analyzer']['base_repository_revision']}`.",
        f"Analyzer source diff: `{report['analyzer']['source_diff_sha256']}`.",
        "Analyzer source tree: "
        f"`{report['analyzer']['source_tree_fingerprint_sha256']}`.",
        f"Analyzer binary: `{report['analyzer']['binary_sha256']}`.",
        "",
        f"Refreshed {summary['artifacts']} pinned artifacts with "
        f"{summary['behavioral_evidence_records']} behavioral evidence records and "
        f"{summary['schemas']} extracted CRD schemas.",
        "",
        "| Component | Role | Commit | Behavioral evidence | Records | Schemas |",
        "|---|---|---|---|---:|---:|",
    ]
    for item in report["cohort"]:
        analyzer = item["refreshed_analyzer"]
        lines.append(
            f"| `{item['component']}` | {item['primary_role']} | "
            f"`{item['source_identity']['commit_sha']}` | "
            f"{analyzer['behavioral_evidence_state']} | "
            f"{analyzer['behavioral_evidence_records']} | {item['schemas']['count']} |"
        )
    lines.extend(
        [
            "",
            "The structured analyzer outputs are stored under `refreshed-analyzers/`. "
            "Historical documents remain comparison-only; generated architecture was "
            "not modified and no live agent ran.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-plan", type=Path, required=True)
    parser.add_argument("--architecture-root", type=Path, required=True)
    parser.add_argument("--refreshed-root", type=Path, required=True)
    parser.add_argument("--checkout-root", type=Path, action="append", required=True)
    parser.add_argument("--analyzer-binary", type=Path, required=True)
    parser.add_argument("--platform", default="rhoai-3.6-ea.2")
    parser.add_argument("--distribution", default="rhoai")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args()
    try:
        plan = json.loads(args.input_plan.read_text())
        report = build_refresh_result(
            input_plan=plan,
            input_plan_path=args.input_plan.resolve(),
            architecture_root=args.architecture_root.resolve(),
            refreshed_root=args.refreshed_root.resolve(),
            checkout_roots=[
                path if path.is_absolute() else PROJECT_ROOT / path
                for path in args.checkout_root
            ],
            output_dir=args.output_dir.resolve(),
            analyzer_binary=args.analyzer_binary.resolve(),
            platform=args.platform,
            distribution=args.distribution,
        )
    except (
        OSError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
        RefreshResultError,
    ) as error:
        parser.error(str(error))
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.output_markdown.write_text(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
