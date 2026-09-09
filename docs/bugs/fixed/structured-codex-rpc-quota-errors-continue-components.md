# Bug: Codex quota exceptions can allow later component calls

Status: open. Blocking P3 finding F-P3-8 from completed independent cycle3,
2026-09-08. Requirement SC-10 and the framework/user stop-on-rate rule.

The installed Codex SDK exposes some failures as `CodexRpcError` with structured
`code`, `message`, and `data`. A quota code such as
`data.codexErrorInfo = usageLimitExceeded` is lost when the producing adapter
reduces the exception to an ordinary error message. The synthesis classifier
then treats it as a component failure and the component loop can continue.
This is distinct from the already-handled failed-turn notification shape.

The reviewer reproduced local SDK exception mapping and adapter classification
at producing `thread/start` and `turn/start`; source inspection establishes
continuation through the ordinary component-failure handler. Preflight
`thread/start` aborts before components but propagates the raw RPC exception
without the required rate-limit type or durable diagnostic.

## Evidence

[Cycle3 report, finding F-P3-8](../../../logs/structured-component-assembly/20260908-review-resume/review-report.md)
and `review-evidence/probe_preflight_quota.out` plus its script retain the
reproduction. Exact source manifest: same directory `inputs.json`, 547 files;
HEAD e0f6f367. Reviewer Fable/high session
50e748ed-9760-46e7-b8f2-b0c9fdbeb37b. These are simulated quota errors; no actual
rate limit occurred during this completed review.

## Acceptance

- Preserve and classify structured SDK RPC error code/data at config/read,
  thread/start, and turn/start, including the preflight route.
- Recognized quota refusals/HTTP429 propagate the existing RateLimitError and
  leave a durable diagnostic. Preserve useful structured error evidence without
  exposing credentials. Ordinary errors remain ordinary failures.
- Stubbed tests cover each hop and use the actual component loop to prove a
  second component/model call never starts after a quota refusal. Keep existing
  failed-turn quota behavior and the default offline SDK startup guard intact.
- Independently review the focused repair. P3 remains unaccepted until then;
  phase budget escalation is required before another cycle.

## Additional review outcome — 2026-09-08

Original F-P3-8 shape independently fixed; broader acceptance remains open due
[F-P3-9](structured-codex-quota-classifier-misses-sdk-error-shapes.md) and
[F-P3-10](structured-preflight-diagnostic-detail-unredacted.md).
Full1220Python tests pass, but new independent probes expose these gaps. See the
[completed review](../../../logs/structured-component-assembly/20260908-rpc-quota-repair/review-report.md).

## Fixed — independently accepted 2026-09-08

Fable/high session `a6ccbff3-0617-487d-9223-2549189ce1f4` returned P3 PASS,
including this finding. [Review evidence](../../../logs/structured-component-assembly/20260908-quota-shapes/review-report.md).
Full Python1274 pass/10skip, focused283 pass, independent boundary probes27 pass;
all547 reviewed source hashes verified unchanged. Offline tests only.
