"""Codex SDK implementation of the pipeline agent contract."""

from __future__ import annotations

import asyncio
import dataclasses
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from openai_codex import AsyncCodex, Sandbox, SkillInput, TextInput

from lib.skill_paths import resolve_skill_file

if TYPE_CHECKING:
    from lib.progress import AgentProgress

_SKILL_PROMPT = re.compile(r"^/([A-Za-z0-9][A-Za-z0-9._-]*)(?:\s+(.*))?$", re.DOTALL)


@dataclass(slots=True)
class _StreamedTurnResult:
    """Subset of the SDK turn result consumed by the pipeline."""

    id: str
    status: object
    error: object | None
    duration_ms: int | None
    final_response: str | None
    items: list[object]
    usage: object | None


class _TerminalEventRenderer:
    """Render useful Codex events without exposing raw protocol noise."""

    def __init__(self, name: str):
        self.name = name
        self._message_ids: set[str] = set()
        self._open_message_id: str | None = None

    def render(self, event) -> None:
        payload = event.payload
        if event.method == "item/agentMessage/delta":
            self._render_message_delta(payload)
            return
        if event.method not in {"item/started", "item/completed"}:
            return

        item = _jsonable(getattr(payload, "item", None))
        if not isinstance(item, dict):
            return
        item_type = item.get("type")
        if item_type == "agentMessage" and event.method == "item/completed":
            self._finish_message(item)
        elif item_type == "commandExecution":
            self._render_command(event.method, item)

    def _render_message_delta(self, payload) -> None:
        item_id = str(getattr(payload, "item_id", ""))
        delta = getattr(payload, "delta", "")
        if not isinstance(delta, str) or not delta:
            return
        if self._open_message_id != item_id:
            self._ensure_newline()
            sys.stdout.write(f"[{self.name}] ")
            self._open_message_id = item_id
        self._message_ids.add(item_id)
        sys.stdout.write(delta)
        sys.stdout.flush()

    def _finish_message(self, item: dict) -> None:
        item_id = str(item.get("id", ""))
        if item_id not in self._message_ids:
            text = item.get("text")
            if isinstance(text, str) and text:
                self._ensure_newline()
                sys.stdout.write(f"[{self.name}] {text}")
        if self._open_message_id == item_id or item_id not in self._message_ids:
            self._ensure_newline()

    def _render_command(self, method: str, item: dict) -> None:
        self._ensure_newline()
        if method == "item/started":
            command = " ".join(str(item.get("command", "")).split())
            if len(command) > 180:
                command = f"{command[:177]}..."
            print(f"[{self.name}] command: {command}", flush=True)
            return
        status = item.get("status", "completed")
        exit_code = item.get("exit_code")
        duration_ms = item.get("duration_ms")
        details = [str(status)]
        if exit_code is not None:
            details.append(f"exit={exit_code}")
        if duration_ms is not None:
            details.append(f"{duration_ms}ms")
        print(f"[{self.name}] command {'; '.join(details)}", flush=True)

    def _ensure_newline(self) -> None:
        if self._open_message_id is not None:
            sys.stdout.write("\n")
            sys.stdout.flush()
            self._open_message_id = None


def _codex_input(
    prompt: str, enable_skills: bool, cwd: str | None = None,
) -> str | list[object]:
    """Translate the pipeline's slash-skill convention to Codex SDK input."""
    if not enable_skills:
        return prompt
    match = _SKILL_PROMPT.match(prompt.strip())
    if not match:
        raise ValueError(
            "Skill-enabled Codex prompts must start with /<skill-name>"
        )
    name, arguments = match.groups()
    staged_skill = (
        Path(cwd) / ".agents" / "skills" / name / "SKILL.md" if cwd else None
    )
    skill_file = (
        staged_skill if staged_skill and staged_skill.is_file()
        else resolve_skill_file(name)
    )
    items: list[object] = [
        SkillInput(name=name, path=str(skill_file.resolve()))
    ]
    items.append(TextInput(text=(
        f"Execute the attached {name} skill now. Read its SKILL.md first and "
        "perform its workflow directly. You are a pipeline worker. "
        "The following are skill arguments and task context:\n"
        f"{arguments or ''}"
    )))
    return items


def _jsonable(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return _jsonable(dataclasses.asdict(value))
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "__dict__"):
        return _jsonable(vars(value))
    if hasattr(value, "value"):
        return value.value
    return value


def _value(value: object) -> object:
    """Return an enum's wire value while preserving plain values."""
    return getattr(value, "value", value)


def _final_response(items: list[object]) -> str | None:
    """Extract the last agent response without depending on generated types."""
    fallback = None
    for item in reversed(items):
        item_data = _jsonable(item)
        if not isinstance(item_data, dict):
            continue
        item_type = item_data.get("type")
        text = item_data.get("text")
        phase = item_data.get("phase")
        if item_type != "agentMessage" or not isinstance(text, str):
            continue
        if phase in {"finalAnswer", "final_answer"}:
            return text
        if phase is None and fallback is None:
            fallback = text
    return fallback


