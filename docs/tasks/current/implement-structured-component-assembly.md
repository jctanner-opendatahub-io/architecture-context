# Task: Implement Structured Component Assembly

Status: current. Started 2026-09-06; implementation and offline gates authorized by the user.

Follow the [consolidated implementation plan](../../plans/structured-component-assembly-consolidated.md).
Make analyzer facts, agent synthesis, typed patches, and accepted document models
JSON throughout component construction. Render the existing component Markdown
interface from the accepted model through the single analyzer renderer.

Consolidation is complete; the [original proposal and reviews](../../plans/structured-component-assembly.md)
remain unchanged for provenance. Track explicit requirements SC-01 through SC-25
and their acceptance checks. Publish `analyzer.json`,
`synthesis.json`, `document.json`, and component Markdown. Retain original model
proposals independently of logs and record their acceptance/rejection mapping
in the accepted document. The orchestrator persists structured model responses;
the model need not issue separate file-writing calls for synthesis sections.

Include early cross-version component reuse as phase 2 of the agreed revised
sequence, immediately after deterministic rendering parity. Select an explicit
prior accepted snapshot and compare normalized analyzer facts plus recorded
supporting evidence and relevant component inputs. Reuse hits must make zero
synthesis calls and retain original provenance. Platform synthesis is outside
this reuse decision. See the consolidated plan's cross-version reuse contract;
whole-component reuse is required, finer section invalidation can follow.

## Work and acceptance

1. Implement deterministic normalization/rendering parity and preservation tests.
2. Implement early whole-component semantic reuse with verified evidence dependencies.
3. Add opt-in single-response structured synthesis, bounded evidence follow-up,
   typed patch assembly, and retained response provenance.
4. Publish four core artifacts and integrate arch-query JSON consumption, existing
   Markdown consumers, indexes/platform/diagrams, audits, and mixed-format compatibility.
5. Complete independent review and offline gates; use a separately authorized
   scoped live canary for adoption and cost/quality measurements.

Preserve non-resource RBAC, canonical prefixes, included-but-not-integrated
components, explicit uncertainty, overlay provenance, and consumer paths. Do not
turn schema validity into semantic assurance. Original canary evidence stays
immutable. Coverage remains warning-only and component workers stay disabled.

Follow the [implementation framework](../../notes/implementation-framework.md):
Astra coordinates, Sol implements, and Fable 5.1 reviews phase gates independently,
with Opus 5 as the disclosed fallback. Record actual model access at kickoff.
Record phase results and limitations; implementation completion and live rollout
approval are separate. No code changes or live runs are authorized by this task's
creation alone.

## Execution checkpoint — 2026-09-06

- Authority: user requested execution to completion using the framework, stopping
  on rate limits. This overrides the framework wait/resume behavior: checkpoint
  and end the run on any rate limit, with no fallback or retry.
- Coordinator: current Codex API session, system identifies GPT-6; exact resolved
  variant is not exposed. Requested implementer: `gpt-5.6-sol`, high effort via
  Codex CLI. Requested independent reviewer: `claude-fable-5-1`, high effort via
  Claude CLI; availability/model identity to be verified, no fallback configured.
- Review budget: proposed maximum three review/repair cycles per phase before
  escalation; no live generation or default adoption in this authorization.
- Baseline: HEAD `39209078846f15f1909373c106d2d665a907a509`, extensive pre-existing
  tracked and untracked changes. Exact diff, status, and file hashes retained in
  `logs/structured-component-assembly/20260906-kickoff/`. Preserve all prior work;
  no commits or historical generated-output rewrites.
- Phases: P1 deterministic contracts/rendering; P2 verified reuse; P3 bounded
  synthesis; P4 publication/consumers (SC-18 parallel after P1); P5 offline review
  and adoption hold evidence. All SC-01–SC-25 remain unverified at kickoff.
- Next action: verify selected CLI model access, then delegate bounded P1 work.
- Implementation: not complete. Live evaluation: not authorized. Rollout: hold.

### Kickoff model access

- Sol CLI first attempt failed before initialization due to sandbox read-only
  session storage. Relaunched with approved outer access and worker sandbox
  `workspace-write`, explicit `gpt-5.6-sol`, high effort; phase-1 assignment is
  running. Detailed attempt stdout/stderr/command files use `p1-implementation*`.
- Fable tool-free access probe first timed out inside sandbox. Approved network
  retry completed, session identity retained in `reviewer-access-escalated.stdout`; response identifies `claude-fable-5-1`. Model usage also lists
  a Claude Haiku auxiliary call; no gate review has run or been accepted. No
  fallback option was passed. Review must inspect actual model usage.
- Requirements matrix and source-inspected consumer inventory retained alongside
  baseline in kickoff run storage. All requirements remain unverified.

- Baseline verification: `uv run pytest -q` — 948 passed, 10 skipped;
  `cd src/arch-query && go test ./...` — passed (cached). These are baseline
  checks, not new-route acceptance. Evidence: kickoff `baseline-verification.json`.

### Phase 1 implementation handoff

