# Bug: Codex default selection sends a placeholder model name

Status: open.

F-P3-7: missing --model sends configured-default literally as params.model rather than None. CLI promises configured Codex default. Resolve actual default before input binding, retain resolved identity/settings, and avoid substituting an unavailable placeholder model.

Evidence: logs/structured-component-assembly/20260907-resume/p3-review2-report.md and p3-review2-evidence/.
