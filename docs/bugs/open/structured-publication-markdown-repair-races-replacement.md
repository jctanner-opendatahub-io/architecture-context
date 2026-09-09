# P4 O-7 — Markdown repair can race a concurrent publisher

Status: open — discovered in independent P4 cycle1 review.

Nonblocking backlog. load_accepted_publication repair runs outside the lock after recover_publication; concurrent replacement can leave old rendering beside new authority. Mismatch is detected and rejected, not silently mixed, and subsequent repair recovers. Independent concurrency probe succeeded; race noted by source inspection. Not included in focused P4 blocker repair.

Evidence: [review report](../../../logs/structured-component-assembly/20260908-publication/review-report.md),
reviewer Fable/high session a5d91853-a159-43d6-8187-97ba233134c9,
2026-09-09T01:12:18Z. No live calls or actual rate limits.
