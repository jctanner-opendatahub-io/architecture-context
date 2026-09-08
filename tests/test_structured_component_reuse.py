"""Phase-two whole-component reuse gates; all synthesis is test-local."""

from __future__ import annotations

import copy
import json
import os
import shlex
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures" / "structured_component"
sys.path.insert(0, str(ROOT))

from lib import agent_runner, codex_agent, structured_component_reuse  # noqa: E402
from lib.structured_component_reuse import (  # noqa: E402
    AcceptedSnapshot,
    ComponentIdentity,
    DependencyRecord,
    ProducerCompatibility,
    ReuseConfigurationError,
    ReuseRecordError,
    ReuseTarget,
    RevalidationResult,
    SourceRunState,
    TargetNormalization,
    _porcelain_v1_z_paths,
    build_input_identities,
    capture_producer_build_identity,
    capture_source_snapshot,
    content_hash,
    decide_reuse,
    dependency_record_from_telemetry,
    render_resolution,
    resolve_or_synthesize,
    resolve_predecessor,
    search_observation_key,
    select_predecessor_snapshot,
    thaw,
)


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _repository(tmp_path: Path, name: str = "repository") -> Path:
    root = tmp_path / name
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "fixture@example.com")
    _git(root, "config", "user.name", "Fixture")
    (root / "source.go").write_text("package source\n\nconst Enabled = true\n")
    (root / "config.yaml").write_text("permission: read\ncondition: enabled\n")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "initial")
    return root


