"""Bounded, parent-controlled structured component synthesis.

The module is opt-in and writes only private run artifacts. It never parses
Markdown candidates, never falls back to the legacy route, and never publishes
an accepted component. Model calls are injected behind a one-response adapter;
the parent owns evidence, limits, validation, assembly policy, and persistence.
"""

from __future__ import annotations

import base64
import copy
import importlib.metadata
import json
import math
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Awaitable, Callable, Mapping, Protocol, Sequence

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from lib.structured_component_reuse import (
    SEMANTIC_KEY_VERSION,
    AcceptedSnapshot,
    ComponentIdentity,
    DependencyRecord,
    FileDependency,
    InputIdentities,
    ProducerCompatibility,
    ReuseConfigurationError,
    ReuseRecordError,
    ReuseResolution,
    ReuseTarget,
    RevalidationResult,
    SearchObservation,
    SourceRunState,
    SourceSnapshot,
    TargetNormalization,
    _analyzer_bundle_fingerprint,
    _predecessor_document_binding_errors,
    build_input_identities,
    capture_source_snapshot,
    content_hash,
    directory_tree_identity,
    file_hash,
    resolve_or_synthesize,
    resolve_predecessor,
    select_predecessor_snapshot,
    thaw,
)
from lib.telemetry_redact import redact_dict, redact_value

SYNTHESIS_ROUTE = "structured-component/v1"
RESPONSE_SCHEMA = "structured-component-synthesis-response-v1.schema.json"
BUNDLE_SCHEMA = "structured-component-evidence-bundle-v1.schema.json"
ENVELOPE_SCHEMA = "structured-component-synthesis-envelope-v1.schema.json"
INPUT_SCHEMA = "structured-component-synthesis-input-v1.schema.json"
RUN_RECORD_SCHEMA = "structured-component-private-run-record-v1.schema.json"
DOCUMENT_SCHEMA = "structured-component-document-v1.schema.json"
PATCH_SCHEMA = "structured-component-patch-v1.schema.json"
POLICY_SCHEMA = "structured-component-assembly-policy-v1.schema.json"
SCHEMA_VERSION = "1.0.0"
PROMPT_PROTOCOL = "structured-component-prompt/v1"
ADAPTER_PROTOCOL = "structured-component-adapter/v1"
PRIVATE_RUN_RECORD = "structured-component-private-run/v1"
SYNTHESIS_CONTRACT_VERSION = "structured-component-synthesis/v1"
NORMALIZER_VERSION = "structured-component-normalizer/v1"
MAX_RESPONSE_JSON_DEPTH = 64
RUN_RECORD_FILENAME = "run-record.json"
SYNTHESIS_BUNDLE_FILENAME = "synthesis-evidence-bundle.json"
PREFLIGHT_DIAGNOSTIC_FILENAME = "preflight-diagnostic.json"
PARENT_RESPONSE_INSTRUCTIONS = (
    "Return exactly one JSON object matching the supplied response schema. "
    "Use only analyzer facts, corrections, and source_evidence in this bundle. "
    "Do not invoke tools or emit Markdown. Proposals carry no authority."
)
_SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"
_MISS = object()


