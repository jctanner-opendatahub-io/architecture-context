from __future__ import annotations

import base64
import copy
import json
import os
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/structured_component"
sys.path.insert(0, str(ROOT))

from lib import structured_component_synthesis as synthesis  # noqa: E402
from lib.structured_component_reuse import (  # noqa: E402
    ReuseConfigurationError,
    ReuseDecision,
    ReuseRecordError,
    ReuseResolution,
    content_hash,
)
from lib.structured_component_synthesis import (  # noqa: E402
    AdapterCapabilityError,
    ClaudeStructuredAdapter,
    CodexStructuredAdapter,
    EvidenceScopeError,
    GoStructuredAssembler,
    HarnessResponse,
    InputMutationError,
    RateLimitError,
    SourceNomination,
    StructuredSynthesisError,
    StructuredSynthesisRequest,
    SynthesisLimits,
    _analyzer_bundle_fingerprint,
    _validate_adapter_settings,
    run_structured_synthesis,
    special_synthesis_envelope,
)


class FakeAssembler:
    def assemble(self, request, payload, artifact_dir):
        document = artifact_dir / "document.json"
        markdown = artifact_dir / "candidate.md"
        document.write_text(json.dumps({"response": payload["response_id"]}))
        markdown.write_text("private candidate\n")
        _, dispositions, _ = synthesis._select_sections(
            payload, request.section_policy, request.version_scope
        )
        return document, markdown, dispositions

    def validate_and_render(self, document, markdown):
        markdown.write_text("private reused candidate\n")


def _inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    (checkout / "source.go").write_text(
        "package source\n\nconst Enabled = true\n\nfunc Run() {}\n"
    )
    analyzer = tmp_path / "analyzer.json"
    analyzer.write_bytes((FIXTURES / "analyzer-rbac-praxis.json").read_bytes())
    component_map = tmp_path / "component-map.json"
    component_map.write_bytes((FIXTURES / "component-map-praxis.json").read_bytes())
    return checkout, analyzer, component_map


def _request(tmp_path: Path, **changes) -> StructuredSynthesisRequest:
    checkout, analyzer, component_map = _inputs(tmp_path)
    values = {
        "artifact_dir": tmp_path / "artifacts",
        "checkout_root": checkout,
        "analyzer_path": analyzer,
        "component_map_path": component_map,
        "component": "praxis-policy",
        "version_scope": "rhoai-test",
        "integration_status": "unknown",
        "distribution": "RHOAI",
        "model": "offline-model",
        "settings": {},
        "instructions": "Use only the complete supplied JSON bundle.",
        "nominations": (
            SourceNomination("source.go", 1, 5, "Analyzer nominated source"),
        ),
        "allowed_followup_paths": ("source.go",),
        "limits": SynthesisLimits(),
    }
    values.update(changes)
    return StructuredSynthesisRequest(**values)


def _response(prompt: str, **changes) -> str:
    bundle = json.loads(prompt)["evidence_bundle"]
    payload = {
        "schema_version": "1.0.0",
        "response_id": "response-01",
        "input_bundle_identity": bundle["bundle_identity"],
        "completion_status": "complete",
        "sections": [],
        "typed_patches": [],
        "limitations": [],
        "evidence_requests": [],
    }
    payload.update(changes)
    return json.dumps(payload, separators=(",", ":"))


def _adapter(kind, callback, **changes):
    async def caller(prompt, schema, model, settings):
        raw = callback(prompt, schema, model, settings)
        return HarnessResponse(
            raw_text=raw,
            reported_model=model,
            reported_settings=settings,
            response_identity=content_hash(raw.encode()),
            observations={"tool_calls": 0},
        )

    cls = ClaudeStructuredAdapter if kind == "claude" else CodexStructuredAdapter
    options = {
        "tool_free_enforced": True,
        "context_complete": True,
        "implicit_context": {"test_transport": "tool-free"},
        **changes,
    }
    return cls(
        caller,
        **options,
    )


def _git(checkout: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=checkout,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


@pytest.fixture(scope="module")
def arch_analyzer_binary(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output = tmp_path_factory.mktemp("structured-cli-go") / "arch-analyzer"
    subprocess.run(
        ["go", "build", "-o", str(output), "."],
        cwd=ROOT / "src/arch-analyzer",
        env={**os.environ, "GOCACHE": "/tmp/structured-component-go-cache"},
        check=True,
        capture_output=True,
        text=True,
    )
    return output


@pytest.fixture(scope="session")
def arch_query_binary(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output = tmp_path_factory.mktemp("structured-query-go") / "arch-query"
    subprocess.run(
        ["go", "build", "-o", str(output), "."],
        cwd=ROOT / "src/arch-query",
        env={**os.environ, "GOCACHE": "/tmp/structured-component-go-cache"},
        check=True,
        capture_output=True,
        text=True,
    )
    return output


def _pipeline_fixture(tmp_path: Path, versions: tuple[str, ...]):
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    _git(checkout, "init", "-q")
    _git(checkout, "config", "user.email", "offline@example.invalid")
    _git(checkout, "config", "user.name", "Offline Test")
    (checkout / "source.go").write_text("package source\n\nconst Enabled = true\n")
    _git(checkout, "add", "source.go")
    _git(checkout, "commit", "-qm", "source")
    architecture = tmp_path / "architecture"
    analyzer_template = json.loads((FIXTURES / "analyzer-rbac-praxis.json").read_text())
    component_map = json.loads((FIXTURES / "component-map-praxis.json").read_text())
    component_map["components"]["praxis-policy"].update(
        {
            "key": "praxis-policy",
            "checkout_path": str(checkout),
            "has_architecture": False,
        }
    )
    for version in versions:
        analyzer = copy.deepcopy(analyzer_template)
        analyzer["commit_sha"] = _git(checkout, "rev-parse", "HEAD")
        analyzer["extracted_at"] = f"2026-09-0{len(version)}T00:00:00Z"
        analyzer_dir = architecture / version / "praxis-policy" / ".analyzer"
        analyzer_dir.mkdir(parents=True)
        (analyzer_dir / "component-architecture.json").write_text(json.dumps(analyzer))
        platform_dir = architecture / version
        (platform_dir / "component-map.json").write_text(json.dumps(component_map))
    component = SimpleNamespace(
        key="praxis-policy",
        checkout_path=checkout,
        has_architecture=False,
    )
    return architecture, checkout, component


def _pipeline_inputs(
    path: Path, *, reuse_version: str | None = None, reuse_component="praxis-policy"
) -> Path:
    component = {
        "nominations": [
            {
                "path": "source.go",
                "start_line": 1,
                "end_line": 3,
                "justification": "Parent-supplied implementation evidence.",
            }
        ],
        "allowed_followup_paths": ["source.go"],
        "semantic_configuration": {"mode": "offline-contract"},
    }
    if reuse_version is not None:
        component["reuse_from"] = {
            "version_scope": reuse_version,
            "component": reuse_component,
        }
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "instructions": "Use only the bounded supplied evidence.",
                "components": {"praxis-policy": component},
            }
        )
    )
    return path


def _pipeline_args(
    *, platform: str, inputs: Path, platforms: Path, refresh: bool = False
):
    return SimpleNamespace(
        platform=platform,
        structured_inputs=str(inputs),
        structured_total_calls=1,
        structured_evidence_followups=0,
        structured_repairs=0,
        structured_refresh=refresh,
        platforms_file=str(platforms),
        overlays_dir=str(platforms.parent / "no-overlays"),
        harness="claude",
        model="offline-model",
        max_budget_usd=None,
        force=False,
        limit=None,
    )


async def _run_pipeline_fixture_version(
    *,
    architecture: Path,
    component: SimpleNamespace,
    version: str,
    inputs: Path,
    platforms: Path,
    refresh: bool = False,
    harness: str = "claude",
):
    args = _pipeline_args(
        platform=version, inputs=inputs, platforms=platforms, refresh=refresh
    )
    args.harness = harness
    await synthesis.run_pipeline_seam(
        args,
        {component.key: component},
        architecture_dir=architecture,
        distribution="RHOAI",
    )


def _private_dir(architecture: Path, version: str, component="praxis-policy") -> Path:
    return architecture / version / component / ".generation" / "structured"


@pytest.mark.parametrize(
    "legacy",
    [
        {"network_policies": [{"name": "deny"}]},
        {"platform_webhooks": [{"component": "a", "webhook": "b"}]},
        {"dockerfiles": [{"path": "Dockerfile", "stages": 2}]},
        {"webhooks": [{"name": "hook", "side_effects": "None"}]},
    ],
)
def test_legacy_conversion_rejects_unrepresentable_fields(legacy: dict) -> None:
    from lib.structured_component_publication import (
        PublicationError,
        validate_legacy_conversion_input,
    )

    with pytest.raises(PublicationError, match="would drop unsupported fields"):
        validate_legacy_conversion_input(legacy)


@pytest.mark.parametrize(
    "fips",
    [None, {}, "supported", [{"claim": "FIPS", "sources": []}]],
)
def test_legacy_conversion_rejects_ambiguous_fips(fips: object) -> None:
    from lib.structured_component_publication import (
        PublicationError,
        validate_legacy_conversion_input,
    )

    with pytest.raises(PublicationError, match="FIPS evidence.*ambiguous"):
        validate_legacy_conversion_input({"cross_cutting_evidence": {"fips": fips}})


def test_deterministic_only_publication_is_honest_and_zero_model(
    tmp_path: Path, arch_analyzer_binary: Path
) -> None:
    from lib.structured_component_publication import (
        load_accepted_publication,
        publish_deterministic_snapshot,
    )

    assembler = GoStructuredAssembler(
        (str(arch_analyzer_binary),), ROOT / "src/arch-analyzer"
    )
    document = tmp_path / "private-document.json"
    analyzer = FIXTURES / "analyzer-rbac-praxis.json"
    assembler._run(
        [
            "normalize",
            "--input",
            str(analyzer),
            "--output",
            str(document),
            "--component-map",
            str(FIXTURES / "component-map-praxis.json"),
            "--version-scope",
            "rhoai-test",
            "--integration-status",
            "not-integrated",
        ]
    )
    published = publish_deterministic_snapshot(
        architecture_dir=tmp_path / "architecture",
        version_scope="rhoai-test",
        component="praxis-policy",
        analyzer=analyzer.read_bytes(),
        private_document=document.read_bytes(),
        assembler=assembler,
        reason="synthesis deliberately unavailable in offline migration",
    )
    envelope = json.loads(published.synthesis)
    assert envelope["state"] == "deterministic-only"
    assert envelope["calls"]["total"] == 0
    assert envelope["responses"] == []
    binding = published.document_value["publication"]["synthesis"]
    assert not binding["producing_model_eligible"]
    assert "accepted_response_identity" not in binding
    load_accepted_publication(published.component_dir, assembler)
    assert {path.name for path in published.component_dir.iterdir()} == {
        "analyzer.json",
        "document.json",
        "synthesis.json",
    }
    assert published.markdown_path.is_file()


def _add_second_pipeline_component(
    architecture: Path,
    checkout: Path,
    inputs: Path,
    *,
    version: str,
    key: str = "second",
) -> SimpleNamespace:
    platform = architecture / version
    component_map_path = platform / "component-map.json"
    component_map = json.loads(component_map_path.read_text())
    component_map["components"][key] = {
        **component_map["components"]["praxis-policy"],
        "key": key,
    }
    component_map_path.write_text(json.dumps(component_map))
    first_analyzer = platform / "praxis-policy/.analyzer/component-architecture.json"
    second_analyzer = platform / key / ".analyzer/component-architecture.json"
    second_analyzer.parent.mkdir(parents=True)
    second_payload = json.loads(first_analyzer.read_text())
    second_payload["component"] = key
    second_analyzer.write_text(json.dumps(second_payload))
    inputs_payload = json.loads(inputs.read_text())
    inputs_payload["components"][key] = copy.deepcopy(
        inputs_payload["components"]["praxis-policy"]
    )
    inputs.write_text(json.dumps(inputs_payload))
    return SimpleNamespace(key=key, checkout_path=checkout, has_architecture=False)


_CODEX_RPC_LOOP_CASES = (
    pytest.param(
        {"codexErrorInfo": "usageLimitExceeded"},
        True,
        id="known-codex-error-info",
    ),
    pytest.param(
        {"codex_error_info": "sessionBudgetExceeded"},
        True,
        id="known-snake-error-info",
    ),
    pytest.param(
        {"errorInfo": "workspaceMemberUsageLimitReached"},
        True,
        id="sdk-error-info",
    ),
    pytest.param(
        "workspace_owner_usage_limit_reached",
        True,
        id="sdk-bare-data",
    ),
    pytest.param(
        {"codexErrorInfo": {"reason": "rate_limit_error"}},
        True,
        id="sdk-nested-info-value",
    ),
    pytest.param(
        {"codexErrorInfo": "internalServerError"},
        False,
        id="ordinary-server-control",
    ),
)


def _refresh_target_analyzer(
    architecture: Path,
    version: str,
    checkout: Path,
    **changes,
) -> None:
    path = (
        architecture
        / version
        / "praxis-policy"
        / ".analyzer"
        / "component-architecture.json"
    )
    analyzer = json.loads(path.read_text())
    analyzer["commit_sha"] = _git(checkout, "rev-parse", "HEAD")
    analyzer.update(changes)
    path.write_text(json.dumps(analyzer))


def _install_pipeline_adapter(monkeypatch, binary: Path, calls: list[str]):
    from lib import fetch

    def answer(prompt, *_):
        calls.append(prompt)
        return _response(prompt)

    async def ensure_analyzer():
        return str(binary)

    adapter = _adapter("claude", answer)
    monkeypatch.setattr(fetch, "_ensure_arch_analyzer", ensure_analyzer)
    monkeypatch.setattr(
        synthesis, "authenticated_harness_adapter", lambda _harness: adapter
    )
    return adapter


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["claude", "codex"])
async def test_one_json_response_success_through_both_adapters(tmp_path, kind):
    calls = []

    def answer(prompt, schema, model, settings):
        calls.append((prompt, schema, model, settings))
        return _response(prompt)

    result = await run_structured_synthesis(
        _request(tmp_path), _adapter(kind, answer), FakeAssembler()
    )

    assert result.state == "synthesized"
    assert result.calls == 1
    assert len(calls) == 1
    envelope = json.loads(result.envelope_path.read_text())
    assert envelope["calls"] == {
        "total": 1,
        "initial": 1,
        "evidence_followup": 0,
        "repair": 0,
        "limits": {"total": 3, "evidence_followup": 1, "repair": 1},
    }
    assert envelope["responses"][0]["raw_response"] == _response(calls[0][0])
    assert envelope["responses"][0]["parsed_payload"] is not None


