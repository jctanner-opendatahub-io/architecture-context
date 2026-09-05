"""Surface-level planning and warning-only architecture coverage validation."""

from __future__ import annotations

import copy
import fnmatch
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from lib.architecture_baseline import (
    _TABLE_SPECS,
    _canonical_rows,
    _normalize_key_value,
    _normalize_section,
    _normalize_text,
    _tables_by_category,
    parse_component_markdown,
)

SCHEMA_VERSION = "architecture-surface-coverage/v1"
DISPOSITIONS = frozenset({"documented", "unresolved", "not-applicable"})
EVIDENCE_STATUSES = frozenset({"available", "unavailable", "unresolved"})
CLAIM_SUPPORT_STATUSES = frozenset({"supported", "unsupported", "uncertain"})
APPLICABILITY_STATUSES = frozenset(
    {"applicable", "uncertain", "not-applicable"}
)
PRIORITIES = frozenset({"required", "high", "normal"})
EVIDENCE_KINDS = frozenset(
    {"analyzer-fact", "source-read", "source-candidate", "manifest"}
)
SAFETY_CRITICAL_SURFACES = frozenset(
    {
        "authentication.metrics-enforcement",
        "authentication.admission-serving-identity",
        "authentication.gateway-modes",
        "controller.named-resource-watches",
        "compliance.runtime-fips",
    }
)

_SURFACE_ID_RE = re.compile(r"^[a-z][a-z0-9-]*(?:\.[a-z0-9-]+)+$")
_SOURCE_REF_RE = re.compile(r"^(?P<path>[^:#]+):(?P<lines>\d+(?:-\d+)?)$")


