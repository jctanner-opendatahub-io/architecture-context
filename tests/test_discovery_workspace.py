import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.codex_agent import _codex_input  # noqa: E402
from lib.discovery_workspace import run_isolated_discovery  # noqa: E402


@pytest.mark.asyncio
@pytest.mark.parametrize("outcome", ["valid", "invalid", "missing", "failed"])
async def test_isolated_discovery_validates_before_promotion(tmp_path, outcome):
    architecture = tmp_path / "architecture"
    destination = architecture / "rhoai.test" / "component-map.json"
    destination.parent.mkdir(parents=True)
    destination.write_text("previous map")
    logs = tmp_path / "logs"
    logs.mkdir()
    captured = []

    async def worker(**job):
        workspace = Path(job["cwd"])
        captured.append(workspace)
        assert not (workspace / "PLAN.md").exists()
        inputs = _codex_input(job["prompt"], True, cwd=job["cwd"])
        assert Path(inputs[0].path).is_relative_to(workspace)
        assert str(architecture) not in job["prompt"]
        assert "do not read or reuse previous" in job["prompt"]
        candidate = workspace / "architecture/rhoai.test/component-map.json"
        candidate.parent.mkdir(parents=True)
        if outcome == "valid":
            candidate.write_text(json.dumps({
                "metadata": {
                    "platform": "rhoai.test", "discovery_method": "breadcrumb",
                    "discovered_at": "2026-09-05T00:00:00Z",
                    "total_repos_scanned": 0, "components_discovered": 0,
                    "components_excluded": 0,
                },
                "components": {}, "excluded": {}, "dependency_graph": {},
            }))
        elif outcome == "invalid":
            candidate.write_text("invalid json")
        return {"success": outcome != "failed", "name": "discover-test"}

    result = await run_isolated_discovery(
        worker, platform="rhoai.test", architecture_dir=str(architecture),
        name="discover-test", cwd=".", log_dir=logs, harness="codex",
        prompt=f"/discover-components --architecture-dir={architecture}",
    )
    assert result["success"] == (outcome == "valid")
    assert not captured[0].exists()
    if outcome == "valid":
        metadata = json.loads(destination.read_text())["metadata"]
        assert metadata["platform"] == "rhoai.test"
    else:
        assert destination.read_text() == "previous map"
