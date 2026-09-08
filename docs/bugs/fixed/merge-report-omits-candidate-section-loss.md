# Bug: Merge Report Omits Candidate Section Loss

## Status

Fixed and independently accepted 2026-09-06.

In Claude repetition 2 of the repeated `rhods-operator` live canary,
`candidate.md` contained a `### FIPS Compliance` section at lines 355-375, but
the promoted document did not. The final coverage validator detected the
omission. The merge report still recorded zero rejected and zero restored
changes and did not expose a prose-loss count.

The retained candidate, promoted document, merge report, and source review are
under
[`live-canary/runs/claude-repetition-2`](../../../evaluations/architecture-surface-coverage/live-canary/runs/claude-repetition-2/).
The candidate placed the subsection outside its valid parent section, so final
assembly was correct to reject it; the bug is the missing merge/promotion
diagnostic.

Expected behavior: final assembly should report candidate narrative sections
that are removed, relocated, or rejected, with enough identity for coverage
validation and canary accounting. It must continue protecting analyzer-owned
tables and document structure.

## Root cause

Arch-doc looked for configured synthesis H3 subsections only inside their
permitted parent. A configured subsection under any other H2 was therefore
invisible to assembly. The command also had no structured report channel, so
the merge runner could not retain an actionable reason for the discarded
candidate content.

## Resolution

Arch-doc now scans the candidate for every synthesis subsection configured in
its section manifest before assembly. A subsection outside its configured
parent produces `synthesis_subsection_parent_mismatch` with its name, source
line, expected parent, and actual parent. Assembly fails without relocating the
text or writing promoted output. Correctly placed configured subsections are
reported as applied; candidate subsections shadowed by protected base content
are reported as discarded.

The Python wrapper carries the structured report on success and failure. Merge
persists it before raising, and the architecture phase copies the assembly
status, section decisions, and diagnostics into durable run reports.

## Verification

The separate [promotion repair replay](../../../evaluations/architecture-surface-coverage/promotion-repair-replay/report.md)
promotes the three valid saved candidates and explicitly rejects Claude
repetition 2. That run writes no `promoted.md` and retains a merge report naming
`FIPS Compliance`, `Security`, and `Admission Webhooks`. Tests cover correct and
misplaced FIPS Compliance and Build Hermeticity subsections, fenced examples,
discard reporting, merge-report persistence, and runner propagation. A fresh
Sol review accepted the fix with no remaining correctness findings.