@pytest.mark.asyncio
async def test_authenticated_claude_adapter_separates_primary_and_auxiliary_models(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    from lib import agent_runner

    captured = {}
    cli_identity = {
        "implementation": "claude-code-cli",
        "version_output": "offline-cli 1.0",
        "binary_sha256": "sha256:" + "1" * 64,
    }
    monkeypatch.setattr(
        agent_runner,
        "resolve_claude_cli_identity",
        lambda _path=None: ("/transport-blocked/claude", cli_identity),
    )

    async def transport(*args, **kwargs):
        captured.update(kwargs)
        raw = '{"ok":true}'
        return {
            "success": True,
            "raw_response": raw,
            "telemetry": {
                "requested_model_identity": "claude-opus-4-6",
                "response_models": ["claude-opus-4-6"],
                "model_usage": {
                    "claude-opus-4-6": {"output_tokens": 10},
                    "claude-haiku-4-5": {"output_tokens": 2},
                },
                "applied_model_settings": {"max_budget_usd": 2.0},
                "claude_cli_identity": cli_identity,
            },
        }

    monkeypatch.setattr(agent_runner, "run_agent", transport)
    response = await synthesis.authenticated_harness_adapter("claude").invoke(
        "{}",
        response_schema={"type": "object"},
        model="opus",
        settings={"max_budget_usd": 2.0},
    )

    assert response.requested_model_identity == "claude-opus-4-6"
    assert response.reported_model == "claude-opus-4-6"
    assert response.reported_settings == {"max_budget_usd": 2.0}
    assert response.auxiliary_models == ("claude-haiku-4-5",)
    assert captured["tool_free"] is True
    assert captured["max_turns"] == 1
    assert captured["claude_cli_path"] == "/transport-blocked/claude"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("case", "expected_state", "expected_calls"),
    [
        ("normal", "synthesized", 1),
        ("malformed-then-repair", "synthesized", 2),
        ("unresolved", "unresolved", 1),
    ],
)
async def test_authenticated_claude_factory_keeps_parent_response_control(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
    expected_state: str,
    expected_calls: int,
):
    """Use the real adapter factory with transport blocked before construction."""

    from lib import agent_runner

    cli_identity = {
        "implementation": "claude-code-cli",
        "version_output": "offline-cli 1.0",
        "binary_sha256": "sha256:" + "2" * 64,
    }
    monkeypatch.setattr(
        agent_runner,
        "resolve_claude_cli_identity",
        lambda _path=None: ("/transport-blocked/claude", cli_identity),
    )
    calls: list[dict] = []

    async def transport(*args, **kwargs):
        prompt = args[2]
        purpose = json.loads(prompt)["purpose"]
        calls.append({"purpose": purpose, **kwargs})
        if case == "malformed-then-repair" and len(calls) == 1:
            raw = "not-json"
        elif case == "unresolved":
            raw = _response(
                prompt,
                completion_status="unresolved",
                limitations=[
                    {
                        "code": "unknown-implementation",
                        "detail": "Evidence is insufficient.",
                    }
                ],
            )
        else:
            raw = _response(prompt)
        calls[-1]["raw"] = raw
        resolved = agent_runner.get_model_id(kwargs["model"])
        return {
            "success": True,
            "raw_response": raw,
            "telemetry": {
                "requested_model_identity": resolved,
                "response_models": [resolved],
                "model_usage": {
                    resolved: {"output_tokens": 1},
                    "claude-auxiliary": {"output_tokens": 1},
                },
                "applied_model_settings": {},
                "claude_cli_identity": cli_identity,
            },
        }

    monkeypatch.setattr(agent_runner, "run_agent", transport)
    adapter = synthesis.authenticated_harness_adapter("claude")
    result = await run_structured_synthesis(
        _request(
            tmp_path,
            model="opus",
            limits=SynthesisLimits(
                total_calls=2,
                evidence_followups=0,
                repairs=1,
            ),
        ),
        adapter,
        FakeAssembler(),
    )

    assert result.state == expected_state
    assert result.calls == expected_calls
    assert len(calls) == expected_calls
    assert all(call["tool_free"] is True for call in calls)
    assert all(call["max_turns"] == 1 for call in calls)
    assert all(call["response_schema"]["type"] == "object" for call in calls)
    envelope = json.loads(result.envelope_path.read_text())
    assert len(envelope["responses"]) == expected_calls
    assert [item["raw_response"] for item in envelope["responses"]] == [
        call["raw"] for call in calls
    ]
    model_context = json.loads(result.evidence_bundle_path.read_text())[
        "synthesis_configuration"
    ]["model_context"]
    assert model_context["implicit_context"]["requested_model_resolution"] == {
        "parent_requested_model": "opus",
        "resolved_model_identity": "claude-opus-4-6",
    }
    if case == "malformed-then-repair":
        assert envelope["responses"][0]["raw_response"] == "not-json"
        assert [call["purpose"] for call in calls] == ["initial", "repair"]
    if case == "unresolved":
        assert envelope["accepted_response_identity"] is not None


@pytest.mark.asyncio
async def test_rate_limit_refusal_is_durable_and_still_propagates(tmp_path: Path):
    async def refused(*_args, **_kwargs):
        raise RateLimitError("provider quota refused the bounded call")

    request = _request(
        tmp_path,
        limits=SynthesisLimits(total_calls=1, evidence_followups=0, repairs=0),
    )
    with pytest.raises(RateLimitError, match="provider quota refused"):
        await run_structured_synthesis(
            request,
            ClaudeStructuredAdapter(refused),
            FakeAssembler(),
        )

    envelope = json.loads((request.artifact_dir / "synthesis.json").read_text())
    assert envelope["state"] == "failed"
    assert envelope["calls"]["total"] == 0
    assert envelope["diagnostics"][-1] == {
        "code": "rate-limit-refusal",
        "detail": "provider quota refused the bounded call",
    }


@pytest.mark.asyncio
async def test_unknown_producing_model_is_audited_but_reuse_ineligible(tmp_path):
    async def caller(prompt, _schema, _model, settings):
        return HarnessResponse(
            raw_text=_response(prompt),
            reported_model=None,
            reported_settings=settings,
            requested_model_identity="offline-model",
            auxiliary_models=("auxiliary-observer",),
        )

    result = await run_structured_synthesis(
        _request(tmp_path), ClaudeStructuredAdapter(caller), FakeAssembler()
    )

    assert result.state == "synthesized"
    envelope = json.loads(result.envelope_path.read_text())
    assert envelope["reuse_eligibility"]["available"] is False
    assert envelope["responses"][0]["reported_model"] is None
    assert envelope["reported"]["auxiliary_models"] == ["auxiliary-observer"]


@pytest.mark.asyncio
async def test_followup_and_repair_accounting_stays_within_total_ceiling(tmp_path):
    seen = []

    def answer(prompt, *_):
        request = json.loads(prompt)
        seen.append(request["purpose"])
        if len(seen) == 1:
            return "not-json"
        if len(seen) == 2:
            return _response(
                prompt,
                completion_status="needs-evidence",
                evidence_requests=[
                    {
                        "request_id": "read-more",
                        "section_id": "multi-tenancy",
                        "path": "source.go",
                        "start_line": 2,
                        "end_line": 4,
                        "reason": "Resolve the nominated behavior.",
                    }
                ],
            )
        return _response(prompt)

    request = _request(
        tmp_path,
        limits=SynthesisLimits(total_calls=3, evidence_followups=1, repairs=1),
    )
    result = await run_structured_synthesis(
        request, _adapter("claude", answer), FakeAssembler()
    )

    assert result.state == "synthesized"
    assert seen == ["initial", "repair", "evidence-followup"]
    envelope = json.loads(result.envelope_path.read_text())
    assert envelope["calls"]["total"] == 3
    assert envelope["calls"]["repair"] == 1
    assert envelope["calls"]["evidence_followup"] == 1
    assert [item["ordinal"] for item in envelope["resolution_provenance"]] == list(
        range(1, len(envelope["resolution_provenance"]) + 1)
    )


@pytest.mark.asyncio
async def test_malformed_response_and_exhausted_repair_are_durable(tmp_path):
    request = _request(
        tmp_path,
        limits=SynthesisLimits(total_calls=1, evidence_followups=0, repairs=0),
    )
    result = await run_structured_synthesis(
        request, _adapter("claude", lambda *_: "# markdown"), FakeAssembler()
    )

    assert result.state == "failed"
    envelope = json.loads(result.envelope_path.read_text())
    assert envelope["responses"][0]["raw_response"] == "# markdown"
    assert envelope["responses"][0]["parsed_payload"] is None
    assert envelope["diagnostics"][-1]["code"] == "response-budget-exhausted"


def _unsafe_response(prompt: str, case: str) -> str:
    raw = _response(prompt)
    if case == "nan":
        return raw.replace('"sections":[]', '"sections":[NaN]')
    if case == "infinity":
        return raw.replace('"sections":[]', '"sections":[Infinity]')
    if case == "overflow":
        return raw.replace('"sections":[]', '"sections":[1e400]')
    if case == "surrogate":
        return raw.replace("response-01", "response-\ud800")
    if case == "nesting":
        return '{"nested":' + "[" * 65 + "0" + "]" * 65 + "}"
    raise AssertionError(case)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("case", "diagnostic"),
    [
        ("nan", "non-standard nonfinite number NaN"),
        ("infinity", "non-standard nonfinite number Infinity"),
        ("overflow", "nonfinite number 1e400"),
        ("surrogate", "unpaired surrogate"),
        ("nesting", "nesting exceeds configured maximum"),
    ],
)
async def test_pipeline_seam_retains_unsafe_answer_then_bounded_repair_succeeds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arch_analyzer_binary: Path,
    case: str,
    diagnostic: str,
):
    from lib import fetch

    architecture, _checkout, component = _pipeline_fixture(tmp_path, ("rhoai-test",))
    platforms = tmp_path / "platforms.yaml"
    platforms.write_text("rhoai-test: {}\n")
    attempts = []

    async def caller(prompt, _schema, model, settings):
        raw = _unsafe_response(prompt, case) if not attempts else _response(prompt)
        attempts.append(raw)
        return HarnessResponse(
            raw_text=raw,
            reported_model=model,
            reported_settings=settings,
            requested_model_identity=model,
            response_identity=None,
        )

    adapter = ClaudeStructuredAdapter(caller)

    async def ensure_analyzer():
        return str(arch_analyzer_binary)

    monkeypatch.setattr(fetch, "_ensure_arch_analyzer", ensure_analyzer)
    monkeypatch.setattr(
        synthesis, "authenticated_harness_adapter", lambda _harness: adapter
    )
    args = _pipeline_args(
        platform="rhoai-test",
        inputs=_pipeline_inputs(tmp_path / "inputs.json"),
        platforms=platforms,
    )
    args.structured_total_calls = 2
    args.structured_repairs = 1
    await synthesis.run_pipeline_seam(
        args,
        {component.key: component},
        architecture_dir=architecture,
        distribution="RHOAI",
    )

    target = _private_dir(architecture, "rhoai-test")
    envelope = json.loads((target / "synthesis.json").read_text())
    assert envelope["state"] == "synthesized"
    assert envelope["calls"]["total"] == 2
    assert len(envelope["responses"]) == 2
    assert diagnostic in envelope["responses"][0]["validation"]["error"]
    retained = envelope["responses"][0]["raw_response"]
    expected_hash = (
        content_hash(retained)
        if isinstance(retained, dict)
        else content_hash(retained.encode())
    )
    assert envelope["responses"][0]["raw_response_hash"] == expected_hash
    if case == "surrogate":
        decoded = base64.b64decode(retained["data"]).decode(
            "utf-8", errors="surrogatepass"
        )
        assert decoded == attempts[0]
    else:
        assert retained == attempts[0]
    assert (target / "run-record.json").is_file()


@pytest.mark.asyncio
async def test_malformed_typed_patch_fails_schema_and_retains_raw_response(tmp_path):
    def answer(prompt, *_):
        return _response(
            prompt,
            typed_patches=[
                {
                    "schema_version": "1.0.0",
                    "patch_id": "missing-bundle-binding",
                    "operations": [],
                }
            ],
        )

    request = _request(
        tmp_path,
        limits=SynthesisLimits(total_calls=1, evidence_followups=0, repairs=0),
    )
    result = await run_structured_synthesis(
        request, _adapter("claude", answer), FakeAssembler()
    )

    envelope = json.loads(result.envelope_path.read_text())
    assert result.state == "failed"
    assert envelope["responses"][0]["parsed_payload"] is None
    assert "bundle_fingerprint" in envelope["responses"][0]["validation"]["error"]
    assert json.loads(envelope["responses"][0]["raw_response"])["typed_patches"]


@pytest.mark.asyncio
async def test_exhausted_evidence_is_explicit_unresolved_without_omission(tmp_path):
    def answer(prompt, *_):
        return _response(
            prompt,
            completion_status="needs-evidence",
            evidence_requests=[
                {
                    "request_id": "more",
                    "section_id": "multi-tenancy",
                    "path": "source.go",
                    "start_line": 1,
                    "end_line": 2,
                    "reason": "Need explicit evidence.",
                }
            ],
        )

    request = _request(
        tmp_path,
        limits=SynthesisLimits(total_calls=1, evidence_followups=0, repairs=0),
    )
    result = await run_structured_synthesis(
        request, _adapter("claude", answer), FakeAssembler()
    )
    envelope = json.loads(result.envelope_path.read_text())
    assert result.state == "unresolved"
    assert envelope["diagnostics"][-1]["code"] == "evidence-budget-exhausted"
    assert envelope["resolution_provenance"][-1]["request_ids"] == ["more"]


@pytest.mark.asyncio
async def test_unknown_request_path_is_rejected_without_followup(tmp_path):
    def answer(prompt, *_):
        return _response(
            prompt,
            completion_status="needs-evidence",
            evidence_requests=[
                {
                    "request_id": "escape",
                    "section_id": "multi-tenancy",
                    "path": "unknown.go",
                    "start_line": 1,
                    "end_line": 2,
                    "reason": "Unknown source.",
                }
            ],
        )

    result = await run_structured_synthesis(
        _request(tmp_path), _adapter("codex", answer), FakeAssembler()
    )
    assert result.state == "unresolved"
    assert result.calls == 1
    envelope = json.loads(result.envelope_path.read_text())
    assert envelope["diagnostics"][-1]["code"] == "evidence-request-rejected"


@pytest.mark.asyncio
async def test_unknown_evidence_query_section_is_invalid_not_silently_followed(
    tmp_path,
):
    def answer(prompt, *_):
        return _response(
            prompt,
            completion_status="needs-evidence",
            evidence_requests=[
                {
                    "request_id": "unknown-query",
                    "section_id": "invented-section",
                    "path": "source.go",
                    "start_line": 1,
                    "end_line": 2,
                    "reason": "Unknown query must be rejected.",
                }
            ],
        )

    request = _request(
        tmp_path,
        limits=SynthesisLimits(total_calls=1, evidence_followups=0, repairs=0),
    )
    result = await run_structured_synthesis(
        request, _adapter("codex", answer), FakeAssembler()
    )

    assert result.state == "failed"
    envelope = json.loads(result.envelope_path.read_text())
    assert envelope["responses"][0]["parsed_payload"] is None
    assert "section_id" in envelope["responses"][0]["validation"]["error"]


@pytest.mark.parametrize(
    "nomination",
    [
        SourceNomination("../outside", 1, 1, "escape"),
        SourceNomination("source.go", 0, 1, "bad range"),
        SourceNomination("source.go", 1, 999, "bad range"),
    ],
)
def test_source_paths_and_ranges_are_parent_enforced(tmp_path, nomination):
    request = _request(tmp_path, nominations=(nomination,))
    with pytest.raises((EvidenceScopeError, FileNotFoundError)):
        synthesis.build_evidence_bundle(request, _adapter("claude", lambda *_: ""))


def test_symlink_evidence_is_rejected(tmp_path):
    request = _request(tmp_path)
    outside = tmp_path / "outside.go"
    outside.write_text("outside\n")
    link = request.checkout_root / "link.go"
    link.symlink_to(outside)
    changed = replace(
        request,
        nominations=(SourceNomination("link.go", 1, 1, "symlink"),),
        allowed_followup_paths=("link.go",),
    )
    with pytest.raises(EvidenceScopeError):
        synthesis.build_evidence_bundle(changed, _adapter("claude", lambda *_: ""))