def _rg_item(
    root: Path,
    command: str,
    *,
    identifier: str = "rg-search",
    env: dict[str, str] | None = None,
) -> dict:
    completed = subprocess.run(
        shlex.split(command),
        cwd=root,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode in {0, 1}
    assert completed.stderr == ""
    return {
        "type": "commandExecution",
        "id": identifier,
        "cwd": str(root),
        "exit_code": completed.returncode,
        "command": command,
        "aggregated_output": completed.stdout,
        "command_actions": [{"type": "search", "command": command}],
    }


def _search_dependencies(
    root: Path,
    telemetry: dict,
    *,
    replay_mode: str = "verify-observation",
) -> DependencyRecord:
    observed = telemetry["dependency_observations"]["searches"][0]
    key = search_observation_key(
        root=Path(observed["resolved_root"]).relative_to(root).as_posix(),
        pattern=observed["pattern"],
        options=observed["options"],
        tool=observed["tool"],
    )
    return dependency_record_from_telemetry(
        telemetry,
        checkout_root=root,
        justifications={},
        search_justifications={key: "independently replayed bounded rg search"},
        search_replay_mode=replay_mode,
    )


def _target_with_dependencies(
    prior: AcceptedSnapshot,
    root: Path,
    dependencies: DependencyRecord,
) -> ReuseTarget:
    state = capture_source_snapshot(root)
    source_state = SourceRunState(state, state)
    analyzer = _analyzer(root)
    return ReuseTarget(
        "rhoai-target",
        prior.identity,
        _inputs(root, dependencies, analyzer=analyzer),
        prior.compatibility,
        dependencies,
        source_state,
        _target_normalization_from_prior(
            prior,
            platform="rhoai-target",
            source_state=source_state,
            analyzer=analyzer,
        ),
    )


def _telemetry(
    root: Path,
    *,
    searches: list[dict] | None = None,
    complete: bool = True,
    unclassified: list[str] | None = None,
) -> dict:
    return {
        "harness": "codex",
        "dependency_observations": {
            "schema_version": "structured-component-dependency-observations/v1",
            "harness": "codex",
            "complete": complete,
            "reads": [
                {
                    "path": "config.yaml",
                    "offset": 1,
                    "limit": 20,
                    "outcome": "successful-sdk-read-action",
                }
            ],
            "searches": searches or [],
            "unclassified_source_commands": unclassified or [],
        },
    }


def _dependencies(
    root: Path,
    *,
    searches: list[dict] | None = None,
    complete: bool = True,
    unclassified: list[str] | None = None,
    supplied_reads: tuple[str, ...] = (),
    justifications: dict[str, str] | None = None,
    accounted_untracked: tuple[str, ...] = (),
    generated_inputs: tuple[Path, ...] = (),
    external_inputs: tuple[Path, ...] = (),
) -> DependencyRecord:
    reasons = {"config.yaml": "configuration supplied to synthesis"}
    reasons.update(justifications or {})
    search_reasons = {}
    for search in searches or []:
        relative = Path(search["resolved_root"]).resolve().relative_to(root).as_posix()
        search_reasons[
            search_observation_key(
                root=relative,
                pattern=search["pattern"],
                options=search["options"],
                tool=search["tool"],
            )
        ] = "bounded search used to establish positive or negative evidence"
    return dependency_record_from_telemetry(
        _telemetry(
            root,
            searches=searches,
            complete=complete,
            unclassified=unclassified,
        ),
        checkout_root=root,
        justifications=reasons,
        search_justifications=search_reasons,
        supplied_reads=supplied_reads,
        accounted_untracked=accounted_untracked,
        generated_inputs=generated_inputs,
        external_inputs=external_inputs,
    )


def _analyzer(root: Path) -> dict:
    data = json.loads((FIXTURES / "analyzer-rbac-praxis.json").read_text())
    data["commit_sha"] = _git(root, "rev-parse", "HEAD")
    data["extracted_at"] = "2026-09-07T12:00:00Z"
    data["scan_statistics"] = [
        {
            "category": "internal_dependencies",
            "metric": "files_scanned",
            "value": 2,
            "unit": "files",
            "scope": "fixture",
        }
    ]
    return data


def _compatibility(**changes: str) -> ProducerCompatibility:
    values = {
        "analyzer_schema_version": "1",
        "analyzer_version": "0.1.0-dev",
        "analyzer_build_identity": "sha256:exact-extractor-source",
        "normalizer_version": "structured-component-normalizer/v1",
        "synthesis_contract_version": "structured-component-synthesis/v1",
    }
    values.update(changes)
    return ProducerCompatibility(**values)


def _normalize_phase_one_document(
    analyzer_path: Path,
    output: Path,
    *,
    version_scope: str,
    extra_args: tuple[str, ...] = (),
) -> dict:
    env = os.environ.copy()
    env["GOCACHE"] = "/tmp/structured-component-go-cache"
    subprocess.run(
        [
            "go",
            "run",
            ".",
            "normalize",
            "--input",
            str(analyzer_path),
            "--component-map",
            str(FIXTURES / "component-map-praxis.json"),
            "--component-map-id",
            "reuse-phase-one-fixture",
            "--version-scope",
            version_scope,
            "--output",
            str(output),
            *extra_args,
        ],
        cwd=ROOT / "src" / "arch-analyzer",
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(output.read_text())


def _retarget_source_provenance(
    document: dict, *, platform: str, revision: str
) -> dict:
    result = copy.deepcopy(document)
    result["identity"]["version_scope"] = platform
    result["identity"]["source_revision"] = revision
    for fact in result["facts"]:
        for evidence in fact["evidence"]:
            evidence["revision"] = revision
    for disposition in result["proposal_dispositions"]:
        for evidence in disposition["evidence"]:
            evidence["revision"] = revision
    result["rendering_view"]["metadata"]["version"] = revision
    return result


def _bind_document_to_analyzer(document: dict, analyzer: dict) -> dict:
    result = copy.deepcopy(document)
    result["analyzer_input"] = {
        "schema_version": analyzer["schema_version"],
        "bundle_fingerprint": (
            structured_component_reuse._analyzer_bundle_fingerprint(analyzer)
        ),
        "extracted_at": analyzer["extracted_at"],
    }
    result["producers"]["analyzer_version"] = analyzer["analyzer_version"]
    return result


def _target_normalization_from_prior(
    prior: AcceptedSnapshot,
    *,
    platform: str,
    source_state: SourceRunState,
    analyzer: dict,
) -> TargetNormalization:
    document = _retarget_source_provenance(
        thaw(prior.document),
        platform=platform,
        revision=source_state.end.head,
    )
    document = _bind_document_to_analyzer(document, analyzer)
    return TargetNormalization.capture(document)


def _go_revalidation(document: dict, directory: Path, name: str) -> RevalidationResult:
    document_path = directory / f"{name}.json"
    rendered_path = directory / f"{name}.md"
    document_path.write_text(json.dumps(document))
    completed = subprocess.run(
        [
            "go",
            "run",
            ".",
            "render-document",
            "--input",
            str(document_path),
            "--output",
            str(rendered_path),
        ],
        cwd=ROOT / "src" / "arch-analyzer",
        env={**os.environ, "GOCACHE": "/tmp/structured-component-go-cache"},
        check=False,
        capture_output=True,
        text=True,
    )
    valid = completed.returncode == 0
    return RevalidationResult(
        document=document,
        checks={
            key: valid
            for key in (
                "document_schema",
                "typed_references",
                "patch_policy",
                "current_acceptance_rules",
            )
        },
        details=(completed.stderr.strip(),) if completed.stderr.strip() else (),
    )


def _inputs(
    root: Path,
    dependencies: DependencyRecord,
    *,
    analyzer: dict | None = None,
    configuration: dict | None = None,
    overlays: list | None = None,
    contracts: dict | None = None,
    settings: dict | None = None,
):
    return build_input_identities(
        analyzer_input=analyzer or _analyzer(root),
        component_configuration=configuration
        or {
            "branch": "release-1",
            "exclude_files": ["vendor/**"],
        },
        overlays=overlays or [{"id": "human-correction", "operations": []}],
        contracts=contracts
        or {
            "patch": {"schema_version": "1.0.0"},
            "policy": {"schema_version": "1.0.0"},
        },
        settings=settings
        or {
            "model": "offline-fixture",
            "permissions": ["read"],
            "conditions": ["bounded", "no-tools"],
            "model_context": {
                "adapter": "fixture",
                "requested_model": "offline-fixture",
                "requested_settings": {},
            },
        },
        dependencies=dependencies,
        checkout_root=root,
    )


@pytest.fixture(scope="module")
def accepted_document(tmp_path_factory: pytest.TempPathFactory) -> dict:
    """Normalize the independently accepted Phase 1 fixtures with its CLI."""

    output = tmp_path_factory.mktemp("reuse-accepted") / "document.json"
    return _normalize_phase_one_document(
        FIXTURES / "analyzer-rbac-praxis.json",
        output,
        version_scope="rhoai-previous",
    )


def _snapshot_and_target(
    root: Path,
    accepted_document: dict,
    *,
    dependencies: DependencyRecord | None = None,
    analyzer: dict | None = None,
    configuration: dict | None = None,
    overlays: list | None = None,
    contracts: dict | None = None,
    settings: dict | None = None,
    compatibility: ProducerCompatibility | None = None,
    source_state: SourceRunState | None = None,
) -> tuple[AcceptedSnapshot, ReuseTarget]:
    fixture = json.loads((FIXTURES / "reuse-snapshot-test-only.json").read_text())
    synthesis = (FIXTURES / fixture["synthesis_fixture"]).read_bytes()
    dependencies = dependencies or _dependencies(root)
    analyzer_data = analyzer or _analyzer(root)
    inputs = _inputs(
        root,
        dependencies,
        analyzer=analyzer_data,
        configuration=configuration,
        overlays=overlays,
        contracts=contracts,
        settings=settings,
    )
    snapshot_state = capture_source_snapshot(root)
    run_state = source_state or SourceRunState(snapshot_state, snapshot_state)
    identity = ComponentIdentity(
        fixture["component"], fixture["repository"], tuple(fixture["aliases"])
    )
    compat = compatibility or _compatibility()
    bound_document = _retarget_source_provenance(
        accepted_document,
        platform=fixture["platform"],
        revision=run_state.end.head,
    )
    bound_document = _bind_document_to_analyzer(bound_document, analyzer_data)
    snapshot = AcceptedSnapshot(
        snapshot_id=fixture["snapshot_id"],
        platform=fixture["platform"],
        identity=identity,
        accepted=fixture["accepted"],
        route=fixture["route"],
        inputs=inputs,
        compatibility=compat,
        dependencies=dependencies,
        source_state=run_state,
        synthesis_bytes=synthesis,
        synthesis_integrity=content_hash(synthesis),
        response_identity=fixture["response_identity"],
        document=bound_document,
        document_integrity=content_hash(bound_document),
    )
    target = ReuseTarget(
        platform="rhoai-target",
        identity=identity,
        inputs=inputs,
        compatibility=compat,
        dependencies=dependencies,
        source_state=run_state,
        normalization=_target_normalization_from_prior(
            snapshot,
            platform="rhoai-target",
            source_state=run_state,
            analyzer=analyzer_data,
        ),
    )
    return snapshot, target


def _valid_revalidation(prior: AcceptedSnapshot, target: ReuseTarget):
    assert target.normalization is not None
    document = thaw(target.normalization.document)
    return RevalidationResult(
        document=document,
        checks={
            "document_schema": True,
            "typed_references": True,
            "patch_policy": True,
            "current_acceptance_rules": True,
        },
    )


def test_unchanged_source_is_zero_call_hit(tmp_path, accepted_document):
    root = _repository(tmp_path)
    prior, target = _snapshot_and_target(root, accepted_document)
    calls = []

    result = resolve_or_synthesize(
        prior,
        target,
        revalidate=lambda snapshot, current: _go_revalidation(
            _valid_revalidation(snapshot, current).document,
            tmp_path,
            "valid-returned-document",
        ),
        synthesize=lambda item: calls.append(item),
    )

    assert result.reused is True
    assert calls == []
    assert result.response_identity == prior.response_identity
    assert result.synthesis_bytes == prior.synthesis_bytes
    assert result.provenance["prior_snapshot_id"] == prior.snapshot_id
    assert result.provenance["target_component"] == target.identity.component
    assert result.provenance["target_repository"] == target.identity.repository
    with pytest.raises(TypeError):
        prior.document["component"] = "mutated"
    with pytest.raises(TypeError):
        target.inputs.semantic_payload["settings"] = "mutated"


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (
            lambda envelope: envelope["reuse_eligibility"].update(
                {"available": False, "reason": "producer-unknown"}
            ),
            "producing_envelope_ineligible",
        ),
        (
            lambda envelope: envelope["responses"][0].update(
                {"reported_model": "different-producing-model"}
            ),
            "producing_model_mismatch",
        ),
        (
            lambda envelope: envelope["responses"][0].update(
                {"reported_settings": {"reasoning_effort": "low"}}
            ),
            "producing_settings_mismatch",
        ),
        (
            lambda envelope: envelope["requested"].update(
                {"model": "tampered-request"}
            ),
            "producing_request_binding_mismatch",
        ),
        (
            lambda envelope: envelope["reported"]["settings"].__setitem__(
                0, {"reasoning_effort": "low"}
            ),
            "producing_model_audit_mismatch",
        ),
    ],
)
def test_reuse_decision_rejects_producing_envelope_tampering(
    tmp_path, accepted_document, mutation, reason,
):
    root = _repository(tmp_path)
    prior, target = _snapshot_and_target(root, accepted_document)
    envelope = json.loads(prior.synthesis_bytes)
    mutation(envelope)
    synthesis_bytes = json.dumps(envelope, sort_keys=True).encode()
    prior = replace(
        prior,
        synthesis_bytes=synthesis_bytes,
        synthesis_integrity=content_hash(synthesis_bytes),
    )

    decision = decide_reuse(prior, target)

    assert decision.hit is False
    assert reason in decision.reasons


def test_missing_target_normalization_is_one_explicit_miss(
    tmp_path, accepted_document
):
    root = _repository(tmp_path)
    prior, target = _snapshot_and_target(root, accepted_document)
    target = replace(target, normalization=None)
    validation_calls = []
    synthesis_calls = []

    result = resolve_or_synthesize(
        prior,
        target,
        revalidate=lambda *_: validation_calls.append(True),
        synthesize=lambda item: synthesis_calls.append(item) or {"fresh": True},
    )

    assert result.reused is False
    assert result.decision.reasons == ("target_normalization_missing",)
    assert validation_calls == []
    assert synthesis_calls == [target]


