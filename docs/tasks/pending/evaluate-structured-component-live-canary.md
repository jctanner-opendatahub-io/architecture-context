# Task: Evaluate the structured component route with a bounded live canary

Status: pending — requires separate execution, model and spending authorization.
Implementation prerequisite: [completed structured assembly](../done/implement-structured-component-assembly.md).

The implementation and offline gates passed independent review. Actual live
quality, calls, tokens, latency and cost remain unmeasured under SC-24, and
default adoption remains HOLD. This task does not authorize a model call.

Use the prepared [future live packet](../../notes/structured-component-future-live-canary.md)
and [completion record](../../notes/structured-component-assembly-completion.md).
Before execution, freeze the actual source versions, repaired analyzer build,
selected model/harness/settings, inputs and output destination. Confirm the
packet's bounded candidates and call/time/cost limits under user authorization.
Do not present historical estimates as measured savings.

Acceptance:

- Run only the authorized bounded sample and preserve raw responses, failures,
  source identities, costs and timing with no model fallback on rate limits.
- Measure facts preserved, unsupported claims, unresolved questions, repairs,
  schema compliance, follow-ups and actual runtime costs.
- Keep candidate fact similarity separate from fully verified reuse; record
  actual producing and dependency observations for any new reusable snapshots.
- Obtain independent review of the measured results and an explicit adopt/HOLD
  decision. Default changes, enforcement and worker enablement are separate
  decisions; preserve rollback and existing warning-only policy.

Stop on actual rate limits and resume only with the same authorized model and
settings after capacity is restored. Preserve rejected results and do not
retroactively accept earlier canaries. No live run has been started for this task.
