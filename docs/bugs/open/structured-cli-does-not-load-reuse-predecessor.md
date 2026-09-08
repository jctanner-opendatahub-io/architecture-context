# Bug: Structured CLI does not load an explicit reuse predecessor

Status: open, P3 integration gap reported by implementer.

The programmatic API can accept AcceptedSnapshot/ReuseTarget but the opt-in CLI
always records predecessor-not-supplied. This leaves the required reuse-first
pipeline integration incomplete. P3 must load an explicitly selected, validated
prior private staged result, build current trusted target inputs/Go normalization,
and preserve normal bounded misses. P4 will integrate published four-file input
locations and retain essential metadata in those core files.

Evidence: logs/structured-component-assembly/20260907-resume/p3-implementation-report.md.