def test_actual_go_validator_cannot_authorize_changed_or_invalid_returned_model(
    tmp_path, accepted_document
):
    root = _repository(tmp_path)
    prior, target = _snapshot_and_target(root, accepted_document)

    changed_analyzer = _analyzer(root)
    changed_analyzer["summary"] = "A different but structurally valid component."
    analyzer_path = tmp_path / "changed-analyzer.json"
    analyzer_path.write_text(json.dumps(changed_analyzer))
    changed_document = _normalize_phase_one_document(
        analyzer_path,
        tmp_path / "changed-document.json",
        version_scope=target.platform,
    )
    changed_document["analyzer_input"] = thaw(prior.document)["analyzer_input"]
    changed_validation = _go_revalidation(
        changed_document,
        tmp_path,
        "validator-valid-semantic-change",
    )
    assert all(changed_validation.checks.values())

    synthesis_calls = []
    changed = resolve_or_synthesize(
        prior,
        target,
        revalidate=lambda *_: changed_validation,
        synthesize=lambda item: synthesis_calls.append(item) or {"fresh": True},
    )
    assert changed.reused is False
    assert changed.decision.reasons == ("revalidated_document_inconsistent",)
    assert changed.decision.comparison["document_consistency_errors"]
    assert changed.decision.comparison["returned_document_integrity"] == content_hash(
        changed_document
    )
    assert len(synthesis_calls) == 1

    invalid_document = _valid_revalidation(prior, target).document
    invalid_document["facts"].pop()
    invalid_validation = _go_revalidation(
        invalid_document,
        tmp_path,
        "validator-invalid-returned-document",
    )
    assert not any(invalid_validation.checks.values())
    assert "fact accounting references missing fact" in invalid_validation.details[0]
    invalid = resolve_or_synthesize(
        prior,
        target,
        revalidate=lambda *_: invalid_validation,
        synthesize=lambda _: {"fresh": True},
    )
    assert invalid.reused is False
    assert "current_revalidation_failed" in invalid.decision.reasons
    assert "revalidated_document_inconsistent" in invalid.decision.reasons

    assert target.normalization is not None
    arbitrary_document = thaw(target.normalization.document)
    arbitrary_document["uncertainty"][0]["detail"] = (
        "Structurally valid but not inherited from the predecessor."
    )
    arbitrary_validation = _go_revalidation(
        arbitrary_document,
        tmp_path,
        "validator-valid-arbitrary-target-claim",
    )
    assert all(arbitrary_validation.checks.values())
    arbitrary_target = replace(
        target,
        normalization=TargetNormalization.capture(arbitrary_document),
    )
    arbitrary_calls = []
    arbitrary = resolve_or_synthesize(
        prior,
        arbitrary_target,
        revalidate=lambda *_: arbitrary_validation,
        synthesize=lambda item: arbitrary_calls.append(item) or {"fresh": True},
    )
    assert arbitrary.reused is False
    assert arbitrary.decision.reasons == (
        "target_normalization_content_mismatch",
    )
    assert arbitrary.decision.comparison[
        "target_normalization_content_errors"
    ] == ("target_normalization_content_mismatch",)
    assert arbitrary_calls == [arbitrary_target]


def test_real_target_normalization_preserves_allowed_typed_patch_policy(
    tmp_path, accepted_document
):
    root = _repository(tmp_path)
    dependencies = _dependencies(root)

    def normalized_with_patch(analyzer: dict, scope: str, label: str) -> dict:
        analyzer_path = tmp_path / f"{label}-analyzer.json"
        analyzer_path.write_text(json.dumps(analyzer))
        base = _normalize_phase_one_document(
            analyzer_path,
            tmp_path / f"{label}-base.json",
            version_scope=scope,
        )
        patch = {
            "schema_version": "1.0.0",
            "patch_id": "reviewed-service-addition",
            "bundle_fingerprint": base["analyzer_input"]["bundle_fingerprint"],
            "operations": [
                {
                    "operation_id": "add-reviewed-service",
                    "action": "add",
                    "fact_type": "service",
                    "value": {
                        "name": "patched-api",
                        "source": "config.yaml:1-2",
                        "type": "ClusterIP",
                        "ports": [],
                        "target_deployment": "patched-api",
                    },
                    "evidence": [
                        {
                            "path": "config.yaml",
                            "start_line": 1,
                            "end_line": 2,
                            "revision": analyzer["commit_sha"],
                        }
                    ],
                    "reason": "Explicitly reviewed source-backed service.",
                }
            ],
        }
        policy = {
            "schema_version": "1.0.0",
            "policy_id": "human-review-policy",
            "patch_id": patch["patch_id"],
            "proposal_fingerprint": content_hash(patch),
            "bundle_fingerprint": patch["bundle_fingerprint"],
            "version_scope": scope,
            "origin": {
                "kind": "model",
                "id": "response:test-only:001",
                "claim_class": "support",
            },
            "authority": {
                "actor": "human-reviewer@example.test",
                "allowed_fact_types": ["service"],
            },
            "decisions": [
                {
                    "decision_id": "decision-1",
                    "operation_id": "add-reviewed-service",
                    "decision": "accept",
                    "decided_by": "human-reviewer@example.test",
                    "reason": "Explicitly reviewed for this analyzer binding.",
                }
            ],
        }
        patch_path = tmp_path / f"{label}-patch.json"
        policy_path = tmp_path / f"{label}-policy.json"
        patch_path.write_text(json.dumps(patch))
        policy_path.write_text(json.dumps(policy))
        return _normalize_phase_one_document(
            analyzer_path,
            tmp_path / f"{label}-accepted.json",
            version_scope=scope,
            extra_args=(
                "--patch",
                str(patch_path),
                "--assembly-policy",
                str(policy_path),
            ),
        )

    prior_analyzer = _analyzer(root)
    prior_document = normalized_with_patch(
        prior_analyzer, "rhoai-previous", "prior-patched"
    )
    prior, _ = _snapshot_and_target(
        root,
        prior_document,
        dependencies=dependencies,
        analyzer=prior_analyzer,
    )

    (root / "irrelevant.txt").write_text("target commit only\n")
    _git(root, "add", "irrelevant.txt")
    _git(root, "commit", "-qm", "target patch refresh")
    target_analyzer = _analyzer(root)
    target_analyzer["extracted_at"] = "2026-09-08T15:00:00Z"
    target_document = normalized_with_patch(
        target_analyzer, "rhoai-target", "target-patched"
    )
    state = capture_source_snapshot(root)
    target = ReuseTarget(
        platform="rhoai-target",
        identity=prior.identity,
        inputs=_inputs(root, dependencies, analyzer=target_analyzer),
        compatibility=prior.compatibility,
        dependencies=dependencies,
        source_state=SourceRunState(state, state),
        normalization=TargetNormalization.capture(target_document),
    )
    synthesis_calls = []

    result = resolve_or_synthesize(
        prior,
        target,
        revalidate=lambda *_: _go_revalidation(
            target_document, tmp_path, "target-patched-validation"
        ),
        synthesize=lambda item: synthesis_calls.append(item),
    )

    assert result.reused is True
    assert synthesis_calls == []
    assert result.synthesis_bytes == prior.synthesis_bytes
    assert result.response_identity == prior.response_identity
    assert result.output == target_document
    patched = [
        fact
        for fact in result.output["facts"]
        if fact["input_pointer"].startswith("/patches/")
    ]
    assert len(patched) == 1
    assert patched[0]["authority"]["claim_class"] == "support"
    assert result.output["proposal_dispositions"][0]["status"] == "accepted"


def test_irrelevant_commit_has_different_exact_but_equal_semantic_identity(
    tmp_path, accepted_document
):
    first = _repository(tmp_path, "first")
    prior, _ = _snapshot_and_target(first, accepted_document)
    second = _repository(tmp_path, "second")
    (second / "unrelated.txt").write_text("not supplied to component synthesis\n")
    _git(second, "add", ".")
    _git(second, "commit", "-qm", "irrelevant")
    dependencies = _dependencies(second)
    state = SourceRunState(
        capture_source_snapshot(second), capture_source_snapshot(second)
    )
    target_analyzer = _analyzer(second)
    target = ReuseTarget(
        platform="rhoai-target",
        identity=prior.identity,
        inputs=_inputs(second, dependencies, analyzer=target_analyzer),
        compatibility=prior.compatibility,
        dependencies=dependencies,
        source_state=state,
        normalization=_target_normalization_from_prior(
            prior,
            platform="rhoai-target",
            source_state=state,
            analyzer=target_analyzer,
        ),
    )

    decision = decide_reuse(prior, target)
    assert prior.inputs.exact != target.inputs.exact
    assert prior.inputs.semantic == target.inputs.semantic
    assert decision.hit is True


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("summary", "meaningfully changed summary"),
        ("dependencies", {"go_version": "1.25", "go_modules": [], "internal_odh": []}),
        (
            "rbac",
            {
                "cluster_roles": [],
                "roles": [],
                "cluster_role_bindings": [],
                "role_bindings": [],
            },
        ),
        (
            "synthesis_evidence",
            {"security": [{"claim": "changed", "sources": ["source.go:1"]}]},
        ),
        (
            "cross_references",
            [
                {
                    "kind": "network",
                    "from": "a",
                    "to": "b",
                    "relationship": "calls",
                    "sources": ["source.go:1"],
                }
            ],
        ),
        (
            "gap_evidence_index",
            {
                "security": [
                    {
                        "source": "source.go",
                        "question": "changed",
                        "expected_signal": "literal",
                        "status": "open",
                    }
                ]
            },
        ),
    ],
)
def test_all_meaningful_analyzer_fields_invalidate(
    tmp_path, accepted_document, field, replacement
):
    root = _repository(tmp_path)
    dependencies = _dependencies(root)
    prior, _ = _snapshot_and_target(root, accepted_document, dependencies=dependencies)
    analyzer = _analyzer(root)
    analyzer[field] = replacement
    target = ReuseTarget(
        platform="rhoai-target",
        identity=prior.identity,
        inputs=_inputs(root, dependencies, analyzer=analyzer),
        compatibility=prior.compatibility,
        dependencies=dependencies,
        source_state=prior.source_state,
    )
    assert "semantic_input_mismatch" in decide_reuse(prior, target).reasons


