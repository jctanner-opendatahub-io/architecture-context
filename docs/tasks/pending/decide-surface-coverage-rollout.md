# Task: Decide Surface Coverage Rollout

Status: pending refreshed audit and independently reviewed live-canary evidence.

Follow step 5 of the [plan](../../plans/architecture-surface-coverage.md).
Record separate decisions for scoped enforcement and optional generation-worker
experiments, with acceptance thresholds, false-positive tolerance, scope, and
rollback. Keeping current defaults is a valid decision.

Acceptance: explicit operator-approved decisions supported by measured evidence;
no implicit enablement from implementation completion, restored model access,
or a green offline canary. Warning-only coverage and disabled workers remain
unchanged until separately authorized. Continue the pending JSON Patch work
after the checkpoint, or request reprioritization if evaluation is deferred.