Sol session `01a07758-c81e-7600-974d-bd8e8f671263` completed the deterministic
slice; no independent acceptance yet. Report: kickoff `p1-implementation-report.md`.
All analyzer Go tests/vet pass, schemas validate, and 71 saved inputs normalize
and render byte-identically to the legacy renderer. Phase-specific diff and
input hashes: `p1-review.diff`, `p1-review-inputs.json`. Review cycle 1 pending.
SC-01 and SC-04–SC-09 have implementation evidence only; other IDs remain open.

### Phase 1 review cycle 1 — REQUEST_CHANGES

Fresh Fable `claude-fable-5-1`, high effort, session
`d74cb201-2f60-4f94-bae0-cd12f81c6ab8`, independently reproduced 71/71 byte
parity and complete corpus fact accounting. It rejected SC-07 structural Markdown
bypasses and SC-06 self-authorizing patches; repo-lineage validation also needs
repair. Findings filed immediately in the bug ledger. Report: kickoff
`p1-review-report.md`; raw stdout and denied probe records retained. Some scratch
probe scripts were denied, so their findings are explicitly code-inspection-only.
No rate limit or fallback occurred; primary review model usage is Fable, with
an auxiliary Haiku call also reported. Gate remains unaccepted.

Coordinator repair scope: all blocking findings, bound component-map provenance,
section attribution and typed table support needed for SC-07/09. These close
phase-one contract gaps; no later-phase implementation is authorized in the repair.
SC-18 will map validated rendering_view plus typed-only facts as needed, avoiding
a second rendering implementation; adapter waits for accepted phase-one schema.

### Phase 1 repairs ready for review cycle 2

Sol completed the bounded repair. Report: kickoff `p1-repair-report.md`.
Trusted policy is now separate from untrusted proposals; mapped lineage is
recomputed from bound inputs; attributed sections and typed tables are validated.
All analyzer tests/vet, three Python schema/CLI tests, and 71/71 corpus byte
parity pass (16,779 facts/accounting records). Input freeze/diff recorded in
`p1-rereview-inputs.json` and `p1-rereview.diff`. Bugs remain open pending
independent acceptance. No rate limit occurred.

### Phase 1 review cycle 2 — REQUEST_CHANGES

Fable `claude-fable-5-1`, high effort, fresh session
`cec81263-90d5-4c18-8ed6-048794fe219f`, independently verified closure of
all cycle-1 blockers, including 27 executed policy probes and lineage tampering.
New findings F1–F3: evidence-path/revision Markdown injection; dropped uncertainty
when sections have content; empty-table JSON roundtrip failure. Filed immediately
as three open bugs. Minor schema empty-provenance and identity-consistency cases
also need repair. Report: kickoff `p1-rereview-report.md`. All 76 historical
evidence files unchanged; both 71-input and 77-input corpora byte-identical.
No rate limit, substitution, or source edits by reviewer. Gate unaccepted.
Next: bounded second repair, then review cycle 3.

### Phase 1 second repair ready for review cycle 3

Sol completed the bounded F1–F3/minor repair; kickoff `p1-repair2-report.md`.
Evidence fields reject controls and sanitize rendering, unresolved sections keep
uncertainty with content, empty tables reject before encoding. Analyzer tests/vet
and three Python tests pass. Both corpora preserve bytes (71+77 inputs), all
148 accepted documents schema-valid. Preserved EA.1 training_hub/training-hub
baseline naming exception is recorded, not fabricated into a mapping.
Frozen packet: `p1-review3-inputs.json`, `p1-review3.diff`. Gate remains open
pending fresh Fable review cycle 3. No rate limit occurred.

### Phase 1 gate — PASS (review cycle 3)

Fresh Fable `claude-fable-5-1`, high effort, session `65b167d3-a7f8-4e98-9110-81a2608b14c4`
accepted the deterministic slice. Report: kickoff `p1-review3-report.md`.
All 14 analyzer test packages/vet and 3 Python tests pass independently;
71+77 corpus documents have byte parity and schema validity. All six phase-one
blocking defects are fixed and moved to the fixed bug ledger. Non-blocking inline
control-character observation is filed for phase 3. No rate limit occurred.
Accepted portions: SC-01, shared renderer SC-04, SC-05–SC-07, identity/section
portions SC-08/09. Later integration guarantees remain open.

The reviewer could not reproduce prior textual manifest digest formats. Preserve
that limitation; coordinator now records an unambiguous corpus map in
`p1-corpus-identity.json`: UTF-8 JSON, sorted repository-relative paths to SHA256,
keys sorted and separators comma/colon with no whitespace/newline. File SHA256
`b0dbd7b9789514776e61eb44feeec34abb9ada617b529f3af979e572b2d8bce0` identifies all 148 analyzer inputs. This
adds reproducibility evidence without changing accepted source or historical data.
Next: phase 2 verified reuse and parallel SC-18 adapter.

### 2026-09-07 — resume and reusable worker launcher

