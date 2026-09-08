"""Regression tests for analyzer RBAC rows lost during promotion.

These tests intentionally exercise the retained canary row shape as well as a
current analyzer shape that carries Kubernetes ``nonResourceURLs``.  The
canary artifacts are evidence fixtures and are never modified by this module.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.architecture_baseline import (  # noqa: E402
    _normalize_row_key,
    parse_component_markdown_text,
)
from lib.architecture_merge import (  # noqa: E402
    ArchitectureMergeError,
    _document_table_rows,
    merge_architecture_documents,
)

LIVE_ROOT = PROJECT_ROOT / "evaluations/architecture-surface-coverage/live-canary"
RUN_IDS = (
    "claude-repetition-1",
    "claude-repetition-2",
    "codex-repetition-1",
    "codex-repetition-2",
)
NON_RESOURCE_ROWS = {
    "opendatahub-operator-metrics-reader",
    "metrics-reader",
}


def _rbac_document(
    rows: list[tuple[str, ...]], *, with_urls: bool = False
) -> str:
    if with_urls:
        headers = "| Role Name | API Group | Resources | Non-Resource URLs | Verbs |"
        separator = "|-----------|-----------|-----------|-------------------|-------|"
    else:
        headers = "| Role Name | API Group | Resources | Verbs |"
        separator = "|-----------|-----------|-----------|-------|"
    body = "\n".join("| " + " | ".join(row) + " |" for row in rows)
    return f"""# Component: RBAC fixture

## Purpose

Analyzer purpose.

## Data Flows

Analyzer flows.

## Architectural Analysis

Analyzer analysis.

## Security

### RBAC - Cluster Roles

