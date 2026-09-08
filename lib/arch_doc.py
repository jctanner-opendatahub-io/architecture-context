"""Integration helpers for the repository-local arch-doc command."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARCH_DOC_SOURCE = PROJECT_ROOT / "src" / "arch-doc"
ARCH_DOC_BINARY = PROJECT_ROOT / "bin" / "arch-doc"


class ArchDocAssemblyError(ValueError):
    """Structured failure returned by ``arch-doc assemble``."""

    def __init__(self, message: str, report: dict[str, object] | None = None):
        super().__init__(message)
        self.report = report or {}
        self.diagnostics = self.report.get("diagnostics", [])
        self.section_decisions = self.report.get("section_decisions", [])


class AssembledArchitecture(str):
    """Assembled Markdown with the structured arch-doc report attached."""

    report: dict[str, object]

    def __new__(
        cls, content: str, report: dict[str, object] | None = None
    ) -> AssembledArchitecture:
        value = super().__new__(cls, content)
        value.report = report or {}
        return value


def ensure_arch_doc_binary() -> Path:
    """Build and return arch-doc when the repository binary is not present."""

    configured = os.environ.get("ARCH_DOC_BIN")
    binary = Path(configured).expanduser().resolve() if configured else ARCH_DOC_BINARY
    if binary.is_file() and os.access(binary, os.X_OK) and not _source_is_newer(binary):
        return binary
    if not ARCH_DOC_SOURCE.is_dir():
        raise FileNotFoundError(
            f"arch-doc source directory not found: {ARCH_DOC_SOURCE}"
        )
    binary.parent.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment.setdefault("GOCACHE", "/tmp/arch-doc-gocache")
    completed = _run_process(
        ["go", "build", "-o", str(binary), "."],
        cwd=ARCH_DOC_SOURCE,
        env=environment,
    )
    if completed.returncode != 0:
        detail = (completed.stdout + completed.stderr).strip()
        raise RuntimeError(f"failed to build arch-doc: {detail}")
    return binary


def assemble_architecture_sections(
    base_text: str, candidate_text: str
) -> AssembledArchitecture:
    """Assemble candidate synthesis sections onto a table-merged base."""

    binary = ensure_arch_doc_binary()
    with TemporaryDirectory(prefix="arch-doc-") as temporary:
        root = Path(temporary)
        base = root / "base.md"
        candidate = root / "candidate.md"
        output = root / "assembled.md"
        report_path = root / "assembly-report.json"
        base.write_text(base_text)
        candidate.write_text(candidate_text)
        completed = _run_process(
            [
                str(binary),
                "assemble",
                "--base",
                str(base),
                "--candidate",
                str(candidate),
                "--output",
                str(output),
                "--report",
                str(report_path),
            ],
        )
        report = _read_assembly_report(report_path)
        if completed.returncode != 0:
            detail = (completed.stdout + completed.stderr).strip()
            raise ArchDocAssemblyError(
                f"arch-doc assemble failed: {detail}", report
            )
        return AssembledArchitecture(output.read_text(), report)


def _read_assembly_report(path: Path) -> dict[str, object] | None:
    if not path.is_file():
        return None
    try:
        decoded = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    return decoded if isinstance(decoded, dict) else None


def _run_process(command: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    """Run a process without using subprocess.run, which tests may patch globally."""

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        **kwargs,
    )
    stdout, stderr = process.communicate()
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def _source_is_newer(binary: Path) -> bool:
    """Return whether a source or manifest file is newer than the binary."""

    binary_mtime = binary.stat().st_mtime
    source_files = list(ARCH_DOC_SOURCE.glob("*.go")) + [
        ARCH_DOC_SOURCE / "go.mod",
        ARCH_DOC_SOURCE / "section-manifest.json",
    ]
    return any(
        path.is_file() and path.stat().st_mtime > binary_mtime
        for path in source_files
    )
