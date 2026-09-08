# Bug: Codex reuse live-wrapper limitations

Status: open, non-blocking P2 follow-up.

F12/F13 low: live SDK wraps all source commands in bash -lc, which intentionally makes current observations incomplete. Unwrapped positive fixtures do not prove live Codex reuse. Other wrapper names/flag shapes paired with recognized SDK reads can remain complete, although live exposure was not found. P3 must document live consequence and keep unsupported observations ineligible; tighten alternate-wrapper read edge with tests when touching adapter.

Evidence: `logs/structured-component-assembly/20260907-resume/p2-review3-report.md`.