The user requested a retry after the prior Sol usage-limit stop, then requested
an on-disk abstraction for repeated Python launch code. Added
`scripts/run_implementation_worker.py`: explicit model/effort, workspace sandbox,
unique attempt directory, copied prompt and digest, command/cwd, stdout/stderr,
exit status and session IDs. No wrapper retry or fallback. Coordinator authored
this operational helper; it has local offline success/failure/evidence/overwrite
checks and Ruff validation, not independent gate acceptance.

The interrupted inline retry did not start either worker. Resumed P2 and SC-18
with `gpt-5.6-sol`, high effort using the saved bounded handoffs. Evidence lives
in `logs/structured-component-assembly/20260907-resume/{p2,sc18}/`.
P2 session: `01a07c6e-85fa-7cb3-a475-eaf3b4bcf6b6`.
SC-18 session: `01a07c6e-f04c-7fa3-b368-ff0d96fd9010`.
P1 remains independently accepted; later gates remain open. User's stop-on-limit
instruction remains in effect. No live generation or default rollout authorized.

Launcher follow-up: the same helper now supports `--harness claude` for fresh
review assignments with the previously used explicit model/effort and tool
settings. Both harnesses passed offline mocked executable checks for exit
propagation, prompt/session evidence and overwrite refusal; Claude final/model
capture also passed. Ruff passes. Usage is linked from the framework and scripts
README. This does not add a retry or fallback and does not constitute product
phase acceptance.

### SC-18 implementation handoff and shared-validator gap

Sol session `01a07c6e-f04c-7fa3-b368-ff0d96fd9010` finished successfully;
report: kickoff `sc18-implementation-report.md`. Query tests/vet/race and cached
v1.64.8 lint pass; 77/77 EA2 and 70/70 publishable EA1 typed parity pass. The known
EA1 training-hub/training_hub mismatch is explicitly rejected/excluded. Embedded
build/command checks pass. These are implementation results, not acceptance.

SC-18 remains unaccepted: its private-validator limitation allows inconsistent
rendering_view versus facts to evade full semantic validation. Filed
`docs/bugs/open/structured-query-does-not-bind-rendering-view-to-facts.md`.
Coordinator approved a narrow public analyzer wrapper around existing
`internal/structured.Decode`, consumed by arch-query as a build-time module
dependency. This avoids copying validation or needing an external runtime binary.
Bounded Sol/high follow-up launched through the reusable helper; prompt and
attempt evidence in `20260907-resume/sc18-shared-validator*`. Public-wrapper
source ownership is disjoint from P2's existing analyzer/Python edits. Fresh
independent review will cover the shared interface after implementation.

P4 still owns publication hash links, release-workflow staging, and legacy
conversion boundaries. The report's unpinned lint-tool/config incompatibility
will be assessed in final checks; compatible pinned lint is recorded separately.
No rate limit or model substitution occurred in the completed SC18 attempt.

### Phase 2 implementation ready for independent gate — 2026-09-07

Sol session `01a07c6e-85fa-7cb3-a475-eaf3b4bcf6b6` completed successfully.
Kickoff `p2-implementation-report.md` records 115 focused Python tests, analyzer
Go tests/vet, all 18 platform validations, and preservation audit. No rate limit.
SC11–16/25 are implemented but unaccepted. Existing defaults and live settings
remain unchanged. Frozen review packet: `20260907-resume/p2-review-inputs.json`
(SHA256 `334aca9e5efa3181e3f88386f1b98cf946872e3a11b6d6c31813102a00c6b678`),
235 copied source/fixture files, cumulative scoped diff plus original dirty
baseline and P1 accepted diff. Reviewer must inspect new untracked sources too.
Fresh Fable 5.1/high review cycle 1 launched through the saved helper, attempt
`20260907-resume/p2-review-1/`. The new public validator wrapper/query worker is
explicitly outside this frozen scope; reviewer Go checks exclude its new package.
No independent acceptance is claimed yet.

### SC-18 combined gate started — 2026-09-07

Sol shared-validator session `01a07ca9-ec6e-7290-9cba-ef7c466de15b` finished
successfully; report `20260907-resume/sc18-shared-validator-report.md`.
Public ValidateJSON delegates to existing strict accepted decoding; copied semantic
checks removed from query. All fixture/tampering tests, full/race tests/vet,
query and public-package lint, 77+70 corpus parity and standalone embedded build
pass. Eight wider analyzer lint findings are recorded separately in the bug ledger
for final validation (six baseline constructs, two P1-added structured findings).
No rate limit occurred.

All 235 frozen P2 files remained unchanged after this follow-up. Combined SC18
packet freezes 276 files in `20260907-resume/sc18-review-inputs.json` (SHA256
`a40f1eae58a4d8ca24a0b34f0a044693eefaf691dedf7e1ec6b6a93244d31a03`), with
copied sources and cumulative scoped diff plus original baseline provenance.
Fresh Fable 5.1/high combined review cycle 1 launched at
`20260907-resume/sc18-review-1/`. No implementation workers are editing source
while the two independent reviews run. The semantic-validation bug remains open
until independent acceptance; P4 publication and final lint requirements stay open.

