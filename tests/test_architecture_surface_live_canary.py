"""Deterministic tests for the retained repeated live surface canary."""

from __future__ import annotations

import copy
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVALUATION_ROOT = PROJECT_ROOT / "evaluations/architecture-surface-coverage"
LIVE_ROOT = EVALUATION_ROOT / "live-canary"
SCRIPT_PATH = EVALUATION_ROOT / "evaluate_live.py"
SPEC = importlib.util.spec_from_file_location("surface_live_canary", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
live_canary = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(live_canary)


@pytest.fixture
def manifest() -> dict:
    return json.loads((LIVE_ROOT / "manifest.json").read_text())


@pytest.fixture
def source_review() -> dict:
    return json.loads((LIVE_ROOT / "source-review.json").read_text())


def test_live_report_records_repeated_source_review() -> None:
    report = live_canary.evaluate(
        LIVE_ROOT / "manifest.json", LIVE_ROOT / "source-review.json"
    )

    harnesses = {item["harness"]: item for item in report["harnesses"]}
    assert harnesses["claude"]["runs_meeting_source_review_gates"] == 0
    assert harnesses["claude"]["surface_recall"]["mean"] == 0.5
    assert harnesses["claude"]["unsupported_claims"] == 6
    assert harnesses["codex"]["runs_meeting_source_review_gates"] == 1
    assert harnesses["codex"]["surface_recall"]["mean"] == 1.0
    assert harnesses["codex"]["unsupported_claims"] == 1
    assert report["warning_quality"] == {
        "artifact_contract": 28,
        "emitted": 44,
        "false_positive": 12,
        "false_positive_rate": 0.272727,
        "semantic_signal": 4,
    }
    assert report["execution"]["all_inputs_preserved"] is True
    assert report["execution"]["surface_inventories_identical"] is True
    assert report["execution"]["analyzer_output_preserved"] is False
    assert report["execution"]["analyzer_row_loss_count"] == 8
    assert report["execution"]["candidate_surface_loss_count"] == 1
    assert report["execution"]["promotion_failure_runs"] == 4
    assert report["conclusion"]["canary_execution_accepted"] is False
    assert report["conclusion"]["codex_two_of_two_source_review_gate"] is False
    assert report["conclusion"]["coverage_enforcement"] == "warning-only"
    assert report["conclusion"]["subsection_workers_enabled"] is False


def test_live_report_is_byte_reproducible(tmp_path: Path) -> None:
    output_json = tmp_path / "report.json"
    output_markdown = tmp_path / "report.md"
    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--manifest",
            str(LIVE_ROOT / "manifest.json"),
            "--source-review",
            str(LIVE_ROOT / "source-review.json"),
            "--output-json",
            str(output_json),
            "--output-markdown",
            str(output_markdown),
        ],
        check=True,
    )

    assert output_json.read_bytes() == (LIVE_ROOT / "report.json").read_bytes()
    assert output_markdown.read_bytes() == (LIVE_ROOT / "report.md").read_bytes()


def test_manifest_rejects_model_substitution(manifest: dict) -> None:
    mutated = copy.deepcopy(manifest)
    mutated["settings"]["models"]["claude"] = "opus"

    with pytest.raises(live_canary.LiveCanaryError, match="exact canary models"):
        live_canary.validate_manifest(mutated, LIVE_ROOT / "manifest.json")


def test_manifest_rejects_retained_input_hash_drift(manifest: dict) -> None:
    mutated = copy.deepcopy(manifest)
    mutated["inputs"]["component_map"]["sha256"] = "0" * 64

    with pytest.raises(live_canary.LiveCanaryError, match="hash mismatch"):
        live_canary.validate_manifest(mutated, LIVE_ROOT / "manifest.json")


def test_retained_run_manifest_rejects_input_hash_drift(manifest: dict) -> None:
    expected = {
        "component_map_sha256": manifest["inputs"]["component_map"]["sha256"],
        "component_architecture_sha256": manifest["inputs"][
            "component_architecture"
        ]["sha256"],
        "analyzer_architecture_sha256": manifest["inputs"][
            "analyzer_architecture"
        ]["sha256"],
        "analyzer_synthesis_context_sha256": manifest["inputs"][
            "analyzer_synthesis_context"
        ]["sha256"],
        "analyzer_binary_sha256": manifest["inputs"]["analyzer_binary_sha256"],
    }
    retained = json.loads(
        (LIVE_ROOT / "runs/claude-repetition-1/input-manifest.json").read_text()
    )
    retained["inputs"]["component_map_sha256"] = "0" * 64

    with pytest.raises(
        live_canary.LiveCanaryError, match="retained input manifest hash mismatch"
    ):
        live_canary.validate_retained_input_manifest(
            retained,
            expected,
            run_id="claude-repetition-1",
            harness="claude",
            model="claude-opus-4-6",
            repetition=1,
        )


def test_review_rejects_incomplete_claim_accounting(
    manifest: dict, source_review: dict
) -> None:
    _, claim_to_surface = live_canary.validate_manifest(
        manifest, LIVE_ROOT / "manifest.json"
    )
    mutated = copy.deepcopy(source_review)
    mutated["runs"][0]["claim_results"].pop()

    with pytest.raises(live_canary.LiveCanaryError, match="claim coverage"):
        live_canary.validate_review(
            mutated,
            {run["run_id"] for run in manifest["runs"]},
            claim_to_surface,
        )


def test_candidate_to_promoted_fips_loss_is_retained() -> None:
    candidate = LIVE_ROOT / "runs/claude-repetition-2/candidate.md"
    promoted = LIVE_ROOT / "runs/claude-repetition-2/promoted.md"

    assert "### FIPS Compliance" in candidate.read_text()
    assert "### FIPS Compliance" not in promoted.read_text()


def test_analyzer_rbac_row_losses_are_reproduced_for_every_run() -> None:
    expected_rows = {
        "| opendatahub-operator-metrics-reader |  |  | get |",
        "| metrics-reader |  |  | get |",
    }
    report = live_canary.evaluate(
        LIVE_ROOT / "manifest.json", LIVE_ROOT / "source-review.json"
    )

    for run in report["runs"]:
        assert run["preservation"]["analyzer_output_preserved"] is False
        assert {
            item["row"] for item in run["preservation"]["analyzer_row_losses"]
        } == expected_rows


def test_dependency_qualified_review_references_match_retained_input() -> None:
    analyzer = (LIVE_ROOT / "inputs/analyzer-architecture.md").read_text()
    retained_version = live_canary.retained_dependency_version(
        analyzer, "sigs.k8s.io/controller-runtime"
    )
    review = json.loads((LIVE_ROOT / "source-review.json").read_text())
    references = [
        reference
        for run in review["runs"]
        for claim in run["unsupported_claims"]
        for reference in claim["review_basis"]
        if reference.startswith("sigs.k8s.io/controller-runtime@")
    ]

    assert references
    assert {
        re.match(r"^sigs\.k8s\.io/controller-runtime@([^/]+)/", reference).group(1)
        for reference in references
    } == {retained_version}
