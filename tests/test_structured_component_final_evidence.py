"""Offline-only tests for the P5 evidence utility."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests/fixtures/structured_component_final"
SCRIPT = ROOT / "scripts/structured_component_final_evidence.py"
FRESH_SCRIPT = ROOT / "scripts/structured_component_fresh_reuse.py"


@pytest.fixture(scope="session")
def final_arch_analyzer_binary(tmp_path_factory: pytest.TempPathFactory) -> Path:
    binary = tmp_path_factory.mktemp("final-evidence-bin") / "arch-analyzer"
    subprocess.run(
        ["go", "build", "-o", str(binary), "."],
        cwd=ROOT / "src/arch-analyzer",
        env={**os.environ, "GOCACHE": "/tmp/structured-component-final-go-cache"},
        check=True,
        capture_output=True,
        text=True,
    )
    return binary


def _module():
    spec = importlib.util.spec_from_file_location("final_evidence", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fresh_module():
    spec = importlib.util.spec_from_file_location("fresh_reuse", FRESH_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_legacy_markdown_requires_fips_under_security() -> None:
    evidence = _module()
    evidence.validate_legacy_markdown((FIXTURES / "valid-security-fips.md").read_text())
    with pytest.raises(
        evidence.LegacyConversionError,
        match="malformed-legacy-fips-placement",
    ):
        evidence.validate_legacy_markdown(
            (FIXTURES / "malformed-fips-placement.md").read_text()
        )


@pytest.mark.parametrize(
    ("fixture", "code"),
    [
        ("unsupported-legacy-fields.json", "unsupported-legacy-fields"),
        ("ambiguous-legacy-fips.json", "ambiguous-legacy-fips-evidence"),
    ],
)
def test_legacy_analyzer_conversion_errors_are_explicit(
    fixture: str, code: str
) -> None:
    evidence = _module()
    value = json.loads((FIXTURES / fixture).read_text())
    with pytest.raises(evidence.LegacyConversionError, match=code):
        evidence.validate_legacy_analyzer(value)


def test_preservation_and_saved_reuse_summary_reproduce(
    tmp_path: Path, final_arch_analyzer_binary: Path
) -> None:
    evidence = _module()
    preservation = evidence.verify_historical_preservation()
    assert preservation["path_count"] == 76
    assert preservation["unchanged_original_paths"] == 75
    assert preservation["mismatches"] == []
    output = tmp_path / "reuse.json"
    report = evidence.reproduce_reuse_comparison(
        output, final_arch_analyzer_binary, "pytest fixture analyzer build"
    )
    assert report["saved_result"]["common_repositories"] == 92
    assert report["candidate_reuse"] == {
        "same_commit": 11,
        "semantic": 33,
        "semantic_after_scan_count_normalization": 38,
        "dropping_dependency_versions_not_recommended": 40,
    }
    assert report["verified_reuse"]["count"] == 0
    assert len(report["recorded_historical_analyzer_build"]["dirty_files"]) == 11
    assert report["fresh_current_analyzer_build"]["dirty_status"]
    assert output.is_file()


def test_saved_canary_replay_is_fresh_and_keeps_rejection(
    tmp_path: Path, final_arch_analyzer_binary: Path
) -> None:
    evidence = _module()
    output = tmp_path / "offline-canary"
    report = evidence.replay_saved_canary(output, final_arch_analyzer_binary)
    assert report["live_model_calls"] == 0
    assert report["summary"] == {
        "runs": 4,
        "analyzer_only_replays": 3,
        "explicit_conversion_errors": 1,
    }
    assert report["original_verdict"]["canary_execution_accepted"] is False
    errors = [
        item for item in report["results"] if item["status"] == "conversion-error"
    ]
    assert [item["run_id"] for item in errors] == ["claude-repetition-2"]
    assert errors[0]["error"]["code"] == "malformed-legacy-fips-placement"
    complete = [
        item
        for item in report["results"]
        if item["status"] == "analyzer-only-replay-complete"
    ]
    assert all(item["candidate_content_converted"] is False for item in complete)
    assert all(item["legacy_response_available"] is False for item in complete)
    assert all(item["model_calls"] == 0 for item in complete)
    assert all(item["document_schema_version"] == "1.0.0" for item in complete)
    with pytest.raises(ValueError, match="already exists"):
        evidence.replay_saved_canary(output, final_arch_analyzer_binary)


def test_standalone_cli_uses_no_model_transport(
    tmp_path: Path, final_arch_analyzer_binary: Path
) -> None:
    output = tmp_path / "preservation.json"
    completed = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "verify-preservation",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(output.read_text())["unchanged_original_paths"] == 75
    assert final_arch_analyzer_binary.is_file()


def test_standalone_transport_guard_rejects_both_sdks() -> None:
    evidence = _module()
    evidence.install_model_transport_guard()

    from claude_agent_sdk._internal.transport.subprocess_cli import (
        SubprocessCLITransport,
    )
    from openai_codex.client import CodexClient

    with pytest.raises(RuntimeError, match="Codex transport startup"):
        CodexClient.start(object())
    coroutine = SubprocessCLITransport.connect(object())
    with pytest.raises(RuntimeError, match="Claude transport startup"):
        asyncio.run(coroutine)


def test_fresh_comparison_matches_unchanged_legacy_rules_and_keeps_versions(
    tmp_path: Path,
) -> None:
    fresh = _fresh_module()
    left = {
        "commit_sha": "a",
        "extracted_at": "old",
        "schema_version": "1",
        "dependencies": {"packages": [{"name": "example", "version": "1"}]},
        "category_coverage": {
            "authentication": {
                "evidence": [
                    "summary:scanned 2 Python source files for "
                    "authentication constructions"
                ]
            }
        },
    }
    right = json.loads(json.dumps(left))
    right["commit_sha"] = "b"
    right["extracted_at"] = "new"
    right["category_coverage"]["authentication"]["evidence"][0] = (
        "summary:scanned 999 Python source files for authentication constructions"
    )
    comparison = fresh.compare_pair("org/example", left, right)
    assert comparison["legacy_compare_py"]["same_semantic_facts"] is False
    assert comparison["reviewed_scan_count_tier"]["same"] is True
    assert comparison["current_sc13_analyzer_payload_only"]["same"] is True

    corpus = tmp_path / "corpus"
    (corpus / "ea1").mkdir(parents=True)
    (corpus / "ea2").mkdir()
    (corpus / "ea1/example.json").write_text(json.dumps(left))
    (corpus / "ea2/example.json").write_text(json.dumps(right))
    completed = subprocess.run(
        [
            "python3",
            str(ROOT / "evaluations/component-reuse-fingerprint/compare.py"),
            str(corpus),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "same semantic facts:        0" in completed.stdout

    right["dependencies"]["packages"][0]["version"] = "2"
    comparison = fresh.compare_pair("org/example", left, right)
    assert comparison["reviewed_scan_count_tier"]["same"] is False
    assert comparison["drop_all_version_keys_sensitivity_only"]["same"] is True
    assert comparison["drop_all_version_keys_sensitivity_only"]["recommended"] is False
    assert comparison["current_sc13_analyzer_payload_only"]["same"] is False


def test_fresh_extraction_uses_recorded_empty_distribution_default(
    tmp_path: Path,
) -> None:
    fresh = _fresh_module()
    command = fresh._extract_command(
        Path("/evidence/arch-analyzer"),
        tmp_path / "checkouts/ea1/example",
        tmp_path / "ea1/example.json",
    )
    assert command == (
        "/evidence/arch-analyzer",
        "extract",
        str(tmp_path / "checkouts/ea1/example"),
        "--output",
        str(tmp_path / "ea1/example.json"),
    )
    assert "--distribution" not in command
    assert fresh._slug("llm-d/.github") != fresh._slug("llm-d/.project")
    github_prefix = tmp_path / fresh._slug("llm-d/.github")
    project_prefix = tmp_path / fresh._slug("llm-d/.project")
    assert Path(f"{github_prefix}.json") != Path(f"{project_prefix}.json")


def test_committed_tree_materialization_ignores_worktree_extras_and_keeps_git_identity(
    tmp_path: Path, final_arch_analyzer_binary: Path
) -> None:
    fresh = _fresh_module()
    source = tmp_path / "source"
    source.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=source, check=True)
    subprocess.run(
        ["git", "config", "user.email", "evidence@example.invalid"],
        cwd=source,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Evidence Test"], cwd=source, check=True
    )
    subprocess.run(
        ["git", "remote", "add", "origin", "https://example.invalid/org/repo.git"],
        cwd=source,
        check=True,
    )
    (source / ".gitignore").write_text("ignored.txt\n")
    (source / "deployment.yaml").write_text(
        "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: evidence\n"
    )
    subprocess.run(
        ["git", "add", ".gitignore", "deployment.yaml"], cwd=source, check=True
    )
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=source, check=True)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=source,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    tree = subprocess.run(
        ["git", "rev-parse", "HEAD^{tree}"],
        cwd=source,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    (source / "ignored.txt").write_text("must not become an analyzer input")
    (source / "untracked.txt").write_text("must not become an analyzer input")
    before = fresh._source_status(source)

    isolated = tmp_path / "isolated" / "checkouts" / "ea1" / "repo"
    materialized = fresh._materialize_tree(source, commit, isolated)
    assert materialized["verified_metadata"] == {
        "head": commit,
        "tree": tree,
        "origin_url": "https://example.invalid/org/repo.git",
    }
    assert not (isolated / "ignored.txt").exists()
    assert not (isolated / "untracked.txt").exists()
    output = tmp_path / "analyzer.json"
    subprocess.run(
        [
            str(final_arch_analyzer_binary),
            "extract",
            str(isolated),
            "--distribution",
            "rhoai.next",
            "--output",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    analyzer = json.loads(output.read_text())
    assert analyzer["commit_sha"] == commit
    assert analyzer["repo"] == "https://example.invalid/org/repo.git"
    assert fresh._source_status(source) == before


def test_committed_tree_materialization_handles_padded_gitlink_size(
    tmp_path: Path,
) -> None:
    fresh = _fresh_module()
    child = tmp_path / "child"
    child.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=child, check=True)
    subprocess.run(
        ["git", "config", "user.email", "evidence@example.invalid"],
        cwd=child,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Evidence Test"], cwd=child, check=True
    )
    (child / "README.md").write_text("submodule fixture\n")
    subprocess.run(["git", "add", "README.md"], cwd=child, check=True)
    subprocess.run(["git", "commit", "-qm", "child fixture"], cwd=child, check=True)
    child_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=child,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    source = tmp_path / "source-with-gitlink"
    source.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=source, check=True)
    subprocess.run(
        ["git", "config", "user.email", "evidence@example.invalid"],
        cwd=source,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Evidence Test"], cwd=source, check=True
    )
    subprocess.run(
        ["git", "remote", "add", "origin", "https://example.invalid/org/parent.git"],
        cwd=source,
        check=True,
    )
    subprocess.run(
        ["git", "fetch", "-q", str(child), child_commit], cwd=source, check=True
    )
    subprocess.run(
        [
            "git",
            "update-index",
            "--add",
            "--cacheinfo",
            f"160000,{child_commit},modules/example",
        ],
        cwd=source,
        check=True,
    )
    subprocess.run(["git", "commit", "-qm", "parent fixture"], cwd=source, check=True)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=source,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    listing, entries = fresh._parse_tree(source, commit)
    assert (
        b"160000 commit " + child_commit.encode() + b"       -\tmodules/example\0"
        in listing
    )
    assert entries == [
        {
            "mode": "160000",
            "type": "commit",
            "object": child_commit,
            "size": None,
            "path": "modules/example",
        }
    ]

    isolated = tmp_path / "isolated-gitlink"
    materialized = fresh._materialize_tree(source, commit, isolated)
    assert materialized["gitlinks"] == [
        {"path": "modules/example", "commit": child_commit}
    ]
    assert (isolated / "modules/example").is_dir()
    assert not any((isolated / "modules/example").iterdir())
    assert not (isolated / ".git/index").exists()
