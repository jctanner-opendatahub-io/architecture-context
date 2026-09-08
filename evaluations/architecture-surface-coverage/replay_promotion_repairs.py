#!/usr/bin/env python3
"""Replay retained canary candidates through the repaired promotion path."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from lib.arch_doc import assemble_architecture_sections  # noqa: E402
from lib.architecture_merge import (  # noqa: E402
    ArchitectureMergeError,
    merge_architecture_files,
)

EVALUATION_ROOT = PROJECT_ROOT / "evaluations/architecture-surface-coverage"
LIVE_ROOT = EVALUATION_ROOT / "live-canary"
DEFAULT_OUTPUT = EVALUATION_ROOT / "promotion-repair-replay"
LEGACY_METRICS_ROWS = (
    "| opendatahub-operator-metrics-reader |  |  | get |",
    "| metrics-reader |  |  | get |",
)
REPAIR_SOURCES = (
    ".claude/skills/repo-to-architecture-summary/SKILL.md",
    ".claude/skills/repo-to-architecture-summary/references/architecture-template.md",
    ".claude/skills/repo-to-architecture-summary/scripts/validate_architecture.py",
    ".claude/skills/repo-to-architecture-summary/templates/architecture-template.md",
    "lib/arch_doc.py",
    "lib/architecture_baseline.py",
    "lib/architecture_merge.py",
    "lib/phases/architecture.py",
    "src/arch-analyzer/internal/extractor/collectors.go",
    "src/arch-analyzer/internal/model/document.go",
    "src/arch-analyzer/internal/model/input.go",
    "src/arch-analyzer/internal/normalize/normalize.go",
    "src/arch-analyzer/internal/renderer/markdown.go",
    "src/arch-doc/main.go",
    "src/arch-doc/section-manifest.json",
    "src/arch-query/cmd/diff.go",
    "src/arch-query/cmd/grep.go",
    "src/arch-query/cmd/platform_summary.go",
    "src/arch-query/internal/diff/diff.go",
    "src/arch-query/internal/markdown/parser.go",
    "src/arch-query/internal/types/types.go",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot_tree(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def aggregate_hash(snapshot: dict[str, str]) -> str:
    payload = "".join(f"{path}\0{digest}\n" for path, digest in snapshot.items())
    return hashlib.sha256(payload.encode()).hexdigest()


def verify_manifest(manifest: dict[str, object]) -> list[str]:
    mismatches: list[str] = []

    def check(entry: object) -> None:
        if not isinstance(entry, dict) or "path" not in entry or "sha256" not in entry:
            return
        path = EVALUATION_ROOT / str(entry["path"])
        if not path.is_file():
            mismatches.append(f"missing {path.relative_to(EVALUATION_ROOT)}")
            return
        actual = sha256(path)
        if actual != entry["sha256"]:
            mismatches.append(
                f"hash mismatch {path.relative_to(EVALUATION_ROOT)}: "
                f"expected {entry['sha256']}, got {actual}"
            )

    for value in dict(manifest.get("inputs", {})).values():
        check(value)
    for run in manifest.get("runs", []):
        if isinstance(run, dict):
            for entry in dict(run.get("artifacts", {})).values():
                check(entry)
    return mismatches


def replay(output_root: Path) -> dict[str, object]:
    manifest = json.loads((LIVE_ROOT / "manifest.json").read_text())
    before = snapshot_tree(LIVE_ROOT)
    manifest_errors = verify_manifest(manifest)
    if manifest_errors:
        raise ValueError(
            "retained canary manifest verification failed: "
            + "; ".join(manifest_errors)
        )

    with TemporaryDirectory(prefix="promotion-repair-replay-") as temporary:
        staging = Path(temporary) / "promotion-repair-replay"
        staging.mkdir()
        run_results: list[dict[str, object]] = []
        for run in manifest["runs"]:
            run_id = run["run_id"]
            original = LIVE_ROOT / "runs" / run_id
            target = staging / "runs" / run_id
            target.mkdir(parents=True)
            run_report = json.loads((original / "run.json").read_text())
            expected_failure = run_id == "claude-repetition-2"
            output = target / "promoted.md"
            report_json = target / "merge.json"
            report_markdown = target / "merge.md"
            merge_result = None
            error = None
            try:
                merge_result = merge_architecture_files(
                    original / "preseed.md",
                    original / "candidate.md",
                    output,
                    patch=original / "patch.json",
                    report_json=report_json,
                    report_markdown=report_markdown,
                    component="rhods-operator",
                    allowed_change_categories=tuple(
                        run_report["routing"]["gap_categories"]
                    ),
                    section_assembler=assemble_architecture_sections,
                )
            except ArchitectureMergeError as caught:
                merge_result = caught.result
                error = str(caught)

            if merge_result is None:
                raise AssertionError(f"{run_id}: replay produced no merge result")
            status = "failed" if error else "success"
            if expected_failure != bool(error):
                raise AssertionError(
                    f"{run_id}: expected_failure={expected_failure}, status={status}"
                )
            if merge_result.preservation.get("expected") != 276:
                raise AssertionError(
                    f"{run_id}: expected 276 analyzer rows, got "
                    f"{merge_result.preservation}"
                )
            if merge_result.preservation.get("missing") != 0:
                raise AssertionError(
                    f"{run_id}: analyzer row loss: {merge_result.preservation}"
                )
            if merge_result.preservation.get("adjudicated_missing") != 0:
                raise AssertionError(
                    f"{run_id}: adjudicated row loss: "
                    f"{merge_result.preservation}"
                )
            if merge_result.preservation.get("all_missing") != 0:
                raise AssertionError(
                    f"{run_id}: unmapped analyzer row loss: "
                    f"{merge_result.preservation}"
                )
            if merge_result.preservation.get("all_adjudicated_missing") != 0:
                raise AssertionError(
                    f"{run_id}: adjudicated all-table row loss: "
                    f"{merge_result.preservation}"
                )
            if error:
                if output.exists():
                    raise AssertionError(f"{run_id}: failed replay wrote promotion")
                codes = {
                    item.get("code")
                    for item in merge_result.assembly_diagnostics
                    if isinstance(item, dict)
                }
                if "synthesis_subsection_parent_mismatch" not in codes:
                    raise AssertionError(
                        f"{run_id}: missing actionable section diagnostic"
                    )
            else:
                promoted = output.read_text()
                missing_metrics = [
                    row for row in LEGACY_METRICS_ROWS if row not in promoted
                ]
                if missing_metrics:
                    raise AssertionError(
                        f"{run_id}: missing legacy RBAC rows {missing_metrics}"
                    )

            run_results.append(
                {
                    "run_id": run_id,
                    "harness": run["harness"],
                    "model": run["model"],
                    "status": status,
                    "expected_failure": expected_failure,
                    "error": error,
                    "counts": merge_result.counts,
                    "preservation": merge_result.preservation,
                    "assembly_status": merge_result.assembly_status,
                    "assembly_diagnostics": merge_result.assembly_diagnostics,
                    "promoted": (
                        str(output.relative_to(staging))
                        if output.exists()
                        else None
                    ),
                    "promoted_sha256": sha256(output) if output.exists() else None,
                    "merge_report": str(report_json.relative_to(staging)),
                    "merge_report_sha256": sha256(report_json),
                }
            )

        after = snapshot_tree(LIVE_ROOT)
        if after != before:
            raise AssertionError("retained live-canary evidence changed during replay")
        report: dict[str, object] = {
            "schema_version": 1,
            "objective": (
                "verify repaired promotion preserves analyzer RBAC rows and "
                "rejects misplaced configured synthesis subsections"
            ),
            "original_canary_status": "rejected",
            "original_evidence": {
                "immutable": True,
                "file_count": len(before),
                "aggregate_sha256_before": aggregate_hash(before),
                "aggregate_sha256_after": aggregate_hash(after),
                "manifest_verified": True,
            },
            "repair_implementation": {
                "files": {
                    path: sha256(PROJECT_ROOT / path)
                    for path in REPAIR_SOURCES
                }
            },
            "summary": {
                "run_count": len(run_results),
                "successful_promotions": sum(
                    item["status"] == "success" for item in run_results
                ),
                "expected_rejections": sum(
                    item["status"] == "failed" for item in run_results
                ),
                "all_analyzer_rows_preserved": all(
                    item["preservation"]["all_missing"] == 0
                    and item["preservation"]["all_adjudicated_missing"] == 0
                    for item in run_results
                ),
            },
            "runs": run_results,
        }
        report["repair_implementation"]["aggregate_sha256"] = aggregate_hash(
            report["repair_implementation"]["files"]
        )
        (staging / "report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n"
        )
        (staging / "report.md").write_text(render_markdown(report))
        (staging / "README.md").write_text(
            "# Promotion Repair Replay\n\n"
            "Offline replay of the four immutable live-canary candidates through "
            "the repaired merge and arch-doc assembly path. The original canary "
            "remains rejected. Claude repetition 2 is an expected repair-time "
            "rejection because FIPS Compliance is under Admission Webhooks.\n"
        )
        if output_root.exists():
            if snapshot_tree(output_root) != snapshot_tree(staging):
                raise FileExistsError(
                    "recorded replay differs from current result: "
                    f"{output_root}"
                )
        else:
            shutil.copytree(staging, output_root)
    return report


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Promotion Repair Replay Results",
        "",
        "The original live canary remains rejected and its retained evidence "
        "was unchanged.",
        "",
        "| Run | Harness | Model | Result | Mapped analyzer rows | "
        "All analyzer rows | Mapped missing | All missing | Diagnostic |",
        "|-----|---------|-------|--------|---------------------:|"
        "------------------:|---------------:|------------:|------------|",
    ]
    for run in report["runs"]:
        codes = ", ".join(
            item.get("code", "") for item in run["assembly_diagnostics"]
        )
        lines.append(
            f"| {run['run_id']} | {run['harness']} | {run['model']} | "
            f"{run['status']} | {run['preservation']['expected']} | "
            f"{run['preservation']['all_expected']} | "
            f"{run['preservation']['mapped_missing']} | "
            f"{run['preservation']['all_missing']} | {codes or '-'} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    replay(args.output.resolve())
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