def build_surface_inventory(
    analyzer: dict[str, object],
    *,
    component: str,
) -> dict[str, object]:
    """Build a deterministic, evidence-nominated surface inventory."""

    roles = _component_roles(analyzer)
    surfaces: list[dict[str, object]] = []

    metrics_sources = _operator_manager_metrics_sources(analyzer)
    behavioral_evidence = _dict_list(analyzer.get("behavioral_evidence"))
    named_namespace_behaviors = sorted(
        (
            behavior
            for behavior in behavioral_evidence
            if behavior.get("kind") == "named-watch-predicate"
            and "namespace"
            in str(behavior.get("watched_gvk", "")).casefold()
        ),
        key=lambda behavior: (
            behavior.get("status") != "observed",
            str(behavior.get("source", "")),
        ),
    )
    namespace_watch_sources = _dedupe_locations(
        _source_locations(named_namespace_behaviors)
        + _source_locations(
            [
            watch
            for watch in _dict_list(analyzer.get("controller_watches"))
            if str(watch.get("type", "")).casefold() == "watches"
            and "namespace" in str(watch.get("gvk", "")).casefold()
            ]
        )
    )
    gateway_sources = _source_locations(
        {
            "deployments": analyzer.get("deployments", []),
            "integration_points": analyzer.get("integration_points", []),
            "controller_watches": analyzer.get("controller_watches", []),
            "gap_evidence_index": analyzer.get("gap_evidence_index", {}),
        },
        keywords=("gateway", "oidc", "oauth", "auth proxy"),
    )
    admission_sources = _source_locations(
        {
            "webhooks": analyzer.get("webhooks", []),
            "runtime_webhook_servers": analyzer.get(
                "runtime_webhook_servers", []
            ),
            "authentication": analyzer.get("authentication", []),
        },
        keywords=("webhook", "admission"),
    )
    outbound_sources = _source_locations(
        {
            "runtime_clients": analyzer.get("runtime_clients", []),
            "external_connections": analyzer.get("external_connections", []),
        }
    )
    lifecycle_sources = _source_locations(
        {
            "entrypoints": analyzer.get("entrypoints", []),
            "security_evidence": analyzer.get("security_evidence", []),
        },
        keywords=("tls", "operator", "controller-runtime", "entrypoint"),
    )
    fips_sources = _source_locations(
        analyzer.get("security_evidence", []),
        keywords=("fips", "crypto", "tls"),
    )
    fips_record = _category_coverage(analyzer, "fips_compliance")

    if "operator" in roles:
        surfaces.append(
            _surface(
                surface_id="authentication.metrics-enforcement",
                parent_category="authentication",
                component_role="operator",
                question=(
                    "When and where are the operator metrics endpoint's "
                    "authentication and authorization filters enforced?"
                ),
                priority="required",
                basis=(
                    "Analyzer identifies an operator-manager metrics serving "
                    "surface."
                    if metrics_sources
                    else "The operator role nominates metrics enforcement for "
                    "applicability review; no manager metrics evidence was extracted."
                ),
                candidates=metrics_sources,
            )
        )
    if "operator" in roles and admission_sources:
        surfaces.append(
            _surface(
                surface_id="authentication.admission-serving-identity",
                parent_category="authentication",
                component_role="operator",
                question=(
                    "What admission behavior is served, and what establishes "
                    "the webhook server identity?"
                ),
                priority="high",
                basis="Analyzer webhook or admission authentication evidence.",
                candidates=admission_sources,
            )
        )
    if "operator" in roles and gateway_sources:
        surfaces.append(
            _surface(
                surface_id="authentication.gateway-modes",
                parent_category="authentication",
                component_role="operator",
                question=(
                    "How do integrated OAuth, external OIDC, and externally "
                    "managed authentication change gateway behavior?"
                ),
                priority="required",
                basis="Analyzer gateway, OAuth, OIDC, or auth-proxy signal.",
                candidates=gateway_sources,
            )
        )
    if "operator" in roles and namespace_watch_sources:
        surfaces.append(
            _surface(
                surface_id="controller.named-resource-watches",
                parent_category="internal_dependencies",
                component_role="operator",
                question=(
                    "Which literal resource or namespace names constrain each "
                    "controller watch, and which controller owns the watch?"
                ),
                priority="required",
                basis="Analyzer records one or more Namespace watch candidates.",
                candidates=namespace_watch_sources,
            )
        )
    if outbound_sources:
        surfaces.append(
            _surface(
                surface_id="dependencies.outbound-credentials",
                parent_category="integration_points",
                component_role="operator" if "operator" in roles else "service",
                question=(
                    "Which outbound clients are used, and how are their target, "
                    "credentials, TLS, and failure boundaries configured?"
                ),
                priority="high",
                basis="Analyzer runtime-client or external-connection evidence.",
                candidates=outbound_sources,
            )
        )
    if "operator" in roles and lifecycle_sources:
        surfaces.append(
            _surface(
                surface_id="lifecycle.configuration-tls",
                parent_category="architecture_components",
                component_role="operator",
                question=(
                    "What initialization ordering and TLS-profile lifecycle "
                    "govern the operator's serving surfaces?"
                ),
                priority="high",
                basis="Operator entrypoint or TLS configuration evidence.",
                candidates=lifecycle_sources,
            )
        )
    if fips_record is not None or fips_sources:
        candidates = list(fips_sources)
        candidates.append(
            {
                "path_pattern": "**/*clusterserviceversion*.yaml",
                "origin": "role-rule",
            }
        )
        surfaces.append(
            _surface(
                surface_id="compliance.runtime-fips",
                parent_category="fips_compliance",
                component_role="operator" if "operator" in roles else roles[0],
                question=(
                    "Which build or packaging signals exist, and what source "
                    "evidence establishes or limits runtime FIPS claims?"
                ),
                priority="required",
                basis="Analyzer FIPS category or crypto/TLS evidence.",
                candidates=candidates,
            )
        )

    if "service" in roles and "operator" not in roles:
        service_sources = _source_locations(
            {
                "http_endpoints": analyzer.get("http_endpoints", []),
                "grpc_services": analyzer.get("grpc_services", []),
                "services": analyzer.get("services", []),
            }
        )
        if service_sources:
            surfaces.append(
                _surface(
                    surface_id="authentication.service-endpoints",
                    parent_category="authentication",
                    component_role="service",
                    question=(
                        "Which service endpoints require authentication or "
                        "authorization, and where is each policy enforced?"
                    ),
                    priority="required",
                    basis="Analyzer service endpoint evidence.",
                    candidates=service_sources,
                )
            )

    if "manifest" in roles:
        workload_sources = _source_locations(
            {
                "deployments": analyzer.get("deployments", []),
                "services": analyzer.get("services", []),
                "ingress_routing": analyzer.get("ingress_routing", []),
            }
        )
        if workload_sources:
            surfaces.append(
                _surface(
                    surface_id="network.workload-exposure",
                    parent_category="ingress",
                    component_role="manifest",
                    question=(
                        "How do selected workloads, Services, and ingress "
                        "resources expose the packaged component?"
                    ),
                    priority="required",
                    basis="Manifest-backed workload or exposure evidence.",
                    candidates=workload_sources,
                )
            )
        credential_sources = _source_locations(
            {
                "secrets_referenced": analyzer.get("secrets_referenced", []),
                "rbac": analyzer.get("rbac", []),
            }
        )
        if credential_sources:
            surfaces.append(
                _surface(
                    surface_id="security.credential-wiring",
                    parent_category="secrets",
                    component_role="manifest",
                    question=(
                        "Which workload identities and secret references are "
                        "wired by the selected manifests?"
                    ),
                    priority="high",
                    basis="Manifest-backed secret or RBAC evidence.",
                    candidates=credential_sources,
                )
            )

    surfaces.sort(key=lambda surface: str(surface["id"]))
    identity_payload = {
        "component": component,
        "component_roles": roles,
        "surfaces": surfaces,
    }
    inventory_id = hashlib.sha256(
        json.dumps(identity_payload, sort_keys=True).encode()
    ).hexdigest()
    return {
        "schema_version": SCHEMA_VERSION,
        "component": component,
        "inventory_id": inventory_id,
        "component_roles": roles,
        "surfaces": surfaces,
        "observed_reads": [],
        "validator_findings": [],
        "summary": _summary(surfaces),
    }