def test_file_level_evidence_requires_parent_supplied_whole_file_range(tmp_path):
    request = _request(tmp_path)
    adapter = _adapter("claude", lambda *_: "")
    bundle, _, _, _ = synthesis.build_evidence_bundle(request, adapter)
    revision = bundle["analyzer"]["payload"]["commit_sha"]
    reference = {"path": "source.go", "revision": revision}

    assert synthesis._evidence_covers(reference, bundle["source_evidence"])

    partial = replace(
        request,
        nominations=(SourceNomination("source.go", 2, 4, "partial"),),
    )
    partial_bundle, _, _, _ = synthesis.build_evidence_bundle(partial, adapter)
    assert not synthesis._evidence_covers(reference, partial_bundle["source_evidence"])


def test_platform_only_integration_state_is_not_model_visible(tmp_path):
    request = _request(tmp_path)
    adapter = _adapter("claude", lambda *_: "")
    first, _, _, _ = synthesis.build_evidence_bundle(request, adapter)
    second, _, _, _ = synthesis.build_evidence_bundle(
        replace(request, integration_status="planned"), adapter
    )

    assert "integration_status" not in first["synthesis_configuration"]
    assert "component_map" not in first["synthesis_configuration"]
    assert first["bundle_identity"] == second["bundle_identity"]


def test_only_version_applicable_corrections_are_model_visible(tmp_path):
    request = _request(
        tmp_path,
        corrections=(
            {
                "version_scope": "other-version",
                "untrusted_out_of_scope_content": "must not be supplied",
            },
        ),
    )
    bundle, _, _, _ = synthesis.build_evidence_bundle(
        request, _adapter("claude", lambda *_: "")
    )

    assert bundle["corrections"] == []


def test_every_model_visible_instruction_configuration_and_context_is_identified(
    tmp_path,
):
    request = _request(tmp_path)
    first, _, first_context, complete = synthesis.build_evidence_bundle(
        request, _adapter("claude", lambda *_: "")
    )
    instructed, _, _, _ = synthesis.build_evidence_bundle(
        replace(request, instructions="Different bounded instruction."),
        _adapter("claude", lambda *_: ""),
    )
    configured, _, _, _ = synthesis.build_evidence_bundle(
        replace(request, semantic_configuration={"mode": "different"}),
        _adapter("claude", lambda *_: ""),
    )
    _, _, changed_context, _ = synthesis.build_evidence_bundle(
        request,
        _adapter(
            "claude",
            lambda *_: "",
            implicit_context={"test_transport": "different"},
        ),
    )

    assert complete is True
    assert first["bundle_identity"] != instructed["bundle_identity"]
    assert first["bundle_identity"] != configured["bundle_identity"]
    assert first_context != changed_context


@pytest.mark.asyncio
async def test_model_cannot_cite_unsupplied_evidence(tmp_path):
    def answer(prompt, *_):
        revision = json.loads(prompt)["evidence_bundle"]["analyzer"]["payload"][
            "commit_sha"
        ]
        return _response(
            prompt,
            sections=[
                {
                    "id": "multi-tenancy",
                    "status": "documented",
                    "blocks": [{"type": "paragraph", "text": "Bounded claim."}],
                    "evidence": [
                        {
                            "path": "not-supplied.go",
                            "start_line": 1,
                            "end_line": 1,
                            "revision": revision,
                        }
                    ],
                }
            ],
        )

    request = _request(
        tmp_path,
        limits=SynthesisLimits(total_calls=1, evidence_followups=0, repairs=0),
    )
    result = await run_structured_synthesis(
        request, _adapter("claude", answer), FakeAssembler()
    )
    assert result.state == "failed"
    assert "not supplied by parent" in result.diagnostics[0]["detail"]


@pytest.mark.asyncio
async def test_rejected_model_patch_is_retained_with_attributable_disposition(tmp_path):
    def answer(prompt, *_):
        request = json.loads(prompt)
        bundle = request["evidence_bundle"]
        revision = bundle["analyzer"]["payload"]["commit_sha"]
        patch = {
            "schema_version": "1.0.0",
            "patch_id": "model-service",
            "bundle_fingerprint": _analyzer_bundle_fingerprint(
                bundle["analyzer"]["payload"]
            ),
            "operations": [
                {
                    "operation_id": "add-api",
                    "action": "add",
                    "fact_type": "service",
                    "value": {
                        "name": "proposed-api",
                        "source": "source.go:1-3",
                        "type": "ClusterIP",
                        "ports": [],
                        "target_deployment": "proposed-api",
                    },
                    "evidence": [
                        {
                            "path": "source.go",
                            "start_line": 1,
                            "end_line": 3,
                            "revision": revision,
                        }
                    ],
                    "reason": "A bounded proposal that lacks trusted acceptance.",
                }
            ],
        }
        return _response(prompt, typed_patches=[patch])

    assembler = GoStructuredAssembler(("go", "run", "."), ROOT / "src/arch-analyzer")
    result = await run_structured_synthesis(
        _request(tmp_path), _adapter("claude", answer), assembler
    )
    assert result.state == "synthesized"
    document = json.loads(result.document_path.read_text())
    disposition = document["proposal_dispositions"][0]
    assert disposition["status"] == "rejected"
    assert disposition["origin_kind"] == "model"
    assert disposition["authorized_by"] == "structured-synthesis-parent"
    envelope = json.loads(result.envelope_path.read_text())
    assert (
        envelope["responses"][0]["parsed_payload"]["typed_patches"][0]
        == json.loads(envelope["responses"][0]["raw_response"])["typed_patches"][0]
    )


@pytest.mark.asyncio
async def test_response_payload_survives_disposable_log_removal(tmp_path):
    log_dir = tmp_path / "disposable-logs"
    log_dir.mkdir()
    (log_dir / "transport.log").write_text("not authoritative\n")

    result = await run_structured_synthesis(
        _request(tmp_path),
        _adapter("claude", lambda prompt, *_: _response(prompt)),
        FakeAssembler(),
    )
    expected = json.loads(result.envelope_path.read_text())["responses"][0]

    shutil.rmtree(log_dir)

    retained = json.loads(result.envelope_path.read_text())["responses"][0]
    assert retained == expected
    assert retained["raw_response_hash"] == content_hash(
        retained["raw_response"].encode()
    )
    assert retained["parsed_payload_hash"] == content_hash(retained["parsed_payload"])


@pytest.mark.asyncio
async def test_trusted_unresolved_section_reaches_document_without_omission(tmp_path):
    def answer(prompt, *_):
        bundle = json.loads(prompt)["evidence_bundle"]
        revision = bundle["analyzer"]["payload"]["commit_sha"]
        return _response(
            prompt,
            sections=[
                {
                    "id": "multi-tenancy",
                    "status": "unresolved",
                    "blocks": [],
                    "evidence": [
                        {
                            "path": "source.go",
                            "start_line": 1,
                            "end_line": 3,
                            "revision": revision,
                        }
                    ],
                    "uncertainty": "Tenant isolation remains unresolved.",
                }
            ],
        )

    section_policy = {
        "policy_id": "reviewed-sections",
        "version_scope": "rhoai-test",
        "decisions": {
            "multi-tenancy": {
                "decision": "accept",
                "decided_by": "offline-reviewer",
                "reason": "Explicit uncertainty and evidence were reviewed.",
                "origin": {
                    "kind": "model",
                    "id": "response-01",
                    "claim_class": "implementation",
                },
            }
        },
    }
    result = await run_structured_synthesis(
        _request(tmp_path, section_policy=section_policy),
        _adapter("claude", answer),
        GoStructuredAssembler(("go", "run", "."), ROOT / "src/arch-analyzer"),
    )

    assert result.state == "synthesized"
    document = json.loads(result.document_path.read_text())
    assert document["sections"][0]["status"] == "unresolved"
    assert document["sections"][0]["uncertainty"] == (
        "Tenant isolation remains unresolved."
    )
    markdown = result.markdown_path.read_text()
    assert "## Multi-Tenancy" in markdown
    assert "Tenant isolation remains unresolved." in markdown


@pytest.mark.asyncio
async def test_conflicting_section_authority_fails_without_self_authorization(tmp_path):
    def answer(prompt, *_):
        bundle = json.loads(prompt)["evidence_bundle"]
        revision = bundle["analyzer"]["payload"]["commit_sha"]
        evidence = [
            {
                "path": "source.go",
                "start_line": 1,
                "end_line": 3,
                "revision": revision,
            }
        ]
        return _response(
            prompt,
            sections=[
                {
                    "id": "security.fips-compliance",
                    "status": "documented",
                    "blocks": [{"type": "paragraph", "text": "First claim."}],
                    "evidence": evidence,
                },
                {
                    "id": "multi-tenancy",
                    "status": "documented",
                    "blocks": [{"type": "paragraph", "text": "Second claim."}],
                    "evidence": evidence,
                },
            ],
        )

    policy = {
        "policy_id": "trusted-sections",
        "version_scope": "rhoai-test",
        "decisions": {
            "security.fips-compliance": {
                "decision": "accept",
                "decided_by": "human-a",
                "reason": "reviewed",
                "origin": {
                    "kind": "model",
                    "id": "response-01",
                    "claim_class": "implementation",
                },
            },
            "multi-tenancy": {
                "decision": "accept",
                "decided_by": "human-b",
                "reason": "reviewed",
                "origin": {
                    "kind": "human-correction",
                    "id": "correction-1",
                    "claim_class": "correction",
                },
            },
        },
    }
    result = await run_structured_synthesis(
        _request(tmp_path, section_policy=policy),
        _adapter("claude", answer),
        FakeAssembler(),
    )
    assert result.state == "failed"
    assert result.diagnostics[-1]["code"] == "assembly-failed"


@pytest.mark.asyncio
async def test_immutable_analyzer_mutation_fails_and_restores_original(tmp_path):
    request = _request(tmp_path)
    original = request.analyzer_path.read_bytes()

    def mutate(prompt, *_):
        request.analyzer_path.write_text("mutated")
        return _response(prompt)

    result = await run_structured_synthesis(
        request, _adapter("claude", mutate), FakeAssembler()
    )
    assert result.state == "failed"
    assert request.analyzer_path.read_bytes() == original
    assert result.diagnostics[-1]["code"] == "immutable-input-mutated"


@pytest.mark.asyncio
async def test_reuse_hit_makes_zero_model_calls_and_preserves_synthesis_bytes(
    tmp_path, monkeypatch
):
    request = _request(tmp_path)
    target_document = tmp_path / "target.json"
    subprocess.run(
        [
            "go",
            "run",
            ".",
            "normalize",
            "--input",
            str(request.analyzer_path),
            "--component-map",
            str(request.component_map_path),
            "--version-scope",
            request.version_scope,
            "--output",
            str(target_document),
        ],
        cwd=ROOT / "src/arch-analyzer",
        env={**os.environ, "GOCACHE": "/tmp/structured-component-go-cache"},
        check=True,
        capture_output=True,
        text=True,
    )
    document = json.loads(target_document.read_text())
    original = json.dumps(
        special_synthesis_envelope(
            "historical-response-missing",
            input_bundle_identity="sha256:" + "a" * 64,
            reason="offline fixture",
        ),
        separators=(",", ":"),
    ).encode()
    target = SimpleNamespace(
        inputs=SimpleNamespace(
            exact="sha256:" + "b" * 64,
            semantic="sha256:" + "c" * 64,
        )
    )
    decision = ReuseDecision(
        True,
        (),
        {
            "prior_snapshot_id": "prior-1",
            "prior_platform": "rhoai-old",
            "target_platform": request.version_scope,
        },
    )
    resolution = ReuseResolution(
        reused=True,
        output=document,
        decision=decision,
        synthesis_bytes=original,
        response_identity="response-original",
        provenance={
            "prior_snapshot_id": "prior-1",
            "prior_platform": "rhoai-old",
            "target_platform": request.version_scope,
            "predecessor_document_integrity": content_hash(document),
            "synthesis_integrity": content_hash(original),
            "reason": "verified_semantic_and_dependency_match",
            "revalidation_checks": {
                "document_schema": True,
                "typed_references": True,
                "patch_policy": True,
                "current_acceptance_rules": True,
            },
        },
    )
    monkeypatch.setattr(synthesis, "resolve_or_synthesize", lambda *a, **k: resolution)
    calls = []
    changed = replace(
        request,
        prior_snapshot=SimpleNamespace(),
        reuse_target=target,
        revalidate_reuse=lambda *_: None,
    )
    result = await run_structured_synthesis(
        changed,
        _adapter("claude", lambda *_: calls.append(1) or ""),
        GoStructuredAssembler(("go", "run", "."), ROOT / "src/arch-analyzer"),
    )
    assert result.reused is True
    assert result.calls == 0
    assert calls == []
    assert result.envelope_path.read_bytes() == original
    reused = json.loads(result.document_path.read_text())
    assert reused["reuse"]["prior_snapshot_id"] == "prior-1"


@pytest.mark.asyncio
async def test_reuse_miss_takes_bounded_route_and_incomplete_context_forces_miss(
    tmp_path, monkeypatch
):
    captured = {}

    def resolve(*args, **kwargs):
        captured.update(kwargs)
        return ReuseResolution(
            reused=False,
            output=object(),
            decision=ReuseDecision(
                False,
                ("forced_refresh",),
                {"target_platform": "rhoai-test"},
            ),
        )

    monkeypatch.setattr(synthesis, "resolve_or_synthesize", resolve)
    calls = []
    adapter = _adapter(
        "claude",
        lambda prompt, *_: calls.append(prompt) or _response(prompt),
        context_complete=False,
        unobserved_context=("provider-system-instructions",),
    )
    request = replace(
        _request(tmp_path),
        prior_snapshot=SimpleNamespace(),
        reuse_target=SimpleNamespace(),
        revalidate_reuse=lambda *_: None,
    )

    result = await run_structured_synthesis(request, adapter, FakeAssembler())

    assert result.state == "synthesized"
    assert result.calls == 1
    assert len(calls) == 1
    assert captured["force_refresh"] is True
    envelope = json.loads(result.envelope_path.read_text())
    assert envelope["resolution_provenance"][0]["reasons"] == ["forced_refresh"]
    assert envelope["reuse_eligibility"]["available"] is False


def test_special_states_and_settings_constraints_are_explicit():
    for state in ("deterministic-only", "historical-response-missing"):
        envelope = special_synthesis_envelope(
            state,
            input_bundle_identity="sha256:" + "0" * 64,
            reason="fixture state",
        )
        assert envelope["state"] == state
        assert envelope["calls"]["total"] == 0
        assert envelope["responses"] == []
    with pytest.raises(ValueError, match="unsupported"):
        _validate_adapter_settings("codex", {"max_turns": 1})
    with pytest.raises(ValueError, match="positive"):
        _validate_adapter_settings("claude", {"max_budget_usd": 0})

    allowed_overage_telemetry = {
        "success": False,
        "provider_error": {
            "kind": "claude-result",
            "is_error": True,
            "result": "ordinary server failure",
            "rate_limit_events": [
                {
                    "status": "allowed_warning",
                    "overage_status": "rejected",
                    "raw": {"overage": {"status": "rejected"}},
                }
            ],
        },
    }
    assert synthesis._provider_rate_limit_denied(allowed_overage_telemetry) is False
    with pytest.raises(ValueError, match="must cover"):
        SynthesisLimits(total_calls=2, evidence_followups=1, repairs=1)


