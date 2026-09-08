# Claude reuse observations ignore unhandled tools

Status: fixed. Found by independent P2 review cycle 1 on 2026-09-07.

Severity/requirements: Medium; SC-14/SC-25.

F2: unrestricted pre-tool hook silently ignores NotebookRead, Task, LS, WebFetch and other unhandled tools. Reviewer reproduced complete empty observations. Unhandled permitted tools must mark observations incomplete; preserve restricted-route denial behavior.

Evidence: `logs/structured-component-assembly/20260907-resume/p2-review-report.md`,
reviewer session `7d385b28-9ec6-4a62-9488-3e49a02fe58e`, Fable 5.1/high.
No phase-two acceptance. Bounded Python repair and fresh re-review required.

Independent acceptance: Fable cycle 3 PASS, session b7b8d76a-e126-4874-be29-36c2433fe4eb. Evidence: `logs/structured-component-assembly/20260907-resume/p2-review3-report.md`. All prior evidence and limitations retained. P3 producer/publication integration remains separate.