def validate_surface_coverage(
    *,
    inventory: dict[str, object],
    sidecar: dict[str, object] | None,
    promoted_document: str | Path | None,
    candidate_document: str | Path | None = None,
    observed_reads: list[dict[str, object]] | None = None,
    analyzer_document: dict[str, object] | None = None,
    source_root: str | Path | None = None,
) -> dict[str, object]:
    """Validate agent dispositions against the final promoted document."""

    findings: list[dict[str, str]] = []
    errors: list[str] = []
    payload = sidecar if isinstance(sidecar, dict) else {}
    expected_component = str(inventory.get("component", ""))
    expected_roles = inventory.get("component_roles")
    inventory_surfaces = _dict_list(inventory.get("surfaces"))
    seeded_by_id = {
        str(surface.get("id", "")): surface for surface in inventory_surfaces
    }
    seeded_ids = set(seeded_by_id)

    if sidecar is None:
        errors.append("surface coverage sidecar is missing or invalid JSON")

    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION!r}")
    if payload.get("component") != expected_component:
        errors.append("component must match the seeded inventory")
    if payload.get("inventory_id") != inventory.get("inventory_id"):
        errors.append("inventory_id must match the seeded inventory")
    roles = payload.get("component_roles")
    if not isinstance(roles, list) or not roles or not all(
        isinstance(role, str) and role.strip() for role in roles
    ):
        errors.append("component_roles must be a non-empty string array")
    elif roles != expected_roles:
        errors.append("component_roles must match the seeded inventory")
    if payload.get("observed_reads") != []:
        errors.append("agent sidecar observed_reads must remain empty")
    if payload.get("validator_findings") != []:
        errors.append("agent sidecar validator_findings must remain empty")
    top_level_valid = not errors

    raw_surfaces = payload.get("surfaces")
    surfaces = _dict_list(raw_surfaces)
    if not isinstance(raw_surfaces, list):
        errors.append("surfaces must be an array")
    elif len(surfaces) != len(raw_surfaces):
        errors.append("all surface records must be objects")
    identifiers = [str(surface.get("id", "")) for surface in surfaces]
    duplicates = sorted(
        identifier
        for identifier, count in Counter(identifiers).items()
        if identifier and count > 1
    )
    if duplicates:
        errors.append("duplicate surface IDs: " + ", ".join(duplicates))

    returned_ids = set(identifiers)
    missing_ids = sorted(seeded_ids - returned_ids)
    if missing_ids:
        errors.append("missing seeded surface IDs: " + ", ".join(missing_ids))

    observation_available = observed_reads is not None
    observed = _normalize_observed_reads(observed_reads or [])
    promoted = _load_document(promoted_document)
    candidate = _load_document(candidate_document)
    resolved_source_root = Path(source_root).resolve() if source_root else None
    valid_by_id: dict[str, dict[str, object]] = {}
    for index, surface in enumerate(surfaces):
        surface_id = str(surface.get("id", ""))
        prefix = f"surface[{index}] {surface_id or '<missing-id>'}"
        seeded = seeded_by_id.get(surface_id)
        record_errors = _surface_record_errors(
            surface,
            analyzer_document=analyzer_document,
            source_root=resolved_source_root,
            observed_reads=observed,
        )
        if seeded is not None:
            record_errors.extend(_seeded_surface_mutation_errors(seeded, surface))
        errors.extend(f"{prefix}: {message}" for message in record_errors)
        if record_errors or not top_level_valid or identifiers.count(surface_id) != 1:
            if surface_id in seeded_ids:
                _finding(
                    findings,
                    "unverifiable_coverage_claim",
                    surface_id,
                    "seeded surface record failed coverage-contract validation",
                )
            continue
        valid_by_id[surface_id] = surface

    for surface_id in missing_ids:
        _finding(
            findings,
            "unverifiable_coverage_claim",
            surface_id,
            "seeded surface coverage record is missing",
        )

    accounted_surfaces: list[dict[str, object]] = []
    for surface_id, seeded in seeded_by_id.items():
        accounted_surfaces.append(
            copy.deepcopy(valid_by_id.get(surface_id, seeded))
        )
    accounted_surfaces.extend(
        copy.deepcopy(surface)
        for surface_id, surface in valid_by_id.items()
        if surface_id not in seeded_ids
    )

    for surface in accounted_surfaces:
        surface_id = str(surface["id"])
        disposition = str(surface["disposition"])
        evidence_status = str(surface["evidence_status"])
        evidence = _dict_list(surface.get("evidence"))
        document_reference = surface.get("document_reference")
        verified_evidence = _verified_evidence_references(
            evidence,
            analyzer_document=analyzer_document,
            source_root=resolved_source_root,
            observed_reads=observed,
        )

        if disposition == "documented":
            if not verified_evidence:
                _finding(
                    findings,
                    "unverifiable_coverage_claim",
                    surface_id,
                    "documented disposition lacks independently verifiable evidence",
                )
            final_present = _document_reference_present(
                promoted, document_reference
            )
            if not final_present:
                if _document_reference_present(candidate, document_reference):
                    _finding(
                        findings,
                        "merge_loss",
                        surface_id,
                        "candidate fact is absent from the promoted document",
                    )
                else:
                    _finding(
                        findings,
                        "unverifiable_coverage_claim",
                        surface_id,
                        "document reference is absent from the promoted document",
                    )
        elif disposition == "not-applicable":
            applicability = surface.get("applicability")
            applicability_evidence = (
                applicability.get("evidence", [])
                if isinstance(applicability, dict)
                else []
            )
            if not set(applicability_evidence).issubset(verified_evidence):
                _finding(
                    findings,
                    "unverifiable_coverage_claim",
                    surface_id,
                    "not-applicable disposition relies on unverified "
                    "applicability evidence",
                )
        elif evidence_status == "available":
            _finding(
                findings,
                "synthesis_omission",
                surface_id,
                "available evidence was not represented in the promoted document",
            )
        elif evidence_status == "unavailable":
            _finding(
                findings,
                "extraction_gap",
                surface_id,
                "required evidence was unavailable to synthesis",
            )
        elif not _surface_was_inspected(surface, observed):
            _finding(
                findings,
                "inspection_gap",
                surface_id,
                (
                    "candidate inspection cannot be verified because source-read "
                    "observation is unavailable"
                    if not observation_available
                    else "candidate evidence locations were not inspected"
                ),
            )

    counts = _summary(accounted_surfaces, seeded_count=len(seeded_ids))
    unresolved_safety = sorted(
        surface_id
        for surface_id in SAFETY_CRITICAL_SURFACES
        if any(
            str(surface.get("id", "")) == surface_id
            and surface.get("disposition") == "unresolved"
            for surface in accounted_surfaces
        )
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "component": expected_component,
        "inventory_id": inventory.get("inventory_id"),
        "structural_valid": not errors,
        "structural_errors": errors,
        "coverage_accounting": {
            "seeded": len(seeded_ids),
            "returned": len(returned_ids & seeded_ids),
            "valid": len(set(valid_by_id) & seeded_ids),
            "missing": missing_ids,
            "duplicates": duplicates,
        },
        "summary": counts,
        "accounted_surfaces": accounted_surfaces,
        "unresolved_safety_critical_surfaces": unresolved_safety,
        "observed_reads": observed,
        "read_observation": {
            "status": "available" if observation_available else "unavailable",
            "source": "harness-telemetry" if observation_available else None,
        },
        "validator_findings": findings,
        "warning_count": len(findings) + len(errors),
        "status": "pass" if not findings and not errors else "warning",
    }


