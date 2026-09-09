# Fresh source materialization can hang while handling a blob error

Status: open backlog — nonblocking classification verified in the completed P5 cycle-2 review.
Found: 2026-09-09, independent review of the fresh comparison utility.

One reviewer run stalled at 183/184 while materializing an MLflow mp4 blob.
An exception in the blob loop entered cleanup, which closed stdin and waited
for git cat-file while Git remained blocked writing into an undrained pipe.
The original exception was not surfaced. Its underlying trigger is unknown;
transient scratch-space pressure is only a hypothesis. Two worker runs and a
second independent reviewer run completed all 184 inputs.

Evidence: section 5 O-C2-2 of
`logs/structured-component-assembly/20260909-ordering-review/review-report-draft-rate-limited.md`
and `review-evidence/reviewer-run-1-stalled-progress.txt` in the same packet.
Follow-up: terminate or safely drain the child on a materialization error,
preserve the original failure, and add a bounded failure-path regression.
No tool repair was attempted after the rate-limit pause.

Final disposition: Fable/high continuation b72d66cb-5ba6-4411-9dcb-7b7ec437700b
confirmed the robustness issue and unknown trigger in the final report. The
implementation gate passed using the completed verified runs; this tooling
failure-path follow-up remains open.
