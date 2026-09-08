# Task: Checkpoint Surface Work and Restore Validation

Status: complete. Checkpoint committed as `39209078`; validation baseline
restored on 2026-09-05. See the
[plan](../../plans/architecture-surface-coverage.md), remaining-work steps 0
and 2.

Before more implementation, inventory and isolate completed changes from user
edits and generated outputs. Record a recoverable checkpoint and obtain commit
scope approval; do not bulk-stage the dirty worktree.

After the FIPS applicability fix, investigate the reported 12 pytest collection
errors from absent legacy benchmark trees and two Ruff findings in
`tests/test_component_output_naming.py`. Restore required inputs or document
explicit retirement of obsolete dependencies; do not blanket-skip tests.

Acceptance: reviewed checkpoint scope and separately recorded baseline repairs;
full pytest/Ruff and preservation verification with exact commands/results.
Keep unavailable external inputs explicit rather than claiming full validation.

## Checkpoint progress

- Recorded branch `regen/praxis-repos` at base HEAD
  `28728163dde09c1007e0c2cb6d9e794cd3c06539`.
- Classified 25 tracked modifications into 18 surface-only and seven mixed
  paths. Classified 2,028 untracked paths into 48 surface files, two separate
  Codex telemetry ledger files, one unknown script, and 1,977 generated
  architecture files.
- Created ignored recovery patches, archives, exact path manifests, and
  checksums under
  `tmp/checkpoints/architecture-surface-coverage-20260905/`.
- Recorded the proposed 25-tracked-plus-50-untracked commit scope in
  [the checkpoint note](../../notes/architecture-surface-checkpoint.md). Before
  approval, no file was staged or committed.
- The user approved the exact scope. Staged and verified all 75 approved paths;
  `TEST.sh`, both generated architecture trees, and the ignored checkpoint are
  absent from the index.
- Pre-commit validation passed: 248 preservation tests with four skips, 96
  focused feature tests, all Go module tests, Go lint, scoped Ruff, staged diff
  checks, and byte reproduction of both durable reports.
- A broad pytest collection attempt reconfirmed the baseline issue: after three
  known benchmark-dependent modules were excluded, nine additional modules
  still failed collection from the same absent `benchmark/analyzer-assisted-v1`
  and `benchmark/consumer-v1` trees. Baseline restoration remains queued after
  the FIPS applicability fix.
- At this checkpoint, the FIPS implementation and local verification were
  complete, while its independent review had not yet run. The later review is
  complete in the linked FIPS task, and the validation-baseline investigation
  below also completed.

## Validation baseline repair

- Confirmed commit `f8a6f6ff` intentionally deleted
  `benchmark/analyzer-assisted-v1` and `benchmark/consumer-v1`. Removed 13 test
  modules and two launchers whose only subject was that deleted harness; no test
  was skipped to conceal the dependency.
- Preserved active contracts by moving context-metrics and failure-proposal
  schemas to `schemas/`, and updated their libraries and tests. Removed the
  deleted benchmark from the generic Claude image build and entry point.
- Updated surviving tests to the current partial-route, soft-budget,
  non-shell-sourced `.env`, moved platform-template, and exact output-fixture
  contracts. Fixed the two reported Ruff findings.
- Recorded the retirement rationale in
  [ADR-0018](../../decisions/ADR-0018-retire-legacy-benchmark-harness.md).
- Full verification: `./.venv/bin/pytest -q` passed 829 tests with nine skips;
  `./.venv/bin/ruff check .` passed; `make test` passed 248 Python preservation
  tests with four skips plus all `arch-query`, `arch-analyzer`, and `arch-doc`
  tests; Go lint/vet passed; 31 overlays, 18 platforms, and 901 architecture
  documents passed their lint targets. `git diff --check` passed and no tracked
  generated architecture file changed.
