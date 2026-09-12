"""Offline consumer boundaries for accepted structured publications."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "tests"))

from lib.phases import collect  # noqa: E402
from lib.structured_component_publication import (  # noqa: E402
    PublicationError,
    has_publication_state,
)
from scripts import collect_architectures as standalone  # noqa: E402
from scripts import lint_architecture_docs  # noqa: E402


def _component(checkout: Path):
    return SimpleNamespace(checkout_path=checkout, tier="core_platform")


def _tree_identity(root: Path) -> tuple[tuple[str, str], ...]:
    entries = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            entries.append((f"link:{relative}", os.readlink(path)))
        elif path.is_dir():
            entries.append((f"dir:{relative}", ""))
        else:
            entries.append(
                (f"file:{relative}", hashlib.sha256(path.read_bytes()).hexdigest())
            )
    return tuple(entries)


def _run_linter(architecture: Path, analyzer: Path | None = None):
    command = [
        sys.executable,
        str(PROJECT_ROOT / "scripts/lint_architecture_docs.py"),
        "--architecture-dir",
        str(architecture),
    ]
    if analyzer is not None:
        command.extend(("--arch-analyzer", str(analyzer)))
    return subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_component_map_collector_preserves_validated_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    architecture = tmp_path / "architecture"
    version = architecture / "rhoai-test"
    accepted_dir = version / "accepted"
    accepted_dir.mkdir(parents=True)
    (accepted_dir / "document.json").write_text("validator trigger")
    accepted_markdown = version / "accepted.md"
    accepted_markdown.write_text("accepted authority derivative\n")
    (version / "component-map.json").write_text(
        json.dumps({"components": {"accepted": {}, "legacy": {}}})
    )
    accepted_checkout = tmp_path / "accepted-checkout"
    legacy_checkout = tmp_path / "legacy-checkout"
    accepted_checkout.mkdir()
    legacy_checkout.mkdir()
    (accepted_checkout / "GENERATED_ARCHITECTURE.md").write_text(
        "must not replace accepted\n"
    )
    (legacy_checkout / "GENERATED_ARCHITECTURE.md").write_text("legacy\n")
    calls = []

    monkeypatch.setattr(collect, "get_component_map_metadata", lambda *_a, **_k: {})
    monkeypatch.setattr(
        collect,
        "read_component_map",
        lambda *_a, **_k: {
            "accepted": _component(accepted_checkout),
            "legacy": _component(legacy_checkout),
        },
    )
    monkeypatch.setattr(collect, "load_platform_config", lambda *_a: {})

    async def fake_ensure():
        return "/offline/arch-analyzer"

    def fake_accepted(platform_dir, _assembler, *, repair_markdown):
        calls.append((platform_dir, repair_markdown))
        return {"accepted": object()}

    monkeypatch.setattr(collect, "_ensure_arch_analyzer", fake_ensure)
    monkeypatch.setattr(collect, "accepted_publications", fake_accepted)
    args = SimpleNamespace(
        architecture_dir=str(architecture), platform="rhoai-test", version=None
    )

    asyncio.run(collect.run_collect_architectures_phase(args))

    assert calls == [(version, True)]
    assert accepted_markdown.read_text() == "accepted authority derivative\n"
    assert (version / "legacy.md").read_text() == "legacy\n"
    index = (version / "README.md").read_text()
    assert "accepted.md" in index and "legacy.md" in index


def test_metadata_directory_is_not_publication_state(tmp_path: Path) -> None:
    version = tmp_path / "rhoai-test"
    metadata = version / "run-metadata"
    metadata.mkdir(parents=True)
    (metadata / "document.json").write_text("not a component")

    assert not has_publication_state(version)


def test_standalone_collector_requires_validator_and_preserves_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    checkouts = tmp_path / "checkouts"
    output = tmp_path / "architecture"
    checkout = checkouts / "rhoai"
    legacy = checkout / "legacy"
    accepted = checkout / "accepted"
    legacy.mkdir(parents=True)
    accepted.mkdir()
    (legacy / "GENERATED_ARCHITECTURE.md").write_text("legacy\n")
    (accepted / "GENERATED_ARCHITECTURE.md").write_text("do not copy\n")
    platform = standalone.Platform("rhoai", "1", checkout, checkout)
    version = output / "rhoai-1"
    (version / "accepted").mkdir(parents=True)
    (version / "accepted" / "document.json").write_text("validator trigger")
    accepted_markdown = version / "accepted.md"
    accepted_markdown.write_text("accepted\n")
    monkeypatch.setattr(standalone, "discover_platforms", lambda _path: [platform])
    monkeypatch.setattr(
        standalone,
        "find_architecture_files",
        lambda _platform: [
            (accepted / "GENERATED_ARCHITECTURE.md", "accepted"),
            (legacy / "GENERATED_ARCHITECTURE.md", "legacy"),
        ],
    )

    with pytest.raises(PublicationError, match="no arch-analyzer validator"):
        standalone.collect_architectures(checkouts, output)

    sentinel_assembler = object()
    calls = []

    def fake_accepted(platform_dir, assembler, *, repair_markdown):
        calls.append((platform_dir, assembler, repair_markdown))
        return {"accepted": object()}

    monkeypatch.setattr(standalone, "accepted_publications", fake_accepted)
    result = standalone.collect_architectures(
        checkouts, output, assembler=sentinel_assembler
    )

    assert calls == [(version, sentinel_assembler, True)]
    assert accepted_markdown.read_text() == "accepted\n"
    assert (version / "legacy.md").read_text() == "legacy\n"
    assert result["platforms"][0]["components"] == ["accepted", "legacy"]


def test_architecture_linter_fails_before_flat_checks_on_invalid_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    version = tmp_path / "rhoai-test"
    (version / "accepted").mkdir(parents=True)
    (version / "accepted" / "document.json").write_text("invalid")
    monkeypatch.setattr(lint_architecture_docs, "ARCHITECTURE_DIR", tmp_path)

    async def fake_ensure():
        return "/offline/arch-analyzer"

    def reject(*_args, **_kwargs):
        raise PublicationError("mixed generation")

    from lib import fetch, structured_component_publication

    monkeypatch.setattr(fetch, "_ensure_arch_analyzer", fake_ensure)
    monkeypatch.setattr(
        structured_component_publication, "validate_accepted_publications", reject
    )

    assert lint_architecture_docs.main() == 1


def test_gitignore_preserves_legacy_sidecars_and_ignores_private_structured_state():
    ignored = (
        "architecture/rhoai-3.7/.generation/structured/preflight-diagnostic.json",
        "architecture/rhoai-3.7/.generation/structured-publication-locks/policy.lock",
        "architecture/rhoai-3.7/policy/.generation/structured/run-record.json",
    )
    trackable = (
        "architecture/rhoai-3.7/policy/.generation/SURFACE_COVERAGE.json",
        "architecture/rhoai-3.7/policy/.generation/SOURCE_READ_JUSTIFICATIONS.json",
        "architecture/rhoai-3.7/policy/.generation/INSIGHTS_ARTIFACT.json",
    )
    for path in ignored:
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "-v", path],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (path, result.stderr)
        assert path in result.stdout
    for path in trackable:
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "-v", path],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1, (path, result.stdout, result.stderr)


def test_actual_linter_leaves_legacy_architecture_tree_unchanged() -> None:
    architecture = PROJECT_ROOT / "architecture"
    before = _tree_identity(architecture)
    result = _run_linter(architecture)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "All 901 component architecture file(s) passed validation." in result.stdout
    assert _tree_identity(architecture) == before
