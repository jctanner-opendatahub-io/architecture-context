#!/usr/bin/env python3
"""Audit surface-planning inputs already stored below ``architecture/``.

The audit is deliberately read-only. It does not validate legacy documents as
if they had produced a coverage sidecar, and it does not infer semantic recall
from source-path mentions in Markdown.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.architecture_surface_coverage import (  # noqa: E402
    SCHEMA_VERSION as COVERAGE_SCHEMA_VERSION,
)
from lib.architecture_surface_coverage import build_surface_inventory  # noqa: E402

AUDIT_SCHEMA_VERSION = "architecture-surface-rollout-audit/v1"
SPECIAL_DOCUMENTS = frozenset({"INDEX.md", "PLATFORM.md", "README.md"})
SIDECAR_NAME = "SURFACE_COVERAGE.json"
REPRESENTATIVES_PER_ROLE = 3
LEGACY_FULL_LLM_PLATFORM_RE = re.compile(
    r"^rhoai-(?:2\.\d+|3\.[0-5](?:$|-))"
)

INTERPRETATION_LIMITS = [
    (
        "Before the 3.6 era, an external architecture-analyzer supplied context "
        "while the LLM retained full control of the generated summary. Those "
        "documents are a distinct legacy cohort, not missing project arch-analyzer "
        "outputs."
    ),
    (
        "A missing legacy coverage sidecar means disposition, read, merge, and "
        "validator telemetry is unavailable. It is not evidence that behavior is "
        "absent from a document."
    ),
    (
        "A document mention of an analyzer candidate path is a structural signal "
        "only. It does not establish that the document expresses the behavior."
    ),
    (
        "Stored analyzer artifacts without behavioral_evidence cannot be used to "
        "estimate the new extractor's recall or false-positive rate."
    ),
    (
        "Repeated platform copies are counted as artifact occurrences and also "
        "collapsed by repository identity for recurrence estimates."
    ),
    (
        "The audit reads no source checkout, pipeline log, agent transcript, or "
        "external service and does not modify generated architecture."
    ),
]


class AuditError(ValueError):
    """Raised when the audit boundary or output contract is invalid."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_bytes(path: Path) -> bytes:
    return path.read_bytes()


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _sorted_counts(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def _primary_role(roles: list[str]) -> str:
    for role in ("operator", "service", "manifest", "unknown"):
        if role in roles:
            return role
    return "unknown"


def _unpaired_generation_cohort(platform: str) -> str:
    if LEGACY_FULL_LLM_PLATFORM_RE.match(platform):
        return "external-architecture-analyzer-full-llm"
    return "no-project-arch-analyzer-artifact-unclassified"


def _behavioral_state(analyzer: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    if "behavioral_evidence" not in analyzer:
        return "field-absent", []
    value = analyzer["behavioral_evidence"]
    if not isinstance(value, list):
        return "field-invalid", []
    records = [item for item in value if isinstance(item, dict)]
    if not records:
        return "present-empty", []
    return "present-records", records


def _gap_candidates(analyzer: dict[str, Any]) -> list[dict[str, str]]:
    index = analyzer.get("gap_evidence_index")
    if not isinstance(index, dict):
        return []
    result: list[dict[str, str]] = []
    for category in sorted(index):
        records = index[category]
        if not isinstance(records, list):
            continue
        for record in records:
            if not isinstance(record, dict):
                continue
            if record.get("status") not in {"candidate", "unresolved"}:
                continue
            result.append(
                {
                    "category": str(category),
                    "question": str(record.get("question", "")).strip(),
                    "source": str(record.get("source", "")).strip(),
                    "line_range": str(record.get("line_range", "")).strip(),
                    "status": str(record.get("status", "")),
                }
            )
    return result


def _sidecar_state(path: Path) -> tuple[str, str | None]:
    if not path.is_file():
        return "missing-legacy-telemetry", None
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return "present-invalid-json", None
    if not isinstance(payload, dict):
        return "present-invalid-structure", None
    version = payload.get("schema_version")
    if version != COVERAGE_SCHEMA_VERSION:
        return "present-schema-mismatch", str(version)
    return "present-unvalidated", str(version)


def _surface_record(surface: dict[str, Any], document: str) -> dict[str, Any]:
    candidates = surface.get("candidate_locations")
    if not isinstance(candidates, list):
        candidates = []
    exact_paths = sorted(
        {
            str(candidate["path"])
            for candidate in candidates
            if isinstance(candidate, dict)
            and isinstance(candidate.get("path"), str)
            and candidate["path"]
        }
    )
    patterns = sorted(
        {
            str(candidate["path_pattern"])
            for candidate in candidates
            if isinstance(candidate, dict)
            and isinstance(candidate.get("path_pattern"), str)
            and candidate["path_pattern"]
        }
    )
    mentioned = [path for path in exact_paths if path in document]
    if not exact_paths:
        reference_signal = "unavailable"
    elif mentioned:
        reference_signal = "present"
    else:
        reference_signal = "absent"
    return {
        "surface_id": str(surface.get("id", "")),
        "priority": str(surface.get("priority", "")),
        "component_role": str(surface.get("component_role", "")),
        "exact_candidate_paths": exact_paths,
        "candidate_path_patterns": patterns,
        "document_candidate_paths_mentioned": mentioned,
        "document_reference_signal": reference_signal,
    }


def _fingerprint(entries: list[tuple[str, bytes]]) -> str:
    digest = hashlib.sha256()
    for name, content in sorted(entries, key=lambda item: item[0]):
        digest.update(name.encode())
        digest.update(b"\0")
        digest.update(content)
        digest.update(b"\0")
    return digest.hexdigest()


def _top_counts(counter: Counter[str], limit: int = 12) -> list[dict[str, Any]]:
    ranked = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    return [
        {"value": value, "count": count}
        for value, count in ranked[:limit]
    ]


def _representatives(components: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Repeated platform copies of one repository may differ. Keep the observation
    # with the richest required inventory, then use stable path order as a tie-break.
    preferred: dict[str, dict[str, Any]] = {}
    for component in components:
        repository = component["repository"]
        current = preferred.get(repository)
        score = (
            component["required_surface_count"],
            component["surface_count"],
            component["artifact_key"],
        )
        if current is None:
            preferred[repository] = component
            continue
        current_score = (
            current["required_surface_count"],
            current["surface_count"],
            current["artifact_key"],
        )
        if score > current_score:
            preferred[repository] = component

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for component in preferred.values():
        grouped[component["primary_role"]].append(component)

    result: list[dict[str, Any]] = []
    for role in ("operator", "service", "manifest", "unknown"):
        candidates = sorted(
            grouped.get(role, []),
            key=lambda component: (
                -component["required_surface_count"],
                -component["surface_count"],
                component["repository"],
                component["artifact_key"],
            ),
        )
        for component in candidates[:REPRESENTATIVES_PER_ROLE]:
            result.append(
                {
                    "primary_role": role,
                    "artifact_key": component["artifact_key"],
                    "repository": component["repository"],
                    "commit_sha": component["commit_sha"],
                    "document": component["document"],
                    "analyzer": component["analyzer"],
                    "required_surface_count": component["required_surface_count"],
                    "surface_ids": [
                        surface["surface_id"] for surface in component["surfaces"]
                    ],
                }
            )
    return result


def _follow_ups(
    *,
    summary: dict[str, Any],
    fips_without_facts: int,
    fips_without_fact_repositories: int,
) -> list[dict[str, Any]]:
    follow_ups: list[dict[str, Any]] = []
    behavioral = summary["behavioral_evidence"]
    unavailable = (
        behavioral["field_states"].get("field-absent", 0)
        + behavioral["field_states"].get("field-invalid", 0)
    )
    if unavailable:
        follow_ups.append(
            {
                "rank": 1,
                "id": "refresh-stored-behavioral-evidence",
                "evidence": (
                    f"{unavailable} analyzer artifact(s) do not expose a usable "
                    "behavioral_evidence field."
                ),
                "action": (
                    "Refresh stored analyzer artifacts before using this corpus to "
                    "judge behavioral-extractor warning quality."
                ),
            }
        )
    if fips_without_facts:
        follow_ups.append(
            {
                "rank": 2,
                "id": "narrow-runtime-fips-applicability",
                "evidence": (
                    f"Runtime FIPS is nominated for {fips_without_facts} artifact(s) "
                    f"across {fips_without_fact_repositories} repository identity(s) "
                    "whose analyzer category reports zero facts."
                ),
                "action": (
                    "Review the role rule and applicability basis so generic category "
                    "coverage does not create required-surface warning noise."
                ),
            }
        )
    unknown_roles = summary["roles"].get("unknown", 0)
    if unknown_roles:
        follow_ups.append(
            {
                "rank": 3,
                "id": "improve-role-classification",
                "evidence": (
                    f"{unknown_roles} eligible artifact(s) retain the unknown role."
                ),
                "action": (
                    "Add deterministic role signals before expanding role-specific "
                    "surface rules."
                ),
            }
        )
    missing_sidecars = summary["sidecars"].get("missing-legacy-telemetry", 0)
    if missing_sidecars:
        follow_ups.append(
            {
                "rank": 4,
                "id": "define-legacy-sidecar-adoption",
                "evidence": (
                    f"{missing_sidecars} eligible legacy artifact(s) have no coverage "
                    "sidecar."
                ),
                "action": (
                    "Keep enforcement warning-only and define an adoption boundary for "
                    "newly generated versus legacy documents."
                ),
            }
        )
    return follow_ups


def audit_architecture_tree(architecture_root: str | Path) -> dict[str, Any]:
    root = Path(architecture_root).resolve()
    if not root.is_dir():
        raise AuditError(f"architecture root does not exist: {root}")

    fingerprint_entries: list[tuple[str, bytes]] = []
    aliases: list[dict[str, str]] = []
    platform_rows: list[dict[str, Any]] = []
    components: list[dict[str, Any]] = []
    invalid_analyzers: list[dict[str, str]] = []
    analyzers_without_document: list[str] = []
    documents_without_analyzer: list[str] = []

    role_counts: Counter[str] = Counter()
    primary_role_counts: Counter[str] = Counter()
    priority_counts: Counter[str] = Counter()
    analyzer_versions: Counter[str] = Counter()
    behavior_states: Counter[str] = Counter()
    behavior_kinds: Counter[str] = Counter()
    behavior_statuses: Counter[str] = Counter()
    gap_categories: Counter[str] = Counter()
    gap_questions: Counter[str] = Counter()
    sidecar_states: Counter[str] = Counter()
    surface_occurrences: Counter[str] = Counter()
    surface_priorities: dict[str, Counter[str]] = defaultdict(Counter)
    surface_roles: dict[str, Counter[str]] = defaultdict(Counter)
    surface_repositories: dict[str, set[str]] = defaultdict(set)
    surface_platforms: dict[str, set[str]] = defaultdict(set)
    surface_exact_candidates: Counter[str] = Counter()
    surface_reference_present: Counter[str] = Counter()
    surface_reference_absent: Counter[str] = Counter()
    repositories: set[str] = set()
    fips_without_facts = 0
    fips_without_fact_repositories: set[str] = set()
    unpaired_generation_cohorts: Counter[str] = Counter()

    for platform_path in sorted(root.iterdir(), key=lambda path: path.name):
        if platform_path.is_symlink():
            aliases.append(
                {
                    "path": platform_path.name,
                    "target": os.readlink(platform_path),
                    "reason": "platform-symlink-alias-excluded",
                }
            )
            fingerprint_entries.append(
                (f"@alias/{platform_path.name}", os.readlink(platform_path).encode())
            )
            continue
        if not platform_path.is_dir():
            continue

        platform = platform_path.name
        documents = {
            path.stem: path
            for path in sorted(platform_path.glob("*.md"))
            if path.name not in SPECIAL_DOCUMENTS and not path.is_symlink()
        }
        for document in documents.values():
            fingerprint_entries.append(
                (f"document/{_relative(root, document)}", _read_bytes(document))
            )

        analyzer_paths: dict[str, Path] = {}
        for component_path in sorted(
            platform_path.iterdir(), key=lambda path: path.name
        ):
            if not component_path.is_dir() or component_path.is_symlink():
                continue
            analyzer_path = component_path / ".analyzer/component-architecture.json"
            if analyzer_path.is_file():
                analyzer_paths[component_path.name] = analyzer_path
                fingerprint_entries.append(
                    (
                        f"analyzer/{_relative(root, analyzer_path)}",
                        _read_bytes(analyzer_path),
                    )
                )

        missing_for_platform = sorted(set(documents) - set(analyzer_paths))
        orphaned_for_platform = sorted(set(analyzer_paths) - set(documents))
        unpaired_generation_cohorts[
            _unpaired_generation_cohort(platform)
        ] += len(missing_for_platform)
        documents_without_analyzer.extend(
            f"{platform}/{component}.md" for component in missing_for_platform
        )
        analyzers_without_document.extend(
            f"{platform}/{component}/.analyzer/component-architecture.json"
            for component in orphaned_for_platform
        )

        eligible_for_platform = 0
        invalid_for_platform = 0
        for component in sorted(set(documents) & set(analyzer_paths)):
            document_path = documents[component]
            analyzer_path = analyzer_paths[component]
            try:
                analyzer = json.loads(analyzer_path.read_text())
                if not isinstance(analyzer, dict):
                    raise AuditError("analyzer root must be an object")
                inventory = build_surface_inventory(analyzer, component=component)
            except (
                OSError,
                json.JSONDecodeError,
                AuditError,
                TypeError,
                ValueError,
            ) as error:
                invalid_for_platform += 1
                invalid_analyzers.append(
                    {
                        "path": _relative(root, analyzer_path),
                        "error": f"{type(error).__name__}: {error}",
                    }
                )
                continue

            eligible_for_platform += 1
            document_bytes = _read_bytes(document_path)
            document_text = document_bytes.decode("utf-8", errors="replace")
            roles = [str(role) for role in inventory.get("component_roles", [])]
            primary_role = _primary_role(roles)
            repository = str(analyzer.get("repo") or f"component:{component}")
            repositories.add(repository)
            role_counts.update(roles)
            primary_role_counts[primary_role] += 1
            analyzer_versions[str(analyzer.get("analyzer_version", "unknown"))] += 1

            behavior_state, behaviors = _behavioral_state(analyzer)
            behavior_states[behavior_state] += 1
            for behavior in behaviors:
                behavior_kinds[str(behavior.get("kind", "unknown"))] += 1
                behavior_statuses[str(behavior.get("status", "unknown"))] += 1

            gaps = _gap_candidates(analyzer)
            for gap in gaps:
                gap_categories[gap["category"]] += 1
                if gap["question"]:
                    gap_questions[gap["question"]] += 1

            sidecar_path = (
                platform_path / component / ".generation" / SIDECAR_NAME
            )
            sidecar_state, sidecar_schema = _sidecar_state(sidecar_path)
            sidecar_states[sidecar_state] += 1
            if sidecar_path.is_file():
                fingerprint_entries.append(
                    (
                        f"sidecar/{_relative(root, sidecar_path)}",
                        _read_bytes(sidecar_path),
                    )
                )

            surfaces = [
                _surface_record(surface, document_text)
                for surface in inventory.get("surfaces", [])
                if isinstance(surface, dict)
            ]
            for surface in surfaces:
                surface_id = surface["surface_id"]
                priority = surface["priority"]
                role = surface["component_role"]
                surface_occurrences[surface_id] += 1
                surface_priorities[surface_id][priority] += 1
                surface_roles[surface_id][role] += 1
                surface_repositories[surface_id].add(repository)
                surface_platforms[surface_id].add(platform)
                priority_counts[priority] += 1
                if surface["exact_candidate_paths"]:
                    surface_exact_candidates[surface_id] += 1
                if surface["document_reference_signal"] == "present":
                    surface_reference_present[surface_id] += 1
                elif surface["document_reference_signal"] == "absent":
                    surface_reference_absent[surface_id] += 1

            fips_record = (
                analyzer.get("category_coverage", {}).get("fips_compliance")
                if isinstance(analyzer.get("category_coverage"), dict)
                else None
            )
            if any(
                surface["surface_id"] == "compliance.runtime-fips"
                for surface in surfaces
            ) and (
                not isinstance(fips_record, dict)
                or not isinstance(fips_record.get("fact_count"), int)
                or fips_record["fact_count"] == 0
            ):
                fips_without_facts += 1
                fips_without_fact_repositories.add(repository)

            components.append(
                {
                    "artifact_key": f"{platform}/{component}",
                    "platform": platform,
                    "component": component,
                    "repository": repository,
                    "commit_sha": str(analyzer.get("commit_sha", "")),
                    "analyzer_version": str(
                        analyzer.get("analyzer_version", "unknown")
                    ),
                    "document": _relative(root, document_path),
                    "document_sha256": _sha256(document_bytes),
                    "analyzer": _relative(root, analyzer_path),
                    "analyzer_sha256": _sha256(_read_bytes(analyzer_path)),
                    "roles": roles,
                    "primary_role": primary_role,
                    "surface_count": len(surfaces),
                    "required_surface_count": sum(
                        surface["priority"] == "required" for surface in surfaces
                    ),
                    "surfaces": surfaces,
                    "behavioral_evidence": {
                        "field_state": behavior_state,
                        "record_count": len(behaviors),
                        "observed_count": sum(
                            behavior.get("status") == "observed"
                            for behavior in behaviors
                        ),
                        "precise_unresolved_count": sum(
                            behavior.get("status") == "unresolved"
                            for behavior in behaviors
                        ),
                    },
                    "generic_gap_candidate_count": len(gaps),
                    "sidecar": {
                        "state": sidecar_state,
                        "schema_version": sidecar_schema,
                    },
                }
            )

        platform_rows.append(
            {
                "platform": platform,
                "component_documents": len(documents),
                "project_arch_analyzer_artifacts": len(analyzer_paths),
                "eligible_pairs": eligible_for_platform,
                "documents_without_project_arch_analyzer": len(
                    missing_for_platform
                ),
                "project_arch_analyzers_without_document": len(
                    orphaned_for_platform
                ),
                "invalid_analyzers": invalid_for_platform,
                "generation_cohort": (
                    "legacy-external-analyzer-full-llm"
                    if LEGACY_FULL_LLM_PLATFORM_RE.match(platform)
                    else "3.6-era-or-rolling"
                ),
            }
        )

    components.sort(key=lambda component: component["artifact_key"])
    surface_rows = []
    for surface_id in sorted(surface_occurrences):
        surface_rows.append(
            {
                "surface_id": surface_id,
                "artifact_occurrences": surface_occurrences[surface_id],
                "repository_occurrences": len(surface_repositories[surface_id]),
                "platforms": sorted(surface_platforms[surface_id]),
                "priorities": _sorted_counts(surface_priorities[surface_id]),
                "roles": _sorted_counts(surface_roles[surface_id]),
                "with_exact_candidates": surface_exact_candidates[surface_id],
                "with_document_candidate_reference": surface_reference_present[
                    surface_id
                ],
                "without_document_candidate_reference": surface_reference_absent[
                    surface_id
                ],
            }
        )

    summary = {
        "canonical_component_documents": sum(
            row["component_documents"] for row in platform_rows
        ),
        "project_arch_analyzer_artifacts": sum(
            row["project_arch_analyzer_artifacts"] for row in platform_rows
        ),
        "eligible_pairs": len(components),
        "unique_repository_identities": len(repositories),
        "duplicate_repository_artifacts": max(0, len(components) - len(repositories)),
        "documents_without_project_arch_analyzer": len(
            documents_without_analyzer
        ),
        "project_arch_analyzers_without_document": len(
            analyzers_without_document
        ),
        "invalid_analyzers": len(invalid_analyzers),
        "platform_aliases_excluded": len(aliases),
        "surface_occurrences": sum(surface_occurrences.values()),
        "roles": _sorted_counts(role_counts),
        "primary_roles": _sorted_counts(primary_role_counts),
        "priorities": _sorted_counts(priority_counts),
        "sidecars": _sorted_counts(sidecar_states),
        "behavioral_evidence": {
            "field_states": _sorted_counts(behavior_states),
            "record_count": sum(behavior_kinds.values()),
            "kinds": _sorted_counts(behavior_kinds),
            "statuses": _sorted_counts(behavior_statuses),
        },
        "generic_gap_candidate_count": sum(gap_categories.values()),
        "generation_cohorts": {
            "project-arch-analyzer-valid-pairs": len(components),
            "project-arch-analyzer-invalid-pairs": len(invalid_analyzers),
            **_sorted_counts(unpaired_generation_cohorts),
        },
    }

    missing_by_platform: Counter[str] = Counter(
        item.split("/", 1)[0] for item in documents_without_analyzer
    )
    excluded_inputs = {
        "platform_aliases": aliases,
        "documents_without_project_arch_analyzer": {
            "count": len(documents_without_analyzer),
            "by_platform": _sorted_counts(missing_by_platform),
            "examples": documents_without_analyzer[:12],
        },
        "project_arch_analyzers_without_document": analyzers_without_document,
        "invalid_analyzers": invalid_analyzers,
    }

    report = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "policy": {
            "input_boundary": "architecture-only",
            "read_only": True,
            "coverage_enforcement": "warning-only",
            "component_generation_workers": "disabled",
            "missing_sidecar_interpretation": "legacy-telemetry-unavailable",
            "generation_history": (
                "Pre-3.6 documents used an external architecture-analyzer with "
                "full LLM control of the generated summary."
            ),
            "generation_history_source": "project-owner-provided",
        },
        "input": {
            "architecture_root": root.name,
            "fingerprint_sha256": _fingerprint(fingerprint_entries),
            "fingerprinted_entry_count": len(fingerprint_entries),
        },
        "summary": summary,
        "platforms": platform_rows,
        "analyzer_evidence": {
            "versions": _sorted_counts(analyzer_versions),
            "behavioral_evidence": summary["behavioral_evidence"],
            "generic_gap_candidates": {
                "total": sum(gap_categories.values()),
                "by_category": _sorted_counts(gap_categories),
                "top_questions": _top_counts(gap_questions),
            },
        },
        "surface_inventory": {
            "total_occurrences": sum(surface_occurrences.values()),
            "by_priority": _sorted_counts(priority_counts),
            "by_surface": surface_rows,
            "structural_signal_only": True,
        },
        "representative_review_set": _representatives(components),
        "follow_up_priorities": _follow_ups(
            summary=summary,
            fips_without_facts=fips_without_facts,
            fips_without_fact_repositories=len(fips_without_fact_repositories),
        ),
        "excluded_inputs": excluded_inputs,
        "components": components,
        "interpretation_limits": INTERPRETATION_LIMITS,
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Architecture Surface Rollout Audit",
        "",
        f"Input fingerprint: `{report['input']['fingerprint_sha256']}`.",
        "",
        "This is a read-only audit of on-disk architecture documents and analyzer "
        "artifacts. Coverage enforcement remains warning-only and component-generation "
        "workers remain disabled.",
        "",
        "## Corpus",
        "",
        "| Measure | Count |",
        "|---|---:|",
        "| Canonical component documents | "
        f"{summary['canonical_component_documents']} |",
        "| Project arch-analyzer artifacts | "
        f"{summary['project_arch_analyzer_artifacts']} |",
        "| Eligible document/project-analyzer pairs | "
        f"{summary['eligible_pairs']} |",
        f"| Unique repository identities | {summary['unique_repository_identities']} |",
        "| Duplicate repository artifacts | "
        f"{summary['duplicate_repository_artifacts']} |",
        "| Documents without project arch-analyzer artifacts | "
        f"{summary['documents_without_project_arch_analyzer']} |",
        f"| Invalid analyzers | {summary['invalid_analyzers']} |",
        f"| Excluded platform aliases | {summary['platform_aliases_excluded']} |",
        "",
        "## Generation cohorts",
        "",
        "| Cohort | Component documents |",
        "|---|---:|",
    ]
    for cohort, count in summary["generation_cohorts"].items():
        lines.append(f"| {cohort} | {count} |")
    lines.extend(
        [
            "",
            "Pre-3.6 documents used an external `architecture-analyzer`, and the "
            "LLM retained full control of each generated summary. They are an "
            "incomparable legacy cohort, not missing project `arch-analyzer` "
            "outputs. Documents from rolling or 3.6-era directories without a "
            "stored project analyzer remain unclassified.",
            "",
            "## Telemetry boundary",
            "",
            "| Sidecar state | Count |",
            "|---|---:|",
        ]
    )
    for state, count in summary["sidecars"].items():
        lines.append(f"| {state} | {count} |")
    lines.extend(
        [
            "",
            "Missing legacy sidecars are counted as unavailable disposition/read/merge "
            "telemetry. They are not counted as behavioral omissions.",
            "",
            "## Platforms",
            "",
            "| Platform | Cohort | Documents | Project analyzers | Eligible | "
            "Without project analyzer | Invalid |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for platform in report["platforms"]:
        lines.append(
            "| {platform} | {generation_cohort} | {component_documents} | "
            "{project_arch_analyzer_artifacts} | "
            "{eligible_pairs} | {documents_without_project_arch_analyzer} | "
            "{invalid_analyzers} |".format(**platform)
        )

    behavioral = report["analyzer_evidence"]["behavioral_evidence"]
    lines.extend(
        [
            "",
            "## Analyzer evidence capability",
            "",
            "| Behavioral evidence field state | Artifacts |",
            "|---|---:|",
        ]
    )
    for state, count in behavioral["field_states"].items():
        lines.append(f"| {state} | {count} |")
    lines.extend(
        [
            f"| Extracted behavioral records | {behavioral['record_count']} |",
            "",
            "| Generic gap category | Candidate records |",
            "|---|---:|",
        ]
    )
    for category, count in report["analyzer_evidence"]["generic_gap_candidates"][
        "by_category"
    ].items():
        lines.append(f"| {category} | {count} |")

    lines.extend(
        [
            "",
            "## Nominated surfaces",
            "",
            "| Surface | Artifacts | Repositories | Exact candidates | "
            "Document path signal |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for surface in report["surface_inventory"]["by_surface"]:
        lines.append(
            "| {surface_id} | {artifact_occurrences} | {repository_occurrences} | "
            "{with_exact_candidates} | {with_document_candidate_reference} |".format(
                **surface
            )
        )
    lines.extend(
        [
            "",
            "A document path signal only means that at least one exact analyzer "
            "candidate path appears in the Markdown. It is not semantic coverage.",
            "",
            "## Representative review set",
            "",
            "| Role | Artifact | Required surfaces | Repository |",
            "|---|---|---:|---|",
        ]
    )
    for item in report["representative_review_set"]:
        lines.append(
            f"| {item['primary_role']} | `{item['artifact_key']}` | "
            f"{item['required_surface_count']} | `{item['repository']}` |"
        )

    lines.extend(["", "## Prioritized follow-up", ""])
    for item in report["follow_up_priorities"]:
        lines.extend(
            [
                f"{item['rank']}. **{item['id']}** — {item['evidence']} "
                f"{item['action']}",
                "",
            ]
        )
    lines.extend(["## Interpretation limits", ""])
    lines.extend(f"- {limit}" for limit in report["interpretation_limits"])
    lines.append("")
    return "\n".join(lines)


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--architecture-root", type=Path, default=PROJECT_ROOT / "architecture"
    )
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args()
    for output in (args.output_json, args.output_markdown):
        if _is_within(output, args.architecture_root):
            parser.error("audit outputs must remain outside the architecture tree")
    try:
        report = audit_architecture_tree(args.architecture_root)
    except (OSError, AuditError) as error:
        parser.error(str(error))
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.output_markdown.write_text(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
