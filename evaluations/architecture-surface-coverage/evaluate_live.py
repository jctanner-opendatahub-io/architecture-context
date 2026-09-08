#!/usr/bin/env python3
"""Reproduce the retained, source-reviewed repeated live canary report."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "architecture-surface-live-canary/v1"
REVIEW_SCHEMA_VERSION = "architecture-surface-live-source-review/v1"
REPORT_SCHEMA_VERSION = "architecture-surface-live-report/v1"
CLAIM_STATUSES = frozenset({"supported", "omitted", "unsupported"})
DEPENDENCY_REFERENCE_RE = re.compile(r"^([^@]+)@([^/]+)/")


class LiveCanaryError(ValueError):
    """Raised when retained evidence cannot reproduce the live report."""


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise LiveCanaryError(f"{path}: expected a JSON object")
    return payload


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise LiveCanaryError(message)


def relative_artifact(evaluation_root: Path, value: object, label: str) -> Path:
    require(isinstance(value, str) and bool(value), f"{label} must be a path")
    path = Path(value)
    require(not path.is_absolute() and ".." not in path.parts, f"{label} is unsafe")
    resolved = evaluation_root / path
    require(resolved.is_file(), f"{label} does not exist: {path}")
    return resolved


def verify_hashed_artifact(evaluation_root: Path, artifact: object, label: str) -> Path:
    require(isinstance(artifact, dict), f"{label} must be an object")
    path = relative_artifact(evaluation_root, artifact.get("path"), f"{label}.path")
    expected = artifact.get("sha256")
    require(
        isinstance(expected, str) and len(expected) == 64,
        f"{label}.sha256 must be SHA-256",
    )
    require(sha256(path) == expected, f"{label} hash mismatch")
    return path


def validate_manifest(
    manifest: dict[str, Any], manifest_path: Path
) -> tuple[Path, dict[str, Any]]:
    require(manifest.get("schema_version") == SCHEMA_VERSION, "invalid manifest schema")
    evaluation_root = manifest_path.parent.parent
    settings = manifest.get("settings")
    require(isinstance(settings, dict), "settings must be an object")
    require(
        settings.get("models") == {"claude": "claude-opus-4-6", "codex": "gpt-5.6-sol"},
        "exact canary models are not pinned",
    )
    require(settings.get("repetitions_per_model") == 2, "expected two repetitions")
    require(settings.get("workers_enabled") is False, "workers must remain disabled")
    require(
        settings.get("coverage_enforcement") == "warning-only",
        "coverage must remain warning-only",
    )
    require(
        settings.get("historical_summary_synthesis_input") is False,
        "historical summaries cannot be synthesis inputs",
    )
    auth = settings.get("claude_auth")
    require(isinstance(auth, dict), "Claude auth record is missing")
    require(
        auth.get("logged_in") is True
        and auth.get("auth_method") == "claude.ai"
        and auth.get("api_provider") == "firstParty",
        "Claude provider was not recorded as first-party claude.ai",
    )
    require(
        set(auth.get("vertex_environment_removed", []))
        == {
            "CLAUDE_CODE_USE_VERTEX",
            "ANTHROPIC_VERTEX_PROJECT_ID",
            "CLOUD_ML_REGION",
        },
        "Vertex environment removals are incomplete",
    )

    source = manifest.get("source")
    require(isinstance(source, dict), "source must be an object")
    revision = source.get("revision")
    require(
        isinstance(revision, str)
        and len(revision) == 40
        and all(character in "0123456789abcdef" for character in revision),
        "source revision must be a full lowercase SHA",
    )

    inputs = manifest.get("inputs")
    require(isinstance(inputs, dict), "inputs must be an object")
    for name in (
        "component_map",
        "component_architecture",
        "analyzer_architecture",
        "analyzer_synthesis_context",
    ):
        verify_hashed_artifact(evaluation_root, inputs.get(name), f"inputs.{name}")
    analyzer_binary_sha = inputs.get("analyzer_binary_sha256")
    require(
        isinstance(analyzer_binary_sha, str) and len(analyzer_binary_sha) == 64,
        "analyzer binary hash is missing",
    )

    expected_claims = manifest.get("expected_claims")
    require(isinstance(expected_claims, dict), "expected_claims must be an object")
    expected_path = relative_artifact(
        evaluation_root, expected_claims.get("manifest"), "expected_claims.manifest"
    )
    require(
        sha256(expected_path) == expected_claims.get("manifest_sha256"),
        "expected-claim manifest hash mismatch",
    )
    experiment = load_json(expected_path)
    claim_to_surface: dict[str, str] = {}
    for surface in experiment.get("surfaces", []):
        surface_id = surface.get("surface_id")
        for claim in surface.get("required_claims", []):
            claim_id = claim.get("claim_id")
            require(
                claim_id not in claim_to_surface,
                f"duplicate expected claim: {claim_id}",
            )
            claim_to_surface[claim_id] = surface_id
    require(
        len(claim_to_surface) == expected_claims.get("claim_count") == 7,
        "expected claim count mismatch",
    )
    require(
        len(set(claim_to_surface.values()))
        == expected_claims.get("surface_count")
        == 4,
        "expected surface count mismatch",
    )

    historical = manifest.get("historical_comparison")
    require(isinstance(historical, dict), "historical comparison must be an object")
    require(
        historical.get("comparison_only") is True, "history must be comparison-only"
    )
    require(
        historical.get("matched_live_baseline") is False,
        "history cannot be labeled a matched live baseline",
    )
    historical_path = relative_artifact(
        evaluation_root, historical.get("report"), "historical_comparison.report"
    )
    require(
        sha256(historical_path) == historical.get("report_sha256"),
        "historical report hash mismatch",
    )
    return evaluation_root, claim_to_surface


def surface_results(
    claim_results: list[dict[str, Any]], claim_to_surface: dict[str, str]
) -> list[dict[str, Any]]:
    by_surface: dict[str, list[str]] = defaultdict(list)
    for result in claim_results:
        by_surface[claim_to_surface[result["claim_id"]]].append(result["status"])
    output = []
    for surface_id in sorted(set(claim_to_surface.values())):
        statuses = by_surface[surface_id]
        if "unsupported" in statuses:
            status = "unsupported"
        elif all(item == "supported" for item in statuses):
            status = "supported"
        elif all(item == "omitted" for item in statuses):
            status = "omitted"
        else:
            status = "partial"
        output.append(
            {
                "surface_id": surface_id,
                "status": status,
                "supported_claims": statuses.count("supported"),
                "claim_count": len(statuses),
            }
        )
    return output


def normalize_usage(harness: str, telemetry: dict[str, Any]) -> dict[str, Any]:
    if harness == "codex":
        usage = telemetry.get("usage", {})
        return {
            "kind": "codex-cumulative",
            "total": usage.get("total"),
            "last": usage.get("last"),
            "model_context_window": usage.get("model_context_window"),
        }
    model_usage = telemetry.get("model_usage", {})
    return {
        "kind": "claude-model-usage",
        "primary": model_usage.get("claude-opus-4-6"),
        "internal_helper": model_usage.get("claude-haiku-4-5-20251001"),
        "total_cost_usd": telemetry.get("total_cost_usd"),
        "num_turns": telemetry.get("num_turns"),
    }


def validate_retained_input_manifest(
    input_manifest: dict[str, Any],
    expected_input_hashes: dict[str, str],
    *,
    run_id: str,
    harness: str,
    model: str,
    repetition: int,
) -> None:
    """Validate the hashes and invocation identity copied into one run."""

    require(input_manifest.get("model") == model, f"{run_id}: input model mismatch")
    require(
        input_manifest.get("harness") == harness,
        f"{run_id}: input harness mismatch",
    )
    require(
        input_manifest.get("repetition") == repetition,
        f"{run_id}: input repetition mismatch",
    )
    require(
        input_manifest.get("historical_summary_synthesis_input") is False,
        f"{run_id}: historical input invariant failed",
    )
    require(
        input_manifest.get("inputs") == expected_input_hashes,
        f"{run_id}: retained input manifest hash mismatch",
    )


def validate_review(
    review: dict[str, Any],
    run_ids: set[str],
    claim_to_surface: dict[str, str],
    dependency_versions: dict[str, str] | None = None,
) -> dict[str, dict[str, Any]]:
    require(
        review.get("schema_version") == REVIEW_SCHEMA_VERSION, "invalid review schema"
    )
    records = review.get("runs")
    require(isinstance(records, list), "review runs must be an array")
    by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        require(isinstance(record, dict), "review run must be an object")
        run_id = record.get("run_id")
        require(
            run_id in run_ids and run_id not in by_id, f"invalid review run: {run_id}"
        )
        claims = record.get("claim_results")
        require(isinstance(claims, list), f"{run_id}: claim_results must be an array")
        claim_ids = {item.get("claim_id") for item in claims if isinstance(item, dict)}
        require(
            claim_ids == set(claim_to_surface), f"{run_id}: claim coverage mismatch"
        )
        for item in claims:
            require(
                item.get("status") in CLAIM_STATUSES, f"{run_id}: invalid claim status"
            )
            bases = item.get("review_basis")
            require(
                isinstance(bases, list) and bases, f"{run_id}: review basis missing"
            )
        unsupported = record.get("unsupported_claims")
        require(isinstance(unsupported, list), f"{run_id}: unsupported_claims missing")
        for claim in unsupported:
            require(isinstance(claim, dict), f"{run_id}: invalid unsupported claim")
            bases = claim.get("review_basis")
            require(
                isinstance(bases, list) and bases,
                f"{run_id}: unsupported claim review basis missing",
            )
            for reference in bases:
                match = DEPENDENCY_REFERENCE_RE.match(reference)
                if match is None or dependency_versions is None:
                    continue
                module, version = match.groups()
                require(
                    dependency_versions.get(module) == version,
                    f"{run_id}: review dependency version mismatch for {module}",
                )
        row_losses = record.get("analyzer_row_losses")
        require(isinstance(row_losses, list), f"{run_id}: analyzer_row_losses missing")
        for loss in row_losses:
            require(isinstance(loss, dict), f"{run_id}: invalid analyzer row loss")
            require(
                isinstance(loss.get("row"), str) and bool(loss["row"]),
                f"{run_id}: analyzer row loss is missing its exact row",
            )
            require(
                loss.get("promoted_absent") is True,
                f"{run_id}: analyzer row loss must record promoted absence",
            )
            require(
                loss.get("merge_reported_loss") is False,
                f"{run_id}: retained merge discrepancy is not recorded",
            )
        warnings = record.get("warning_review")
        require(isinstance(warnings, dict), f"{run_id}: warning review missing")
        require(
            warnings.get("emitted")
            == warnings.get("artifact_contract", 0)
            + warnings.get("semantic_signal", 0)
            + warnings.get("false_positive", 0),
            f"{run_id}: warning classifications do not sum",
        )
        by_id[run_id] = record
    require(set(by_id) == run_ids, "source review does not cover every run")
    return by_id


def retained_dependency_version(analyzer_markdown: str, module: str) -> str:
    """Read one exact dependency version from the retained analyzer table."""

    pattern = re.compile(
        rf"(?m)^\|\s*{re.escape(module)}\s*\|\s*([^|\s]+)\s*\|"
    )
    matches = pattern.findall(analyzer_markdown)
    require(len(matches) == 1, f"expected one retained dependency row for {module}")
    return matches[0]


def evaluate(manifest_path: Path, review_path: Path) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    review = load_json(review_path)
    evaluation_root, claim_to_surface = validate_manifest(manifest, manifest_path)
    recorded_review_path = verify_hashed_artifact(
        evaluation_root, manifest.get("source_review"), "source_review"
    )
    require(
        recorded_review_path.resolve() == review_path.resolve(),
        "source review path does not match the manifest",
    )
    runs = manifest.get("runs")
    require(isinstance(runs, list) and len(runs) == 4, "expected four live runs")
    run_ids = {run.get("run_id") for run in runs if isinstance(run, dict)}
    require(len(run_ids) == 4 and None not in run_ids, "run IDs must be unique")
    analyzer_input_path = verify_hashed_artifact(
        evaluation_root,
        manifest["inputs"]["analyzer_architecture"],
        "inputs.analyzer_architecture",
    )
    dependency_versions = {
        "sigs.k8s.io/controller-runtime": retained_dependency_version(
            analyzer_input_path.read_text(), "sigs.k8s.io/controller-runtime"
        )
    }
    reviews = validate_review(
        review,
        run_ids,
        claim_to_surface,
        dependency_versions=dependency_versions,
    )

    expected_models = manifest["settings"]["models"]
    expected_input_hashes = {
        "component_map_sha256": manifest["inputs"]["component_map"]["sha256"],
        "component_architecture_sha256": manifest["inputs"]["component_architecture"][
            "sha256"
        ],
        "analyzer_architecture_sha256": manifest["inputs"]["analyzer_architecture"][
            "sha256"
        ],
        "analyzer_synthesis_context_sha256": manifest["inputs"][
            "analyzer_synthesis_context"
        ]["sha256"],
        "analyzer_binary_sha256": manifest["inputs"]["analyzer_binary_sha256"],
    }
    results: list[dict[str, Any]] = []
    surface_inventory_hashes: set[str] = set()
    for record in runs:
        run_id = record["run_id"]
        harness = record["harness"]
        model = record["model"]
        require(model == expected_models.get(harness), f"{run_id}: model mismatch")
        require(record.get("repetition") in {1, 2}, f"{run_id}: invalid repetition")
        require(
            record.get("source_checkout", {}).get("clean") is True,
            f"{run_id}: dirty source",
        )
        require(
            record.get("source_checkout", {}).get("revision")
            == manifest["source"]["revision"],
            f"{run_id}: source revision mismatch",
        )
        require(
            record.get("observed_input_hashes") == expected_input_hashes,
            f"{run_id}: input hash mismatch",
        )

        artifacts = record.get("artifacts")
        require(isinstance(artifacts, dict), f"{run_id}: artifacts missing")
        resolved = {
            name: verify_hashed_artifact(evaluation_root, value, f"{run_id}.{name}")
            for name, value in artifacts.items()
        }
        for required_name in (
            "candidate.md",
            "coverage.json",
            "input-manifest.json",
            "invocation.txt",
            "merge.json",
            "preseed.md",
            "promoted.md",
            "run.json",
            "source-read-justifications.json",
            "surface-inventory.json",
        ):
            require(required_name in resolved, f"{run_id}: missing {required_name}")

        invocation = resolved["invocation.txt"].read_text()
        require(
            f"Model: {model}\n" in invocation, f"{run_id}: invocation model mismatch"
        )
        promoted = resolved["promoted.md"].read_text()
        require(
            f"**Generated By**: {model}" in promoted,
            f"{run_id}: promoted model mismatch",
        )
        input_manifest = load_json(resolved["input-manifest.json"])
        validate_retained_input_manifest(
            input_manifest,
            expected_input_hashes,
            run_id=run_id,
            harness=harness,
            model=model,
            repetition=record["repetition"],
        )
        require(
            sha256(resolved["preseed.md"])
            == expected_input_hashes["analyzer_architecture_sha256"],
            f"{run_id}: retained analyzer preseed hash mismatch",
        )
        surface_inventory_hashes.add(
            record["artifacts"]["surface-inventory.json"]["sha256"]
        )

        run_payload = load_json(resolved["run.json"])
        merge = load_json(resolved["merge.json"])
        require(run_payload.get("success") is True, f"{run_id}: run failed")
        require(run_payload.get("error") is None, f"{run_id}: run error recorded")
        require(run_payload.get("fallback") is None, f"{run_id}: fallback was used")
        duration = float(run_payload["duration_seconds"])
        require(
            duration <= record["limits"]["wall_clock_seconds"],
            f"{run_id}: wall-clock limit exceeded",
        )
        telemetry = run_payload.get("telemetry", {})
        require(isinstance(telemetry, dict), f"{run_id}: telemetry missing")
        if harness == "claude":
            require(
                telemetry.get("claude_credentials_staged") is True,
                f"{run_id}: auth not staged",
            )
            require(
                model in telemetry.get("model_usage", {}),
                f"{run_id}: primary model absent",
            )
            require(
                telemetry.get("total_cost_usd") <= record["limits"]["max_budget_usd"],
                f"{run_id}: Claude budget exceeded",
            )
        else:
            require(
                telemetry.get("harness") == "codex",
                f"{run_id}: harness telemetry mismatch",
            )
            require(
                telemetry.get("immutable_input_check") == "passed",
                f"{run_id}: Codex immutable input check failed",
            )

        source_count = int(telemetry.get("source_file_count", 0))
        file_budget = int(manifest["settings"]["file_budget"])
        warning_review = reviews[run_id]["warning_review"]
        coverage = run_payload.get("surface_coverage", {})
        require(
            warning_review["emitted"] == coverage.get("warning_count"),
            f"{run_id}: warning count mismatch",
        )
        claims = reviews[run_id]["claim_results"]
        surfaces = surface_results(claims, claim_to_surface)
        supported_claims = sum(item["status"] == "supported" for item in claims)
        supported_surfaces = sum(item["status"] == "supported" for item in surfaces)

        losses = reviews[run_id].get("candidate_to_promoted_losses", [])
        for loss in losses:
            if loss.get("surface_id") == "compliance.runtime-fips":
                require(
                    "### FIPS Compliance" in resolved["candidate.md"].read_text()
                    and "### FIPS Compliance" not in promoted,
                    f"{run_id}: retained FIPS loss does not reproduce",
                )
        analyzer_row_losses = reviews[run_id]["analyzer_row_losses"]
        preseed = resolved["preseed.md"].read_text()
        candidate = resolved["candidate.md"].read_text()
        for loss in analyzer_row_losses:
            row = loss["row"]
            require(
                row in preseed and row in candidate and row not in promoted,
                f"{run_id}: retained analyzer row loss does not reproduce: {row}",
            )

        results.append(
            {
                "run_id": run_id,
                "harness": harness,
                "model": model,
                "repetition": record["repetition"],
                "success": True,
                "duration_seconds": round(duration, 6),
                "source_reads": {
                    "unique_files": source_count,
                    "operations": telemetry.get("source_read_operations"),
                    "file_budget": file_budget,
                    "budget_exceeded_by": max(0, source_count - file_budget),
                    "files": telemetry.get("source_files_read", []),
                    "telemetry_discovery_calls": run_payload.get(
                        "runtime_breakdown", {}
                    )
                    .get("agent_activity_counts", {})
                    .get("targeted_discovery_calls"),
                    "codex_discovery_observation_limit": (
                        "command telemetry does not classify rg discovery separately"
                        if harness == "codex"
                        else None
                    ),
                },
                "usage": normalize_usage(harness, telemetry),
                "merge": {
                    **merge.get("counts", {}),
                    "candidate_to_promoted_surface_losses": len(losses),
                    "losses": losses,
                },
                "coverage_validator": {
                    "status": coverage.get("status"),
                    "structural_valid": coverage.get("structural_valid"),
                    "summary": coverage.get("summary"),
                    "warning_count": coverage.get("warning_count"),
                },
                "source_review": {
                    "claim_recall": round(supported_claims / len(claims), 6),
                    "surface_recall": round(supported_surfaces / len(surfaces), 6),
                    "claim_results": claims,
                    "surface_results": surfaces,
                    "unsupported_claim_count": len(
                        reviews[run_id]["unsupported_claims"]
                    ),
                    "unsupported_claims": reviews[run_id]["unsupported_claims"],
                    "warning_review": warning_review,
                },
                "preservation": {
                    "input_hashes_match": True,
                    "checkout_clean_at_pinned_revision": True,
                    "merge_reported_unchanged_rows": merge.get("counts", {}).get(
                        "unchanged"
                    ),
                    "analyzer_output_preserved": not analyzer_row_losses,
                    "analyzer_row_loss_count": len(analyzer_row_losses),
                    "analyzer_row_losses": analyzer_row_losses,
                },
            }
        )

    results.sort(key=lambda item: (item["harness"], item["repetition"]))
    require(
        len(surface_inventory_hashes) == 1,
        "retained surface inventories differ across runs",
    )
    harnesses = []
    for harness in ("claude", "codex"):
        selected = [item for item in results if item["harness"] == harness]
        require(len(selected) == 2, f"{harness}: expected two repetitions")
        repeated_surfaces = []
        surface_ids = [
            item["surface_id"]
            for item in selected[0]["source_review"]["surface_results"]
        ]
        for surface_id in surface_ids:
            statuses = [
                next(
                    surface["status"]
                    for surface in item["source_review"]["surface_results"]
                    if surface["surface_id"] == surface_id
                )
                for item in selected
            ]
            repeated_surfaces.append(
                {
                    "surface_id": surface_id,
                    "statuses": statuses,
                    "supported_repetitions": statuses.count("supported"),
                    "repeat_count": 2,
                }
            )
        recalls = [item["source_review"]["surface_recall"] for item in selected]
        harnesses.append(
            {
                "harness": harness,
                "model": selected[0]["model"],
                "repeat_count": 2,
                "surface_recall": {
                    "mean": round(statistics.fmean(recalls), 6),
                    "minimum": min(recalls),
                    "maximum": max(recalls),
                },
                "claim_recall": {
                    "mean": round(
                        statistics.fmean(
                            item["source_review"]["claim_recall"] for item in selected
                        ),
                        6,
                    ),
                    "minimum": min(
                        item["source_review"]["claim_recall"] for item in selected
                    ),
                    "maximum": max(
                        item["source_review"]["claim_recall"] for item in selected
                    ),
                },
                "unsupported_claims": sum(
                    item["source_review"]["unsupported_claim_count"]
                    for item in selected
                ),
                "runs_meeting_source_review_gates": sum(
                    item["source_review"]["surface_recall"] == 1.0
                    and item["source_review"]["unsupported_claim_count"] == 0
                    for item in selected
                ),
                "repeated_surface_results": repeated_surfaces,
                "duration_seconds": {
                    "mean": round(
                        statistics.fmean(item["duration_seconds"] for item in selected),
                        6,
                    ),
                    "minimum": min(item["duration_seconds"] for item in selected),
                    "maximum": max(item["duration_seconds"] for item in selected),
                },
                "source_file_count": {
                    "mean": round(
                        statistics.fmean(
                            item["source_reads"]["unique_files"] for item in selected
                        ),
                        6,
                    ),
                    "minimum": min(
                        item["source_reads"]["unique_files"] for item in selected
                    ),
                    "maximum": max(
                        item["source_reads"]["unique_files"] for item in selected
                    ),
                },
                "warning_count": {
                    "mean": round(
                        statistics.fmean(
                            item["coverage_validator"]["warning_count"]
                            for item in selected
                        ),
                        6,
                    ),
                    "minimum": min(
                        item["coverage_validator"]["warning_count"] for item in selected
                    ),
                    "maximum": max(
                        item["coverage_validator"]["warning_count"] for item in selected
                    ),
                },
            }
        )

    warning_totals = {
        key: sum(item["source_review"]["warning_review"][key] for item in results)
        for key in ("emitted", "artifact_contract", "semantic_signal", "false_positive")
    }
    claude_cost = sum(
        item["usage"].get("total_cost_usd", 0)
        for item in results
        if item["harness"] == "claude"
    )
    codex_tokens = sum(
        item["usage"].get("total", {}).get("total_tokens", 0)
        for item in results
        if item["harness"] == "codex"
    )
    successful_runs = sum(item["success"] for item in results)
    all_inputs_preserved = all(
        item["preservation"]["input_hashes_match"] for item in results
    )
    all_checkouts_clean = all(
        item["preservation"]["checkout_clean_at_pinned_revision"]
        for item in results
    )
    analyzer_output_preserved = all(
        item["preservation"]["analyzer_output_preserved"] for item in results
    )
    analyzer_row_loss_count = sum(
        item["preservation"]["analyzer_row_loss_count"] for item in results
    )
    promotion_failure_runs = sum(
        bool(item["preservation"]["analyzer_row_loss_count"])
        or bool(item["merge"]["candidate_to_promoted_surface_losses"])
        for item in results
    )
    candidate_surface_loss_count = sum(
        item["merge"]["candidate_to_promoted_surface_losses"] for item in results
    )
    structurally_invalid_sidecars = sum(
        item["coverage_validator"]["structural_valid"] is not True for item in results
    )
    harness_by_name = {item["harness"]: item for item in harnesses}
    codex_two_of_two = (
        harness_by_name["codex"]["runs_meeting_source_review_gates"] == 2
    )
    claude_two_of_two = (
        harness_by_name["claude"]["runs_meeting_source_review_gates"] == 2
    )
    historical_input_excluded = (
        manifest["settings"]["historical_summary_synthesis_input"] is False
        and all(
            item["historical_summary_synthesis_input"] is False
            for item in (
                load_json(
                    verify_hashed_artifact(
                        evaluation_root,
                        record["artifacts"]["input-manifest.json"],
                        f"{record['run_id']}.input-manifest.json",
                    )
                )
                for record in runs
            )
        )
    )
    provider_preflight_retained = all(
        "provider-preflight.json" in record["artifacts"]
        for record in runs
        if record["harness"] == "claude"
    )
    full_prompt_or_transcript_retained = all(
        "prompt.txt" in record["artifacts"] or "transcript.jsonl" in record["artifacts"]
        for record in runs
    )
    canary_execution_accepted = (
        successful_runs == len(results)
        and all_inputs_preserved
        and all_checkouts_clean
        and historical_input_excluded
        and promotion_failure_runs == 0
    )
    codex_passing_runs = harness_by_name["codex"][
        "runs_meeting_source_review_gates"
    ]
    claude_passing_runs = harness_by_name["claude"][
        "runs_meeting_source_review_gates"
    ]
    reason = (
        f"The canary is rejected because promotion failed in "
        f"{promotion_failure_runs} of {len(results)} runs: final output lost "
        f"{analyzer_row_loss_count} analyzer-row occurrences. Codex passed the "
        f"source-review gate in {codex_passing_runs} of 2 repetitions and Claude "
        f"passed in {claude_passing_runs} of 2; "
        f"{structurally_invalid_sidecars} sidecars were structurally invalid and "
        f"{warning_totals['false_positive']} of {warning_totals['emitted']} warnings "
        "were confirmed false positives."
    )
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "canary_id": manifest["canary_id"],
        "source": manifest["source"],
        "settings": manifest["settings"],
        "execution": {
            "run_count": len(results),
            "successful_agent_runs": successful_runs,
            "claude_aggregate_cost_usd": round(claude_cost, 6),
            "claude_aggregate_budget_usd": sum(
                record["limits"].get("max_budget_usd") or 0
                for record in runs
                if record["harness"] == "claude"
            ),
            "codex_aggregate_total_tokens": codex_tokens,
            "all_inputs_preserved": all_inputs_preserved,
            "all_checkouts_clean": all_checkouts_clean,
            "historical_summary_synthesis_input": not historical_input_excluded,
            "analyzer_output_preserved": analyzer_output_preserved,
            "analyzer_row_loss_count": analyzer_row_loss_count,
            "candidate_surface_loss_count": candidate_surface_loss_count,
            "promotion_failure_runs": promotion_failure_runs,
            "surface_inventories_identical": len(surface_inventory_hashes) == 1,
        },
        "warning_quality": warning_totals
        | {
            "false_positive_rate": round(
                warning_totals["false_positive"] / warning_totals["emitted"], 6
            )
        },
        "runs": results,
        "harnesses": harnesses,
        "historical_comparison": {
            "comparison_only": manifest["historical_comparison"]["comparison_only"],
            "matched_live_baseline": manifest["historical_comparison"][
                "matched_live_baseline"
            ],
            "observation": (
                "The historical single outputs had complementary 0.5 surface recall. "
                "The retained live runs use refreshed analyzer evidence and "
                "therefore are not a matched baseline."
            ),
        },
        "provenance": {
            "requested_models_pinned": all(
                item["model"] == expected_models[item["harness"]] for item in results
            ),
            "claude_launch_record": manifest["settings"]["claude_auth"],
            "provider_preflight_retained": provider_preflight_retained,
            "provider_limitation": (
                "The operator-run preflight recorded firstParty claude.ai and the "
                "launch removed all three Vertex selectors, but the retained artifact "
                "set has no hashed per-run provider preflight transcript."
            ),
            "model_limitation": (
                "Requested model IDs and runner telemetry are pinned; the retained "
                "artifacts do not contain a service-signed model-identity attestation."
            ),
            "historical_input_exclusion_recorded": historical_input_excluded,
            "full_prompt_or_transcript_retained": full_prompt_or_transcript_retained,
            "historical_input_limitation": (
                "Per-run input manifests record that historical summaries were not "
                "synthesis inputs, but no full prompt or raw transcript was retained."
            ),
        },
        "conclusion": {
            "canary_execution_accepted": canary_execution_accepted,
            "codex_two_of_two_source_review_gate": codex_two_of_two,
            "claude_two_of_two_source_review_gate": claude_two_of_two,
            "coverage_enforcement": manifest["settings"]["coverage_enforcement"],
            "subsection_workers_enabled": manifest["settings"]["workers_enabled"],
            "rollout_change_justified": (
                canary_execution_accepted and codex_two_of_two and claude_two_of_two
            ),
            "reason": reason,
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    harness_by_name = {item["harness"]: item for item in report["harnesses"]}
    lines = [
        "# Repeated Live Architecture Surface Canary",
        "",
        "## Result",
        "",
        (
            f"All {report['execution']['run_count']} isolated agent runs completed at "
            "the recorded pinned source revision with the requested exact models and "
            "hash-identical retained inputs. The canary is rejected because every "
            "promoted document lost two analyzer-rendered RBAC rows. Coverage remains "
            "warning-only and subsection workers remain disabled."
        ),
        "",
        "The operator-run Claude preflight recorded first-party `claude.ai` "
        "authentication, and `CLAUDE_CODE_USE_VERTEX`, "
        "`ANTHROPIC_VERTEX_PROJECT_ID`, and `CLOUD_ML_REGION` were explicitly "
        "removed from each launch. The durable artifact set does not include a "
        "hashed per-run provider-preflight transcript, so it cannot independently "
        "re-attest the provider after the run.",
        "",
        "## Repeated source review",
        "",
        "| Harness | Exact model | Surface recall | Claim recall | Unsupported "
        "claims | Runs passing gate |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for harness in ("claude", "codex"):
        item = harness_by_name[harness]
        lines.append(
            f"| {harness} | `{item['model']}` | {item['surface_recall']['mean']:.3f} | "
            f"{item['claim_recall']['mean']:.3f} | {item['unsupported_claims']} | "
            f"{item['runs_meeting_source_review_gates']}/2 |"
        )
    lines.extend(
        [
            "",
            "| Surface | Claude | Codex |",
            "|---|---|---|",
        ]
    )
    surface_ids = [
        item["surface_id"]
        for item in harness_by_name["claude"]["repeated_surface_results"]
    ]
    for surface_id in surface_ids:
        cells = []
        for harness in ("claude", "codex"):
            entry = next(
                item
                for item in harness_by_name[harness]["repeated_surface_results"]
                if item["surface_id"] == surface_id
            )
            cells.append(", ".join(entry["statuses"]))
        lines.append(f"| `{surface_id}` | {cells[0]} | {cells[1]} |")

    lines.extend(
        [
            "",
            "Claude recalled conditional metrics enforcement and both literal "
            "namespace watches in both runs. Neither Claude run fully represented "
            "integrated OAuth, external OIDC, and externally managed authentication. "
            "Repetition 1 promoted unsupported FIPS, linkage, and gateway-proxy "
            "claims; repetition 2 "
            "authored a FIPS section in the candidate, but final assembly removed it.",
            "",
            "Both Codex runs represented all seven required claims across the four "
            "surfaces and explicitly stated that build and TLS signals do not "
            "establish runtime FIPS compliance. Repetition 1 also made an unsupported "
            "initialization-ordering claim outside those four required surfaces, so "
            "only Codex repetition 2 passed the zero-unsupported-claim gate.",
            "",
            "## Run measurements",
            "",
            "| Run | Duration | Files | Budget delta | Merge | Warnings | Surface "
            "recall | Unsupported | Usage |",
            "|---|---:|---:|---:|---|---:|---:|---:|---|",
        ]
    )
    for item in report["runs"]:
        merge = item["merge"]
        if item["harness"] == "claude":
            usage = f"${item['usage']['total_cost_usd']:.4f}"
        else:
            usage = f"{item['usage']['total']['total_tokens']:,} tokens"
        lines.append(
            f"| `{item['run_id']}` | {item['duration_seconds']:.1f}s | "
            f"{item['source_reads']['unique_files']} | "
            f"+{item['source_reads']['budget_exceeded_by']} | "
            f"{merge.get('applied', 0)} applied/{merge.get('rejected', 0)} rejected/"
            f"{merge.get('restored', 0)} restored | "
            f"{item['coverage_validator']['warning_count']} | "
            f"{item['source_review']['surface_recall']:.3f} | "
            f"{item['source_review']['unsupported_claim_count']} | {usage} |"
        )

    warning = report["warning_quality"]
    lines.extend(
        [
            "",
            "Claude aggregate cost was "
            f"`${report['execution']['claude_aggregate_cost_usd']:.4f}` against the "
            "approved `$40` aggregate cap. Codex reported "
            f"`{report['execution']['codex_aggregate_total_tokens']:,}` cumulative "
            "tokens across its two single-turn runs. Codex command telemetry does "
            "not classify its `rg` discovery calls separately, so the retained zero "
            "discovery count is an instrumentation limit rather than proof of "
            "no search.",
            "",
            "## Warning and promotion quality",
            "",
            f"The validator emitted {warning['emitted']} messages: "
            f"{warning['artifact_contract']} sidecar-contract diagnostics, "
            f"{warning['semantic_signal']} useful semantic signals, and "
            f"{warning['false_positive']} confirmed false positives "
            f"({warning['false_positive_rate']:.1%}). The false positives mostly "
            "reported missing document references even when source-reviewed content "
            "was present.",
            "",
            "Every promoted document lost the analyzer-rendered "
            "`opendatahub-operator-metrics-reader` and `metrics-reader` RBAC rows, "
            "for eight lost row occurrences across four runs. The merge reports still "
            "recorded 274 unchanged rows and zero restorations because those two rows "
            "were outside the parser's accounted set. Claude repetition 2 also lost "
            "`compliance.runtime-fips` between candidate and promoted output. Its "
            "coverage validator detected that surface omission, but the merge report "
            "did not. These are promotion failures under the approved stop conditions.",
            "",
            "The two Claude patches each applied one evidence-backed metrics "
            "authentication row; both Codex patches were empty.",
            "",
            "## Provenance limits",
            "",
            report["provenance"]["model_limitation"],
            "",
            report["provenance"]["historical_input_limitation"],
            "",
            "## Decision",
            "",
            report["conclusion"]["reason"],
            "",
            "This result does not change rollout policy. Coverage stays warning-only, "
            "subsection workers stay disabled, and historical outputs remain "
            "comparison-only because they are not a matched live baseline.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--source-review", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-markdown", required=True, type=Path)
    args = parser.parse_args()

    report = evaluate(args.manifest, args.source_review)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.output_markdown.write_text(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
