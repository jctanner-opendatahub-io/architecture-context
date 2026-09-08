# Task: Fix Surface FIPS Applicability

Status: complete and independently accepted 2026-09-05. Started after commit
`39209078` checkpointed the completed architecture-surface implementation and
audit.

Follow step 1 of the [plan](../../plans/architecture-surface-coverage.md) and the
[fixed bug](../../bugs/fixed/surface-inventory-nominates-empty-fips-category.md).
Require an explicit applicability basis, not merely an empty coverage category.
Preserve uncertain applicability and distinguish build evidence from runtime
compliance; zero facts do not prove not-applicable.

Acceptance: positive, empty, ambiguous, and explicit-negative tests; independent
review; reproducible audit nomination deltas; no generated-document edits or
enforcement changes. Close the bug only after verification.

## Progress

- Empty category coverage now produces a preserved, immutable uncertain
  applicability observation without nominating a required surface.
- Concrete build, packaging, provider, crypto, and TLS signals nominate an
  uncertain runtime-FIPS question. Explicit runtime/policy and explicit-negative
  signals make the question applicable without establishing compliance.
- Positive, empty-category, ambiguous-provider, explicit-negative, observation
  immutability, audit aggregation, comparison-fingerprint, source-path,
  record-provenance, and negative-specificity regressions pass: 64 focused
  coverage/audit tests total.
- The same-input audit is byte-reproducible. It changes runtime-FIPS nominations
  from 149 artifacts/80 repositories to 97 artifacts/54 repositories and retains
  52 evidence-free category records as uncertain without nomination. Required
  surface occurrences change from 314 to 262. These deltas measure the planning
  rule only and do not demonstrate improved semantic recall.
- No generated document, enforcement mode, or worker policy changed.
- A pre-review edge-case audit added source-backed category-level negatives and
  common negative phrases such as `FIPS mode is not enabled`. Evidence-free
  negative category state remains unseeded uncertainty. The on-disk result still
  has 97 nominations, now classified as 90 uncertain questions and seven
  applicable limitation questions; claim support remains uncertain for all 97.
- The bounded independent-review inputs and reproduction commands are collected
  in the [review packet](../../notes/fips-applicability-review-packet.md).

## Independent review

Fresh reviewer `/root/fips_independent_review` (`gpt-5.6-sol`) reviewed the
source diff, tests, and reproduction artifacts without editing files. Three
review rounds rejected boundary defects before the final review was accepted:

1. Zero-fact source-backed negative category evidence was suppressed, while
   URI and Windows drive sources were treated as repository-relative.
2. An unbacked category status could borrow an unrelated static provider path.
3. Generic disabled/false/required fields on provider, TLS, packaging, and
   unrelated policy records could become FIPS determinations.

The final implementation ties category determinations to category-local valid
paths, requires FIPS context for structured security-record determinations, and
uses the same strict repository-relative check for nomination and candidate
validation. The final reviewer ran the full accumulated boundary matrix (64
tests), reproduced both audit artifacts byte-for-byte, confirmed the input
fingerprint and no-recall interpretation, and found no blocking defect. The
review did not modify generated architecture.
