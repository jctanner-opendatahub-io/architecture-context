"""Conservative whole-component synthesis reuse primitives.

This module is deliberately not wired into pipeline routing or publication.
Phase 3 can call :func:`resolve_or_synthesize` after it supplies the accepted
document revalidation callback for its final synthesis envelope.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Iterable, Mapping, Sequence
from urllib.parse import urlparse

from lib.context_telemetry import parse_bounded_rg_invocation, search_result_identity

SEMANTIC_KEY_VERSION = "structured-component-semantic-input/v2"
DEPENDENCY_RECORD_VERSION = "structured-component-dependencies/v1"
DEPENDENCY_OBSERVATION_VERSION = "structured-component-dependency-observations/v1"
STRUCTURED_ROUTE = "structured-component/v1"
REVALIDATION_CHECKS = frozenset(
    {
        "document_schema",
        "typed_references",
        "patch_policy",
        "current_acceptance_rules",
    }
)
# These analyzer fields are retained in the exact audit identity but are not
# semantic synthesis inputs. Producer/schema compatibility is checked
# separately. Recent changes and scan statistics are not supplied to reusable
# synthesis at all.
_ANALYZER_PRESENTATION_FIELDS = frozenset(
    {
        "analyzer_version",
        "commit_sha",
        "extracted_at",
        "generated_at",
        "schema_version",
    }
)
_ANALYZER_NOT_SYNTHESIZED = frozenset({"recent_changes", "scan_statistics"})
_COMPONENT_PLATFORM_ONLY_FIELDS = frozenset(
    {
        "integration_status",
        "platform_integration",
        "platform_membership",
        "release_label",
        "target_release",
        "version_scope",
    }
)
_LEGACY_SCAN_SUMMARY = re.compile(
    r"^summary:scanned \d+ (?:Python source files for authentication constructions|"
    r"runtime source/config files against \d+ platform aliases)$"
)


class ReuseConfigurationError(ValueError):
    """The explicit predecessor configuration is invalid."""


class ReuseRecordError(ValueError):
    """A prospective snapshot or dependency record is incomplete."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def content_hash(value: bytes | Any) -> str:
    """Return a named SHA-256 over exact bytes or canonical JSON."""

    raw = value if isinstance(value, bytes) else _canonical_bytes(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _analyzer_bundle_fingerprint(value: Mapping[str, Any]) -> str:
    """Match Go's canonical JSON HTML escaping for analyzer bundle identity."""

    canonical = _canonical_bytes(dict(value))
    for character, escape in (
        (b"&", b"\\u0026"),
        (b"<", b"\\u003c"),
        (b">", b"\\u003e"),
        ("\u2028".encode(), b"\\u2028"),
        ("\u2029".encode(), b"\\u2029"),
    ):
        canonical = canonical.replace(character, escape)
    return content_hash(canonical)


def file_hash(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _frozen(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _frozen(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_frozen(item) for item in value)
    return value


def thaw(value: Any) -> Any:
    """Return a detached mutable JSON-shaped copy of frozen snapshot data."""

    if isinstance(value, Mapping):
        return {str(key): thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw(item) for item in value]
    return copy.deepcopy(value)


def canonical_repository_identity(repository: str) -> str:
    """Normalize common Git remote spellings without guessing repository aliases."""

    candidate = repository.strip()
    if candidate.startswith("git@") and ":" in candidate:
        host, path = candidate[4:].split(":", 1)
        candidate = f"ssh://git@{host}/{path}"
    parsed = urlparse(candidate)
    if parsed.scheme and parsed.hostname:
        path = parsed.path
        host = parsed.hostname.casefold()
    else:
        path = candidate
        host = ""
    path = path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    if not path or path in {".", ".."}:
        raise ReuseRecordError("repository identity is empty")
    normalized = path.casefold() if host == "github.com" else path
    return f"{host}/{normalized}" if host else normalized


@dataclass(frozen=True)
class ComponentIdentity:
    component: str
    repository: str
    aliases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        component = self.component.strip()
        if not component:
            raise ReuseRecordError("component identity is empty")
        aliases = tuple(sorted({item.strip() for item in self.aliases if item.strip()}))
        object.__setattr__(self, "component", component)
        object.__setattr__(
            self, "repository", canonical_repository_identity(self.repository)
        )
        object.__setattr__(self, "aliases", aliases)

    @property
    def names(self) -> frozenset[str]:
        return frozenset((self.component, *self.aliases))


@dataclass(frozen=True)
class ProducerCompatibility:
    analyzer_schema_version: str
    analyzer_version: str
    analyzer_build_identity: str
    normalizer_version: str
    synthesis_contract_version: str

    def complete(self) -> bool:
        return all(
            (
                self.analyzer_schema_version,
                self.analyzer_version,
                self.analyzer_build_identity,
                self.normalizer_version,
                self.synthesis_contract_version,
            )
        )


@dataclass(frozen=True)
class SourceSnapshot:
    head: str
    working_tree_identity: str
    tracked_tree_identity: str
    dirty_paths: tuple[str, ...] = ()
    untracked_paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class SourceRunState:
    start: SourceSnapshot
    end: SourceSnapshot

    @property
    def unchanged(self) -> bool:
        return self.start == self.end


@dataclass(frozen=True)
class FileDependency:
    path: str
    content_hash: str
    kind: str = "checkout"


@dataclass(frozen=True)
class ReadObservation:
    path: str
    outcome: str = "observed-by-harness"
    offset: int | None = None
    limit: int | None = None


@dataclass(frozen=True)
class SearchObservation:
    root: str
    resolved_root: str
    pattern: str
    options: tuple[tuple[str, Any], ...]
    tree_identity: str
    tool: str
    justification: str
    outcome: str = "observed-by-harness"
    tracked_clean: bool = True
    replay_result_identity: str = ""
    replay_context_identity: str = ""
    observed_result_identity: str = ""
    execution_cwd: str = "."

    @property
    def reusable_shape(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "pattern": self.pattern,
            "options": {key: thaw(value) for key, value in self.options},
            "tree_identity": self.tree_identity,
            "tool": self.tool,
            "justification": self.justification,
            "outcome": self.outcome,
            "tracked_clean": self.tracked_clean,
            "replay_result_identity": self.replay_result_identity,
            "replay_context_identity": self.replay_context_identity,
            "execution_cwd": self.execution_cwd,
        }


@dataclass(frozen=True)
class DependencyRecord:
    harness: str
    complete: bool
    reads: tuple[ReadObservation, ...]
    supplied_reads: tuple[str, ...]
    justifications: Mapping[str, str]
    files: tuple[FileDependency, ...]
    searches: tuple[SearchObservation, ...]
    unclassified_source_commands: tuple[str, ...] = ()
    accounted_untracked: tuple[str, ...] = ()
    generated_inputs: tuple[FileDependency, ...] = ()
    external_inputs: tuple[FileDependency, ...] = ()
    schema_version: str = DEPENDENCY_RECORD_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "justifications", _frozen(dict(self.justifications)))

    def reusable_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "harness": self.harness,
            "reads": [vars(item) for item in self.reads],
            "supplied_reads": list(self.supplied_reads),
            "justifications": thaw(self.justifications),
            "files": [vars(item) for item in self.files],
            "searches": [item.reusable_shape for item in self.searches],
            "accounted_untracked": list(self.accounted_untracked),
            "generated_inputs": [vars(item) for item in self.generated_inputs],
            "external_inputs": [vars(item) for item in self.external_inputs],
        }


@dataclass(frozen=True)
class InputIdentities:
    exact: str
    semantic: str
    semantic_payload: Mapping[str, Any]
    analyzer_binding: Mapping[str, Any]
    recent_changes: tuple[Any, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "semantic_payload", _frozen(self.semantic_payload))
        object.__setattr__(self, "analyzer_binding", _frozen(self.analyzer_binding))
        object.__setattr__(self, "recent_changes", _frozen(self.recent_changes))


@dataclass(frozen=True)
class TargetNormalization:
    """Frozen current analyzer normalization supplied to the reuse boundary."""

    document: Mapping[str, Any]
    document_integrity: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "document", _frozen(thaw(self.document)))

    @classmethod
    def capture(cls, document: Mapping[str, Any]) -> TargetNormalization:
        detached = thaw(document)
        return cls(detached, content_hash(detached))