def finalized_sidecar(
    sidecar: dict[str, object] | None,
    report: dict[str, object],
    *,
    inventory: dict[str, object] | None = None,
) -> dict[str, object]:
    """Return a sidecar with orchestrator-owned observations and findings."""

    payload = dict(sidecar or inventory or {})
    if inventory is not None:
        for field in (
            "schema_version",
            "component",
            "inventory_id",
            "component_roles",
        ):
            payload[field] = copy.deepcopy(inventory.get(field))
    payload["surfaces"] = report["accounted_surfaces"]
    payload["observed_reads"] = report["observed_reads"]
    payload["read_observation"] = report["read_observation"]
    payload["validator_findings"] = report["validator_findings"]
    payload["summary"] = report["summary"]
    payload["validation"] = {
        "structural_valid": report["structural_valid"],
        "structural_errors": report["structural_errors"],
        "coverage_accounting": report["coverage_accounting"],
        "unresolved_safety_critical_surfaces": report[
            "unresolved_safety_critical_surfaces"
        ],
        "status": report["status"],
    }
    return payload


def load_sidecar(path: str | Path) -> dict[str, object] | None:
    """Load a JSON sidecar, returning ``None`` for absent or invalid JSON."""

    try:
        payload = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _component_roles(analyzer: dict[str, object]) -> list[str]:
    serialized = json.dumps(
        {
            "entrypoints": analyzer.get("entrypoints", []),
            "source_components": analyzer.get("source_components", []),
            "behavioral_evidence": analyzer.get("behavioral_evidence", []),
        }
    ).casefold()
    roles: list[str] = []
    if (
        "operator" in serialized
        or "controller-runtime" in serialized
        or bool(_dict_list(analyzer.get("controller_watches")))
        or bool(_dict_list(analyzer.get("crds")))
    ):
        roles.append("operator")
    if (
        bool(_dict_list(analyzer.get("http_endpoints")))
        or bool(_dict_list(analyzer.get("grpc_services")))
        or "service" in serialized
    ):
        roles.append("service")
    if (
        bool(_dict_list(analyzer.get("deployments")))
        or bool(_dict_list(analyzer.get("services")))
        or bool(_dict_list(analyzer.get("ingress_routing")))
    ) and not roles:
        roles.append("manifest")
    return roles or ["unknown"]


def _category_coverage(
    analyzer: dict[str, object], category: str
) -> dict[str, object] | None:
    coverage = analyzer.get("category_coverage")
    if not isinstance(coverage, dict):
        return None
    record = coverage.get(category)
    return record if isinstance(record, dict) else None


