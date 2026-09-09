# Structured publication linter cannot import the repository library

Status: open — P4 development failure observed; independent acceptance pending.
Requirement: SC-21, architecture lint integration.

During the P4 implementation, `make lint-architecture-docs` failed when the
standalone script imported `lib.structured_component_publication`:
`ModuleNotFoundError: No module named 'lib'`. Running a script by path puts
`scripts/` on Python's import path, so the repository library must be available
through the supported direct entry point as well as tests/imported execution.

Evidence: failed command and traceback retained in
`logs/structured-component-assembly/20260908-publication/worker/stdout.jsonl`.
The implementer is addressing this within P4. Acceptance requires running the
actual Make target/direct script successfully and preserving invalid-publication
rejection; close only after the P4 independent review accepts the repair.

## Fixed — P4 independently accepted 2026-09-09 UTC

Fable/high sessionb036fa12-9fc3-444a-ab72-fcc15280a655 returnedP4 PASS,
confirming this bug's acceptance criteria on555verifiedsourcefiles. Independent
fullPython1320pass10skip, readonlyCLI/treeidentity andactualGit tests pass;
cycle1query/consumer/reuseevidence retainedbyhash. [Review report](../../../logs/structured-component-assembly/20260909-publication-repair/review-report.md).
Offline implementation acceptance only; liveadoption separate.