@pytest.mark.parametrize(
    ("rpc_data", "denied"),
    _CODEX_RPC_LOOP_CASES
    + (
        pytest.param(
            {"errorInfo": "unauthorized"},
            False,
            id="ordinary-auth-control",
        ),
        pytest.param(
            {"codex_error_info": "badRequest"},
            False,
            id="ordinary-config-control",
        ),
        pytest.param(
            {"errorInfo": "serverOverloaded"},
            False,
            id="ordinary-overload-control",
        ),
        pytest.param(
            "usage limit exceeded",
            False,
            id="bare-prose-control",
        ),
        pytest.param(
            {"message": "usageLimitExceeded"},
            False,
            id="message-field-control",
        ),
    ),
)
def test_codex_quota_classifiers_share_sdk_structural_boundaries(
    rpc_data: object,
    denied: bool,
):
    from openai_codex.errors import map_jsonrpc_error

    from lib import codex_agent

    provider_error = codex_agent.codex_exception_details(
        map_jsonrpc_error(-32000, "usageLimitExceeded", rpc_data)
    )

    assert codex_agent._codex_rate_limit_denied(provider_error) is denied
    assert (
        synthesis._provider_rate_limit_denied(
            {
                "success": False,
                "provider_error": provider_error,
            }
        )
        is denied
    )


def test_parent_input_schema_rejects_unknown_or_escaping_configuration(tmp_path):
    valid = tmp_path / "valid.json"
    valid.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "instructions": "bounded",
                "components": {"praxis-policy": {}},
            }
        )
    )
    assert synthesis._load_pipeline_inputs(valid)["instructions"] == "bounded"

    selected = json.loads(valid.read_text())
    selected["components"]["praxis-policy"]["reuse_from"] = {
        "version_scope": "rhoai-previous",
        "component": "policy",
    }
    valid.write_text(json.dumps(selected))
    assert synthesis._load_pipeline_inputs(valid)["components"]["praxis-policy"][
        "reuse_from"
    ] == {"version_scope": "rhoai-previous", "component": "policy"}

    invalid = tmp_path / "invalid.json"
    invalid.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "instructions": "bounded",
                "components": {
                    "praxis-policy": {"allowed_followup_paths": ["../escape"]}
                },
            }
        )
    )
    with pytest.raises(ValueError, match="validation failed"):
        synthesis._load_pipeline_inputs(invalid)

    selected["components"]["praxis-policy"]["reuse_from"]["component"] = "../policy"
    invalid.write_text(json.dumps(selected))
    with pytest.raises(ValueError, match="validation failed"):
        synthesis._load_pipeline_inputs(invalid)


@pytest.mark.asyncio
async def test_adapter_without_hard_tool_boundary_refuses_before_call():
    calls = []

    async def caller(*args):
        calls.append(args)
        return HarnessResponse("{}")

    adapter = CodexStructuredAdapter(caller, tool_free_enforced=False)
    with pytest.raises(AdapterCapabilityError):
        await adapter.invoke("{}", response_schema={}, model="m", settings={})
    assert calls == []


def test_new_schemas_are_valid_and_inline_controls_reject_at_schema():
    schemas, registry = synthesis._schemas()
    for name in (
        synthesis.RESPONSE_SCHEMA,
        synthesis.BUNDLE_SCHEMA,
        synthesis.ENVELOPE_SCHEMA,
        synthesis.INPUT_SCHEMA,
        synthesis.RUN_RECORD_SCHEMA,
        synthesis.DOCUMENT_SCHEMA,
    ):
        Draft202012Validator.check_schema(schemas[name])
    validator = Draft202012Validator(
        schemas[synthesis.RESPONSE_SCHEMA], registry=registry
    )
    payload = {
        "schema_version": "1.0.0",
        "response_id": "r",
        "input_bundle_identity": "sha256:" + "0" * 64,
        "completion_status": "complete",
        "sections": [
            {
                "id": "multi-tenancy",
                "status": "unresolved",
                "blocks": [{"type": "paragraph", "text": "unsafe\u001btext"}],
                "evidence": [{"path": "source.go", "revision": "rev"}],
                "uncertainty": "unsafe\u2028text",
            }
        ],
        "typed_patches": [],
        "limitations": [],
        "evidence_requests": [],
    }
    assert list(validator.iter_errors(payload))


@pytest.mark.asyncio
async def test_pipeline_seam_persists_reloads_and_reuses_with_actual_go(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arch_analyzer_binary: Path,
):
    from lib import fetch

    architecture, checkout, component = _pipeline_fixture(
        tmp_path, ("rhoai-old", "rhoai-new")
    )
    platforms = tmp_path / "platforms.yaml"
    platforms.write_text("rhoai-old: {}\nrhoai-new:\n  reuse_from: rhoai-old\n")
    old_inputs = _pipeline_inputs(tmp_path / "old-inputs.json")
    new_inputs = _pipeline_inputs(
        tmp_path / "new-inputs.json", reuse_version="rhoai-old"
    )
    calls: list[str] = []

    def answer(prompt, *_):
        calls.append(prompt)
        return _response(prompt)

    adapter = _adapter("claude", answer)

    async def ensure_analyzer():
        return str(arch_analyzer_binary)

    monkeypatch.setattr(fetch, "_ensure_arch_analyzer", ensure_analyzer)
    monkeypatch.setattr(
        synthesis, "authenticated_harness_adapter", lambda _harness: adapter
    )
    await synthesis.run_pipeline_seam(
        _pipeline_args(platform="rhoai-old", inputs=old_inputs, platforms=platforms),
        {"praxis-policy": component},
        architecture_dir=architecture,
        distribution="RHOAI",
    )
    old_dir = (
        architecture / "rhoai-old" / "praxis-policy" / ".generation" / "structured"
    )
    original_synthesis = (old_dir / "synthesis.json").read_bytes()
    assert (old_dir / "run-record.json").is_file()
    assert len(calls) == 1
    original_envelope = json.loads(original_synthesis)
    assert original_envelope["resolution_provenance"][0]["reasons"] == [
        "predecessor-not-supplied"
    ]

    (checkout / "irrelevant.txt").write_text("version refresh only\n")
    _git(checkout, "add", "irrelevant.txt")
    _git(checkout, "commit", "-qm", "irrelevant version refresh")
    new_analyzer_path = (
        architecture
        / "rhoai-new"
        / "praxis-policy"
        / ".analyzer"
        / "component-architecture.json"
    )
    new_analyzer = json.loads(new_analyzer_path.read_text())
    new_analyzer["commit_sha"] = _git(checkout, "rev-parse", "HEAD")
    new_analyzer["extracted_at"] = "2026-09-08T01:02:03Z"
    new_analyzer["scan_statistics"] = [{"metric": "refresh", "value": 1}]
    new_analyzer_path.write_text(json.dumps(new_analyzer))
    new_map_path = architecture / "rhoai-new" / "component-map.json"
    new_map = json.loads(new_map_path.read_text())
    new_map["components"]["praxis-policy"]["integration_status"] = "current"
    new_map["components"]["praxis-policy"]["target_release"] = "rhoai-new"
    new_map_path.write_text(json.dumps(new_map))

    await synthesis.run_pipeline_seam(
        _pipeline_args(platform="rhoai-new", inputs=new_inputs, platforms=platforms),
        {"praxis-policy": component},
        architecture_dir=architecture,
        distribution="RHOAI",
    )
    new_dir = (
        architecture / "rhoai-new" / "praxis-policy" / ".generation" / "structured"
    )
    assert len(calls) == 1
    assert (new_dir / "synthesis.json").read_bytes() == original_synthesis
    document = json.loads((new_dir / "document.json").read_text())
    assert document["reuse"]["prior_platform"] == "rhoai-old"
    assert document["identity"]["integration_status"] == "current"
    assert document["identity"]["source_revision"] == new_analyzer["commit_sha"]
    record = json.loads((new_dir / "run-record.json").read_text())
    assert record["state"] == "completed"
    assert record["artifacts"]["synthesis_bundle"]["path"] == (
        "synthesis-evidence-bundle.json"
    )
    synthesis.PrivateRunRecordStore(
        architecture,
        synthesis.GoStructuredAssembler(
            (str(arch_analyzer_binary),), ROOT / "src/arch-analyzer"
        ),
    ).load("rhoai-new", "praxis-policy")