def _surface(
    *,
    surface_id: str,
    parent_category: str,
    component_role: str,
    question: str,
    priority: str,
    basis: str,
    candidates: list[dict[str, str]],
) -> dict[str, object]:
    return {
        "id": surface_id,
        "parent_category": parent_category,
        "component_role": component_role,
        "applicability": {
            "status": "applicable" if candidates else "uncertain",
            "basis": basis,
            "evidence": [],
        },
        "question": question,
        "priority": priority,
        "candidate_locations": candidates[:8],
        "evidence_status": "unresolved",
        "claim_support": "uncertain",
        "disposition": "unresolved",
        "evidence": [],
        "document_reference": None,
        "reason": "Pending evidence-to-output review.",
        "remaining_question": question,
    }


def _dict_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _source_locations(
    value: object,
    *,
    keywords: tuple[str, ...] = (),
) -> list[dict[str, str]]:
    locations: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def visit(item: object) -> None:
        if isinstance(item, dict):
            serialized = json.dumps(item, sort_keys=True).casefold()
            matches = not keywords or any(word in serialized for word in keywords)
            source = item.get("source")
            if matches and isinstance(source, str):
                location = _candidate_location(source)
                key = (
                    location.get("path", location.get("path_pattern", "")),
                    location.get("line_range", ""),
                )
                if key[0] and key not in seen:
                    seen.add(key)
                    locations.append(location)
            for nested in item.values():
                visit(nested)
        elif isinstance(item, list):
            for nested in item:
                visit(nested)

    visit(value)
    return locations


def _operator_manager_metrics_sources(
    analyzer: dict[str, object],
) -> list[dict[str, str]]:
    """Return metrics evidence tied to the operator manager serving surface."""

    records: list[dict[str, object]] = []
    behaviors = sorted(
        _dict_list(analyzer.get("behavioral_evidence")),
        key=lambda behavior: (
            behavior.get("status") != "observed",
            str(behavior.get("source", "")),
        ),
    )
    for behavior in behaviors:
        if (
            behavior.get("kind") == "conditional-metrics-enforcement"
            and behavior.get("identity") == "controller-runtime metrics"
        ):
            records.append(behavior)
    for service in _dict_list(analyzer.get("services")):
        serialized = json.dumps(service, sort_keys=True).casefold()
        source = str(service.get("source", "")).casefold()
        if (
            "metric" in serialized
            and any(token in serialized for token in ("manager", "operator"))
            and "/gateway/" not in source
            and "auth-proxy" not in serialized
        ):
            records.append(service)
    for deployment in _dict_list(analyzer.get("deployments")):
        serialized = json.dumps(deployment, sort_keys=True).casefold()
        source = str(deployment.get("source", "")).casefold()
        if (
            any(
                token in serialized
                for token in ("--metrics-bind-address", "--metrics-secure")
            )
            and any(token in serialized for token in ("manager", "operator"))
            and "/gateway/" not in source
            and "auth-proxy" not in serialized
        ):
            records.append(deployment)
    for authentication in _dict_list(analyzer.get("authentication")):
        serialized = json.dumps(authentication, sort_keys=True).casefold()
        source = str(authentication.get("source", "")).casefold()
        if (
            "metric" in serialized
            and any(token in serialized for token in ("manager", "operator"))
            and "/gateway/" not in source
            and "auth-proxy" not in serialized
        ):
            records.append(authentication)
    return _dedupe_locations(_source_locations(records))


def _candidate_location(reference: str) -> dict[str, str]:
    match = _SOURCE_REF_RE.fullmatch(reference.strip())
    if match:
        return {
            "path": match.group("path"),
            "line_range": match.group("lines"),
            "origin": "analyzer",
        }
    return {"path": reference.strip(), "origin": "analyzer"}


def _dedupe_locations(
    locations: list[dict[str, str]],
) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for location in locations:
        key = (
            location.get("path", location.get("path_pattern", "")),
            location.get("line_range", ""),
        )
        if not key[0] or key in seen:
            continue
        seen.add(key)
        result.append(location)
    return result


