"""Offline verification for the retained live-canary repair replay."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LIVE_ROOT = PROJECT_ROOT / "evaluations/architecture-surface-coverage/live-canary"
RECORDED_ROOT = (
    PROJECT_ROOT
    / "evaluations/architecture-surface-coverage/promotion-repair-replay"
)
SCRIPT = (
    PROJECT_ROOT
    / "evaluations/architecture-surface-coverage/replay_promotion_repairs.py"
)


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_all_four_retained_runs_replay_offline_without_mutating_evidence(
    tmp_path: Path,
) -> None:
    before = _tree_hashes(LIVE_ROOT)
    output = tmp_path / "replay"

    subprocess.run(
        [sys.executable, str(SCRIPT), "--output", str(output)],
        cwd=PROJECT_ROOT,
        env={**os.environ, "GOCACHE": "/tmp/promotion-repair-replay-test-cache"},
        check=True,
        capture_output=True,
        text=True,
    )

    assert _tree_hashes(LIVE_ROOT) == before
    report = json.loads((output / "report.json").read_text())
    assert report["original_canary_status"] == "rejected"
    assert report["summary"] == {
        "all_analyzer_rows_preserved": True,
        "expected_rejections": 1,
        "run_count": 4,
        "successful_promotions": 3,
    }
    by_run = {run["run_id"]: run for run in report["runs"]}
    assert by_run["claude-repetition-2"]["promoted"] is None
    diagnostic = by_run["claude-repetition-2"]["assembly_diagnostics"][0]
    assert diagnostic["code"] == "synthesis_subsection_parent_mismatch"
    assert diagnostic["expected_parent"] == "Security"
    assert diagnostic["actual_parent"] == "Admission Webhooks"
    for run in report["runs"]:
        assert run["preservation"]["expected"] == 276
        assert run["preservation"]["preserved"] == 276
        assert run["preservation"]["mapped_missing"] == 0
        assert run["preservation"]["all_expected"] == 310
        assert run["preservation"]["all_preserved"] == 310
        assert run["preservation"]["all_missing"] == 0
        assert run["preservation"]["all_adjudicated_missing"] == 0


def test_recorded_replay_keeps_original_canary_rejected() -> None:
    report = json.loads((RECORDED_ROOT / "report.json").read_text())

    assert report["original_canary_status"] == "rejected"
    assert report["original_evidence"]["immutable"] is True
    assert (
        report["original_evidence"]["aggregate_sha256_before"]
        == report["original_evidence"]["aggregate_sha256_after"]
    )
