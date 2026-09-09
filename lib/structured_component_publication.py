"""Validated four-file publication and deterministic interrupted-write recovery."""

from __future__ import annotations

import copy
import fcntl
import json
import os
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lib.structured_component_reuse import (
    AcceptedSnapshot,
    ComponentIdentity,
    ProducerCompatibility,
    SourceRunState,
)
from lib.structured_component_synthesis import (
    BUNDLE_SCHEMA,
    DOCUMENT_SCHEMA,
    ENVELOPE_SCHEMA,
    RUN_RECORD_SCHEMA,
    GoStructuredAssembler,
    PrivateRunRecordStore,
    ReuseRecordError,
    _analyzer_bundle_fingerprint,
    _bundle_without_identity,
    _canonical,
    _dependency_from_value,
    _identity_from_document,
    _input_from_value,
    _record_without_identity,
    _source_snapshot_from_value,
    _successful_response,
    _validate_schema,
    content_hash,
)

PUBLICATION_CONTRACT = "structured-component-publication/v1"
PUBLISHED_DOCUMENT_SCHEMA = "1.1.0"
CORE_NAMES = ("analyzer.json", "synthesis.json", "document.json")
RECOVERY_SUFFIXES = ("next", "previous")
NON_COMPONENT_DIRECTORIES = frozenset(
    {
        "contracts",
        "diagrams",
        "logs",
        "metadata",
        "overlays",
        "prompts",
        "run-metadata",
        "runs",
    }
)


class PublicationError(RuntimeError):
    """A candidate or published snapshot is incomplete or inconsistent."""


def validate_legacy_conversion_input(analyzer: Mapping[str, Any]) -> None:
    """Reject legacy analyzer shapes the accepted v1 facts cannot preserve."""

    unsupported = [
        field
        for field in ("network_policies", "platform_webhooks")
        if analyzer.get(field)
    ]
    dockerfile_fields = {"path", "base_image", "user", "issues"}
    for index, item in enumerate(analyzer.get("dockerfiles") or []):
        if not isinstance(item, Mapping):
            raise PublicationError(f"legacy dockerfiles[{index}] is malformed")
        extras = sorted(set(item) - dockerfile_fields)
        if extras:
            unsupported.append(f"dockerfiles[{index}].{','.join(extras)}")
    webhook_fields = {
        "name",
        "type",
        "service_ref",
        "path",
        "port",
        "failure_policy",
        "rules",
        "sources",
        "purpose",
    }
    for index, item in enumerate(analyzer.get("webhooks") or []):
        if not isinstance(item, Mapping):
            raise PublicationError(f"legacy webhooks[{index}] is malformed")
        extras = sorted(set(item) - webhook_fields)
        if extras:
            unsupported.append(f"webhooks[{index}].{','.join(extras)}")
    evidence = analyzer.get("cross_cutting_evidence")
    if isinstance(evidence, Mapping) and "fips" in evidence:
        fips = evidence["fips"]
        if not isinstance(fips, list) or not fips:
            raise PublicationError("legacy FIPS evidence is ambiguous or malformed")
        for index, item in enumerate(fips):
            if (
                not isinstance(item, Mapping)
                or not isinstance(item.get("claim"), str)
                or item.get("status")
                not in {
                    "verified",
                    "supported",
                    "unsupported",
                    "unknown",
                    "unresolved",
                    "not-applicable",
                }
                or not isinstance(item.get("sources"), list)
            ):
                raise PublicationError(
                    f"legacy FIPS evidence[{index}] is ambiguous or malformed"
                )
    elif evidence is not None and not isinstance(evidence, Mapping):
        raise PublicationError("legacy cross-cutting evidence is malformed")
    if unsupported:
        raise PublicationError(
            "legacy conversion would drop unsupported fields: " + "; ".join(unsupported)
        )


@dataclass(frozen=True)
class AcceptedPublication:
    component_dir: Path
    markdown_path: Path
    analyzer: bytes
    synthesis: bytes
    document: bytes
    markdown: bytes
    document_value: Mapping[str, Any]