@pytest.mark.asyncio
async def test_published_core_survives_private_state_removal_and_reuses(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arch_analyzer_binary: Path,
    arch_query_binary: Path,
):
    from lib import fetch
    from lib.structured_component_publication import (
        PublicationError,
        load_accepted_publication,
    )

    architecture, checkout, component = _pipeline_fixture(
        tmp_path, ("rhoai-old", "rhoai-new")
    )
    platforms = tmp_path / "platforms.yaml"
    platforms.write_text("rhoai-old: {}\nrhoai-new:\n  reuse_from: rhoai-old\n")
    calls: list[str] = []

    def answer(prompt, *_):
        calls.append(prompt)
        return _response(prompt)

    async def ensure_analyzer():
        return str(arch_analyzer_binary)

    monkeypatch.setattr(fetch, "_ensure_arch_analyzer", ensure_analyzer)
    monkeypatch.setattr(
        synthesis,
        "authenticated_harness_adapter",
        lambda _harness: _adapter("claude", answer),
    )
    await _run_pipeline_fixture_version(
        architecture=architecture,
        component=component,
        version="rhoai-old",
        inputs=_pipeline_inputs(tmp_path / "old-inputs.json"),
        platforms=platforms,
    )
    component_dir = architecture / "rhoai-old" / "praxis-policy"
    assembler = GoStructuredAssembler(
        (str(arch_analyzer_binary),), ROOT / "src/arch-analyzer"
    )
    published = load_accepted_publication(component_dir, assembler)
    original_synthesis = published.synthesis
    query = subprocess.run(
        [
            str(arch_query_binary),
            "--base-dir",
            str(architecture),
            "--version",
            "rhoai-old",
            "component",
            "praxis-policy",
            "--output",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(query.stdout)["name"] == "praxis-policy"
    markdown = architecture / "rhoai-old" / "praxis-policy.md"
    marker, body = markdown.read_bytes().split(b"\n", 1)
    markdown.write_bytes(marker + b"\nTAMPERED\n" + body)
    with pytest.raises(PublicationError, match="stale, or tampered"):
        load_accepted_publication(component_dir, assembler)
    load_accepted_publication(component_dir, assembler, repair_markdown=True)
    shutil.rmtree(component_dir / ".generation")

    (checkout / "irrelevant.txt").write_text("new release only\n")
    _git(checkout, "add", "irrelevant.txt")
    _git(checkout, "commit", "-qm", "new release")
    _refresh_target_analyzer(
        architecture,
        "rhoai-new",
        checkout,
        extracted_at="2026-09-08T05:00:00Z",
    )
    await _run_pipeline_fixture_version(
        architecture=architecture,
        component=component,
        version="rhoai-new",
        inputs=_pipeline_inputs(
            tmp_path / "new-inputs.json", reuse_version="rhoai-old"
        ),
        platforms=platforms,
    )
    assert len(calls) == 1
    target = load_accepted_publication(
        architecture / "rhoai-new" / "praxis-policy", assembler
    )
    assert target.synthesis == original_synthesis
    assert target.document_value["reuse"]["prior_platform"] == "rhoai-old"
    assert target.document_value["publication"]["accepted_inputs"]["run_record"][
        "dependencies"
    ]["complete"]

    original_document = (target.component_dir / "document.json").read_bytes()
    forged = json.loads(original_document)
    forged["publication"]["analyzer"]["producer_build_identity"] = (
        "sha256:" + "0" * 64
    )
    (target.component_dir / "document.json").write_text(json.dumps(forged))
    with pytest.raises(PublicationError, match="build differs"):
        load_accepted_publication(target.component_dir, assembler)
    (target.component_dir / "document.json").write_bytes(original_document)

    forged = json.loads(original_document)
    forged["identity"]["aliases"] = ["self-asserted-alias"]
    (target.component_dir / "document.json").write_text(json.dumps(forged))
    with pytest.raises(PublicationError, match="originally accepted model"):
        load_accepted_publication(target.component_dir, assembler)
    (target.component_dir / "document.json").write_bytes(original_document)


@pytest.mark.asyncio
async def test_failed_synthesis_cannot_replace_prior_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arch_analyzer_binary: Path,
):
    from lib import fetch
    from lib.structured_component_publication import load_accepted_publication

    architecture, checkout, component = _pipeline_fixture(tmp_path, ("rhoai-test",))
    platforms = tmp_path / "platforms.yaml"
    platforms.write_text("rhoai-test: {}\n")

    async def ensure_analyzer():
        return str(arch_analyzer_binary)

    monkeypatch.setattr(fetch, "_ensure_arch_analyzer", ensure_analyzer)
    monkeypatch.setattr(
        synthesis,
        "authenticated_harness_adapter",
        lambda _harness: _adapter("claude", lambda prompt, *_: _response(prompt)),
    )
    inputs = _pipeline_inputs(tmp_path / "inputs.json")
    await _run_pipeline_fixture_version(
        architecture=architecture,
        component=component,
        version="rhoai-test",
        inputs=inputs,
        platforms=platforms,
    )
    assembler = GoStructuredAssembler(
        (str(arch_analyzer_binary),), ROOT / "src/arch-analyzer"
    )
    component_dir = architecture / "rhoai-test" / "praxis-policy"
    prior = load_accepted_publication(component_dir, assembler)
    (checkout / "source.go").write_text("package source\n\nconst Broken = true\n")
    _git(checkout, "add", "source.go")
    _git(checkout, "commit", "-qm", "new input before failed synthesis")
    _refresh_target_analyzer(
        architecture,
        "rhoai-test",
        checkout,
        extracted_at="2026-09-08T07:00:00Z",
    )
    failing = _adapter(
        "claude",
        lambda *_: (_ for _ in ()).throw(
            StructuredSynthesisError("offline synthesis failure")
        ),
    )
    monkeypatch.setattr(
        synthesis, "authenticated_harness_adapter", lambda _harness: failing
    )
    await _run_pipeline_fixture_version(
        architecture=architecture,
        component=component,
        version="rhoai-test",
        inputs=inputs,
        platforms=platforms,
        refresh=True,
    )
    current = load_accepted_publication(component_dir, assembler)
    assert current.document == prior.document
    assert current.synthesis == prior.synthesis


def test_recovery_discards_incomplete_first_atomic_temporary(tmp_path: Path):
    from lib import structured_component_publication as publication

    component_dir = tmp_path / "architecture/rhoai-test/praxis-policy"
    component_dir.mkdir(parents=True)
    temporary = component_dir / ".analyzer.json.interrupted"
    temporary.write_text("partial write")

    assert publication.recover_publication(component_dir, FakeAssembler()) is None
    assert not temporary.exists()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "boundary",
    [
        "staged:analyzer.json",
        "staged:synthesis.json",
        "staged:document.json",
        "staged:praxis-policy.md",
        "staged",
        "backed-up:analyzer.json",
        "backed-up:synthesis.json",
        "backed-up:document.json",
        "backed-up:praxis-policy.md",
        "replaced:analyzer.json",
        "replaced:synthesis.json",
        "replaced:document.json",
        "replaced:praxis-policy.md",
    ],
)
@pytest.mark.parametrize("replacement", [False, True], ids=["first", "replacement"])
async def test_publication_recovers_every_replacement_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arch_analyzer_binary: Path,
    boundary: str,
    replacement: bool,
):
    from lib import fetch
    from lib import structured_component_publication as publication

    architecture, checkout, component = _pipeline_fixture(tmp_path, ("rhoai-test",))
    platforms = tmp_path / "platforms.yaml"
    platforms.write_text("rhoai-test: {}\n")
    calls: list[str] = []

    def answer(prompt, *_):
        calls.append(prompt)
        return _response(prompt)

    async def ensure_analyzer():
        return str(arch_analyzer_binary)

    monkeypatch.setattr(fetch, "_ensure_arch_analyzer", ensure_analyzer)
    monkeypatch.setattr(
        synthesis,
        "authenticated_harness_adapter",
        lambda _harness: _adapter("claude", answer),
    )
    inputs = _pipeline_inputs(tmp_path / "inputs.json")
    await _run_pipeline_fixture_version(
        architecture=architecture,
        component=component,
        version="rhoai-test",
        inputs=inputs,
        platforms=platforms,
    )
    assembler = GoStructuredAssembler(
        (str(arch_analyzer_binary),), ROOT / "src/arch-analyzer"
    )
    component_dir = architecture / "rhoai-test" / "praxis-policy"
    prior = publication.load_accepted_publication(component_dir, assembler)

    if not replacement:
        for path in (
            component_dir / "analyzer.json",
            component_dir / "synthesis.json",
            component_dir / "document.json",
            component_dir.parent / "praxis-policy.md",
        ):
            path.unlink()
        with pytest.raises(publication.PublicationError, match="incomplete"):
            publication.load_accepted_publication(component_dir, assembler)
        with pytest.raises(
            publication.PublicationError, match="simulated interruption"
        ):
            publication.publish_private_run(
                architecture_dir=architecture,
                version_scope="rhoai-test",
                component="praxis-policy",
                assembler=assembler,
                interrupt_after=boundary,
            )
        recovered = publication.recover_publication(component_dir, assembler)
        if boundary in {"staged:analyzer.json", "staged:synthesis.json"}:
            assert recovered is None
            assert not (component_dir / "document.json").exists()
            return
        assert recovered is not None
        assert publication.load_accepted_publication(component_dir, assembler)
        return

    (checkout / "source.go").write_text("package source\n\nconst Enabled = false\n")
    _git(checkout, "add", "source.go")
    _git(checkout, "commit", "-qm", "change accepted input")
    _refresh_target_analyzer(
        architecture,
        "rhoai-test",
        checkout,
        extracted_at="2026-09-08T06:00:00Z",
    )
    real_publish = publication.publish_private_run
    monkeypatch.setattr(publication, "publish_private_run", lambda **_kwargs: None)
    await _run_pipeline_fixture_version(
        architecture=architecture,
        component=component,
        version="rhoai-test",
        inputs=inputs,
        platforms=platforms,
        refresh=True,
    )
    monkeypatch.setattr(publication, "publish_private_run", real_publish)
    with pytest.raises(publication.PublicationError, match="simulated interruption"):
        real_publish(
            architecture_dir=architecture,
            version_scope="rhoai-test",
            component="praxis-policy",
            assembler=assembler,
            interrupt_after=boundary,
        )
    recovered = publication.recover_publication(component_dir, assembler)
    assert recovered is not None
    validated = publication.load_accepted_publication(component_dir, assembler)
    assert validated.document == recovered.document
    if boundary in {"replaced:document.json", "replaced:praxis-policy.md"}:
        assert validated.document != prior.document
    else:
        assert validated.document == prior.document


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("change", "expected_reason"),
    [
        ("evidence", "semantic_input_mismatch"),
        ("configuration", "semantic_input_mismatch"),
        ("observations", "semantic_input_mismatch"),
        ("excerpt-range", "semantic_input_mismatch"),
        ("component-map", "semantic_input_mismatch"),
        ("compatibility", "producer_or_contract_mismatch"),
        ("refresh", "explicit_refresh"),
    ],
)
async def test_pipeline_seam_reuse_misses_are_bounded_and_explicit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arch_analyzer_binary: Path,
    change: str,
    expected_reason: str,
):
    architecture, checkout, component = _pipeline_fixture(
        tmp_path, ("rhoai-old", "rhoai-new")
    )
    platforms = tmp_path / "platforms.yaml"
    platforms.write_text("rhoai-old: {}\nrhoai-new:\n  reuse_from: rhoai-old\n")
    old_inputs = _pipeline_inputs(tmp_path / "old-inputs.json")
    new_inputs = _pipeline_inputs(
        tmp_path / "new-inputs.json", reuse_version="rhoai-old"
    )
    calls: list[str] = []
    _install_pipeline_adapter(monkeypatch, arch_analyzer_binary, calls)
    await _run_pipeline_fixture_version(
        architecture=architecture,
        component=component,
        version="rhoai-old",
        inputs=old_inputs,
        platforms=platforms,
    )
    if change == "evidence":
        (checkout / "source.go").write_text("package source\n\nconst Enabled = false\n")
        _git(checkout, "add", "source.go")
        _git(checkout, "commit", "-qm", "changed evidence")
        _refresh_target_analyzer(architecture, "rhoai-new", checkout)
    elif change == "configuration":
        payload = json.loads(new_inputs.read_text())
        payload["components"]["praxis-policy"]["semantic_configuration"]["mode"] = (
            "changed"
        )
        new_inputs.write_text(json.dumps(payload))
    elif change == "observations":
        payload = json.loads(new_inputs.read_text())
        payload["components"]["praxis-policy"]["observations"] = {
            "parent-visible-feature": "changed"
        }
        new_inputs.write_text(json.dumps(payload))
    elif change == "excerpt-range":
        payload = json.loads(new_inputs.read_text())
        payload["components"]["praxis-policy"]["nominations"][0]["end_line"] = 2
        new_inputs.write_text(json.dumps(payload))
    elif change == "component-map":
        component_map_path = architecture / "rhoai-new" / "component-map.json"
        component_map = json.loads(component_map_path.read_text())
        component_map["components"]["praxis-policy"]["type"] = "changed-type"
        component_map_path.write_text(json.dumps(component_map))
    elif change == "compatibility":
        _refresh_target_analyzer(
            architecture,
            "rhoai-new",
            checkout,
            analyzer_version="0.2.0-incompatible",
        )
    await _run_pipeline_fixture_version(
        architecture=architecture,
        component=component,
        version="rhoai-new",
        inputs=new_inputs,
        platforms=platforms,
        refresh=change == "refresh",
    )
    assert len(calls) == 2
    envelope = json.loads(
        (_private_dir(architecture, "rhoai-new") / "synthesis.json").read_text()
    )
    assert expected_reason in envelope["resolution_provenance"][0]["reasons"]
    assert envelope["calls"]["total"] == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "record_case",
    [
        "missing",
        "tampered",
        "tampered-response",
        "producer-model-mismatch",
        "producer-settings-mismatch",
        "producer-ineligible",
        "malformed",
        "inconsistent",
        "renderer-inconsistent",
        "failed",
    ],
)
async def test_pipeline_seam_never_accepts_unusable_predecessor_records(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arch_analyzer_binary: Path,
    record_case: str,
):
    architecture, _checkout, component = _pipeline_fixture(
        tmp_path, ("rhoai-old", "rhoai-new")
    )
    platforms = tmp_path / "platforms.yaml"
    platforms.write_text("rhoai-old: {}\nrhoai-new:\n  reuse_from: rhoai-old\n")
    old_inputs = _pipeline_inputs(tmp_path / "old-inputs.json")
    new_inputs = _pipeline_inputs(
        tmp_path / "new-inputs.json", reuse_version="rhoai-old"
    )
    calls: list[str] = []
    _install_pipeline_adapter(monkeypatch, arch_analyzer_binary, calls)
    if record_case != "missing":
        if record_case == "failed":
            failing = _adapter(
                "claude",
                lambda *_: (_ for _ in ()).throw(
                    StructuredSynthesisError("offline failure")
                ),
            )
            monkeypatch.setattr(
                synthesis,
                "authenticated_harness_adapter",
                lambda _harness: failing,
            )
            await _run_pipeline_fixture_version(
                architecture=architecture,
                component=component,
                version="rhoai-old",
                inputs=old_inputs,
                platforms=platforms,
            )
            assert not (
                _private_dir(architecture, "rhoai-old") / "run-record.json"
            ).exists()
            _install_pipeline_adapter(monkeypatch, arch_analyzer_binary, calls)
        else:
            await _run_pipeline_fixture_version(
                architecture=architecture,
                component=component,
                version="rhoai-old",
                inputs=old_inputs,
                platforms=platforms,
            )
            predecessor = _private_dir(architecture, "rhoai-old")
            record_path = predecessor / "run-record.json"
            if record_case == "tampered":
                document = predecessor / "document.json"
                document.write_bytes(document.read_bytes() + b" ")
            elif record_case == "tampered-response":
                response = predecessor / "synthesis.json"
                response.write_bytes(response.read_bytes() + b" ")
            elif record_case.startswith("producer-"):
                response = predecessor / "synthesis.json"
                envelope = json.loads(response.read_text())
                if record_case == "producer-model-mismatch":
                    envelope["responses"][0]["reported_model"] = "other-model"
                elif record_case == "producer-settings-mismatch":
                    envelope["responses"][0]["reported_settings"] = {
                        "reasoning_effort": "low"
                    }
                else:
                    envelope["reuse_eligibility"] = {
                        "available": False,
                        "reason": "producer-unknown",
                        "unobserved_context": ["reported-model-or-settings"],
                    }
                response.write_text(json.dumps(envelope))
                record = json.loads(record_path.read_text())
                record["artifacts"]["synthesis"]["content_hash"] = content_hash(
                    response.read_bytes()
                )
                record["snapshot_id"] = content_hash(
                    {
                        "version_scope": "rhoai-old",
                        "component": "praxis-policy",
                        "document": record["artifacts"]["document"]["content_hash"],
                        "synthesis": record["artifacts"]["synthesis"]["content_hash"],
                    }
                )
                record["record_identity"] = content_hash(
                    synthesis._record_without_identity(record)
                )
                record_path.write_text(json.dumps(record))
            elif record_case == "malformed":
                record_path.write_text("{")
            else:
                record = json.loads(record_path.read_text())
                if record_case == "inconsistent":
                    record["response_identity"] = "inconsistent-response"
                else:
                    markdown = predecessor / "candidate.md"
                    markdown.write_text(markdown.read_text() + "tampered\n")
                    record["artifacts"]["markdown"]["content_hash"] = content_hash(
                        markdown.read_bytes()
                    )
                record["record_identity"] = content_hash(
                    synthesis._record_without_identity(record)
                )
                record_path.write_text(json.dumps(record))
            # This P3 regression exercises an unusable predecessor with no
            # independently accepted P4 authority.  A valid published snapshot
            # is deliberately covered by the publication-removal reuse test.
            published = architecture / "rhoai-old" / "praxis-policy"
            for path in (
                published / "analyzer.json",
                published / "synthesis.json",
                published / "document.json",
                architecture / "rhoai-old" / "praxis-policy.md",
            ):
                path.unlink(missing_ok=True)
    await _run_pipeline_fixture_version(
        architecture=architecture,
        component=component,
        version="rhoai-new",
        inputs=new_inputs,
        platforms=platforms,
    )
    envelope = json.loads(
        (_private_dir(architecture, "rhoai-new") / "synthesis.json").read_text()
    )
    assert envelope["resolution_provenance"][0]["reasons"] == [
        "predecessor-record-invalid"
    ]
    assert envelope["calls"]["total"] == 1
    assert (_private_dir(architecture, "rhoai-new") / "run-record.json").is_file()


@pytest.mark.asyncio
async def test_pipeline_seam_alias_selection_and_repository_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arch_analyzer_binary: Path,
):
    architecture, _checkout, old_component = _pipeline_fixture(
        tmp_path, ("rhoai-old", "rhoai-new")
    )
    platforms = tmp_path / "platforms.yaml"
    platforms.write_text("rhoai-old: {}\nrhoai-new:\n  reuse_from: rhoai-old\n")
    calls: list[str] = []
    _install_pipeline_adapter(monkeypatch, arch_analyzer_binary, calls)
    await _run_pipeline_fixture_version(
        architecture=architecture,
        component=old_component,
        version="rhoai-old",
        inputs=_pipeline_inputs(tmp_path / "old-inputs.json"),
        platforms=platforms,
    )
    new_platform = architecture / "rhoai-new"
    component_map = json.loads((new_platform / "component-map.json").read_text())
    raw = component_map["components"].pop("praxis-policy")
    raw["key"] = "policy"
    component_map["components"]["policy"] = raw
    (new_platform / "component-map.json").write_text(json.dumps(component_map))
    old_analyzer_dir = new_platform / "praxis-policy" / ".analyzer"
    new_analyzer_dir = new_platform / "policy" / ".analyzer"
    new_analyzer_dir.parent.mkdir(parents=True)
    old_analyzer_dir.rename(new_analyzer_dir)
    alias_inputs = _pipeline_inputs(
        tmp_path / "alias-inputs.json", reuse_version="rhoai-old"
    )
    payload = json.loads(alias_inputs.read_text())
    payload["components"]["policy"] = payload["components"].pop("praxis-policy")
    alias_inputs.write_text(json.dumps(payload))
    alias_component = SimpleNamespace(
        key="policy",
        checkout_path=old_component.checkout_path,
        has_architecture=False,
    )
    await _run_pipeline_fixture_version(
        architecture=architecture,
        component=alias_component,
        version="rhoai-new",
        inputs=alias_inputs,
        platforms=platforms,
    )
    assert len(calls) == 1
    alias_document = json.loads(
        (
            _private_dir(architecture, "rhoai-new", "policy") / "document.json"
        ).read_text()
    )
    assert alias_document["identity"]["component"] == "policy"
    assert alias_document["reuse"]["prior_platform"] == "rhoai-old"

    wrong_map = json.loads((new_platform / "component-map.json").read_text())
    del wrong_map["components"]["policy"]
    wrong_map["components"]["praxis-policy"] = raw
    (new_platform / "component-map.json").write_text(json.dumps(wrong_map))
    wrong_analyzer = json.loads(
        (new_analyzer_dir / "component-architecture.json").read_text()
    )
    wrong_analyzer["repo"] = "https://example.invalid/different/repository"
    wrong_dir = new_platform / "praxis-policy" / ".analyzer"
    wrong_dir.parent.mkdir(parents=True, exist_ok=True)
    wrong_dir.mkdir(exist_ok=True)
    (wrong_dir / "component-architecture.json").write_text(json.dumps(wrong_analyzer))
    with pytest.raises(ReuseRecordError, match="different repository"):
        await _run_pipeline_fixture_version(
            architecture=architecture,
            component=old_component,
            version="rhoai-new",
            inputs=_pipeline_inputs(
                tmp_path / "wrong-inputs.json", reuse_version="rhoai-old"
            ),
            platforms=platforms,
        )


