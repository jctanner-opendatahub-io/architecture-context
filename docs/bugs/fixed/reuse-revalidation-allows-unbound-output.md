# Reuse revalidation allows unbound output

Status: fixed. Found by independent P2 review cycle 1 on 2026-09-07.

Severity/requirements: Medium; SC-15.

F3: all-true callback booleans plus an empty facts array can return reused output unrelated to accepted predecessor. Current tests use hardcoded validation booleans. Require predecessor/target consistency across explicitly permitted deterministic refresh and tests whose checks run actual accepted Go validation, including invalid output.

Evidence: `logs/structured-component-assembly/20260907-resume/p2-review-report.md`,
reviewer session `7d385b28-9ec6-4a62-9488-3e49a02fe58e`, Fable 5.1/high.
No phase-two acceptance. Bounded Python repair and fresh re-review required.

Independent acceptance: Fable cycle 3 PASS, session b7b8d76a-e126-4874-be29-36c2433fe4eb. Evidence: `logs/structured-component-assembly/20260907-resume/p2-review3-report.md`. All prior evidence and limitations retained. P3 producer/publication integration remains separate.