def test_only_reviewed_volatile_analyzer_fields_are_excluded(tmp_path):
    root = _repository(tmp_path)
    dependencies = _dependencies(root)
    left = _analyzer(root)
    right = copy.deepcopy(left)
    right.update(
        {
            "commit_sha": "different-commit-label",
            "extracted_at": "2030-01-01T00:00:00Z",
            "schema_version": "presentation-label",
            "analyzer_version": "compatibility-is-separate",
            "scan_statistics": [{"value": 999}],
            "recent_changes": [{"version": "new", "date": "2030", "changes": "new"}],
        }
    )
    left_ids = _inputs(root, dependencies, analyzer=left)
    right_ids = _inputs(root, dependencies, analyzer=right)
    assert left_ids.exact != right_ids.exact
    assert left_ids.semantic == right_ids.semantic
    assert left_ids.recent_changes != right_ids.recent_changes


def test_legacy_category_scan_count_is_excluded_but_other_evidence_is_not(tmp_path):
    root = _repository(tmp_path)
    dependencies = _dependencies(root)
    left = _analyzer(root)
    left["category_coverage"] = {
        "authentication": {
            "status": "complete",
            "fact_count": 0,
            "discovery_contract": "authentication/v1",
            "completed_checks": ["scan"],
            "limitations": [],
            "evidence": [
                "summary:scanned 2 Python source files for "
                "authentication constructions",
                "summary:no inbound runtime surfaces",
            ],
        }
    }
    right = copy.deepcopy(left)
    right["category_coverage"]["authentication"]["evidence"][0] = (
        "summary:scanned 999 Python source files for authentication constructions"
    )
    assert (
        _inputs(root, dependencies, analyzer=left).semantic
        == _inputs(root, dependencies, analyzer=right).semantic
    )

    right["category_coverage"]["authentication"]["evidence"][1] = (
        "summary:an inbound surface now exists"
    )
    assert (
        _inputs(root, dependencies, analyzer=left).semantic
        != _inputs(root, dependencies, analyzer=right).semantic
    )

    right = copy.deepcopy(left)
    right["category_coverage"]["authentication"]["evidence"][0] = (
        "summary:scanned 999 endpoints and found a meaningful gap"
    )
    assert (
        _inputs(root, dependencies, analyzer=left).semantic
        != _inputs(root, dependencies, analyzer=right).semantic
    )


def test_meaningful_order_permissions_and_conditions_remain_significant(tmp_path):
    root = _repository(tmp_path)
    dependencies = _dependencies(root)
    left = _inputs(
        root,
        dependencies,
        settings={"permissions": ["read", "write"], "conditions": ["a", "b"]},
    )
    right = _inputs(
        root,
        dependencies,
        settings={"permissions": ["write", "read"], "conditions": ["b", "a"]},
    )
    assert left.semantic != right.semantic


@pytest.mark.parametrize("kind", ["configuration", "overlay", "contract", "settings"])
def test_configuration_overlay_contract_and_settings_changes_miss(
    tmp_path, accepted_document, kind
):
    root = _repository(tmp_path)
    dependencies = _dependencies(root)
    prior, _ = _snapshot_and_target(root, accepted_document, dependencies=dependencies)
    kwargs = {
        "configuration": {"branch": "changed"} if kind == "configuration" else None,
        "overlays": [{"id": "changed"}] if kind == "overlay" else None,
        "contracts": {"patch": {"schema_version": "2"}} if kind == "contract" else None,
        "settings": {"permissions": ["read", "network"]}
        if kind == "settings"
        else None,
    }
    inputs = _inputs(root, dependencies, **kwargs)
    target = replace(prior, platform="rhoai-target", inputs=inputs)
    target = ReuseTarget(
        target.platform,
        target.identity,
        target.inputs,
        target.compatibility,
        target.dependencies,
        target.source_state,
    )
    assert "semantic_input_mismatch" in decide_reuse(prior, target).reasons


def test_platform_only_integration_does_not_invalidate_but_component_fact_does(
    tmp_path, accepted_document
):
    root = _repository(tmp_path)
    dependencies = _dependencies(root)
    prior, _ = _snapshot_and_target(
        root,
        accepted_document,
        dependencies=dependencies,
        configuration={"branch": "release", "integration_status": "planned"},
    )
    platform_only = _inputs(
        root,
        dependencies,
        configuration={"branch": "release", "integration_status": "current"},
    )
    assert platform_only.semantic == prior.inputs.semantic
    assert platform_only.exact != prior.inputs.exact

    changed = _analyzer(root)
    changed.setdefault("dependencies", {}).setdefault("internal_odh", []).append(
        {"component": "new-runtime", "interaction": "client", "purpose": "real"}
    )
    component_change = _inputs(
        root,
        dependencies,
        analyzer=changed,
        configuration={"branch": "release", "integration_status": "current"},
    )
    assert component_change.semantic != prior.inputs.semantic


def test_supporting_file_and_search_scope_options_and_tree_changes_miss(
    tmp_path, accepted_document
):
    root = _repository(tmp_path)
    search_subtree = root / "search-scope"
    search_subtree.mkdir()
    (search_subtree / "marker.txt").write_text("Enabled\n")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "add search scope")
    search = [
        {
            "tool": "rg",
            "resolved_root": str(root),
            "pattern": "Enabled",
            "options": {"argv": ["-n"]},
            "outcome": "successful-sdk-search",
        }
    ]
    prior_dependencies = _dependencies(root, searches=search)
    prior, _ = _snapshot_and_target(
        root, accepted_document, dependencies=prior_dependencies
    )
    (root / "config.yaml").write_text("permission: write\ncondition: enabled\n")
    changed_file_dependencies = _dependencies(root)
    changed_file = ReuseTarget(
        "rhoai-target",
        prior.identity,
        _inputs(root, changed_file_dependencies),
        prior.compatibility,
        changed_file_dependencies,
        SourceRunState(capture_source_snapshot(root), capture_source_snapshot(root)),
    )
    assert "semantic_input_mismatch" in decide_reuse(prior, changed_file).reasons

    _git(root, "checkout", "--", "config.yaml")
    changed_options = copy.deepcopy(search)
    changed_options[0]["options"] = {"argv": ["-n", "--hidden"]}
    option_dependencies = _dependencies(root, searches=changed_options)
    option_target = ReuseTarget(
        "rhoai-target",
        prior.identity,
        _inputs(root, option_dependencies),
        prior.compatibility,
        option_dependencies,
        SourceRunState(capture_source_snapshot(root), capture_source_snapshot(root)),
    )
    assert "semantic_input_mismatch" in decide_reuse(prior, option_target).reasons

    changed_root = copy.deepcopy(search)
    changed_root[0]["resolved_root"] = str(search_subtree)
    root_dependencies = _dependencies(root, searches=changed_root)
    root_target = ReuseTarget(
        "rhoai-target",
        prior.identity,
        _inputs(root, root_dependencies),
        prior.compatibility,
        root_dependencies,
        SourceRunState(capture_source_snapshot(root), capture_source_snapshot(root)),
    )
    assert "semantic_input_mismatch" in decide_reuse(prior, root_target).reasons

    (root / "source.go").write_text("package source\nconst Enabled = false\n")
    tree_dependencies = _dependencies(root, searches=search)
    tree_target = ReuseTarget(
        "rhoai-target",
        prior.identity,
        _inputs(root, tree_dependencies),
        prior.compatibility,
        tree_dependencies,
        SourceRunState(capture_source_snapshot(root), capture_source_snapshot(root)),
    )
    reasons = decide_reuse(prior, tree_target).reasons
    assert "searched_tree_not_clean" in reasons
    assert "semantic_input_mismatch" in reasons