@dataclass(frozen=True)
class ReuseTarget:
    platform: str
    identity: ComponentIdentity
    inputs: InputIdentities
    compatibility: ProducerCompatibility
    dependencies: DependencyRecord
    source_state: SourceRunState
    normalization: TargetNormalization | None = None


@dataclass(frozen=True)
class AcceptedSnapshot:
    snapshot_id: str
    platform: str
    identity: ComponentIdentity
    accepted: bool
    route: str
    inputs: InputIdentities
    compatibility: ProducerCompatibility
    dependencies: DependencyRecord
    source_state: SourceRunState
    synthesis_bytes: bytes
    synthesis_integrity: str
    response_identity: str
    document: Mapping[str, Any]
    document_integrity: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "synthesis_bytes", bytes(self.synthesis_bytes))
        object.__setattr__(self, "document", _frozen(thaw(self.document)))


@dataclass(frozen=True)
class ReuseDecision:
    hit: bool
    reasons: tuple[str, ...]
    comparison: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "comparison", _frozen(self.comparison))


@dataclass(frozen=True)
class RevalidationResult:
    document: Mapping[str, Any]
    checks: Mapping[str, bool]
    details: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReuseResolution:
    reused: bool
    output: Any
    decision: ReuseDecision
    synthesis_bytes: bytes | None = None
    response_identity: str | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)


def resolve_predecessor(
    platform: str,
    configurations: Mapping[str, Mapping[str, Any]],
) -> str:
    """Resolve an explicit ``reuse_from`` edge and reject invalid chains."""

    if platform not in configurations:
        raise ReuseConfigurationError(f"unknown target platform {platform!r}")
    predecessor = configurations[platform].get("reuse_from")
    if not isinstance(predecessor, str) or not predecessor.strip():
        raise ReuseConfigurationError(
            f"platform {platform!r} has no explicit reuse_from predecessor"
        )
    predecessor = predecessor.strip()
    if predecessor == platform:
        raise ReuseConfigurationError(f"platform {platform!r} reuses itself")
    if predecessor not in configurations or predecessor.startswith("_"):
        raise ReuseConfigurationError(
            f"platform {platform!r} reuse_from target {predecessor!r} is missing"
        )

    chain = [platform]
    current = predecessor
    while True:
        if current in chain:
            cycle = " -> ".join((*chain[chain.index(current) :], current))
            raise ReuseConfigurationError(f"reuse_from cycle detected: {cycle}")
        chain.append(current)
        raw_next = configurations[current].get("reuse_from")
        if raw_next is None:
            break
        if not isinstance(raw_next, str) or not raw_next.strip():
            raise ReuseConfigurationError(
                f"platform {current!r} has an invalid reuse_from value"
            )
        next_platform = raw_next.strip()
        if next_platform not in configurations or next_platform.startswith("_"):
            raise ReuseConfigurationError(
                f"platform {current!r} reuse_from target {next_platform!r} is missing"
            )
        current = next_platform
    return predecessor


def select_predecessor_snapshot(
    snapshots: Sequence[AcceptedSnapshot],
    predecessor: str,
    target: ComponentIdentity,
) -> AcceptedSnapshot:
    """Select one immutable predecessor snapshot using canonical names/aliases."""

    matches = [
        item
        for item in snapshots
        if item.platform == predecessor and item.identity.names & target.names
    ]
    if not matches:
        raise ReuseRecordError(
            f"predecessor {predecessor!r} has no snapshot for {target.component!r}"
        )
    if len(matches) != 1:
        raise ReuseRecordError(
            f"predecessor aliases are ambiguous for {target.component!r}"
        )
    snapshot = matches[0]
    if snapshot.identity.repository != target.repository:
        raise ReuseRecordError(
            "predecessor component alias resolves to a different repository"
        )
    return snapshot


def _mask_checkout_paths(value: Any, checkout_root: str | Path | None) -> Any:
    if checkout_root is None:
        return value
    root = str(Path(checkout_root).resolve()).rstrip(os.sep)
    prefix = root + os.sep
    if isinstance(value, str):
        if value == root:
            return "<checkout>"
        return value.replace(prefix, "<checkout>/")
    if isinstance(value, list):
        return [_mask_checkout_paths(item, checkout_root) for item in value]
    if isinstance(value, dict):
        return {
            key: _mask_checkout_paths(item, checkout_root)
            for key, item in value.items()
        }
    return value


def _semantic_analyzer(
    analyzer_input: Mapping[str, Any],
    checkout_root: str | Path | None,
) -> dict[str, Any]:
    result = {
        key: copy.deepcopy(value)
        for key, value in analyzer_input.items()
        if key not in _ANALYZER_PRESENTATION_FIELDS | _ANALYZER_NOT_SYNTHESIZED
    }
    # Compatibility with analyzer outputs predating the dedicated top-level
    # scan_statistics field. Only the reviewed, exact scan-summary form is
    # excluded; no other coverage, evidence, gap, or cross-reference text is.
    coverage = result.get("category_coverage")
    if isinstance(coverage, dict):
        for record in coverage.values():
            if not isinstance(record, dict) or not isinstance(
                record.get("evidence"), list
            ):
                continue
            record["evidence"] = [
                item
                for item in record["evidence"]
                if not (isinstance(item, str) and _LEGACY_SCAN_SUMMARY.match(item))
            ]
    return _mask_checkout_paths(result, checkout_root)


def _component_configuration(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: copy.deepcopy(item)
        for key, item in value.items()
        if key not in _COMPONENT_PLATFORM_ONLY_FIELDS
    }


