"""Deterministic tests for the offline architecture-surface canary."""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CANARY_ROOT = PROJECT_ROOT / "evaluations" / "architecture-surface-coverage"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


evaluate_module = _load_module(
    "architecture_surface_canary", CANARY_ROOT / "evaluate.py"
)


@pytest.fixture
def manifest() -> dict:
    return json.loads((CANARY_ROOT / "experiment.json").read_text())


@pytest.fixture
def replay() -> dict:
    return json.loads((CANARY_ROOT / "replay-results.json").read_text())


def test_durable_replay_selects_behavioral_extraction(manifest, replay):
    report = evaluate_module.evaluate(manifest, replay)

    assert report["recommendation"] == {
        "selected_condition": "behavioral-extraction",
        "decision": "provisional-offline-selection",
        "provisional": True,
        "subsection_workers": "remain-disabled",
        "global_enforcement": "remain-warning-only",
        "separate_rollout_decision_required": True,
        "reason": (
            "Deterministic fixtures make behavioral extraction the earliest passing "
            "condition; the two single on-disk outputs have complementary supported "
            "surface sets (claude 0.50; codex 0.50), "
            "so repeated controlled evidence is still required before rollout."
        ),
    }
    conditions = {item["condition_id"]: item for item in report["conditions"]}
    assert conditions["baseline"]["surface_recall"]["minimum"] == 0.5
    assert conditions["surface-planning-review"]["surface_recall"]["minimum"] == 0.75
    assert conditions["surface-planning-review"]["unresolved_surfaces"]["maximum"] == 1
    assert conditions["behavioral-extraction"]["surface_recall"]["minimum"] == 1.0
    assert conditions["surface-aware-budget"]["surface_recall"]["minimum"] == 1.0
    assert all(
        item["analyzer_preservation_rate"]["minimum"] == 1.0
        for item in conditions.values()
    )
    assert all(item["merge_totals"]["lost"] == 0 for item in conditions.values())


def test_manifest_fingerprints_match_current_analyzer_and_skill(manifest):
    settings = manifest["settings"]
    assert (
        evaluate_module.source_bundle_sha256(settings["analyzer_sources"])
        == settings["analyzer_source_sha256"]
    )
    assert (
        evaluate_module.file_sha256(
            PROJECT_ROOT / ".claude/skills/repo-to-architecture-summary/SKILL.md"
        )
        == settings["skill_sha256"]
    )
    assert (
        evaluate_module.file_sha256(
            PROJECT_ROOT / "src/arch-analyzer/schema/component-architecture.schema.json"
        )
        == settings["analyzer_schema_sha256"]
    )


def test_durable_report_is_reproducible(tmp_path):
    output_json = tmp_path / "report.json"
    output_markdown = tmp_path / "report.md"
    subprocess.run(
        [
            sys.executable,
            str(CANARY_ROOT / "evaluate.py"),
            "--manifest",
            str(CANARY_ROOT / "experiment.json"),
            "--results",
            str(CANARY_ROOT / "replay-results.json"),
            "--output-json",
            str(output_json),
            "--output-markdown",
            str(output_markdown),
        ],
        check=True,
    )
    assert output_json.read_text() == (CANARY_ROOT / "report.json").read_text()
    assert output_markdown.read_text() == (CANARY_ROOT / "report.md").read_text()


def test_manifest_rejects_more_than_one_changed_factor(manifest):
    mutated = copy.deepcopy(manifest)
    factors = mutated["conditions"][2]["factors"]
    factors["behavioral_extraction"] = True
    factors["budget_policy"] = "surface-aware"

    with pytest.raises(evaluate_module.CanaryError, match="change exactly"):
        evaluate_module.validate_manifest(mutated)


def test_manifest_rejects_workers_after_passing_non_worker_condition(manifest, replay):
    mutated_manifest = copy.deepcopy(manifest)
    worker = copy.deepcopy(mutated_manifest["conditions"][-1])
    worker["condition_id"] = "subsection-workers"
    worker["changed_factor"] = "subsection_workers"
    worker["factors"]["subsection_workers"] = True
    mutated_manifest["conditions"].append(worker)
    mutated_results = copy.deepcopy(replay)
    source_runs = [
        run for run in replay["runs"] if run["condition_id"] == "surface-aware-budget"
    ]
    for run in source_runs:
        duplicate = copy.deepcopy(run)
        duplicate["run_id"] = run["run_id"].replace(
            "surface-aware-budget", "subsection-workers"
        )
        duplicate["condition_id"] = "subsection-workers"
        mutated_results["runs"].append(duplicate)

    with pytest.raises(evaluate_module.CanaryError, match="workers were tested"):
        evaluate_module.evaluate(mutated_manifest, mutated_results)


def test_recommendation_reason_uses_derived_selected_condition(manifest, replay):
    mutated = copy.deepcopy(replay)
    behavioral_runs = {
        run["run_id"].rsplit("-", 1)[-1]: run
        for run in mutated["runs"]
        if run["condition_id"] == "behavioral-extraction"
    }
    for run in mutated["runs"]:
        if run["condition_id"] == "surface-planning-review":
            repeat = run["run_id"].rsplit("-", 1)[-1]
            run["surface_results"] = copy.deepcopy(
                behavioral_runs[repeat]["surface_results"]
            )

    report = evaluate_module.evaluate(manifest, mutated)

    assert report["recommendation"]["selected_condition"] == "surface-planning-review"
    assert (
        "surface planning review the earliest passing"
        in report["recommendation"]["reason"]
    )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("workers_enabled", True, "must remain false"),
        ("coverage_enforcement", "blocking", "must remain warning-only"),
    ],
)
def test_manifest_rejects_safety_setting_drift(manifest, replay, field, value, message):
    mutated = copy.deepcopy(manifest)
    mutated["settings"][field] = value

    with pytest.raises(evaluate_module.CanaryError, match=message):
        evaluate_module.evaluate(mutated, replay)