### Phase 2 review cycle 1 — REQUEST_CHANGES

Fresh Fable 5.1/high session `7d385b28-9ec6-4a62-9488-3e49a02fe58e`
returned REQUEST_CHANGES; saved `20260907-resume/p2-review-report.md`.
SC11–13/16 and scan separation verified; SC14/25 blocked by unclassified Codex
commands and unhandled Claude tools incorrectly leaving complete observations.
SC15 needs non-stub actual-validator tests and predecessor/result consistency.
F4–F6 cover rename parsing, ignored search inputs and shell redirections; F7
records conservative false misses and dependency replay documentation. Four bug
records filed immediately. No rate limit. Primary model Fable; raw modelUsage
also records an auxiliary Haiku call, not a reviewer substitution.

Reviewer independently passed 115 Python tests, analyzer tests/vet, lint/platform
checks, and 71+77 corpus parity/schema/accounting. All 235 frozen files, all 76
historical evidence files and original proposal unchanged. No formatter spillover
survived. Reviewer disclosed temporary git-worktree metadata use for baseline
reconstruction and a remaining evidence limitation for the initially untracked
index test baseline. Preserve those limitations in subsequent review.

Bounded Sol/high repair launched at `20260907-resume/p2-repair-1/`, Python and
reuse-note ownership only; no Go/schema/query edits while the SC18 review runs.
Fix blockers plus bounded edge cases, then fresh re-review. Gate unaccepted.

### SC-18 review cycle 1 — PASS, dependency recheck pending

Fresh Fable 5.1/high session `a7b596b1-a251-4e25-8e3b-323dd6f7da0d`
returned PASS for the bounded SC18 adapter/shared-validator slice, with F1 final
freeze recheck after the active P2 repair exits. Report:
`20260907-resume/sc18-review-report.md`. All 276 inputs and 318 broader Go/schema
files unchanged at reviewer conclusion; 66 adversarial CLI cases reject without
fallback, both corpus replays pass, standalone static embedded build works after
source removal. Shared-validator bug acceptance criteria independently met but
bug movement/gate recording waits for the explicit F1 recheck.

The review prompt's statement that no implementer was active became stale when
Python-only P2 repair started after the SC18 review launch. The worker was given
no Go/schema/query ownership. Record this timeline openly; recheck all SC18 hashes
and classify the expected P2 Python delta after its exit. No source overlap may
silently invalidate the gate. No rate limit; primary Fable, auxiliary Haiku usage
disclosed by the harness.

F2 purpose-projection drift guard and F5 JSON-only exists path filed for P4. F4
pre-existing deps content/order nondeterminism filed separately, not attributed
to SC18 and not silently added to implementation scope. Coordinator F3 choice:
retain actionable whole-version load failure for an invalid accepted component;
do not return silently partial typed answers. Document that behavior in P4.
Publication hash binding, stale raw derivatives, release workflow, latent legacy
conversion fields, and final analyzer lint remain explicit P4/P5 obligations.

### SC-18 condition satisfied; P2 extra configuration repair

P2 repair session `01a07cc3-3508-7ed0-92c1-d7c4f5015065` completed, 112 focused
tests/lint/whitespace checks passed; report `20260907-resume/p2-repair1-report.md`.
No rate limit. Post-exit freeze check: all 276 SC18 files unchanged; only six
allowed Python/reuse-note files changed in the P2 packet. Evidence:
`20260907-resume/sc18-post-p2-repair-freeze-check.json`. Record the SC18 bounded
gate PASS and move the shared-validator gap bug to fixed. P4/final-lint limits
remain in force.

Coordinator's independent parent-ignore probe found that changing a committed
ancestor .gitignore changes rg results without changing the recorded subtree
identity. Evidence script/result retained; edge-case bug updated. The first
repair's F5 option exclusions do not yet demonstrate closure of this case.
Bounded same-model/high search-configuration follow-up launched at
`20260907-resume/p2-search-config/` before independent re-review. No Go/schema/
query edits authorized; originals/review evidence remain immutable.

### P2 search-config follow-up complete; review cycle 2 launched

Sol session `01a07ce3-3ada-7cf3-ac56-9e3fb6b265ba` finished the additional
search-configuration repair. Report `20260907-resume/p2-search-config-report.md`:
120 focused tests/lint pass, including real rg parent/local ignore changes,
include globs, ignored roots, external config and global excludes. Supported
searches require direct execution, completed output, explicit isolation/sort flags,
independent replay and execution-context/result identities; missing/unverifiable
records miss. Installed rg's actual config variable is RIPGREP_CONFIG_PATH; the
coordinator's RG_CONFIG_PATH example is not recognized and was handled explicitly.
No rate limit or model substitution.

All 276 SC18 frozen files remain unchanged. Fresh P2 cycle-2 packet freezes 241
files and a repair delta versus the first review snapshot:
`20260907-resume/p2-rereview-inputs.json`, SHA256
`ebb36197b68dd5d164520e0c08e21dcd18308c06b4518b467d6085c02d1c6ac4`.
Fresh Fable 5.1/high re-review launched at `20260907-resume/p2-review-2/`.
No implementation worker is active. P2 gate and its four bug records remain open
pending verdict; P3/P4/P5 assignments are drafts only.

