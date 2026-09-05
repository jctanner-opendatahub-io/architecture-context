# Architecture Synthesis Omits Behavioral Surfaces

## Status

Fixed 2026-09-05. Independent coverage-contract, behavioral-analyzer, and
offline-canary reviews passed. Coverage validation remains warning-only, and
worker adoption or broader enforcement still requires a separate rollout
decision.

Observed in the rhods-operator Codex run `20260905T032122Z` at source commit
`4ada791819c522a4cda54f9029ab3e4056ed31ed`.

The generated document passed validation but omitted conditional metrics
authentication already present in source tool output. It also omitted named
namespace-watch integrations that the analyzer represented only generically
and the agent did not inspect. Read justification and merge validity do not
establish behavioral completeness.

See the [coverage plan](../../plans/architecture-surface-coverage.md) for
evidence, regression cases, and remediation. The implementation now extracts
and validates both omitted surfaces and preserves the gateway/FIPS regressions.
The reviewed offline canary keeps its selection provisional because the
user-directed no-live-agent constraint prevents repeat, cost, latency, token,
and source-read comparisons.