def has_publication_state(platform_dir: Path) -> bool:
    """Return whether a version contains visible or interrupted core state."""

    if not platform_dir.is_dir():
        return False
    for component_dir in platform_dir.iterdir():
        if (
            not component_dir.is_dir()
            or component_dir.name.startswith(".")
            or component_dir.name in NON_COMPONENT_DIRECTORIES
        ):
            continue
        for name in CORE_NAMES:
            if (component_dir / name).exists() or any(
                (component_dir / f".{name}.{suffix}").exists()
                for suffix in RECOVERY_SUFFIXES
            ):
                return True
    return False


def _atomic_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _replace(source: Path, destination: Path) -> None:
    os.replace(source, destination)
    directory = os.open(destination.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def _json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PublicationError(f"{label} is not valid JSON: {error}") from error
    if not isinstance(value, dict):
        raise PublicationError(f"{label} must be a JSON object")
    return value


def _bundle_identity(bundle: Mapping[str, Any], label: str) -> str:
    identity = bundle.get("bundle_identity")
    if identity != content_hash(_bundle_without_identity(bundle)):
        raise PublicationError(f"{label} bundle identity is invalid")
    return str(identity)


def _snapshot_id(
    *, analyzer_hash: str, synthesis_hash: str, record: Mapping[str, Any]
) -> str:
    return content_hash(
        {
            "contract": PUBLICATION_CONTRACT,
            "version_scope": record["version_scope"],
            "component": record["component"],
            "analyzer": analyzer_hash,
            "synthesis": synthesis_hash,
            "exact_input": record["inputs"]["exact"],
            "semantic_input": record["inputs"]["semantic"],
            "producer_build": record["compatibility"]["analyzer_build_identity"],
        }
    )


def _special_snapshot_id(
    *,
    analyzer_hash: str,
    synthesis_hash: str,
    component: str,
    version_scope: str,
) -> str:
    return content_hash(
        {
            "contract": PUBLICATION_CONTRACT,
            "version_scope": version_scope,
            "component": component,
            "analyzer": analyzer_hash,
            "synthesis": synthesis_hash,
            "acceptance": "deterministic-only",
        }
    )


def _render_published(assembler: GoStructuredAssembler, document: bytes) -> bytes:
    with tempfile.TemporaryDirectory(prefix="structured-publication-render-") as raw:
        directory = Path(raw)
        document_path = directory / "document.json"
        markdown_path = directory / "component.md"
        document_path.write_bytes(document)
        assembler._run(
            [
                "render-published-document",
                "--input",
                str(document_path),
                "--output",
                str(markdown_path),
            ]
        )
        return markdown_path.read_bytes()


def _validate_record_document_binding(
    record: Mapping[str, Any],
    document: Mapping[str, Any],
    analyzer: Mapping[str, Any],
) -> None:
    private_document = copy.deepcopy(dict(document))
    private_document.pop("publication", None)
    private_document["schema_version"] = "1.0.0"
    if content_hash(private_document) != record.get("document_integrity"):
        raise PublicationError(
            "published document does not reconstruct the originally accepted model"
        )
    recorded_identity = record.get("identity", {})
    normalized_identity = _identity_from_document(document)
    if (
        recorded_identity.get("component") != normalized_identity.component
        or recorded_identity.get("repository") != normalized_identity.repository
        or tuple(recorded_identity.get("aliases", ()))
        != normalized_identity.aliases
    ):
        raise PublicationError("published document identity differs from acceptance")
    expected_binding = {
        "component": analyzer.get("component"),
        "repository": analyzer.get("repo"),
        "commit_sha": analyzer.get("commit_sha"),
        "extracted_at": analyzer.get("extracted_at"),
        "analyzer_version": analyzer.get("analyzer_version"),
        "schema_version": analyzer.get("schema_version"),
        "bundle_fingerprint": _analyzer_bundle_fingerprint(analyzer),
    }
    if record.get("inputs", {}).get("analyzer_binding") != expected_binding:
        raise PublicationError(
            "published analyzer differs from the parent-recorded accepted input"
        )
    compatibility = record.get("compatibility", {})
    producers = document.get("producers", {})
    if (
        compatibility.get("analyzer_version") != analyzer.get("analyzer_version")
        or compatibility.get("analyzer_schema_version")
        != analyzer.get("schema_version")
        or compatibility.get("normalizer_version")
        != producers.get("normalizer_version")
    ):
        raise PublicationError("published producer compatibility binding is invalid")
    source_end = record.get("source_state", {}).get("end", {})
    if source_end.get("head") != analyzer.get("commit_sha"):
        raise PublicationError("published source revision differs from accepted source")
    revision = analyzer.get("commit_sha")

    def verify_evidence(node: Any) -> None:
        if isinstance(node, Mapping):
            evidence = node.get("evidence")
            if isinstance(evidence, list):
                for reference in evidence:
                    if (
                        isinstance(reference, Mapping)
                        and reference.get("revision") != revision
                    ):
                        raise PublicationError(
                            "published evidence revision differs from accepted source"
                        )
            for value in node.values():
                verify_evidence(value)
        elif isinstance(node, list):
            for value in node:
                verify_evidence(value)

    for collection in (
        document.get("facts", []),
        document.get("sections", []),
        document.get("proposal_dispositions", []),
    ):
        verify_evidence(collection)


def _validate_authority_bytes(
    *,
    component_dir: Path,
    markdown_path: Path,
    analyzer: bytes,
    synthesis: bytes,
    document: bytes,
    assembler: GoStructuredAssembler,
) -> AcceptedPublication:
    analyzer_value = _json(analyzer, "published analyzer")
    synthesis_value = _json(synthesis, "published synthesis")
    document_value = _json(document, "published document")
    try:
        _validate_schema(ENVELOPE_SCHEMA, synthesis_value)
        _validate_schema(DOCUMENT_SCHEMA, document_value)
    except Exception as error:
        raise PublicationError(str(error)) from error
    publication = document_value.get("publication")
    if document_value.get(
        "schema_version"
    ) != PUBLISHED_DOCUMENT_SCHEMA or not isinstance(publication, dict):
        raise PublicationError(
            "document.json is not a complete published 1.1.0 authority"
        )
    identity = document_value.get("identity", {})
    if identity.get("component") != component_dir.name:
        raise PublicationError(
            "document component does not match publication directory"
        )
    if publication.get("markdown", {}).get("path") != markdown_path.name:
        raise PublicationError("document Markdown path does not match flat derivative")
    analyzer_binding = publication.get("analyzer", {})
    synthesis_binding = publication.get("synthesis", {})
    if analyzer_binding.get("content_hash") != content_hash(analyzer):
        raise PublicationError("published analyzer bytes do not match document hash")
    if synthesis_binding.get("content_hash") != content_hash(synthesis):
        raise PublicationError("published synthesis bytes do not match document hash")
    expected_analyzer = {
        "source_component": analyzer_value.get("component"),
        "repository": analyzer_value.get("repo"),
        "source_revision": analyzer_value.get("commit_sha"),
        "analyzer_version": analyzer_value.get("analyzer_version"),
        "schema_version": analyzer_value.get("schema_version"),
        "bundle_fingerprint": _analyzer_bundle_fingerprint(analyzer_value),
    }
    for key, expected in expected_analyzer.items():
        if analyzer_binding.get(key) != expected:
            raise PublicationError(f"published analyzer {key} binding is invalid")
    if synthesis_binding.get("state") != synthesis_value.get(
        "state"
    ) or synthesis_binding.get("input_bundle_identity") != synthesis_value.get(
        "input_bundle_identity"
    ):
        raise PublicationError("published synthesis envelope binding is invalid")
    accepted = synthesis_value.get("accepted_response_identity")
    if synthesis_binding.get("accepted_response_identity") != accepted:
        raise PublicationError("published accepted response identity is invalid")

    accepted_inputs = publication.get("accepted_inputs", {})
    record = accepted_inputs.get("run_record")
    current_bundle = accepted_inputs.get("current_evidence_bundle")
    original_bundle = accepted_inputs.get("original_evidence_bundle")
    if not all(
        isinstance(item, dict) for item in (record, current_bundle, original_bundle)
    ):
        raise PublicationError("published recovery provenance is incomplete")
    if synthesis_value.get("state") == "synthesized":
        try:
            _validate_schema(RUN_RECORD_SCHEMA, record)
            _validate_schema(BUNDLE_SCHEMA, current_bundle)
            _validate_schema(BUNDLE_SCHEMA, original_bundle)
        except Exception as error:
            raise PublicationError(str(error)) from error
        if record["record_identity"] != content_hash(_record_without_identity(record)):
            raise PublicationError("published run record identity is invalid")
        current_identity = _bundle_identity(current_bundle, "current evidence")
        original_identity = _bundle_identity(original_bundle, "original evidence")
        if (
            synthesis_binding.get("current_evidence_bundle_identity")
            != current_identity
            or synthesis_binding.get("original_evidence_bundle_identity")
            != original_identity
            or synthesis_value.get("input_bundle_identity") != original_identity
        ):
            raise PublicationError("published evidence bundle binding is invalid")
        if analyzer_binding.get("producer_build_identity") != record.get(
            "compatibility", {}
        ).get("analyzer_build_identity"):
            raise PublicationError(
                "published analyzer build differs from the accepted producer"
            )
        if not record["dependencies"].get("complete"):
            raise PublicationError(
                "published snapshot lacks complete dependency provenance"
            )
        try:
            _, response_identity = _successful_response(synthesis, original_bundle)
        except ReuseRecordError as error:
            raise PublicationError(
                f"published synthesis producer is ineligible: {error}"
            ) from error
        if (
            response_identity != record["response_identity"]
            or response_identity != accepted
        ):
            raise PublicationError(
                "published response identity does not match acceptance record"
            )
        if synthesis_binding.get("producing_model_eligible") is not True:
            raise PublicationError(
                "published synthesis is not producing-model eligible"
            )
        analyzer_payload = current_bundle.get("analyzer", {}).get("payload")
        if analyzer_payload != analyzer_value:
            raise PublicationError(
                "published analyzer differs from the accepted evidence input"
            )
        _validate_record_document_binding(record, document_value, analyzer_value)
        expected_snapshot = _snapshot_id(
            analyzer_hash=content_hash(analyzer),
            synthesis_hash=content_hash(synthesis),
            record=record,
        )
    else:
        unavailable = {
            "state": "unavailable",
            "reason": synthesis_value["state"],
        }
        if (
            record != unavailable
            or current_bundle != unavailable
            or original_bundle != unavailable
        ):
            raise PublicationError(
                "deterministic-only publication must label audit inputs unavailable"
            )
        if accepted is not None or synthesis_binding.get("producing_model_eligible"):
            raise PublicationError(
                "deterministic-only publication cannot claim a producing model"
            )
        unavailable_identity = content_hash(unavailable)
        if (
            synthesis_binding.get("current_evidence_bundle_identity")
            != unavailable_identity
            or synthesis_binding.get("original_evidence_bundle_identity")
            != unavailable_identity
        ):
            raise PublicationError(
                "deterministic-only unavailable provenance identity is invalid"
            )
        expected_snapshot = _special_snapshot_id(
            analyzer_hash=content_hash(analyzer),
            synthesis_hash=content_hash(synthesis),
            component=identity["component"],
            version_scope=identity["version_scope"],
        )
    if publication.get("snapshot_id") != expected_snapshot:
        raise PublicationError("published snapshot identity is invalid")
    expected_markdown = _render_published(assembler, document)
    return AcceptedPublication(
        component_dir,
        markdown_path,
        analyzer,
        synthesis,
        document,
        expected_markdown,
        document_value,
    )


def load_accepted_publication(
    component_dir: Path,
    assembler: GoStructuredAssembler,
    *,
    repair_markdown: bool = False,
) -> AcceptedPublication:
    component_dir = component_dir.resolve()
    markdown_path = component_dir.parent / f"{component_dir.name}.md"
    try:
        publication = _validate_authority_bytes(
            component_dir=component_dir,
            markdown_path=markdown_path,
            analyzer=(component_dir / "analyzer.json").read_bytes(),
            synthesis=(component_dir / "synthesis.json").read_bytes(),
            document=(component_dir / "document.json").read_bytes(),
            assembler=assembler,
        )
    except OSError as error:
        raise PublicationError(f"accepted snapshot is incomplete: {error}") from error
    try:
        actual_markdown = markdown_path.read_bytes()
    except OSError:
        actual_markdown = b""
    if actual_markdown != publication.markdown:
        if not repair_markdown:
            raise PublicationError(
                "flat Markdown derivative is missing, stale, or tampered"
            )
        _atomic_bytes(markdown_path, publication.markdown)
    return publication


def load_published_reuse_snapshot(
    architecture_dir: Path,
    version_scope: str,
    component: str,
    assembler: GoStructuredAssembler,
) -> AcceptedSnapshot:
    """Rebuild the P3 reuse object using only the published four-file core."""

    publication = load_accepted_publication(
        architecture_dir / version_scope / component,
        assembler,
        repair_markdown=True,
    )
    published = publication.document_value["publication"]
    if published["synthesis"]["state"] != "synthesized":
        raise PublicationError(
            "deterministic-only or missing-response publication is not reusable"
        )
    record = published["accepted_inputs"]["run_record"]
    document = copy.deepcopy(dict(publication.document_value))
    document.pop("publication")
    document["schema_version"] = "1.0.0"
    if content_hash(document) != record["document_integrity"]:
        raise PublicationError(
            "published authority cannot reconstruct the accepted private document"
        )
    identity = ComponentIdentity(**record["identity"])
    compatibility = ProducerCompatibility(**record["compatibility"])
    dependencies = _dependency_from_value(record["dependencies"])
    source_state = SourceRunState(
        _source_snapshot_from_value(record["source_state"]["start"]),
        _source_snapshot_from_value(record["source_state"]["end"]),
    )
    inputs = _input_from_value(record["inputs"])
    return AcceptedSnapshot(
        snapshot_id=record["snapshot_id"],
        platform=record["version_scope"],
        identity=identity,
        accepted=True,
        route=record["route"],
        inputs=inputs,
        compatibility=compatibility,
        dependencies=dependencies,
        source_state=source_state,
        synthesis_bytes=publication.synthesis,
        synthesis_integrity=content_hash(publication.synthesis),
        response_identity=record["response_identity"],
        document=document,
        document_integrity=record["document_integrity"],
    )


def _recover_locked(
    component_dir: Path, assembler: GoStructuredAssembler
) -> AcceptedPublication | None:
    markdown_path = component_dir.parent / f"{component_dir.name}.md"

    def variants(path: Path) -> list[bytes]:
        result = []
        for candidate in (
            path,
            path.with_name(f".{path.name}.next"),
            path.with_name(f".{path.name}.previous"),
        ):
            try:
                value = candidate.read_bytes()
            except OSError:
                continue
            if value not in result:
                result.append(value)
        return result

    documents = variants(component_dir / "document.json")
    analyzers = variants(component_dir / "analyzer.json")
    syntheses = variants(component_dir / "synthesis.json")
    for document in documents:
        for analyzer in analyzers:
            for synthesis in syntheses:
                try:
                    publication = _validate_authority_bytes(
                        component_dir=component_dir,
                        markdown_path=markdown_path,
                        analyzer=analyzer,
                        synthesis=synthesis,
                        document=document,
                        assembler=assembler,
                    )
                except PublicationError:
                    continue
                for path, value in (
                    (component_dir / "analyzer.json", analyzer),
                    (component_dir / "synthesis.json", synthesis),
                    (component_dir / "document.json", document),
                    (markdown_path, publication.markdown),
                ):
                    if not path.is_file() or path.read_bytes() != value:
                        _atomic_bytes(path, value)
                _cleanup_recovery_files(component_dir, markdown_path)
                return publication
    current_or_previous = any(
        path.exists() or path.with_name(f".{path.name}.previous").exists()
        for path in (component_dir / name for name in CORE_NAMES)
    )
    if not current_or_previous:
        # A first publication interrupted before its three authority files were
        # staged has exposed no accepted snapshot.  Discard the incomplete
        # hidden candidate and preserve that prior (empty) state.
        _cleanup_recovery_files(component_dir, markdown_path)
        return None
    if any(analyzers) or any(syntheses) or any(documents):
        raise PublicationError(
            "interrupted publication has no complete recoverable authority"
        )
    return None


def _cleanup_recovery_files(component_dir: Path, markdown_path: Path) -> None:
    for path in (*[component_dir / name for name in CORE_NAMES], markdown_path):
        for temporary in path.parent.glob(f".{path.name}.*"):
            temporary.unlink(missing_ok=True)


def _publication_lock_path(component_dir: Path) -> Path:
    lock_dir = component_dir.parent / ".generation" / "structured-publication-locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    return lock_dir / f"{component_dir.name}.lock"


def recover_publication(
    component_dir: Path, assembler: GoStructuredAssembler
) -> AcceptedPublication | None:
    component_dir.mkdir(parents=True, exist_ok=True)
    lock_path = _publication_lock_path(component_dir)
    with lock_path.open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return _recover_locked(component_dir, assembler)


def accepted_publications(
    platform_dir: Path,
    assembler: GoStructuredAssembler,
    *,
    repair_markdown: bool = False,
) -> dict[str, AcceptedPublication]:
    """Enumerate component directories without treating metadata as components."""

    result: dict[str, AcceptedPublication] = {}
    if not platform_dir.is_dir():
        return result
    for component_dir in sorted(platform_dir.iterdir()):
        if (
            not component_dir.is_dir()
            or component_dir.name.startswith(".")
            or component_dir.name in NON_COMPONENT_DIRECTORIES
        ):
            continue
        core_present = any(
            (component_dir / name).exists()
            or any(
                (component_dir / f".{name}.{suffix}").exists()
                for suffix in RECOVERY_SUFFIXES
            )
            for name in CORE_NAMES
        )
        if not core_present:
            continue
        recovered = recover_publication(component_dir, assembler)
        if recovered is None:
            raise PublicationError(
                f"{component_dir} advertises structured files without an "
                "accepted snapshot"
            )
        result[component_dir.name] = load_accepted_publication(
            component_dir,
            assembler,
            repair_markdown=repair_markdown,
        )
    return result


def validate_accepted_publications(
    platform_dir: Path,
    assembler: GoStructuredAssembler,
) -> dict[str, AcceptedPublication]:
    """Validate visible publications without recovery or derivative repair.

    This read-only boundary is intended for repository linting. Generation and
    consumer paths continue to use ``accepted_publications`` when recovery or
    local derivative repair is appropriate.
    """

    result: dict[str, AcceptedPublication] = {}
    if not platform_dir.is_dir():
        return result
    for component_dir in sorted(platform_dir.iterdir()):
        if (
            not component_dir.is_dir()
            or component_dir.name.startswith(".")
            or component_dir.name in NON_COMPONENT_DIRECTORIES
        ):
            continue
        core_present = any(
            (component_dir / name).exists()
            or any(
                (component_dir / f".{name}.{suffix}").exists()
                for suffix in RECOVERY_SUFFIXES
            )
            for name in CORE_NAMES
        )
        if not core_present:
            continue
        try:
            result[component_dir.name] = load_accepted_publication(
                component_dir,
                assembler,
                repair_markdown=False,
            )
        except PublicationError as error:
            raise PublicationError(f"{component_dir}: {error}") from error
    return result


def _publish_candidate(
    candidate: AcceptedPublication,
    assembler: GoStructuredAssembler,
    *,
    interrupt_after: str | None = None,
    observer: Callable[[str], None] | None = None,
) -> AcceptedPublication:
    component_dir = candidate.component_dir
    markdown_path = candidate.markdown_path
    component_dir.mkdir(parents=True, exist_ok=True)
    lock_path = _publication_lock_path(component_dir)
    with lock_path.open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        _recover_locked(component_dir, assembler)
        files = (
            (component_dir / "analyzer.json", candidate.analyzer),
            (component_dir / "synthesis.json", candidate.synthesis),
            (component_dir / "document.json", candidate.document),
            (markdown_path, candidate.markdown),
        )
        for path, value in files:
            _atomic_bytes(path.with_name(f".{path.name}.next"), value)
            boundary = f"staged:{path.name}"
            if observer:
                observer(boundary)
            if interrupt_after == boundary:
                raise PublicationError(
                    f"simulated interruption while staging {path.name}"
                )
        if observer:
            observer("staged")
        if interrupt_after == "staged":
            raise PublicationError("simulated interruption after staged")
        for path, _value in files:
            if path.is_file():
                _atomic_bytes(
                    path.with_name(f".{path.name}.previous"), path.read_bytes()
                )
            boundary = f"backed-up:{path.name}"
            if observer:
                observer(boundary)
            if interrupt_after == boundary:
                raise PublicationError(
                    f"simulated interruption while backing up {path.name}"
                )
        for path, _value in files:
            _replace(path.with_name(f".{path.name}.next"), path)
            boundary = f"replaced:{path.name}"
            if observer:
                observer(boundary)
            if interrupt_after == boundary:
                raise PublicationError(f"simulated interruption after {path.name}")
        result = load_accepted_publication(component_dir, assembler)
        _cleanup_recovery_files(component_dir, markdown_path)
        return result


def publish_deterministic_snapshot(
    *,
    architecture_dir: Path,
    version_scope: str,
    component: str,
    analyzer: bytes,
    private_document: bytes,
    assembler: GoStructuredAssembler,
    reason: str,
) -> AcceptedPublication:
    """Publish an explicit zero-model snapshot; never accepts a failed envelope."""

    from lib.structured_component_synthesis import special_synthesis_envelope

    analyzer_value = _json(analyzer, "deterministic analyzer")
    document_value = _json(private_document, "deterministic document")
    if document_value.get("schema_version") != "1.0.0":
        raise PublicationError(
            "deterministic publication requires a private 1.0.0 document"
        )
    if (
        document_value.get("identity", {}).get("component") != component
        or document_value.get("identity", {}).get("version_scope") != version_scope
    ):
        raise PublicationError("deterministic document identity does not match target")
    analyzer = _canonical(analyzer_value) + b"\n"
    synthesis_value = special_synthesis_envelope(
        "deterministic-only",
        input_bundle_identity=_analyzer_bundle_fingerprint(analyzer_value),
        reason=reason,
    )
    synthesis = _canonical(synthesis_value) + b"\n"
    unavailable = {"state": "unavailable", "reason": "deterministic-only"}
    unavailable_identity = content_hash(unavailable)
    analyzer_hash = content_hash(analyzer)
    synthesis_hash = content_hash(synthesis)
    document_value["schema_version"] = PUBLISHED_DOCUMENT_SCHEMA
    document_value["publication"] = {
        "contract": PUBLICATION_CONTRACT,
        "snapshot_id": _special_snapshot_id(
            analyzer_hash=analyzer_hash,
            synthesis_hash=synthesis_hash,
            component=component,
            version_scope=version_scope,
        ),
        "analyzer": {
            "content_hash": analyzer_hash,
            "bundle_fingerprint": _analyzer_bundle_fingerprint(analyzer_value),
            "schema_version": analyzer_value["schema_version"],
            "source_component": analyzer_value["component"],
            "repository": analyzer_value.get("repo", ""),
            "source_revision": analyzer_value.get("commit_sha", ""),
            "analyzer_version": analyzer_value.get("analyzer_version", ""),
            "producer_build_identity": content_hash(
                {"state": "unavailable", "reason": "producer-build-not-recorded"}
            ),
        },
        "synthesis": {
            "content_hash": synthesis_hash,
            "state": "deterministic-only",
            "input_bundle_identity": synthesis_value["input_bundle_identity"],
            "current_evidence_bundle_identity": unavailable_identity,
            "original_evidence_bundle_identity": unavailable_identity,
            "producing_model_eligible": False,
        },
        "accepted_inputs": {
            "run_record": unavailable,
            "current_evidence_bundle": unavailable,
            "original_evidence_bundle": unavailable,
        },
        "markdown": {
            "path": f"{component}.md",
            "renderer_version": document_value["producers"]["renderer_version"],
        },
        "diagram": {"state": "unavailable"},
    }
    document = _canonical(document_value) + b"\n"
    component_dir = (architecture_dir / version_scope / component).resolve()
    candidate = _validate_authority_bytes(
        component_dir=component_dir,
        markdown_path=component_dir.parent / f"{component}.md",
        analyzer=analyzer,
        synthesis=synthesis,
        document=document,
        assembler=assembler,
    )
    return _publish_candidate(candidate, assembler)


def publish_private_run(
    *,
    architecture_dir: Path,
    version_scope: str,
    component: str,
    assembler: GoStructuredAssembler,
    interrupt_after: str | None = None,
    observer: Callable[[str], None] | None = None,
) -> AcceptedPublication:
    """Publish one validated private run; ``interrupt_after`` is test-only."""

    store = PrivateRunRecordStore(architecture_dir, assembler)
    store.load(version_scope, component)
    private_dir = store.directory(version_scope, component)
    record = _json((private_dir / "run-record.json").read_bytes(), "private run record")
    current_bundle = _json(
        (private_dir / "evidence-bundle.json").read_bytes(),
        "current evidence bundle",
    )
    original_path = private_dir / record["artifacts"]["synthesis_bundle"]["path"]
    original_bundle = _json(original_path.read_bytes(), "original evidence bundle")
    analyzer_value = current_bundle["analyzer"]["payload"]
    analyzer = _canonical(analyzer_value) + b"\n"
    synthesis = (private_dir / "synthesis.json").read_bytes()
    private_document = _json(
        (private_dir / "document.json").read_bytes(), "private document"
    )
    _, response_identity = _successful_response(synthesis, original_bundle)
    synthesis_value = _json(synthesis, "private synthesis")
    analyzer_hash = content_hash(analyzer)
    synthesis_hash = content_hash(synthesis)
    publication = {
        "contract": PUBLICATION_CONTRACT,
        "snapshot_id": _snapshot_id(
            analyzer_hash=analyzer_hash, synthesis_hash=synthesis_hash, record=record
        ),
        "analyzer": {
            "content_hash": analyzer_hash,
            "bundle_fingerprint": _analyzer_bundle_fingerprint(analyzer_value),
            "schema_version": analyzer_value["schema_version"],
            "source_component": analyzer_value["component"],
            "repository": analyzer_value.get("repo", ""),
            "source_revision": analyzer_value.get("commit_sha", ""),
            "analyzer_version": analyzer_value.get("analyzer_version", ""),
            "producer_build_identity": record["compatibility"][
                "analyzer_build_identity"
            ],
        },
        "synthesis": {
            "content_hash": synthesis_hash,
            "state": synthesis_value["state"],
            "input_bundle_identity": synthesis_value["input_bundle_identity"],
            "current_evidence_bundle_identity": _bundle_identity(
                current_bundle, "current evidence"
            ),
            "original_evidence_bundle_identity": _bundle_identity(
                original_bundle, "original evidence"
            ),
            "accepted_response_identity": response_identity,
            "producing_model_eligible": True,
        },
        "accepted_inputs": {
            "run_record": copy.deepcopy(record),
            "current_evidence_bundle": copy.deepcopy(current_bundle),
            "original_evidence_bundle": copy.deepcopy(original_bundle),
        },
        "markdown": {
            "path": f"{component}.md",
            "renderer_version": private_document["producers"]["renderer_version"],
        },
        "diagram": {"state": "unavailable"},
    }
    document_value = copy.deepcopy(private_document)
    document_value["schema_version"] = PUBLISHED_DOCUMENT_SCHEMA
    document_value["publication"] = publication
    document = _canonical(document_value) + b"\n"
    component_dir = (architecture_dir / version_scope / component).resolve()
    markdown_path = component_dir.parent / f"{component}.md"
    candidate = _validate_authority_bytes(
        component_dir=component_dir,
        markdown_path=markdown_path,
        analyzer=analyzer,
        synthesis=synthesis,
        document=document,
        assembler=assembler,
    )
    return _publish_candidate(
        candidate,
        assembler,
        interrupt_after=interrupt_after,
        observer=observer,
    )