@pytest.mark.parametrize(
    "compatibility",
    [
        _compatibility(analyzer_schema_version="2"),
        _compatibility(analyzer_build_identity="sha256:dirty-extractor-change"),
        _compatibility(normalizer_version="structured-component-normalizer/v2"),
    ],
)
def test_exact_build_and_normalization_mismatches(
    tmp_path, accepted_document, compatibility
):
    root = _repository(tmp_path)
    prior, target = _snapshot_and_target(root, accepted_document)
    target = replace(target, compatibility=compatibility)
    assert "producer_or_contract_mismatch" in decide_reuse(prior, target).reasons


def test_dirty_extractor_source_changes_build_identity(tmp_path):
    root = _repository(tmp_path)
    clean = capture_producer_build_identity(root, version="0.1.0-dev")
    (root / "source.go").write_text("package source\nconst Enabled = false\n")
    dirty = capture_producer_build_identity(root, version="0.1.0-dev")
    assert clean != dirty


def test_real_git_rename_records_both_paths_and_copy_records_parse(tmp_path):
    root = _repository(tmp_path)
    _git(root, "mv", "source.go", "renamed.go")

    snapshot = capture_source_snapshot(root)

    assert snapshot.dirty_paths == ("renamed.go", "source.go")
    assert _porcelain_v1_z_paths(b"C  copied.go\0source.go\0") == (
        "copied.go",
        "source.go",
    )


def test_codex_telemetry_dependency_decision_defaults_unknown_to_miss_and_rg_hits(
    tmp_path, accepted_document
):
    root = _repository(tmp_path)
    command = (
        "rg --no-config --no-ignore-global --color never --sort path -n Enabled ."
    )
    direct_rg = _rg_item(root, command, identifier="direct-rg")
    telemetry = codex_agent._source_read_telemetry([direct_rg], root)
    dependencies = _search_dependencies(root, telemetry)
    prior, target = _snapshot_and_target(
        root,
        accepted_document,
        dependencies=dependencies,
    )
    assert decide_reuse(prior, target).hit is True
    assert dependencies.searches[0].pattern == "Enabled"
    assert dict(dependencies.searches[0].options)["argv"] == (
        "--no-config",
        "--no-ignore-global",
        "--color",
        "never",
        "--sort",
        "path",
        "-n",
        "Enabled",
        ".",
    )
    assert dependencies.searches[0].replay_result_identity
    assert dependencies.searches[0].replay_context_identity
    assert "observed_result_identity" not in dependencies.reusable_payload()[
        "searches"
    ][0]

    synthesis_calls = []
    result = resolve_or_synthesize(
        prior,
        target,
        revalidate=lambda snapshot, current: _go_revalidation(
            _valid_revalidation(snapshot, current).document,
            tmp_path,
            "verified-rg-zero-call",
        ),
        synthesize=lambda item: synthesis_calls.append(item),
    )
    assert result.reused is True
    assert synthesis_calls == []

    unknown = {
        "type": "commandExecution",
        "id": "unknown-list",
        "cwd": str(root),
        "exit_code": 0,
        "command_actions": [{"type": "listFiles", "command": "ls -R ."}],
    }
    unknown_telemetry = codex_agent._source_read_telemetry([unknown], root)
    unknown_dependencies = dependency_record_from_telemetry(
        unknown_telemetry,
        checkout_root=root,
        justifications={},
    )
    unknown_prior, unknown_target = _snapshot_and_target(
        root,
        accepted_document,
        dependencies=unknown_dependencies,
    )
    reasons = decide_reuse(unknown_prior, unknown_target).reasons
    assert "dependency_record_incomplete" in reasons
    assert "unclassified_source_command" in reasons


@pytest.mark.parametrize("replay_mode", ["verify-observation", "target-replay"])
@pytest.mark.parametrize(
    ("mutation", "value"),
    [
        ("argv", [
            "--no-config", "--no-ignore-global", "--color", "never",
            "--sort", "path", "--pre", "/tmp/not-allowed", "Enabled", ".",
        ]),
        ("argv", [
            "--no-config", "--no-ignore-global", "--color", "never",
            "--sort", "path", "-f", "/etc/hostname", ".",
        ]),
        ("argv", [
            "--no-config", "--no-ignore-global", "--color", "never",
            "--sort", "path", "Enabled", "/etc/passwd",
        ]),
        ("argv", [
            "--no-ignore-global", "--color", "never", "--sort", "path",
            "Enabled", ".",
        ]),
        ("argv", [
            "--no-config", "--no-ignore-global", "--color", "never",
            "--sort", "path", "--hidden", "Enabled", ".",
        ]),
        ("argv", [
            "--no-config", "--no-ignore-global", "--color", "never",
            "--sort", "path", "Enabled", ".", "&",
        ]),
        ("pattern", "Different"),
        ("resolved_root", "/etc"),
        ("execution_cwd", "/etc"),
        ("option", {"--glob": "*.go"}),
    ],
)
def test_persisted_rg_replay_rejects_unbound_or_unsafe_argv_before_execution(
    tmp_path, monkeypatch, replay_mode, mutation, value
):
    root = _repository(tmp_path)
    command = (
        "rg --no-config --no-ignore-global --color never --sort path -n Enabled ."
    )
    telemetry = codex_agent._source_read_telemetry([_rg_item(root, command)], root)
    observed = copy.deepcopy(telemetry["dependency_observations"]["searches"][0])
    marker = tmp_path / "unsafe-replay-executed"
    if mutation == "argv":
        argv = list(value)
        if "--pre" in argv:
            preprocessor = tmp_path / "unsafe-preprocessor.sh"
            preprocessor.write_text(
                f"#!/bin/sh\ntouch {marker}\ncat \"$1\"\n"
            )
            preprocessor.chmod(0o755)
            argv[argv.index("--pre") + 1] = str(preprocessor)
        observed["options"]["argv"] = argv
    elif mutation == "option":
        observed["options"].update(value)
    else:
        observed[mutation] = value
    telemetry["dependency_observations"]["searches"] = [observed]

    executed_searches = []
    actual_run = structured_component_reuse.subprocess.run

    def observe_run(argv, *args, **kwargs):
        if argv and Path(str(argv[0])).name == "rg" and argv[1:] != ["--version"]:
            executed_searches.append(list(argv))
        return actual_run(argv, *args, **kwargs)

    monkeypatch.setattr(structured_component_reuse.subprocess, "run", observe_run)
    if mutation == "resolved_root":
        with pytest.raises(ReuseRecordError, match="escapes checkout"):
            dependency_record_from_telemetry(
                telemetry,
                checkout_root=root,
                justifications={},
                search_replay_mode=replay_mode,
            )
    else:
        dependencies = _search_dependencies(
            root,
            telemetry,
            replay_mode=replay_mode,
        )
        assert dependencies.complete is False
        assert dependencies.unclassified_source_commands == (
            "rg-search-verification-unavailable:.",
        )
    assert executed_searches == []
    assert marker.exists() is False