@pytest.mark.parametrize("field", ["mode", "harness", "model"])
def test_replay_provenance_must_match_controlled_settings(manifest, replay, field):
    mutated = copy.deepcopy(replay)
    mutated["runs"][0]["provenance"][field] = "drifted"

    with pytest.raises(evaluate_module.CanaryError, match=f"controlled {field} drift"):
        evaluate_module.evaluate(manifest, mutated)


def test_supported_claim_requires_pinned_source_reference(manifest, replay):
    mutated = copy.deepcopy(replay)
    metrics = next(
        result
        for result in mutated["runs"][4]["surface_results"]
        if result["surface_id"] == "authentication.metrics-enforcement"
    )
    metrics["evidence"]["metrics.secure-conditional-filter"] = ["cmd/main.go:1-10"]

    with pytest.raises(evaluate_module.CanaryError, match="outside pinned"):
        evaluate_module.evaluate(manifest, mutated)


def test_missing_repeat_is_rejected(manifest, replay):
    mutated = copy.deepcopy(replay)
    mutated["runs"] = [
        run
        for run in mutated["runs"]
        if run["run_id"] != "behavioral-extraction-fixture-2"
    ]

    with pytest.raises(evaluate_module.CanaryError, match="at least 2 repeats"):
        evaluate_module.evaluate(manifest, mutated)


def test_cumulative_context_window_is_rejected(manifest, replay):
    mutated = copy.deepcopy(replay)
    mutated["runs"][0]["performance"]["tokens"]["cumulative"] = {
        "input_tokens": 100,
        "model_context_window": 200000,
    }

    with pytest.raises(evaluate_module.CanaryError, match="not cumulative"):
        evaluate_module.evaluate(manifest, mutated)


def test_observed_outputs_have_complementary_half_recall(manifest, replay):
    report = evaluate_module.evaluate(manifest, replay)
    comparisons = {item["harness"]: item for item in report["observed_comparisons"]}

    assert comparisons["claude"]["surface_recall"] == 0.5
    assert comparisons["codex"]["surface_recall"] == 0.5
    assert comparisons["claude"]["unsupported_claim_count"] == 3
    assert comparisons["codex"]["unsupported_claim_count"] == 0
    assert all(
        item["artifact"].startswith("architecture/") for item in comparisons.values()
    )
    assert all(item["repeat_count"] == 1 for item in comparisons.values())
    assert all(
        all(value is None for value in item["measurements"].values())
        for item in comparisons.values()
    )


def test_observed_review_basis_must_match_surface_source_inventory(manifest, replay):
    mutated = copy.deepcopy(replay)
    mutated["observed_comparisons"][0]["surface_results"][0]["review_basis"] = [
        "cmd/main.go:1-10"
    ]

    with pytest.raises(evaluate_module.CanaryError, match="pinned source"):
        evaluate_module.evaluate(manifest, mutated)


def test_observed_harness_and_model_must_match_manifest(manifest, replay):
    mutated = copy.deepcopy(replay)
    mutated["observed_comparisons"][0]["model"] = "uncontrolled-model"

    with pytest.raises(evaluate_module.CanaryError, match="does not match manifest"):
        evaluate_module.evaluate(manifest, mutated)


def test_observed_recall_is_derived_from_surface_statuses(manifest, replay):
    mutated = copy.deepcopy(replay)
    mutated["observed_comparisons"][0]["surface_recall"] = 1.0

    report = evaluate_module.evaluate(manifest, mutated)

    assert report["observed_comparisons"][0]["surface_recall"] == 0.5


def test_observed_runtime_measurements_must_all_be_explicitly_unavailable(
    manifest, replay
):
    mutated = copy.deepcopy(replay)
    del mutated["observed_comparisons"][0]["measurements"]["latency_seconds"]

    with pytest.raises(evaluate_module.CanaryError, match="every unavailable"):
        evaluate_module.evaluate(manifest, mutated)


def test_unsupported_surface_requires_attributable_claim(manifest, replay):
    mutated = copy.deepcopy(replay)
    mutated["observed_comparisons"][0]["unsupported_claims"] = []

    with pytest.raises(evaluate_module.CanaryError, match="every unsupported surface"):
        evaluate_module.evaluate(manifest, mutated)


def test_unsupported_claim_must_name_an_unsupported_surface(manifest, replay):
    mutated = copy.deepcopy(replay)
    mutated["observed_comparisons"][0]["unsupported_claims"][0]["surface_id"] = (
        "authentication.gateway-modes"
    )

    with pytest.raises(evaluate_module.CanaryError, match="unsupported surface"):
        evaluate_module.evaluate(manifest, mutated)


def test_recommendation_reason_uses_derived_observed_recall(manifest, replay):
    mutated = copy.deepcopy(replay)
    gateway = next(
        result
        for result in mutated["observed_comparisons"][0]["surface_results"]
        if result["surface_id"] == "authentication.gateway-modes"
    )
    gateway["status"] = "supported"

    report = evaluate_module.evaluate(manifest, mutated)

    reason = report["recommendation"]["reason"]
    assert "claude 0.75" in reason
    assert "complementary supported surface sets" not in reason


def test_observed_artifact_must_stay_under_architecture(manifest, replay):
    mutated = copy.deepcopy(replay)
    mutated["observed_comparisons"][0]["artifact"] = "logs/run.json"

    with pytest.raises(evaluate_module.CanaryError, match="under architecture"):
        evaluate_module.evaluate(manifest, mutated)