@pytest.mark.asyncio
async def test_pipeline_seam_rebinds_typed_proposal_and_trusted_policy_copies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arch_analyzer_binary: Path,
):
    from lib import fetch

    architecture, checkout, component = _pipeline_fixture(
        tmp_path, ("rhoai-old", "rhoai-new")
    )
    platforms = tmp_path / "platforms.yaml"
    platforms.write_text("rhoai-old: {}\nrhoai-new:\n  reuse_from: rhoai-old\n")
    old_inputs = _pipeline_inputs(tmp_path / "old-inputs.json")
    old_analyzer = json.loads(
        (
            architecture
            / "rhoai-old"
            / "praxis-policy"
            / ".analyzer"
            / "component-architecture.json"
        ).read_text()
    )
    patch = {
        "schema_version": "1.0.0",
        "patch_id": "reviewed-service",
        "bundle_fingerprint": _analyzer_bundle_fingerprint(old_analyzer),
        "operations": [
            {
                "operation_id": "add-reviewed-service",
                "action": "add",
                "fact_type": "service",
                "value": {
                    "name": "reviewed-service",
                    "source": "source.go:1-3",
                    "type": "ClusterIP",
                    "ports": [],
                    "target_deployment": "reviewed-service",
                },
                "evidence": [
                    {
                        "path": "source.go",
                        "start_line": 1,
                        "end_line": 3,
                        "revision": old_analyzer["commit_sha"],
                    }
                ],
                "reason": "Offline reviewed typed proposal.",
            }
        ],
    }
    policy = {
        "schema_version": "1.0.0",
        "policy_id": "offline-reviewed-policy",
        "patch_id": patch["patch_id"],
        "proposal_fingerprint": synthesis._proposal_fingerprint(patch),
        "bundle_fingerprint": patch["bundle_fingerprint"],
        "version_scope": "rhoai-old",
        "origin": {
            "kind": "model",
            "id": "response-01",
            "claim_class": "implementation",
        },
        "authority": {
            "actor": "offline-reviewer",
            "allowed_fact_types": ["service"],
        },
        "decisions": [
            {
                "decision_id": "accept-reviewed-service",
                "operation_id": "add-reviewed-service",
                "decision": "accept",
                "decided_by": "offline-reviewer",
                "reason": "Bounded fixture acceptance.",
            }
        ],
    }
    for inputs_path in (old_inputs,):
        value = json.loads(inputs_path.read_text())
        value["components"]["praxis-policy"]["assembly_policies"] = [policy]
        inputs_path.write_text(json.dumps(value))
    new_inputs = _pipeline_inputs(
        tmp_path / "new-inputs.json", reuse_version="rhoai-old"
    )
    value = json.loads(new_inputs.read_text())
    value["components"]["praxis-policy"]["assembly_policies"] = [policy]
    new_inputs.write_text(json.dumps(value))
    calls: list[str] = []

    def answer(prompt, *_):
        calls.append(prompt)
        return _response(prompt, typed_patches=[patch])

    async def ensure_analyzer():
        return str(arch_analyzer_binary)

    monkeypatch.setattr(fetch, "_ensure_arch_analyzer", ensure_analyzer)
    monkeypatch.setattr(
        synthesis,
        "authenticated_harness_adapter",
        lambda _harness: _adapter("claude", answer),
    )
    await _run_pipeline_fixture_version(
        architecture=architecture,
        component=component,
        version="rhoai-old",
        inputs=old_inputs,
        platforms=platforms,
    )
    predecessor_bytes = (
        _private_dir(architecture, "rhoai-old") / "synthesis.json"
    ).read_bytes()
    (checkout / "irrelevant.txt").write_text("new release only\n")
    _git(checkout, "add", "irrelevant.txt")
    _git(checkout, "commit", "-qm", "new release")
    _refresh_target_analyzer(
        architecture,
        "rhoai-new",
        checkout,
        extracted_at="2026-09-08T04:00:00Z",
    )
    await _run_pipeline_fixture_version(
        architecture=architecture,
        component=component,
        version="rhoai-new",
        inputs=new_inputs,
        platforms=platforms,
    )
    target = _private_dir(architecture, "rhoai-new")
    assert len(calls) == 1
    assert (target / "synthesis.json").read_bytes() == predecessor_bytes
    document = json.loads((target / "document.json").read_text())
    accepted = [
        item
        for item in document["proposal_dispositions"]
        if item["operation_id"] == "add-reviewed-service"
    ]
    assert accepted[0]["status"] == "accepted"
    assert accepted[0]["evidence"][0]["revision"] == _git(checkout, "rev-parse", "HEAD")
    record = json.loads((target / "run-record.json").read_text())
    binding = record["target_rebindings"][0]
    assert binding["kind"] == "typed-proposal-target-binding"
    assert binding["policy_id"] == "offline-reviewed-policy"
    assert binding["authority_source"] == "trusted-current-parent-input"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "platform_yaml",
    [
        "rhoai-old: {}\nrhoai-new:\n  reuse_from: rhoai-new\n",
        "rhoai-old:\n  reuse_from: rhoai-new\nrhoai-new:\n  reuse_from: rhoai-old\n",
    ],
)
async def test_pipeline_seam_rejects_self_and_cycle_before_model_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arch_analyzer_binary: Path,
    platform_yaml: str,
):
    architecture, _checkout, component = _pipeline_fixture(tmp_path, ("rhoai-new",))
    platforms = tmp_path / "platforms.yaml"
    platforms.write_text(platform_yaml)
    calls: list[str] = []
    _install_pipeline_adapter(monkeypatch, arch_analyzer_binary, calls)
    inputs = _pipeline_inputs(tmp_path / "inputs.json", reuse_version="rhoai-old")
    with pytest.raises(ReuseConfigurationError):
        await _run_pipeline_fixture_version(
            architecture=architecture,
            component=component,
            version="rhoai-new",
            inputs=inputs,
            platforms=platforms,
        )
    assert calls == []


@pytest.mark.asyncio
async def test_pipeline_seam_production_adapters_use_bounded_transport_stubs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arch_analyzer_binary: Path,
):
    from lib import codex_agent, fetch

    production_factory = synthesis.authenticated_harness_adapter
    architecture, _checkout, component = _pipeline_fixture(
        tmp_path, ("rhoai-old", "rhoai-new")
    )
    platforms = tmp_path / "platforms.yaml"
    platforms.write_text("rhoai-old: {}\nrhoai-new:\n  reuse_from: rhoai-old\n")
    calls: list[str] = []
    _install_pipeline_adapter(monkeypatch, arch_analyzer_binary, calls)
    await _run_pipeline_fixture_version(
        architecture=architecture,
        component=component,
        version="rhoai-old",
        inputs=_pipeline_inputs(tmp_path / "old-inputs.json"),
        platforms=platforms,
    )

    async def ensure_analyzer():
        return str(arch_analyzer_binary)

    monkeypatch.setattr(fetch, "_ensure_arch_analyzer", ensure_analyzer)
    from lib import agent_runner

    local_transport_calls = []
    codex_context = {
        "protocol": codex_agent._CODEX_CONTEXT_PROTOCOL,
        "parent_requested_model": "offline-model",
        "selection_mode": "explicit",
        "resolved_model_identity": "offline-model",
        "model_provider": "openai",
        "reasoning_effort": "high",
        "service_tier": None,
        "sandbox": {"type": "readOnly"},
        "approval_policy": {"type": "never"},
        "provider_model_fallback_allowed": False,
        "cli_implementation": {
            "implementation": "codex-cli",
            "version_output": "codex-cli transport-blocked",
            "binary_sha256": "sha256:" + "a" * 64,
        },
        "isolated_local_context": {
            "effective_config_identity": "sha256:" + "b" * 64,
        },
        "context_identity": "sha256:" + "c" * 64,
    }

    async def offline_preflight(model):
        assert model == "offline-model"
        return copy.deepcopy(codex_context)

    async def offline_transport(*args, **kwargs):
        local_transport_calls.append((args, kwargs))
        raw = _response(args[2])
        requested = codex_context["resolved_model_identity"]
        return {
            "success": True,
            "raw_response": raw,
            "telemetry": {
                "requested_model_identity": requested,
                "response_models": [requested],
                "model_usage": {requested: {"input_tokens": 1}},
                "applied_model_settings": {
                    "model_provider": "openai",
                    "reasoning_effort": "high",
                    "service_tier": None,
                },
                "codex_structured_context": copy.deepcopy(codex_context),
            },
        }

    monkeypatch.setattr(agent_runner, "run_agent", offline_transport)
    monkeypatch.setattr(
        codex_agent,
        "preflight_structured_codex_context",
        offline_preflight,
    )
    monkeypatch.setattr(synthesis, "authenticated_harness_adapter", production_factory)
    await _run_pipeline_fixture_version(
        architecture=architecture,
        component=component,
        version="rhoai-new",
        inputs=_pipeline_inputs(
            tmp_path / "new-inputs.json", reuse_version="rhoai-old"
        ),
        platforms=platforms,
        harness="codex",
    )
    target = _private_dir(architecture, "rhoai-new")
    envelope = json.loads((target / "synthesis.json").read_text())
    assert envelope["reuse_eligibility"]["available"] is True
    assert "semantic_input_mismatch" in envelope["resolution_provenance"][0]["reasons"]
    assert envelope["calls"]["total"] == 1
    assert (target / "run-record.json").is_file()
    assert len(local_transport_calls) == 1
    assert local_transport_calls[0][1]["tool_free"] is True
    assert local_transport_calls[0][1]["response_schema"]["type"] == "object"
    production_claude = production_factory("claude")
    assert production_claude.context_complete is True
    assert production_claude.unobserved_context == ()


def _install_production_codex_protocol_stub(monkeypatch, state, captured):
    """Block transport before SDK construction while retaining real wire types."""

    from openai_codex.generated import v2_all as codex_types
    from openai_codex.models import Notification

    from lib import codex_agent

    def maybe_raise(stage, occurrence):
        failures = state.get("rpc_failures")
        if failures is None:
            failures = (state.get("rpc_failure"),)
        for failure in failures:
            if (
                isinstance(failure, dict)
                and failure.get("stage") == stage
                and failure.get("occurrence") == occurrence
            ):
                raise failure["error"]

    class FakeTurn:
        def __init__(self, prompt):
            self.id = f"turn-{len(captured['turns']) + 1}"
            self.prompt = prompt

        async def interrupt(self):
            captured["interrupts"] += 1

        async def stream(self):
            answer = codex_types.ThreadItem(
                root=codex_types.AgentMessageThreadItem(
                    id=f"answer-{self.id}",
                    phase="final_answer",
                    text=_response(self.prompt),
                    type="agentMessage",
                )
            )
            yield Notification(
                method="item/completed",
                payload=codex_types.ItemCompletedNotification(
                    item=answer,
                    thread_id="thread-stub",
                    turn_id=self.id,
                    completed_at_ms=1,
                ),
            )
            yield Notification(
                method="turn/completed",
                payload=codex_types.TurnCompletedNotification(
                    thread_id="thread-stub",
                    turn=codex_types.Turn(
                        id=self.id,
                        items=[answer],
                        items_view=codex_types.TurnItemsView.full,
                        status=codex_types.TurnStatus.completed,
                    ),
                ),
            )

    class FakeThread:
        def __init__(self, _codex, thread_id):
            self.id = thread_id

        async def turn(self, prompt, **kwargs):
            captured["turns"].append({"prompt": prompt, "kwargs": kwargs})
            maybe_raise("turn/start", len(captured["turns"]))
            return FakeTurn(prompt)

    class FakeProtocol:
        async def request(self, method, params, *, response_model):
            assert method == "config/read"
            captured["config_reads"].append(copy.deepcopy(params))
            maybe_raise("config/read", len(captured["config_reads"]))
            return codex_types.ConfigReadResponse(
                config={
                    "model": state["resolved_model"],
                    "model_provider": state["model_provider"],
                    "model_reasoning_effort": state["reasoning_effort"],
                    "service_tier": state["service_tier"],
                    "test_context_revision": state["config_revision"],
                },
                layers=[],
                origins={},
            )

        async def thread_start(self, params):
            captured["thread_starts"].append(copy.deepcopy(params))
            maybe_raise("thread/start", len(captured["thread_starts"]))
            return SimpleNamespace(
                thread=SimpleNamespace(id="thread-stub"),
                model=state["resolved_model"],
                model_provider=state["model_provider"],
                reasoning_effort=state["reasoning_effort"],
                service_tier=state["service_tier"],
                instruction_sources=[],
                runtime_workspace_roots=[],
                sandbox={"type": "readOnly"},
                approval_policy={"type": "never"},
            )

    class FakeCodex:
        def __init__(self, config=None):
            captured["constructors"].append(config)
            self._client = FakeProtocol()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

    def resolve_cli():
        return (
            "/transport-blocked/codex",
            {
                "implementation": "codex-cli",
                "version_output": state["cli_version"],
                "binary_sha256": "sha256:" + state["cli_hash"] * 64,
            },
        )

    def isolated(private_home, *, cli_path):
        staged = {
            "model": state["configured_model"],
            "model_reasoning_effort": state["reasoning_effort"],
        }
        return (
            codex_agent.CodexConfig(
                codex_bin=cli_path,
                env={"CODEX_HOME": str(private_home)},
            ),
            {
                "protocol": codex_agent._CODEX_CONTEXT_PROTOCOL,
                "auth_route": "transport-blocked-existing-auth",
                "staged_model_config": staged,
                "staged_model_config_identity": content_hash(staged),
                "suppressed_local_sources": ["memories", "plugins"],
                "environment_access": "disabled-by-empty-thread-environments",
            },
        )

    monkeypatch.setattr(codex_agent, "AsyncCodex", FakeCodex)
    monkeypatch.setattr(codex_agent, "AsyncThread", FakeThread)
    monkeypatch.setattr(codex_agent, "resolve_codex_cli_identity", resolve_cli)
    monkeypatch.setattr(codex_agent, "_isolated_codex_config", isolated)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("parent_model", "change", "expected_target_turns"),
    [
        ("gpt-5.6-sol", "none", 0),
        (None, "none", 0),
        (None, "model", 1),
        ("gpt-5.6-sol", "effort", 1),
        ("gpt-5.6-sol", "provider", 1),
        ("gpt-5.6-sol", "service-tier", 1),
        ("gpt-5.6-sol", "config", 1),
        ("gpt-5.6-sol", "cli", 1),
    ],
)
async def test_production_codex_preflight_controls_actual_go_reuse(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arch_analyzer_binary: Path,
    parent_model: str | None,
    change: str,
    expected_target_turns: int,
):
    from lib import fetch

    architecture, checkout, component = _pipeline_fixture(
        tmp_path, ("rhoai-old", "rhoai-new")
    )
    platforms = tmp_path / "platforms.yaml"
    platforms.write_text("rhoai-old: {}\nrhoai-new:\n  reuse_from: rhoai-old\n")
    state = {
        "configured_model": "gpt-default-a",
        "resolved_model": parent_model or "gpt-default-a",
        "model_provider": "openai",
        "reasoning_effort": "high",
        "service_tier": "priority",
        "config_revision": "a",
        "cli_version": "codex-cli 0.147.0-test",
        "cli_hash": "a",
    }
    captured = {
        "constructors": [],
        "config_reads": [],
        "thread_starts": [],
        "turns": [],
        "interrupts": 0,
    }
    _install_production_codex_protocol_stub(monkeypatch, state, captured)

    async def ensure_analyzer():
        return str(arch_analyzer_binary)

    monkeypatch.setattr(fetch, "_ensure_arch_analyzer", ensure_analyzer)
    old_args = _pipeline_args(
        platform="rhoai-old",
        inputs=_pipeline_inputs(tmp_path / "old-inputs.json"),
        platforms=platforms,
    )
    old_args.harness = "codex"
    old_args.model = parent_model
    await synthesis.run_pipeline_seam(
        old_args,
        {component.key: component},
        architecture_dir=architecture,
        distribution="RHOAI",
    )
    assert len(captured["turns"]) == 1

    (checkout / "irrelevant.txt").write_text("new release only\n")
    _git(checkout, "add", "irrelevant.txt")
    _git(checkout, "commit", "-qm", "irrelevant release")
    _refresh_target_analyzer(
        architecture,
        "rhoai-new",
        checkout,
        extracted_at="2026-09-08T18:00:00Z",
    )
    if change == "model":
        state["configured_model"] = "gpt-default-b"
        state["resolved_model"] = "gpt-default-b"
    elif change == "effort":
        state["reasoning_effort"] = "xhigh"
    elif change == "provider":
        state["model_provider"] = "alternate-provider"
    elif change == "service-tier":
        state["service_tier"] = "flex"
    elif change == "config":
        state["config_revision"] = "b"
    elif change == "cli":
        state["cli_version"] = "codex-cli 0.147.0-test-changed"
        state["cli_hash"] = "b"

    before_target = len(captured["turns"])
    target_args = _pipeline_args(
        platform="rhoai-new",
        inputs=_pipeline_inputs(
            tmp_path / "new-inputs.json", reuse_version="rhoai-old"
        ),
        platforms=platforms,
    )
    target_args.harness = "codex"
    target_args.model = parent_model
    await synthesis.run_pipeline_seam(
        target_args,
        {component.key: component},
        architecture_dir=architecture,
        distribution="RHOAI",
    )

    assert len(captured["turns"]) - before_target == expected_target_turns
    target = _private_dir(architecture, "rhoai-new")
    envelope = json.loads((target / "synthesis.json").read_text())
    bundle = json.loads((target / "evidence-bundle.json").read_text())
    resolution = bundle["synthesis_configuration"]["model_context"]["implicit_context"][
        "requested_model_resolution"
    ]
    assert resolution["parent_requested_model"] == parent_model
    assert resolution["resolved_model_identity"] == state["resolved_model"]
    assert all(
        start["allowProviderModelFallback"] is False
        and start["dynamicTools"] == []
        and start["environments"] == []
        for start in captured["thread_starts"]
    )
    if parent_model is None:
        assert all("model" not in start for start in captured["thread_starts"])
    if expected_target_turns == 0:
        assert envelope["state"] == "synthesized"
        assert envelope["calls"]["total"] == 1
        document = json.loads((target / "document.json").read_text())
        assert "reuse" in document
    else:
        assert (
            "semantic_input_mismatch" in envelope["resolution_provenance"][0]["reasons"]
        )
        assert envelope["calls"]["total"] == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("resolved_model", "model_provider", "message"),
    [
        ("gpt-5.6-mini", "openai", "requested/resolved model mismatch"),
        ("", "openai", "did not report a resolved model"),
        ("gpt-5.6-sol", "", "did not report a resolved model provider"),
    ],
)
async def test_production_codex_preflight_fails_before_any_model_turn(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arch_analyzer_binary: Path,
    resolved_model: str,
    model_provider: str,
    message: str,
):
    from lib import fetch

    architecture, _checkout, component = _pipeline_fixture(tmp_path, ("rhoai-test",))
    platforms = tmp_path / "platforms.yaml"
    platforms.write_text("rhoai-test: {}\n")
    state = {
        "configured_model": "gpt-5.6-sol",
        "resolved_model": resolved_model,
        "model_provider": model_provider,
        "reasoning_effort": "high",
        "service_tier": None,
        "config_revision": "a",
        "cli_version": "codex-cli 0.147.0-test",
        "cli_hash": "a",
    }
    captured = {
        "constructors": [],
        "config_reads": [],
        "thread_starts": [],
        "turns": [],
        "interrupts": 0,
    }
    _install_production_codex_protocol_stub(monkeypatch, state, captured)

    async def ensure_analyzer():
        return str(arch_analyzer_binary)

    monkeypatch.setattr(fetch, "_ensure_arch_analyzer", ensure_analyzer)
    args = _pipeline_args(
        platform="rhoai-test",
        inputs=_pipeline_inputs(tmp_path / "inputs.json"),
        platforms=platforms,
    )
    args.harness = "codex"
    args.model = "gpt-5.6-sol"

    with pytest.raises(RuntimeError, match=message):
        await synthesis.run_pipeline_seam(
            args,
            {component.key: component},
            architecture_dir=architecture,
            distribution="RHOAI",
        )

    assert captured["turns"] == []
    assert len(captured["thread_starts"]) == 1
    assert not _private_dir(architecture, "rhoai-test").exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("stage", ["config/read", "thread/start"])