@pytest.mark.asyncio
async def test_claude_unknown_tools_flow_to_dependency_decision_and_denials_do_not(
    tmp_path, accepted_document
):
    root = _repository(tmp_path)
    unrestricted = agent_runner._AgentExecutionGuard({}, root)
    for tool in ("NotebookRead", "Task", "LS", "WebFetch"):
        await unrestricted.pre_tool_use(
            {"tool_name": tool, "tool_input": {}},
            None,
            {},
        )
    telemetry = unrestricted.telemetry()
    assert telemetry["dependency_observations"]["unclassified_source_commands"] == [
        "NotebookRead",
        "Task",
        "LS",
        "WebFetch",
    ]
    dependencies = dependency_record_from_telemetry(
        telemetry,
        checkout_root=root,
        justifications={},
    )
    prior, target = _snapshot_and_target(
        root,
        accepted_document,
        dependencies=dependencies,
    )
    reasons = decide_reuse(prior, target).reasons
    assert "dependency_record_incomplete" in reasons
    assert "unclassified_source_command" in reasons

    permitted_unhandled = agent_runner._AgentExecutionGuard(
        {
            "route": "partial",
            "readiness": "partial",
            "discovery_tools": ("NotebookRead",),
        },
        root,
    )
    permitted = await permitted_unhandled.pre_tool_use(
        {"tool_name": "NotebookRead", "tool_input": {}},
        None,
        {},
    )
    assert permitted == {}
    permitted_observation = permitted_unhandled.telemetry()[
        "dependency_observations"
    ]
    assert permitted_observation["complete"] is False
    assert permitted_observation["unclassified_source_commands"] == [
        "NotebookRead"
    ]

    restricted = agent_runner._AgentExecutionGuard(
        {"route": "partial", "readiness": "partial"},
        root,
    )
    for tool in ("NotebookRead", "Task", "LS", "WebFetch"):
        result = await restricted.pre_tool_use(
            {"tool_name": tool, "tool_input": {}},
            None,
            {},
        )
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
    denied = restricted.telemetry()["dependency_observations"]
    assert denied["complete"] is True
    assert denied["reads"] == []
    assert denied["searches"] == []
    assert denied["unclassified_source_commands"] == []


