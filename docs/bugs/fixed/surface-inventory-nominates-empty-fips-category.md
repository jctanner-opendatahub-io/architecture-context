# Bug: Surface Inventory Nominates Empty FIPS Category

## Status

Fixed and independently accepted 2026-09-05.

## Problem

`build_surface_inventory` nominates `compliance.runtime-fips` whenever the
analyzer contains a `category_coverage.fips_compliance` record, including when
that record contains no facts or source evidence. The surface is required, so a
generic coverage record can create a required warning for components with no
extracted FIPS signal.

The on-disk audit found the surface on all 149 eligible analyzer artifacts. In
138 artifacts across 72 repository identities, the FIPS category reports zero
facts. This prevents the corpus from providing a useful warning-quality signal
until applicability is narrowed.

## Expected behavior

Nominate runtime FIPS from a concrete build, packaging, crypto, or runtime
signal, or retain an explicitly uncertain applicability record that does not
look like a universally applicable required warning. Preserve the distinction
between build signals and evidence of runtime compliance.

## Evidence

- `evaluations/architecture-surface-coverage/rollout-audit.json`
- `evaluations/architecture-surface-coverage/rollout-audit.md`

Do not infer a missing runtime behavior from the zero-fact category. The audit
contains stored analyzer evidence only and does not inspect component source.

The same-input post-fix audit reports 90 source-linked uncertain nominations,
seven source-backed applicable limitation questions, and 52 evidence-free
uncertain observations without nomination. See
`rollout-audit-fips-baseline.json` for the pinned pre-fix metrics and report
hash. The nomination decrease measures a rule change, not semantic recall.

## Resolution

Empty and evidence-free categories now remain explicit uncertain observations
without required-surface nomination. Static build, packaging, provider, crypto,
and TLS records nominate uncertain questions only from valid repository-relative
sources. Runtime, policy, and negative status becomes applicable only when the
same source-bearing record has FIPS-specific meaning; one record cannot borrow
another record's path. Every seeded surface remains unresolved with uncertain
claim support.

An independent fresh Sol review found and drove fixes for zero-fact negative
evidence, URI/drive paths, cross-record provenance borrowing, and generic
negative-field overclassification. The final 64-case focused matrix and
byte-identical audit reproduction passed. The stored audit remains 97
nominations (90 uncertain, seven applicable limitations) plus 52 explicit
unnominated uncertainties; this is planning-rule evidence only.
