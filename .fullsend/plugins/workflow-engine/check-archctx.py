#!/usr/bin/env python3
"""Rung-1 check for the arch-context workflow (port plan P3, ladder rung 1).

Runs the arch-context workflow N times under plain local pi (no sandbox,
no fullsend) with scripted test-child children and asserts:

Per run:
  - pi exits 0 and the --mode json stream parses;
  - the deterministic conversation: one toolUse assistant message with a
    single `workflow` tool call (command run-arch-context), a successful
    tool_execution_end, a final stop assistant message, agent_end
    willRetry=false, agent_settled;
  - every assistant message reports zero usage (no parent inference);
  - usage.jsonl holds one record per component, in item order;
  - artifact.json is complete; results/ holds one file per component;
    PLATFORM.md is rendered.

Across runs:
  - normalized event streams are byte-identical (timestamps, durations,
    session ids and the per-run scratch directory masked). Ephemeral
    tool_execution_update progress events are excluded: they forward
    child text deltas as they stream, so their interleaving under
    concurrency is arrival-ordered by nature. The settled stream —
    message contents, tool result, final message — stays in scope.

Negative suite (failures must be loud, in-stream):
  - stages without generate -> journal-replay (P5) error;
  - unknown component requested -> unknown-component error;
  - malformed child output -> invalid-JSON error (host parse);
  - wrong-key child output -> reality-check error (assertComplete).

Usage:
  python3 check-archctx.py --runs 3 --out ./check-runs
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # .fullsend/plugins/workflow-engine
REPO_ROOT = HERE.parents[2]                     # the architecture-context fork root
DEFAULT_INPUT_FILE = REPO_ROOT / "architecture" / "breadboard" / "components.json"
DEFAULT_WORKFLOW_INPUT = '{"platform":"breadboard","stages":["generate","collect","platform"],"concurrency":2}'
PROMPT = "Run the architecture context workflow"
DROP_KEYS = {"timestamp", "durationMs"}


def normalize(value):
	if isinstance(value, dict):
		out = {}
		for k, v in value.items():
			if k in DROP_KEYS:
				continue
			if k == "id" and isinstance(v, str) and len(v) == 36 and v.count("-") == 4:
				out[k] = "<uuid>"
			else:
				out[k] = normalize(v)
		return out
	if isinstance(value, list):
		return [normalize(v) for v in value]
	return value


def run_once(pi: str, ext: Path, repo_root: Path, run_dir: Path, workflow_input: str,
             input_file: Path | None, prompt: str = PROMPT) -> dict:
	run_dir.mkdir(parents=True, exist_ok=False)
	home = run_dir / "home"
	home.mkdir()
	session = run_dir / "session"
	argv = [
		pi, "--print", "--mode", "json", "--no-approve", "--no-extensions",
		"--no-prompt-templates", "--no-themes", "--session-dir", str(session),
		"-e", str(ext), "--model", "workflow-engine/v1", "--tools", "workflow",
		prompt,
	]
	env = dict(os.environ)
	env["HOME"] = str(home)
	env["WORKFLOW_COMMAND"] = "run-arch-context"
	env["WORKFLOW_INPUT"] = workflow_input
	if input_file is not None:
		env["WORKFLOW_INPUT_FILE"] = str(input_file)
	proc = subprocess.run(argv, cwd=str(repo_root), env=env, capture_output=True,
	                      text=True, timeout=600)
	(run_dir / "stdout.jsonl").write_text(proc.stdout)
	(run_dir / "stderr.txt").write_text(proc.stderr)
	events = []
	for line in proc.stdout.splitlines():
		line = line.strip()
		if not line.startswith("{"):
			continue
		try:
			events.append(json.loads(line))
		except ValueError:
			pass
	return {"returncode": proc.returncode, "events": events, "run_dir": run_dir}


def latest_run_dir(repo_root: Path) -> Path:
	"""Newest workflow-runs/* by mtime (run dirs are hash-named)."""
	candidates = sorted((repo_root / "workflow-runs").glob("*/usage.jsonl"),
	                    key=lambda p: p.stat().st_mtime)
	if not candidates:
		raise AssertionError("no workflow-runs/*/usage.jsonl found")
	return candidates[-1].parent


