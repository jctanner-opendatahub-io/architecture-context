"""Pipeline boundary tests for the deterministic index phase."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.phases import diagrams, index, platform  # noqa: E402


def test_index_phase_runs_without_agent_dispatch(tmp_path: Path, monkeypatch) -> None:
    architecture = tmp_path / "architecture"
    version = architecture / "rhoai-test"
    version.mkdir(parents=True)
    (version / "component-map.json").write_text(
        json.dumps({"components": {"example": {"type": "service"}}})
    )
    (version / "example.md").write_text(
        "# Example\n\n## Purpose\n\nExample service.\n"
    )

    def forbidden(*_args, **_kwargs):
        raise AssertionError("agent dispatch is forbidden for generate-index")

    monkeypatch.setattr(diagrams, "run_agents_concurrently", forbidden)
    monkeypatch.setattr(platform, "run_agents_concurrently", forbidden)
    args = SimpleNamespace(
        architecture_dir=str(architecture),
        platform="rhoai-test",
        platforms_file=str(tmp_path / "missing-platforms.yaml"),
        overlays_dir=str(tmp_path / "missing-overlays"),
    )

    asyncio.run(index.run_generate_index_phase(args))

    assert (version / "INDEX.md").is_file()


def test_diagram_discovery_excludes_version_index(tmp_path: Path, monkeypatch) -> None:
    architecture = tmp_path / "architecture"
    version = architecture / "rhoai-test"
    version.mkdir(parents=True)
    (version / "INDEX.md").write_text("# Index\n")

    async def forbidden(*_args, **_kwargs):
        raise AssertionError("INDEX.md must not create a diagram job")

    monkeypatch.setattr(diagrams, "run_agents_concurrently", forbidden)
    args = SimpleNamespace(
        architecture_dir=str(architecture),
        platform="rhoai-test",
        version=None,
        component=None,
        force_regenerate=False,
        limit=None,
        export_png=False,
        max_concurrent=1,
        model=None,
        harness="claude",
        strace=False,
    )

    asyncio.run(diagrams.run_generate_diagrams_phase(args))


def test_platform_aggregation_excludes_version_index(
    tmp_path: Path, monkeypatch
) -> None:
    architecture = tmp_path / "architecture"
    version = architecture / "rhoai-test"
    version.mkdir(parents=True)
    (version / "INDEX.md").write_text("# Index\n")

    async def forbidden(*_args, **_kwargs):
        raise AssertionError("INDEX.md must not create a platform aggregation job")

    monkeypatch.setattr(platform, "_ensure_arch_query", forbidden)
    monkeypatch.setattr(platform, "run_agents_concurrently", forbidden)
    args = SimpleNamespace(
        architecture_dir=str(architecture),
        platform="rhoai-test",
        version=None,
        force=False,
        limit=None,
        max_concurrent=1,
        model=None,
        harness="claude",
        strace=False,
    )

    asyncio.run(platform.run_generate_platform_architecture_phase(args))