def build_input_identities(
    *,
    analyzer_input: Mapping[str, Any],
    component_configuration: Mapping[str, Any],
    overlays: Sequence[Any],
    contracts: Mapping[str, Any],
    settings: Mapping[str, Any],
    dependencies: DependencyRecord,
    checkout_root: str | Path | None = None,
) -> InputIdentities:
    """Build exact audit and semantic reuse identities for one synthesis input.

    ``recent_changes`` and ``scan_statistics`` remain in the exact audit
    identity but are absent from the semantic synthesis payload because
    reusable synthesis must never consume them. The returned recent changes
    are retained for deterministic target refresh.
    """

    recent = tuple(copy.deepcopy(analyzer_input.get("recent_changes", ())))
    exact_analyzer = copy.deepcopy(dict(analyzer_input))
    semantic_common = {
        "component_configuration": _component_configuration(component_configuration),
        "overlays": copy.deepcopy(list(overlays)),
        "contracts": copy.deepcopy(dict(contracts)),
        "settings": copy.deepcopy(dict(settings)),
        "dependencies": dependencies.reusable_payload(),
    }
    exact_payload = {
        "analyzer": exact_analyzer,
        "component_configuration": copy.deepcopy(dict(component_configuration)),
        "overlays": copy.deepcopy(list(overlays)),
        "contracts": copy.deepcopy(dict(contracts)),
        "settings": copy.deepcopy(dict(settings)),
        "dependencies": dependencies.reusable_payload(),
    }
    semantic_payload = {
        "key_version": SEMANTIC_KEY_VERSION,
        "analyzer": _semantic_analyzer(analyzer_input, checkout_root),
        **semantic_common,
    }
    return InputIdentities(
        exact=content_hash(exact_payload),
        semantic=content_hash(semantic_payload),
        semantic_payload=semantic_payload,
        analyzer_binding={
            "component": copy.deepcopy(analyzer_input.get("component")),
            "repository": copy.deepcopy(analyzer_input.get("repo")),
            "commit_sha": copy.deepcopy(analyzer_input.get("commit_sha")),
            "extracted_at": copy.deepcopy(analyzer_input.get("extracted_at")),
            "analyzer_version": copy.deepcopy(analyzer_input.get("analyzer_version")),
            "schema_version": copy.deepcopy(analyzer_input.get("schema_version")),
            "bundle_fingerprint": _analyzer_bundle_fingerprint(analyzer_input),
        },
        recent_changes=recent,
    )


def _run_git(root: Path, *args: str, allow_failure: bool = False) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0 and not allow_failure:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ReuseRecordError(f"git {' '.join(args)} failed: {detail}")
    return completed.stdout


def _tree_entries(root: Path, *, tracked_only: bool, pathspec: str = ".") -> list[str]:
    args = ["ls-files", "-z"]
    if not tracked_only:
        args.extend(["--cached", "--others", "--exclude-standard"])
    args.extend(["--", pathspec])
    raw = _run_git(root, *args)
    return sorted(
        {
            item.decode("utf-8", errors="surrogateescape")
            for item in raw.split(b"\0")
            if item
        }
    )