async def _stream_turn(turn, log, name: str, show_events: bool):
    """Log turn notifications as JSONL and collect the terminal result."""
    completed_turn = None
    items = []
    usage = None
    renderer = _TerminalEventRenderer(name) if show_events else None

    async for event in turn.stream():
        event_data = _jsonable(event)
        log.write(json.dumps(event_data, separators=(",", ":"), default=str))
        log.write("\n")
        log.flush()
        if renderer is not None:
            renderer.render(event)

        payload = event.payload
        event_turn_id = getattr(payload, "turn_id", None)
        if event.method == "item/completed" and event_turn_id == turn.id:
            items.append(payload.item)
        elif (
            event.method == "thread/tokenUsage/updated"
            and event_turn_id == turn.id
        ):
            usage = payload.token_usage
        elif event.method == "turn/completed":
            candidate = getattr(payload, "turn", None)
            if candidate is not None and candidate.id == turn.id:
                completed_turn = candidate

    if completed_turn is None:
        raise RuntimeError("turn completed event not received")

    status = _value(completed_turn.status)
    if status == "failed":
        error = completed_turn.error
        message = getattr(error, "message", None)
        raise RuntimeError(message or f"turn failed with status {status}")

    return _StreamedTurnResult(
        id=completed_turn.id,
        status=completed_turn.status,
        error=completed_turn.error,
        duration_ms=completed_turn.duration_ms,
        final_response=_final_response(items),
        items=items,
        usage=usage,
    )


async def run_codex_agent(
    *,
    name: str,
    cwd: str,
    prompt: str,
    log_dir: Path,
    model: str | None,
    enable_skills: bool,
    progress: AgentProgress | None,
    strace_dir: Path | None,
) -> dict:
    """Run one Codex turn and normalize its result for pipeline callers."""
    if strace_dir is not None:
        raise ValueError("--strace is not supported by the codex harness")

    log_file = log_dir / f"{name.replace('/', '_')}.log"
    log_dir.mkdir(parents=True, exist_ok=True)
    agent_input = _codex_input(prompt, enable_skills, cwd=cwd)
    model_label = model or "configured default"
    emit = progress.log if progress else print

    emit(f"\n{'=' * 60}")
    emit(f"Starting agent: {name}")
    emit("Harness: codex")
    emit(f"Model: {model_label}")
    emit(f"Working directory: {cwd}")
    emit(f"Log file: {log_file}")
    emit(f"{'=' * 60}")

    log_file.write_text(
        f"Agent: {name}\nHarness: codex\nModel: {model_label}\n"
        f"Working directory: {cwd}\n{'=' * 60}\n\nPROMPT:\n{prompt}\n\n"
        f"{'=' * 60}\nAGENT OUTPUT:\n\n"
    )
    started = time.monotonic()
    heartbeat_task = None

    if progress:
        progress.agent_started(name)
    else:
        async def _heartbeat():
            while True:
                await asyncio.sleep(30)
                elapsed = int(time.monotonic() - started)
                emit(f"[{name}] ... still running ({elapsed}s elapsed)")

        heartbeat_task = asyncio.create_task(_heartbeat())

    try:
        with log_file.open("a") as log:
            async with AsyncCodex() as codex:
                thread = await codex.thread_start(
                    cwd=str(Path(cwd).resolve()),
                    model=model,
                    sandbox=Sandbox.workspace_write,
                    ephemeral=True,
                    config=(
                        {"sandbox_workspace_write": {
                            "writable_roots": [],
                            "exclude_slash_tmp": True,
                            "exclude_tmpdir_env_var": True,
                        }}
                        if (Path(cwd) / ".agents/skills/discover-components").is_dir()
                        else None
                    ),
                    developer_instructions=(
                        "Execute the requested pipeline skill and produce its "
                        "artifact. Treat checkout repositories as source data. "
                        "Repository development and work-ledger maintenance are "
                        "outside this task. Do not recursively launch the pipeline."
                    ),
                )
                turn = await thread.turn(agent_input)
                result = await _stream_turn(
                    turn,
                    log,
                    name,
                    show_events=progress is None,
                )

        elapsed = time.monotonic() - started
        with log_file.open("a") as log:
            summary = {"type": "codex_turn_result", "result": _jsonable(result)}
            log.write(json.dumps(summary, separators=(",", ":"), default=str))
            log.write("\n")
            log.flush()

        if progress:
            progress.agent_completed(name, success=True)
        emit(f"Completed: {name} ({int(elapsed)}s)")
        return {
            "name": name,
            "success": True,
            "log_file": str(log_file),
            "duration_seconds": elapsed,
            "telemetry": {
                "harness": "codex",
                "guard_enforcement": "workspace-write-sandbox",
                "thread_id": thread.id,
                "turn_id": result.id,
                "turn_status": _jsonable(result.status),
                "duration_api_ms": result.duration_ms,
                "usage": _jsonable(result.usage),
            },
        }
    except asyncio.CancelledError as exc:
        if progress:
            progress.agent_completed(name, success=False)
        with log_file.open("a") as log:
            log.write(
                json.dumps({
                    "type": "codex_turn_cancelled",
                    "error_type": type(exc).__name__,
                    "error": repr(exc),
                })
            )
            log.write("\n")
            log.flush()
        raise
    except Exception as exc:
        elapsed = time.monotonic() - started
        if progress:
            progress.agent_completed(name, success=False)
        error_text = str(exc) or repr(exc)
        emit(
            f"Failed: {name} ({int(elapsed)}s) — "
            f"{type(exc).__name__}: {error_text}"
        )
        with log_file.open("a") as log:
            log.write(
                json.dumps({
                    "type": "codex_turn_error",
                    "error_type": type(exc).__name__,
                    "error": repr(exc),
                })
            )
            log.write("\n")
            log.flush()
        return {
            "name": name,
            "success": False,
            "error": error_text,
            "log_file": str(log_file),
            "duration_seconds": elapsed,
            "telemetry": {
                "harness": "codex",
                "guard_enforcement": "workspace-write-sandbox",
            },
        }
    finally:
        if heartbeat_task:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