{headers}
{separator}
{body}
"""


def _rbac_rows(text: str):
    document = parse_component_markdown_text(text)
    return [
        row
        for table in _document_table_rows(document.tables)
        if table.category == "rbac_cluster_roles"
        for row in table.rows
    ]


def _remove_misplaced_fips_candidate(text: str) -> str:
    """Remove only the known malformed section from the in-memory fixture copy."""

    marker = "## Admission Webhooks\n"
    start = text.find(marker)
    if start < 0:
        return text
    fips = text.find("### FIPS Compliance\n", start)
    next_section = text.find("## Data Flows\n", fips)
    if fips < 0 or next_section < 0:
        return text
    return text[:fips] + text[next_section:]


def test_analyzer_rendering_preserves_non_resource_urls(tmp_path: Path) -> None:
    """The analyzer model and Markdown renderer must retain GET /metrics."""

    input_path = tmp_path / "component-architecture.json"
    output_path = tmp_path / "architecture.md"
    input_path.write_text(
        json.dumps(
            {
                "component": "metrics-fixture",
                "repo": "example/metrics-fixture",
                "commit_sha": "fixture",
                "summary": "Metrics fixture.",
                "behavioral_evidence": [],
                "rbac": {
                    "cluster_roles": [
                        {
                            "name": "metrics-reader",
                            "source": "config/rbac.yaml:1",
                            "rules": [
                                {
                                    "apiGroups": [],
                                    "resources": [],
                                    "nonResourceURLs": ["/metrics"],
                                    "verbs": ["get"],
                                }
                            ],
                        }
                    ]
                },
            }
        )
    )

    subprocess.run(
        [
            "go",
            "run",
            ".",
            "render",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ],
        cwd=PROJECT_ROOT / "src/arch-analyzer",
        env={**os.environ, "GOCACHE": "/tmp/promotion-repair-analyzer-gocache"},
        check=True,
        capture_output=True,
        text=True,
    )

    rendered = output_path.read_text()
    assert (
        "| Role Name | API Group | Resources | Non-Resource URLs | Verbs |"
        in rendered
    )
    assert "| metrics-reader |  |  | /metrics | get |" in rendered


def test_resource_and_non_resource_rbac_identities_do_not_collide() -> None:
    resource = _normalize_row_key("rbac_cluster_roles", ("reader", "apps", "pods"))
    non_resource = _normalize_row_key(
        "rbac_cluster_roles", ("reader", "<non-resource>", "/metrics")
    )
    other_non_resource = _normalize_row_key(
        "rbac_cluster_roles", ("reader", "<non-resource>", "/healthz")
    )

    assert resource != non_resource
    assert non_resource != other_non_resource
    assert resource == ("reader", "apps", "pods")
    assert non_resource == ("reader", "<non-resource>", "/metrics")


def test_non_resource_rows_are_parsed_with_empty_resource_column() -> None:
    document = _rbac_document(
        [
            ("reader", "apps", "pods", "", "get"),
            ("reader", "", "", "/metrics", "get"),
        ],
        with_urls=True,
    )

    rows = _rbac_rows(document)

    assert len(rows) == 2
    assert len({row.key for row in rows}) == 2
    non_resource = next(row for row in rows if row.key[-1] == "/metrics")
    assert non_resource.key == ("reader", "<non-resource>", "/metrics")
    assert non_resource.cells["api_group"] == ""
    assert non_resource.cells["resources"] == ""
    assert non_resource.cells["non_resource_urls"] == "/metrics"


def test_mixed_resource_target_does_not_collide_with_either_rule_kind() -> None:
    document = _rbac_document(
        [
            ("reader", "", "pods", "", "get"),
            ("reader", "", "", "/metrics", "get"),
            ("reader", "", "pods", "/metrics", "get"),
        ],
        with_urls=True,
    )

    keys = {row.key for row in _rbac_rows(document)}

    assert len(keys) == 3
    assert any(key[1] == "<mixed-resource-target>" for key in keys)


def test_legacy_rbac_rows_do_not_invent_non_resource_urls() -> None:
    document = _rbac_document([("legacy-reader", "", "", "get")])

    rows = _rbac_rows(document)

    assert len(rows) == 1
    assert rows[0].key == ("legacy-reader", "<legacy-target-unknown>", "get")
    assert rows[0].cells["resources"] == ""
    assert "/metrics" not in rows[0].key
    assert all("/metrics" not in value for value in rows[0].cells.values())


def test_missing_non_resource_row_is_restored_and_accounted_for() -> None:
    analyzer = _rbac_document(
        [("metrics-reader", "", "", "/metrics", "get")], with_urls=True
    )
    candidate = _rbac_document([], with_urls=True)

    result = merge_architecture_documents(analyzer, candidate)

    assert "| metrics-reader |  |  | /metrics | get |" in result.text
    assert any(
        decision.status == "restored"
        and decision.action == "delete"
        and decision.category == "rbac_cluster_roles"
        for decision in result.decisions
    )
    assert result.counts["restored"] == 1


def test_non_resource_patch_key_authorizes_only_the_matching_url_row() -> None:
    analyzer = _rbac_document([], with_urls=True)
    candidate = _rbac_document(
        [("metrics-reader", "", "", "/metrics", "get")], with_urls=True
    )
    patch = json.dumps(
        {
            "schema_version": 1,
            "operations": [
                {
                    "action": "add",
                    "category": "rbac_cluster_roles",
                    "key": [
                        "metrics-reader",
                        "<non-resource>",
                        "/metrics",
                    ],
                    "column": "*",
                    "analyzer_value": None,
                    "candidate_value": None,
                    "reason": "The role grants metrics access.",
                    "evidence": ["config/rbac.yaml:1"],
                }
            ],
        }
    )

    result = merge_architecture_documents(
        analyzer, candidate, patch_text=patch
    )

    assert "| metrics-reader |  |  | /metrics | get |" in result.text
    assert result.counts["applied"] == 1


def test_legacy_blank_target_cannot_authorize_an_invented_url() -> None:
    analyzer = _rbac_document([("metrics-reader", "", "", "get")])
    candidate = _rbac_document(
        [("metrics-reader", "", "", "/metrics", "get")], with_urls=True
    )

    result = merge_architecture_documents(analyzer, candidate)

    assert (
        "| Role Name | API Group | Resources | Non-Resource URLs | Verbs |"
        in result.text
    )
    assert "| metrics-reader |  |  |  | get |" in result.text
    assert "/metrics" not in result.text
    assert result.counts["restored"] == 1
    assert result.counts["rejected"] == 1


@pytest.mark.parametrize("run_id", RUN_IDS)
def test_all_retained_canary_runs_preserve_non_resource_rows(run_id: str) -> None:
    """Replay each saved row set while isolating the known malformed FIPS case."""

    run_root = LIVE_ROOT / "runs" / run_id
    analyzer = (run_root / "preseed.md").read_text()
    candidate = (run_root / "candidate.md").read_text()
    candidate = _remove_misplaced_fips_candidate(candidate)

    result = merge_architecture_documents(analyzer, candidate)
    promoted_rows = {
        row.key[0]
        for row in _rbac_rows(result.text)
        if row.key and row.key[0] in NON_RESOURCE_ROWS
    }

    assert promoted_rows == NON_RESOURCE_ROWS
    baseline_rows = _rbac_rows(analyzer)
    assert result.unchanged_by_category.get("rbac_cluster_roles", 0) == len(
        baseline_rows
    )


def test_retained_canary_artifacts_still_show_original_rbac_loss() -> None:
    """Pin the actual pre-fix symptom without changing the retained evidence."""

    expected_lines = {
        "| opendatahub-operator-metrics-reader |  |  | get |",
        "| metrics-reader |  |  | get |",
    }
    for run_id in RUN_IDS:
        run_root = LIVE_ROOT / "runs" / run_id
        candidate = (run_root / "candidate.md").read_text()
        promoted = (run_root / "promoted.md").read_text()
        assert expected_lines <= set(candidate.splitlines())
        assert expected_lines.isdisjoint(promoted.splitlines())


def test_raw_analyzer_table_rows_are_not_discarded_when_normalized_identity_is_empty():
    """A legacy analyzer row lacking a URL field remains visible."""

    analyzer = _rbac_document([("legacy-reader", "", "", "get")])
    candidate = _rbac_document([])
    result = merge_architecture_documents(analyzer, candidate)

    assert "| legacy-reader |  |  | get |" in result.text
    assert result.preservation == {
        "expected": 1,
        "all_expected": 1,
        "authorized_deletes": 0,
        "adjudicated_expected": 1,
        "all_adjudicated_expected": 1,
        "unchanged": 0,
        "restored": 1,
        "opaque": 0,
        "preserved": 1,
        "all_preserved": 1,
        "adjudicated_preserved": 1,
        "all_adjudicated_preserved": 1,
        "missing": 0,
        "mapped_missing": 0,
        "all_missing": 0,
        "adjudicated_missing": 0,
        "all_adjudicated_missing": 0,
        "stage": "assembly-complete",
    }


def test_unrepresentable_analyzer_rbac_row_is_retained_or_reports_loss() -> None:
    """Rows outside the normalized identity contract cannot disappear silently."""

    raw_row = "| raw-role |  |  |  |"
    analyzer = _rbac_document([("raw-role", "", "", "")])
    candidate = _rbac_document([])

    try:
        result = merge_architecture_documents(analyzer, candidate)
    except ValueError as error:
        assert "analyzer" in str(error).casefold()
        assert "raw-role" in str(error)
        return

    if raw_row in result.text:
        return

    diagnostics = "\n".join(result.parse_errors)
    assert "raw-role" in diagnostics
    assert "analyzer" in diagnostics.casefold()


def test_assembly_cannot_silently_drop_an_unrepresentable_analyzer_row() -> None:
    analyzer = _rbac_document([("raw-role", "", "", "")])
    candidate = _rbac_document([("raw-role", "", "", "")])

    def discard_row(base: str, _candidate: str) -> str:
        return base.replace("| raw-role |  |  |  |\n", "")

    with pytest.raises(ArchitectureMergeError) as caught:
        merge_architecture_documents(
            analyzer, candidate, section_assembler=discard_row
        )

    result = caught.value.result
    assert result.preservation["opaque"] == 1
    assert result.preservation["missing"] == 1
    assert result.assembly_diagnostics[0]["code"] == (
        "analyzer_row_lost_during_assembly"
    )


def test_rbac_internal_identity_includes_verbs_but_patch_key_does_not() -> None:
    document = _rbac_document(
        [
            ("metrics-reader", "", "", "/metrics", "get"),
            ("metrics-reader", "", "", "/metrics", "head"),
        ],
        with_urls=True,
    )

    rows = _rbac_rows(document)

    assert rows[0].key == rows[1].key
    assert rows[0].identity != rows[1].identity


def test_one_v1_delete_cannot_delete_two_rbac_verb_variants() -> None:
    analyzer = _rbac_document(
        [
            ("metrics-reader", "", "", "/metrics", "get"),
            ("metrics-reader", "", "", "/metrics", "head"),
        ],
        with_urls=True,
    )
    candidate = _rbac_document([], with_urls=True)
    patch = json.dumps(
        {
            "schema_version": 1,
            "operations": [
                {
                    "action": "delete",
                    "category": "rbac_cluster_roles",
                    "key": ["metrics-reader", "<non-resource>", "/metrics"],
                    "column": "*",
                    "analyzer_value": None,
                    "candidate_value": None,
                    "reason": "Fixture deletion request.",
                    "evidence": ["config/rbac.yaml:1"],
                }
            ],
        }
    )

    result = merge_architecture_documents(analyzer, candidate, patch_text=patch)

    assert "| metrics-reader |  |  | /metrics | get |" in result.text
    assert "| metrics-reader |  |  | /metrics | head |" in result.text
    assert result.counts["applied"] == 0
    assert result.counts["restored"] == 2
    assert result.parse_errors


def test_legacy_blank_targets_with_different_api_groups_do_not_collide() -> None:
    document = _rbac_document(
        [
            ("reader", "apps", "", "get"),
            ("reader", "batch", "", "get"),
        ]
    )

    rows = _rbac_rows(document)

    assert rows[0].key == (
        "reader",
        "<legacy-target-unknown>",
        "apps :: get",
    )
    assert rows[1].key == (
        "reader",
        "<legacy-target-unknown>",
        "batch :: get",
    )
    assert rows[0].identity != rows[1].identity


def test_source_backed_non_resource_add_upgrades_legacy_table_schema() -> None:
    analyzer = _rbac_document([])
    candidate = _rbac_document(
        [("health-reader", "", "", "/healthz", "get")],
        with_urls=True,
    )
    patch = json.dumps(
        {
            "schema_version": 1,
            "operations": [
                {
                    "action": "add",
                    "category": "rbac_cluster_roles",
                    "key": ["health-reader", "<non-resource>", "/healthz"],
                    "column": "*",
                    "analyzer_value": None,
                    "candidate_value": None,
                    "reason": "The role grants health endpoint access.",
                    "evidence": ["config/rbac.yaml:1"],
                }
            ],
        }
    )

    result = merge_architecture_documents(analyzer, candidate, patch_text=patch)

    assert (
        "| Role Name | API Group | Resources | Non-Resource URLs | Verbs |"
        in result.text
    )
    assert "| health-reader |  |  | /healthz | get |" in result.text
    assert result.counts["applied"] == 1


def test_assembly_detects_loss_from_an_unmapped_analyzer_table() -> None:
    table = """### Custom Inventory

| Label | Detail |
|-------|--------|
| analyzer-only | retained fact |

"""
    analyzer = _rbac_document([]).replace(
        "### RBAC - Cluster Roles\n", table + "### RBAC - Cluster Roles\n"
    )
    candidate = analyzer

    def discard_unmapped_row(base: str, _candidate: str) -> str:
        return base.replace("| analyzer-only | retained fact |\n", "")

    with pytest.raises(ArchitectureMergeError) as caught:
        merge_architecture_documents(
            analyzer, candidate, section_assembler=discard_unmapped_row
        )

    result = caught.value.result
    assert result.preservation["all_expected"] == 1
    assert result.preservation["all_missing"] == 1
    assert result.preservation["all_adjudicated_missing"] == 1
    assert result.assembly_diagnostics[0]["missing_rows"][0]["category"] == (
        "<unmapped>"
    )