### STOP — actual Fable session limit during P2 review cycle 2

User stop-on-rate instruction triggered. Fresh Fable 5.1/high session
`0655758b-f3a4-4e1d-8da5-625b86c3f735` returned actual HTTP 429 and rejected
five-hour rate-limit status, exiting 1 at 2026-09-07T17:51:43Z. Provider message:
"You've hit your session limit · resets 5:20pm (America/New_York)".
Evidence: `20260907-resume/p2-review-2/{stdout.jsonl,result.json,final.txt}`.
No verdict or P2 acceptance; any partial review is not a waived gate.

Stopped immediately on observing the limit. No retries, waiting loop, fallback,
effort reduction, or role reassignment. All implementation workers and reviewers
have exited; no other task process is pending. P1 and bounded SC18 remain accepted.
P2 repairs/config follow-up have implementation evidence (120 focused tests pass)
but fresh independent re-review remains incomplete. P3–P5 are draft handoffs only.
Next authorized resumption: inspect the failed review evidence and source freeze,
then resume/relaunch the same Fable 5.1/high gate after user requests continuation
with available capacity. The reusable on-disk launcher and all evidence remain
saved. No live generation or rollout occurred.

### P2 review resumed — 2026-09-07

User reports capacity reset and authorizes continuation. Coordinator verified all
241 frozen P2 inputs unchanged before relaunch. Fresh same-model Fable 5.1/high
review session `21058cd3-930d-4d53-8991-ba62f7c594b4` launched through the saved
worker helper; evidence: `logs/structured-component-assembly/20260907-resume/p2-review-2-resumed/`.
This completes the interrupted cycle-2 attempt, not an additional repair cycle.
No implementation worker is active; P2 acceptance remains pending. Stop-on-rate,
no fallback, and live/default-adoption hold remain in force.

### P2 cycle 2 resumed verdict — REQUEST_CHANGES

Fable session `21058cd3-930d-4d53-8991-ba62f7c594b4` completed without rate
limit. Primary Fable 5.1, auxiliary Haiku usage disclosed in launcher result.
Report/probes retained as `20260907-resume/p2-review2-report.md` and
`p2-review2-probes/`. Independently: 143 focused tests, 1012 full-suite tests
(10 skipped), Python lint/platform checks, analyzer vet/all 15 packages pass.
All 241 P2, 276 SC18, 76 historical files and original proposal unchanged.
Earlier F1/F2/F4/F6/F7 closed in review; F3 mechanism/F5 Codex subset verified.
Four new gate bugs F8–F11 filed immediately: unsafe persisted replay argv, shell
wrapper classification, Claude ancestor-ignore search gap, stale target analyzer
input claim. P2 unaccepted. Same-model Sol/high bounded repair follows, then
cycle 3 (last scheduled review cycle before escalation). No P3 launch.

### P2 repair 2 complete; cycle 3 packet

Sol/high session `01a07dd1-9d6e-73c3-a636-54190b84d76c` exited successfully at
2026-09-07T22:24:26Z. Requested model retained in invocation; no separate resolved
identity reported. No rate limit. Report `20260907-resume/p2-repair2-report.md`:
172 focused tests, five actual-Go-backed target-binding tests, lint pass.
Coordinator verified exactly eight permitted changed files and all 276 SC18
inputs unchanged. New frozen packet `p2-review3-inputs.json`, source and delta
retained beside report. All bugs/gate remain pending fresh cycle-3 review.
Conservative Claude search misses and required trusted TargetNormalization
producer input explicitly disclosed; P3 must integrate that contract.

### P2 independently accepted — phase 3 next

Fresh Fable/high cycle3 session `b7b8d76a-e126-4874-be29-36c2433fe4eb` exited
2026-09-07T22:43:43Z PASS for bounded P2, all F1–F11 criteria met. Primary
Fable, auxiliary Haiku usage disclosed; no rate limit. Report/probes saved as
`20260907-resume/p2-review3-report.md` and `p2-review3-evidence/`.
Independent checks: 172 focused and 1041 full Python tests (10 skipped), changed
Python lint, targeted Go tests/vet pass; all252 packet/276 SC18/76 historical
hashes and proposal unchanged. Go fingerprint parity148 and actual normalization11
real inputs; zero-call reuse and malformed/altered output misses independently
verified. Eight P2 bugs moved fixed with evidence; requirement matrix updated.
F12–F16 nonblockers filed: live Codex wrappers currently preclude reuse, alternate
wrapper/read edge, target integration status must be producer-bound, noncanonical
number-literal false misses, six out-of-delta Python lint findings. P3 must honor
trusted normalization/validator and actual current component-map binding. P5 must
resolve final lint. No live generation or adoption; P3 opt-in route is next.

### Phase 3 implementation launched

