#!/usr/bin/env python3
"""Evaluate deterministic replays and pinned, comparison-only architecture files.

The evaluator never launches agents. Deterministic fixture records exercise the
scoring and rollout gates; separately recorded architecture-file observations
are fingerprinted and checked against the manifest's source-reference inventory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "architecture-surface-canary/v1"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FACTOR_KEYS = (
    "surface_planning_review",
    "behavioral_extraction",
    "budget_policy",
    "subsection_workers",
)
SURFACE_STATUSES = frozenset({"supported", "unresolved", "omitted"})
OBSERVED_MEASUREMENTS = frozenset(
    {
        "analyzer_preservation",
        "cache_usage",
        "cost_usd",
        "discovery_calls",
        "latency_seconds",
        "merge_rejection_loss",
        "source_read_files",
        "source_read_ranges",
        "token_usage",
    }
)


class CanaryError(ValueError):
    """Raised when a canary artifact cannot support a comparison."""


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_bundle_sha256(paths: list[str]) -> str:
    digest = hashlib.sha256()
    for raw_path in paths:
        path = PROJECT_ROOT / raw_path
        digest.update(raw_path.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def load_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise CanaryError(f"{path}: expected a JSON object")
    return payload


def _nonempty(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CanaryError(f"{label} must be a nonempty string")
    return value.strip()


def _number(value: object, label: str, *, nullable: bool = False) -> float | None:
    if value is None and nullable:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise CanaryError(f"{label} must be a nonnegative number")
    return float(value)


def _integer(value: object, label: str) -> int:
    number = _number(value, label)
    assert number is not None
    if not number.is_integer():
        raise CanaryError(f"{label} must be an integer")
    return int(number)


def _validate_source_ref(reference: object, label: str) -> str:
    value = _nonempty(reference, label)
    if value.startswith("/") or ".." in Path(value.split(":", 1)[0]).parts:
        raise CanaryError(f"{label} must be repository-relative")
    path, separator, lines = value.rpartition(":")
    if not separator or not path or not lines:
        raise CanaryError(f"{label} must include a numeric line or range")
    bounds = lines.split("-", 1)
    if not all(item.isdigit() and int(item) > 0 for item in bounds):
        raise CanaryError(f"{label} must include a numeric line or range")
    if len(bounds) == 2 and int(bounds[0]) > int(bounds[1]):
        raise CanaryError(f"{label} range is reversed")
    return value


def _validate_read_range(reference: object, label: str) -> str:
    value = _nonempty(reference, label)
    if value.endswith(":unknown"):
        path = value.removesuffix(":unknown")
        if path and not path.startswith("/") and ".." not in Path(path).parts:
            return value
    if value.endswith("-unknown"):
        path_and_start = value.removesuffix("-unknown")
        path, separator, start = path_and_start.rpartition(":")
        if (
            separator
            and path
            and not path.startswith("/")
            and ".." not in Path(path).parts
            and start.isdigit()
            and int(start) > 0
        ):
            return value
    return _validate_source_ref(value, label)


def validate_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise CanaryError(f"schema_version must be {SCHEMA_VERSION}")
    source = manifest.get("source")
    if not isinstance(source, dict):
        raise CanaryError("source must be an object")
    _nonempty(source.get("repository"), "source.repository")
    revision = _nonempty(source.get("revision"), "source.revision")
    if len(revision) != 40 or any(char not in "0123456789abcdef" for char in revision):
        raise CanaryError("source.revision must be a full lowercase SHA")

    settings = manifest.get("settings")
    if not isinstance(settings, dict):
        raise CanaryError("settings must be an object")
    for field in (
        "analyzer_revision",
        "analyzer_source_sha256",
        "analyzer_schema_sha256",
        "skill_sha256",
        "controlled_harness",
        "controlled_model",
    ):
        _nonempty(settings.get(field), f"settings.{field}")
    if settings.get("workers_enabled") is not False:
        raise CanaryError("settings.workers_enabled must remain false")
    if settings.get("coverage_enforcement") != "warning-only":
        raise CanaryError("settings.coverage_enforcement must remain warning-only")
    analyzer_sources = settings.get("analyzer_sources")
    if (
        not isinstance(analyzer_sources, list)
        or not analyzer_sources
        or not all(isinstance(path, str) and path for path in analyzer_sources)
    ):
        raise CanaryError("settings.analyzer_sources must be a nonempty path array")
    if source_bundle_sha256(analyzer_sources) != settings["analyzer_source_sha256"]:
        raise CanaryError("settings.analyzer_source_sha256 does not match the checkout")
    if (
        file_sha256(
            PROJECT_ROOT / "src/arch-analyzer/schema/component-architecture.schema.json"
        )
        != settings["analyzer_schema_sha256"]
    ):
        raise CanaryError("settings.analyzer_schema_sha256 does not match the checkout")
    if (
        file_sha256(
            PROJECT_ROOT / ".claude/skills/repo-to-architecture-summary/SKILL.md"
        )
        != settings["skill_sha256"]
    ):
        raise CanaryError("settings.skill_sha256 does not match the checkout")

    surfaces = manifest.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        raise CanaryError("surfaces must be a nonempty array")
    surface_ids: set[str] = set()
    claim_ids: set[str] = set()
    for index, surface in enumerate(surfaces):
        if not isinstance(surface, dict):
            raise CanaryError(f"surfaces[{index}] must be an object")
        surface_id = _nonempty(
            surface.get("surface_id"), f"surfaces[{index}].surface_id"
        )
        if surface_id in surface_ids:
            raise CanaryError(f"duplicate surface_id: {surface_id}")
        surface_ids.add(surface_id)
        claims = surface.get("required_claims")
        if not isinstance(claims, list) or not claims:
            raise CanaryError(f"{surface_id}: required_claims must be nonempty")
        for claim_index, claim in enumerate(claims):
            if not isinstance(claim, dict):
                raise CanaryError(
                    f"{surface_id}: claim {claim_index} must be an object"
                )
            claim_id = _nonempty(claim.get("claim_id"), f"{surface_id}.claim_id")
            if claim_id in claim_ids:
                raise CanaryError(f"duplicate claim_id: {claim_id}")
            claim_ids.add(claim_id)
            references = claim.get("source_references")
            if not isinstance(references, list) or not references:
                raise CanaryError(f"{claim_id}: source_references must be nonempty")
            for ref_index, reference in enumerate(references):
                _validate_source_ref(
                    reference, f"{claim_id}.source_references[{ref_index}]"
                )

    minimum_repeats = _integer(manifest.get("minimum_repeats"), "minimum_repeats")
    if minimum_repeats < 2:
        raise CanaryError("minimum_repeats must be at least 2")

    observed_artifacts = manifest.get("observed_artifacts")
    if not isinstance(observed_artifacts, list) or not observed_artifacts:
        raise CanaryError("observed_artifacts must be a nonempty array")
    observed_harnesses: set[str] = set()
    observed_paths: set[str] = set()
    for index, observed in enumerate(observed_artifacts):
        if not isinstance(observed, dict):
            raise CanaryError(f"observed_artifacts[{index}] must be an object")
        harness = _nonempty(
            observed.get("harness"), f"observed_artifacts[{index}].harness"
        )
        _nonempty(observed.get("model"), f"observed_artifacts[{index}].model")
        artifact = _nonempty(
            observed.get("artifact"), f"observed_artifacts[{index}].artifact"
        )
        artifact_path = Path(artifact)
        if (
            artifact_path.is_absolute()
            or ".." in artifact_path.parts
            or not artifact_path.parts
            or artifact_path.parts[0] != "architecture"
        ):
            raise CanaryError(
                f"observed_artifacts[{index}] artifact must be under architecture/"
            )
        artifact_sha256 = _nonempty(
            observed.get("artifact_sha256"),
            f"observed_artifacts[{index}].artifact_sha256",
        )
        if len(artifact_sha256) != 64 or any(
            character not in "0123456789abcdef" for character in artifact_sha256
        ):
            raise CanaryError("observed artifact_sha256 must be lowercase SHA-256")
        if harness in observed_harnesses or artifact in observed_paths:
            raise CanaryError("observed artifact harnesses and paths must be unique")
        observed_harnesses.add(harness)
        observed_paths.add(artifact)

    conditions = manifest.get("conditions")
    if not isinstance(conditions, list) or len(conditions) < 2:
        raise CanaryError("conditions must contain at least two entries")
    condition_ids: set[str] = set()
    previous: dict[str, Any] | None = None
    for index, condition in enumerate(conditions):
        if not isinstance(condition, dict):
            raise CanaryError(f"conditions[{index}] must be an object")
        condition_id = _nonempty(
            condition.get("condition_id"), f"conditions[{index}].condition_id"
        )
        if condition_id in condition_ids:
            raise CanaryError(f"duplicate condition_id: {condition_id}")
        condition_ids.add(condition_id)
        factors = condition.get("factors")
        if not isinstance(factors, dict) or set(factors) != set(FACTOR_KEYS):
            raise CanaryError(
                f"{condition_id}: factors must contain exactly {', '.join(FACTOR_KEYS)}"
            )
        if factors["budget_policy"] not in {"existing", "surface-aware"}:
            raise CanaryError(f"{condition_id}: unsupported budget_policy")
        for key in (
            "surface_planning_review",
            "behavioral_extraction",
            "subsection_workers",
        ):
            if not isinstance(factors[key], bool):
                raise CanaryError(f"{condition_id}: factors.{key} must be boolean")
        if previous is None:
            if condition.get("changed_factor") is not None:
                raise CanaryError(
                    f"{condition_id}: the first condition cannot declare changed_factor"
                )
        else:
            differences = [
                key for key in FACTOR_KEYS if factors[key] != previous["factors"][key]
            ]
            if differences != [condition.get("changed_factor")]:
                raise CanaryError(
                    f"{condition_id}: adjacent condition must change exactly its "
                    "declared factor; "
                    f"found {differences}"
                )
        previous = condition

    gates = manifest.get("gates")
    if not isinstance(gates, dict):
        raise CanaryError("gates must be an object")
    recall = _number(
        gates.get("minimum_surface_recall"), "gates.minimum_surface_recall"
    )
    if recall is None or recall > 1:
        raise CanaryError("gates.minimum_surface_recall must be between 0 and 1")
    _integer(
        gates.get("maximum_unsupported_claims"), "gates.maximum_unsupported_claims"
    )


def _claim_inventory(
    manifest: dict[str, Any],
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    claims_by_surface: dict[str, set[str]] = {}
    refs_by_claim: dict[str, set[str]] = {}
    for surface in manifest["surfaces"]:
        surface_claims: set[str] = set()
        for claim in surface["required_claims"]:
            claim_id = claim["claim_id"]
            surface_claims.add(claim_id)
            refs_by_claim[claim_id] = set(claim["source_references"])
        claims_by_surface[surface["surface_id"]] = surface_claims
    return claims_by_surface, refs_by_claim


def _validate_tokens(tokens: object, run_id: str) -> None:
    if not isinstance(tokens, dict):
        raise CanaryError(f"{run_id}: performance.tokens must be an object")
    if set(tokens) - {"request", "cumulative"}:
        raise CanaryError(
            f"{run_id}: token usage must be split into request and cumulative"
        )
    for group in ("request", "cumulative"):
        values = tokens.get(group)
        if values is None:
            continue
        if not isinstance(values, dict):
            raise CanaryError(f"{run_id}: tokens.{group} must be an object or null")
        allowed = {
            "input_tokens",
            "output_tokens",
            "reasoning_output_tokens",
            "cached_input_tokens",
            "cache_write_input_tokens",
            "total_tokens",
            "model_context_window",
        }
        if set(values) - allowed:
            raise CanaryError(f"{run_id}: tokens.{group} contains unknown fields")
        for key, value in values.items():
            _integer(value, f"{run_id}.tokens.{group}.{key}")
        if group == "cumulative" and "model_context_window" in values:
            raise CanaryError(
                f"{run_id}: model_context_window is request metadata, "
                "not cumulative usage"
            )


def validate_runs(
    manifest: dict[str, Any],
    runs: list[dict[str, Any]],
    *,
    enforce_repeats: bool = True,
) -> None:
    claims_by_surface, refs_by_claim = _claim_inventory(manifest)
    condition_map = {
        condition["condition_id"]: condition for condition in manifest["conditions"]
    }
    run_ids: set[str] = set()
    repeats: Counter[str] = Counter()
    expected_settings = manifest["settings"]
    expected_revision = manifest["source"]["revision"]

    for index, run in enumerate(runs):
        if not isinstance(run, dict):
            raise CanaryError(f"runs[{index}] must be an object")
        run_id = _nonempty(run.get("run_id"), f"runs[{index}].run_id")
        if run_id in run_ids:
            raise CanaryError(f"duplicate run_id: {run_id}")
        run_ids.add(run_id)
        condition_id = _nonempty(run.get("condition_id"), f"{run_id}.condition_id")
        if condition_id not in condition_map:
            raise CanaryError(f"{run_id}: unknown condition_id {condition_id}")
        repeats[condition_id] += 1

        provenance = run.get("provenance")
        if not isinstance(provenance, dict):
            raise CanaryError(f"{run_id}: provenance must be an object")
        if provenance.get("source_revision") != expected_revision:
            raise CanaryError(f"{run_id}: source revision drift")
        for field in (
            "analyzer_revision",
            "analyzer_source_sha256",
            "analyzer_schema_sha256",
            "skill_sha256",
        ):
            if provenance.get(field) != expected_settings[field]:
                raise CanaryError(f"{run_id}: {field} drift")
        for field in ("mode", "harness"):
            if provenance.get(field) != expected_settings["controlled_harness"]:
                raise CanaryError(f"{run_id}: controlled {field} drift")
        if provenance.get("model") != expected_settings["controlled_model"]:
            raise CanaryError(f"{run_id}: controlled model drift")
        _nonempty(provenance.get("review"), f"{run_id}.provenance.review")

        results = run.get("surface_results")
        if not isinstance(results, list) or len(results) != len(claims_by_surface):
            raise CanaryError(
                f"{run_id}: exactly one result is required for every surface"
            )
        seen_surfaces: set[str] = set()
        for result_index, result in enumerate(results):
            if not isinstance(result, dict):
                raise CanaryError(
                    f"{run_id}: surface result {result_index} must be an object"
                )
            surface_id = result.get("surface_id")
            if surface_id not in claims_by_surface or surface_id in seen_surfaces:
                raise CanaryError(
                    f"{run_id}: unknown or duplicate surface_id {surface_id}"
                )
            seen_surfaces.add(surface_id)
            status = result.get("status")
            if status not in SURFACE_STATUSES:
                raise CanaryError(f"{run_id}/{surface_id}: invalid status")
            supported_claims = result.get("supported_claims")
            if not isinstance(supported_claims, list):
                raise CanaryError(
                    f"{run_id}/{surface_id}: supported_claims must be an array"
                )
            if set(supported_claims) - claims_by_surface[surface_id]:
                raise CanaryError(f"{run_id}/{surface_id}: unknown supported claim")
            evidence = result.get("evidence")
            if not isinstance(evidence, dict):
                raise CanaryError(f"{run_id}/{surface_id}: evidence must be an object")
            for claim_id in supported_claims:
                references = evidence.get(claim_id)
                if not isinstance(references, list) or not references:
                    raise CanaryError(
                        f"{run_id}/{claim_id}: supported claim lacks evidence"
                    )
                if not set(references).issubset(refs_by_claim[claim_id]):
                    raise CanaryError(
                        f"{run_id}/{claim_id}: evidence is outside pinned "
                        "source references"
                    )
            fully_supported = set(supported_claims) == claims_by_surface[surface_id]
            if (status == "supported") != fully_supported:
                raise CanaryError(
                    f"{run_id}/{surface_id}: supported status must include "
                    "every required claim"
                )
            if status != "supported" and not _nonempty(
                result.get("remaining_question"),
                f"{run_id}/{surface_id}.remaining_question",
            ):
                raise AssertionError("unreachable")

        unsupported = run.get("unsupported_claims")
        if not isinstance(unsupported, list):
            raise CanaryError(f"{run_id}: unsupported_claims must be an array")
        for claim_index, claim in enumerate(unsupported):
            if not isinstance(claim, dict):
                raise CanaryError(
                    f"{run_id}: unsupported claim {claim_index} must be an object"
                )
            _nonempty(
                claim.get("claim"), f"{run_id}.unsupported_claims[{claim_index}].claim"
            )
            _nonempty(
                claim.get("source_reason"),
                f"{run_id}.unsupported_claims[{claim_index}].source_reason",
            )

        preservation = run.get("preservation")
        if not isinstance(preservation, dict):
            raise CanaryError(f"{run_id}: preservation must be an object")
        seeded = _integer(
            preservation.get("analyzer_seeded"), f"{run_id}.analyzer_seeded"
        )
        preserved = _integer(
            preservation.get("analyzer_preserved"), f"{run_id}.analyzer_preserved"
        )
        if preserved > seeded:
            raise CanaryError(f"{run_id}: analyzer_preserved exceeds analyzer_seeded")
        merge = preservation.get("merge")
        if not isinstance(merge, dict):
            raise CanaryError(f"{run_id}: preservation.merge must be an object")
        for field in ("applied", "rejected", "restored", "lost"):
            _integer(merge.get(field), f"{run_id}.merge.{field}")

        reads = run.get("reads")
        if not isinstance(reads, dict):
            raise CanaryError(f"{run_id}: reads must be an object")
        files = reads.get("unique_files")
        ranges = reads.get("ranges")
        if not isinstance(files, list) or len(files) != len(set(files)):
            raise CanaryError(f"{run_id}: unique_files must be a unique array")
        if not isinstance(ranges, list) or len(ranges) != len(set(ranges)):
            raise CanaryError(f"{run_id}: ranges must be a unique array")
        for range_index, reference in enumerate(ranges):
            _validate_read_range(reference, f"{run_id}.reads.ranges[{range_index}]")
        _integer(reads.get("discovery_calls"), f"{run_id}.reads.discovery_calls")

        performance = run.get("performance")
        if not isinstance(performance, dict):
            raise CanaryError(f"{run_id}: performance must be an object")
        _number(
            performance.get("latency_seconds"),
            f"{run_id}.latency_seconds",
            nullable=True,
        )
        _number(performance.get("cost_usd"), f"{run_id}.cost_usd", nullable=True)
        _validate_tokens(performance.get("tokens"), run_id)

    if enforce_repeats:
        required = manifest["minimum_repeats"]
        missing = [
            condition_id
            for condition_id in condition_map
            if repeats[condition_id] < required
        ]
        if missing:
            raise CanaryError(
                f"conditions require at least {required} repeats: {', '.join(missing)}"
            )


def _average(values: list[float]) -> float | None:
    return round(statistics.fmean(values), 4) if values else None


def _numeric_average(runs: list[dict[str, Any]], path: tuple[str, ...]) -> float | None:
    values: list[float] = []
    for run in runs:
        value: object = run
        for key in path:
            if not isinstance(value, dict):
                value = None
                break
            value = value.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            values.append(float(value))
    return _average(values)


def _condition_summary(
    condition: dict[str, Any], runs: list[dict[str, Any]], surface_count: int
) -> dict[str, Any]:
    recalls: list[float] = []
    unsupported_counts: list[int] = []
    unresolved_counts: list[int] = []
    omitted_counts: list[int] = []
    preservation_rates: list[float] = []
    read_files: set[str] = set()
    read_ranges: set[str] = set()
    merge_totals: Counter[str] = Counter()
    discovery_calls: list[float] = []

    for run in runs:
        counts = Counter(result["status"] for result in run["surface_results"])
        recalls.append(counts["supported"] / surface_count)
        unsupported_counts.append(len(run["unsupported_claims"]))
        unresolved_counts.append(counts["unresolved"])
        omitted_counts.append(counts["omitted"])
        seeded = run["preservation"]["analyzer_seeded"]
        preserved = run["preservation"]["analyzer_preserved"]
        preservation_rates.append(1.0 if seeded == 0 else preserved / seeded)
        merge_totals.update(run["preservation"]["merge"])
        read_files.update(run["reads"]["unique_files"])
        read_ranges.update(run["reads"]["ranges"])
        discovery_calls.append(float(run["reads"]["discovery_calls"]))

    token_paths = {
        "request_input_tokens": ("performance", "tokens", "request", "input_tokens"),
        "request_output_tokens": ("performance", "tokens", "request", "output_tokens"),
        "request_cached_input_tokens": (
            "performance",
            "tokens",
            "request",
            "cached_input_tokens",
        ),
        "request_context_window": (
            "performance",
            "tokens",
            "request",
            "model_context_window",
        ),
        "cumulative_input_tokens": (
            "performance",
            "tokens",
            "cumulative",
            "input_tokens",
        ),
        "cumulative_output_tokens": (
            "performance",
            "tokens",
            "cumulative",
            "output_tokens",
        ),
        "cumulative_cached_input_tokens": (
            "performance",
            "tokens",
            "cumulative",
            "cached_input_tokens",
        ),
    }
    return {
        "condition_id": condition["condition_id"],
        "changed_factor": condition.get("changed_factor"),
        "factors": condition["factors"],
        "repeat_count": len(runs),
        "surface_recall": {
            "mean": _average(recalls),
            "minimum": round(min(recalls), 4),
            "maximum": round(max(recalls), 4),
        },
        "unsupported_claims": {
            "mean": _average([float(value) for value in unsupported_counts]),
            "maximum": max(unsupported_counts),
        },
        "unresolved_surfaces": {
            "mean": _average([float(value) for value in unresolved_counts]),
            "maximum": max(unresolved_counts),
        },
        "omitted_surfaces": {
            "mean": _average([float(value) for value in omitted_counts]),
            "maximum": max(omitted_counts),
        },
        "analyzer_preservation_rate": {
            "mean": _average(preservation_rates),
            "minimum": round(min(preservation_rates), 4),
        },
        "merge_totals": dict(sorted(merge_totals.items())),
        "source_reads": {
            "unique_files": sorted(read_files),
            "unique_file_count": len(read_files),
            "unique_ranges": sorted(read_ranges),
            "unique_range_count": len(read_ranges),
            "mean_discovery_calls": _average(discovery_calls),
        },
        "performance": {
            "mean_latency_seconds": _numeric_average(
                runs, ("performance", "latency_seconds")
            ),
            "mean_cost_usd": _numeric_average(runs, ("performance", "cost_usd")),
            "token_usage": {
                key: _numeric_average(runs, path) for key, path in token_paths.items()
            },
        },
    }


def _passes_gate(summary: dict[str, Any], gates: dict[str, Any]) -> bool:
    return bool(
        summary["surface_recall"]["minimum"] >= gates["minimum_surface_recall"]
        and summary["unsupported_claims"]["maximum"]
        <= gates["maximum_unsupported_claims"]
        and summary["analyzer_preservation_rate"]["minimum"] == 1.0
        and summary["merge_totals"].get("lost", 0) == 0
    )


def _observed_summary_clause(
    observed: list[dict[str, Any]], surface_ids: set[str]
) -> str:
    recalls = "; ".join(
        f"{item['harness']} {item['surface_recall']:.2f}" for item in observed
    )
    supported_sets = [
        {
            result["surface_id"]
            for result in item["surface_results"]
            if result["status"] == "supported"
        }
        for item in observed
    ]
    complementary = (
        len(supported_sets) == 2
        and supported_sets[0].isdisjoint(supported_sets[1])
        and supported_sets[0] | supported_sets[1] == surface_ids
    )
    if complementary:
        return (
            "the two single on-disk outputs have complementary supported surface "
            f"sets ({recalls})"
        )
    return f"the single on-disk output recalls are {recalls}"


def evaluate(manifest: dict[str, Any], results: dict[str, Any]) -> dict[str, Any]:
    validate_manifest(manifest)
    if results.get("schema_version") != SCHEMA_VERSION:
        raise CanaryError(f"results.schema_version must be {SCHEMA_VERSION}")
    runs = results.get("runs")
    if not isinstance(runs, list):
        raise CanaryError("results.runs must be an array")
    validate_runs(manifest, runs)

    execution_notes = results.get("execution_notes", [])
    if not isinstance(execution_notes, list) or not all(
        isinstance(note, str) and note.strip() for note in execution_notes
    ):
        raise CanaryError("results.execution_notes must be an array of strings")
    measurement_limits = results.get("measurement_limits", [])
    if not isinstance(measurement_limits, list) or not all(
        isinstance(limit, str) and limit.strip() for limit in measurement_limits
    ):
        raise CanaryError("results.measurement_limits must be an array of strings")
    observed_comparisons = results.get("observed_comparisons", [])
    if not isinstance(observed_comparisons, list):
        raise CanaryError("results.observed_comparisons must be an array")
    claims_by_surface, refs_by_claim = _claim_inventory(manifest)
    surface_ids = set(claims_by_surface)
    allowed_refs_by_surface = {
        surface_id: set().union(*(refs_by_claim[claim_id] for claim_id in claim_ids))
        for surface_id, claim_ids in claims_by_surface.items()
    }
    expected_observed = {
        observed["harness"]: observed for observed in manifest["observed_artifacts"]
    }
    if len(observed_comparisons) != len(expected_observed):
        raise CanaryError("observed comparisons must match the manifest inventory")
    observed_summaries: list[dict[str, Any]] = []
    observed_harnesses: set[str] = set()
    for index, comparison in enumerate(observed_comparisons):
        if not isinstance(comparison, dict):
            raise CanaryError(f"observed_comparisons[{index}] must be an object")
        for field in ("harness", "model", "artifact", "limitation"):
            _nonempty(comparison.get(field), f"observed_comparisons[{index}].{field}")
        harness = comparison["harness"]
        expected = expected_observed.get(harness)
        if expected is None or harness in observed_harnesses:
            raise CanaryError("observed comparison harness is unknown or duplicated")
        observed_harnesses.add(harness)
        if comparison.get("source_revision") != manifest["source"]["revision"]:
            raise CanaryError(f"observed_comparisons[{index}] source drift")
        if comparison.get("comparison_only") is not True:
            raise CanaryError(
                f"observed_comparisons[{index}] must be marked comparison_only"
            )
        if comparison.get("repeat_count") != 1:
            raise CanaryError("an observed architecture file must have repeat_count 1")
        artifact = Path(comparison["artifact"])
        if (
            artifact.is_absolute()
            or ".." in artifact.parts
            or not artifact.parts
            or artifact.parts[0] != "architecture"
        ):
            raise CanaryError(
                f"observed_comparisons[{index}] artifact must be under architecture/"
            )
        for field in ("model", "artifact", "artifact_sha256"):
            if comparison.get(field) != expected[field]:
                raise CanaryError(
                    f"observed_comparisons[{index}].{field} does not match manifest"
                )
        artifact_sha256 = _nonempty(
            comparison.get("artifact_sha256"),
            f"observed_comparisons[{index}].artifact_sha256",
        )
        if len(artifact_sha256) != 64 or any(
            character not in "0123456789abcdef" for character in artifact_sha256
        ):
            raise CanaryError("observed artifact_sha256 must be lowercase SHA-256")
        if file_sha256(PROJECT_ROOT / artifact) != artifact_sha256:
            raise CanaryError(
                f"observed_comparisons[{index}] artifact fingerprint drift"
            )
        surface_results = comparison.get("surface_results")
        if not isinstance(surface_results, list) or len(surface_results) != len(
            surface_ids
        ):
            raise CanaryError(
                f"observed_comparisons[{index}] must account for every surface"
            )
        observed_ids: set[str] = set()
        unsupported_surface_ids: set[str] = set()
        for surface_result in surface_results:
            if not isinstance(surface_result, dict):
                raise CanaryError("observed surface result must be an object")
            surface_id = surface_result.get("surface_id")
            if surface_id not in surface_ids or surface_id in observed_ids:
                raise CanaryError("observed surface ID is unknown or duplicated")
            observed_ids.add(surface_id)
            if surface_result.get("status") not in {
                "supported",
                "partial",
                "omitted",
                "unsupported",
            }:
                raise CanaryError("observed surface status is invalid")
            if surface_result["status"] == "unsupported":
                unsupported_surface_ids.add(surface_id)
            review_basis = surface_result.get("review_basis")
            if not isinstance(review_basis, list) or not review_basis:
                raise CanaryError("observed surface requires source review_basis")
            for reference in review_basis:
                validated_reference = _validate_source_ref(
                    reference, "observed surface review_basis"
                )
                if validated_reference not in allowed_refs_by_surface[surface_id]:
                    raise CanaryError(
                        "observed review_basis is outside the pinned source "
                        f"references for {surface_id}"
                    )
            _nonempty(surface_result.get("finding"), "observed surface finding")
        unsupported_claims = comparison.get("unsupported_claims")
        if not isinstance(unsupported_claims, list):
            raise CanaryError("observed unsupported_claims must be an array")
        for unsupported in unsupported_claims:
            if not isinstance(unsupported, dict):
                raise CanaryError("observed unsupported claim must be an object")
            _nonempty(unsupported.get("claim"), "observed unsupported claim")
            _nonempty(unsupported.get("source_reason"), "unsupported source_reason")
            if unsupported.get("surface_id") not in unsupported_surface_ids:
                raise CanaryError(
                    "observed unsupported claim must identify an unsupported surface"
                )
        claimed_unsupported_surfaces = {
            unsupported["surface_id"] for unsupported in unsupported_claims
        }
        if unsupported_surface_ids != claimed_unsupported_surfaces:
            raise CanaryError(
                "every unsupported surface must have an attributable unsupported claim"
            )
        measurements = comparison.get("measurements")
        if not isinstance(measurements, dict):
            raise CanaryError("observed comparison measurements must be an object")
        if set(measurements) != OBSERVED_MEASUREMENTS:
            raise CanaryError(
                "observed comparison must account for every unavailable measurement"
            )
        if any(value is not None for value in measurements.values()):
            raise CanaryError(
                "single on-disk output cannot establish runtime measurements"
            )
        surface_recall = round(
            sum(result["status"] == "supported" for result in surface_results)
            / len(surface_ids),
            4,
        )
        observed_summaries.append(
            {
                **comparison,
                "surface_recall": surface_recall,
                "unsupported_claim_count": len(unsupported_claims),
            }
        )

    summaries: list[dict[str, Any]] = []
    for condition in manifest["conditions"]:
        condition_runs = [
            run for run in runs if run["condition_id"] == condition["condition_id"]
        ]
        summaries.append(
            _condition_summary(condition, condition_runs, len(manifest["surfaces"]))
        )

    selected = next(
        (summary for summary in summaries if _passes_gate(summary, manifest["gates"])),
        None,
    )
    workers_tested = any(
        summary["factors"]["subsection_workers"] for summary in summaries
    )
    if workers_tested:
        first_worker = next(
            index
            for index, summary in enumerate(summaries)
            if summary["factors"]["subsection_workers"]
        )
        if any(
            _passes_gate(summary, manifest["gates"])
            for summary in summaries[:first_worker]
        ):
            raise CanaryError(
                "subsection workers were tested after a non-worker condition passed"
            )

    observed_clause = _observed_summary_clause(observed_summaries, surface_ids)
    selected_label = selected["condition_id"].replace("-", " ") if selected else None
    recommendation = {
        "selected_condition": selected["condition_id"] if selected else None,
        "decision": "provisional-offline-selection"
        if selected
        else "provisional-coverage-inadequate",
        "provisional": True,
        "subsection_workers": (
            "enabled" if manifest["settings"]["workers_enabled"] else "remain-disabled"
        ),
        "global_enforcement": f"remain-{manifest['settings']['coverage_enforcement']}",
        "separate_rollout_decision_required": True,
        "reason": (
            f"Deterministic fixtures make {selected_label} the earliest passing "
            f"condition; {observed_clause}, "
            "so repeated controlled evidence is still required before rollout."
            if selected
            else "No staged condition met the source-recall, support, preservation, "
            "and merge-loss gates."
        ),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "canary_id": manifest["canary_id"],
        "source": manifest["source"],
        "settings": manifest["settings"],
        "measurement_scope": results.get("measurement_scope"),
        "measurement_limits": measurement_limits,
        "execution_notes": execution_notes,
        "observed_comparisons": observed_summaries,
        "conditions": summaries,
        "recommendation": recommendation,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Architecture Surface Coverage Canary",
        "",
        "Pinned source: "
        f"`{report['source']['repository']}@{report['source']['revision']}`.",
        "",
        str(report.get("measurement_scope") or ""),
        "",
        "| Condition | Repeats | Recall (min/mean) | Unsupported max | "
        "Unresolved max | Preserved min | Merge lost | Files / ranges | "
        "Discovery mean | Latency mean |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for condition in report["conditions"]:
        latency = condition["performance"]["mean_latency_seconds"]
        lines.append(
            "| {condition_id} | {repeat_count} | {minimum:.2f} / {mean:.2f} | "
            "{unsupported} | {unresolved} | {preserved:.2f} | {lost} | "
            "{files} / {ranges} | {discovery} | {latency} |".format(
                condition_id=condition["condition_id"],
                repeat_count=condition["repeat_count"],
                minimum=condition["surface_recall"]["minimum"],
                mean=condition["surface_recall"]["mean"],
                unsupported=condition["unsupported_claims"]["maximum"],
                unresolved=condition["unresolved_surfaces"]["maximum"],
                preserved=condition["analyzer_preservation_rate"]["minimum"],
                lost=condition["merge_totals"].get("lost", 0),
                files=condition["source_reads"]["unique_file_count"],
                ranges=condition["source_reads"]["unique_range_count"],
                discovery=condition["source_reads"]["mean_discovery_calls"],
                latency="unavailable" if latency is None else f"{latency:.2f}s",
            )
        )
    lines.extend(["", "## Measurement limits", ""])
    lines.extend(f"- {limit}" for limit in report["measurement_limits"])
    if report["execution_notes"]:
        lines.extend(["", "Execution notes:", ""])
        lines.extend(f"- {note}" for note in report["execution_notes"])
    lines.extend(["", "## Observed on-disk comparison", ""])
    if report["observed_comparisons"]:
        lines.extend(
            [
                "| Harness / model | Recall | Unsupported | Artifact SHA-256 | "
                "Artifact | Limitation |",
                "|---|---:|---:|---|---|---|",
            ]
        )
        for item in report["observed_comparisons"]:
            lines.append(
                "| {harness} / {model} | {recall:.2f} | {unsupported} | "
                "`{sha}` | `{artifact}` | {limitation} |".format(
                    harness=item["harness"],
                    model=item["model"],
                    recall=item["surface_recall"],
                    unsupported=item["unsupported_claim_count"],
                    sha=item["artifact_sha256"],
                    artifact=item["artifact"],
                    limitation=item["limitation"],
                )
            )
        lines.extend(
            [
                "",
                "| Harness | Metrics enforcement | Named watches | Gateway modes | "
                "Runtime FIPS |",
                "|---|---|---|---|---|",
            ]
        )
        for item in report["observed_comparisons"]:
            statuses = {
                result["surface_id"]: result["status"]
                for result in item["surface_results"]
            }
            lines.append(
                "| {harness} | {metrics} | {watches} | {gateway} | {fips} |".format(
                    harness=item["harness"],
                    metrics=statuses["authentication.metrics-enforcement"],
                    watches=statuses["controller.named-resource-watches"],
                    gateway=statuses["authentication.gateway-modes"],
                    fips=statuses["compliance.runtime-fips"],
                )
            )
        unsupported = [
            (item["harness"], claim)
            for item in report["observed_comparisons"]
            for claim in item["unsupported_claims"]
        ]
        if unsupported:
            lines.extend(["", "Source-refuted claims:", ""])
            lines.extend(
                f"- {harness}: {claim['claim']} {claim['source_reason']}"
                for harness, claim in unsupported
            )
    else:
        lines.append("No on-disk comparison was recorded.")
    lines.extend(
        [
            "",
            "These architecture files were reviewed only for comparison and were "
            "never provided to synthesis runs.",
        ]
    )
    recommendation = report["recommendation"]
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"Provisional condition: `{recommendation['selected_condition']}`.",
            "",
            recommendation["reason"],
            "",
            "Subsection workers remain disabled and coverage validation remains "
            "warning-only. Worker adoption and global enforcement require a separate "
            "rollout decision.",
            "",
            "Runtime token, cost, latency, read, and variability measurements remain "
            "unavailable under the current no-live-agent constraint.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = evaluate(load_json(args.manifest), load_json(args.results))
    except (OSError, json.JSONDecodeError, CanaryError) as error:
        parser.error(str(error))
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.output_markdown.write_text(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
