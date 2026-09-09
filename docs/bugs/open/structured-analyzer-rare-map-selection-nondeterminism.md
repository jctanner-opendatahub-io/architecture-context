# Rare analyzer input shapes retain map-order-dependent selection

Status: open backlog — nonblocking classification verified in the completed P5 cycle-2 review.
Found: 2026-09-09, Fable/high session 79b9135b-098b-4c27-a207-e8d0738a68ee.

The source audit identified uncommon cases where map iteration can influence
selected content: access-policy exclusion order, first-match authentication
sources, first matching CLI configuration, and the retained source of duplicate
gRPC registrations. The tested 184-side corpus does not exercise these ambiguous
shapes; three full repaired-build runs and targeted repeats agree. Universal
determinism is not established by that corpus.

Evidence and exact sites are in section 5 of
`logs/structured-component-assembly/20260909-ordering-review/review-report-draft-rate-limited.md`.
The draft is preserved evidence, not a finalized acceptance verdict.
Follow-up: construct adversarial fixtures for those input shapes, stabilize
selection without discarding facts or meaningful ordering, and independently
review any product change. No repair was started after the rate-limit pause.

Final disposition: Fable/high continuation b72d66cb-5ba6-4411-9dcb-7b7ec437700b
confirmed this backlog classification in section 5 of the final review report.
The implementation gate passed; this rare-input follow-up remains open and
does not establish universal determinism for arbitrary input shapes.