Sol/high session `01a07e0c-aa56-78f1-91a8-eb669c53c42c` launched via saved
helper after P2 acceptance. Assignment: `20260907-resume/p3-implementation-prompt.txt`;
attempt `p3-implementation/`. Coordinator froze521 source/fixture files in
`p3-baseline-inputs.json` / `p3-baseline-source/` plus cumulative dirty diff.
Ownership is bounded generation/adapters/CLI/assembly/tests/docs, including minimum
shared-schema/Go changes and synchronized query schema needed by P3. Fresh review
must renew affected P1/P2/SC18 guarantees; no competing source worker. Publication
protocol and wider consumers are P4. No live generation/default adoption.

### P3 initial implementation complete; CLI predecessor gap remains

Sol/high `01a07e0c-aa56-78f1-91a8-eb669c53c42c` completed at
2026-09-08T00:00:20Z without rate limit. Report `p3-implementation-report.md`
SHA256 6cb4b52127a9f1e8c72cc979d9c064cb3d6bb595ef1f88f1d1435f4b6704366b.
233 focused tests and full analyzer/query Go tests/vet passed, affected lint
passed. Shared reuse field/inline-control/schema/parser changes require renewed
review. Formatter spillover was reportedly removed using frozen P2 files;
coordinator/reviewer must verify against P3 baseline. Full lint remains pending.
Implementer reports missing CLI predecessor loader; bug filed, gate unaccepted.
Coordinator resolves storage question with a versioned private staged run record,
not an extra published artifact; P4 must retain essential records in four cores.
Bounded integration followup precedes P3 review. Production capability limits
remain material: Codex tool-free calls refused; Claude opaque-context gap forces
reuse misses. No claim of live support or completed runtime savings.

### P3 CLI followup complete; first independent review packet

Sol/high session `01a07e54-9826-7301-bde6-522668a4306c` completed at
2026-09-08T00:48:24Z without rate limit. Report `p3-integration-followup-report.md`
retains original P3 report unchanged. Real entry-point/reload/current-Go tests
pass: 164 focused Python tests, structured/renderer/cmd Go tests/vet and scoped
lint. Private predecessor run record/loader implemented; four-core publication
metadata retention is explicit P4 work. Production Codex tool-free invocation
remains unsupported; production Claude always records incomplete opaque provider
context and therefore misses reuse. These are material review limitations.
Coordinator checked initial24 reported paths (18 old+6 new), no unreported P3
baseline changes; followup10 hashes matched and only reported changes plus root
cleanup exist. Original formatter spillover absent from initial snapshot delta.
Coordinator escalated compatible golangci-lint1.64.8 after worker's sandboxed
latest failure; found original8 plus new S1009 reuse nil-check. Filed bug and
applied a one-line behavior-preserving fix; structured Go tests pass. Root is
author of this cleanup, not its independent approver. Review packet includes it.
Packet: p3-review-inputs.json/source/diff and p3-coordinator-scope-check.json.
No active implementer; fresh Fable/high review follows, no gate accepted yet.

### STOP — actual Fable session limit during P3 review cycle 1

User stop-on-rate instruction triggered. Fable5.1/high session
`06777b8e-8943-4630-9614-c79790a63e62` exited1 at
2026-09-08T01:24:55Z with actual HTTP429/session limit. Provider reset:
"10:20pm (America/New_York)". Attempt `20260907-resume/p3-review-1/` retains
raw events/result/model usage (primary Fable, auxiliary Haiku). No verdict or
P3 acceptance. No retry, fallback, effort reduction, or role reassignment.
All coordinator-launched implementation/review sessions have exited; no further
implementation launched. Partial scratch evidence preserved in
`p3-review1-partial-evidence/`; freeze/checkpoint `p3-rate-stop-checkpoint.json`.

P1/P2/SC18 prior bounded approvals retained for frozen inputs. P3 implementation
and CLI followup have local evidence, but shared P1/P2/SC18 renewals remain open.
P4/P5 not launched. Production Codex refusal and Claude reuse-context limitation
remain material, unaccepted limitations. No live generation or default adoption.

During review coordinator found offline simulated HTTP429/provider quota wording
misclassified as ordinary failure; bug
`structured-rate-limit-errors-can-continue-components.md` filed immediately.
Reproduction script/output retained; those simulated inputs were not rate events.
This real stop is the reviewer-provider429. Required repair remains unimplemented
at stop. Codex capability investigation is read-only, uses OpenAI Docs skill,
and is saved in `codex-tool-free-capability-note.md`; no global hard-disable
control established from official docs or generated local protocol, no live call.

Next authorized resumption after user continuation/capacity: verify source freeze
and partial review evidence, complete same Fable/high P3 cycle1 review against
unchanged packet (including coordinator rate-classification finding), then route
repairs under the framework. No partial review or passing local tests waive gate.

### P3 review resumed after user-reported reset

User authorized continuation. Coordinator verified all530 frozen P3 source files unchanged. Completing interrupted cycle1 with fresh Claude Fable5.1/high session, same role/model/effort, no fallback. Saved partial evidence and uncorrected rate-error finding included; production limitations remain unaccepted. Stop again on actual rate limit. Assignment: `logs/structured-component-assembly/20260907-resume/p3-review1-resumed-prompt.txt`.

