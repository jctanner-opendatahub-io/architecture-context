# Publication enumeration repairs despite repair_markdown=False

Status: open, nonblocking API-clarity backlog (P4 cycle2 O-12).

`accepted_publications(..., repair_markdown=False)` invokes recovery before
loading, and recovery repairs Markdown. The flag therefore does not mean that
this function is read-only. This predates the cycle2 repair and is not a P4
blocker; the accepted lint fix uses the distinct `validate_accepted_publications`
read-only entrypoint. Consider documenting or simplifying the flag separately.

Evidence: [independent review](../../../logs/structured-component-assembly/20260909-publication-repair/review-report.md),
`consumer_paths_review2.json`, Fable/high sessionb036fa12-9fc3-444a-ab72-fcc15280a655.
