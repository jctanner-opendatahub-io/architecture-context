# Bug: Structured rate-limit errors can continue to another component

Status: open, coordinator-discovered P3 blocker during independent review.

The production adapter recognizes only substrings "rate limit" and "rate_limit".
An offline stub returning HTTP429 or the actual provider session-limit wording
produces generic StructuredSynthesisError. The synthesis routine converts that
to a failed result and the pipeline component loop continues. User instruction
requires stopping on any actual rate limit; no retry/fallback/later component
call may follow. Preserve structured provider error status/code rather than
relying solely on prose; support observed quota wording and add two-component
entry-point tests proving no second adapter invocation after each real error shape.
Ordinary failures must retain their deliberately specified behavior.

Evidence: logs/structured-component-assembly/20260907-resume/
probe_rate_limit_classification.py and .txt. These were offline simulated errors,
not actual rate-limit events; current independent review remains running.

Independent repair criteria met: P3 cycle2, Fable/high session8e971bcc-9390-4b38-b213-4faa03d218a4; see p3-review2-report.md. Whole P3 gate remains open on new F6/F7.
