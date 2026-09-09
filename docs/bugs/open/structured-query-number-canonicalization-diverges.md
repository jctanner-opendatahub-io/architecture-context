# P4 O-1 — Go published-input fingerprint changes numeric literals

Status: open — discovered in independent P4 cycle1 review.

Nonblocking backlog; no real current analyzer snapshot affected (220-file corpus emits supported integer forms). Go ValidateAuthorityJSON decodes without UseNumber and changes443.0,1e2,large integers relative to Python/normalizer; query and Stage may reject otherwise Python-valid input. Independent evidence21-go-canon.txt. Distinct from existing conservative reuse-miss bug. Not included in focused P4 blocker repair.

Evidence: [review report](../../../logs/structured-component-assembly/20260908-publication/review-report.md),
reviewer Fable/high session a5d91853-a159-43d6-8187-97ba233134c9,
2026-09-09T01:12:18Z. No live calls or actual rate limits.