@pytest.mark.parametrize(("rpc_data", "denied"), _CODEX_RPC_LOOP_CASES)
async def test_codex_preflight_rpc_quota_is_durable_without_component_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arch_analyzer_binary: Path,
    stage: str,
    rpc_data: object,
    denied: bool,
):
    from openai_codex.errors import map_jsonrpc_error

    from lib import fetch

    architecture, checkout, first = _pipeline_fixture(tmp_path, ("rhoai-test",))
    inputs = _pipeline_inputs(tmp_path / "inputs.json")
    second = _add_second_pipeline_component(
        architecture, checkout, inputs, version="rhoai-test"
    )
    platforms = tmp_path / "platforms.yaml"
    platforms.write_text("rhoai-test: {}\n")
    fake_bearer = "sk-abcdefghijklmnopqrstuvwxyz0123"
    rpc_error = map_jsonrpc_error(
        -32000,
        f"usage limit wording is not sufficient; Bearer {fake_bearer}",
        rpc_data,
    )
    state = {
        "configured_model": "gpt-5.6-sol",
        "resolved_model": "gpt-5.6-sol",
        "model_provider": "openai",
        "reasoning_effort": "high",
        "service_tier": None,
        "config_revision": "a",
        "cli_version": "codex-cli 0.147.0-test",
        "cli_hash": "a",
        "rpc_failure": {"stage": stage, "occurrence": 1, "error": rpc_error},
    }
    captured = {
        "constructors": [],
        "config_reads": [],
        "thread_starts": [],
        "turns": [],
        "interrupts": 0,
    }
    _install_production_codex_protocol_stub(monkeypatch, state, captured)

    async def ensure_analyzer():
        return str(arch_analyzer_binary)

    monkeypatch.setattr(fetch, "_ensure_arch_analyzer", ensure_analyzer)
    args = _pipeline_args(platform="rhoai-test", inputs=inputs, platforms=platforms)
    args.harness = "codex"
    args.model = "gpt-5.6-sol"
    run = synthesis.run_pipeline_seam(
        args,
        {first.key: first, second.key: second},
        architecture_dir=architecture,
        distribution="RHOAI",
    )
    if denied:
        with pytest.raises(RateLimitError):
            await run
    else:
        with pytest.raises(Exception) as raised:
            await run
        assert raised.value is rpc_error

    diagnostic_path = (
        architecture
        / "rhoai-test/.generation/structured"
        / synthesis.PREFLIGHT_DIAGNOSTIC_FILENAME
    )
    assert diagnostic_path.exists() is denied
    if denied:
        diagnostic = json.loads(diagnostic_path.read_text())
        assert diagnostic["phase"] == "context-preflight"
        assert diagnostic["model_calls_started"] == 0
        assert diagnostic["diagnostic"]["provider_error"]["code"] == -32000
        assert diagnostic["diagnostic"]["provider_error"]["data"] == rpc_data
        diagnostic_text = diagnostic_path.read_text()
        assert fake_bearer not in diagnostic_text
        assert "Bearer [REDACTED]" in diagnostic["diagnostic"]["detail"]
    assert captured["turns"] == []
    for component in (first, second):
        target = _private_dir(architecture, "rhoai-test", component.key)
        assert not (target / "synthesis.json").exists()
        assert not (target / "run-record.json").exists()


@pytest.mark.asyncio
async def test_codex_preflight_diagnostic_write_failure_still_stops_pipeline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arch_analyzer_binary: Path,
):
    from openai_codex.errors import map_jsonrpc_error

    from lib import fetch

    architecture, checkout, first = _pipeline_fixture(tmp_path, ("rhoai-test",))
    inputs = _pipeline_inputs(tmp_path / "inputs.json")
    second = _add_second_pipeline_component(
        architecture, checkout, inputs, version="rhoai-test"
    )
    platforms = tmp_path / "platforms.yaml"
    platforms.write_text("rhoai-test: {}\n")
    state = {
        "configured_model": "gpt-5.6-sol",
        "resolved_model": "gpt-5.6-sol",
        "model_provider": "openai",
        "reasoning_effort": "high",
        "service_tier": None,
        "config_revision": "a",
        "cli_version": "codex-cli 0.147.0-test",
        "cli_hash": "a",
        "rpc_failure": {
            "stage": "config/read",
            "occurrence": 1,
            "error": map_jsonrpc_error(
                -32000,
                "quota",
                {"errorInfo": "usageLimitExceeded"},
            ),
        },
    }
    captured = {
        "constructors": [],
        "config_reads": [],
        "thread_starts": [],
        "turns": [],
        "interrupts": 0,
    }
    _install_production_codex_protocol_stub(monkeypatch, state, captured)

    async def ensure_analyzer():
        return str(arch_analyzer_binary)

    real_atomic_json = synthesis._atomic_json

    def fail_preflight_diagnostic(path, value):
        if path.name == synthesis.PREFLIGHT_DIAGNOSTIC_FILENAME:
            raise OSError(28, "simulated full diagnostic volume")
        return real_atomic_json(path, value)

    monkeypatch.setattr(fetch, "_ensure_arch_analyzer", ensure_analyzer)
    monkeypatch.setattr(synthesis, "_atomic_json", fail_preflight_diagnostic)
    args = _pipeline_args(platform="rhoai-test", inputs=inputs, platforms=platforms)
    args.harness = "codex"
    args.model = "gpt-5.6-sol"

    with pytest.raises(OSError) as raised:
        await synthesis.run_pipeline_seam(
            args,
            {first.key: first, second.key: second},
            architecture_dir=architecture,
            distribution="RHOAI",
        )

    assert isinstance(raised.value.__context__, RateLimitError)
    assert len(captured["config_reads"]) == 1
    assert captured["thread_starts"] == []
    assert captured["turns"] == []
    for component in (first, second):
        target = _private_dir(architecture, "rhoai-test", component.key)
        assert not (target / "synthesis.json").exists()
        assert not (target / "run-record.json").exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("stage", ["config/read", "thread/start", "turn/start"])
@pytest.mark.parametrize(("rpc_data", "denied"), _CODEX_RPC_LOOP_CASES)
async def test_producing_rpc_quota_stops_actual_two_component_loop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arch_analyzer_binary: Path,
    stage: str,
    rpc_data: object,
    denied: bool,
):
    from openai_codex.errors import map_jsonrpc_error

    from lib import fetch

    architecture, checkout, first = _pipeline_fixture(tmp_path, ("rhoai-test",))
    inputs = _pipeline_inputs(tmp_path / "inputs.json")
    second = _add_second_pipeline_component(
        architecture, checkout, inputs, version="rhoai-test"
    )
    platforms = tmp_path / "platforms.yaml"
    platforms.write_text("rhoai-test: {}\n")
    rpc_error = map_jsonrpc_error(
        -32000,
        "ordinary provider wording",
        rpc_data,
    )
    state = {
        "configured_model": "gpt-5.6-sol",
        "resolved_model": "gpt-5.6-sol",
        "model_provider": "openai",
        "reasoning_effort": "high",
        "service_tier": None,
        "config_revision": "a",
        "cli_version": "codex-cli 0.147.0-test",
        "cli_hash": "a",
        "rpc_failure": {
            "stage": stage,
            "occurrence": 1 if stage == "turn/start" else 2,
            "error": rpc_error,
        },
    }
    captured = {
        "constructors": [],
        "config_reads": [],
        "thread_starts": [],
        "turns": [],
        "interrupts": 0,
    }
    _install_production_codex_protocol_stub(monkeypatch, state, captured)

    async def ensure_analyzer():
        return str(arch_analyzer_binary)

    monkeypatch.setattr(fetch, "_ensure_arch_analyzer", ensure_analyzer)
    args = _pipeline_args(platform="rhoai-test", inputs=inputs, platforms=platforms)
    args.harness = "codex"
    args.model = "gpt-5.6-sol"
    run = synthesis.run_pipeline_seam(
        args,
        {first.key: first, second.key: second},
        architecture_dir=architecture,
        distribution="RHOAI",
    )
    if denied:
        with pytest.raises(RateLimitError):
            await run
    else:
        await run

    first_target = _private_dir(architecture, "rhoai-test", first.key)
    first_envelope = json.loads((first_target / "synthesis.json").read_text())
    expected_code = "rate-limit-refusal" if denied else "adapter-failed"
    assert first_envelope["diagnostics"][-1]["code"] == expected_code
    provider_error = first_envelope["diagnostics"][-1]["provider_error"]
    assert provider_error["code"] == -32000
    assert provider_error["data"] == rpc_data
    assert not (first_target / "run-record.json").exists()
    second_target = _private_dir(architecture, "rhoai-test", second.key)
    assert (second_target / "synthesis.json").exists() is (not denied)
    assert (second_target / "run-record.json").exists() is (not denied)
    expected_turns = {
        ("config/read", True): 0,
        ("thread/start", True): 0,
        ("turn/start", True): 1,
        ("config/read", False): 1,
        ("thread/start", False): 1,
        ("turn/start", False): 2,
    }
    assert len(captured["turns"]) == expected_turns[(stage, denied)]


