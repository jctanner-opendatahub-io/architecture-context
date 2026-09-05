import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from openai_codex import SkillInput, TextInput

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib import agent_runner, codex_agent  # noqa: E402


def _event(method, payload):
    return SimpleNamespace(method=method, payload=payload)


def test_codex_input_resolves_shared_discovery_skill():
    items = codex_agent._codex_input(
        "/discover-components --platform=rhoai-3.6-ea.2 --force",
        enable_skills=True,
    )

    assert isinstance(items, list)
    assert isinstance(items[0], SkillInput)
    assert items[0].name == "discover-components"
    assert items[0].path.endswith("/.claude/skills/discover-components/SKILL.md")
    assert isinstance(items[1], TextInput)
    assert "--platform=rhoai-3.6-ea.2" in items[1].text


def test_terminal_renderer_streams_messages_and_concise_commands(capsys):
    renderer = codex_agent._TerminalEventRenderer("discovery")
    renderer.render(_event(
        "item/agentMessage/delta",
        SimpleNamespace(item_id="message-1", delta="Checking "),
    ))
    renderer.render(_event(
        "item/agentMessage/delta",
        SimpleNamespace(item_id="message-1", delta="repositories."),
    ))
    renderer.render(_event(
        "item/completed",
        SimpleNamespace(item={
            "id": "message-1",
            "type": "agentMessage",
            "text": "Checking repositories.",
        }),
    ))
    renderer.render(_event(
        "item/started",
        SimpleNamespace(item={
            "type": "commandExecution",
            "command": "rg --files checkouts",
        }),
    ))
    renderer.render(_event(
        "item/commandExecution/outputDelta",
        SimpleNamespace(delta="large command output that stays in JSONL"),
    ))
    renderer.render(_event(
        "item/completed",
        SimpleNamespace(item={
            "type": "commandExecution",
            "status": "completed",
            "exit_code": 0,
            "duration_ms": 42,
        }),
    ))

    output = capsys.readouterr().out
    assert "[discovery] Checking repositories.\n" in output
    assert "[discovery] command: rg --files checkouts\n" in output
    assert "[discovery] command completed; exit=0; 42ms\n" in output
    assert "large command output" not in output


@pytest.mark.asyncio
async def test_agent_runner_dispatches_to_codex_harness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    captured = {}

    async def fake_run_codex_agent(**kwargs):
        captured.update(kwargs)
        return {"name": kwargs["name"], "success": True}

    monkeypatch.setattr(codex_agent, "run_codex_agent", fake_run_codex_agent)

    result = await agent_runner.run_agent(
        "discovery",
        str(tmp_path),
        "/discover-components --platform=rhoai-3.6-ea.2",
        tmp_path,
        model=None,
        enable_skills=True,
        harness="codex",
    )

    assert result["success"] is True
    assert captured["model"] is None
    assert captured["enable_skills"] is True


@pytest.mark.asyncio
async def test_codex_agent_uses_workspace_sandbox_and_normalizes_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    captured = {}

    class FakeTurn:
        id = "turn-1"

        async def stream(self):
            yield SimpleNamespace(
                method="thread/tokenUsage/updated",
                payload=SimpleNamespace(
                    turn_id=self.id,
                    token_usage={"input_tokens": 10, "output_tokens": 20},
                ),
            )
            yield SimpleNamespace(
                method="turn/completed",
                payload=SimpleNamespace(
                    turn=SimpleNamespace(
                        id=self.id,
                        status="completed",
                        error=None,
                        duration_ms=123,
                    )
                ),
            )

    class FakeThread:
        id = "thread-1"

        async def turn(self, agent_input):
            captured["input"] = agent_input
            return FakeTurn()

    class FakeCodex:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        async def thread_start(self, **kwargs):
            captured["thread_start"] = kwargs
            return FakeThread()

    monkeypatch.setattr(codex_agent, "AsyncCodex", FakeCodex)

    result = await codex_agent.run_codex_agent(
        name="discovery",
        cwd=str(tmp_path),
        prompt="/discover-components --platform=rhoai-3.6-ea.2",
        log_dir=tmp_path / "logs",
        model=None,
        enable_skills=True,
        progress=None,
        strace_dir=None,
    )

    assert result["success"] is True
    assert result["telemetry"]["harness"] == "codex"
    assert captured["thread_start"]["model"] is None
    assert captured["thread_start"]["ephemeral"] is True
    assert captured["thread_start"]["sandbox"].value == "workspace-write"
    assert isinstance(captured["input"][0], SkillInput)
    assert "turn-1" in (tmp_path / "logs" / "discovery.log").read_text()


@pytest.mark.asyncio
async def test_codex_agent_flushes_events_before_turn_completion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    waiting = asyncio.Event()
    release = asyncio.Event()

    class FakeTurn:
        id = "turn-stream"

        async def stream(self):
            yield SimpleNamespace(
                method="item/started",
                payload={"turnId": self.id, "item": {"type": "command"}},
            )
            waiting.set()
            await release.wait()
            yield SimpleNamespace(
                method="turn/completed",
                payload=SimpleNamespace(
                    turn=SimpleNamespace(
                        id=self.id,
                        status="completed",
                        error=None,
                        duration_ms=1,
                    )
                ),
            )

    class FakeThread:
        id = "thread-stream"

        async def turn(self, _agent_input):
            return FakeTurn()

    class FakeCodex:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        async def thread_start(self, **_kwargs):
            return FakeThread()

    monkeypatch.setattr(codex_agent, "AsyncCodex", FakeCodex)

    run = asyncio.create_task(codex_agent.run_codex_agent(
        name="streaming",
        cwd=str(tmp_path),
        prompt="plain prompt",
        log_dir=tmp_path / "logs",
        model=None,
        enable_skills=False,
        progress=None,
        strace_dir=None,
    ))
    await waiting.wait()

    in_progress_log = (tmp_path / "logs" / "streaming.log").read_text()
    assert '"method":"item/started"' in in_progress_log

    release.set()
    result = await run
    assert result["success"] is True


@pytest.mark.asyncio
async def test_codex_agent_propagates_cancellation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    class FakeTurn:
        id = "turn-cancelled"

        async def stream(self):
            raise asyncio.CancelledError
            yield  # pragma: no cover

    class FakeThread:
        id = "thread-cancelled"

        async def turn(self, _agent_input):
            return FakeTurn()

    class FakeCodex:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        async def thread_start(self, **_kwargs):
            return FakeThread()

    monkeypatch.setattr(codex_agent, "AsyncCodex", FakeCodex)

    with pytest.raises(asyncio.CancelledError):
        await codex_agent.run_codex_agent(
            name="cancelled",
            cwd=str(tmp_path),
            prompt="plain prompt",
            log_dir=tmp_path / "logs",
            model=None,
            enable_skills=False,
            progress=None,
            strace_dir=None,
        )

    log = (tmp_path / "logs" / "cancelled.log").read_text()
    assert '"error_type": "CancelledError"' in log
