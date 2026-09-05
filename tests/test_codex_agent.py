import asyncio
import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from openai_codex import SkillInput, TextInput
from openai_codex.generated.v2_all import TurnStatus

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib import agent_runner, codex_agent  # noqa: E402
from lib.architecture_surface_coverage import (  # noqa: E402
    build_surface_inventory,
    validate_surface_coverage,
)
from lib.phases.architecture import (  # noqa: E402
    _observed_read_records_from_telemetry,
)


def _event(method, payload):
    return SimpleNamespace(method=method, payload=payload)


def test_source_read_telemetry_resolves_checkout_aliases_and_bounds(tmp_path):
    checkout = tmp_path / "repo"
    checkout.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(checkout, target_is_directory=True)

    def command(identifier, path, text, exit_code=0):
        return {
            "type": "commandExecution", "id": identifier,
            "cwd": str(alias), "exit_code": exit_code,
            "command_actions": [{"type": "read", "path": path, "command": text}],
        }

    bounded = command("one", "main.go", "sed -n '90,210p' main.go")
    telemetry = codex_agent._source_read_telemetry([
        bounded, bounded,
        command("two", str(checkout / "main.go"), "cat main.go"),
        command("three", "../skill.md", "cat ../skill.md"),
        command("four", "failed.go", "cat failed.go", exit_code=1),
        {"type": "agentMessage", "text": "I read other.go"},
    ], checkout)
    assert telemetry["source_files_read"] == ["main.go"]
    assert telemetry["source_file_count"] == 1
    assert telemetry["source_read_operations"] == 2
    assert telemetry["source_read_ranges"] == [
        {"path": "main.go", "offset": 90, "limit": 121},
        {"path": "main.go", "offset": None, "limit": None},
    ]
    unscoped = codex_agent._source_read_telemetry([bounded], None)
    assert unscoped["source_files_read"] == []
    json.dumps(telemetry)


def test_unparsed_codex_read_range_cannot_verify_distant_evidence(tmp_path):
    checkout = tmp_path / "repo"
    checkout.mkdir()
    source = checkout / "cmd/main.go"
    source.parent.mkdir()
    source.write_text("\n".join(f"line {line}" for line in range(1, 521)))
    telemetry = codex_agent._source_read_telemetry(
        [
            {
                "type": "commandExecution",
                "id": "head-read",
                "cwd": str(checkout),
                "exit_code": 0,
                "command_actions": [
                    {
                        "type": "read",
                        "path": "cmd/main.go",
                        "command": "head -20 cmd/main.go",
                    }
                ],
            }
        ],
        checkout,
    )
    observed = _observed_read_records_from_telemetry(telemetry)
    assert telemetry["source_file_count"] == 1
    assert telemetry["source_read_operations"] == 1
    assert telemetry["source_read_ranges"] == [
        {"path": "cmd/main.go", "offset": None, "limit": None}
    ]
    assert observed == [
        {
            "path": "cmd/main.go",
            "line_range": "unknown",
            "outcome": "observed-by-harness",
        }
    ]

    inventory = build_surface_inventory(
        {
            "entrypoints": [
                {
                    "name": "manager",
                    "type": "Go controller-runtime operator",
                    "source": "cmd/main.go:10",
                }
            ]
        },
        component="example",
    )
    inventory["surfaces"] = [
        surface
        for surface in inventory["surfaces"]
        if surface["id"] == "authentication.metrics-enforcement"
    ]
    inventory["surfaces"][0]["candidate_locations"] = [
        {"path": "cmd/main.go", "line_range": "480-500", "origin": "analyzer"}
    ]
    sidecar = copy.deepcopy(inventory)
    sidecar["surfaces"][0].update(
        {
            "disposition": "documented",
            "evidence_status": "available",
            "claim_support": "supported",
            "evidence": [
                {"kind": "source-read", "reference": "cmd/main.go:480-500"}
            ],
            "document_reference": {
                "kind": "section",
                "section": "Architectural Analysis",
                "fact_identity": "conditional metrics authentication",
            },
        }
    )
    document = tmp_path / "component.md"
    document.write_text(
        "# Component: example\n\n## Architectural Analysis\n\n"
        "conditional metrics authentication\n"
    )

    report = validate_surface_coverage(
        inventory=inventory,
        sidecar=sidecar,
        promoted_document=document,
        observed_reads=observed,
        source_root=checkout,
    )

    assert report["structural_valid"] is False
    assert report["summary"]["documented"] == 0
    assert report["summary"]["unresolved"] == 1
    assert {item["classification"] for item in report["validator_findings"]} == {
        "inspection_gap",
        "unverifiable_coverage_claim",
    }


