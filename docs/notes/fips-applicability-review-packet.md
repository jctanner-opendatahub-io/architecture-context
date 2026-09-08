# FIPS Applicability Review Packet

## Review boundary

This packet supported the independent review required by
`docs/tasks/done/fix-surface-fips-applicability.md`. The review outcome is
recorded below. Review the implementation against checkpoint
`39209078846f15f1909373c106d2d665a907a509` with:

```bash
git diff 39209078 -- \
  lib/architecture_surface_coverage.py \
  tests/test_architecture_surface_coverage.py \
  evaluations/architecture-surface-coverage/audit_tree.py \
  tests/test_architecture_surface_rollout_audit.py \
  evaluations/architecture-surface-coverage/rollout-audit-fips-baseline.json \
  evaluations/architecture-surface-coverage/rollout-audit.json \
  evaluations/architecture-surface-coverage/rollout-audit.md \
  .claude/skills/repo-to-architecture-summary/references/surface-coverage-contract.md
```

The worktree also contains validation-baseline and JSON Patch changes. They are
outside this review boundary.

## Required behavior and current evidence

| Case | Required result | Regression |
|---|---|---|
| Empty FIPS category with only `coverage:fips_compliance` | Preserve an immutable uncertain observation; do not nominate a required surface | `test_empty_fips_category_retains_uncertainty_without_surface` |
| Static build, packaging, provider, crypto, or TLS source | Nominate an unresolved surface with uncertain applicability and claim support | `test_operator_inventory_uses_specific_evidence_nominated_surfaces`, `test_crypto_provider_signal_keeps_runtime_fips_applicability_uncertain` |
| Explicit runtime or policy source | Mark the question applicable while leaving claim support uncertain | `test_runtime_fips_signal_nominates_applicable_surface` |
| Source-backed explicit negative | Mark the limitation question applicable while leaving claim support uncertain | `test_explicit_negative_fips_signal_nominates_limitation_surface`, `test_source_backed_negative_fips_category_is_applicable`, `test_common_explicit_negative_phrases_are_applicable` |
| Evidence-free explicit negative category state | Preserve uncertainty without nomination | `test_evidence_free_negative_category_remains_unseeded_uncertainty` |
| Agent mutates an unseeded applicability observation | Fail structural validation and restore the seeded observation | mutation assertions in `test_empty_fips_category_retains_uncertainty_without_surface` |

The implementation never converts a build flag, dependency, provider, TLS
configuration, packaging annotation, negative signal, or category fact into a
supported runtime-compliance claim. Every nominated FIPS surface begins with
`claim_support: uncertain` and `disposition: unresolved`.

## Same-input audit

The checked-in baseline pins the pre-fix report to checkpoint `39209078` and
input fingerprint
`8a21066d05c68d202d07f02c5f43366c3debdd3b1935877f94b4b7928f0a1051`.
The current report uses the identical fingerprint.

| Measure | Before | After | Delta |
|---|---:|---:|---:|
| Surface occurrences | 526 | 474 | -52 |
| Required surface occurrences | 314 | 262 | -52 |
| Runtime-FIPS surface occurrences | 149 | 97 | -52 |
| Runtime-FIPS repository occurrences | 80 | 54 | -26 |
| Nominated without category facts | 138 | 86 | -52 |

The 97 post-fix nominations comprise 90 uncertain static-signal questions and
seven applicable source-backed limitation questions. Another 52 artifacts
across 29 repository identities retain explicit uncertainty without nomination.
The decrease measures only the planning-rule change and is not semantic-recall
evidence.

Current artifact checksums:

```text
64ea54ed30473d1f6a44fa8ffa7aeeb0e606c11a2e697c4b532f988643e721a9  rollout-audit.json
bb7a5320fbe1f8fdf99778eef442509dd03f6bce252c3bb902ba49e1106e6308  rollout-audit.md
```

## Reproduction

```bash
./.venv/bin/pytest -q \
  tests/test_architecture_surface_coverage.py \
  tests/test_architecture_surface_rollout_audit.py

./.venv/bin/python evaluations/architecture-surface-coverage/audit_tree.py \
  --architecture-root architecture \
  --comparison-baseline \
    evaluations/architecture-surface-coverage/rollout-audit-fips-baseline.json \
  --output-json /tmp/rollout-audit.json \
  --output-markdown /tmp/rollout-audit.md

cmp /tmp/rollout-audit.json \
  evaluations/architecture-surface-coverage/rollout-audit.json
cmp /tmp/rollout-audit.md \
  evaluations/architecture-surface-coverage/rollout-audit.md
```

## Reviewer decisions

The independent reviewer should explicitly determine whether:

1. every nomination has a concrete repository-relative analyzer source;
2. evidence-free category state remains visible without producing a required
   warning;
3. the negative-signal matcher identifies limitations without treating generic
   uncertainty such as “not fully determined” as an explicit negative;
4. applicable status is kept separate from supported compliance;
5. observation immutability and final-sidecar repair preserve the inventory
   identity; and
6. the audit comparison uses the same input fingerprint and describes the
   reduced count only as a rule delta.

Record the reviewer identity, date, commands run, findings, and acceptance or
requested changes in the task before moving it to `done/` and closing the bug.

## Independent review outcome

Fresh reviewer `/root/fips_independent_review` (`gpt-5.6-sol`) completed the
review on 2026-09-05. The first three review rounds rejected unsafe or missing
source attribution, cross-record provenance borrowing, and generic structured
statuses being interpreted as FIPS determinations. Each defect received a
focused regression before re-review.

The fourth review accepted the final implementation. The complete 64-test
boundary matrix passed, both audit artifacts reproduced byte-for-byte with the
checksums above, the identical input fingerprint and rule-delta interpretation
were preserved, and no tracked architecture file or review input was modified.
The task records the reviewed cases and final disposition.
