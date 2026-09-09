"""Fresh committed-tree extractor replay for the P5 reuse evidence packet.

The driver materializes committed Git trees without checkout filters or hooks,
runs the recorded analyzer once per source, and retains raw and normalized
comparison evidence.  It deliberately does not construct a reusable snapshot:
legacy analyzer-fact similarity is only one input to the SC-13 contract.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import tarfile
import tempfile
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from lib.structured_component_reuse import _semantic_analyzer

LEGACY_VOLATILE_FIELDS = frozenset(
    {"analyzer_version", "commit_sha", "extracted_at", "generated_at", "schema_version"}
)
LEGACY_NOISE_FIELDS = frozenset(
    {
        "coverage_findings",
        "cross_references",
        "data_coverage",
        "gap_evidence_index",
        "recent_changes",
        "summary",
        "synthesis_evidence",
    }
)
LEGACY_CHECKOUT_PATH = re.compile(r'(?:/home/[^"\s]*?)?checkouts/[^/"\s]+/')
REVIEWED_SCAN_SUMMARY = re.compile(
    r"^summary:scanned \d+ (?:Python source files for authentication constructions|"
    r"runtime source/config files against \d+ platform aliases)$"
)
EXPECTED_COMPARISON_SHA256 = (
    "2df2ca5dcc1853c624726474dea9278b4f7d50c8f8f2374d6585a0c55c9100dd"
)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical_bytes(value))


def _git_bytes(repository: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    environment = os.environ.copy()
    environment["GIT_NO_LAZY_FETCH"] = "1"
    return subprocess.run(
        ("git", "-C", str(repository), *arguments),
        capture_output=True,
        check=False,
        env=environment,
    )


def _git_text(repository: Path, *arguments: str) -> str:
    completed = _git_bytes(repository, *arguments)
    if completed.returncode:
        detail = completed.stderr.decode(errors="replace").strip()
        raise RuntimeError(f"git {' '.join(arguments)} failed: {detail}")
    return completed.stdout.decode(errors="strict").strip()


def _legacy_canonical(value: Any) -> Any:
    """Exactly mirror evaluations/component-reuse-fingerprint/compare.py."""

    if isinstance(value, dict):
        return {
            key: _legacy_canonical(item)
            for key, item in sorted(value.items())
            if key not in LEGACY_VOLATILE_FIELDS
        }
    if isinstance(value, list):
        return [_legacy_canonical(item) for item in value]
    if isinstance(value, str):
        return LEGACY_CHECKOUT_PATH.sub("<co>/", value)
    return value


def _legacy_fingerprint(value: Any) -> str:
    # compare.py uses json.dumps defaults, including spaces, then truncates to 12.
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:12]


def _drop_reviewed_scan_counts(value: Mapping[str, Any]) -> dict[str, Any]:
    result = json.loads(json.dumps(value))
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
                if not (isinstance(item, str) and REVIEWED_SCAN_SUMMARY.match(item))
            ]
    return result


def _drop_every_version_key(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _drop_every_version_key(item)
            for key, item in value.items()
            if key != "version"
        }
    if isinstance(value, list):
        return [_drop_every_version_key(item) for item in value]
    return value


def _fingerprint(value: Any) -> str:
    return _sha256_bytes(_canonical_bytes(value))


def compare_pair(
    component: str,
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    *,
    left_checkout: str | Path | None = None,
    right_checkout: str | Path | None = None,
) -> dict[str, Any]:
    """Compare one extraction pair at legacy and current analyzer-payload tiers."""

    left_canonical = _legacy_canonical(dict(left))
    right_canonical = _legacy_canonical(dict(right))
    left_semantic = {
        key: item
        for key, item in left_canonical.items()
        if key not in LEGACY_NOISE_FIELDS
    }
    right_semantic = {
        key: item
        for key, item in right_canonical.items()
        if key not in LEGACY_NOISE_FIELDS
    }
    left_scan = _drop_reviewed_scan_counts(left_semantic)
    right_scan = _drop_reviewed_scan_counts(right_semantic)
    left_no_versions = _drop_every_version_key(left_scan)
    right_no_versions = _drop_every_version_key(right_scan)
    current_left = _semantic_analyzer(left, left_checkout)
    current_right = _semantic_analyzer(right, right_checkout)

    def differing(
        left_value: Mapping[str, Any], right_value: Mapping[str, Any]
    ) -> list[str]:
        return sorted(
            key
            for key in set(left_value) | set(right_value)
            if left_value.get(key) != right_value.get(key)
        )

    return {
        "component": component,
        "same_commit": left.get("commit_sha") == right.get("commit_sha"),
        "legacy_compare_py": {
            "same_full_canonical_json": _legacy_fingerprint(left_canonical)
            == _legacy_fingerprint(right_canonical),
            "full_fingerprints": {
                "ea1": _legacy_fingerprint(left_canonical),
                "ea2": _legacy_fingerprint(right_canonical),
            },
            "same_semantic_facts": _legacy_fingerprint(left_semantic)
            == _legacy_fingerprint(right_semantic),
            "semantic_fingerprints": {
                "ea1": _legacy_fingerprint(left_semantic),
                "ea2": _legacy_fingerprint(right_semantic),
            },
            "differing_categories": differing(left_semantic, right_semantic),
        },
        "reviewed_scan_count_tier": {
            "same": _fingerprint(left_scan) == _fingerprint(right_scan),
            "fingerprints": {
                "ea1": _fingerprint(left_scan),
                "ea2": _fingerprint(right_scan),
            },
            "differing_categories": differing(left_scan, right_scan),
            "scope": "only the two reviewed legacy summary:scanned forms are removed",
        },
        "drop_all_version_keys_sensitivity_only": {
            "same": _fingerprint(left_no_versions) == _fingerprint(right_no_versions),
            "fingerprints": {
                "ea1": _fingerprint(left_no_versions),
                "ea2": _fingerprint(right_no_versions),
            },
            "differing_categories": differing(left_no_versions, right_no_versions),
            "recommended": False,
            "reason": (
                "dependency and other version fields are meaningful and remain required"
            ),
        },
        "current_sc13_analyzer_payload_only": {
            "same": _fingerprint(current_left) == _fingerprint(current_right),
            "fingerprints": {
                "ea1": _fingerprint(current_left),
                "ea2": _fingerprint(current_right),
            },
            "differing_categories": differing(current_left, current_right),
            "complete_sc13_fingerprint": False,
            "reason": (
                "component configuration, overlays, contracts, settings, dependency "
                "observations, and producing synthesis context are not present"
            ),
        },
    }


def _source_status(repository: Path) -> dict[str, Any]:
    status = _git_bytes(
        repository,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--ignored=matching",
    )
    if status.returncode:
        raise RuntimeError(status.stderr.decode(errors="replace"))
    raw_entries = [entry for entry in status.stdout.split(b"\0") if entry]
    return {
        "head": _git_text(repository, "rev-parse", "HEAD"),
        "tree": _git_text(repository, "rev-parse", "HEAD^{tree}"),
        "origin_url": _git_text(repository, "config", "--get", "remote.origin.url"),
        "status_sha256": _sha256_bytes(status.stdout),
        "status_entries": [
            entry.decode(errors="backslashreplace") for entry in raw_entries
        ],
    }


def _parse_tree(repository: Path, commit: str) -> tuple[bytes, list[dict[str, Any]]]:
    listing = _git_bytes(
        repository, "ls-tree", "-rz", "-l", "--full-tree", f"{commit}^{{tree}}"
    )
    if listing.returncode:
        raise RuntimeError(listing.stderr.decode(errors="replace"))
    entries: list[dict[str, Any]] = []
    for raw_record in listing.stdout.split(b"\0"):
        if not raw_record:
            continue
        metadata, raw_path = raw_record.split(b"\t", 1)
        mode, object_type, object_id, size = metadata.split(b" ", 3)
        size = size.strip()
        try:
            path = raw_path.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise ValueError(f"non-UTF-8 Git path {raw_path.hex()}") from error
        entries.append(
            {
                "mode": mode.decode(),
                "type": object_type.decode(),
                "object": object_id.decode(),
                "size": None if size == b"-" else int(size),
                "path": path,
            }
        )
    return listing.stdout, entries


def _copy_blob(stream: Any, size: int, destination: Path | None) -> bytes | str:
    digest = hashlib.sha256()
    remaining = size
    chunks: list[bytes] = []
    output = destination.open("wb") if destination is not None else None
    try:
        while remaining:
            chunk = stream.read(min(1024 * 1024, remaining))
            if not chunk:
                raise RuntimeError("unexpected EOF from git cat-file --batch")
            remaining -= len(chunk)
            digest.update(chunk)
            if output is not None:
                output.write(chunk)
            else:
                chunks.append(chunk)
    finally:
        if output is not None:
            output.close()
    return b"".join(chunks) if destination is None else digest.hexdigest()


def _minimal_git_directory(
    destination: Path, repository: Path, commit: str, origin: str
) -> None:
    initialized = subprocess.run(
        ("git", "init", "--quiet", "--template=", str(destination)),
        capture_output=True,
        check=False,
    )
    if initialized.returncode:
        raise RuntimeError(initialized.stderr.decode(errors="replace"))
    git_directory = destination / ".git"
    (git_directory / "objects/info").mkdir(parents=True, exist_ok=True)
    common = Path(_git_text(repository, "rev-parse", "--git-common-dir"))
    if not common.is_absolute():
        common = (repository / common).resolve()
    object_paths = [str((common / "objects").resolve())]
    source_alternates = common / "objects/info/alternates"
    if source_alternates.is_file():
        object_paths.extend(
            line for line in source_alternates.read_text().splitlines() if line.strip()
        )
    (git_directory / "objects/info/alternates").write_text(
        "\n".join(object_paths) + "\n"
    )
    (git_directory / "HEAD").write_text(commit + "\n")
    (git_directory / "config").write_text(
        "[core]\n\trepositoryformatversion = 0\n\tbare = false\n\tfilemode = true\n"
    )
    configured = subprocess.run(
        (
            "git",
            "config",
            "--file",
            str(git_directory / "config"),
            "remote.origin.url",
            origin,
        ),
        capture_output=True,
        check=False,
    )
    if configured.returncode:
        raise RuntimeError(configured.stderr.decode(errors="replace"))
    shallow = common / "shallow"
    if shallow.is_file():
        shutil.copyfile(shallow, git_directory / "shallow")


def _materialize_tree(
    repository: Path, commit: str, destination: Path
) -> dict[str, Any]:
    listing, entries = _parse_tree(repository, commit)
    destination.mkdir(parents=True)
    origin = _git_text(repository, "config", "--get", "remote.origin.url")
    environment = os.environ.copy()
    environment["GIT_NO_LAZY_FETCH"] = "1"
    process = subprocess.Popen(
        ("git", "-C", str(repository), "cat-file", "--batch"),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
    )
    assert process.stdin is not None and process.stdout is not None
    physical_records: list[dict[str, str]] = []
    gitlinks: list[dict[str, str]] = []
    symlinks: list[dict[str, str]] = []
    try:
        for entry in entries:
            path = destination / entry["path"]
            if not path.resolve().is_relative_to(destination.resolve()):
                raise ValueError(f"unsafe Git path: {entry['path']!r}")
            if entry["mode"] == "160000":
                path.mkdir(parents=True, exist_ok=True)
                gitlinks.append({"path": entry["path"], "commit": entry["object"]})
                continue
            if entry["type"] != "blob" or entry["size"] is None:
                raise ValueError(f"unsupported Git tree entry: {entry}")
            path.parent.mkdir(parents=True, exist_ok=True)
            process.stdin.write((entry["object"] + "\n").encode())
            process.stdin.flush()
            header = process.stdout.readline().rstrip(b"\n").split()
            if len(header) != 3 or header[1] != b"blob":
                raise RuntimeError(
                    f"git cat-file rejected {entry['object']}: {header!r}"
                )
            size = int(header[2])
            if size != entry["size"]:
                raise RuntimeError(f"blob size changed for {entry['path']}")
            if entry["mode"] == "120000":
                raw_target = _copy_blob(process.stdout, size, None)
                assert isinstance(raw_target, bytes)
                target = raw_target.decode("utf-8", errors="surrogateescape")
                resolved_target = (path.parent / target).resolve()
                if Path(target).is_absolute() or not resolved_target.is_relative_to(
                    destination.resolve()
                ):
                    raise ValueError(
                        f"symlink escapes isolated committed tree: {entry['path']!r}"
                    )
                os.symlink(target, path)
                digest = _sha256_bytes(raw_target)
                symlinks.append({"path": entry["path"], "target_sha256": digest})
            else:
                digest = _copy_blob(process.stdout, size, path)
                assert isinstance(digest, str)
                path.chmod(0o755 if entry["mode"] == "100755" else 0o644)
            if process.stdout.read(1) != b"\n":
                raise RuntimeError("invalid git cat-file record delimiter")
            physical_records.append(
                {"mode": entry["mode"], "path": entry["path"], "sha256": digest}
            )
    finally:
        if process.stdin is not None:
            process.stdin.close()
        return_code = process.wait()
    stderr = process.stderr.read().decode(errors="replace") if process.stderr else ""
    if return_code:
        raise RuntimeError(f"git cat-file --batch failed: {stderr}")
    _minimal_git_directory(destination, repository, commit, origin)
    verified = {
        "head": _git_text(destination, "rev-parse", "HEAD"),
        "tree": _git_text(destination, "rev-parse", "HEAD^{tree}"),
        "origin_url": _git_text(destination, "config", "--get", "remote.origin.url"),
    }
    return {
        "git_ls_tree_sha256": _sha256_bytes(listing),
        "entry_count": len(entries),
        "blob_count": sum(entry["type"] == "blob" for entry in entries),
        "blob_bytes": sum(entry["size"] or 0 for entry in entries),
        "physical_manifest_sha256": _fingerprint(physical_records),
        "gitlinks": gitlinks,
        "gitlink_limit": (
            "gitlinks are recorded but their external submodule trees are not "
            "materialized"
            if gitlinks
            else "none"
        ),
        "symlinks": symlinks,
        "verified_metadata": verified,
    }


def _physical_manifest(repository: Path) -> dict[str, Any]:
    records: list[dict[str, str]] = []
    for root, directories, files in os.walk(repository, followlinks=False):
        root_path = Path(root)
        if root_path == repository:
            directories[:] = [name for name in directories if name != ".git"]
        for name in sorted(files):
            path = root_path / name
            relative = path.relative_to(repository).as_posix()
            value = (
                os.readlink(path).encode(errors="surrogateescape")
                if path.is_symlink()
                else path.read_bytes()
            )
            mode = stat.S_IMODE(path.lstat().st_mode)
            records.append(
                {"mode": f"{mode:o}", "path": relative, "sha256": _sha256_bytes(value)}
            )
    records.sort(key=lambda item: item["path"])
    return {"file_count": len(records), "sha256": _fingerprint(records)}


def _run_once(command: Sequence[str], timeout_seconds: int) -> dict[str, Any]:
    started = time.time()
    monotonic = time.monotonic()
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
    ended = time.time()
    return {
        "command": list(command),
        "started_unix": started,
        "ended_unix": ended,
        "duration_seconds": time.monotonic() - monotonic,
        "exit_code": process.returncode,
        "timed_out": timed_out,
        "stdout": stdout,
        "stderr": stderr,
    }


def _slug(component: str) -> str:
    readable = re.sub(r"[^A-Za-z0-9_.-]+", "-", component).strip("-")[:80]
    return f"{readable}-{hashlib.sha256(component.encode()).hexdigest()[:12]}"


def _extract_command(analyzer: Path, checkout: Path, output: Path) -> tuple[str, ...]:
    # The recorded committed analyzer defaults to an empty distribution selector,
    # which compares the repository without guessing a platform overlay.
    return (str(analyzer), "extract", str(checkout), "--output", str(output))


def _extract_one(
    entry: Mapping[str, Any],
    *,
    object_source: Path,
    analyzer: Path,
    output: Path,
    scratch: Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    component = str(entry["component"])
    side = str(entry["side"])
    slug = _slug(component)
    evidence = output / "extractions" / side
    evidence.mkdir(parents=True, exist_ok=True)
    prefix = evidence / slug
    raw_output = Path(f"{prefix}.json")
    result: dict[str, Any] = {
        "component": component,
        "side": side,
        "slug": slug,
        "original_checkout": str(entry["path"]),
        "object_source": str(object_source),
        "expected_commit": entry["expected_commit"],
        "expected_tree": entry["expected_tree"],
        "raw_output": str(raw_output.relative_to(output)),
    }
    try:
        original_before = _source_status(Path(str(entry["path"])))
        object_before = _source_status(object_source)
        if (
            object_before["head"] != entry["expected_commit"]
            or object_before["tree"] != entry["expected_tree"]
        ):
            raise ValueError("object source does not match recorded commit/tree")
        with tempfile.TemporaryDirectory(
            prefix=f"{side}-{slug}-", dir=scratch
        ) as temporary:
            checkout = Path(temporary) / "checkouts" / f"rhoai-3.6-{side}" / slug
            materialized = _materialize_tree(
                object_source, str(entry["expected_commit"]), checkout
            )
            before_physical = _physical_manifest(checkout)
            if materialized["verified_metadata"] != {
                "head": entry["expected_commit"],
                "tree": entry["expected_tree"],
                "origin_url": object_before["origin_url"],
            }:
                raise ValueError("isolated committed-tree metadata mismatch")
            command = _extract_command(analyzer, checkout, raw_output)
            executed = _run_once(command, timeout_seconds)
            after_physical = _physical_manifest(checkout)
            source_unchanged = before_physical == after_physical
            stdout_path = Path(f"{prefix}.stdout")
            stderr_path = Path(f"{prefix}.stderr")
            stdout_path.write_bytes(executed.pop("stdout"))
            stderr_path.write_bytes(executed.pop("stderr"))
            result.update(
                {
                    "status": "success" if executed["exit_code"] == 0 else "failed",
                    "source": {
                        "original_before": original_before,
                        "object_source_before": object_before,
                        "committed_tree_materialization": materialized,
                        "isolated_physical_before": before_physical,
                        "isolated_physical_after": after_physical,
                        "isolated_source_unchanged": source_unchanged,
                        "materialized_checkout": str(checkout),
                        "retained_after_run": False,
                    },
                    "execution": executed,
                    "stdout_sha256": _sha256_file(stdout_path),
                    "stderr_sha256": _sha256_file(stderr_path),
                }
            )
            if executed["exit_code"] != 0:
                stderr = stderr_path.read_text(errors="replace")
                result["error"] = stderr.strip() or (
                    f"analyzer exited {executed['exit_code']} without stderr"
                )
            if executed["exit_code"] == 0 and not source_unchanged:
                result["status"] = "failed"
                result["error"] = "analyzer changed the isolated committed source"
            if raw_output.is_file():
                result["raw_output_sha256"] = _sha256_file(raw_output)
                result["raw_output_bytes"] = raw_output.stat().st_size
                try:
                    decoded = json.loads(raw_output.read_text())
                    if not isinstance(decoded, dict):
                        raise ValueError("extractor output is not a JSON object")
                    result["raw_output_valid_json_object"] = True
                    result["analyzer_reported_commit"] = decoded.get("commit_sha")
                    result["analyzer_reported_repository"] = decoded.get("repo")
                    if decoded.get("commit_sha") != entry["expected_commit"]:
                        result["status"] = "failed"
                        result["error"] = (
                            "analyzer output commit does not match recorded source"
                        )
                except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as error:
                    result["raw_output_valid_json_object"] = False
                    result["status"] = "failed"
                    result["error"] = str(error)
            elif executed["exit_code"] == 0:
                result["status"] = "failed"
                result["error"] = "successful command did not create raw JSON"
        original_after = _source_status(Path(str(entry["path"])))
        object_after = _source_status(object_source)
        result["source"]["original_after"] = original_after
        result["source"]["object_source_after"] = object_after
        result["source"]["original_checkout_unchanged"] = (
            original_before == original_after
        )
        result["source"]["object_source_unchanged"] = object_before == object_after
        if original_before != original_after or object_before != object_after:
            result["status"] = "failed"
            result["error"] = "source checkout identity changed during extraction"
    except Exception as error:  # preserve every bounded per-source failure
        result["status"] = "failed"
        result["error"] = f"{type(error).__name__}: {error}"
    _write_json(output / "runs" / side / f"{slug}.json", result)
    return result


def verify_analyzer_build(
    *,
    root: Path,
    analyzer: Path,
    analyzer_source: Path,
    expected_commit: str,
    expected_archive_sha256: str,
    expected_binary_sha256: str,
    build_command: str,
) -> dict[str, Any]:
    archive = subprocess.run(
        ("git", "archive", expected_commit, "src/arch-analyzer"),
        cwd=root,
        capture_output=True,
        check=False,
    )
    if archive.returncode:
        raise RuntimeError(archive.stderr.decode(errors="replace"))
    archive_sha256 = _sha256_bytes(archive.stdout)
    if archive_sha256 != expected_archive_sha256:
        raise ValueError("committed analyzer archive SHA-256 mismatch")
    binary_sha256 = _sha256_file(analyzer)
    if binary_sha256 != expected_binary_sha256:
        raise ValueError("committed analyzer binary SHA-256 mismatch")
    source_records: list[dict[str, Any]] = []
    with tarfile.open(fileobj=__import__("io").BytesIO(archive.stdout)) as stream:
        prefix = "src/arch-analyzer/"
        for member in stream.getmembers():
            if not member.isfile() and not member.issym():
                continue
            relative = member.name.removeprefix(prefix)
            path = analyzer_source / relative
            if member.issym():
                raw = member.linkname.encode()
                actual = os.readlink(path).encode()
            else:
                archived = stream.extractfile(member)
                assert archived is not None
                raw = archived.read()
                actual = path.read_bytes()
            if raw != actual:
                raise ValueError(
                    f"prepared analyzer source differs from archive: {relative}"
                )
            source_records.append(
                {"path": relative, "mode": member.mode, "sha256": _sha256_bytes(raw)}
            )
    disk_paths = sorted(
        path.relative_to(analyzer_source).as_posix()
        for path in analyzer_source.rglob("*")
        if path.is_file() or path.is_symlink()
    )
    if disk_paths != sorted(record["path"] for record in source_records):
        raise ValueError("prepared analyzer source has missing or extra paths")
    build_info = subprocess.run(
        ("go", "version", "-m", str(analyzer)),
        capture_output=True,
        text=True,
        check=False,
    )
    if build_info.returncode:
        raise RuntimeError(build_info.stderr)
    if "vcs.modified=" in build_info.stdout or "vcs.revision=" in build_info.stdout:
        raise ValueError(
            "-buildvcs=false analyzer unexpectedly contains VCS build settings"
        )
    return {
        "classification": "committed-source-archive-build",
        "commit": expected_commit,
        "commit_tree": _git_text(root, "rev-parse", f"{expected_commit}^{{tree}}"),
        "archive_command": ["git", "archive", expected_commit, "src/arch-analyzer"],
        "archive_sha256": archive_sha256,
        "prepared_source": str(analyzer_source),
        "prepared_source_file_count": len(source_records),
        "prepared_source_manifest_sha256": _fingerprint(source_records),
        "binary": str(analyzer),
        "binary_sha256": binary_sha256,
        "binary_bytes": analyzer.stat().st_size,
        "recorded_build_command": build_command,
        "build_vcs": False,
        "go_version": subprocess.run(
            ("go", "version"), capture_output=True, text=True, check=True
        ).stdout.strip(),
        "go_build_info": build_info.stdout.splitlines(),
        "identity_limit": (
            "the binary omits VCS settings by design; commit identity is established "
            "by the verified Git archive and matching prepared-source manifest"
        ),
    }


def fresh_compare_reuse(
    *,
    root: Path,
    output: Path,
    analyzer: Path,
    source_audit: Path,
    prepared_inputs: Path,
    comparison_script: Path,
    expected_commit: str,
    expected_archive_sha256: str,
    expected_binary_sha256: str,
    build_command: str,
    jobs: int = 4,
    timeout_seconds: int = 900,
    scratch_root: Path | None = None,
    successful_extractions_from: Path | None = None,
) -> dict[str, Any]:
    if output.exists():
        raise ValueError(f"output directory already exists: {output}")
    output.mkdir(parents=True)
    owned_sources = (
        "scripts/structured_component_final_evidence.py",
        "scripts/structured_component_fresh_reuse.py",
        "tests/test_structured_component_final_evidence.py",
    )
    source_manifest: dict[str, str] = {}
    for relative in owned_sources:
        source = root / relative
        destination = output / "source" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        source_manifest[relative] = _sha256_file(source)
    _write_json(
        output / "source-manifest.json",
        {
            "files": source_manifest,
            "snapshot_sha256": _fingerprint(source_manifest),
        },
    )
    scratch_base = scratch_root or Path(tempfile.gettempdir())
    scratch_base.mkdir(parents=True, exist_ok=True)
    build = verify_analyzer_build(
        root=root,
        analyzer=analyzer,
        analyzer_source=Path(
            json.loads(prepared_inputs.read_text())["analyzer_source"]
        ),
        expected_commit=expected_commit,
        expected_archive_sha256=expected_archive_sha256,
        expected_binary_sha256=expected_binary_sha256,
        build_command=build_command,
    )
    _write_json(output / "analyzer-build.json", build)
    if _sha256_file(comparison_script) != EXPECTED_COMPARISON_SHA256:
        raise ValueError("unchanged compare.py identity mismatch")
    audit = json.loads(source_audit.read_text())
    prepared = json.loads(prepared_inputs.read_text())
    isolated = {
        (item["component"], item["side"]): Path(item["path"])
        for item in prepared["isolated_copies"]
    }
    entries = list(audit["entries"])
    if len(entries) != 184:
        raise ValueError(f"expected 184 source sides, found {len(entries)}")
    results: list[dict[str, Any]] = []
    progress_path = output / "fresh-extraction.progress.txt"
    carried_keys: set[tuple[str, str]] = set()
    if successful_extractions_from is not None:
        prior_build = json.loads(
            (successful_extractions_from / "analyzer-build.json").read_text()
        )
        if (
            prior_build["commit"] != expected_commit
            or prior_build["binary_sha256"] != expected_binary_sha256
        ):
            raise ValueError("prior successful extractions use a different analyzer")
        prior_index = json.loads(
            (successful_extractions_from / "extraction-index.json").read_text()
        )
        raw_path_counts = Counter(
            item.get("raw_output")
            for item in prior_index
            if item.get("status") == "success"
        )
        for prior in prior_index:
            key = (prior["component"], prior["side"])
            source = prior.get("source", {})
            prior_raw = successful_extractions_from / prior.get("raw_output", "")
            prior_stdout = prior_raw.with_suffix(".stdout")
            prior_stderr = prior_raw.with_suffix(".stderr")
            eligible = (
                prior.get("status") == "success"
                and raw_path_counts[prior.get("raw_output")] == 1
                and prior_raw.is_file()
                and _sha256_file(prior_raw) == prior.get("raw_output_sha256")
                and prior_stdout.is_file()
                and _sha256_file(prior_stdout) == prior.get("stdout_sha256")
                and prior_stderr.is_file()
                and _sha256_file(prior_stderr) == prior.get("stderr_sha256")
                and source.get("original_checkout_unchanged") is True
                and source.get("object_source_unchanged") is True
                and source.get("isolated_source_unchanged") is True
            )
            if not eligible:
                continue
            slug = _slug(prior["component"])
            new_prefix = output / "extractions" / prior["side"] / slug
            new_prefix.parent.mkdir(parents=True, exist_ok=True)
            new_raw = Path(f"{new_prefix}.json")
            shutil.copyfile(prior_raw, new_raw)
            shutil.copyfile(prior_stdout, Path(f"{new_prefix}.stdout"))
            shutil.copyfile(prior_stderr, Path(f"{new_prefix}.stderr"))
            carried = dict(prior)
            carried["raw_output"] = str(new_raw.relative_to(output))
            carried["carried_from"] = str(successful_extractions_from)
            _write_json(output / "runs" / prior["side"] / f"{slug}.json", carried)
            results.append(carried)
            carried_keys.add(key)
        with progress_path.open("a") as stream:
            stream.write(
                f"carried {len(results)} unique hash-verified successful extractions "
                f"from {successful_extractions_from}\n"
            )
    pending_entries = [
        entry
        for entry in entries
        if (entry["component"], entry["side"]) not in carried_keys
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as executor:
        futures = {
            executor.submit(
                _extract_one,
                entry,
                object_source=isolated.get(
                    (entry["component"], entry["side"]), Path(entry["path"])
                ),
                analyzer=analyzer,
                output=output,
                scratch=scratch_base,
                timeout_seconds=timeout_seconds,
            ): entry
            for entry in pending_entries
        }
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
            progress = (
                f"fresh-reuse {len(results)}/{len(entries)} "
                f"{result['side']} {result['component']}: {result['status']}"
            )
            with progress_path.open("a") as stream:
                stream.write(progress + "\n")
            print(progress, flush=True)
    results.sort(key=lambda item: (item["component"], item["side"]))
    _write_json(output / "extraction-index.json", results)

    by_key = {(item["component"], item["side"]): item for item in results}
    pairs: list[dict[str, Any]] = []
    for component in sorted({entry["component"] for entry in entries}):
        left_run = by_key[(component, "ea1")]
        right_run = by_key[(component, "ea2")]
        if left_run["status"] != "success" or right_run["status"] != "success":
            pair = {
                "component": component,
                "status": "not-compared-extraction-failure",
                "ea1_status": left_run["status"],
                "ea2_status": right_run["status"],
            }
        else:
            left = json.loads((output / left_run["raw_output"]).read_text())
            right = json.loads((output / right_run["raw_output"]).read_text())
            pair = compare_pair(
                component,
                left,
                right,
                left_checkout=left_run["source"]["materialized_checkout"],
                right_checkout=right_run["source"]["materialized_checkout"],
            )
            pair["status"] = "compared"
            pair["source_commits"] = {
                "ea1": left_run["expected_commit"],
                "ea2": right_run["expected_commit"],
            }
            pair["source_trees"] = {
                "ea1": left_run["expected_tree"],
                "ea2": right_run["expected_tree"],
            }
            pair["raw_output_sha256"] = {
                "ea1": left_run["raw_output_sha256"],
                "ea2": right_run["raw_output_sha256"],
            }
        pairs.append(pair)
        _write_json(output / "pairs" / f"{_slug(component)}.json", pair)
    compared = [pair for pair in pairs if pair["status"] == "compared"]

    comparison = subprocess.run(
        ("python3", str(comparison_script), str(output / "extractions")),
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    (output / "compare-py.stdout").write_text(comparison.stdout)
    (output / "compare-py.stderr").write_text(comparison.stderr)
    _write_json(
        output / "compare-py.run.json",
        {
            "command": ["python3", str(comparison_script), str(output / "extractions")],
            "exit_code": comparison.returncode,
            "stdout_sha256": _sha256_file(output / "compare-py.stdout"),
            "stderr_sha256": _sha256_file(output / "compare-py.stderr"),
        },
    )
    if comparison.returncode:
        raise RuntimeError("unchanged compare.py failed; retained stdout/stderr")

    def total(path: Sequence[str]) -> int:
        value = 0
        for pair in compared:
            current: Any = pair
            for key in path:
                current = current[key]
            value += bool(current)
        return value

    difference_counts = Counter(
        category
        for pair in compared
        for category in pair["legacy_compare_py"]["differing_categories"]
    )
    summary = {
        "requested_pairs": len(entries) // 2,
        "extraction_attempts": len(results),
        "extractions_executed_this_attempt": len(pending_entries),
        "successful_extractions_carried_from_prior_attempt": len(carried_keys),
        "successful_extractions": sum(item["status"] == "success" for item in results),
        "failed_extractions": sum(item["status"] != "success" for item in results),
        "compared_pairs": len(compared),
        "uncompared_pairs": len(pairs) - len(compared),
        "same_commit": total(("same_commit",)),
        "legacy_compare_py_same_full": total(
            ("legacy_compare_py", "same_full_canonical_json")
        ),
        "legacy_candidate_semantic_facts": total(
            ("legacy_compare_py", "same_semantic_facts")
        ),
        "reviewed_scan_count_tier": total(("reviewed_scan_count_tier", "same")),
        "drop_all_version_keys_sensitivity_only": total(
            ("drop_all_version_keys_sensitivity_only", "same")
        ),
        "current_sc13_analyzer_payload_only": total(
            ("current_sc13_analyzer_payload_only", "same")
        ),
        "verified_reuse": 0,
    }
    report = {
        "schema_version": "structured-component-fresh-reuse-comparison/v1",
        "mode": "fresh-extraction-from-deterministically-materialized-committed-trees",
        "summary": summary,
        "analyzer_build": build,
        "source_selection": {
            "audit": str(source_audit),
            "audit_sha256": _sha256_file(source_audit),
            "prepared_inputs": str(prepared_inputs),
            "prepared_inputs_sha256": _sha256_file(prepared_inputs),
            "original_checkouts_used_as_worktrees": False,
            "materialization": (
                "Git blobs were copied from the recorded commits with cat-file; "
                "checkout filters and hooks were not run; temporary minimal Git "
                "metadata retained commit history and the original origin URL; "
                "the minimal metadata intentionally has no Git index"
            ),
            "dirty_originals": 2,
            "dirty_object_sources_replaced_by_prepared_clean_copies": 2,
            "successful_extractions_from": (
                str(successful_extractions_from)
                if successful_extractions_from is not None
                else None
            ),
            "ignored_and_untracked_inputs": (
                "excluded by exact committed-tree materialization; original status "
                "including ignored/untracked names is retained before and after"
            ),
        },
        "comparison_contracts": {
            "unchanged_compare_py": {
                "path": str(comparison_script),
                "sha256": _sha256_file(comparison_script),
                "stdout": "compare-py.stdout",
                "classification": "legacy candidate analyzer-fact comparison",
            },
            "reviewed_scan_count_tier": (
                "additional diagnostic matching the two exact exclusions reviewed "
                "for the current analyzer payload normalizer"
            ),
            "drop_all_version_keys_sensitivity_only": (
                "not a supported reuse tier; versions remain meaningful"
            ),
            "current_sc13_analyzer_payload_only": (
                "current analyzer payload normalization only, not the complete "
                "SC-13 key"
            ),
            "verified_reuse": (
                "zero: historical pairs have no accepted structured predecessor, "
                "producing-model/synthesis context, or verified read/search "
                "dependencies"
            ),
        },
        "legacy_differing_category_counts": dict(difference_counts.most_common()),
        "historical_separation": {
            "historical_build": (
                "39209078846f15f1909373c106d2d665a907a509 plus 11 dirty analyzer files"
            ),
            "historical_saved_rows": (
                "unchanged and not relabeled as this committed build"
            ),
            "historical_extraction_failures": [
                "llm-d/llm-d-infra",
                "llm-d/llm-d-go-template",
            ],
            "fresh_failures_are_reported_only_from_this run": [
                {
                    "component": item["component"],
                    "side": item["side"],
                    "error": item.get("error"),
                }
                for item in results
                if item["status"] != "success"
            ],
        },
        "measurements": {
            "live_model_calls": 0,
            "tokens": "unavailable-no-live-run",
            "cost": "unavailable-no-live-run",
            "promised_savings": False,
            "aggregate_subprocess_seconds": sum(
                item.get("execution", {}).get("duration_seconds", 0) for item in results
            ),
            "executed_this_attempt_subprocess_seconds": sum(
                item.get("execution", {}).get("duration_seconds", 0)
                for item in results
                if (item["component"], item["side"]) not in carried_keys
            ),
            "carried_prior_attempt_subprocess_seconds": sum(
                item.get("execution", {}).get("duration_seconds", 0)
                for item in results
                if (item["component"], item["side"]) in carried_keys
            ),
            "timing_scope": (
                "aggregate subprocess time; carried records retain their original "
                "attempt durations and are not current-attempt wall time"
            ),
        },
        "driver_source": {
            "manifest": "source-manifest.json",
            "manifest_sha256": _sha256_file(output / "source-manifest.json"),
            "progress_output": "fresh-extraction.progress.txt",
            "progress_output_sha256": _sha256_file(progress_path),
        },
        "pairs": pairs,
    }
    _write_json(output / "report.json", report)
    return report