@pytest.mark.asyncio
async def test_reporting_failure_is_terminal_and_retains_telemetry(
    tmp_path, monkeypatch,
):
    async def run(*args, **kwargs):
        return {"success": True, "telemetry": {"source_files_read": ["main.go"]}}

    async def report(*args):
        raise TypeError("report serialization failed")

    monkeypatch.setattr(agent_runner, "run_agent", run)
    results = await agent_runner.run_agents_concurrently(
        [{"name": "component", "cwd": str(tmp_path), "prompt": "test"}],
        tmp_path, model=None, max_concurrent=1, on_result=report,
    )
    assert results[0]["success"] is False
    assert results[0]["_postprocessed"] is True
    assert results[0]["telemetry"]["source_files_read"] == ["main.go"]
    assert "post-processing failed" in results[0]["error"]


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
    inventory = tmp_path / "SURFACE_INVENTORY.json"
    coverage = tmp_path / "SURFACE_COVERAGE.json"
    inventory.write_text("{}\n")

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
        checkout_path=tmp_path / "checkout",
        input_paths=(inventory,),
        output_paths=(coverage,),
    )

    assert result["success"] is True
    assert captured["model"] is None
    assert captured["enable_skills"] is True
    assert captured["checkout_path"] == tmp_path / "checkout"
    assert captured["input_paths"] == (inventory,)
    assert captured["output_paths"] == (coverage,)


@pytest.mark.asyncio
async def test_codex_agent_uses_workspace_sandbox_and_normalizes_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    captured = {}

    class FakeTurn:
        id = "turn-1"

        async def stream(self):
            yield _event("item/completed", SimpleNamespace(
                turn_id=self.id,
                item={
                    "type": "commandExecution", "id": "read-1",
                    "cwd": str(tmp_path), "exit_code": 0,
                    "command_actions": [{
                        "type": "read", "path": "main.go",
                        "command": "sed -n '1,20p' main.go",
                    }],
                },
            ))
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
                        status=TurnStatus.completed,
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
        checkout_path=tmp_path,
    )

    assert result["success"] is True
    assert result["telemetry"]["harness"] == "codex"
    assert result["telemetry"]["turn_status"] == "completed"
    assert result["telemetry"]["source_files_read"] == ["main.go"]
    assert result["telemetry"]["source_read_observation"] == (
        "successful-sdk-read-actions"
    )
    json.dumps(result)  # Reports serialize without a permissive default=str.
    assert captured["thread_start"]["model"] is None
    assert captured["thread_start"]["ephemeral"] is True
    assert captured["thread_start"]["sandbox"].value == "workspace-write"
    assert isinstance(captured["input"][0], SkillInput)
    assert "turn-1" in (tmp_path / "logs" / "discovery.log").read_text()


@pytest.mark.asyncio
async def test_codex_restores_mutated_planning_input_and_keeps_sidecar_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    inventory = tmp_path / "SURFACE_INVENTORY.json"
    coverage = tmp_path / "SURFACE_COVERAGE.json"
    original = '{"inventory_id":"trusted"}\n'
    inventory.write_text(original)

    class FakeTurn:
        id = "turn-integrity"

        async def stream(self):
            yield SimpleNamespace(
                method="turn/completed",
                payload=SimpleNamespace(
                    turn=SimpleNamespace(
                        id=self.id,
                        status=TurnStatus.completed,
                        error=None,
                        duration_ms=1,
                    )
                ),
            )

    class FakeThread:
        id = "thread-integrity"

        async def turn(self, _agent_input):
            inventory.write_text('{"inventory_id":"mutated"}\n')
            coverage.write_text('{"surfaces":[]}\n')
            return FakeTurn()

    class FakeCodex:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        async def thread_start(self, **_kwargs):
            return FakeThread()

    monkeypatch.setattr(codex_agent, "AsyncCodex", FakeCodex)

    result = await codex_agent.run_codex_agent(
        name="integrity",
        cwd=str(tmp_path),
        prompt="write coverage",
        log_dir=tmp_path / "logs",
        model=None,
        enable_skills=False,
        progress=None,
        strace_dir=None,
        checkout_path=tmp_path,
        input_paths=(inventory,),
        output_paths=(coverage,),
    )

    assert result["success"] is False
    assert "mutated immutable planning input" in result["error"]
    assert result["telemetry"]["immutable_input_check"] == "failed-restored"
    assert result["telemetry"]["mutated_input_paths"] == [str(inventory)]
    assert inventory.read_text() == original
    assert json.loads(coverage.read_text()) == {"surfaces": []}


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
