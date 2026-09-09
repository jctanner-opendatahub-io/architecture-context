#!/usr/bin/env python3
"""Build offline-only final evidence for structured component assembly.

This utility never starts a model harness.  It converts only deterministic
analyzer facts; legacy agent Markdown remains an identified proposal and is not
represented as if it had been emitted through the structured response schema.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.structured_component_publication import (  # noqa: E402
    PublicationError,
    validate_legacy_conversion_input,
)
from lib.structured_component_synthesis import (  # noqa: E402
    content_hash,
    special_synthesis_envelope,
)
from scripts.structured_component_fresh_reuse import (  # noqa: E402
    fresh_compare_reuse,
)

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
CURRENT_COMPARISON_SHA256 = (
    "2df2ca5dcc1853c624726474dea9278b4f7d50c8f8f2374d6585a0c55c9100dd"
)
HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$", re.MULTILINE)
FIPS_TITLE = "FIPS Compliance"
HISTORICAL_MANIFEST = (
    ROOT
    / "logs/structured-component-assembly/20260906-kickoff"
    / "historical-evidence-hashes.json"
)
KICKOFF_HASHES = (
    ROOT / "logs/structured-component-assembly/20260906-kickoff/baseline-hashes.json"
)
ORIGINAL_COMPARISON = (
    ROOT
    / "logs/structured-component-assembly/20260908-codex-only"
    / "compare-baseline-reconstructed.py"
)
CURRENT_COMPARISON = ROOT / "evaluations/component-reuse-fingerprint/compare.py"
REUSE_RESULT = (
    ROOT / "evaluations/component-reuse-fingerprint/rhoai-3.6-ea.1-to-ea.2.json"
)
LIVE_ROOT = ROOT / "evaluations/architecture-surface-coverage/live-canary"


class LegacyConversionError(ValueError):
    """A legacy input cannot be represented without ambiguity or loss."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def install_model_transport_guard() -> None:
    """Fail before either authenticated model transport can start."""

    from claude_agent_sdk._internal.transport.subprocess_cli import (
        SubprocessCLITransport,
    )
    from openai_codex.client import CodexClient

    def reject_codex_start(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("offline evidence attempted Codex transport startup")

    async def reject_claude_connect(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("offline evidence attempted Claude transport startup")

    CodexClient.start = reject_codex_start
    SubprocessCLITransport.connect = reject_claude_connect


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def validate_legacy_analyzer(value: Mapping[str, Any]) -> None:
    """Translate the production guard into a stable evaluation error."""

    try:
        validate_legacy_conversion_input(value)
    except PublicationError as error:
        detail = str(error)
        if "unsupported fields" in detail:
            code = "unsupported-legacy-fields"
        elif "FIPS" in detail:
            code = "ambiguous-legacy-fips-evidence"
        else:
            code = "malformed-legacy-analyzer"
        raise LegacyConversionError(code, detail) from error


def validate_legacy_markdown(text: str) -> None:
    """Require every legacy FIPS subsection to have the Security parent."""

    parents: dict[int, str] = {}
    for match in HEADING_RE.finditer(text):
        level = len(match.group(1))
        title = match.group(2).strip()
        for deeper in range(level, 7):
            parents.pop(deeper, None)
        if title == FIPS_TITLE:
            parent = parents.get(2)
            if level != 3 or parent != "Security":
                raise LegacyConversionError(
                    "malformed-legacy-fips-placement",
                    f"{FIPS_TITLE!r} must be a level-3 subsection of 'Security'; "
                    f"found level {level} under {parent!r}",
                )
        parents[level] = title


def verify_historical_preservation() -> dict[str, Any]:
    """Check the 75 unchanged paths and the one accepted formatting exception."""

    expected = load_object(HISTORICAL_MANIFEST)
    comparison_key = "evaluations/component-reuse-fingerprint/compare.py"
    mismatches: list[dict[str, str]] = []
    for relative, digest in sorted(expected.items()):
        if relative == comparison_key:
            continue
        path = ROOT / relative
        actual = sha256_file(path) if path.is_file() else "missing"
        if actual != digest:
            mismatches.append(
                {"path": relative, "expected_sha256": digest, "actual_sha256": actual}
            )
    original_hash = sha256_file(ORIGINAL_COMPARISON)
    current_hash = sha256_file(CURRENT_COMPARISON)
    if original_hash != expected[comparison_key]:
        raise ValueError("reconstructed comparison baseline does not match kickoff")
    if current_hash != CURRENT_COMPARISON_SHA256:
        raise ValueError("accepted formatted comparison script changed")
    if mismatches:
        raise ValueError(f"historical evidence changed: {mismatches}")
    return {
        "manifest": str(HISTORICAL_MANIFEST.relative_to(ROOT)),
        "manifest_sha256": sha256_file(HISTORICAL_MANIFEST),
        "path_count": len(expected),
        "unchanged_original_paths": len(expected) - 1,
        "mismatches": [],
        "accepted_formatting_exception": {
            "path": comparison_key,
            "kickoff_sha256": original_hash,
            "reconstructed_baseline": str(ORIGINAL_COMPARISON.relative_to(ROOT)),
            "current_sha256": current_hash,
            "disposition": "independently-accepted-cleanup-formatting",
        },
    }


def _manifest_path(relative: str) -> Path:
    return LIVE_ROOT.parent / relative


def verify_canary_manifest() -> tuple[dict[str, Any], dict[str, str]]:
    manifest = load_object(LIVE_ROOT / "manifest.json")
    checked: dict[str, str] = {}

    def check(relative: str, expected: str) -> None:
        if not SHA256_RE.fullmatch(expected):
            raise ValueError(f"invalid manifest SHA-256 for {relative}")
        path = _manifest_path(relative)
        actual = sha256_file(path)
        if actual != expected:
            raise ValueError(f"saved canary hash mismatch: {relative}")
        checked[str(path.relative_to(ROOT))] = actual

    for value in manifest["inputs"].values():
        if isinstance(value, Mapping) and "path" in value:
            check(str(value["path"]), str(value["sha256"]))
    check(
        str(manifest["expected_claims"]["manifest"]),
        str(manifest["expected_claims"]["manifest_sha256"]),
    )
    check(
        str(manifest["historical_comparison"]["report"]),
        str(manifest["historical_comparison"]["report_sha256"]),
    )
    check(
        str(manifest["source_review"]["path"]),
        str(manifest["source_review"]["sha256"]),
    )
    for run in manifest["runs"]:
        for artifact in run["artifacts"].values():
            check(str(artifact["path"]), str(artifact["sha256"]))
    return manifest, checked


def _run(
    command: Sequence[str], *, cwd: Path = ROOT
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command, cwd=cwd, capture_output=True, text=True, check=False
    )
    if completed.returncode:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            + (completed.stderr or completed.stdout)
        )
    return completed


def _proposal_identity(run: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "run_id": run["run_id"],
        "harness": run["harness"],
        "model": run["model"],
        "repetition": run["repetition"],
        "source_checkout": run["source_checkout"],
        "artifacts": run["artifacts"],
    }


def replay_saved_canary(output: Path, analyzer: Path) -> dict[str, Any]:
    """Replay analyzer facts into new directories without converting agent prose."""

    if output.exists():
        raise ValueError(f"output directory already exists: {output}")
    output.mkdir(parents=True)
    manifest, canary_hashes = verify_canary_manifest()
    preservation = verify_historical_preservation()
    analyzer_input = LIVE_ROOT / "inputs/component-architecture.json"
    component_map = LIVE_ROOT / "inputs/component-map.json"
    analyzer_value = load_object(analyzer_input)
    validate_legacy_analyzer(analyzer_value)
    source_identity = {
        "repository": manifest["source"]["repository"],
        "revision": manifest["source"]["revision"],
        "analyzer_input_sha256": sha256_file(analyzer_input),
        "component_map_sha256": sha256_file(component_map),
        "saved_analyzer_markdown_sha256": sha256_file(
            LIVE_ROOT / "inputs/analyzer-architecture.md"
        ),
    }
    results: list[dict[str, Any]] = []
    for run in manifest["runs"]:
        run_id = str(run["run_id"])
        destination = output / "runs" / run_id
        proposal = _proposal_identity(run)
        candidate = _manifest_path(run["artifacts"]["candidate.md"]["path"])
        base = {
            "run_id": run_id,
            "source_identity": source_identity,
            "proposal_identity": proposal,
            "original_canary_verdict": "rejected",
            "model_calls": 0,
            "legacy_response_state": "historical-response-missing",
            "legacy_response_available": False,
            "candidate_schema_compliance": "unavailable-not-emitted-as-structured-json",
            "candidate_content_converted": False,
        }
        try:
            validate_legacy_markdown(candidate.read_text())
        except LegacyConversionError as error:
            destination.mkdir(parents=True)
            result = {
                **base,
                "status": "conversion-error",
                "error": {"code": error.code, "detail": error.detail},
            }
            write_json(destination / "conversion-error.json", result)
            results.append(result)
            continue

        destination.mkdir(parents=True)
        shutil.copyfile(analyzer_input, destination / "analyzer.json")
        bundle_identity = content_hash(
            {
                "kind": "test-only-legacy-analyzer-replay",
                "analyzer_sha256": sha256_file(analyzer_input),
                "proposal_sha256": run["artifacts"]["candidate.md"]["sha256"],
            }
        )
        envelope = special_synthesis_envelope(
            "historical-response-missing",
            input_bundle_identity=bundle_identity,
            reason=(
                "saved legacy run retained Markdown and telemetry but no original "
                "structured synthesis response"
            ),
        )
        write_json(destination / "synthesis.json", envelope)
        normalize = [
            str(analyzer),
            "normalize",
            "--input",
            str(destination / "analyzer.json"),
            "--component-map",
            str(component_map),
            "--component-map-id",
            f"saved-canary:{sha256_file(component_map)}",
            "--version-scope",
            "rhoai-3.6-ea.2",
            "--integration-status",
            "current",
            "--distribution",
            "RHOAI",
            "--generated-by",
            "offline legacy analyzer replay; model response unavailable",
            "--output",
            str(destination / "document.json"),
        ]
        render = [
            str(analyzer),
            "render-document",
            "--input",
            str(destination / "document.json"),
            "--output",
            str(destination / "rhods-operator.md"),
        ]
        _run(normalize)
        _run(render)
        rendered = (destination / "rhods-operator.md").read_text()
        required_rbac = (
            "opendatahub-operator-metrics-reader",
            "metrics-reader",
        )
        missing_rbac = [name for name in required_rbac if name not in rendered]
        if missing_rbac:
            raise ValueError(
                f"offline renderer lost baseline RBAC rows: {missing_rbac}"
            )
        result = {
            **base,
            "status": "analyzer-only-replay-complete",
            "output": {
                name: {"sha256": sha256_file(destination / name)}
                for name in (
                    "analyzer.json",
                    "synthesis.json",
                    "document.json",
                    "rhods-operator.md",
                )
            },
            "document_schema_version": load_object(destination / "document.json")[
                "schema_version"
            ],
            "baseline_rbac_row_names_present": list(required_rbac),
            "limits": [
                "the renderer output contains deterministic analyzer facts only",
                "the original rejected promoted Markdown is unchanged",
                "the replay does not prove an agent can emit the structured schema",
                "legacy RBAC rows without URL values do not acquire invented URLs",
            ],
        }
        write_json(destination / "conversion.json", result)
        results.append(result)

    report = {
        "schema_version": "structured-component-offline-canary-replay/v1",
        "mode": "offline-test-only",
        "live_model_calls": 0,
        "analyzer_binary": {
            "path": str(analyzer),
            "sha256": sha256_file(analyzer),
        },
        "source_identity": source_identity,
        "canary_manifest_sha256": sha256_file(LIVE_ROOT / "manifest.json"),
        "verified_manifest_paths": canary_hashes,
        "historical_preservation": preservation,
        "original_verdict": load_object(LIVE_ROOT / "report.json")["conclusion"],
        "results": results,
        "summary": {
            "runs": len(results),
            "analyzer_only_replays": sum(
                item["status"] == "analyzer-only-replay-complete" for item in results
            ),
            "explicit_conversion_errors": sum(
                item["status"] == "conversion-error" for item in results
            ),
        },
    }
    write_json(output / "report.json", report)
    return report


def _git(*arguments: str) -> str:
    return _run(("git", *arguments)).stdout.strip()


def _current_analyzer_identity(binary: Path, build_command: str) -> dict[str, Any]:
    dirty = _run(
        ("git", "status", "--porcelain=v1", "-z", "--", "src/arch-analyzer")
    ).stdout
    paths = _git(
        "ls-files", "--cached", "--others", "--exclude-standard", "src/arch-analyzer"
    ).splitlines()
    sources = {path: sha256_file(ROOT / path) for path in sorted(paths)}
    payload = {
        "head": _git("rev-parse", "HEAD"),
        "sources": sources,
    }
    return {
        "head": payload["head"],
        # Preserve both porcelain columns. Stripping would misreport an
        # unstaged " M" entry as the different staged status "M ".
        "dirty_status": [entry for entry in dirty.split("\0") if entry],
        "source_file_count": len(sources),
        "source_manifest": sources,
        "source_identity": content_hash(payload),
        "binary_sha256": sha256_file(binary),
        "binary_size": binary.stat().st_size,
        "go_version": _run(("go", "version")).stdout.strip(),
        "go_build_info": _run(("go", "version", "-m", str(binary))).stdout.splitlines(),
        "build_command": build_command,
    }


def _historical_analyzer_identity(report: Mapping[str, Any]) -> dict[str, Any]:
    baseline = load_object(KICKOFF_HASHES)
    commit = str(report["analyzer"]["repo_head"])
    dirty: list[dict[str, str]] = []
    for path, working_hash in sorted(baseline.items()):
        if not path.startswith("src/arch-analyzer/"):
            continue
        completed = subprocess.run(
            ("git", "show", f"{commit}:{path}"),
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
        commit_hash = (
            sha256_bytes(completed.stdout)
            if completed.returncode == 0
            else "absent-at-commit"
        )
        if commit_hash != working_hash:
            dirty.append(
                {
                    "path": path,
                    "commit_sha256": commit_hash,
                    "recorded_worktree_sha256": str(working_hash),
                }
            )
    if len(dirty) != report["analyzer"]["src_arch_analyzer_dirty_files"]:
        raise ValueError("historical dirty analyzer identity cannot be reconstructed")
    return {
        "head": commit,
        "dirty_file_count": len(dirty),
        "dirty_files": dirty,
        "binary": report["analyzer"]["binary"],
        "binary_sha256": "unavailable-not-recorded",
        "identity_basis": str(KICKOFF_HASHES.relative_to(ROOT)),
        "identity_basis_sha256": sha256_file(KICKOFF_HASHES),
    }


def reproduce_reuse_comparison(
    output: Path, analyzer: Path, build_command: str
) -> dict[str, Any]:
    saved = load_object(REUSE_RESULT)
    components = saved["components"]
    totals = {
        "same_commit": sum(bool(item["same_commit"]) for item in components),
        "semantic": sum(bool(item["semantic"]) for item in components),
        "semantic_no_scancount": sum(
            bool(item["semantic_no_scancount"]) for item in components
        ),
        "semantic_no_scancount_no_depversions": sum(
            bool(item["semantic_no_scancount_no_depversions"]) for item in components
        ),
    }
    if totals != saved["totals"] or len(components) != saved["pair"]["common_repos"]:
        raise ValueError("saved reuse totals do not reproduce from component records")
    original_hash = sha256_file(ORIGINAL_COMPARISON)
    current_hash = sha256_file(CURRENT_COMPARISON)
    historical = _historical_analyzer_identity(saved)
    current = _current_analyzer_identity(analyzer, build_command)
    report = {
        "schema_version": "structured-component-reuse-comparison/v1",
        "mode": "offline-saved-result-reproduction",
        "saved_result": {
            "path": str(REUSE_RESULT.relative_to(ROOT)),
            "sha256": sha256_file(REUSE_RESULT),
            "common_repositories": len(components),
            "reproduced_totals": totals,
            "extraction_failures": saved["pair"]["extraction_failures"],
        },
        "comparison_implementation": {
            "pre_format_baseline": {
                "path": str(ORIGINAL_COMPARISON.relative_to(ROOT)),
                "sha256": original_hash,
            },
            "current": {
                "path": str(CURRENT_COMPARISON.relative_to(ROOT)),
                "sha256": current_hash,
            },
            "disposition": "independently-accepted-cleanup-formatting",
        },
        "recorded_historical_analyzer_build": historical,
        "fresh_current_analyzer_build": current,
        "build_comparability": {
            "comparable": False,
            "reason": (
                "the saved extraction pair was produced by the historical dirty "
                "build; the source checkouts and raw paired extractor outputs are "
                "not available to rerun with the fresh current build"
            ),
        },
        "candidate_reuse": {
            "same_commit": totals["same_commit"],
            "semantic": totals["semantic"],
            "semantic_after_scan_count_normalization": totals["semantic_no_scancount"],
            "dropping_dependency_versions_not_recommended": totals[
                "semantic_no_scancount_no_depversions"
            ],
        },
        "verified_reuse": {
            "count": 0,
            "reason": (
                "no saved row has the complete dependency record required by "
                "SC-14/SC-25"
            ),
        },
        "recorded_inputs": [
            "paired repository commit identities",
            "paired repository tree identities",
            "per-tier semantic fingerprints and differing categories",
            "normalization exclusions",
        ],
        "missing_required_inputs": [
            "raw paired analyzer extraction outputs",
            "the 92 exact source checkouts",
            "supporting source-read observations and whole-file hashes",
            "resolved search roots, patterns, options, result identities, and replay",
            "component configuration and applicable overlay identities",
            "synthesis contract, model settings, and complete context identity",
            "accepted structured predecessor snapshots and response identities",
        ],
        "measurements": {
            "pipeline_test_synthesis_calls": 0,
            "measured_live_model_calls": "unavailable-no-live-run",
            "tokens": "unavailable-no-live-run",
            "latency": "unavailable-no-live-run",
            "cost": "unavailable-no-live-run",
        },
    }
    write_json(output, report)
    return report


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    replay = subparsers.add_parser("replay-canary")
    replay.add_argument("--output-dir", type=Path, required=True)
    replay.add_argument("--arch-analyzer", type=Path, required=True)
    reuse = subparsers.add_parser("compare-reuse")
    reuse.add_argument("--output", type=Path, required=True)
    reuse.add_argument("--arch-analyzer", type=Path, required=True)
    reuse.add_argument("--build-command", required=True)
    fresh = subparsers.add_parser("fresh-compare-reuse")
    fresh.add_argument("--output-dir", type=Path, required=True)
    fresh.add_argument("--arch-analyzer", type=Path, required=True)
    fresh.add_argument("--source-audit", type=Path, required=True)
    fresh.add_argument("--prepared-inputs", type=Path, required=True)
    fresh.add_argument("--committed-analyzer-source", type=Path, required=True)
    fresh.add_argument("--expected-analyzer-commit", required=True)
    fresh.add_argument("--expected-archive-sha256", required=True)
    fresh.add_argument("--expected-binary-sha256", required=True)
    fresh.add_argument("--build-command", required=True)
    fresh.add_argument("--jobs", type=int, default=4)
    fresh.add_argument("--timeout-seconds", type=int, default=900)
    fresh.add_argument("--scratch-root", type=Path)
    fresh.add_argument("--successful-extractions-from", type=Path)
    preservation = subparsers.add_parser("verify-preservation")
    preservation.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    install_model_transport_guard()
    args = parse_args(argv)
    if args.command == "replay-canary":
        result = replay_saved_canary(
            args.output_dir.resolve(), args.arch_analyzer.resolve()
        )
    elif args.command == "compare-reuse":
        result = reproduce_reuse_comparison(
            args.output.resolve(), args.arch_analyzer.resolve(), args.build_command
        )
    elif args.command == "fresh-compare-reuse":
        prepared = load_object(args.prepared_inputs.resolve())
        if (
            Path(prepared["analyzer_source"]).resolve()
            != args.committed_analyzer_source.resolve()
        ):
            raise ValueError(
                "prepared analyzer source argument does not match manifest"
            )
        if args.jobs < 1 or args.jobs > 16:
            raise ValueError("jobs must be between 1 and 16")
        if args.timeout_seconds < 1:
            raise ValueError("timeout must be positive")
        result = fresh_compare_reuse(
            root=ROOT,
            output=args.output_dir.resolve(),
            analyzer=args.arch_analyzer.resolve(),
            source_audit=args.source_audit.resolve(),
            prepared_inputs=args.prepared_inputs.resolve(),
            comparison_script=CURRENT_COMPARISON,
            expected_commit=args.expected_analyzer_commit,
            expected_archive_sha256=args.expected_archive_sha256,
            expected_binary_sha256=args.expected_binary_sha256,
            build_command=args.build_command,
            jobs=args.jobs,
            timeout_seconds=args.timeout_seconds,
            scratch_root=args.scratch_root.resolve() if args.scratch_root else None,
            successful_extractions_from=(
                args.successful_extractions_from.resolve()
                if args.successful_extractions_from
                else None
            ),
        )
    else:
        result = verify_historical_preservation()
        write_json(args.output.resolve(), result)
    print(json.dumps(result.get("summary", result), sort_keys=True))
    if (
        args.command == "fresh-compare-reuse"
        and result["summary"]["failed_extractions"]
    ):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
