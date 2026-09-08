# Bug: Structured route cannot generate with Codex or reuse with Claude

Status: open.

P3 review section5: Codex rejects all structured calls because an all-tools-disable control is not established; Claude declares opaque provider internals incomplete and always misses reuse. These are material unaccepted limitations. The plan requires bounded tool use, not necessarily global tool disabling. Evaluate supported controls and distinguish supplied local context from opaque provider implementation; do not silently reduce scope or invent support.

Evidence: logs/structured-component-assembly/20260907-resume/p3-review1-report.md and p3-review1-evidence/.