### P3 cycle1 review complete — repairs required

Fable/high session39888686-67c7-48fe-b894-621e7a28bad8 completed 2026-09-08T04:05:08Z REQUEST_CHANGES, no rate limit; auxiliary Haiku usage disclosed. Report p3-review1-report.md and p3-review1-evidence saved. All530 source/76 historical/proposal hashes preserved. Full1092 Python tests10skip, analyzer/query Go tests/vet, query lint pass; 148 corpus byte parity and34,777 facts accounted. Five blockers: rate errors continue components; analyzer mutation window; model-visible observations/ranges omitted from reuse key; reported-model eligibility ignored; malformed answers escape raw audit capture. Production capability gaps remain unaccepted. Inline-control and root nil-check bugs independently accepted and moved fixed. Correction to prior scope report: five cosmetic reflows remain in reuse module (AST-equivalent), no unreported behavior change. P3 gate remains open; Sol/high repair next, then fresh cycle2.

### P3 repair1 completed; bounded guard followup before review

Sol/high session01a080fd-dfb7-7392-939e-192540bee11d exited0 at2026-09-08T13:53:31Z without actual rate limit. Report p3-repair1-report.md; exactly11 reported source changes/hashes checked against530-file review baseline, frozen p3-repair1-inputs.json/source. Reports212 focused tests,1121 full Python10skip/7 sandbox-deselected, Make283/4skip and Go suites pass. Root separately reran all7 localhost MLflow tests escalated:7pass. Six preexisting Python lint remain. Allfive review blockers implemented pending review. New bounded Codex first-tool-interruption and Claude documented provider-boundary interpretation require review. One stale refusal test unintentionally reached authenticated SDK startup and was cancelled; no response/rate event retained, no claim that a provider request definitely did not occur. Subsequent tests use stubs; no planned live generation or adoption. Coordinator identified omitted image tool events and current CLI fallback-control question, recorded in open bug/review draft; bounded Sol followup before fresh cycle2.

### P3 guard followup complete; cycle2 review packet

Sol/high01a0814e-b482-7a43-b0d4-0db573d14a33 completed2026-09-08T14:27:58Z no rate. Exactly3 reported changes verified against530-file repair1 snapshot; original report unchanged.255focused tests/scopedlintpass. Guard now rejects all non-passive/unknown/malformed lifecycle and terminal items; model reroutes reject; supported bundled experimental protocol sends allowProviderModelFallback=false through actual SDK JSON transport. Best-effort interruption cannot prove already-started tool action never ran. All capability interpretations/repairs remain unaccepted. Frozen cycle2 packet p3-review2-inputs.json/source/diff/prompt and preserved protocol evidence ready for fresh Fable/high review. No live call in followup.

### P3 cycle2 REQUEST_CHANGES; original five repairs verified

Fresh Fable/high8e971bcc-9390-4b38-b213-4faa03d218a4 exited0 at2026-09-08T15:00:28Z, no rate; auxiliaryHaiku disclosed.1171Pythonpass10skip, originalF1–5 reproduced repaired; Codexguard accepted. NewF6Claude --json-schema hidden tool/retry path and F7Codex requested/resolved identity/localcontext/default-placeholder block. Fullreport/evidence retained. Five independently verified bugs moved fixed; model mismatch/capability gap remainopen. Filealias/CLIversioncompatibility followup recorded. One scheduled review cycle remains. Incident correction: stale test completed with failure and13later tests ran before SIGINT; immediate interruption claim inaccurate. AuthenticatedSDK session startup at13:00:16Z confirmed; provider request/billing cannot be determined from retained evidence. No survivors found. A Vim swap for lib/codex_agent.py appeared duringreview; source bytes stillmatch at finalreview. Coordinator asked user about active editing and will avoid that file pendinganswer; separate Claude correction can proceed.

### Claude partA complete; user clears Codex edit hold

Sol/high01a0818b-c166-7eb2-8cf1-a859770d5fd2 completed2026-09-08T15:25:57Z without rate.118focused tests/scopedlintpass. Exactly5reported changes/hashverified, other525unchanged; report p3-claude-repair2-report.md and frozen p3-claude-repair2-inputs.json/source. F6 output_format removed only boundedClaude, actualSDKserializer tested; actual bundledClaude2.1.119 identity/hash and staticmodelalias enterkey, rate refusal durable diagnostic. Previousreview inspected system2.1.263; actualSDKbundle identity corrected without rewriting oldevidence. No liveSDK/provider invocation. User explicitly confirmed Vim was read-only viewing and closed it, authorizing codex_agent.py changes. CurrentCodexfile stillreviewhash13d843cd. Holdlifted; bounded Sol/highF7model/default/localcontext repair follows, then third/finalscheduled P3review. Allrepairs remainunaccepted.

### Codex part B and coordinator test guard complete; final P3 review next

