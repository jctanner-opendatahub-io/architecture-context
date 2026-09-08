# Bug: Structured Inline Content Allows Control Characters

Status: open, non-blocking phase-one follow-up.

Fable cycle-three probes found VT, FF, ESC, DEL, NEL, U+2028 and U+2029 accepted
and rendered in paragraph/list/table-cell/uncertainty text. These are not
CommonMark line endings, so the review found no structural Markdown bypass,
but raw ESC can reach consumer output. Evidence: kickoff `p1-review3-report.md`.
Address the inline control policy when extending synthesis sections in phase 3,
with regression tests and renewed review of the affected rendering guarantee.

Independent acceptance: P3 cycle1 resumed review, session39888686-67c7-48fe-b894-621e7a28bad8, criteria met. See logs/structured-component-assembly/20260907-resume/p3-review1-report.md. Other P3 blockers remain open.