def _hash_paths(root: Path, paths: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for relative in sorted(set(paths)):
        path = root / relative
        digest.update(relative.encode("utf-8", errors="surrogateescape"))
        digest.update(b"\0")
        if path.is_symlink():
            digest.update(b"symlink\0" + os.readlink(path).encode("utf-8"))
        elif path.is_file():
            digest.update(b"file\0" + file_hash(path).encode("ascii"))
        else:
            digest.update(b"missing\0")
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def directory_tree_identity(
    root: str | Path,
    relative_root: str = ".",
    *,
    tracked_only: bool = True,
) -> str:
    repository = Path(root).resolve()
    return _hash_paths(
        repository,
        _tree_entries(repository, tracked_only=tracked_only, pathspec=relative_root),
    )


def _porcelain_v1_z_paths(raw: bytes) -> tuple[str, ...]:
    """Return every path from ``git status --porcelain=v1 -z``.

    Rename and copy records carry the destination in the status record and the
    source as the following NUL-delimited field. Both paths are dependencies of
    tracked cleanliness and must be retained.
    """

    fields = raw.split(b"\0")
    paths: list[str] = []
    index = 0
    while index < len(fields):
        record = fields[index]
        index += 1
        if not record:
            continue
        text = record.decode("utf-8", errors="surrogateescape")
        status = text[:2]
        paths.append(text[3:] if len(text) >= 4 else text)
        if "R" not in status and "C" not in status:
            continue
        if index >= len(fields) or not fields[index]:
            raise ReuseRecordError("malformed git porcelain rename/copy record")
        paths.append(fields[index].decode("utf-8", errors="surrogateescape"))
        index += 1
    return tuple(sorted(paths))


def capture_source_snapshot(root: str | Path) -> SourceSnapshot:
    """Capture HEAD plus actual tracked and untracked working-tree content."""

    repository = Path(root).resolve()
    head = _run_git(repository, "rev-parse", "HEAD").decode().strip()
    tracked = _tree_entries(repository, tracked_only=True)
    all_visible = _tree_entries(repository, tracked_only=False)
    untracked = tuple(sorted(set(all_visible) - set(tracked)))
    status = _run_git(repository, "status", "--porcelain=v1", "-z")
    return SourceSnapshot(
        head=head,
        working_tree_identity=_hash_paths(repository, all_visible),
        tracked_tree_identity=_hash_paths(repository, tracked),
        dirty_paths=_porcelain_v1_z_paths(status),
        untracked_paths=untracked,
    )


def capture_producer_build_identity(
    source_root: str | Path,
    *,
    version: str,
) -> str:
    """Identify the exact producer source, including dirty/untracked extractor files."""

    snapshot = capture_source_snapshot(source_root)
    return content_hash(
        {
            "version": version,
            "head": snapshot.head,
            "working_tree_identity": snapshot.working_tree_identity,
            "dirty_paths": list(snapshot.dirty_paths),
            "untracked_paths": list(snapshot.untracked_paths),
        }
    )


def _normalize_relative(path: str, root: Path) -> str:
    candidate = Path(path)
    resolved = (
        candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    )
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError as exc:
        raise ReuseRecordError(f"input path escapes checkout: {path}") from exc


def search_observation_key(
    *, root: str, pattern: str, options: Mapping[str, Any], tool: str
) -> str:
    """Return the stable reconciliation key for one resolved search scope."""

    return content_hash(
        {
            "root": root,
            "pattern": pattern,
            "options": dict(options),
            "tool": tool,
        }
    )


def dependency_record_from_telemetry(
    telemetry: Mapping[str, Any],
    *,
    checkout_root: str | Path,
    justifications: Mapping[str, str],
    search_justifications: Mapping[str, str] | None = None,
    supplied_reads: Sequence[str] = (),
    accounted_untracked: Sequence[str] = (),
    generated_inputs: Sequence[str | Path] = (),
    external_inputs: Sequence[str | Path] = (),
    search_replay_mode: str = "verify-observation",
) -> DependencyRecord:
    """Materialize independently observed dependencies with whole-file hashes."""

    if search_replay_mode not in {"verify-observation", "target-replay"}:
        raise ReuseRecordError(f"unsupported search replay mode: {search_replay_mode}")
    root = Path(checkout_root).resolve()
    observations = telemetry.get("dependency_observations")
    if not isinstance(observations, Mapping):
        raise ReuseRecordError("missing harness dependency observations")
    if observations.get("schema_version") != DEPENDENCY_OBSERVATION_VERSION:
        raise ReuseRecordError("unsupported harness dependency observation version")
    raw_reads = observations.get("reads")
    raw_searches = observations.get("searches")
    raw_unclassified = observations.get("unclassified_source_commands")
    if (
        not isinstance(raw_reads, list)
        or not isinstance(raw_searches, list)
        or not isinstance(raw_unclassified, list)
    ):
        raise ReuseRecordError("incomplete harness dependency observation arrays")

    reads: list[ReadObservation] = []
    paths: set[str] = set()
    for raw in raw_reads:
        if not isinstance(raw, Mapping) or not isinstance(raw.get("path"), str):
            raise ReuseRecordError("malformed read observation")
        relative = _normalize_relative(raw["path"], root)
        paths.add(relative)
        reads.append(
            ReadObservation(
                path=relative,
                outcome=str(raw.get("outcome") or "observed-by-harness"),
                offset=raw.get("offset")
                if isinstance(raw.get("offset"), int)
                else None,
                limit=raw.get("limit") if isinstance(raw.get("limit"), int) else None,
            )
        )
    normalized_supplied = tuple(
        sorted({_normalize_relative(item, root) for item in supplied_reads})
    )
    normalized_untracked = tuple(
        sorted({_normalize_relative(item, root) for item in accounted_untracked})
    )
    paths.update(normalized_supplied)
    normalized_justifications = {
        _normalize_relative(path, root): reason.strip()
        for path, reason in justifications.items()
        if isinstance(reason, str) and reason.strip()
    }
    missing_justifications = sorted(paths - set(normalized_justifications))
    if missing_justifications:
        raise ReuseRecordError(
            "observed/supplied reads lack justifications: "
            + ", ".join(missing_justifications)
        )
    extra_justifications = sorted(set(normalized_justifications) - paths)
    if extra_justifications:
        raise ReuseRecordError(
            "justifications were not independently observed or supplied: "
            + ", ".join(extra_justifications)
        )
    files: list[FileDependency] = []
    for relative in sorted(paths):
        path = root / relative
        if not path.is_file():
            raise ReuseRecordError(f"supporting file is missing: {relative}")
        files.append(FileDependency(relative, file_hash(path)))
    for relative in normalized_untracked:
        if relative in paths:
            continue
        path = root / relative
        if not path.is_file():
            raise ReuseRecordError(f"accounted untracked input is missing: {relative}")
        files.append(FileDependency(relative, file_hash(path), "untracked"))

    searches: list[SearchObservation] = []
    record_complete = bool(observations.get("complete"))
    unclassified = [str(item) for item in raw_unclassified]
    normalized_search_justifications = {
        str(key): reason.strip()
        for key, reason in (search_justifications or {}).items()
        if isinstance(reason, str) and reason.strip()
    }
    used_search_justifications: set[str] = set()
    status_paths = set(capture_source_snapshot(root).dirty_paths)
    for raw in raw_searches:
        if not isinstance(raw, Mapping):
            raise ReuseRecordError("malformed search observation")
        pattern = raw.get("pattern")
        resolved_root = raw.get("resolved_root")
        options = raw.get("options")
        if (
            not isinstance(pattern, str)
            or not pattern
            or not isinstance(resolved_root, str)
            or not resolved_root
            or not isinstance(options, Mapping)
        ):
            raise ReuseRecordError(
                "search requires pattern, resolved_root, and options"
            )
        relative_root = _normalize_relative(resolved_root, root)
        tool = str(raw.get("tool") or "unknown")
        justification_key = search_observation_key(
            root=relative_root,
            pattern=pattern,
            options=options,
            tool=tool,
        )
        justification = normalized_search_justifications.get(justification_key)
        if not justification:
            raise ReuseRecordError(
                "observed search lacks justification: " + justification_key
            )
        used_search_justifications.add(justification_key)
        prefix = "" if relative_root == "." else relative_root.rstrip("/") + "/"
        tracked_clean = not any(
            path == relative_root or path.startswith(prefix) for path in status_paths
        )
        replay = (
            _replay_rg_search(
                root,
                raw,
                options,
                mode=search_replay_mode,
            )
            if tool == "rg"
            else None
        )
        if replay is None:
            record_complete = False
            unclassified.append(
                f"{tool}-search-verification-unavailable:{relative_root}"
            )
        replay_result, replay_context, replay_outcome, execution_cwd = (
            replay
            if replay is not None
            else ("", "", str(raw.get("outcome") or ""), ".")
        )
        searches.append(
            SearchObservation(
                root=relative_root,
                resolved_root=str((root / relative_root).resolve()),
                pattern=pattern,
                options=tuple(
                    sorted((str(key), _frozen(value)) for key, value in options.items())
                ),
                tree_identity=directory_tree_identity(
                    root, relative_root, tracked_only=True
                ),
                tool=tool,
                justification=justification,
                outcome=replay_outcome
                or str(raw.get("outcome") or "observed-by-harness"),
                tracked_clean=tracked_clean,
                replay_result_identity=replay_result,
                replay_context_identity=replay_context,
                observed_result_identity=str(raw.get("observed_result_identity") or ""),
                execution_cwd=execution_cwd,
            )
        )
    unused_search_justifications = (
        set(normalized_search_justifications) - used_search_justifications
    )
    if unused_search_justifications:
        raise ReuseRecordError(
            "search justifications were not independently observed: "
            + ", ".join(sorted(unused_search_justifications))
        )

    def outside_dependencies(
        items: Sequence[str | Path], kind: str
    ) -> tuple[FileDependency, ...]:
        result = []
        for item in items:
            path = Path(item).resolve()
            if not path.is_file():
                raise ReuseRecordError(f"{kind} input is missing: {path}")
            try:
                identity = path.relative_to(root).as_posix()
            except ValueError:
                identity = str(path)
            result.append(FileDependency(identity, file_hash(path), kind))
        return tuple(result)

    return DependencyRecord(
        harness=str(
            observations.get("harness") or telemetry.get("harness") or "unknown"
        ),
        complete=record_complete,
        reads=tuple(reads),
        supplied_reads=normalized_supplied,
        justifications=normalized_justifications,
        files=tuple(files),
        searches=tuple(searches),
        unclassified_source_commands=tuple(dict.fromkeys(unclassified)),
        accounted_untracked=normalized_untracked,
        generated_inputs=outside_dependencies(generated_inputs, "generated"),
        external_inputs=outside_dependencies(external_inputs, "external"),
    )


def _replay_rg_search(
    root: Path,
    raw: Mapping[str, Any],
    options: Mapping[str, Any],
    *,
    mode: str,
) -> tuple[str, str, str, str] | None:
    """Replay one bounded rg observation under an explicit local context."""

    argv = options.get("argv")
    execution_cwd = raw.get("execution_cwd")
    observed_result = raw.get("observed_result_identity")
    if (
        not isinstance(argv, (list, tuple))
        or not argv
        or not all(isinstance(item, str) for item in argv)
        or not isinstance(execution_cwd, str)
        or not execution_cwd
        or not isinstance(observed_result, str)
        or not observed_result.startswith("sha256:")
    ):
        return None
    parsed = parse_bounded_rg_invocation(
        ["rg", *argv],
        execution_cwd=execution_cwd,
        checkout_root=root,
    )
    if parsed is None:
        return None
    recorded_options = {str(key): thaw(value) for key, value in options.items()}
    try:
        recorded_relative_cwd = _normalize_relative(execution_cwd, root)
        recorded_root = str(
            (
                root / _normalize_relative(str(raw.get("resolved_root") or ""), root)
            ).resolve()
        )
    except ReuseRecordError:
        return None
    if (
        parsed["pattern"] != raw.get("pattern")
        or parsed["options"] != recorded_options
        or parsed["relative_cwd"] != recorded_relative_cwd
        or recorded_root not in parsed["resolved_roots"]
    ):
        return None
    cwd = Path(parsed["execution_cwd"])
    relative_cwd = str(parsed["relative_cwd"])

    executable = shutil.which("rg")
    if executable is None:
        return None
    executable_path = Path(executable).resolve()
    try:
        executable_hash = file_hash(executable_path)
    except OSError:
        return None
    version = subprocess.run(
        [str(executable_path), "--version"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if version.returncode != 0 or version.stderr:
        return None

    replay_env = os.environ.copy()
    replay_env.pop("RIPGREP_CONFIG_PATH", None)
    replay_env.pop("RG_CONFIG_PATH", None)
    replay_env.update({"LC_ALL": "C", "NO_COLOR": "1"})
    completed = subprocess.run(
        [str(executable_path), *argv],
        cwd=cwd,
        env=replay_env,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode not in {0, 1} or completed.stderr:
        return None
    replay_result = search_result_identity(completed.returncode, completed.stdout)
    if mode == "verify-observation" and observed_result != replay_result:
        return None
    replay_context = content_hash(
        {
            "kind": "direct-rg-replay/v1",
            "executable_hash": executable_hash,
            "version_output": version.stdout.decode("utf-8", errors="replace"),
            "cwd": relative_cwd,
            "environment": {
                "LC_ALL": "C",
                "NO_COLOR": "1",
                "RG_CONFIG_PATH": "unset",
                "RIPGREP_CONFIG_PATH": "unset",
            },
        }
    )
    outcome = (
        "successful-command-execution"
        if completed.returncode == 0
        else "successful-no-match-search"
    )
    return replay_result, replay_context, outcome, relative_cwd


def _dependency_errors(record: DependencyRecord, state: SourceRunState) -> list[str]:
    errors: list[str] = []
    if record.schema_version != DEPENDENCY_RECORD_VERSION:
        errors.append("dependency_record_version_mismatch")
    if not record.complete:
        errors.append("dependency_record_incomplete")
    if record.unclassified_source_commands:
        errors.append("unclassified_source_command")
    if not state.unchanged:
        errors.append("source_mutated_during_run")
    unaccounted = set(state.end.untracked_paths) - set(record.accounted_untracked)
    if unaccounted:
        errors.append("unaccounted_untracked_inputs")
    paths = {item.path for item in record.files}
    required = {item.path for item in record.reads} | set(record.supplied_reads)
    if required - paths:
        errors.append("supporting_file_hash_missing")
    if set(record.accounted_untracked) - paths:
        errors.append("untracked_input_hash_missing")
    if required - set(record.justifications):
        errors.append("read_justification_missing")
    if any(not item.tracked_clean for item in record.searches):
        errors.append("searched_tree_not_clean")
    return errors


def _input_record_errors(
    inputs: InputIdentities,
    dependencies: DependencyRecord,
    prefix: str,
) -> list[str]:
    payload = thaw(inputs.semantic_payload)
    errors: list[str] = []
    if payload.get("key_version") != SEMANTIC_KEY_VERSION:
        errors.append(f"{prefix}_semantic_key_version_mismatch")
    if content_hash(payload) != inputs.semantic:
        errors.append(f"{prefix}_semantic_identity_integrity_mismatch")
    if payload.get("dependencies") != dependencies.reusable_payload():
        errors.append(f"{prefix}_dependency_record_mismatch")
    return errors


def _producing_envelope_errors(
    synthesis_bytes: bytes, inputs: InputIdentities
) -> list[str]:
    """Validate the reuse-critical producer identity retained in an envelope."""

    try:
        envelope = json.loads(synthesis_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        return ["producing_envelope_malformed"]
    if not isinstance(envelope, dict):
        return ["producing_envelope_malformed"]
    errors: list[str] = []
    eligibility = envelope.get("reuse_eligibility")
    if not isinstance(eligibility, dict) or eligibility.get("available") is not True:
        errors.append("producing_envelope_ineligible")
    requested = envelope.get("requested")
    accepted_identity = envelope.get("accepted_response_identity")
    responses = envelope.get("responses")
    if not isinstance(requested, dict) or not isinstance(responses, list):
        return [*errors, "producing_envelope_identity_missing"]
    semantic_settings = thaw(inputs.semantic_payload).get("settings", {})
    model_context = (
        semantic_settings.get("model_context", {})
        if isinstance(semantic_settings, dict)
        else {}
    )
    if (
        requested.get("harness") != model_context.get("adapter")
        or requested.get("model") != model_context.get("requested_model")
        or requested.get("settings") != model_context.get("requested_settings")
    ):
        errors.append("producing_request_binding_mismatch")
    accepted_indexes = [
        index
        for index, item in enumerate(responses)
        if isinstance(item, dict) and item.get("response_identity") == accepted_identity
    ]
    if len(accepted_indexes) != 1:
        return [*errors, "producing_envelope_identity_missing"]
    accepted_index = accepted_indexes[0]
    response = responses[accepted_index]
    if (
        not isinstance(response.get("requested_model_identity"), str)
        or not response["requested_model_identity"]
        or response.get("reported_model") != response["requested_model_identity"]
    ):
        errors.append("producing_model_mismatch")
    if response.get("reported_settings") != requested.get("settings"):
        errors.append("producing_settings_mismatch")
    reported = envelope.get("reported")
    models = reported.get("models") if isinstance(reported, dict) else None
    settings = reported.get("settings") if isinstance(reported, dict) else None
    auxiliary = reported.get("auxiliary_models") if isinstance(reported, dict) else None
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
        errors.append("producing_model_audit_mismatch")
    return errors


def _target_normalization_content_errors(
    prior: AcceptedSnapshot,
    target: ReuseTarget,
    binding_errors: Sequence[str],
) -> list[str]:
    if binding_errors or target.normalization is None:
        return []
    try:
        prior_invariant = _reuse_invariant_document(thaw(prior.document))
        target_invariant = _reuse_invariant_document(
            thaw(target.normalization.document)
        )
    except (KeyError, TypeError, ValueError):
        return ["target_normalization_content_malformed"]
    if prior_invariant != target_invariant:
        return ["target_normalization_content_mismatch"]
    return []


def decide_reuse(
    prior: AcceptedSnapshot,
    target: ReuseTarget,
    *,
    force_refresh: bool = False,
) -> ReuseDecision:
    """Return an explicit, auditable hit/miss without invoking synthesis."""

    reasons: list[str] = []
    if force_refresh:
        reasons.append("explicit_refresh")
    if not prior.accepted:
        reasons.append("predecessor_not_accepted")
    if prior.route != STRUCTURED_ROUTE:
        reasons.append("legacy_or_incompatible_snapshot")
    if prior.platform == target.platform:
        reasons.append("predecessor_is_target")
    if prior.identity.repository != target.identity.repository:
        reasons.append("repository_mismatch")
    if not prior.identity.names & target.identity.names:
        reasons.append("component_identity_mismatch")
    if not prior.compatibility.complete() or not target.compatibility.complete():
        reasons.append("producer_compatibility_incomplete")
    elif prior.compatibility != target.compatibility:
        reasons.append("producer_or_contract_mismatch")
    reasons.extend(_dependency_errors(prior.dependencies, prior.source_state))
    reasons.extend(_dependency_errors(target.dependencies, target.source_state))
    reasons.extend(_input_record_errors(prior.inputs, prior.dependencies, "prior"))
    reasons.extend(_input_record_errors(target.inputs, target.dependencies, "target"))
    target_normalization_errors = _target_normalization_binding_errors(target)
    reasons.extend(target_normalization_errors)
    target_content_errors = _target_normalization_content_errors(
        prior, target, target_normalization_errors
    )
    reasons.extend(target_content_errors)
    if prior.inputs.semantic != target.inputs.semantic:
        reasons.append("semantic_input_mismatch")
    reasons.extend(_producing_envelope_errors(prior.synthesis_bytes, prior.inputs))
    if content_hash(prior.synthesis_bytes) != prior.synthesis_integrity:
        reasons.append("synthesis_integrity_mismatch")
    if content_hash(thaw(prior.document)) != prior.document_integrity:
        reasons.append("document_integrity_mismatch")

    comparison = {
        "prior_snapshot_id": prior.snapshot_id,
        "prior_platform": prior.platform,
        "target_platform": target.platform,
        "prior_component": prior.identity.component,
        "target_component": target.identity.component,
        "prior_repository": prior.identity.repository,
        "target_repository": target.identity.repository,
        "prior_exact_input": prior.inputs.exact,
        "target_exact_input": target.inputs.exact,
        "prior_semantic_input": prior.inputs.semantic,
        "target_semantic_input": target.inputs.semantic,
        "prior_source_head": prior.source_state.end.head,
        "target_source_head": target.source_state.end.head,
        "prior_worktree": prior.source_state.end.working_tree_identity,
        "target_worktree": target.source_state.end.working_tree_identity,
        "synthesis_integrity": prior.synthesis_integrity,
        "response_identity": prior.response_identity,
        "target_normalization_errors": target_normalization_errors,
        "target_normalization_content_errors": target_content_errors,
        "target_normalization_integrity": (
            target.normalization.document_integrity
            if target.normalization is not None
            else None
        ),
    }
    return ReuseDecision(not reasons, tuple(dict.fromkeys(reasons)), comparison)


def resolve_or_synthesize(
    prior: AcceptedSnapshot,
    target: ReuseTarget,
    *,
    revalidate: Callable[[AcceptedSnapshot, ReuseTarget], RevalidationResult],
    synthesize: Callable[[ReuseTarget], Any],
    force_refresh: bool = False,
) -> ReuseResolution:
    """Reuse with zero synthesis calls, or take one bounded normal miss path."""

    decision = decide_reuse(prior, target, force_refresh=force_refresh)
    if decision.hit:
        try:
            validation = revalidate(prior, target)
        except Exception as exc:  # current validation failure is a cache miss
            decision = ReuseDecision(
                False,
                ("current_revalidation_failed",),
                {**thaw(decision.comparison), "revalidation_error": str(exc)},
            )
        else:
            checks = {str(key): bool(value) for key, value in validation.checks.items()}
            refreshed_recent = (
                _accepted_recent_changes(validation.document)
                if isinstance(validation.document, Mapping)
                else None
            )
            checks["recent_changes_refresh"] = (
                refreshed_recent is not None
                and refreshed_recent == thaw(target.inputs.recent_changes)
            )
            consistency_errors, expected_hash, returned_hash = (
                _revalidated_document_consistency(
                    prior,
                    target,
                    validation.document,
                )
            )
            checks["predecessor_target_consistency"] = not consistency_errors
            missing = sorted(REVALIDATION_CHECKS - set(checks))
            failed = sorted(
                key
                for key in (
                    *REVALIDATION_CHECKS,
                    "recent_changes_refresh",
                    "predecessor_target_consistency",
                )
                if not checks.get(key)
            )
            if missing or failed:
                reasons = []
                if missing or any(
                    key != "predecessor_target_consistency" for key in failed
                ):
                    reasons.append("current_revalidation_failed")
                if consistency_errors:
                    reasons.append("revalidated_document_inconsistent")
                decision = ReuseDecision(
                    False,
                    tuple(reasons),
                    {
                        **thaw(decision.comparison),
                        "missing_revalidation_checks": missing,
                        "failed_revalidation_checks": failed,
                        "revalidation_details": list(validation.details),
                        "document_consistency_errors": list(consistency_errors),
                        "expected_target_document_integrity": expected_hash,
                        "returned_document_integrity": returned_hash,
                    },
                )
            else:
                provenance = {
                    **thaw(decision.comparison),
                    "decision": "reuse",
                    "reason": "verified_semantic_and_dependency_match",
                    "recent_changes_refreshed": True,
                    "revalidation_checks": checks,
                    "predecessor_document_integrity": prior.document_integrity,
                    "target_document_integrity": returned_hash,
                }
                return ReuseResolution(
                    reused=True,
                    output=thaw(validation.document),
                    decision=decision,
                    synthesis_bytes=prior.synthesis_bytes,
                    response_identity=prior.response_identity,
                    provenance=_frozen(provenance),
                )

    output = synthesize(target)
    return ReuseResolution(
        reused=False,
        output=output,
        decision=decision,
        provenance=_frozen(
            {
                **thaw(decision.comparison),
                "decision": "miss",
                "reasons": list(decision.reasons),
            }
        ),
    )


def _accepted_recent_changes(document: Mapping[str, Any]) -> list[Any] | None:
    facts = document.get("facts")
    if not isinstance(facts, (list, tuple)):
        return None
    recent: list[tuple[int, Any]] = []
    for fact in facts:
        if not isinstance(fact, Mapping) or fact.get("type") != "recent_change":
            continue
        ordinal = fact.get("ordinal")
        if not isinstance(ordinal, int) or "value" not in fact:
            return None
        recent.append((ordinal, thaw(fact["value"])))
    recent.sort(key=lambda item: item[0])
    if [ordinal for ordinal, _ in recent] != list(range(len(recent))):
        return None
    return [value for _, value in recent]


def _predecessor_document_binding_errors(
    prior: AcceptedSnapshot,
) -> list[str]:
    document = thaw(prior.document)
    identity = document.get("identity")
    producers = document.get("producers")
    analyzer_input = document.get("analyzer_input")
    analyzer_binding = thaw(prior.inputs.analyzer_binding)
    errors: list[str] = []
    if not isinstance(identity, dict):
        return ["predecessor document identity is missing"]
    if identity.get("component") != prior.identity.component:
        errors.append("predecessor document component is not snapshot-bound")
    source_component = identity.get("source_component")
    if (
        not isinstance(source_component, str)
        or source_component not in prior.identity.names
    ):
        errors.append("predecessor source component is not snapshot-bound")
    try:
        document_repository = canonical_repository_identity(
            str(identity.get("repository") or "")
        )
    except ReuseRecordError:
        document_repository = ""
    if document_repository != prior.identity.repository:
        errors.append("predecessor document repository is not snapshot-bound")
    aliases = identity.get("aliases")
    if not isinstance(aliases, (list, tuple)) or not all(
        isinstance(alias, str) for alias in aliases
    ):
        errors.append("predecessor document aliases are malformed")
    elif tuple(sorted(aliases)) != prior.identity.aliases:
        errors.append("predecessor document aliases are not snapshot-bound")
    if identity.get("version_scope") != prior.platform:
        errors.append("predecessor document version scope is not snapshot-bound")
    if identity.get("source_revision") != prior.source_state.end.head:
        errors.append("predecessor document source revision is not snapshot-bound")
    if identity.get("source_revision") != analyzer_binding.get("commit_sha"):
        errors.append("predecessor source revision is not analyzer-input-bound")
    if not isinstance(producers, dict):
        errors.append("predecessor document producers are missing")
    else:
        if producers.get(
            "analyzer_version"
        ) != prior.compatibility.analyzer_version or producers.get(
            "analyzer_version"
        ) != analyzer_binding.get("analyzer_version"):
            errors.append("predecessor analyzer version is not snapshot-bound")
        if (
            producers.get("normalizer_version")
            != prior.compatibility.normalizer_version
        ):
            errors.append("predecessor normalizer version is not snapshot-bound")
    if not isinstance(analyzer_input, dict):
        errors.append("predecessor analyzer input is missing")
    elif analyzer_input.get(
        "schema_version"
    ) != prior.compatibility.analyzer_schema_version or analyzer_input.get(
        "schema_version"
    ) != analyzer_binding.get("schema_version"):
        errors.append("predecessor analyzer schema is not snapshot-bound")
    else:
        if analyzer_input.get("bundle_fingerprint") != analyzer_binding.get(
            "bundle_fingerprint"
        ):
            errors.append("predecessor analyzer fingerprint is not input-bound")
        if analyzer_input.get("extracted_at") != analyzer_binding.get("extracted_at"):
            errors.append("predecessor extraction metadata is not input-bound")
    predecessor_revision = prior.source_state.end.head
    for collection in (
        document.get("facts", ()),
        document.get("proposal_dispositions", ()),
    ):
        if not isinstance(collection, list):
            continue
        for item in collection:
            if not isinstance(item, dict):
                continue
            evidence = item.get("evidence", ())
            if isinstance(evidence, list) and any(
                isinstance(reference, dict)
                and reference.get("revision") != predecessor_revision
                for reference in evidence
            ):
                errors.append("predecessor evidence revision is not snapshot-bound")
                return errors
    return errors


def _target_normalization_binding_errors(target: ReuseTarget) -> list[str]:
    """Bind the prospective hit to the actual current normalized analyzer model."""

    normalization = target.normalization
    if normalization is None:
        return ["target_normalization_missing"]
    document = thaw(normalization.document)
    if not isinstance(document, dict):
        return ["target_normalization_document_malformed"]
    try:
        actual_integrity = content_hash(document)
    except (TypeError, ValueError):
        return ["target_normalization_document_malformed"]
    if actual_integrity != normalization.document_integrity:
        return ["target_normalization_integrity_mismatch"]
    identity = document.get("identity")
    producers = document.get("producers")
    analyzer_input = document.get("analyzer_input")
    rendering_view = document.get("rendering_view")
    binding = thaw(target.inputs.analyzer_binding)
    errors: list[str] = []
    if not isinstance(identity, dict):
        errors.append("target_normalization_identity_missing")
    else:
        if identity.get("component") != target.identity.component:
            errors.append("target_normalization_component_mismatch")
        if identity.get("source_component") != binding.get("component"):
            errors.append("target_normalization_source_component_mismatch")
        try:
            repository = canonical_repository_identity(
                str(identity.get("repository") or "")
            )
            analyzer_repository = canonical_repository_identity(
                str(binding.get("repository") or "")
            )
        except ReuseRecordError:
            repository = analyzer_repository = ""
        if (
            repository != target.identity.repository
            or analyzer_repository != target.identity.repository
        ):
            errors.append("target_normalization_repository_mismatch")
        aliases = identity.get("aliases")
        if (
            not isinstance(aliases, list)
            or not all(isinstance(alias, str) for alias in aliases)
            or tuple(sorted(aliases)) != target.identity.aliases
        ):
            errors.append("target_normalization_aliases_mismatch")
        if identity.get("version_scope") != target.platform:
            errors.append("target_normalization_version_scope_mismatch")
        revision = identity.get("source_revision")
        if (
            revision != binding.get("commit_sha")
            or revision != target.source_state.end.head
        ):
            errors.append("target_normalization_source_revision_mismatch")
    if not isinstance(producers, dict):
        errors.append("target_normalization_producers_missing")
    else:
        if producers.get(
            "analyzer_version"
        ) != target.compatibility.analyzer_version or producers.get(
            "analyzer_version"
        ) != binding.get("analyzer_version"):
            errors.append("target_normalization_analyzer_version_mismatch")
        if (
            producers.get("normalizer_version")
            != target.compatibility.normalizer_version
        ):
            errors.append("target_normalization_normalizer_version_mismatch")
    if not isinstance(analyzer_input, dict):
        errors.append("target_normalization_analyzer_input_missing")
    else:
        if analyzer_input.get(
            "schema_version"
        ) != target.compatibility.analyzer_schema_version or analyzer_input.get(
            "schema_version"
        ) != binding.get("schema_version"):
            errors.append("target_normalization_analyzer_schema_mismatch")
        if analyzer_input.get("bundle_fingerprint") != binding.get(
            "bundle_fingerprint"
        ):
            errors.append("target_normalization_analyzer_fingerprint_mismatch")
        if analyzer_input.get("extracted_at") != binding.get("extracted_at"):
            errors.append("target_normalization_extraction_metadata_mismatch")
    metadata = (
        rendering_view.get("metadata") if isinstance(rendering_view, dict) else None
    )
    if not isinstance(metadata, dict) or metadata.get("version") != binding.get(
        "commit_sha"
    ):
        errors.append("target_normalization_rendered_revision_mismatch")
    if _accepted_recent_changes(document) != thaw(target.inputs.recent_changes):
        errors.append("target_normalization_recent_changes_mismatch")
    target_revision = target.source_state.end.head
    for collection in (
        document.get("facts", ()),
        document.get("proposal_dispositions", ()),
    ):
        if not isinstance(collection, list):
            continue
        for item in collection:
            if not isinstance(item, dict):
                continue
            evidence = item.get("evidence", ())
            if isinstance(evidence, list) and any(
                isinstance(reference, dict)
                and reference.get("revision") != target_revision
                for reference in evidence
            ):
                errors.append("target_normalization_evidence_revision_mismatch")
                return errors
    return errors


def _expected_target_document(
    prior: AcceptedSnapshot,
    target: ReuseTarget,
) -> dict[str, Any]:
    """Return the exact target normalization that current validation must accept."""

    del prior
    if target.normalization is None:
        raise ReuseRecordError("target normalization is missing")
    return thaw(target.normalization.document)


def _without_evidence_revisions(items: Any) -> None:
    if not isinstance(items, list):
        return
    for item in items:
        if not isinstance(item, dict):
            continue
        evidence = item.get("evidence")
        if not isinstance(evidence, list):
            continue
        for reference in evidence:
            if isinstance(reference, dict):
                reference.pop("revision", None)


def _reuse_invariant_document(document: Mapping[str, Any]) -> dict[str, Any]:
    """Remove only reviewed target-refresh fields from a normalized document."""

    result = thaw(document)
    # A prior target may itself be a verified reuse result. Its trusted reuse
    # audit record describes that earlier decision, not synthesized component
    # content, and must not prevent an explicitly selected later reuse hop.
    result.pop("reuse", None)
    # Publication binds exact artifact bytes and recovery provenance, not
    # synthesized component semantics. A target publication receives fresh
    # bindings after current-input revalidation.
    result.pop("publication", None)
    if result.get("schema_version") == "1.1.0":
        result["schema_version"] = "1.0.0"
    identity = result.get("identity")
    if isinstance(identity, dict):
        identity.pop("component", None)
        identity.pop("aliases", None)
        identity.pop("version_scope", None)
        identity.pop("source_revision", None)
        identity.pop("integration_status", None)
    analyzer_input = result.get("analyzer_input")
    if isinstance(analyzer_input, dict):
        analyzer_input.pop("bundle_fingerprint", None)
        analyzer_input.pop("extracted_at", None)
    # The exact current map remains bound in TargetNormalization and relevant
    # component fields remain in InputIdentities. This retained audit copy also
    # contains platform/version-only values and a target-scoped origin ID, so it
    # is refreshed rather than treated as reusable synthesized content.
    result.pop("assembly_inputs", None)

    facts = result.get("facts")
    recent_ids: set[str] = set()
    if isinstance(facts, list):
        recent_ids = {
            str(fact.get("id"))
            for fact in facts
            if isinstance(fact, dict) and fact.get("type") == "recent_change"
        }
        result["facts"] = [
            fact
            for fact in facts
            if not isinstance(fact, dict) or fact.get("type") != "recent_change"
        ]
        _without_evidence_revisions(result["facts"])
    accounting = result.get("fact_accounting")
    if isinstance(accounting, list):
        result["fact_accounting"] = [
            item
            for item in accounting
            if not isinstance(item, dict) or item.get("fact_id") not in recent_ids
        ]
    _without_evidence_revisions(result.get("proposal_dispositions"))
    for item in result.get("patch_inputs", ()):
        if isinstance(item, dict):
            item.pop("bundle_fingerprint", None)
            item.pop("proposal_fingerprint", None)
    for item in result.get("proposal_dispositions", ()):
        if isinstance(item, dict):
            item.pop("bundle_fingerprint", None)
            item.pop("proposal_fingerprint", None)
    rendering_view = result.get("rendering_view")
    if isinstance(rendering_view, dict):
        rendering_view.pop("component", None)
        metadata = rendering_view.get("metadata")
        if isinstance(metadata, dict):
            metadata.pop("version", None)
        rendering_view.pop("recent_changes", None)
    uncertainty = result.get("uncertainty")
    if isinstance(uncertainty, list):
        for item in uncertainty:
            if isinstance(item, dict) and item.get("scope") == "component-integration":
                item.pop("status", None)
    return result


def _revalidated_document_consistency(
    prior: AcceptedSnapshot,
    target: ReuseTarget,
    returned: Mapping[str, Any],
) -> tuple[tuple[str, ...], str | None, str | None]:
    errors = _predecessor_document_binding_errors(prior)
    errors.extend(_target_normalization_binding_errors(target))
    if not isinstance(returned, Mapping):
        return (*errors, "revalidation returned a non-document value"), None, None
    try:
        expected = _expected_target_document(prior, target)
        actual = thaw(returned)
        expected_hash = content_hash(expected)
        returned_hash = content_hash(actual)
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(f"document consistency could not be evaluated: {exc}")
        return tuple(errors), None, None
    if actual != expected:
        changed = sorted(
            key
            for key in set(expected) | set(actual)
            if expected.get(key) != actual.get(key)
        )
        errors.append(
            "returned document differs from bound target normalization"
            + (f" ({', '.join(changed)})" if changed else "")
        )
    try:
        prior_invariant = _reuse_invariant_document(thaw(prior.document))
        target_invariant = _reuse_invariant_document(expected)
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(f"reuse invariant could not be evaluated: {exc}")
    else:
        if prior_invariant != target_invariant:
            changed = sorted(
                key
                for key in set(prior_invariant) | set(target_invariant)
                if prior_invariant.get(key) != target_invariant.get(key)
            )
            errors.append(
                "target normalization differs outside reviewed reuse refresh"
                + (f" ({', '.join(changed)})" if changed else "")
            )
    return tuple(errors), expected_hash, returned_hash


def render_resolution(
    resolution: ReuseResolution,
    renderer: Callable[[Any], Any],
) -> Any:
    """Render an accepted result; renderer identity never enters reuse keys."""

    return renderer(resolution.output)