class StructuredSynthesisError(RuntimeError):
    """The bounded structured route could not produce an accepted result."""

    def __init__(
        self,
        message: str,
        *,
        provider_error: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.provider_error = redact_dict(copy.deepcopy(dict(provider_error or {})))


class EvidenceScopeError(StructuredSynthesisError):
    """A requested or cited source falls outside the parent-owned boundary."""


class InputMutationError(StructuredSynthesisError):
    """An immutable analyzer or synthesis input changed during a call."""


class RateLimitError(StructuredSynthesisError):
    """A harness reported an actual rate limit; callers must stop immediately."""


class AdapterCapabilityError(StructuredSynthesisError):
    """An installed harness cannot enforce this route's call/tool boundary."""


@dataclass(frozen=True)
class SynthesisLimits:
    total_calls: int = 3
    evidence_followups: int = 1
    repairs: int = 1
    max_evidence_files: int = 12
    max_lines_per_read: int = 240

    def __post_init__(self) -> None:
        values = (
            self.total_calls,
            self.max_evidence_files,
            self.max_lines_per_read,
        )
        if any(not isinstance(value, int) or value < 1 for value in values):
            raise ValueError("total_calls and evidence bounds must be positive")
        if (
            not isinstance(self.evidence_followups, int)
            or self.evidence_followups < 0
            or not isinstance(self.repairs, int)
            or self.repairs < 0
        ):
            raise ValueError("follow-up and repair limits must be non-negative")
        if self.evidence_followups + self.repairs + 1 > self.total_calls:
            raise ValueError(
                "total_calls must cover the initial, follow-up, and repair limits"
            )


@dataclass(frozen=True)
class SourceNomination:
    path: str
    start_line: int
    end_line: int
    justification: str
    origin: str = "analyzer-nominated"


@dataclass(frozen=True)
class HarnessResponse:
    raw_text: str
    reported_model: str | None = None
    reported_settings: Mapping[str, Any] | None = None
    requested_model_identity: str | None = None
    settings_source: str = "adapter-reported"
    auxiliary_models: tuple[str, ...] = ()
    response_identity: str | None = None
    observations: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PreparedAdapterSelection:
    model: str
    settings: Mapping[str, Any]
    implicit_context: Mapping[str, Any]
    context_complete: bool = True
    unobserved_context: tuple[str, ...] = ()


class StructuredAdapter(Protocol):
    name: str
    adapter_version: str
    tool_free_enforced: bool
    context_complete: bool
    implicit_context: Mapping[str, Any]
    unobserved_context: tuple[str, ...]

    async def prepare(
        self,
        model: str | None,
        settings: Mapping[str, Any],
    ) -> PreparedAdapterSelection: ...

    async def invoke(
        self,
        prompt: str,
        *,
        response_schema: Mapping[str, Any],
        model: str,
        settings: Mapping[str, Any],
    ) -> HarnessResponse: ...


AdapterCall = Callable[
    [str, Mapping[str, Any], str, Mapping[str, Any]],
    Awaitable[HarnessResponse],
]
AdapterPreparer = Callable[
    [str | None, Mapping[str, Any]],
    Awaitable[PreparedAdapterSelection],
]


class CallbackStructuredAdapter:
    """Capability-declaring adapter used by harness wrappers and test doubles."""

    adapter_version = ADAPTER_PROTOCOL

    def __init__(
        self,
        name: str,
        caller: AdapterCall,
        *,
        tool_free_enforced: bool = True,
        context_complete: bool = True,
        implicit_context: Mapping[str, Any] | None = None,
        unobserved_context: Sequence[str] = (),
    ) -> None:
        self.name = name
        self._caller = caller
        self.tool_free_enforced = tool_free_enforced
        self.context_complete = context_complete
        self.implicit_context = copy.deepcopy(dict(implicit_context or {}))
        self.unobserved_context = tuple(unobserved_context)

    async def invoke(
        self,
        prompt: str,
        *,
        response_schema: Mapping[str, Any],
        model: str,
        settings: Mapping[str, Any],
    ) -> HarnessResponse:
        if not self.tool_free_enforced:
            raise AdapterCapabilityError(
                f"{self.name} adapter cannot enforce a tool-free single response"
            )
        return await self._caller(prompt, response_schema, model, settings)

    async def prepare(
        self,
        model: str | None,
        settings: Mapping[str, Any],
    ) -> PreparedAdapterSelection:
        if not isinstance(model, str) or not model:
            raise AdapterCapabilityError(
                f"{self.name} adapter requires a resolved model identity"
            )
        return PreparedAdapterSelection(
            model=model,
            settings=copy.deepcopy(dict(settings)),
            implicit_context=copy.deepcopy(dict(self.implicit_context)),
            context_complete=self.context_complete,
            unobserved_context=self.unobserved_context,
        )


class ClaudeStructuredAdapter(CallbackStructuredAdapter):
    """Claude structured adapter; an injected caller preserves existing auth."""

    def __init__(self, caller: AdapterCall, **kwargs: Any) -> None:
        super().__init__("claude", caller, **kwargs)


class CodexStructuredAdapter(CallbackStructuredAdapter):
    """Codex adapter using one bounded turn and cancellation on tool activity."""

    def __init__(
        self,
        caller: AdapterCall,
        *,
        preparer: AdapterPreparer | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__("codex", caller, **kwargs)
        self._preparer = preparer

    async def prepare(
        self,
        model: str | None,
        settings: Mapping[str, Any],
    ) -> PreparedAdapterSelection:
        if self._preparer is None:
            return await super().prepare(model, settings)
        prepared = await self._preparer(model, settings)
        self.implicit_context = copy.deepcopy(dict(prepared.implicit_context))
        self.context_complete = prepared.context_complete
        self.unobserved_context = tuple(prepared.unobserved_context)
        return prepared


def _validate_adapter_settings(harness: str, settings: Mapping[str, Any]) -> None:
    allowed = (
        {"max_budget_usd"}
        if harness == "claude"
        else {"model_provider", "reasoning_effort", "service_tier"}
    )
    unknown = sorted(set(settings) - allowed)
    if unknown:
        raise ValueError(
            f"unsupported structured {harness} settings: {', '.join(unknown)}"
        )
    budget = settings.get("max_budget_usd")
    if budget is not None and (
        isinstance(budget, bool) or not isinstance(budget, (int, float)) or budget <= 0
    ):
        raise ValueError("max_budget_usd must be a positive number")


def _provider_rate_limit_denied(result: Mapping[str, Any]) -> bool:
    """Classify structured quota refusals without treating warnings as denial."""

    if result.get("rate_limit_denied") is True:
        return True
    provider_error = result.get("provider_error")

    known_codes = {
        "ratelimit",
        "ratelimiterror",
        "ratelimitreached",
        "sessionbudgetexceeded",
        "usagelimit",
        "usagelimitexceeded",
        "workspacememberusagelimitreached",
        "workspaceownerusagelimitreached",
    }
    code_fields = {"code", "codexerrorinfo", "errorinfo", "errorcode", "type"}
    error_info_fields = {"codexerrorinfo", "errorinfo"}
    error_code_token = re.compile(r"[a-z][a-z0-9_-]*", re.IGNORECASE)

    def normalize_code(value: Any) -> str:
        return "".join(
            character for character in str(value).casefold() if character.isalnum()
        )

    def known_rate_limit_code(value: Any) -> bool:
        return (
            isinstance(value, str)
            and error_code_token.fullmatch(value) is not None
            and normalize_code(value) in known_codes
        )

    def contains_structured_denial(
        value: Any,
        *,
        allow_code_value: bool,
    ) -> bool:
        if isinstance(value, Mapping):
            for key, item in value.items():
                normalized_key = normalize_code(key)
                if normalized_key in {"httpstatuscode", "statuscode"} and item == 429:
                    return True
                if normalized_key in code_fields and known_rate_limit_code(item):
                    return True
                if normalized_key == "data" and known_rate_limit_code(item):
                    return True
                child_allows_code = (
                    allow_code_value or normalized_key in error_info_fields
                )
                if isinstance(item, (Mapping, list, tuple)) and (
                    contains_structured_denial(
                        item,
                        allow_code_value=child_allows_code,
                    )
                ):
                    return True
                if child_allows_code and known_rate_limit_code(item):
                    return True
            return False
        if isinstance(value, (list, tuple)):
            return any(
                contains_structured_denial(
                    item,
                    allow_code_value=allow_code_value,
                )
                for item in value
            )
        return allow_code_value and known_rate_limit_code(value)

    if isinstance(provider_error, Mapping):
        rate_events = provider_error.get("rate_limit_events")
        if isinstance(rate_events, (list, tuple)) and any(
            isinstance(event, Mapping) and event.get("status") == "rejected"
            for event in rate_events
        ):
            return True
    if contains_structured_denial(
        provider_error,
        allow_code_value=not isinstance(provider_error, (Mapping, list, tuple)),
    ):
        return True
    if (
        not isinstance(provider_error, Mapping)
        or provider_error.get("is_error") is not True
    ):
        return False
    detail = provider_error.get("result")
    if not isinstance(detail, str):
        return False
    normalized = " ".join(detail.casefold().replace("_", " ").split())
    return (
        "you've hit your session limit" in normalized
        or "you have hit your session limit" in normalized
        or "http 429" in normalized
        or "too many requests" in normalized
    )


def authenticated_harness_adapter(harness: str) -> StructuredAdapter:
    """Use the repository's existing authenticated harness entry points.

    The parent-controlled prompt, local instruction/config sources, tool policy,
    SDK/CLI boundary, and producer identity are audited separately from opaque
    provider implementation internals. Provider internals are not source reads
    and do not by themselves make the recorded parent input incomplete.
    """

    claude_cli_path: str | None = None
    claude_cli_identity: dict[str, Any] | None = None
    codex_context: dict[str, Any] | None = None
    if harness == "claude":
        from lib.agent_runner import resolve_claude_cli_identity

        claude_cli_path, claude_cli_identity = resolve_claude_cli_identity()

    async def call(
        prompt: str,
        _schema: Mapping[str, Any],
        model: str,
        settings: Mapping[str, Any],
    ) -> HarnessResponse:
        nonlocal codex_context
        _validate_adapter_settings(harness, settings)
        from lib.agent_runner import run_agent

        with tempfile.TemporaryDirectory(prefix="structured-synthesis-") as raw:
            directory = Path(raw)
            if harness == "codex":
                if codex_context is None:
                    raise AdapterCapabilityError(
                        "Codex context preflight was not completed"
                    )
                expected_settings = {
                    "model_provider": codex_context["model_provider"],
                    "reasoning_effort": codex_context["reasoning_effort"],
                    "service_tier": codex_context["service_tier"],
                }
                if (
                    model != codex_context["resolved_model_identity"]
                    or dict(settings) != expected_settings
                ):
                    raise AdapterCapabilityError(
                        "Codex invocation does not match its resolved preflight"
                    )
                transport_model = codex_context["parent_requested_model"]
                transport_binding = {
                    "codex_structured_context": copy.deepcopy(codex_context)
                }
            else:
                transport_model = model
                transport_binding = {"claude_cli_path": claude_cli_path}
            result = await run_agent(
                "structured-response",
                str(directory),
                prompt,
                directory,
                model=transport_model,
                enable_skills=False,
                harness=harness,
                max_turns=1 if harness == "claude" else None,
                max_budget_usd=settings.get("max_budget_usd"),
                tool_free=True,
                response_schema=dict(_schema),
                **transport_binding,
            )
        if not result.get("success"):
            detail = str(result.get("error") or "harness call failed")
            provider_error = result.get("provider_error")
            if _provider_rate_limit_denied(result):
                raise RateLimitError(
                    detail,
                    provider_error=(
                        provider_error if isinstance(provider_error, Mapping) else None
                    ),
                )
            raise StructuredSynthesisError(
                detail,
                provider_error=(
                    provider_error if isinstance(provider_error, Mapping) else None
                ),
            )
        raw_response = result.get("raw_response")
        if not isinstance(raw_response, str):
            raise StructuredSynthesisError("harness returned no final response text")
        telemetry = result.get("telemetry") or {}
        if (
            harness == "claude"
            and telemetry.get("claude_cli_identity") != claude_cli_identity
        ):
            raise StructuredSynthesisError(
                "Claude CLI identity changed or was not reported by the transport"
            )
        if harness == "codex":
            reported_context = telemetry.get("codex_structured_context")
            if (
                codex_context is None
                or not isinstance(reported_context, Mapping)
                or reported_context.get("context_identity")
                != codex_context.get("context_identity")
            ):
                raise StructuredSynthesisError(
                    "Codex context changed or was not reported by the transport"
                )
        model_usage = telemetry.get("model_usage") or {}
        response_models = tuple(dict.fromkeys(telemetry.get("response_models") or ()))
        reported_model = response_models[0] if len(response_models) == 1 else None
        auxiliary_models = tuple(sorted(set(model_usage).difference(response_models)))
        applied_settings = telemetry.get("applied_model_settings")
        settings_observed = isinstance(applied_settings, Mapping)
        return HarnessResponse(
            raw_text=raw_response,
            reported_model=reported_model,
            reported_settings=(
                copy.deepcopy(dict(applied_settings)) if settings_observed else None
            ),
            requested_model_identity=(
                str(telemetry["requested_model_identity"])
                if telemetry.get("requested_model_identity")
                else None
            ),
            settings_source=("applied-sdk-options" if settings_observed else "unknown"),
            auxiliary_models=auxiliary_models,
            observations=telemetry,
        )

    try:
        sdk_version = importlib.metadata.version(
            "claude-agent-sdk" if harness == "claude" else "openai-codex"
        )
    except importlib.metadata.PackageNotFoundError:
        sdk_version = "unknown"
    common = {
        "context_complete": True,
        "implicit_context": {
            "project_settings": "disabled",
            "local_instruction_sources": "suppressed-and-runtime-verified",
            "sdk_version": sdk_version,
            "tool_policy": (
                "sdk-disabled"
                if harness == "claude"
                else "read-only-deny-all-interrupt-and-reject-first-tool-event"
            ),
            "outer_calls_per_invoke": 1,
            "provider_implementation_boundary": (
                "opaque non-source provider internals excluded; exact producing "
                "model and applied settings remain required"
            ),
        },
        "unobserved_context": (),
    }
    if harness == "claude":
        common["implicit_context"]["cli_implementation"] = copy.deepcopy(
            claude_cli_identity
        )
        return ClaudeStructuredAdapter(call, tool_free_enforced=True, **common)
    if harness == "codex":

        async def prepare_codex(
            model: str | None,
            settings: Mapping[str, Any],
        ) -> PreparedAdapterSelection:
            nonlocal codex_context
            if settings:
                raise ValueError(
                    "Codex settings are resolved by the isolated preflight"
                )
            from lib.codex_agent import (
                _codex_rate_limit_denied,
                codex_exception_details,
                preflight_structured_codex_context,
            )

            try:
                codex_context = await preflight_structured_codex_context(model)
            except Exception as error:
                provider_error = codex_exception_details(error)
                if _codex_rate_limit_denied(provider_error):
                    detail = str(redact_value("message", str(error) or repr(error)))
                    raise RateLimitError(
                        detail,
                        provider_error=provider_error,
                    ) from error
                raise
            implicit_context = copy.deepcopy(dict(common["implicit_context"]))
            implicit_context.update(
                {
                    "cli_implementation": copy.deepcopy(
                        codex_context["cli_implementation"]
                    ),
                    "requested_model_resolution": {
                        "parent_requested_model": model,
                        "resolved_model_identity": codex_context[
                            "resolved_model_identity"
                        ],
                        "model_provider": codex_context["model_provider"],
                        "reasoning_effort": codex_context["reasoning_effort"],
                        "service_tier": codex_context["service_tier"],
                    },
                    "isolated_local_context": copy.deepcopy(
                        codex_context["isolated_local_context"]
                    ),
                    "codex_context_identity": codex_context["context_identity"],
                }
            )
            resolved_settings = {
                "model_provider": codex_context["model_provider"],
                "reasoning_effort": codex_context["reasoning_effort"],
                "service_tier": codex_context["service_tier"],
            }
            return PreparedAdapterSelection(
                model=codex_context["resolved_model_identity"],
                settings=resolved_settings,
                implicit_context=implicit_context,
            )

        return CodexStructuredAdapter(
            call,
            preparer=prepare_codex,
            tool_free_enforced=True,
            context_complete=False,
            implicit_context=common["implicit_context"],
            unobserved_context=("codex-preflight-not-completed",),
        )
    raise ValueError(f"unsupported structured harness: {harness}")


@dataclass(frozen=True)
class StructuredSynthesisRequest:
    artifact_dir: Path
    checkout_root: Path
    analyzer_path: Path
    component_map_path: Path
    component: str
    version_scope: str
    integration_status: str
    distribution: str
    model: str
    settings: Mapping[str, Any]
    instructions: str
    analyzer_bytes: bytes | None = None
    component_map_bytes: bytes | None = None
    initial_evidence_bundle: Mapping[str, Any] | None = None
    initial_source_bytes: Mapping[str, bytes] = field(default_factory=dict)
    nominations: tuple[SourceNomination, ...] = ()
    allowed_followup_paths: tuple[str, ...] = ()
    corrections: tuple[Mapping[str, Any], ...] = ()
    assembly_policies: tuple[Mapping[str, Any], ...] = ()
    section_policy: Mapping[str, Any] = field(default_factory=dict)
    observations: Mapping[str, Any] = field(default_factory=dict)
    semantic_configuration: Mapping[str, Any] = field(default_factory=dict)
    immutable_paths: tuple[Path, ...] = ()
    limits: SynthesisLimits = field(default_factory=SynthesisLimits)
    prior_snapshot: AcceptedSnapshot | None = None
    reuse_target: ReuseTarget | None = None
    revalidate_reuse: (
        Callable[[AcceptedSnapshot, ReuseTarget], RevalidationResult] | None
    ) = None
    force_refresh: bool = False
    predecessor_miss_reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class StructuredSynthesisResult:
    state: str
    envelope_path: Path
    evidence_bundle_path: Path
    document_path: Path | None
    markdown_path: Path | None
    calls: int
    reused: bool = False
    diagnostics: tuple[Mapping[str, Any], ...] = ()


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()


def _raw_response_representation(raw: str) -> str | dict[str, Any]:
    """Return directly emit-able text or a reversible surrogate-safe form."""

    try:
        raw.encode("utf-8")
    except UnicodeEncodeError:
        payload = base64.b64encode(raw.encode("utf-8", errors="surrogatepass"))
        return {
            "encoding": "utf-8-surrogatepass-base64",
            "data": payload.decode("ascii"),
            "character_count": len(raw),
        }
    return raw


def _raw_response_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if not isinstance(value, Mapping) or value.get("encoding") != (
        "utf-8-surrogatepass-base64"
    ):
        raise ReuseRecordError("predecessor raw response representation is invalid")
    try:
        raw = base64.b64decode(str(value["data"]), validate=True).decode(
            "utf-8", errors="surrogatepass"
        )
    except (KeyError, ValueError, UnicodeDecodeError) as error:
        raise ReuseRecordError(
            "predecessor raw response representation is invalid"
        ) from error
    if len(raw) != value.get("character_count"):
        raise ReuseRecordError(
            "predecessor raw response representation length is invalid"
        )
    return raw


def _raw_response_hash(value: str | Mapping[str, Any]) -> str:
    if isinstance(value, str):
        return content_hash(value.encode("utf-8"))
    return content_hash(dict(value))


def _reject_excessive_json_nesting(raw: str) -> None:
    depth = 0
    quoted = False
    escaped = False
    for character in raw:
        if quoted:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
            continue
        if character == '"':
            quoted = True
        elif character in "[{":
            depth += 1
            if depth > MAX_RESPONSE_JSON_DEPTH:
                raise StructuredSynthesisError(
                    "response JSON nesting exceeds configured maximum "
                    f"of {MAX_RESPONSE_JSON_DEPTH}"
                )
        elif character in "]}":
            depth -= 1


def _validate_json_text(value: Any, path: str = "$") -> None:
    if isinstance(value, str):
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as error:
            raise StructuredSynthesisError(
                f"response contains unpaired surrogate text at {path}"
            ) from error
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            _validate_json_text(str(key), f"{path}.<key>")
            _validate_json_text(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _validate_json_text(item, f"{path}[{index}]")


def _schemas() -> tuple[dict[str, dict[str, Any]], Registry]:
    schemas = {
        path.name: json.loads(path.read_text())
        for path in sorted(_SCHEMA_DIR.glob("structured-*.schema.json"))
    }
    registry = Registry().with_resources(
        [(schema["$id"], Resource.from_contents(schema)) for schema in schemas.values()]
    )
    return schemas, registry


def _validate_schema(name: str, value: Any) -> None:
    schemas, registry = _schemas()
    validator = Draft202012Validator(schemas[name], registry=registry)
    errors = sorted(validator.iter_errors(value), key=lambda item: list(item.path))
    if errors:
        error = errors[0]
        location = "/" + "/".join(str(item) for item in error.absolute_path)
        raise StructuredSynthesisError(
            f"{name} validation failed at {location}: {error.message}"
        )


def _snapshot(paths: Sequence[Path]) -> dict[Path, bytes]:
    result: dict[Path, bytes] = {}
    for raw in paths:
        path = Path(raw).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"immutable synthesis input is missing: {path}")
        result[path] = path.read_bytes()
    return result


def _bound_analyzer_bytes(request: StructuredSynthesisRequest) -> bytes:
    return (
        bytes(request.analyzer_bytes)
        if request.analyzer_bytes is not None
        else request.analyzer_path.read_bytes()
    )


def _bound_component_map_bytes(request: StructuredSynthesisRequest) -> bytes:
    return (
        bytes(request.component_map_bytes)
        if request.component_map_bytes is not None
        else request.component_map_path.read_bytes()
    )


def _verify_immutable(snapshot: Mapping[Path, bytes]) -> None:
    mutations: list[str] = []
    for path, original in snapshot.items():
        try:
            current = path.read_bytes()
        except OSError:
            current = None
        if current == original:
            continue
        mutations.append(str(path))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(original)
    if mutations:
        raise InputMutationError(
            "immutable synthesis input mutated and was restored: "
            + ", ".join(mutations)
        )


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(payload)
    temporary.replace(path)


def _write_preflight_rate_limit_diagnostic(
    architecture_dir: Path,
    platform: str,
    *,
    harness: str,
    requested_model: str | None,
    error: RateLimitError,
) -> Path:
    """Persist a private, component-independent preflight refusal record."""

    path = (
        architecture_dir
        / platform
        / ".generation"
        / "structured"
        / PREFLIGHT_DIAGNOSTIC_FILENAME
    )
    diagnostic: dict[str, Any] = {
        "code": "rate-limit-refusal",
        "detail": str(error),
    }
    if error.provider_error:
        diagnostic["provider_error"] = copy.deepcopy(error.provider_error)
    _atomic_json(
        path,
        {
            "schema_version": SCHEMA_VERSION,
            "state": "failed",
            "phase": "context-preflight",
            "harness": harness,
            "requested_model": requested_model,
            "model_calls_started": 0,
            "diagnostic": diagnostic,
        },
    )
    return path


class EvidenceBundleBuilder:
    """Resolve only parent-allowed regular files and retain whole-file identity."""

    def __init__(
        self,
        checkout_root: Path,
        revision: str,
        allowed_paths: Sequence[str],
        limits: SynthesisLimits,
    ) -> None:
        self.root = checkout_root.resolve()
        self.revision = revision
        self.limits = limits
        self.allowed = {self._relative(path) for path in allowed_paths}

    def _relative(self, raw: str) -> str:
        candidate = Path(raw)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise EvidenceScopeError(f"source path escapes checkout: {raw}")
        lexical = self.root / candidate
        resolved = lexical.resolve()
        try:
            relative = resolved.relative_to(self.root).as_posix()
        except ValueError as error:
            raise EvidenceScopeError(f"source path escapes checkout: {raw}") from error
        if lexical.is_symlink() or any(
            parent.is_symlink() for parent in lexical.parents if parent != self.root
        ):
            raise EvidenceScopeError(f"symlinked evidence path is not allowed: {raw}")
        return relative

    def read(self, nomination: SourceNomination) -> dict[str, Any]:
        relative = self._relative(nomination.path)
        if relative not in self.allowed:
            raise EvidenceScopeError(f"source path was not parent-allowed: {relative}")
        if (
            nomination.start_line < 1
            or nomination.end_line < nomination.start_line
            or nomination.end_line - nomination.start_line + 1
            > self.limits.max_lines_per_read
        ):
            raise EvidenceScopeError(
                f"source range is invalid or exceeds limit: {relative}:"
                f"{nomination.start_line}-{nomination.end_line}"
            )
        if nomination.origin not in {"analyzer-nominated", "parent-follow-up"}:
            raise EvidenceScopeError(
                f"unknown source evidence origin: {nomination.origin}"
            )
        if not nomination.justification.strip():
            raise EvidenceScopeError(f"source evidence lacks justification: {relative}")
        path = self.root / relative
        if not path.is_file():
            raise EvidenceScopeError(
                f"source evidence is not a regular file: {relative}"
            )
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise EvidenceScopeError(
                f"source evidence is not UTF-8: {relative}"
            ) from error
        lines = text.splitlines()
        if nomination.end_line > len(lines):
            raise EvidenceScopeError(
                f"source range exceeds file: {relative}:{nomination.end_line}"
            )
        return {
            "path": relative,
            "start_line": nomination.start_line,
            "end_line": nomination.end_line,
            "revision": self.revision,
            "content": "\n".join(
                lines[nomination.start_line - 1 : nomination.end_line]
            ),
            "whole_file_hash": content_hash(raw),
            "whole_file_line_count": len(lines),
            "origin": nomination.origin,
            "justification": nomination.justification.strip(),
        }


def _bundle_without_identity(bundle: Mapping[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(dict(bundle))
    result.pop("bundle_identity", None)
    return result


def _set_bundle_identity(bundle: dict[str, Any]) -> None:
    bundle["bundle_identity"] = content_hash(_bundle_without_identity(bundle))


def _context_identity(
    request: StructuredSynthesisRequest,
    adapter: StructuredAdapter,
) -> tuple[str, bool, dict[str, Any]]:
    implicit_context = copy.deepcopy(dict(adapter.implicit_context))
    if adapter.name == "claude":
        from lib.agent_runner import get_model_id

        implicit_context["requested_model_resolution"] = {
            "parent_requested_model": request.model,
            "resolved_model_identity": get_model_id(request.model),
        }
    payload = {
        "protocol": PROMPT_PROTOCOL,
        "adapter": adapter.name,
        "adapter_version": adapter.adapter_version,
        "parent_response_instructions": PARENT_RESPONSE_INSTRUCTIONS,
        "instructions": request.instructions,
        "requested_model": request.model,
        "requested_settings": copy.deepcopy(dict(request.settings)),
        "implicit_context": implicit_context,
        "unobserved_context": list(adapter.unobserved_context),
        "tool_free_enforced": adapter.tool_free_enforced,
    }
    complete = adapter.context_complete and not adapter.unobserved_context
    return content_hash(payload), complete, payload


def build_evidence_bundle(
    request: StructuredSynthesisRequest,
    adapter: StructuredAdapter,
) -> tuple[dict[str, Any], EvidenceBundleBuilder, str, bool]:
    analyzer_bytes = _bound_analyzer_bytes(request)
    try:
        analyzer = json.loads(analyzer_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise StructuredSynthesisError(
            f"bound analyzer input is not JSON: {error}"
        ) from error
    # The component map remains an immutable trusted assembly input, but it is
    # intentionally not model-visible. Platform integration and overlay state
    # likewise belong to target normalization, so platform-only metadata cannot
    # silently influence reusable synthesis.
    revision = str(analyzer.get("commit_sha") or "")
    if not revision:
        raise StructuredSynthesisError("analyzer input lacks commit_sha")
    builder = EvidenceBundleBuilder(
        request.checkout_root,
        revision,
        (*request.allowed_followup_paths, *(item.path for item in request.nominations)),
        request.limits,
    )
    context_identity, context_complete, context_payload = _context_identity(
        request, adapter
    )
    if request.initial_evidence_bundle is not None:
        bundle = copy.deepcopy(dict(request.initial_evidence_bundle))
        try:
            _validate_schema(BUNDLE_SCHEMA, bundle)
        except StructuredSynthesisError as error:
            raise StructuredSynthesisError(
                f"bound evidence bundle is invalid: {error}"
            ) from error
        if (
            content_hash(_bundle_without_identity(bundle))
            != bundle.get("bundle_identity")
            or bundle.get("analyzer", {}).get("content_hash")
            != content_hash(analyzer_bytes)
            or bundle.get("synthesis_configuration", {}).get("model_context")
            != context_payload
        ):
            raise InputMutationError(
                "bound evidence bundle no longer matches its analyzer or context"
            )
        return bundle, builder, context_identity, context_complete
    source_evidence = [builder.read(item) for item in request.nominations]
    if len(source_evidence) > request.limits.max_evidence_files:
        raise EvidenceScopeError("initial evidence exceeds max_evidence_files")
    schemas, _ = _schemas()
    configuration = {
        "component": request.component,
        "version_scope": request.version_scope,
        "distribution": request.distribution,
        "semantic_configuration": copy.deepcopy(dict(request.semantic_configuration)),
        "model_context": context_payload,
        "limits": {
            "total_calls": request.limits.total_calls,
            "evidence_followups": request.limits.evidence_followups,
            "repairs": request.limits.repairs,
            "max_evidence_files": request.limits.max_evidence_files,
            "max_lines_per_read": request.limits.max_lines_per_read,
        },
    }
    bundle = {
        "schema_version": SCHEMA_VERSION,
        "bundle_identity": "",
        "analyzer": {
            "content_hash": content_hash(analyzer_bytes),
            "payload": analyzer,
        },
        "corrections": copy.deepcopy(
            [
                item
                for item in request.corrections
                if item.get("version_scope") == request.version_scope
            ]
        ),
        "contracts": {
            name: schemas[name]
            for name in (RESPONSE_SCHEMA, PATCH_SCHEMA, POLICY_SCHEMA, DOCUMENT_SCHEMA)
        },
        "source_evidence": source_evidence,
        "observations": copy.deepcopy(dict(request.observations)),
        "synthesis_configuration": configuration,
    }
    _set_bundle_identity(bundle)
    _validate_schema(BUNDLE_SCHEMA, bundle)
    return bundle, builder, context_identity, context_complete


def _response_diagnostics(
    payload: Mapping[str, Any], bundle: Mapping[str, Any]
) -> list[str]:
    errors: list[str] = []
    if payload.get("input_bundle_identity") != bundle["bundle_identity"]:
        errors.append("response input_bundle_identity does not match current bundle")
    status = payload.get("completion_status")
    requests = payload.get("evidence_requests")
    if status == "complete" and requests:
        errors.append("complete response must not contain evidence_requests")
    if status == "needs-evidence" and not requests:
        errors.append("needs-evidence response requires evidence_requests")
    if status == "unresolved" and not payload.get("limitations"):
        errors.append("unresolved response requires explicit limitations")
    if status == "unresolved" and requests:
        errors.append("unresolved response must not contain evidence_requests")
    analyzer_fingerprint = _analyzer_bundle_fingerprint(bundle["analyzer"]["payload"])
    patch_ids: set[str] = set()
    for patch in payload.get("typed_patches", ()):
        patch_id = patch.get("patch_id")
        if patch_id in patch_ids:
            errors.append(f"duplicate patch_id: {patch_id}")
        patch_ids.add(patch_id)
        if patch.get("bundle_fingerprint") != analyzer_fingerprint:
            errors.append(f"patch {patch_id} is not bound to the analyzer bundle")
    section_ids = [item.get("id") for item in payload.get("sections", ())]
    if len(section_ids) != len(set(section_ids)):
        errors.append("duplicate section id")
    return errors


def _parse_response(raw: str, bundle: Mapping[str, Any]) -> dict[str, Any]:
    _reject_excessive_json_nesting(raw)

    def reject_constant(value: str) -> None:
        raise ValueError(f"non-standard nonfinite number {value} is not allowed")

    def finite_float(value: str) -> float:
        result = float(value)
        if not math.isfinite(result):
            raise ValueError(f"nonfinite number {value} is not allowed")
        return result

    try:
        payload = json.loads(
            raw,
            parse_constant=reject_constant,
            parse_float=finite_float,
        )
    except (json.JSONDecodeError, RecursionError, ValueError) as error:
        raise StructuredSynthesisError(
            f"response is not one JSON value: {error}"
        ) from error
    if not isinstance(payload, dict):
        raise StructuredSynthesisError("response JSON root must be an object")
    _validate_json_text(payload)
    try:
        _validate_schema(RESPONSE_SCHEMA, payload)
    except RecursionError as error:
        raise StructuredSynthesisError(
            "response validation exceeded the configured structural bound"
        ) from error
    errors = _response_diagnostics(payload, bundle)
    if errors:
        raise StructuredSynthesisError("; ".join(errors))
    return payload


def _evidence_covers(
    reference: Mapping[str, Any], evidence: Sequence[Mapping[str, Any]]
) -> bool:
    start = reference.get("start_line")
    end = reference.get("end_line")
    for supplied in evidence:
        if reference.get("path") != supplied.get("path") or reference.get(
            "revision"
        ) != supplied.get("revision"):
            continue
        if start is None and end is None:
            return supplied.get("start_line") == 1 and supplied.get(
                "end_line"
            ) == supplied.get("whole_file_line_count")
        if (
            isinstance(start, int)
            and isinstance(end, int)
            and supplied["start_line"] <= start <= end <= supplied["end_line"]
        ):
            return True
    return False


def _validate_model_evidence(
    payload: Mapping[str, Any], bundle: Mapping[str, Any]
) -> None:
    references: list[Mapping[str, Any]] = []
    for section in payload["sections"]:
        references.extend(section["evidence"])
        for block in section["blocks"]:
            for row in block.get("rows", ()):
                references.extend(row["evidence"])
    for patch in payload["typed_patches"]:
        for operation in patch["operations"]:
            references.extend(operation["evidence"])
    missing = [
        f"{item.get('path')}:{item.get('start_line', '?')}-{item.get('end_line', '?')}"
        for item in references
        if not _evidence_covers(item, bundle["source_evidence"])
    ]
    if missing:
        raise EvidenceScopeError(
            "model cited evidence not supplied by parent: " + ", ".join(missing)
        )


def _prompt(
    bundle: Mapping[str, Any],
    *,
    purpose: str,
    prior: str | Mapping[str, Any] | None = None,
    diagnostics: Sequence[str] = (),
) -> str:
    request = {
        "protocol": PROMPT_PROTOCOL,
        "purpose": purpose,
        "instructions": PARENT_RESPONSE_INSTRUCTIONS,
        "evidence_bundle": bundle,
        "response_schema": bundle["contracts"][RESPONSE_SCHEMA],
        "prior_response": prior,
        "validation_diagnostics": list(diagnostics),
    }
    return _canonical(request).decode()


def _proposal_fingerprint(patch: Mapping[str, Any]) -> str:
    return _analyzer_bundle_fingerprint(patch)


def _default_reject_policy(
    patch: Mapping[str, Any], response_id: str, version_scope: str
) -> dict[str, Any]:
    fact_types = sorted({str(item["fact_type"]) for item in patch["operations"]})
    return {
        "schema_version": SCHEMA_VERSION,
        "policy_id": f"parent-default-reject:{patch['patch_id']}",
        "patch_id": patch["patch_id"],
        "proposal_fingerprint": _proposal_fingerprint(patch),
        "bundle_fingerprint": patch["bundle_fingerprint"],
        "version_scope": version_scope,
        "origin": {"kind": "model", "id": response_id, "claim_class": "implementation"},
        "authority": {
            "actor": "structured-synthesis-parent",
            "allowed_fact_types": fact_types,
        },
        "decisions": [
            {
                "decision_id": f"default-reject:{item['operation_id']}",
                "operation_id": item["operation_id"],
                "decision": "reject",
                "decided_by": "structured-synthesis-parent",
                "reason": "No independent trusted acceptance policy was supplied.",
            }
            for item in patch["operations"]
        ],
    }


def _select_sections(
    payload: Mapping[str, Any], policy: Mapping[str, Any], version_scope: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], tuple[str, str, str] | None]:
    accepted: list[dict[str, Any]] = []
    dispositions: list[dict[str, Any]] = []
    authorities: set[tuple[str, str, str]] = set()
    decisions = policy.get("decisions", {}) if isinstance(policy, Mapping) else {}
    policy_scope = policy.get("version_scope") if isinstance(policy, Mapping) else None
    proposed_section_ids = {str(item["id"]) for item in payload["sections"]}
    if isinstance(decisions, Mapping):
        missing = sorted(set(decisions) - proposed_section_ids)
        if missing:
            raise StructuredSynthesisError(
                "trusted section policy references missing model section: "
                + ", ".join(missing)
            )
    for section in payload["sections"]:
        decision = (
            decisions.get(section["id"], {}) if isinstance(decisions, Mapping) else {}
        )
        is_accepted = (
            decision.get("decision") == "accept" and policy_scope == version_scope
        )
        disposition = {
            "kind": "section",
            "section_id": section["id"],
            "status": "accepted" if is_accepted else "rejected",
            "policy_id": str(policy.get("policy_id") or "no-section-policy"),
            "decided_by": str(
                decision.get("decided_by") or "structured-synthesis-parent"
            ),
            "reason": str(
                decision.get("reason")
                or "No matching trusted section acceptance decision."
            ),
        }
        dispositions.append(disposition)
        if not is_accepted:
            continue
        origin = decision.get("origin")
        if not isinstance(origin, Mapping):
            raise StructuredSynthesisError(
                f"accepted section {section['id']} lacks trusted origin"
            )
        authority = (
            str(origin.get("kind") or ""),
            str(origin.get("id") or ""),
            str(origin.get("claim_class") or ""),
        )
        if (
            authority[0] != "model"
            or authority[1] != payload["response_id"]
            or not all(authority)
        ):
            raise StructuredSynthesisError(
                f"accepted model section {section['id']} has invalid trusted origin"
            )
        authorities.add(authority)
        accepted.append(copy.deepcopy(section))
    if len(authorities) > 1:
        raise StructuredSynthesisError(
            "current Go section adapter requires one trusted authority per response"
        )
    return accepted, dispositions, next(iter(authorities), None)


class GoStructuredAssembler:
    """Invoke the current Go normalizer/validator and sole Markdown renderer."""

    def __init__(self, command: Sequence[str], cwd: Path) -> None:
        self.command = tuple(command)
        self.cwd = cwd

    def _run(self, arguments: Sequence[str]) -> None:
        completed = subprocess.run(
            [*self.command, *arguments],
            cwd=self.cwd,
            env={**os.environ, "GOCACHE": "/tmp/structured-component-go-cache"},
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise StructuredSynthesisError(
                "Go structured assembly failed: "
                + (completed.stderr or completed.stdout).strip()
            )

    def assemble(
        self,
        request: StructuredSynthesisRequest,
        payload: Mapping[str, Any],
        artifact_dir: Path,
    ) -> tuple[Path, Path, list[dict[str, Any]]]:
        sections, section_dispositions, authority = _select_sections(
            payload, request.section_policy, request.version_scope
        )
        patches = [copy.deepcopy(item) for item in payload["typed_patches"]]
        policies_by_patch: dict[str, dict[str, Any]] = {}
        for item in request.assembly_policies:
            patch_id = str(item.get("patch_id"))
            if patch_id in policies_by_patch:
                raise StructuredSynthesisError(
                    f"duplicate trusted assembly policy for patch: {patch_id}"
                )
            policies_by_patch[patch_id] = copy.deepcopy(dict(item))
        policies: list[dict[str, Any]] = []
        for patch in patches:
            policy = policies_by_patch.pop(patch["patch_id"], None)
            if patch["operations"] and policy is None:
                policy = _default_reject_policy(
                    patch, payload["response_id"], request.version_scope
                )
            if policy is not None:
                policies.append(policy)
        if policies_by_patch:
            raise StructuredSynthesisError(
                "trusted assembly policy references missing model patch: "
                + ", ".join(sorted(policies_by_patch))
            )
        for correction in request.corrections:
            patch = correction.get("patch")
            policy = correction.get("policy")
            if not isinstance(patch, Mapping) or not isinstance(policy, Mapping):
                raise StructuredSynthesisError("correction requires patch and policy")
            if correction.get("version_scope") != request.version_scope:
                continue
            if policy.get("origin", {}).get("kind") != "human-correction":
                raise StructuredSynthesisError(
                    "correction policy must retain human-correction authority"
                )
            patches.append(copy.deepcopy(dict(patch)))
            policies.append(copy.deepcopy(dict(policy)))

        work = artifact_dir / "assembly"
        work.mkdir(parents=True, exist_ok=True)
        analyzer_input_path = work / "bound-analyzer.json"
        component_map_input_path = work / "bound-component-map.json"
        analyzer_input_path.write_bytes(_bound_analyzer_bytes(request))
        component_map_input_path.write_bytes(_bound_component_map_bytes(request))
        sections_path = work / "sections.json"
        _atomic_json(sections_path, sections)
        arguments = [
            "normalize",
            "--input",
            str(analyzer_input_path),
            "--component-map",
            str(component_map_input_path),
            "--component-map-id",
            f"component-map:{request.version_scope}",
            "--version-scope",
            request.version_scope,
            "--integration-status",
            request.integration_status,
            "--distribution",
            request.distribution,
            "--generated-by",
            f"{payload['response_id']} via structured synthesis",
            "--sections",
            str(sections_path),
        ]
        if sections:
            assert authority is not None
            arguments.extend(
                [
                    "--section-origin-kind",
                    authority[0],
                    "--section-origin-id",
                    authority[1],
                    "--section-claim-class",
                    authority[2],
                ]
            )
        for index, patch in enumerate(patches):
            path = work / f"patch-{index + 1:02d}.json"
            _atomic_json(path, patch)
            arguments.extend(["--patch", str(path)])
        for index, policy in enumerate(policies):
            path = work / f"policy-{index + 1:02d}.json"
            _atomic_json(path, policy)
            arguments.extend(["--assembly-policy", str(path)])
        document = artifact_dir / "document.json"
        markdown = artifact_dir / "candidate.md"
        arguments.extend(["--output", str(document)])
        self._run(arguments)
        _validate_schema(DOCUMENT_SCHEMA, json.loads(document.read_text()))
        self._run(
            ["render-document", "--input", str(document), "--output", str(markdown)]
        )
        return document, markdown, section_dispositions

    def validate_and_render(self, document: Path, markdown: Path) -> None:
        _validate_schema(DOCUMENT_SCHEMA, json.loads(document.read_text()))
        self._run(
            ["render-document", "--input", str(document), "--output", str(markdown)]
        )


def _envelope_base(
    request: StructuredSynthesisRequest,
    adapter: StructuredAdapter,
    bundle: Mapping[str, Any],
    context_identity: str,
    context_complete: bool,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "state": "failed",
        "route": SYNTHESIS_ROUTE,
        "input_bundle_identity": bundle["bundle_identity"],
        "context_identity": context_identity,
        "reuse_eligibility": {
            "available": context_complete,
            "reason": "complete-model-visible-context"
            if context_complete
            else "unobserved-model-context",
            "unobserved_context": list(adapter.unobserved_context),
        },
        "requested": {
            "harness": adapter.name,
            "model": request.model,
            "settings": copy.deepcopy(dict(request.settings)),
        },
        "reported": {"models": [], "settings": [], "auxiliary_models": []},
        "calls": {
            "total": 0,
            "initial": 0,
            "evidence_followup": 0,
            "repair": 0,
            "limits": {
                "total": request.limits.total_calls,
                "evidence_followup": request.limits.evidence_followups,
                "repair": request.limits.repairs,
            },
        },
        "responses": [],
        "resolution_provenance": [],
        "observations": copy.deepcopy(dict(request.observations)),
        "justifications": [item["justification"] for item in bundle["source_evidence"]],
        "accepted_response_identity": None,
        "diagnostics": [],
    }


def special_synthesis_envelope(
    state: str,
    *,
    input_bundle_identity: str,
    reason: str,
) -> dict[str, Any]:
    """Represent deterministic-only and missing historical response states."""

    if state not in {"deterministic-only", "historical-response-missing"}:
        raise ValueError("unsupported special synthesis state")
    envelope = {
        "schema_version": SCHEMA_VERSION,
        "state": state,
        "route": SYNTHESIS_ROUTE,
        "input_bundle_identity": input_bundle_identity,
        "context_identity": content_hash({"state": state}),
        "reuse_eligibility": {
            "available": False,
            "reason": reason,
            "unobserved_context": [],
        },
        "requested": {"harness": "none", "model": "none", "settings": {}},
        "reported": {"models": [], "settings": [], "auxiliary_models": []},
        "calls": {
            "total": 0,
            "initial": 0,
            "evidence_followup": 0,
            "repair": 0,
            "limits": {"total": 0, "evidence_followup": 0, "repair": 0},
        },
        "responses": [],
        "resolution_provenance": [],
        "observations": {},
        "justifications": [],
        "accepted_response_identity": None,
        "diagnostics": [{"code": state, "detail": reason}],
    }
    _validate_schema(ENVELOPE_SCHEMA, envelope)
    return envelope


def _reuse_record(resolution: ReuseResolution, target: ReuseTarget) -> dict[str, Any]:
    provenance = thaw(resolution.provenance)
    checks = sorted(
        key for key, value in provenance.get("revalidation_checks", {}).items() if value
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "prior_snapshot_id": provenance["prior_snapshot_id"],
        "prior_platform": provenance["prior_platform"],
        "target_platform": provenance["target_platform"],
        "prior_document_hash": provenance["predecessor_document_integrity"],
        "original_synthesis_hash": provenance["synthesis_integrity"],
        "response_identity": resolution.response_identity,
        "target_exact_input": target.inputs.exact,
        "target_semantic_input": target.inputs.semantic,
        "comparison_hash": content_hash(thaw(resolution.decision.comparison)),
        "reason": provenance["reason"],
        "revalidation_checks": checks,
    }


async def run_structured_synthesis(
    request: StructuredSynthesisRequest,
    adapter: StructuredAdapter,
    assembler: GoStructuredAssembler,
) -> StructuredSynthesisResult:
    """Run a reuse-first, bounded structured attempt without publication."""

    artifact_dir = request.artifact_dir.resolve()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    envelope_path = artifact_dir / "synthesis.json"
    bundle_path = artifact_dir / "evidence-bundle.json"
    source_paths = tuple(
        request.checkout_root / path
        for path in (
            *request.allowed_followup_paths,
            *(item.path for item in request.nominations),
        )
    )
    # Resolve and enforce every parent-owned evidence boundary before any
    # source path is opened for the immutable snapshot.
    bundle, builder, context_identity, context_complete = build_evidence_bundle(
        request, adapter
    )
    immutable = _snapshot(
        (
            request.analyzer_path,
            request.component_map_path,
            *request.immutable_paths,
            *source_paths,
        )
    )
    immutable[request.analyzer_path.resolve()] = _bound_analyzer_bytes(request)
    immutable[request.component_map_path.resolve()] = _bound_component_map_bytes(
        request
    )
    for relative, raw in request.initial_source_bytes.items():
        immutable[(request.checkout_root / relative).resolve()] = bytes(raw)
    _verify_immutable(immutable)
    _atomic_json(bundle_path, bundle)

    if request.prior_snapshot is not None or request.reuse_target is not None:
        if not all(
            (request.prior_snapshot, request.reuse_target, request.revalidate_reuse)
        ):
            raise StructuredSynthesisError(
                "reuse requires prior snapshot, target, and Go-backed revalidator"
            )
        resolution = resolve_or_synthesize(
            request.prior_snapshot,
            request.reuse_target,
            revalidate=request.revalidate_reuse,
            synthesize=lambda _target: _MISS,
            force_refresh=request.force_refresh or not context_complete,
        )
        if resolution.reused:
            if resolution.synthesis_bytes is None:
                raise StructuredSynthesisError(
                    "reuse hit lacks original synthesis bytes"
                )
            envelope_path.write_bytes(resolution.synthesis_bytes)
            document_value = copy.deepcopy(resolution.output)
            document_value["reuse"] = _reuse_record(resolution, request.reuse_target)
            document_path = artifact_dir / "document.json"
            markdown_path = artifact_dir / "candidate.md"
            _atomic_json(document_path, document_value)
            assembler.validate_and_render(document_path, markdown_path)
            _verify_immutable(immutable)
            return StructuredSynthesisResult(
                "reused",
                envelope_path,
                bundle_path,
                document_path,
                markdown_path,
                0,
                True,
            )

    envelope = _envelope_base(
        request, adapter, bundle, context_identity, context_complete
    )
    envelope["resolution_provenance"].append(
        {
            "ordinal": 1,
            "kind": "reuse-miss",
            "reasons": (
                list(resolution.decision.reasons)
                if "resolution" in locals()
                else list(request.predecessor_miss_reasons)
                or ["predecessor-not-supplied"]
            ),
        }
    )
    _atomic_json(envelope_path, envelope)
    response_schema = bundle["contracts"][RESPONSE_SCHEMA]
    purpose = "initial"
    prior_raw: str | Mapping[str, Any] | None = None
    repair_diagnostics: list[str] = []
    accepted_payload: dict[str, Any] | None = None

    while envelope["calls"]["total"] < request.limits.total_calls:
        if (
            purpose == "repair"
            and envelope["calls"]["repair"] >= request.limits.repairs
        ):
            break
        if (
            purpose == "evidence-followup"
            and envelope["calls"]["evidence_followup"]
            >= request.limits.evidence_followups
        ):
            break
        prompt = _prompt(
            bundle, purpose=purpose, prior=prior_raw, diagnostics=repair_diagnostics
        )
        request_identity = content_hash(
            {"prompt": prompt, "context_identity": context_identity}
        )
        try:
            response = await adapter.invoke(
                prompt,
                response_schema=response_schema,
                model=request.model,
                settings=request.settings,
            )
        except RateLimitError as error:
            envelope["state"] = "failed"
            diagnostic: dict[str, Any] = {
                "code": "rate-limit-refusal",
                "detail": str(error),
            }
            if error.provider_error:
                diagnostic["provider_error"] = copy.deepcopy(error.provider_error)
            envelope["diagnostics"].append(diagnostic)
            _validate_schema(ENVELOPE_SCHEMA, envelope)
            _atomic_json(envelope_path, envelope)
            raise
        except StructuredSynthesisError as error:
            envelope["state"] = "failed"
            diagnostic = {"code": "adapter-failed", "detail": str(error)}
            if error.provider_error:
                diagnostic["provider_error"] = copy.deepcopy(error.provider_error)
            envelope["diagnostics"].append(diagnostic)
            _validate_schema(ENVELOPE_SCHEMA, envelope)
            _atomic_json(envelope_path, envelope)
            return StructuredSynthesisResult(
                "failed",
                envelope_path,
                bundle_path,
                None,
                None,
                envelope["calls"]["total"],
                diagnostics=tuple(envelope["diagnostics"]),
            )
        envelope["calls"]["total"] += 1
        key = "initial" if purpose == "initial" else purpose.replace("-", "_")
        envelope["calls"][key] += 1
        raw_representation = _raw_response_representation(response.raw_text)
        raw_hash = _raw_response_hash(raw_representation)
        response_identity = response.response_identity or raw_hash
        model_context = bundle["synthesis_configuration"]["model_context"]
        resolved_model_identity = (
            model_context.get("implicit_context", {})
            .get("requested_model_resolution", {})
            .get("resolved_model_identity")
        )
        parent_requested_model = (
            model_context.get("implicit_context", {})
            .get("requested_model_resolution", {})
            .get("parent_requested_model")
        )
        requested_model_identity = (
            response.requested_model_identity
            or resolved_model_identity
            or request.model
        )
        record = {
            "ordinal": len(envelope["responses"]) + 1,
            "purpose": purpose,
            "request_identity": request_identity,
            "input_bundle_identity": bundle["bundle_identity"],
            "response_identity": response_identity,
            "raw_response": raw_representation,
            "raw_response_hash": raw_hash,
            "parsed_payload": None,
            "parsed_payload_hash": None,
            "validation": {
                "valid": False,
                "error": "validation-pending",
            },
            "reported_model": response.reported_model,
            "reported_settings": (
                copy.deepcopy(dict(response.reported_settings))
                if response.reported_settings is not None
                else None
            ),
            "requested_model_identity": requested_model_identity,
            "settings_source": response.settings_source,
            "auxiliary_models": list(response.auxiliary_models),
        }
        envelope["responses"].append(record)
        envelope["reported"]["models"].append(response.reported_model)
        envelope["reported"]["settings"].append(
            copy.deepcopy(dict(response.reported_settings))
            if response.reported_settings is not None
            else None
        )
        envelope["reported"]["auxiliary_models"].extend(
            model
            for model in response.auxiliary_models
            if model not in envelope["reported"]["auxiliary_models"]
        )
        if (
            response.reported_model != requested_model_identity
            or (
                adapter.name in {"claude", "codex"}
                and requested_model_identity != resolved_model_identity
            )
            or (
                adapter.name == "codex"
                and parent_requested_model is not None
                and parent_requested_model != resolved_model_identity
            )
            or response.reported_settings is None
            or dict(response.reported_settings) != dict(request.settings)
        ):
            envelope["reuse_eligibility"] = {
                "available": False,
                "reason": "reported-model-or-settings-not-exactly-bound",
                "unobserved_context": list(
                    dict.fromkeys(
                        [
                            *envelope["reuse_eligibility"]["unobserved_context"],
                            "reported-model-or-settings",
                        ]
                    )
                ),
            }
        envelope["observations"] = {
            **envelope["observations"],
            f"response-{record['ordinal']:02d}": copy.deepcopy(
                dict(response.observations)
            ),
        }
        # Persist the exact answer representation before parsing, validation,
        # or hashing any decoded JSON value can fail.
        _validate_schema(ENVELOPE_SCHEMA, envelope)
        _atomic_json(envelope_path, envelope)

        try:
            _verify_immutable(immutable)
        except InputMutationError as error:
            record["validation"] = {"valid": False, "error": str(error)}
            envelope["state"] = "failed"
            envelope["diagnostics"].append(
                {"code": "immutable-input-mutated", "detail": str(error)}
            )
            _validate_schema(ENVELOPE_SCHEMA, envelope)
            _atomic_json(envelope_path, envelope)
            return StructuredSynthesisResult(
                "failed",
                envelope_path,
                bundle_path,
                None,
                None,
                envelope["calls"]["total"],
                diagnostics=tuple(envelope["diagnostics"]),
            )

        parsed: dict[str, Any] | None = None
        validation_error: str | None = None
        try:
            parsed = _parse_response(response.raw_text, bundle)
            _validate_model_evidence(parsed, bundle)
        except (StructuredSynthesisError, EvidenceScopeError) as error:
            validation_error = str(error)
        record["parsed_payload"] = parsed
        record["parsed_payload_hash"] = (
            content_hash(parsed) if parsed is not None else None
        )
        record["validation"] = {
            "valid": validation_error is None,
            "error": validation_error,
        }
        if validation_error is not None:
            diagnostic = {
                "code": "invalid-response",
                "detail": validation_error,
                "response_identity": response_identity,
            }
            envelope["diagnostics"].append(diagnostic)
            envelope["resolution_provenance"].append(
                {
                    "ordinal": len(envelope["resolution_provenance"]) + 1,
                    "kind": "repair-required",
                    **diagnostic,
                }
            )
            _atomic_json(envelope_path, envelope)
            prior_raw = raw_representation
            repair_diagnostics = [validation_error]
            purpose = "repair"
            continue
        assert parsed is not None
        if parsed["completion_status"] == "needs-evidence":
            new_evidence: list[dict[str, Any]] = []
            request_errors: list[str] = []
            for evidence_request in parsed["evidence_requests"]:
                try:
                    item = builder.read(
                        SourceNomination(
                            path=evidence_request["path"],
                            start_line=evidence_request["start_line"],
                            end_line=evidence_request["end_line"],
                            justification=evidence_request["reason"],
                            origin="parent-follow-up",
                        )
                    )
                except EvidenceScopeError as error:
                    request_errors.append(str(error))
                else:
                    new_evidence.append(item)
            if (
                len(bundle["source_evidence"]) + len(new_evidence)
                > request.limits.max_evidence_files
            ):
                request_errors.append("evidence request exceeds max_evidence_files")
            if request_errors:
                envelope["state"] = "unresolved"
                for detail in request_errors:
                    envelope["diagnostics"].append(
                        {"code": "evidence-request-rejected", "detail": detail}
                    )
                envelope["resolution_provenance"].append(
                    {
                        "ordinal": len(envelope["resolution_provenance"]) + 1,
                        "kind": "evidence-request-rejected",
                        "response_identity": response_identity,
                        "details": request_errors,
                    }
                )
                break
            if (
                envelope["calls"]["evidence_followup"]
                >= request.limits.evidence_followups
                or envelope["calls"]["total"] >= request.limits.total_calls
            ):
                envelope["state"] = "unresolved"
                envelope["diagnostics"].append(
                    {
                        "code": "evidence-budget-exhausted",
                        "detail": (
                            "Justified evidence requests remain unresolved at "
                            "the configured bound."
                        ),
                    }
                )
                envelope["resolution_provenance"].append(
                    {
                        "ordinal": len(envelope["resolution_provenance"]) + 1,
                        "kind": "unresolved-evidence",
                        "response_identity": response_identity,
                        "request_ids": [
                            item["request_id"] for item in parsed["evidence_requests"]
                        ],
                    }
                )
                break
            bundle["source_evidence"].extend(new_evidence)
            envelope["justifications"].extend(
                item["justification"] for item in new_evidence
            )
            _set_bundle_identity(bundle)
            _validate_schema(BUNDLE_SCHEMA, bundle)
            _atomic_json(bundle_path, bundle)
            envelope["input_bundle_identity"] = bundle["bundle_identity"]
            envelope["resolution_provenance"].append(
                {
                    "ordinal": len(envelope["resolution_provenance"]) + 1,
                    "kind": "evidence-supplied",
                    "response_identity": response_identity,
                    "request_ids": [
                        item["request_id"] for item in parsed["evidence_requests"]
                    ],
                    "new_bundle_identity": bundle["bundle_identity"],
                }
            )
            prior_raw = response.raw_text
            repair_diagnostics = []
            purpose = "evidence-followup"
            _atomic_json(envelope_path, envelope)
            continue
        if parsed["completion_status"] == "unresolved":
            envelope["state"] = "unresolved"
            envelope["accepted_response_identity"] = response_identity
            envelope["resolution_provenance"].append(
                {
                    "ordinal": len(envelope["resolution_provenance"]) + 1,
                    "kind": "model-unresolved",
                    "response_identity": response_identity,
                }
            )
            break
        accepted_payload = parsed
        envelope["accepted_response_identity"] = response_identity
        envelope["resolution_provenance"].append(
            {
                "ordinal": len(envelope["resolution_provenance"]) + 1,
                "kind": "response-accepted-for-assembly",
                "response_identity": response_identity,
            }
        )
        break

    if accepted_payload is None:
        if envelope["state"] != "unresolved":
            envelope["state"] = "failed"
            envelope["diagnostics"].append(
                {
                    "code": "response-budget-exhausted",
                    "detail": (
                        "No valid complete response was available within "
                        "configured limits."
                    ),
                }
            )
        _validate_schema(ENVELOPE_SCHEMA, envelope)
        _atomic_json(envelope_path, envelope)
        _verify_immutable(immutable)
        return StructuredSynthesisResult(
            envelope["state"],
            envelope_path,
            bundle_path,
            None,
            None,
            envelope["calls"]["total"],
            diagnostics=tuple(envelope["diagnostics"]),
        )

    try:
        document_path, markdown_path, section_dispositions = assembler.assemble(
            request, accepted_payload, artifact_dir
        )
    except StructuredSynthesisError as error:
        envelope["state"] = "failed"
        envelope["diagnostics"].append(
            {"code": "assembly-failed", "detail": str(error)}
        )
        _validate_schema(ENVELOPE_SCHEMA, envelope)
        _atomic_json(envelope_path, envelope)
        _verify_immutable(immutable)
        return StructuredSynthesisResult(
            "failed",
            envelope_path,
            bundle_path,
            None,
            None,
            envelope["calls"]["total"],
            diagnostics=tuple(envelope["diagnostics"]),
        )
    envelope["state"] = "synthesized"
    for disposition in section_dispositions:
        envelope["resolution_provenance"].append(
            {"ordinal": len(envelope["resolution_provenance"]) + 1, **disposition}
        )
    _validate_schema(ENVELOPE_SCHEMA, envelope)
    _atomic_json(envelope_path, envelope)
    _verify_immutable(immutable)
    return StructuredSynthesisResult(
        "synthesized",
        envelope_path,
        bundle_path,
        document_path,
        markdown_path,
        envelope["calls"]["total"],
    )


def _source_snapshot_value(snapshot: SourceSnapshot) -> dict[str, Any]:
    return {
        "head": snapshot.head,
        "working_tree_identity": snapshot.working_tree_identity,
        "tracked_tree_identity": snapshot.tracked_tree_identity,
        "dirty_paths": list(snapshot.dirty_paths),
        "untracked_paths": list(snapshot.untracked_paths),
    }


def _source_snapshot_from_value(value: Mapping[str, Any]) -> SourceSnapshot:
    return SourceSnapshot(
        head=str(value["head"]),
        working_tree_identity=str(value["working_tree_identity"]),
        tracked_tree_identity=str(value["tracked_tree_identity"]),
        dirty_paths=tuple(value["dirty_paths"]),
        untracked_paths=tuple(value["untracked_paths"]),
    )


def _dependency_value(record: DependencyRecord) -> dict[str, Any]:
    return {
        **record.reusable_payload(),
        "complete": record.complete,
        "unclassified_source_commands": list(record.unclassified_source_commands),
        "searches": [
            {
                "root": item.root,
                "resolved_root": item.resolved_root,
                "pattern": item.pattern,
                "options": {key: thaw(value) for key, value in item.options},
                "tree_identity": item.tree_identity,
                "tool": item.tool,
                "justification": item.justification,
                "outcome": item.outcome,
                "tracked_clean": item.tracked_clean,
                "replay_result_identity": item.replay_result_identity,
                "replay_context_identity": item.replay_context_identity,
                "observed_result_identity": item.observed_result_identity,
                "execution_cwd": item.execution_cwd,
            }
            for item in record.searches
        ],
    }


def _dependency_from_value(value: Mapping[str, Any]) -> DependencyRecord:
    from lib.structured_component_reuse import ReadObservation

    return DependencyRecord(
        schema_version=str(value["schema_version"]),
        harness=str(value["harness"]),
        complete=value["complete"] is True,
        reads=tuple(ReadObservation(**item) for item in value["reads"]),
        supplied_reads=tuple(value["supplied_reads"]),
        justifications=dict(value["justifications"]),
        files=tuple(FileDependency(**item) for item in value["files"]),
        searches=tuple(
            SearchObservation(
                root=item["root"],
                resolved_root=item.get("resolved_root", item["root"]),
                pattern=item["pattern"],
                options=tuple(sorted(item["options"].items())),
                tree_identity=item["tree_identity"],
                tool=item["tool"],
                justification=item["justification"],
                outcome=item.get("outcome", "observed-by-harness"),
                tracked_clean=item.get("tracked_clean", True),
                replay_result_identity=item.get("replay_result_identity", ""),
                replay_context_identity=item.get("replay_context_identity", ""),
                observed_result_identity=item.get("observed_result_identity", ""),
                execution_cwd=item.get("execution_cwd", "."),
            )
            for item in value["searches"]
        ),
        unclassified_source_commands=tuple(value["unclassified_source_commands"]),
        accounted_untracked=tuple(value["accounted_untracked"]),
        generated_inputs=tuple(
            FileDependency(**item) for item in value["generated_inputs"]
        ),
        external_inputs=tuple(
            FileDependency(**item) for item in value["external_inputs"]
        ),
    )


def _input_value(inputs: InputIdentities) -> dict[str, Any]:
    return {
        "exact": inputs.exact,
        "semantic": inputs.semantic,
        "semantic_payload": thaw(inputs.semantic_payload),
        "analyzer_binding": thaw(inputs.analyzer_binding),
        "recent_changes": thaw(inputs.recent_changes),
    }


def _input_from_value(value: Mapping[str, Any]) -> InputIdentities:
    return InputIdentities(
        exact=str(value["exact"]),
        semantic=str(value["semantic"]),
        semantic_payload=dict(value["semantic_payload"]),
        analyzer_binding=dict(value["analyzer_binding"]),
        recent_changes=tuple(value["recent_changes"]),
    )


def _compatibility_value(value: ProducerCompatibility) -> dict[str, str]:
    return {
        "analyzer_schema_version": value.analyzer_schema_version,
        "analyzer_version": value.analyzer_version,
        "analyzer_build_identity": value.analyzer_build_identity,
        "normalizer_version": value.normalizer_version,
        "synthesis_contract_version": value.synthesis_contract_version,
    }


def _record_without_identity(record: Mapping[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(dict(record))
    value.pop("record_identity", None)
    return value


def _successful_response(
    synthesis_bytes: bytes,
    bundle: Mapping[str, Any],
) -> tuple[dict[str, Any], str]:
    try:
        envelope = json.loads(synthesis_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReuseRecordError(f"predecessor synthesis is not JSON: {error}") from error
    try:
        _validate_schema(ENVELOPE_SCHEMA, envelope)
        _validate_schema(BUNDLE_SCHEMA, bundle)
    except StructuredSynthesisError as error:
        raise ReuseRecordError(str(error)) from error
    if envelope.get("state") != "synthesized":
        raise ReuseRecordError("predecessor synthesis did not complete successfully")
    eligibility = envelope.get("reuse_eligibility")
    if not isinstance(eligibility, Mapping) or eligibility.get("available") is not True:
        raise ReuseRecordError("predecessor producing envelope is reuse-ineligible")
    if envelope.get("input_bundle_identity") != bundle.get("bundle_identity"):
        raise ReuseRecordError("predecessor synthesis/evidence bundle mismatch")
    if content_hash(_bundle_without_identity(bundle)) != bundle.get("bundle_identity"):
        raise ReuseRecordError("predecessor evidence bundle identity is invalid")
    accepted_identity = envelope.get("accepted_response_identity")
    responses = envelope.get("responses", ())
    accepted_indexes = [
        index
        for index, item in enumerate(responses)
        if item.get("response_identity") == accepted_identity
    ]
    if len(accepted_indexes) != 1:
        raise ReuseRecordError("predecessor accepted response is missing or ambiguous")
    accepted_index = accepted_indexes[0]
    response = responses[accepted_index]
    requested = envelope.get("requested")
    if not isinstance(requested, Mapping):
        raise ReuseRecordError("predecessor requested producer identity is missing")
    model_context = bundle.get("synthesis_configuration", {}).get("model_context", {})
    if (
        not isinstance(model_context, Mapping)
        or requested.get("harness") != model_context.get("adapter")
        or requested.get("model") != model_context.get("requested_model")
        or requested.get("settings") != model_context.get("requested_settings")
    ):
        raise ReuseRecordError(
            "predecessor requested producer is not bound to the evidence bundle"
        )
    if (
        not isinstance(response.get("requested_model_identity"), str)
        or response.get("reported_model") != response.get("requested_model_identity")
        or response.get("reported_settings") != requested.get("settings")
    ):
        raise ReuseRecordError(
            "predecessor requested/reported producer settings are incompatible"
        )
    if requested.get("harness") in {"claude", "codex"}:
        resolution = model_context.get("implicit_context", {}).get(
            "requested_model_resolution", {}
        )
        resolved_model_identity = resolution.get("resolved_model_identity")
        if (
            not isinstance(resolved_model_identity, str)
            or response.get("requested_model_identity") != resolved_model_identity
        ):
            raise ReuseRecordError(
                "predecessor model resolution is not bound to the request"
            )
        parent_requested_model = resolution.get("parent_requested_model")
        if (
            requested.get("harness") == "codex"
            and parent_requested_model is not None
            and parent_requested_model != resolved_model_identity
        ):
            raise ReuseRecordError(
                "predecessor Codex explicit model request was substituted"
            )
    reported = envelope.get("reported")
    models = reported.get("models") if isinstance(reported, Mapping) else None
    settings = reported.get("settings") if isinstance(reported, Mapping) else None
    auxiliary = (
        reported.get("auxiliary_models") if isinstance(reported, Mapping) else None
    )
    if (
        not isinstance(models, list)
        or not isinstance(settings, list)
        or not isinstance(auxiliary, list)
        or len(models) != len(responses)
        or len(settings) != len(responses)
        or models[accepted_index] != response.get("reported_model")
        or settings[accepted_index] != response.get("reported_settings")
        or not all(item in auxiliary for item in response.get("auxiliary_models") or ())
    ):
        raise ReuseRecordError("predecessor producing model audit is inconsistent")
    raw_representation = response.get("raw_response")
    parsed = response.get("parsed_payload")
    if not isinstance(parsed, dict):
        raise ReuseRecordError("predecessor accepted response bytes are missing")
    try:
        raw = _raw_response_text(raw_representation)
        expected_raw_hash = _raw_response_hash(raw_representation)
    except (ReuseRecordError, UnicodeEncodeError, TypeError, ValueError) as error:
        raise ReuseRecordError(
            "predecessor raw response representation is invalid"
        ) from error
    if response.get("raw_response_hash") != expected_raw_hash:
        raise ReuseRecordError("predecessor raw response hash is invalid")
    if response.get("parsed_payload_hash") != content_hash(parsed):
        raise ReuseRecordError("predecessor parsed response hash is invalid")
    try:
        reparsed = _parse_response(raw, bundle)
        _validate_model_evidence(reparsed, bundle)
    except (StructuredSynthesisError, EvidenceScopeError) as error:
        raise ReuseRecordError(f"predecessor response is invalid: {error}") from error
    if reparsed != parsed or response.get("validation", {}).get("valid") is not True:
        raise ReuseRecordError("predecessor raw and parsed responses are inconsistent")
    if not isinstance(accepted_identity, str) or not accepted_identity:
        raise ReuseRecordError("predecessor response identity is missing")
    return parsed, accepted_identity


class PrivateRunRecordStore:
    """Strict loader/writer for the phase-three private staged run record."""

    _ARTIFACTS = {
        "evidence_bundle": "evidence-bundle.json",
        "synthesis": "synthesis.json",
        "document": "document.json",
        "markdown": "candidate.md",
    }

    def __init__(
        self, architecture_dir: Path, assembler: GoStructuredAssembler
    ) -> None:
        self.architecture_dir = architecture_dir.resolve()
        self.assembler = assembler

    def directory(self, version_scope: str, component: str) -> Path:
        for label, value in (("version", version_scope), ("component", component)):
            if (
                not value
                or Path(value).name != value
                or value in {".", ".."}
                or any(ord(character) < 32 for character in value)
            ):
                raise ReuseConfigurationError(f"invalid predecessor {label}: {value!r}")
        directory = (
            self.architecture_dir
            / version_scope
            / component
            / ".generation"
            / "structured"
        ).resolve()
        try:
            directory.relative_to(self.architecture_dir)
        except ValueError as error:
            raise ReuseConfigurationError(
                "predecessor location escapes architecture"
            ) from error
        return directory

    def invalidate(self, version_scope: str, component: str) -> None:
        (self.directory(version_scope, component) / RUN_RECORD_FILENAME).unlink(
            missing_ok=True
        )

    def load(self, version_scope: str, component: str) -> AcceptedSnapshot:
        directory = self.directory(version_scope, component)
        record_path = directory / RUN_RECORD_FILENAME
        try:
            record = json.loads(record_path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            raise ReuseRecordError(
                f"invalid predecessor run record {record_path}: {error}"
            ) from error
        try:
            _validate_schema(RUN_RECORD_SCHEMA, record)
        except StructuredSynthesisError as error:
            raise ReuseRecordError(str(error)) from error
        if record["record_identity"] != content_hash(_record_without_identity(record)):
            raise ReuseRecordError("predecessor run record identity is invalid")
        if record["version_scope"] != version_scope or record["component"] != component:
            raise ReuseRecordError("predecessor run record selection is inconsistent")
        artifacts: dict[str, bytes] = {}
        for name, filename in {
            **self._ARTIFACTS,
            "synthesis_bundle": record["artifacts"]["synthesis_bundle"]["path"],
        }.items():
            reference = record["artifacts"][name]
            allowed_paths = (
                {"evidence-bundle.json", SYNTHESIS_BUNDLE_FILENAME}
                if name == "synthesis_bundle"
                else {filename}
            )
            if reference["path"] not in allowed_paths:
                raise ReuseRecordError(f"predecessor {name} path is not canonical")
            path = directory / reference["path"]
            try:
                raw = path.read_bytes()
            except OSError as error:
                raise ReuseRecordError(
                    f"predecessor {name} is missing: {error}"
                ) from error
            if content_hash(raw) != reference["content_hash"]:
                raise ReuseRecordError(f"predecessor {name} hash is invalid")
            artifacts[name] = raw
        try:
            bundle = json.loads(artifacts["evidence_bundle"])
            document = json.loads(artifacts["document"])
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ReuseRecordError(
                f"predecessor artifact is not JSON: {error}"
            ) from error
        try:
            _validate_schema(BUNDLE_SCHEMA, bundle)
        except StructuredSynthesisError as error:
            raise ReuseRecordError(str(error)) from error
        if content_hash(_bundle_without_identity(bundle)) != bundle.get(
            "bundle_identity"
        ):
            raise ReuseRecordError(
                "predecessor current evidence bundle identity is invalid"
            )
        synthesis_bundle = json.loads(artifacts["synthesis_bundle"])
        _, response_identity = _successful_response(
            artifacts["synthesis"], synthesis_bundle
        )
        if record["response_identity"] != response_identity:
            raise ReuseRecordError("predecessor response identity is inconsistent")
        try:
            with tempfile.TemporaryDirectory(prefix="structured-predecessor-") as raw:
                rendered = Path(raw) / "candidate.md"
                document_path = Path(raw) / "document.json"
                document_path.write_bytes(artifacts["document"])
                self.assembler.validate_and_render(document_path, rendered)
                if rendered.read_bytes() != artifacts["markdown"]:
                    raise ReuseRecordError(
                        "predecessor Markdown does not match the current renderer"
                    )
        except StructuredSynthesisError as error:
            raise ReuseRecordError(
                f"predecessor document fails current Go validation: {error}"
            ) from error
        identity = ComponentIdentity(**record["identity"])
        compatibility = ProducerCompatibility(**record["compatibility"])
        dependencies = _dependency_from_value(record["dependencies"])
        source_state = SourceRunState(
            _source_snapshot_from_value(record["source_state"]["start"]),
            _source_snapshot_from_value(record["source_state"]["end"]),
        )
        inputs = _input_from_value(record["inputs"])
        snapshot = AcceptedSnapshot(
            snapshot_id=record["snapshot_id"],
            platform=record["version_scope"],
            identity=identity,
            accepted=True,
            route=record["route"],
            inputs=inputs,
            compatibility=compatibility,
            dependencies=dependencies,
            source_state=source_state,
            synthesis_bytes=artifacts["synthesis"],
            synthesis_integrity=record["artifacts"]["synthesis"]["content_hash"],
            response_identity=response_identity,
            document=document,
            document_integrity=record["document_integrity"],
        )
        expected_snapshot_id = content_hash(
            {
                "version_scope": version_scope,
                "component": component,
                "document": record["artifacts"]["document"]["content_hash"],
                "synthesis": record["artifacts"]["synthesis"]["content_hash"],
            }
        )
        if snapshot.snapshot_id != expected_snapshot_id:
            raise ReuseRecordError("predecessor snapshot identity is invalid")
        if content_hash(document) != snapshot.document_integrity:
            raise ReuseRecordError("predecessor document integrity is invalid")
        if (
            content_hash(thaw(snapshot.inputs.semantic_payload))
            != snapshot.inputs.semantic
        ):
            raise ReuseRecordError("predecessor semantic input identity is invalid")
        if (
            thaw(snapshot.inputs.semantic_payload).get("dependencies")
            != snapshot.dependencies.reusable_payload()
        ):
            raise ReuseRecordError("predecessor dependency/input binding is invalid")
        analyzer = bundle["analyzer"]["payload"]
        expected_binding = {
            "component": analyzer.get("component"),
            "repository": analyzer.get("repo"),
            "commit_sha": analyzer.get("commit_sha"),
            "extracted_at": analyzer.get("extracted_at"),
            "analyzer_version": analyzer.get("analyzer_version"),
            "schema_version": analyzer.get("schema_version"),
            "bundle_fingerprint": _analyzer_bundle_fingerprint(analyzer),
        }
        if thaw(snapshot.inputs.analyzer_binding) != expected_binding:
            raise ReuseRecordError("predecessor analyzer/input binding is invalid")
        supplied = {
            item["path"]: (item["whole_file_hash"], item["justification"])
            for item in bundle["source_evidence"]
        }
        dependency_files = {
            item.path: item.content_hash for item in snapshot.dependencies.files
        }
        if (
            set(supplied) != set(snapshot.dependencies.supplied_reads)
            or any(
                dependency_files.get(path) != value[0]
                for path, value in supplied.items()
            )
            or any(
                snapshot.dependencies.justifications.get(path) != value[1]
                for path, value in supplied.items()
            )
        ):
            raise ReuseRecordError("predecessor evidence/dependency binding is invalid")
        binding_errors = _predecessor_document_binding_errors(snapshot)
        if binding_errors:
            raise ReuseRecordError(
                "predecessor snapshot/document binding is invalid: "
                + "; ".join(binding_errors)
            )
        return snapshot

    def save(
        self,
        *,
        version_scope: str,
        component: str,
        identity: ComponentIdentity,
        inputs: InputIdentities,
        compatibility: ProducerCompatibility,
        dependencies: DependencyRecord,
        source_state: SourceRunState,
        response_identity: str,
        rebindings: Sequence[Mapping[str, Any]],
    ) -> Path:
        directory = self.directory(version_scope, component)
        artifact_values: dict[str, dict[str, str]] = {}
        for name, filename in self._ARTIFACTS.items():
            path = directory / filename
            if not path.is_file():
                raise ReuseRecordError(f"completed run lacks {filename}")
            artifact_values[name] = {
                "path": filename,
                "content_hash": file_hash(path),
            }
        synthesis_bytes = (directory / "synthesis.json").read_bytes()
        bundle = json.loads((directory / "evidence-bundle.json").read_text())
        try:
            _, actual_response_identity = _successful_response(synthesis_bytes, bundle)
        except ReuseRecordError:
            synthesis_bundle_path = directory / SYNTHESIS_BUNDLE_FILENAME
            if not synthesis_bundle_path.is_file():
                raise
            synthesis_bundle = json.loads(synthesis_bundle_path.read_text())
            _, actual_response_identity = _successful_response(
                synthesis_bytes, synthesis_bundle
            )
        else:
            synthesis_bundle_path = directory / "evidence-bundle.json"
        artifact_values["synthesis_bundle"] = {
            "path": synthesis_bundle_path.name,
            "content_hash": file_hash(synthesis_bundle_path),
        }
        if response_identity != actual_response_identity:
            raise ReuseRecordError("completed run response identity is inconsistent")
        document = json.loads((directory / "document.json").read_text())
        _validate_schema(DOCUMENT_SCHEMA, document)
        semantic_payload = thaw(inputs.semantic_payload)
        if content_hash(semantic_payload) != inputs.semantic:
            raise ReuseRecordError("completed run semantic identity is inconsistent")
        if semantic_payload.get("key_version") != SEMANTIC_KEY_VERSION:
            raise ReuseRecordError("completed run semantic key version is unsupported")
        if semantic_payload.get("dependencies") != dependencies.reusable_payload():
            raise ReuseRecordError("completed run dependency identity is inconsistent")
        analyzer = bundle["analyzer"]["payload"]
        expected_binding = {
            "component": analyzer.get("component"),
            "repository": analyzer.get("repo"),
            "commit_sha": analyzer.get("commit_sha"),
            "extracted_at": analyzer.get("extracted_at"),
            "analyzer_version": analyzer.get("analyzer_version"),
            "schema_version": analyzer.get("schema_version"),
            "bundle_fingerprint": _analyzer_bundle_fingerprint(analyzer),
        }
        if thaw(inputs.analyzer_binding) != expected_binding:
            raise ReuseRecordError("completed run analyzer identity is inconsistent")
        component_map = (
            document.get("assembly_inputs", {})
            .get("component_map", {})
            .get("value", {})
        )
        map_components = (
            component_map.get("components", {})
            if isinstance(component_map, Mapping)
            else {}
        )
        document_component = (
            map_components.get(identity.component)
            if isinstance(map_components, Mapping)
            else None
        )
        if not isinstance(document_component, Mapping) or (
            _go_component_configuration(document_component)
            != _go_component_configuration(
                semantic_payload.get("component_configuration") or {}
            )
        ):
            raise ReuseRecordError(
                "completed run component configuration is inconsistent"
            )
        probe = AcceptedSnapshot(
            snapshot_id="pending",
            platform=version_scope,
            identity=identity,
            accepted=True,
            route=SYNTHESIS_ROUTE,
            inputs=inputs,
            compatibility=compatibility,
            dependencies=dependencies,
            source_state=source_state,
            synthesis_bytes=synthesis_bytes,
            synthesis_integrity=content_hash(synthesis_bytes),
            response_identity=response_identity,
            document=document,
            document_integrity=content_hash(document),
        )
        binding_errors = _predecessor_document_binding_errors(probe)
        if binding_errors:
            raise ReuseRecordError(
                "completed run document/input binding is inconsistent: "
                + "; ".join(binding_errors)
            )
        snapshot_id = content_hash(
            {
                "version_scope": version_scope,
                "component": component,
                "document": artifact_values["document"]["content_hash"],
                "synthesis": artifact_values["synthesis"]["content_hash"],
            }
        )
        record = {
            "schema_version": SCHEMA_VERSION,
            "record_kind": PRIVATE_RUN_RECORD,
            "record_identity": "",
            "state": "completed",
            "acceptance": "validated-private-assembly",
            "route": SYNTHESIS_ROUTE,
            "snapshot_id": snapshot_id,
            "version_scope": version_scope,
            "component": component,
            "identity": {
                "component": identity.component,
                "repository": identity.repository,
                "aliases": list(identity.aliases),
            },
            "inputs": _input_value(inputs),
            "compatibility": _compatibility_value(compatibility),
            "dependencies": _dependency_value(dependencies),
            "source_state": {
                "start": _source_snapshot_value(source_state.start),
                "end": _source_snapshot_value(source_state.end),
            },
            "response_identity": response_identity,
            "document_integrity": content_hash(document),
            "artifacts": artifact_values,
            "target_rebindings": copy.deepcopy(list(rebindings)),
            "migration": {
                "phase": "P4",
                "obligation": (
                    "Bind to the published four-core snapshot and retain essential "
                    "metadata in core artifacts before publication."
                ),
            },
        }
        record["record_identity"] = content_hash(_record_without_identity(record))
        _validate_schema(RUN_RECORD_SCHEMA, record)
        path = directory / RUN_RECORD_FILENAME
        _atomic_json(path, record)
        return path


def _component_reuse_configuration(component: Mapping[str, Any]) -> dict[str, Any]:
    operational = {
        "checkout_path",
        "checkout_branch",
        "has_architecture",
        "key",
        "ref",
        "release_label",
        "target_release",
        "version_scope",
        "integration_status",
        "platform_integration",
        "platform_membership",
    }
    return {
        str(key): copy.deepcopy(value)
        for key, value in component.items()
        if key not in operational
    }


def _go_component_configuration(component: Mapping[str, Any]) -> dict[str, Any]:
    """Project the fields the Go component-map decoder actually consumes."""

    return {
        key: copy.deepcopy(component.get(key, ""))
        for key in ("repo_org", "repo_name", "repo_url")
    }


def _portable_overlays(
    overlays: Sequence[Mapping[str, Any]],
    component: str,
    raw_component: Mapping[str, Any],
) -> list[dict[str, Any]]:
    identities = {component, str(raw_component.get("repo_name") or "")}
    result: list[dict[str, Any]] = []
    for overlay in overlays:
        affects = overlay.get("affects", ())
        if not isinstance(affects, (list, tuple)) or not (
            "platform" in affects or identities.intersection(affects)
        ):
            continue
        result.append(
            {
                "path": Path(overlay["path"]).name,
                "title": overlay["title"],
                "affects": list(overlay["affects"]),
                "integration_status": overlay.get("integration_status"),
            }
        )
    return result


def _authority_identity(value: Any) -> Any:
    """Remove only target-version/fingerprint bindings from trusted authority."""

    if isinstance(value, Mapping):
        return {
            str(key): _authority_identity(item)
            for key, item in value.items()
            if key
            not in {"version_scope", "bundle_fingerprint", "proposal_fingerprint"}
        }
    if isinstance(value, (list, tuple)):
        return [_authority_identity(item) for item in value]
    return copy.deepcopy(value)


def _reuse_settings(
    request: StructuredSynthesisRequest,
    adapter: StructuredAdapter,
    bundle: Mapping[str, Any],
) -> dict[str, Any]:
    context_identity, context_complete, context_payload = _context_identity(
        request, adapter
    )
    return {
        "prompt_protocol": PROMPT_PROTOCOL,
        "response_instructions": PARENT_RESPONSE_INSTRUCTIONS,
        "instructions": request.instructions,
        "distribution": request.distribution,
        "semantic_configuration": copy.deepcopy(dict(request.semantic_configuration)),
        "model_context_identity": context_identity,
        "model_context_complete": context_complete,
        "model_context": context_payload,
        "assembly_policies": _authority_identity(request.assembly_policies),
        "section_policy": _authority_identity(request.section_policy),
        "corrections": _authority_identity(
            [
                item
                for item in request.corrections
                if item.get("version_scope") == request.version_scope
            ]
        ),
        "model_visible_observations": copy.deepcopy(
            dict(bundle.get("observations") or {})
        ),
        "source_evidence_selections": [
            {
                key: copy.deepcopy(value)
                for key, value in item.items()
                if key != "revision"
            }
            for item in bundle.get("source_evidence", ())
        ],
        "limits": {
            "total_calls": request.limits.total_calls,
            "evidence_followups": request.limits.evidence_followups,
            "repairs": request.limits.repairs,
            "max_evidence_files": request.limits.max_evidence_files,
            "max_lines_per_read": request.limits.max_lines_per_read,
        },
    }


def _dependencies_from_bundle(
    bundle: Mapping[str, Any], adapter: StructuredAdapter, source: SourceSnapshot
) -> DependencyRecord:
    evidence = bundle.get("source_evidence", ())
    supplied = tuple(sorted({str(item["path"]) for item in evidence}))
    justifications = {
        str(item["path"]): str(item["justification"]) for item in evidence
    }
    files = tuple(
        FileDependency(
            path,
            str(
                next(
                    item["whole_file_hash"] for item in evidence if item["path"] == path
                )
            ),
        )
        for path in supplied
    )
    accounted_untracked = tuple(
        path for path in supplied if path in set(source.untracked_paths)
    )
    return DependencyRecord(
        harness=adapter.name,
        complete=True,
        reads=(),
        supplied_reads=supplied,
        justifications=justifications,
        files=files,
        searches=(),
        accounted_untracked=accounted_untracked,
    )


def _producer_compatibility(analyzer: Mapping[str, Any]) -> ProducerCompatibility:
    project = Path(__file__).resolve().parent.parent
    source_identity = directory_tree_identity(
        project, "src/arch-analyzer", tracked_only=False
    )
    return ProducerCompatibility(
        analyzer_schema_version=str(analyzer.get("schema_version") or ""),
        analyzer_version=str(analyzer.get("analyzer_version") or ""),
        analyzer_build_identity=content_hash(
            {
                "analyzer_version": analyzer.get("analyzer_version"),
                "source_tree_identity": source_identity,
            }
        ),
        normalizer_version=NORMALIZER_VERSION,
        synthesis_contract_version=SYNTHESIS_CONTRACT_VERSION,
    )


def _current_input_identities(
    request: StructuredSynthesisRequest,
    adapter: StructuredAdapter,
    bundle: Mapping[str, Any],
    raw_component: Mapping[str, Any],
    overlays: Sequence[Mapping[str, Any]],
    dependencies: DependencyRecord,
) -> InputIdentities:
    schemas, _ = _schemas()
    return build_input_identities(
        analyzer_input=bundle["analyzer"]["payload"],
        component_configuration=_component_reuse_configuration(raw_component),
        overlays=_portable_overlays(overlays, request.component, raw_component),
        contracts={
            name: schemas[name]
            for name in (RESPONSE_SCHEMA, PATCH_SCHEMA, POLICY_SCHEMA, DOCUMENT_SCHEMA)
        },
        settings=_reuse_settings(request, adapter, bundle),
        dependencies=dependencies,
        checkout_root=request.checkout_root,
    )


def _identity_from_document(document: Mapping[str, Any]) -> ComponentIdentity:
    identity = document.get("identity")
    if not isinstance(identity, Mapping):
        raise ReuseRecordError("normalized target identity is missing")
    return ComponentIdentity(
        component=str(identity.get("component") or ""),
        repository=str(identity.get("repository") or ""),
        aliases=tuple(identity.get("aliases") or ()),
    )


def _rebind_predecessor_payload(
    payload: Mapping[str, Any],
    request: StructuredSynthesisRequest,
) -> tuple[dict[str, Any], StructuredSynthesisRequest, list[dict[str, Any]]]:
    """Rebind copies of proposals/policies; never alter the retained response."""

    rebound_payload = copy.deepcopy(dict(payload))
    analyzer = json.loads(_bound_analyzer_bytes(request))
    target_fingerprint = _analyzer_bundle_fingerprint(analyzer)
    target_revision = str(analyzer.get("commit_sha") or "")

    def rebind_evidence(items: Any) -> None:
        if not isinstance(items, list):
            return
        for item in items:
            if isinstance(item, dict):
                item["revision"] = target_revision

    for section in rebound_payload["sections"]:
        rebind_evidence(section.get("evidence"))
        for block in section.get("blocks", ()):
            if not isinstance(block, dict):
                continue
            for row in block.get("rows", ()):
                if isinstance(row, dict):
                    rebind_evidence(row.get("evidence"))
    policies = {
        str(item.get("patch_id")): copy.deepcopy(dict(item))
        for item in request.assembly_policies
    }
    rebound_policies: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    for patch in rebound_payload["typed_patches"]:
        patch_id = patch["patch_id"]
        prior_bundle = patch["bundle_fingerprint"]
        patch["bundle_fingerprint"] = target_fingerprint
        for operation in patch["operations"]:
            rebind_evidence(operation.get("evidence"))
        policy = policies.pop(patch_id, None)
        record = {
            "kind": "typed-proposal-target-binding",
            "patch_id": patch_id,
            "response_id": rebound_payload["response_id"],
            "prior_bundle_fingerprint": prior_bundle,
            "target_bundle_fingerprint": target_fingerprint,
            "target_source_revision": target_revision,
            "authority_source": "trusted-current-parent-input",
        }
        if policy is not None:
            policy["version_scope"] = request.version_scope
            policy["bundle_fingerprint"] = target_fingerprint
            policy["proposal_fingerprint"] = _proposal_fingerprint(patch)
            rebound_policies.append(policy)
            record.update(
                {
                    "policy_id": policy.get("policy_id"),
                    "proposal_fingerprint": policy["proposal_fingerprint"],
                }
            )
        records.append(record)
    if policies:
        raise ReuseRecordError(
            "trusted policy has no predecessor proposal: " + ", ".join(sorted(policies))
        )
    section_policy = copy.deepcopy(dict(request.section_policy))
    if section_policy:
        section_policy["version_scope"] = request.version_scope
        records.append(
            {
                "kind": "section-policy-target-binding",
                "policy_id": section_policy.get("policy_id"),
                "response_id": rebound_payload["response_id"],
                "target_version_scope": request.version_scope,
                "authority_source": "trusted-current-parent-input",
            }
        )
    rebound_request = replace(
        request,
        assembly_policies=tuple(rebound_policies),
        section_policy=section_policy,
    )
    return rebound_payload, rebound_request, records


def _target_normalization(
    prior_payload: Mapping[str, Any],
    request: StructuredSynthesisRequest,
    assembler: GoStructuredAssembler,
) -> tuple[TargetNormalization, list[dict[str, Any]]]:
    payload, rebound_request, records = _rebind_predecessor_payload(
        prior_payload, request
    )
    with tempfile.TemporaryDirectory(prefix="structured-target-normalization-") as raw:
        target_dir = Path(raw)
        normalized, _, _ = assembler.assemble(
            replace(rebound_request, artifact_dir=target_dir), payload, target_dir
        )
        document = json.loads(normalized.read_text())
    return TargetNormalization.capture(document), records


def _go_revalidator(
    assembler: GoStructuredAssembler,
) -> Callable[[AcceptedSnapshot, ReuseTarget], RevalidationResult]:
    def revalidate(_prior: AcceptedSnapshot, target: ReuseTarget) -> RevalidationResult:
        if target.normalization is None:
            raise ReuseRecordError("target normalization is missing")
        document = thaw(target.normalization.document)
        with tempfile.TemporaryDirectory(prefix="structured-target-revalidate-") as raw:
            directory = Path(raw)
            document_path = directory / "document.json"
            markdown_path = directory / "candidate.md"
            _atomic_json(document_path, document)
            assembler.validate_and_render(document_path, markdown_path)
        return RevalidationResult(
            document=document,
            checks={
                "document_schema": True,
                "typed_references": True,
                "patch_policy": True,
                "current_acceptance_rules": True,
            },
        )

    return revalidate


def _load_platform_graph(path: Path) -> dict[str, Mapping[str, Any]]:
    try:
        value = yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError) as error:
        raise ReuseConfigurationError(
            f"cannot load platform graph {path}: {error}"
        ) from error
    if not isinstance(value, dict) or not all(
        isinstance(key, str) and isinstance(item, dict) for key, item in value.items()
    ):
        raise ReuseConfigurationError(
            "platform graph must contain object configurations"
        )
    return value


def _load_pipeline_inputs(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        raise ValueError("--structured-synthesis requires --structured-inputs")
    try:
        payload = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid structured inputs {path}: {error}") from error
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("structured inputs require schema_version 1.0.0")
    try:
        _validate_schema(INPUT_SCHEMA, payload)
    except StructuredSynthesisError as error:
        raise ValueError(f"invalid structured inputs {path}: {error}") from error
    return payload


def _record_producer_ineligible_failure(
    result: StructuredSynthesisResult,
    error: ReuseRecordError,
) -> StructuredSynthesisResult:
    envelope = json.loads(result.envelope_path.read_text())
    diagnostic = {"code": "producer-ineligible", "detail": str(error)}
    envelope["state"] = "failed"
    envelope["reuse_eligibility"] = {
        "available": False,
        "reason": "producer-ineligible",
        "unobserved_context": list(
            dict.fromkeys(
                [
                    *envelope.get("reuse_eligibility", {}).get(
                        "unobserved_context", []
                    ),
                    "reported-model-or-settings",
                ]
            )
        ),
    }
    envelope["diagnostics"].append(diagnostic)
    _validate_schema(ENVELOPE_SCHEMA, envelope)
    _atomic_json(result.envelope_path, envelope)
    return replace(
        result,
        state="failed",
        diagnostics=(*result.diagnostics, diagnostic),
    )


async def run_pipeline_seam(
    args: Any,
    components: Mapping[str, Any],
    *,
    architecture_dir: Path,
    distribution: str,
) -> None:
    """Concrete opt-in pipeline seam with validated P4 publication."""

    from lib.fetch import _ensure_arch_analyzer, load_platform_config
    from lib.phases.static_analysis import analyzer_output_dir
    from lib.structured_component_publication import (
        PublicationError,
        load_accepted_publication,
        load_published_reuse_snapshot,
        publish_private_run,
        recover_publication,
        validate_legacy_conversion_input,
    )
    from lib.version_index import _resolve_integration, load_active_overlays

    inputs = _load_pipeline_inputs(getattr(args, "structured_inputs", None))
    configured_components = inputs["components"]
    component_map_path = (
        architecture_dir / args.platform / "component-map.json"
    ).resolve()
    component_map_bytes = component_map_path.read_bytes()
    component_map = json.loads(component_map_bytes)
    raw_components = component_map.get("components")
    if not isinstance(raw_components, dict):
        raise ValueError("structured route requires object-form component-map")
    platforms_file = Path(getattr(args, "platforms_file", "platforms.yaml"))
    platform_config = load_platform_config(args.platform, str(platforms_file)) or {}
    active_overlays = load_active_overlays(
        Path(getattr(args, "overlays_dir", "overlays")), args.platform
    )
    assembler = GoStructuredAssembler(
        (await _ensure_arch_analyzer(),),
        Path(__file__).resolve().parent.parent / "src/arch-analyzer",
    )
    record_store = PrivateRunRecordStore(architecture_dir, assembler)
    harness = getattr(args, "harness", "claude")
    adapter = authenticated_harness_adapter(harness)
    parent_model = args.model or ("opus" if harness == "claude" else None)
    parent_settings = (
        {"max_budget_usd": args.max_budget_usd}
        if getattr(args, "max_budget_usd", None) is not None
        else {}
    )
    try:
        prepared = await adapter.prepare(parent_model, parent_settings)
    except RateLimitError as error:
        _write_preflight_rate_limit_diagnostic(
            architecture_dir,
            args.platform,
            harness=harness,
            requested_model=parent_model,
            error=error,
        )
        raise
    limits = SynthesisLimits(
        total_calls=getattr(args, "structured_total_calls", 3),
        evidence_followups=getattr(args, "structured_evidence_followups", 1),
        repairs=getattr(args, "structured_repairs", 1),
    )
    selected = [
        item
        for item in sorted(components.values(), key=lambda value: value.key)
        if getattr(args, "force", False) or not item.has_architecture
    ]
    if getattr(args, "limit", None):
        selected = selected[: args.limit]
    for component in selected:
        component_overlays = copy.deepcopy(active_overlays)
        configured = copy.deepcopy(configured_components.get(component.key))
        if not isinstance(configured, dict):
            raise ValueError(f"structured inputs missing component {component.key!r}")
        raw_component = copy.deepcopy(raw_components.get(component.key))
        if not isinstance(raw_component, dict):
            raise ValueError(f"component-map missing component {component.key!r}")
        integration_status, _integration_source = _resolve_integration(
            component.key,
            raw_component,
            platform_config,
            component_overlays,
        )
        nominations = tuple(
            SourceNomination(
                path=item["path"],
                start_line=item["start_line"],
                end_line=item["end_line"],
                justification=item["justification"],
            )
            for item in configured.get("nominations", ())
        )
        analyzer_path = (
            analyzer_output_dir(architecture_dir, args.platform, component.key)
            / "component-architecture.json"
        ).resolve()
        analyzer_bytes = analyzer_path.read_bytes()
        analyzer_value = json.loads(analyzer_bytes)
        if not isinstance(analyzer_value, dict):
            raise ValueError("structured analyzer input must be a JSON object")
        validate_legacy_conversion_input(analyzer_value)
        artifact_dir = (
            architecture_dir
            / args.platform
            / component.key
            / ".generation"
            / "structured"
        )
        request = StructuredSynthesisRequest(
            artifact_dir=artifact_dir,
            checkout_root=component.checkout_path.resolve(),
            analyzer_path=analyzer_path,
            component_map_path=component_map_path,
            component=component.key,
            version_scope=args.platform,
            integration_status=integration_status,
            distribution=distribution,
            model=prepared.model,
            settings=copy.deepcopy(dict(prepared.settings)),
            instructions=str(inputs.get("instructions") or ""),
            analyzer_bytes=analyzer_bytes,
            component_map_bytes=component_map_bytes,
            nominations=nominations,
            allowed_followup_paths=tuple(configured.get("allowed_followup_paths", ())),
            corrections=tuple(configured.get("corrections", ())),
            assembly_policies=tuple(configured.get("assembly_policies", ())),
            section_policy=configured.get("section_policy", {}),
            observations=configured.get("observations", {}),
            semantic_configuration={
                **configured.get("semantic_configuration", {}),
            },
            limits=limits,
            force_refresh=getattr(args, "structured_refresh", False),
        )
        recover_publication(
            architecture_dir / args.platform / component.key,
            assembler,
        )
        source_start = capture_source_snapshot(request.checkout_root)
        bundle, _, _, _ = build_evidence_bundle(request, adapter)
        initial_source_bytes: dict[str, bytes] = {}
        for evidence in bundle["source_evidence"]:
            relative = str(evidence["path"])
            raw = (request.checkout_root / relative).read_bytes()
            if content_hash(raw) != evidence["whole_file_hash"]:
                raise InputMutationError(
                    "source evidence mutated while binding the pipeline seam: "
                    + relative
                )
            initial_source_bytes[relative] = raw
        request = replace(
            request,
            initial_evidence_bundle=copy.deepcopy(bundle),
            initial_source_bytes=initial_source_bytes,
        )
        dependencies = _dependencies_from_bundle(bundle, adapter, source_start)
        input_identities = _current_input_identities(
            request,
            adapter,
            bundle,
            raw_component,
            component_overlays,
            dependencies,
        )
        compatibility = _producer_compatibility(bundle["analyzer"]["payload"])
        rebindings: list[dict[str, Any]] = []
        reuse_selection = configured.get("reuse_from")
        if reuse_selection is not None:
            graph = _load_platform_graph(platforms_file)
            predecessor = resolve_predecessor(args.platform, graph)
            if predecessor != reuse_selection["version_scope"]:
                raise ReuseConfigurationError(
                    "trusted reuse_from version does not match the platform graph"
                )
            prior = None
            prior_record = None
            prior_bundle = None
            try:
                prior = record_store.load(
                    reuse_selection["version_scope"], reuse_selection["component"]
                )
            except ReuseRecordError:
                try:
                    prior = load_published_reuse_snapshot(
                        architecture_dir,
                        reuse_selection["version_scope"],
                        reuse_selection["component"],
                        assembler,
                    )
                    published = load_accepted_publication(
                        architecture_dir
                        / reuse_selection["version_scope"]
                        / reuse_selection["component"],
                        assembler,
                        repair_markdown=True,
                    ).document_value["publication"]["accepted_inputs"]
                    prior_record = published["run_record"]
                    prior_bundle = published["original_evidence_bundle"]
                except PublicationError:
                    request = replace(
                        request,
                        predecessor_miss_reasons=("predecessor-record-invalid",),
                    )
            if prior_record is None and prior is not None:
                prior_directory = record_store.directory(
                    reuse_selection["version_scope"], reuse_selection["component"]
                )
                prior_record = json.loads(
                    (prior_directory / RUN_RECORD_FILENAME).read_text()
                )
                prior_bundle = json.loads(
                    (
                        prior_directory
                        / prior_record["artifacts"]["synthesis_bundle"]["path"]
                    ).read_text()
                )
            if prior_record is not None and prior_bundle is not None:
                prior_payload, _ = _successful_response(
                    prior.synthesis_bytes, prior_bundle
                )
                normalization, rebindings = _target_normalization(
                    prior_payload, request, assembler
                )
                target_identity = _identity_from_document(normalization.document)
                prior = select_predecessor_snapshot(
                    [prior], predecessor, target_identity
                )
                target = ReuseTarget(
                    platform=args.platform,
                    identity=target_identity,
                    inputs=input_identities,
                    compatibility=compatibility,
                    dependencies=dependencies,
                    source_state=SourceRunState(source_start, source_start),
                    normalization=normalization,
                )
                request = replace(
                    request,
                    prior_snapshot=prior,
                    reuse_target=target,
                    revalidate_reuse=_go_revalidator(assembler),
                )
        record_store.invalidate(args.platform, component.key)
        result = await run_structured_synthesis(request, adapter, assembler)
        if result.state in {"synthesized", "reused"}:
            source_end = capture_source_snapshot(request.checkout_root)
            if source_start != source_end:
                raise StructuredSynthesisError(
                    "source checkout changed during structured assembly; "
                    "private run record was not persisted"
                )
            completed_bundle = json.loads(result.evidence_bundle_path.read_text())
            completed_dependencies = _dependencies_from_bundle(
                completed_bundle, adapter, source_end
            )
            completed_inputs = _current_input_identities(
                request,
                adapter,
                completed_bundle,
                raw_component,
                component_overlays,
                completed_dependencies,
            )
            completed_document = json.loads(result.document_path.read_text())
            completed_identity = _identity_from_document(completed_document)
            synthesis_bundle = completed_bundle
            if result.reused:
                synthesis_bundle_path = artifact_dir / SYNTHESIS_BUNDLE_FILENAME
                synthesis_bundle_path.write_bytes(_canonical(prior_bundle) + b"\n")
                synthesis_bundle = prior_bundle
            try:
                _, response_identity = _successful_response(
                    result.envelope_path.read_bytes(), synthesis_bundle
                )
                record_store.save(
                    version_scope=args.platform,
                    component=component.key,
                    identity=completed_identity,
                    inputs=completed_inputs,
                    compatibility=compatibility,
                    dependencies=completed_dependencies,
                    source_state=SourceRunState(source_start, source_end),
                    response_identity=response_identity,
                    rebindings=rebindings if result.reused else (),
                )
                publish_private_run(
                    architecture_dir=architecture_dir,
                    version_scope=args.platform,
                    component=component.key,
                    assembler=assembler,
                )
            except ReuseRecordError as error:
                failed_envelope = json.loads(result.envelope_path.read_text())
                if (
                    failed_envelope.get("reuse_eligibility", {}).get("reason")
                    != "reported-model-or-settings-not-exactly-bound"
                ):
                    raise
                record_store.invalidate(args.platform, component.key)
                result = _record_producer_ineligible_failure(result, error)
        print(
            f"Structured private result: {component.key}: {result.state}; "
            f"calls={result.calls}; artifacts={artifact_dir}"
        )