def _surface_record_errors(
    surface: dict[str, object],
    *,
    analyzer_document: dict[str, object] | None,
    source_root: Path | None,
    observed_reads: list[dict[str, object]],
) -> list[str]:
    errors: list[str] = []
    surface_id = surface.get("id")
    if not isinstance(surface_id, str) or not _SURFACE_ID_RE.fullmatch(surface_id):
        errors.append("id must be a stable dotted lowercase identifier")
    for field in ("parent_category", "component_role", "question"):
        if not isinstance(surface.get(field), str) or not str(
            surface.get(field)
        ).strip():
            errors.append(f"{field} must be a non-empty string")
    if not isinstance(surface.get("reason"), str) or not str(
        surface.get("reason")
    ).strip():
        errors.append("reason must be a non-empty string")
    if surface.get("priority") not in PRIORITIES:
        errors.append("priority is invalid")
    if surface.get("disposition") not in DISPOSITIONS:
        errors.append("disposition is invalid")
    if surface.get("evidence_status") not in EVIDENCE_STATUSES:
        errors.append("evidence_status is invalid")
    if surface.get("claim_support") not in CLAIM_SUPPORT_STATUSES:
        errors.append("claim_support is invalid")
    applicability = surface.get("applicability")
    if not isinstance(applicability, dict):
        errors.append("applicability must be an object")
    else:
        if applicability.get("status") not in APPLICABILITY_STATUSES:
            errors.append("applicability status is invalid")
        if not isinstance(applicability.get("basis"), str) or not str(
            applicability.get("basis")
        ).strip():
            errors.append("applicability basis must be a non-empty string")
    locations = surface.get("candidate_locations")
    if not isinstance(locations, list):
        errors.append("candidate_locations must be an array")
    else:
        for location in locations:
            errors.extend(_candidate_location_errors(location))
    evidence = surface.get("evidence")
    if not isinstance(evidence, list):
        errors.append("evidence must be an array")
    else:
        for item in evidence:
            errors.extend(
                _evidence_item_errors(
                    item,
                    analyzer_document=analyzer_document,
                    source_root=source_root,
                )
            )
    disposition = surface.get("disposition")
    evidence_status = surface.get("evidence_status")
    claim_support = surface.get("claim_support")
    if evidence_status == "available" and not evidence:
        errors.append("available evidence status requires evidence")
    if evidence_status != "available" and claim_support != "uncertain":
        errors.append(
            "supported or unsupported claim status requires available evidence"
        )
    if claim_support in {"supported", "unsupported"} and not evidence:
        errors.append("claim support requires evidence")
    if disposition == "documented":
        if evidence_status != "available" or claim_support != "supported":
            errors.append(
                "documented surfaces require available, supported evidence"
            )
        verified = _verified_evidence_references(
            _dict_list(evidence),
            analyzer_document=analyzer_document,
            source_root=source_root,
            observed_reads=observed_reads,
        )
        if not verified:
            errors.append(
                "documented surfaces require independently verified evidence"
            )
        reference = surface.get("document_reference")
        if not isinstance(reference, dict):
            errors.append("documented surfaces require document_reference")
        else:
            errors.extend(_document_reference_errors(reference))
    if disposition == "unresolved" and (
        not isinstance(surface.get("remaining_question"), str)
        or not str(surface.get("remaining_question")).strip()
    ):
        errors.append("unresolved surfaces require remaining_question")
    if disposition == "not-applicable" and isinstance(applicability, dict):
        applicability_evidence = applicability.get("evidence")
        if not isinstance(applicability_evidence, list) or not applicability_evidence:
            errors.append(
                "not-applicable surfaces require applicability evidence"
            )
        elif not all(
            isinstance(reference, str) and reference.strip()
            for reference in applicability_evidence
        ):
            errors.append("applicability evidence entries must be references")
        else:
            top_level_references = {
                str(item.get("reference"))
                for item in _dict_list(evidence)
                if isinstance(item.get("reference"), str)
            }
            missing = sorted(set(applicability_evidence) - top_level_references)
            if missing:
                errors.append(
                    "applicability evidence must reference top-level evidence: "
                    + ", ".join(missing)
                )
        if evidence_status != "available" or claim_support != "supported":
            errors.append(
                "not-applicable surfaces require available, supported evidence"
            )
        verified = _verified_evidence_references(
            _dict_list(evidence),
            analyzer_document=analyzer_document,
            source_root=source_root,
            observed_reads=observed_reads,
        )
        if not isinstance(applicability_evidence, list) or not set(
            applicability_evidence
        ).issubset(verified):
            errors.append(
                "not-applicable applicability requires independently verified evidence"
            )
    return errors


def _seeded_surface_mutation_errors(
    seeded: dict[str, object], returned: dict[str, object]
) -> list[str]:
    errors: list[str] = []
    for field in (
        "parent_category",
        "component_role",
        "question",
        "priority",
        "candidate_locations",
    ):
        if returned.get(field) != seeded.get(field):
            errors.append(f"seeded {field} is immutable")
    seeded_applicability = seeded.get("applicability")
    returned_applicability = returned.get("applicability")
    if (
        isinstance(seeded_applicability, dict)
        and isinstance(returned_applicability, dict)
        and returned_applicability.get("basis")
        != seeded_applicability.get("basis")
    ):
        errors.append("seeded applicability basis is immutable")
    return errors


def _evidence_item_errors(
    item: object,
    *,
    analyzer_document: dict[str, object] | None,
    source_root: Path | None,
) -> list[str]:
    if not isinstance(item, dict) or item.get("kind") not in EVIDENCE_KINDS:
        return ["evidence items require a recognized kind"]
    reference = item.get("reference")
    if not isinstance(reference, str) or not reference.strip():
        return ["evidence items require a reference"]
    reference = reference.strip()
    if item.get("kind") == "analyzer-fact":
        if not reference.startswith("component-architecture.json#/"):
            return ["analyzer evidence requires an exact component JSON pointer"]
        pointer = reference.removeprefix("component-architecture.json#")
        if re.search(r"~(?![01])", pointer):
            return ["analyzer evidence JSON pointer has an invalid escape"]
        if analyzer_document is not None and not _json_pointer_exists(
            analyzer_document, pointer
        ):
            return ["analyzer evidence JSON pointer does not exist"]
        return []
    match = _SOURCE_REF_RE.fullmatch(reference)
    if match is None:
        return ["source evidence requires a numeric path reference"]
    path_errors = _repository_relative_path_errors(match.group("path"))
    if path_errors:
        return [f"source evidence {message}" for message in path_errors]
    bounds = [int(value) for value in match.group("lines").split("-")]
    if bounds[0] <= 0 or (len(bounds) == 2 and bounds[0] > bounds[1]):
        return ["source evidence line range is invalid"]
    if source_root is not None:
        source_path = (source_root / match.group("path")).resolve()
        if source_root != source_path and source_root not in source_path.parents:
            return ["source evidence path escapes the repository"]
        if not source_path.is_file():
            return ["source evidence path does not exist"]
        last = bounds[-1]
        try:
            line_count = sum(
                1 for _ in source_path.open(encoding="utf-8", errors="ignore")
            )
        except OSError:
            return ["source evidence path cannot be read"]
        if last > line_count:
            return ["source evidence line range exceeds the file"]
    return []


