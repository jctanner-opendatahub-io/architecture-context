# Codex reuse observations ignore unclassified readers

Status: fixed. Found by independent P2 review cycle 1 on 2026-09-07.

Severity/requirements: High; SC-14/SC-25.

F1: fixed reader-verb allowlist silently ignores ls -R, git show, nl, wc/stat/kustomize and raw bash wrappers. Reviewer reproduced complete telemetry and a reuse hit despite unrecorded discovery. Unknown commands must default to incomplete unless positively proven fully observed or non-reading.

Evidence: `logs/structured-component-assembly/20260907-resume/p2-review-report.md`,
reviewer session `7d385b28-9ec6-4a62-9488-3e49a02fe58e`, Fable 5.1/high.
No phase-two acceptance. Bounded Python repair and fresh re-review required.

Independent acceptance: Fable cycle 3 PASS, session b7b8d76a-e126-4874-be29-36c2433fe4eb. Evidence: `logs/structured-component-assembly/20260907-resume/p2-review3-report.md`. All prior evidence and limitations retained. P3 producer/publication integration remains separate.