Sol/high session 01a081a2-5f91-7163-921c-c3b7989a3d49 exited 0 at 2026-09-08T16:28:32Z without rate limit. Exactly six reported changes/hashes verified against the 530-file Claude snapshot. Codex preflight resolves model/provider/effort/service and isolated context before reuse; explicit mismatch prevents a turn; omitted model is correct; unknown activity/terminal views reject; producer-ineligible failure remains per-component. Report: p3-codex-repair2-report.md. Prior reports/history preserved. 284 focused tests and 1192 runnable full Python tests reported, with seven sandbox socket errors. A second SDK startup during preflight is disclosed: no model-turn path available, control-plane network unknown. Subsequent worker tests were stubbed.

Coordinator then authored a default pytest SDK startup/connect guard and two direct regression tests, after worker exit. Both tests and scoped lint pass; full escalated suite: 1202 passed, 10 skipped. Output: p3-final-repair-pytest.txt. Existing 530 source files remain unchanged after worker; root authored the two test files and cannot independently approve them. Report: p3-transport-guard-report.md. Fresh final scheduled Fable/high P3 review follows; all current repairs remain unaccepted. No live generation or adoption.

### P3 final review paused at actual Claude rate limit

Claude Fable5.1/high session 94728990-a54a-4230-9c86-e4edf303e620 stopped at 2026-09-08T16:44:42Z with HTTP 429 and session-limit message, reset reported as 3:30 p.m. America/New_York. Auxiliary Haiku usage disclosed. No retry, fallback, new worker, or further implementation after the limit. Cycle3 is incomplete: no report or verdict was produced. Saved two partial scratch files in p3-review3-partial-evidence and checkpoint p3-review3-rate-stop-checkpoint.json. All 546 frozen source files checked unchanged. P3 repairs and coordinator test guard remain awaiting independent acceptance; 1202 passing Python tests do not waive that gate. P4 publication/collection work and P5 final checks remain pending. On explicit user resumption, verify packet and finish interrupted cycle3 with the same reviewer model/effort. The user's clarification cleared the Codex edit hold; its changes are included.

### Durable review backlog — 2026-09-08

At the user's request, saved three pending Claude handoffs:
[finish P3](../pending/review-structured-synthesis-final.md),
[review P4](../pending/review-structured-publication-consumers.md), and
[review P5](../pending/review-structured-final-readiness.md).
They retain the existing dependencies, model/effort, phase budgets, frozen P3
packet, and separate adoption hold. P4/P5 packets must be completed before
review dispatch. No worker launched or implementation resumed in this bookkeeping
turn; the interrupted review remains unaccepted. Creating backlog tasks does not
reset the review budget or authorize a fourth P3 cycle.

### Codex-only preparation authorized — 2026-09-08

User explicitly authorized work that can continue without Claude. Bringing
forward bounded P5 lint cleanup and offline checks; Claude P3 cycle3 and all
dependent approval gates remain paused. No reviewer substitution or review-budget
reset. Same Sol/high implementer via existing CLI launcher; no live generation,
default adoption, or commits. New actual rate limits still stop the work.
Baseline and cleanup assignment: logs/structured-component-assembly/20260908-codex-only/.
Existing frozen review evidence remains immutable; changed source will be recorded
for impact assessment before Claude resumes. Implementation completion remains open.

### Codex-only cleanup complete — 2026-09-08

Sol/high session 01a0822a-ba78-7e81-8cdd-717042539136 exited 0 at 18:23:10Z.
Verified exactly 12 reported changes and hashes against 547 baseline files;
11 changed paths overlap the paused P3 review. No actual rate limit occurred.
The CLI recorded automatic timeout reconnections before work, correcting the
worker report's broad no-retry wording. Full lint (including default pinned Go
commands), make test, and normal builds pass. Full Python: 1195 passed, 10
skipped, seven sandbox socket errors; coordinator permitted rerun: seven passed.
Combined coverage is 1202 passed/10 skipped, with no SDK guard bypass.

The old 546-file P3 snapshot is preserved. Of 76 historical-manifest paths, 75
are unchanged; the intentional exception is compare.py formatting, with original
bytes retained and hash-verified. Original result data, rejected verdicts, and
proposal are unchanged. Reports, deltas, and current hashes are in
logs/structured-component-assembly/20260908-codex-only/.

Queued reviews now reference the source changes; lint bugs remain pending
independent acceptance. Bounded offline preparation moved to done. P3/P4/P5 gates
remain open. No Claude review, live generation, rollout, or commit. The publishing
test checklist is prepared and linked. All new documentation links resolve and
all 547 final source identities still match after ledger updates.

### Branch checkpoint authorized — 2026-09-08

User explicitly requested committing and pushing the current changes to
regen/praxis-repos. This supersedes the earlier no-commit restriction for this
checkpoint. Code/tests/work records and existing generated outputs are grouped
separately. No review gate is waived and no generation or rollout is run.
Remote origin is jctanner-opendatahub-io/architecture-context; its observed branch
head 28728163 is an ancestor of local HEAD 39209078. A normal push is planned.
Detailed local review logs remain ignored; the tracked checkpoint note records
current validation, outstanding reviews, and this evidence-availability limit.