def _verified_evidence_references(
    evidence: list[dict[str, object]],
    *,
    analyzer_document: dict[str, object] | None,
    source_root: Path | None,
    observed_reads: list[dict[str, object]],
) -> set[str]:
    verified: set[str] = set()
    for item in evidence:
        if _evidence_item_errors(
            item,
            analyzer_document=analyzer_document,
            source_root=source_root,
        ):
            continue
        kind = item.get("kind")
        reference = str(item.get("reference", ""))
        if kind == "analyzer-fact":
            if analyzer_document is not None and _json_pointer_exists(
                analyzer_document,
                reference.removeprefix("component-architecture.json#"),
            ):
                verified.add(reference)
        elif kind == "source-read":
            if _source_reference_was_observed(reference, observed_reads):
                verified.add(reference)
        elif kind == "manifest":
            if source_root is not None:
                verified.add(reference)
        elif kind == "source-candidate":
            # A candidate nominates inspection work. It never proves a claim.
            continue
    return verified


def _json_pointer_exists(document: object, pointer: str) -> bool:
    if not pointer.startswith("/"):
        return False
    current = document
    for raw_part in pointer[1:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
        else:
            return False
    return True


def _repository_relative_path_errors(path: str) -> list[str]:
    normalized = path.replace("\\", "/")
    if not normalized or normalized.startswith("/") or ".." in Path(normalized).parts:
        return ["path must be repository-relative"]
    return []


def _candidate_location_errors(location: object) -> list[str]:
    if not isinstance(location, dict):
        return ["candidate locations must be objects"]
    path = location.get("path")
    pattern = location.get("path_pattern")
    if bool(path) == bool(pattern):
        return ["candidate location requires exactly one path or path_pattern"]
    selected = path or pattern
    if not isinstance(selected, str) or not selected.strip():
        return ["candidate location path must be a non-empty string"]
    normalized = selected.replace("\\", "/")
    if normalized.startswith("/") or ".." in Path(normalized).parts:
        return ["candidate location path must be repository-relative"]
    line_range = location.get("line_range")
    if line_range is not None and not re.fullmatch(
        r"\d+(?:-\d+)?", str(line_range)
    ):
        return ["candidate location line_range must be numeric"]
    return []


def _document_reference_errors(reference: dict[str, object]) -> list[str]:
    kind = reference.get("kind")
    if kind == "table-row":
        if not isinstance(reference.get("category"), str) or not str(
            reference.get("category")
        ).strip():
            return ["table document reference requires category"]
        row_key = reference.get("row_key")
        if not isinstance(row_key, list) or not row_key or not all(
            isinstance(value, str) and value.strip() for value in row_key
        ):
            return ["table document reference requires a non-empty row_key"]
        expected_cells = reference.get("expected_cells")
        if (
            not isinstance(expected_cells, dict)
            or not expected_cells
            or not all(
                isinstance(column, str)
                and column.strip()
                and isinstance(value, str)
                and value.strip()
                for column, value in expected_cells.items()
            )
        ):
            return [
                "table document reference requires non-empty expected_cells"
            ]
        category = str(reference.get("category"))
        spec = next(
            (candidate for candidate in _TABLE_SPECS if candidate.category == category),
            None,
        )
        if spec is None:
            return ["table document reference category is unknown"]
        unknown_columns = sorted(set(expected_cells) - set(spec.columns))
        if unknown_columns:
            return [
                "table document reference has unknown expected columns: "
                + ", ".join(unknown_columns)
            ]
        if not (set(expected_cells) - set(spec.keys)):
            return [
                "table document reference must identify at least one non-key cell"
            ]
        return []
    if kind == "section":
        if not isinstance(reference.get("section"), str) or not str(
            reference.get("section")
        ).strip():
            return ["section document reference requires section"]
        if not isinstance(reference.get("fact_identity"), str) or not str(
            reference.get("fact_identity")
        ).strip():
            return ["section document reference requires fact_identity"]
        return []
    return ["document_reference kind must be table-row or section"]


def _load_document(path: str | Path | None):
    if path is None:
        return None
    try:
        return parse_component_markdown(Path(path))
    except OSError:
        return None


def _document_reference_present(document, reference: object) -> bool:
    if document is None or not isinstance(reference, dict):
        return False
    kind = reference.get("kind")
    if kind == "table-row":
        category = reference.get("category")
        row_key = reference.get("row_key")
        if not isinstance(category, str) or not isinstance(row_key, list):
            return False
        spec = next(
            (candidate for candidate in _TABLE_SPECS if candidate.category == category),
            None,
        )
        if spec is None or len(row_key) != len(spec.keys):
            return False
        normalized_key = tuple(
            _normalize_key_value(category, column, str(value))
            for column, value in zip(spec.keys, row_key, strict=True)
        )
        tables = _tables_by_category(document.tables)
        row = _canonical_rows(tables.get(category, ()), spec).get(normalized_key)
        expected_cells = reference.get("expected_cells")
        if row is None or not isinstance(expected_cells, dict):
            return False
        return all(
            column in row
            and _normalize_text(row[column]) == _normalize_text(str(value))
            for column, value in expected_cells.items()
        )
    if kind == "section":
        section = reference.get("section")
        identity = reference.get("fact_identity")
        if not isinstance(section, str) or not isinstance(identity, str):
            return False
        wanted_section = tuple(
            _normalize_section(part) for part in section.split(">") if part.strip()
        )
        wanted_identity = _normalize_text(identity)
        for path, text in document.section_text.items():
            normalized_path = tuple(_normalize_section(part) for part in path)
            if normalized_path[-len(wanted_section) :] != wanted_section:
                continue
            if wanted_identity in _normalize_text(text):
                return True
        for table in document.tables:
            normalized_path = tuple(
                _normalize_section(part) for part in table.section_path
            )
            if normalized_path[-len(wanted_section) :] != wanted_section:
                continue
            if wanted_identity in _normalize_text(
                " ".join(cell for row in table.rows for cell in row)
            ):
                return True
    return False


def _normalize_observed_reads(
    reads: list[dict[str, object]],
) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for read in reads:
        path = read.get("path")
        if not isinstance(path, str) or not path.strip():
            continue
        normalized.append(
            {
                "path": path.strip().replace("\\", "/"),
                "line_range": str(read.get("line_range", "unknown")),
                "outcome": str(read.get("outcome", "unhelpful")),
            }
        )
    return normalized


def _parse_line_interval(value: object) -> tuple[int, int | None] | None:
    text = str(value).strip()
    bounded = re.fullmatch(r"(\d+)(?:-(\d+))?", text)
    if bounded:
        start = int(bounded.group(1))
        end = int(bounded.group(2) or start)
        if start > 0 and end >= start:
            return start, end
        return None
    open_ended = re.fullmatch(r"(\d+)-unknown", text)
    if open_ended and int(open_ended.group(1)) > 0:
        return int(open_ended.group(1)), None
    return None


def _source_reference_was_observed(
    reference: str,
    observed_reads: list[dict[str, object]],
) -> bool:
    match = _SOURCE_REF_RE.fullmatch(reference)
    if match is None:
        return False
    expected = _parse_line_interval(match.group("lines"))
    if expected is None:
        return False
    expected_start, expected_end = expected
    expected_path = match.group("path").replace("\\", "/")
    for read in observed_reads:
        if read.get("path") != expected_path:
            continue
        observed = _parse_line_interval(read.get("line_range"))
        if observed is None:
            continue
        observed_start, observed_end = observed
        if observed_start <= expected_start and (
            observed_end is None or observed_end >= expected_end
        ):
            return True
    return False


def _surface_was_inspected(
    surface: dict[str, object], observed_reads: list[dict[str, object]]
) -> bool:
    for location in _dict_list(surface.get("candidate_locations")):
        path = location.get("path")
        pattern = location.get("path_pattern")
        candidate_interval = _parse_line_interval(location.get("line_range"))
        for read in observed_reads:
            observed_path = str(read.get("path", ""))
            path_matches = isinstance(path, str) and path == observed_path
            pattern_matches = isinstance(pattern, str) and fnmatch.fnmatch(
                observed_path, pattern
            )
            if not path_matches and not pattern_matches:
                continue
            observed_interval = _parse_line_interval(read.get("line_range"))
            if observed_interval is None:
                continue
            if candidate_interval is None:
                return True
            candidate_start, candidate_end = candidate_interval
            observed_start, observed_end = observed_interval
            if observed_start <= candidate_end and (
                observed_end is None or observed_end >= candidate_start
            ):
                return True
    return False


def _summary(
    surfaces: list[dict[str, object]], *, seeded_count: int | None = None
) -> dict[str, int]:
    counts = Counter(str(surface.get("disposition", "invalid")) for surface in surfaces)
    return {
        "seeded": len(surfaces) if seeded_count is None else seeded_count,
        "documented": counts["documented"],
        "unresolved": counts["unresolved"],
        "not_applicable": counts["not-applicable"],
    }


def _finding(
    findings: list[dict[str, str]],
    classification: str,
    surface_id: str,
    message: str,
) -> None:
    findings.append(
        {
            "classification": classification,
            "surface_id": surface_id,
            "message": message,
        }
    )