def tool_result_text(events) -> str:
	for e in events:
		if e.get("type") == "tool_execution_end" and e.get("toolName") == "workflow":
			result = e.get("result") or {}
			for block in result.get("content", []):
				if block.get("type") == "text":
					return block.get("text", "")
	return ""


def check_run(result: dict, expected_keys: list[str], platform: str,
              expect_child_model: str | None, repo_root: Path) -> list[str]:
	errors: list[str] = []
	run_dir: Path = result["run_dir"]
	events = result["events"]

	if result["returncode"] != 0:
		errors.append(f"exit code {result['returncode']}")
		return errors

	kinds = [e.get("type") for e in events]
	if kinds[:1] != ["session"]:
		errors.append(f"first event is {kinds[:1]}, expected session header")

	# Tool-call turn.
	tool_msgs = [
		e for e in events
		if e.get("type") == "message_end" and e.get("message", {}).get("role") == "assistant"
		and e["message"].get("stopReason") == "toolUse"
	]
	if len(tool_msgs) != 1:
		errors.append(f"expected exactly one toolUse assistant message, got {len(tool_msgs)}")
	else:
		calls = [b for b in tool_msgs[0]["message"].get("content", []) if b.get("type") == "toolCall"]
		if len(calls) != 1 or calls[0].get("name") != "workflow":
			errors.append(f"expected one workflow toolCall, got {calls}")
		else:
			args = calls[0].get("arguments", {})
			if args.get("command") != "run-arch-context":
				errors.append(f"tool call command {args.get('command')!r} != run-arch-context")
			if args.get("input", {}).get("platform") != platform:
				errors.append(f"tool call platform {args.get('input', {}).get('platform')!r} != {platform!r}")

	tool_ends = [e for e in events if e.get("type") == "tool_execution_end" and e.get("toolName") == "workflow"]
	if len(tool_ends) != 1 or tool_ends[0].get("isError"):
		errors.append(f"expected one successful workflow tool_execution_end, got {tool_ends}")
		return errors

	# Final turn.
	final_msgs = [
		e for e in events
		if e.get("type") == "message_end" and e.get("message", {}).get("role") == "assistant"
		and e["message"].get("stopReason") == "stop"
	]
	if len(final_msgs) != 1:
		errors.append(f"expected exactly one final stop assistant message, got {len(final_msgs)}")
	else:
		text = "".join(b.get("text", "") for b in final_msgs[0]["message"].get("content", []) if b.get("type") == "text")
		want = f"workflow complete: {len(expected_keys)}/{len(expected_keys)} components analyzed"
		if want not in text:
			errors.append(f"final message missing {want!r}: {text[:200]!r}")

	if not any(e.get("type") == "agent_end" and e.get("willRetry") is False for e in events):
		errors.append("no agent_end with willRetry=false")
	if not any(e.get("type") == "agent_settled" for e in events):
		errors.append("no agent_settled")

	# Zero parent usage on every assistant message.
	for e in events:
		msg = e.get("message", {})
		if e.get("type") in ("message_end", "message_update") and msg.get("role") == "assistant":
			u = msg.get("usage") or e.get("usage") or {}
			if any(u.get(k) for k in ("input", "output", "cacheRead", "cacheWrite")):
				errors.append(f"non-zero parent usage: {u}")
				break

	# Workflow run dir: usage records, artifact, results, PLATFORM.md.
	try:
		wf_dir = latest_run_dir(repo_root)
	except AssertionError as err:
		errors.append(str(err))
		return errors

	usage_file = wf_dir / "usage.jsonl"
	records = [json.loads(l) for l in usage_file.read_text().splitlines() if l.strip()]
	if len(records) != len(expected_keys):
		errors.append(f"usage.jsonl has {len(records)} records, expected {len(expected_keys)}")
	for i, rec in enumerate(records):
		if rec.get("seq") != i + 1:
			errors.append(f"usage record {i} seq={rec.get('seq')}")
		if "usage" not in rec or "model" not in rec:
			errors.append(f"usage record {i} missing model/usage: {rec}")
		if expect_child_model and rec.get("model") != expect_child_model:
			errors.append(f"usage record {i} model {rec.get('model')!r} != {expect_child_model!r}")

	artifact_file = wf_dir / "artifact.json"
	if not artifact_file.exists():
		errors.append(f"no artifact.json in {wf_dir}")
		return errors
	art = json.loads(artifact_file.read_text())
	if not art.get("complete") or art.get("analyzed") != len(expected_keys) or art.get("expected") != len(expected_keys):
		errors.append(f"artifact not complete: {json.dumps(art)[:300]}")
	if sorted(art.get("components", [])) != sorted(expected_keys):
		errors.append(f"artifact components mismatch: {art.get('components')}")
	if len(art.get("results", [])) != len(expected_keys):
		errors.append(f"artifact has {len(art.get('results', []))} results, expected {len(expected_keys)}")

	results_files = sorted(p.name for p in (wf_dir / "results").glob("*.json"))
	if results_files != sorted(f"{k}.json" for k in expected_keys):
		errors.append(f"results/ files mismatch: {results_files}")

	platform_doc = wf_dir / "PLATFORM.md"
	if not platform_doc.exists():
		errors.append(f"no PLATFORM.md in {wf_dir}")
	elif not platform_doc.read_text().startswith(f"# Platform Architecture — {platform}"):
		errors.append("PLATFORM.md has wrong title")

	# Published artifacts in the repo's architecture tree (pipeline
	# convention: <architectureDir>/<platform>/<component>.md + PLATFORM.md).
	arch_dir = repo_root / "architecture" / platform
	for key in expected_keys:
		comp_md = arch_dir / f"{key}.md"
		if not comp_md.exists():
			errors.append(f"no published {comp_md}")
		elif not comp_md.read_text().startswith(f"# {key}"):
			errors.append(f"published {comp_md} has wrong title")
	pub_platform = arch_dir / "PLATFORM.md"
	if not pub_platform.exists():
		errors.append(f"no published {pub_platform}")
	elif not pub_platform.read_text().startswith(f"# Platform Architecture — {platform}"):
		errors.append(f"published {pub_platform} has wrong title")

	return errors