@pytest.mark.asyncio
async def test_claude_search_scope_is_preserved_but_parent_ignore_case_misses(
    tmp_path, accepted_document
):
    root = _repository(tmp_path)
    source = root / "src" / "a.txt"
    source.parent.mkdir()
    source.write_text("secret-marker\n")
    _git(root, "add", "src/a.txt")
    _git(root, "commit", "-qm", "add scoped source")
    (root / ".gitignore").write_text("src/a.txt\n")
    _git(root, "add", ".gitignore")
    _git(root, "commit", "-qm", "ignore scoped source")

    guard = agent_runner._AgentExecutionGuard({}, root)
    await guard.pre_tool_use(
        {
            "tool_name": "Read",
            "tool_input": {
                "file_path": "config.yaml",
                "offset": 1,
                "limit": 2,
            },
        },
        None,
        {},
    )
    await guard.pre_tool_use(
        {
            "tool_name": "Grep",
            "tool_input": {
                "pattern": "secret-marker",
                "path": "src",
                "output_mode": "content",
            },
        },
        None,
        {},
    )
    telemetry = guard.telemetry()
    observed = telemetry["dependency_observations"]
    assert observed["complete"] is False
    assert observed["reads"][0]["path"] == "config.yaml"
    assert observed["searches"][0]["resolved_root"] == str(source.parent)
    assert observed["unclassified_source_commands"] == [
        "Grep-search-result-unverified:src"
    ]

    search = observed["searches"][0]
    key = search_observation_key(
        root="src",
        pattern=search["pattern"],
        options=search["options"],
        tool=search["tool"],
    )
    prior_dependencies = dependency_record_from_telemetry(
        telemetry,
        checkout_root=root,
        justifications={"config.yaml": "direct source read"},
        search_justifications={key: "Claude pre-tool search scope"},
    )
    assert prior_dependencies.unclassified_source_commands == (
        "Grep-search-result-unverified:src",
        "Grep-search-verification-unavailable:src",
    )
    prior, _ = _snapshot_and_target(
        root, accepted_document, dependencies=prior_dependencies
    )
    before = subprocess.run(
        ["rg", "-n", "secret-marker", "src"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert before.returncode == 1
    assert prior_dependencies.files[0].path == "config.yaml"

    (root / ".gitignore").write_text("")
    _git(root, "add", ".gitignore")
    _git(root, "commit", "-qm", "unignore scoped source")
    target_dependencies = dependency_record_from_telemetry(
        telemetry,
        checkout_root=root,
        justifications={"config.yaml": "direct source read"},
        search_justifications={key: "Claude pre-tool search scope"},
        search_replay_mode="target-replay",
    )
    after = subprocess.run(
        ["rg", "-n", "secret-marker", "src"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert after.returncode == 0
    assert prior_dependencies.searches[0].tree_identity == (
        target_dependencies.searches[0].tree_identity
    )
    assert target_dependencies.complete is False
    target = _target_with_dependencies(prior, root, target_dependencies)
    decision = decide_reuse(prior, target)
    assert decision.hit is False
    assert "dependency_record_incomplete" in decision.reasons
    assert "unclassified_source_command" in decision.reasons


@pytest.mark.parametrize(
    "scope_option",
    ["--no-ignore", "--no-ignore-vcs", "--hidden", "--follow", "-L", "-Ln"],
)
def test_ignored_source_search_modes_are_incomplete_with_real_git_state(
    tmp_path, accepted_document, scope_option
):
    root = _repository(tmp_path)
    (root / ".gitignore").write_text("ignored/\n")
    _git(root, "add", ".gitignore")
    _git(root, "commit", "-qm", "ignore generated source")
    before = capture_source_snapshot(root)
    ignored = root / "ignored" / "generated.go"
    ignored.parent.mkdir()
    ignored.write_text("package ignored\nconst Hidden = true\n")
    after = capture_source_snapshot(root)
    assert after == before

    command = f"rg {scope_option} Hidden ."
    telemetry = codex_agent._source_read_telemetry(
        [
            {
                "type": "commandExecution",
                "id": f"ignored-{scope_option}",
                "cwd": str(root),
                "exit_code": 0,
                "command_actions": [{"type": "search", "command": command}],
            }
        ],
        root,
    )
    observations = telemetry["dependency_observations"]
    assert observations["complete"] is False
    assert observations["searches"] == []
    dependencies = dependency_record_from_telemetry(
        telemetry,
        checkout_root=root,
        justifications={},
    )
    prior, target = _snapshot_and_target(
        root,
        accepted_document,
        dependencies=dependencies,
    )
    assert "dependency_record_incomplete" in decide_reuse(prior, target).reasons


def test_parent_gitignore_change_updates_verified_search_and_misses_end_to_end(
    tmp_path, accepted_document
):
    root = _repository(tmp_path)
    (root / "src").mkdir()
    (root / "src" / "a.txt").write_text("secret-marker\n")
    _git(root, "add", "src/a.txt")
    _git(root, "commit", "-qm", "fixture source")
    (root / ".gitignore").write_text("src/a.txt\n")
    _git(root, "add", ".gitignore")
    _git(root, "commit", "-qm", "ignore scoped tracked source")

    command = (
        "rg --no-config --no-ignore-global --color never --sort path "
        "-n secret-marker src"
    )
    item = _rg_item(root, command)
    assert item["exit_code"] == 1
    telemetry = codex_agent._source_read_telemetry([item], root)
    prior_dependencies = _search_dependencies(root, telemetry)
    prior, prior_target = _snapshot_and_target(
        root, accepted_document, dependencies=prior_dependencies
    )
    assert decide_reuse(prior, prior_target).hit is True

    (root / ".gitignore").write_text("")
    _git(root, "add", ".gitignore")
    _git(root, "commit", "-qm", "unignore scoped tracked source")
    stale_observation = _search_dependencies(root, telemetry)
    assert stale_observation.complete is False
    assert stale_observation.unclassified_source_commands == (
        "rg-search-verification-unavailable:src",
    )
    target_dependencies = _search_dependencies(
        root, telemetry, replay_mode="target-replay"
    )
    target = _target_with_dependencies(prior, root, target_dependencies)

    assert (
        prior_dependencies.searches[0].tree_identity
        == target_dependencies.searches[0].tree_identity
    )
    assert (
        prior_dependencies.searches[0].replay_result_identity
        != target_dependencies.searches[0].replay_result_identity
    )
    assert "semantic_input_mismatch" in decide_reuse(prior, target).reasons

    unsafe = _rg_item(root, "rg -n secret-marker src", identifier="unsafe-rg")
    unsafe_observations = codex_agent._source_read_telemetry([unsafe], root)[
        "dependency_observations"
    ]
    assert unsafe_observations["complete"] is False
    assert unsafe_observations["searches"] == []
    unsafe_dependencies = dependency_record_from_telemetry(
        {"dependency_observations": unsafe_observations},
        checkout_root=root,
        justifications={},
    )
    unsafe_target = _target_with_dependencies(prior, root, unsafe_dependencies)
    assert "dependency_record_incomplete" in decide_reuse(
        prior, unsafe_target
    ).reasons


def test_created_and_deleted_local_ignore_config_is_verified_by_replay(
    tmp_path, accepted_document
):
    root = _repository(tmp_path)
    command = (
        "rg --no-config --no-ignore-global --color never --sort path -n Enabled ."
    )
    telemetry = codex_agent._source_read_telemetry([_rg_item(root, command)], root)
    prior_dependencies = _search_dependencies(root, telemetry)
    prior, _ = _snapshot_and_target(
        root, accepted_document, dependencies=prior_dependencies
    )

    (root / ".ignore").write_text("source.go\n")
    _git(root, "add", ".ignore")
    _git(root, "commit", "-qm", "add local ripgrep ignore")
    created = _search_dependencies(root, telemetry, replay_mode="target-replay")
    created_target = _target_with_dependencies(prior, root, created)
    assert created.searches[0].replay_result_identity != (
        prior_dependencies.searches[0].replay_result_identity
    )
    assert "semantic_input_mismatch" in decide_reuse(
        prior, created_target
    ).reasons

    _git(root, "rm", "-q", ".ignore")
    _git(root, "commit", "-qm", "delete local ripgrep ignore")
    deleted = _search_dependencies(root, telemetry, replay_mode="target-replay")
    deleted_target = _target_with_dependencies(prior, root, deleted)
    assert deleted.searches[0].replay_result_identity == (
        prior_dependencies.searches[0].replay_result_identity
    )
    assert decide_reuse(prior, deleted_target).hit is True


@pytest.mark.parametrize(
    "search_tail",
    ["-g '*.txt' secret-marker src", "secret-marker src/a.txt"],
)
def test_include_glob_and_explicit_ignored_file_root_have_verified_hits(
    tmp_path, accepted_document, search_tail
):
    root = _repository(tmp_path)
    (root / "src").mkdir()
    (root / "src" / "a.txt").write_text("secret-marker\n")
    _git(root, "add", "src/a.txt")
    _git(root, "commit", "-qm", "fixture source")
    (root / ".gitignore").write_text("src/a.txt\n")
    _git(root, "add", ".gitignore")
    _git(root, "commit", "-qm", "ignore tracked source")
    command = (
        "rg --no-config --no-ignore-global --color never --sort path "
        + search_tail
    )
    item = _rg_item(root, command)
    assert item["exit_code"] == 0
    telemetry = codex_agent._source_read_telemetry([item], root)
    dependencies = _search_dependencies(root, telemetry)
    prior, target = _snapshot_and_target(
        root, accepted_document, dependencies=dependencies
    )

    assert dependencies.complete is True
    assert dependencies.searches[0].replay_result_identity
    assert decide_reuse(prior, target).hit is True


@pytest.mark.parametrize("config_variable", ["RIPGREP_CONFIG_PATH", "RG_CONFIG_PATH"])
def test_external_ripgrep_config_is_disabled_or_search_is_unavailable(
    tmp_path, accepted_document, monkeypatch, config_variable
):
    root = _repository(tmp_path)
    external_config = tmp_path / "ripgrep.conf"
    external_config.write_text("--glob=!source.go\n")
    execution_env = os.environ.copy()
    execution_env[config_variable] = str(external_config)
    monkeypatch.setenv(config_variable, str(external_config))
    command = (
        "rg --no-config --no-ignore-global --color never --sort path -n Enabled ."
    )
    item = _rg_item(root, command, env=execution_env)
    assert "source.go" in item["aggregated_output"]
    telemetry = codex_agent._source_read_telemetry([item], root)
    dependencies = _search_dependencies(root, telemetry)
    prior, _ = _snapshot_and_target(
        root, accepted_document, dependencies=dependencies
    )

    external_config.unlink()
    target_dependencies = _search_dependencies(
        root, telemetry, replay_mode="target-replay"
    )
    target = _target_with_dependencies(prior, root, target_dependencies)
    assert target_dependencies.searches[0].replay_result_identity == (
        dependencies.searches[0].replay_result_identity
    )
    assert decide_reuse(prior, target).hit is True

    monkeypatch.delenv(config_variable)
    unsafe = _rg_item(root, "rg -n Enabled .", identifier="ambient-config-missing")
    observation = codex_agent._source_read_telemetry([unsafe], root)[
        "dependency_observations"
    ]
    assert observation["complete"] is False
    assert observation["searches"] == []


def test_global_ignore_configuration_is_explicitly_disabled(
    tmp_path, accepted_document, monkeypatch
):
    root = _repository(tmp_path)
    global_ignore = tmp_path / "global-ignore"
    global_ignore.write_text("source.go\n")
    global_config = tmp_path / "gitconfig"
    global_config.write_text(
        f"[core]\n\texcludesFile = {global_ignore.as_posix()}\n"
    )
    execution_env = os.environ.copy()
    execution_env["GIT_CONFIG_GLOBAL"] = str(global_config)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(global_config))
    command = (
        "rg --no-config --no-ignore-global --color never --sort path -n Enabled ."
    )
    item = _rg_item(root, command, env=execution_env)
    assert "source.go" in item["aggregated_output"]
    telemetry = codex_agent._source_read_telemetry([item], root)
    dependencies = _search_dependencies(root, telemetry)
    prior, target = _snapshot_and_target(
        root, accepted_document, dependencies=dependencies
    )
    assert decide_reuse(prior, target).hit is True

    unsafe_command = "rg --no-config --color never --sort path -n Enabled ."
    unsafe = _rg_item(root, unsafe_command, env=execution_env)
    assert unsafe["exit_code"] == 1
    observation = codex_agent._source_read_telemetry([unsafe], root)[
        "dependency_observations"
    ]
    assert observation["complete"] is False
    assert observation["searches"] == []


def test_incomplete_unclassified_and_midrun_mutation_are_explicit_misses(
    tmp_path, accepted_document
):
    root = _repository(tmp_path)
    prior, _ = _snapshot_and_target(root, accepted_document)
    incomplete = replace(prior.dependencies, complete=False)
    incomplete_target = replace(
        ReuseTarget(
            "rhoai-target",
            prior.identity,
            _inputs(root, incomplete),
            prior.compatibility,
            incomplete,
            prior.source_state,
        )
    )
    assert (
        "dependency_record_incomplete" in decide_reuse(prior, incomplete_target).reasons
    )

    unclassified = replace(
        prior.dependencies,
        complete=False,
        unclassified_source_commands=("rg | sed",),
    )
    unclassified_target = ReuseTarget(
        "rhoai-target",
        prior.identity,
        _inputs(root, unclassified),
        prior.compatibility,
        unclassified,
        prior.source_state,
    )
    reasons = decide_reuse(prior, unclassified_target).reasons
    assert "unclassified_source_command" in reasons
    assert "dependency_record_incomplete" in reasons

    start = capture_source_snapshot(root)
    (root / "source.go").write_text("package source\nconst Mutated = true\n")
    end = capture_source_snapshot(root)
    mutated_target = replace(
        unclassified_target, source_state=SourceRunState(start, end)
    )
    assert "source_mutated_during_run" in decide_reuse(prior, mutated_target).reasons


def test_same_head_dirty_worktree_is_not_treated_as_same_input(
    tmp_path, accepted_document
):
    root = _repository(tmp_path)
    prior, _ = _snapshot_and_target(root, accepted_document)
    head = _git(root, "rev-parse", "HEAD")
    (root / "config.yaml").write_text("permission: changed-without-commit\n")
    dependencies = _dependencies(root)
    dirty = capture_source_snapshot(root)
    target = ReuseTarget(
        "rhoai-target",
        prior.identity,
        _inputs(root, dependencies),
        prior.compatibility,
        dependencies,
        SourceRunState(dirty, dirty),
    )
    assert dirty.head == head == prior.source_state.end.head
    assert "semantic_input_mismatch" in decide_reuse(prior, target).reasons


def test_missing_justification_and_unaccounted_untracked_input_miss(
    tmp_path, accepted_document
):
    root = _repository(tmp_path)
    with pytest.raises(ReuseRecordError, match="lack justifications"):
        dependency_record_from_telemetry(
            _telemetry(root), checkout_root=root, justifications={}
        )

    search = {
        "tool": "rg",
        "resolved_root": str(root),
        "pattern": "Enabled",
        "options": {"argv": ["-n"]},
        "outcome": "successful-sdk-search",
    }
    with pytest.raises(ReuseRecordError, match="search lacks justification"):
        dependency_record_from_telemetry(
            _telemetry(root, searches=[search]),
            checkout_root=root,
            justifications={"config.yaml": "read reason"},
        )

    prior, target = _snapshot_and_target(root, accepted_document)
    (root / "generated.txt").write_text("untracked generator input\n")
    state = capture_source_snapshot(root)
    target = replace(target, source_state=SourceRunState(state, state))
    assert "unaccounted_untracked_inputs" in decide_reuse(prior, target).reasons


def test_accounted_untracked_generated_and_external_inputs_are_hashed(
    tmp_path, accepted_document
):
    root = _repository(tmp_path)
    generated = root / "generated.txt"
    generated.write_text("generated input\n")
    external = tmp_path / "external-policy.json"
    external.write_text('{"allowed":true}\n')
    dependencies = _dependencies(
        root,
        accounted_untracked=("generated.txt",),
        generated_inputs=(generated,),
        external_inputs=(external,),
    )
    prior, target = _snapshot_and_target(
        root, accepted_document, dependencies=dependencies
    )
    assert decide_reuse(prior, target).hit is True

    external.write_text('{"allowed":false}\n')
    changed_dependencies = _dependencies(
        root,
        accounted_untracked=("generated.txt",),
        generated_inputs=(generated,),
        external_inputs=(external,),
    )
    changed = replace(
        target,
        inputs=_inputs(root, changed_dependencies),
        dependencies=changed_dependencies,
    )
    assert "semantic_input_mismatch" in decide_reuse(prior, changed).reasons


def test_predecessor_resolution_cycles_self_missing_aliases_and_wrong_repo(
    tmp_path, accepted_document
):
    configs = {
        "old": {},
        "new": {"reuse_from": "old"},
    }
    assert resolve_predecessor("new", configs) == "old"
    with pytest.raises(ReuseConfigurationError, match="reuses itself"):
        resolve_predecessor("new", {"new": {"reuse_from": "new"}})
    with pytest.raises(ReuseConfigurationError, match="missing"):
        resolve_predecessor("new", {"new": {"reuse_from": "absent"}})
    with pytest.raises(ReuseConfigurationError, match="cycle"):
        resolve_predecessor(
            "new",
            {"new": {"reuse_from": "old"}, "old": {"reuse_from": "new"}},
        )

    root = _repository(tmp_path)
    prior, _ = _snapshot_and_target(root, accepted_document)
    alias_target = ComponentIdentity(
        "policy", "https://github.com/praxis-proxy/policy.git"
    )
    assert select_predecessor_snapshot([prior], "rhoai-previous", alias_target) is prior
    with pytest.raises(ReuseRecordError, match="different repository"):
        select_predecessor_snapshot(
            [prior],
            "rhoai-previous",
            ComponentIdentity("policy", "https://github.com/other/policy.git"),
        )
    with pytest.raises(ReuseRecordError, match="no snapshot"):
        select_predecessor_snapshot(
            [prior],
            "rhoai-previous",
            ComponentIdentity(
                "unrelated", "https://github.com/praxis-proxy/policy.git"
            ),
        )
    ambiguous = replace(prior, snapshot_id="duplicate", identity=alias_target)
    with pytest.raises(ReuseRecordError, match="ambiguous"):
        select_predecessor_snapshot([prior, ambiguous], "rhoai-previous", alias_target)


def test_rejected_legacy_refresh_integrity_and_invalid_output_take_one_miss_path(
    tmp_path, accepted_document
):
    root = _repository(tmp_path)
    prior, target = _snapshot_and_target(root, accepted_document)
    variants = [
        replace(prior, accepted=False),
        replace(prior, route="legacy-markdown"),
        replace(prior, synthesis_integrity="sha256:tampered"),
        replace(prior, document_integrity="sha256:tampered"),
    ]
    for variant in variants:
        calls = []
        result = resolve_or_synthesize(
            variant,
            target,
            revalidate=_valid_revalidation,
            synthesize=lambda item: calls.append(item) or {"fresh": True},
        )
        assert result.reused is False
        assert len(calls) == 1

    refresh_calls = []
    refresh = resolve_or_synthesize(
        prior,
        target,
        revalidate=_valid_revalidation,
        synthesize=lambda item: refresh_calls.append(item) or {"fresh": True},
        force_refresh=True,
    )
    assert refresh.decision.reasons == ("explicit_refresh",)
    assert len(refresh_calls) == 1

    invalid_calls = []
    invalid = resolve_or_synthesize(
        prior,
        target,
        revalidate=lambda *_: RevalidationResult(
            document=accepted_document,
            checks={
                "document_schema": False,
                "typed_references": True,
                "patch_policy": True,
                "current_acceptance_rules": True,
            },
        ),
        synthesize=lambda item: invalid_calls.append(item) or {"fresh": True},
    )
    assert "current_revalidation_failed" in invalid.decision.reasons
    assert "revalidated_document_inconsistent" in invalid.decision.reasons
    assert len(invalid_calls) == 1

    tampered_inputs = replace(prior.inputs, semantic="sha256:tampered")
    tampered_target = replace(target, inputs=tampered_inputs)
    assert "target_semantic_identity_integrity_mismatch" in decide_reuse(
        prior, tampered_target
    ).reasons


def test_recent_changes_refresh_original_response_and_renderer_only_rerender(
    tmp_path, accepted_document
):
    root = _repository(tmp_path)
    prior, target = _snapshot_and_target(root, accepted_document)
    (root / "irrelevant.txt").write_text("not supplied to synthesis\n")
    _git(root, "add", "irrelevant.txt")
    _git(root, "commit", "-qm", "irrelevant target commit")
    analyzer = _analyzer(root)
    analyzer["extracted_at"] = "2026-09-08T13:14:15Z"
    analyzer["recent_changes"] = [
        {"version": "new", "date": "2026-09-08", "changes": "refreshed"}
    ]
    refreshed_inputs = _inputs(root, target.dependencies, analyzer=analyzer)
    state = capture_source_snapshot(root)
    target = replace(
        target,
        inputs=refreshed_inputs,
        source_state=SourceRunState(state, state),
    )
    with pytest.raises(TypeError):
        target.inputs.recent_changes[0]["changes"] = "mutated"
    synthesis_calls = []

    stale_calls = []
    stale = resolve_or_synthesize(
        prior,
        target,
        revalidate=_valid_revalidation,
        synthesize=lambda item: stale_calls.append(item) or {"fresh": True},
    )
    assert stale.reused is False
    assert "target_normalization_analyzer_fingerprint_mismatch" in (
        stale.decision.reasons
    )
    assert "target_normalization_recent_changes_mismatch" in stale.decision.reasons
    assert len(stale_calls) == 1

    analyzer_path = tmp_path / "analyzer.json"
    analyzer_path.write_text(json.dumps(analyzer))
    refreshed_path = tmp_path / "refreshed-document.json"
    refreshed_document = _normalize_phase_one_document(
        analyzer_path, refreshed_path, version_scope="rhoai-target"
    )
    target = replace(
        target,
        normalization=TargetNormalization.capture(refreshed_document),
    )
    refreshed_validation = _go_revalidation(
        refreshed_document,
        tmp_path,
        "valid-refreshed-document",
    )
    assert all(refreshed_validation.checks.values())

    def refreshed_revalidation(snapshot, current):
        return refreshed_validation

    result = resolve_or_synthesize(
        prior,
        target,
        revalidate=refreshed_revalidation,
        synthesize=lambda item: synthesis_calls.append(item),
    )
    rendered = render_resolution(result, lambda document: json.dumps(document))
    assert result.reused is True
    assert synthesis_calls == []
    assert "refreshed" in rendered
    assert result.synthesis_bytes == prior.synthesis_bytes
    assert result.response_identity == prior.response_identity
    assert result.provenance["recent_changes_refreshed"] is True
    assert result.provenance["predecessor_document_integrity"] == (
        prior.document_integrity
    )
    assert result.provenance["target_document_integrity"] == content_hash(
        result.output
    )
    assert result.output == refreshed_document
    assert result.output["identity"]["version_scope"] == "rhoai-target"
    assert result.output["identity"]["source_revision"] == analyzer["commit_sha"]
    assert result.output["analyzer_input"]["bundle_fingerprint"] == (
        target.inputs.analyzer_binding["bundle_fingerprint"]
    )
    assert result.output["analyzer_input"]["extracted_at"] == (
        analyzer["extracted_at"]
    )
