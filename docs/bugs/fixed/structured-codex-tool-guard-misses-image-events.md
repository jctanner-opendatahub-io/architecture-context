# Bug: Structured Codex tool guard omits image tool events

Status: open; coordinator source inspection during P3 repair, pending worker reconciliation and independent review.

Current lib/codex_agent.py `_is_tool_item` enumerates six tool item kinds, but
the installed SDK also exposes `imageView` and `imageGeneration` tool items.
These currently bypass first-tool interruption. Verify all installed tool event
variants and unknown future activity fail conservatively; no open-ended loop or
accepted tool-active answer may pass through an incomplete event list.

Evidence: installed openai_codex/generated/v2_all.py lines4702/4724 and ThreadItem
union, compared with lib/codex_agent.py `_is_tool_item` during repair1. The repair
is still in progress, so reconcile final bytes before declaring unresolved.

Independent repair criteria met: P3 cycle2, Fable/high session8e971bcc-9390-4b38-b213-4faa03d218a4; see p3-review2-report.md. Whole P3 gate remains open on new F6/F7.