@pytest.mark.asyncio
async def test_ordinary_rpc_failure_then_quota_never_starts_third_component(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arch_analyzer_binary: Path,
):
    from openai_codex.errors import map_jsonrpc_error

    from lib import fetch

    architecture, checkout, first = _pipeline_fixture(tmp_path, ("rhoai-test",))
    inputs = _pipeline_inputs(tmp_path / "inputs.json")
    second = _add_second_pipeline_component(
        architecture, checkout, inputs, version="rhoai-test"
    )
    third = _add_second_pipeline_component(
        architecture,
        checkout,
        inputs,
        version="rhoai-test",
        key="third",
    )
    platforms = tmp_path / "platforms.yaml"
    platforms.write_text("rhoai-test: {}\n")
    state = {
        "configured_model": "gpt-5.6-sol",
        "resolved_model": "gpt-5.6-sol",
        "model_provider": "openai",
        "reasoning_effort": "high",
        "service_tier": None,
        "config_revision": "a",
        "cli_version": "codex-cli 0.147.0-test",
        "cli_hash": "a",
        "rpc_failures": (
            {
                "stage": "turn/start",
                "occurrence": 1,
                "error": map_jsonrpc_error(
                    -32000,
                    "ordinary failure",
                    {"codexErrorInfo": "internalServerError"},
                ),
            },
            {
                "stage": "turn/start",
                "occurrence": 2,
                "error": map_jsonrpc_error(
                    -32000,
                    "quota",
                    {"errorInfo": "usageLimitExceeded"},
                ),
            },
        ),
    }
    captured = {
        "constructors": [],
        "config_reads": [],
        "thread_starts": [],
        "turns": [],
        "interrupts": 0,
    }
    _install_production_codex_protocol_stub(monkeypatch, state, captured)

    async def ensure_analyzer():
        return str(arch_analyzer_binary)

    monkeypatch.setattr(fetch, "_ensure_arch_analyzer", ensure_analyzer)
    args = _pipeline_args(platform="rhoai-test", inputs=inputs, platforms=platforms)
    args.harness = "codex"
    args.model = "gpt-5.6-sol"

    with pytest.raises(RateLimitError):
        await synthesis.run_pipeline_seam(
            args,
            {item.key: item for item in (first, second, third)},
            architecture_dir=architecture,
            distribution="RHOAI",
        )

    assert len(captured["turns"]) == 2
    assert len(captured["thread_starts"]) == 3
    first_path = _private_dir(architecture, "rhoai-test", first.key)
    second_path = _private_dir(architecture, "rhoai-test", second.key)
    first_envelope = json.loads((first_path / "synthesis.json").read_text())
    second_envelope = json.loads((second_path / "synthesis.json").read_text())
    assert first_envelope["diagnostics"][-1]["code"] == "adapter-failed"
    assert second_envelope["diagnostics"][-1]["code"] == "rate-limit-refusal"
    third_target = _private_dir(architecture, "rhoai-test", third.key)
    assert not (third_target / "synthesis.json").exists()
    assert not (third_target / "run-record.json").exists()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("context_change", "expected_target_calls"),
    [("none", 0), ("model-alias", 1), ("claude-cli", 1)],
)
async def test_production_claude_context_controls_zero_call_reuse(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arch_analyzer_binary: Path,
    context_change: str,
    expected_target_calls: int,
):
    """Use the real factory with transport blocked before adapter construction."""

    from lib import agent_runner, fetch

    architecture, checkout, component = _pipeline_fixture(
        tmp_path, ("rhoai-old", "rhoai-new")
    )
    platforms = tmp_path / "platforms.yaml"
    platforms.write_text("rhoai-old: {}\nrhoai-new:\n  reuse_from: rhoai-old\n")
    old_inputs = _pipeline_inputs(tmp_path / "old-inputs.json")
    new_inputs = _pipeline_inputs(
        tmp_path / "new-inputs.json", reuse_version="rhoai-old"
    )
    cli_state = {
        "path": "/transport-blocked/claude-a",
        "identity": {
            "implementation": "claude-code-cli",
            "version_output": "offline-cli 1.0",
            "binary_sha256": "sha256:" + "3" * 64,
        },
    }

    def resolve_cli(_path=None):
        return cli_state["path"], copy.deepcopy(cli_state["identity"])

    async def ensure_analyzer():
        return str(arch_analyzer_binary)

    transport_calls: list[dict] = []

    async def offline_transport(*args, **kwargs):
        prompt = args[2]
        transport_calls.append(kwargs)
        resolved = agent_runner.get_model_id(kwargs["model"])
        return {
            "success": True,
            "raw_response": _response(prompt),
            "telemetry": {
                "requested_model_identity": resolved,
                "response_models": [resolved],
                "model_usage": {resolved: {"output_tokens": 1}},
                "applied_model_settings": {},
                "claude_cli_identity": copy.deepcopy(cli_state["identity"]),
            },
        }

    monkeypatch.setattr(fetch, "_ensure_arch_analyzer", ensure_analyzer)
    monkeypatch.setattr(agent_runner, "resolve_claude_cli_identity", resolve_cli)
    monkeypatch.setattr(agent_runner, "run_agent", offline_transport)

    old_args = _pipeline_args(
        platform="rhoai-old", inputs=old_inputs, platforms=platforms
    )
    old_args.model = "opus"
    await synthesis.run_pipeline_seam(
        old_args,
        {component.key: component},
        architecture_dir=architecture,
        distribution="RHOAI",
    )
    assert len(transport_calls) == 1

    (checkout / "irrelevant.txt").write_text("new release only\n")
    _git(checkout, "add", "irrelevant.txt")
    _git(checkout, "commit", "-qm", "irrelevant release")
    _refresh_target_analyzer(
        architecture,
        "rhoai-new",
        checkout,
        extracted_at="2026-09-08T16:00:00Z",
    )
    if context_change == "model-alias":
        original_get_model_id = agent_runner.get_model_id

        def changed_alias(model: str) -> str:
            if model == "opus":
                return "claude-opus-changed-alias"
            return original_get_model_id(model)

        monkeypatch.setattr(agent_runner, "get_model_id", changed_alias)
    elif context_change == "claude-cli":
        cli_state["path"] = "/transport-blocked/claude-b"
        cli_state["identity"] = {
            "implementation": "claude-code-cli",
            "version_output": "offline-cli 2.0",
            "binary_sha256": "sha256:" + "4" * 64,
        }

    calls_before_target = len(transport_calls)
    target_args = _pipeline_args(
        platform="rhoai-new", inputs=new_inputs, platforms=platforms
    )
    target_args.model = "opus"
    await synthesis.run_pipeline_seam(
        target_args,
        {component.key: component},
        architecture_dir=architecture,
        distribution="RHOAI",
    )

    assert len(transport_calls) - calls_before_target == expected_target_calls
    target = _private_dir(architecture, "rhoai-new")
    envelope = json.loads((target / "synthesis.json").read_text())
    bundle = json.loads((target / "evidence-bundle.json").read_text())
    implicit = bundle["synthesis_configuration"]["model_context"]["implicit_context"]
    assert implicit["cli_implementation"] == cli_state["identity"]
    assert implicit["requested_model_resolution"]["parent_requested_model"] == ("opus")
    if context_change == "none":
        document = json.loads((target / "document.json").read_text())
        assert "reuse" in document
    else:
        assert (
            "semantic_input_mismatch" in envelope["resolution_provenance"][0]["reasons"]
        )
        assert envelope["calls"]["total"] == 1
        assert (target / "run-record.json").is_file()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("provider_error", "rate_limit_denied", "expect_stop"),
    [
        (
            {
                "kind": "claude-result",
                "is_error": True,
                "errors": [],
                "result": "You've hit your session limit · resets 2am",
            },
            False,
            True,
        ),
        (
            {"kind": "claude-exception", "status_code": 429},
            True,
            True,
        ),
        (
            {
                "kind": "claude-result",
                "is_error": False,
                "rate_limit_events": [{"status": "rejected"}],
            },
            True,
            True,
        ),
        (
            {
                "kind": "claude-result",
                "is_error": True,
                "errors": ["ordinary server failure"],
                "result": None,
            },
            False,
            False,
        ),
    ],
)
async def test_pipeline_seam_stops_all_components_on_real_provider_quota_denial(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arch_analyzer_binary: Path,
    provider_error: dict,
    rate_limit_denied: bool,
    expect_stop: bool,
):
    from lib import agent_runner, fetch

    architecture, checkout, first = _pipeline_fixture(tmp_path, ("rhoai-test",))
    platform = architecture / "rhoai-test"
    component_map_path = platform / "component-map.json"
    component_map = json.loads(component_map_path.read_text())
    component_map["components"]["second"] = {
        **component_map["components"]["praxis-policy"],
        "key": "second",
    }
    component_map_path.write_text(json.dumps(component_map))
    first_analyzer = platform / "praxis-policy/.analyzer/component-architecture.json"
    second_analyzer = platform / "second/.analyzer/component-architecture.json"
    second_analyzer.parent.mkdir(parents=True)
    second_payload = json.loads(first_analyzer.read_text())
    second_payload["component"] = "second"
    second_analyzer.write_text(json.dumps(second_payload))
    inputs = _pipeline_inputs(tmp_path / "inputs.json")
    inputs_payload = json.loads(inputs.read_text())
    inputs_payload["components"]["second"] = copy.deepcopy(
        inputs_payload["components"]["praxis-policy"]
    )
    inputs.write_text(json.dumps(inputs_payload))
    platforms = tmp_path / "platforms.yaml"
    platforms.write_text("rhoai-test: {}\n")
    second = SimpleNamespace(
        key="second", checkout_path=checkout, has_architecture=False
    )
    calls = []

    async def ensure_analyzer():
        return str(arch_analyzer_binary)

    async def refused_transport(*args, **kwargs):
        calls.append(
            json.loads(args[2])["evidence_bundle"]["analyzer"]["payload"]["component"]
        )
        return {
            "success": False,
            "error": "provider refused request",
            "provider_error": provider_error,
            "rate_limit_denied": rate_limit_denied,
        }

    monkeypatch.setattr(fetch, "_ensure_arch_analyzer", ensure_analyzer)
    monkeypatch.setattr(agent_runner, "run_agent", refused_transport)
    run = synthesis.run_pipeline_seam(
        _pipeline_args(platform="rhoai-test", inputs=inputs, platforms=platforms),
        {first.key: first, second.key: second},
        architecture_dir=architecture,
        distribution="RHOAI",
    )
    if expect_stop:
        with pytest.raises(RateLimitError):
            await run
        assert calls == ["policy"]
        refused = json.loads(
            (
                _private_dir(architecture, "rhoai-test", first.key) / "synthesis.json"
            ).read_text()
        )
        assert refused["diagnostics"][-1]["code"] == "rate-limit-refusal"
        assert not (
            _private_dir(architecture, "rhoai-test", "second") / "synthesis.json"
        ).exists()
    else:
        await run
        assert calls == ["policy", "second"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mutated_input", ["analyzer", "component-map", "source-excerpt"]
)
async def test_pipeline_seam_binds_input_bytes_before_run_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arch_analyzer_binary: Path,
    mutated_input: str,
):
    from lib import fetch

    architecture, _checkout, component = _pipeline_fixture(tmp_path, ("rhoai-test",))
    platforms = tmp_path / "platforms.yaml"
    platforms.write_text("rhoai-test: {}\n")
    inputs = _pipeline_inputs(tmp_path / "inputs.json")
    calls: list[str] = []
    _install_pipeline_adapter(monkeypatch, arch_analyzer_binary, calls)

    async def ensure_analyzer():
        return str(arch_analyzer_binary)

    monkeypatch.setattr(fetch, "_ensure_arch_analyzer", ensure_analyzer)
    original_run = synthesis.run_structured_synthesis

    async def mutate_at_boundary(request, adapter, assembler):
        if mutated_input == "analyzer":
            path = request.analyzer_path
        elif mutated_input == "component-map":
            path = request.component_map_path
        else:
            path = request.checkout_root / "source.go"
        path.write_bytes(path.read_bytes() + b" ")
        return await original_run(request, adapter, assembler)

    monkeypatch.setattr(synthesis, "run_structured_synthesis", mutate_at_boundary)
    with pytest.raises(InputMutationError, match="mutated and was restored"):
        await _run_pipeline_fixture_version(
            architecture=architecture,
            component=component,
            version="rhoai-test",
            inputs=inputs,
            platforms=platforms,
        )

    assert calls == []
    target = _private_dir(architecture, "rhoai-test")
    assert not (target / "run-record.json").exists()
    assert not (target / "synthesis.json").exists()


@pytest.mark.asyncio
async def test_pipeline_seam_refuses_inconsistent_completed_record_at_save(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arch_analyzer_binary: Path,
):
    architecture, _checkout, component = _pipeline_fixture(tmp_path, ("rhoai-test",))
    platforms = tmp_path / "platforms.yaml"
    platforms.write_text("rhoai-test: {}\n")
    calls: list[str] = []
    _install_pipeline_adapter(monkeypatch, arch_analyzer_binary, calls)
    original_run = synthesis.run_structured_synthesis

    async def corrupt_after_actual_go(request, adapter, assembler):
        result = await original_run(request, adapter, assembler)
        document = json.loads(result.document_path.read_text())
        document["identity"]["source_revision"] = "0" * 40
        result.document_path.write_text(json.dumps(document))
        return result

    monkeypatch.setattr(synthesis, "run_structured_synthesis", corrupt_after_actual_go)
    with pytest.raises(ReuseRecordError, match="document/input binding"):
        await _run_pipeline_fixture_version(
            architecture=architecture,
            component=component,
            version="rhoai-test",
            inputs=_pipeline_inputs(tmp_path / "inputs.json"),
            platforms=platforms,
        )

    assert len(calls) == 1
    assert not (_private_dir(architecture, "rhoai-test") / "run-record.json").exists()


@pytest.mark.asyncio
async def test_pipeline_seam_does_not_save_unknown_producing_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arch_analyzer_binary: Path,
):
    from lib import fetch

    architecture, _checkout, component = _pipeline_fixture(tmp_path, ("rhoai-test",))
    platforms = tmp_path / "platforms.yaml"
    platforms.write_text("rhoai-test: {}\n")

    async def caller(prompt, _schema, _model, _settings):
        return HarnessResponse(
            raw_text=_response(prompt),
            reported_model=None,
            reported_settings=None,
            requested_model_identity="offline-model",
        )

    async def ensure_analyzer():
        return str(arch_analyzer_binary)

    monkeypatch.setattr(fetch, "_ensure_arch_analyzer", ensure_analyzer)
    monkeypatch.setattr(
        synthesis,
        "authenticated_harness_adapter",
        lambda _harness: ClaudeStructuredAdapter(caller),
    )
    await _run_pipeline_fixture_version(
        architecture=architecture,
        component=component,
        version="rhoai-test",
        inputs=_pipeline_inputs(tmp_path / "inputs.json"),
        platforms=platforms,
    )

    target = _private_dir(architecture, "rhoai-test")
    envelope = json.loads((target / "synthesis.json").read_text())
    assert envelope["state"] == "failed"
    assert envelope["reuse_eligibility"]["available"] is False
    assert envelope["diagnostics"][-1]["code"] == "producer-ineligible"
    assert envelope["responses"][0]["raw_response"].startswith("{")
    assert not (target / "run-record.json").exists()


@pytest.mark.asyncio
async def test_producer_ineligible_component_does_not_abort_unrelated_component(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arch_analyzer_binary: Path,
):
    from lib import fetch

    architecture, checkout, first = _pipeline_fixture(tmp_path, ("rhoai-test",))
    platform = architecture / "rhoai-test"
    component_map_path = platform / "component-map.json"
    component_map = json.loads(component_map_path.read_text())
    component_map["components"]["second"] = {
        **component_map["components"]["praxis-policy"],
        "key": "second",
    }
    component_map_path.write_text(json.dumps(component_map))
    first_analyzer = platform / "praxis-policy/.analyzer/component-architecture.json"
    second_analyzer = platform / "second/.analyzer/component-architecture.json"
    second_analyzer.parent.mkdir(parents=True)
    second_payload = json.loads(first_analyzer.read_text())
    second_payload["component"] = "second"
    second_analyzer.write_text(json.dumps(second_payload))
    inputs = _pipeline_inputs(tmp_path / "inputs.json")
    inputs_payload = json.loads(inputs.read_text())
    inputs_payload["components"]["second"] = copy.deepcopy(
        inputs_payload["components"]["praxis-policy"]
    )
    inputs.write_text(json.dumps(inputs_payload))
    platforms = tmp_path / "platforms.yaml"
    platforms.write_text("rhoai-test: {}\n")
    second = SimpleNamespace(
        key="second", checkout_path=checkout, has_architecture=False
    )
    seen: list[str] = []

    async def caller(prompt, _schema, model, settings):
        component_name = json.loads(prompt)["evidence_bundle"]["analyzer"]["payload"][
            "component"
        ]
        seen.append(component_name)
        return HarnessResponse(
            raw_text=_response(prompt),
            reported_model=None if component_name == "policy" else model,
            reported_settings=None if component_name == "policy" else settings,
            requested_model_identity=model,
        )

    async def ensure_analyzer():
        return str(arch_analyzer_binary)

    monkeypatch.setattr(fetch, "_ensure_arch_analyzer", ensure_analyzer)
    monkeypatch.setattr(
        synthesis,
        "authenticated_harness_adapter",
        lambda _harness: ClaudeStructuredAdapter(caller),
    )
    await synthesis.run_pipeline_seam(
        _pipeline_args(platform="rhoai-test", inputs=inputs, platforms=platforms),
        {first.key: first, second.key: second},
        architecture_dir=architecture,
        distribution="RHOAI",
    )

    assert seen == ["policy", "second"]
    first_target = _private_dir(architecture, "rhoai-test", first.key)
    first_envelope = json.loads((first_target / "synthesis.json").read_text())
    assert first_envelope["state"] == "failed"
    assert first_envelope["responses"][0]["raw_response"]
    assert first_envelope["diagnostics"][-1]["code"] == "producer-ineligible"
    assert not (first_target / "run-record.json").exists()
    assert (
        _private_dir(architecture, "rhoai-test", second.key) / "run-record.json"
    ).is_file()
