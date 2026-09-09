# Bug: Codex quota classification misses SDK-supported error formats

Status: open, blocking F-P3-9 / SC-10. Found independently 2026-09-08 in the
user-authorized additional P3 review. The original F-P3-8 example is fixed, but
its broader stop-on-quota requirement remains incomplete.

The installed SDK's `_is_server_overloaded` examines several forms of RPC
`error.data`: a plain string, `errorInfo` as well as `codexErrorInfo` and
`codex_error_info`, and code values inside dictionaries under those keys.
Our classifiers miss `errorInfo`, bare-string data, and code values under
otherwise unrecognized keys inside an error-info dictionary. The reviewer
reproduced all three through the real component loop: the quota error was saved,
but a second component started and made a model call.

Evidence: [additional review §4](../../../logs/structured-component-assembly/20260908-rpc-quota-repair/review-report.md),
`review-evidence/probe_classifier_shapes.py/.out`, `test_seam_probes.py/.out`,
and `seam-probe-results.jsonl`. All model transports were blocked; errors were
local stubs. Reviewer Fable/high session02cfe002-63e0-4cbe-8cf1-707e84e46530.

Acceptance: both Codex and synthesis classification recognize exact known quota
codes in all the SDK-supported forms, including startup and producing calls.
Real-loop tests prove no second component starts for each form. Preserve ordinary
error controls and avoid interpreting arbitrary prose as quota. Retain the
original fixed notification/RPC cases and safe structured diagnostics.
The authorized extra cycle is exhausted; further repair/review needs direction.

## Fixed — independently accepted 2026-09-08

Fable/high session `a6ccbff3-0617-487d-9223-2549189ce1f4` returned P3 PASS,
including this finding. [Review evidence](../../../logs/structured-component-assembly/20260908-quota-shapes/review-report.md).
Full Python1274 pass/10skip, focused283 pass, independent boundary probes27 pass;
all547 reviewed source hashes verified unchanged. Offline tests only.