def check_negative(result: dict, expect_substr: str) -> list[str]:
	"""A negative run: exit ok, but the workflow tool must fail loudly."""
	errors: list[str] = []
	if result["returncode"] != 0:
		errors.append(f"exit code {result['returncode']} (tool errors surface in-stream)")
		return errors
	ends = [e for e in result["events"]
	        if e.get("type") == "tool_execution_end" and e.get("toolName") == "workflow"]
	if len(ends) != 1 or not ends[0].get("isError"):
		errors.append("expected exactly one tool_execution_end with isError=true")
		return errors
	text = tool_result_text(result["events"])
	if expect_substr not in text:
		errors.append(f"failure text missing {expect_substr!r}: {text[:200]!r}")
	return errors


def main() -> int:
	parser = argparse.ArgumentParser()
	parser.add_argument("--pi", default="pi")
	parser.add_argument("--ext", type=Path, default=HERE)
	parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
	parser.add_argument("--runs", type=int, default=3)
	parser.add_argument("--out", type=Path, required=True)
	parser.add_argument("--input-file", type=Path, default=DEFAULT_INPUT_FILE)
	parser.add_argument("--workflow-input", default=DEFAULT_WORKFLOW_INPUT)
	parser.add_argument("--expect-child-model", default="test-child/echo")
	parser.add_argument("--skip-negative", action="store_true")
	args = parser.parse_args()

	repo_root = args.repo_root

	args.out.mkdir(parents=True, exist_ok=True)
	items = json.loads(args.input_file.read_text())
	expected_keys = [it["key"] for it in items]
	platform = json.loads(args.workflow_input).get("platform", "unknown")
	print(f"expecting {len(expected_keys)} components: {', '.join(expected_keys)}")

	failures = 0
	normalized_streams = []
	published = []
	for n in range(1, args.runs + 1):
		result = run_once(args.pi, args.ext, args.repo_root, args.out / f"run-{n}",
		                  args.workflow_input, args.input_file)
		errors = check_run(result, expected_keys, platform, args.expect_child_model, repo_root)
		# Mask the per-run scratch dir and the repo root so the comparison
		# isolates engine determinism from run location.
		masks = [str(result["run_dir"].resolve()), str(args.repo_root.resolve())]
		normalized = []
		for e in result["events"]:
			if e.get("type") == "tool_execution_update":
				continue  # ephemeral progress; arrival-ordered, not settled
			s = json.dumps(normalize(e), sort_keys=True)
			for m in masks:
				s = s.replace(m, "<masked>")
			normalized.append(s)
		normalized_streams.append(normalized)
		pub_dir = args.repo_root / "architecture" / platform
		pub_names = [f"{k}.md" for k in expected_keys] + ["PLATFORM.md"]
		published.append({
			name: ((pub_dir / name).read_bytes() if (pub_dir / name).exists() else None)
			for name in pub_names
		})
		status = "PASS" if not errors else "FAIL"
		print(f"run {n}: {status} ({len(result['events'])} events, exit {result['returncode']})")
		for err in errors:
			print(f"  - {err}")
		failures += bool(errors)

	# Published-artifact determinism: the published markdown must be
	# byte-identical across runs (deterministic render of validated
	# results).
	if any(content is None for run in published for content in run.values()):
		failures += 1
		print("published artifacts: FAIL — missing published files")
	elif len({json.dumps({k: (v.hex() if v else None) for k, v in run.items()}) for run in published}) != 1:
		failures += 1
		print("published artifacts: FAIL — published markdown differs across runs")
	else:
		n = len(published[0])
		print(f"published artifacts: PASS — {n} files byte-identical across {args.runs} runs")

	if len({json.dumps(s) for s in normalized_streams}) != 1:
		failures += 1
		print("determinism: FAIL — normalized event streams differ across runs")
		import hashlib
		for n, s in enumerate(normalized_streams, 1):
			print(f"  run {n}: {len(s)} events, sha256={hashlib.sha256(json.dumps(s).encode()).hexdigest()[:16]}")
	else:
		print(f"determinism: PASS — {args.runs}/{args.runs} normalized streams identical")

	if not args.skip_negative:
		negatives = [
			("stages-without-generate",
			 '{"platform":"breadboard","stages":["collect","platform"]}',
			 "journal replay"),
			("unknown-component",
			 '{"platform":"breadboard","components":["no-such-component"]}',
			 "unknown component"),
			("malformed-child-output",
			 '{"platform":"test","items":[{"key":"__malformed__","repoDir":"."}]}',
			 "output not valid JSON"),
			("wrong-key-child-output",
			 '{"platform":"test","items":[{"key":"__wrongkey__","repoDir":"."}]}',
			 "is about"),
		]
		for name, wf_input, expect in negatives:
			result = run_once(args.pi, args.ext, args.repo_root, args.out / f"neg-{name}",
			                  wf_input, args.input_file)
			errors = check_negative(result, expect)
			status = "PASS" if not errors else "FAIL"
			print(f"negative {name}: {status}")
			for err in errors:
				print(f"  - {err}")
			failures += bool(errors)

	print("RUNG1-CHECK:", "PASS" if failures == 0 else "FAIL")
	return 0 if failures == 0 else 1


if __name__ == "__main__":
	sys.exit(main())
