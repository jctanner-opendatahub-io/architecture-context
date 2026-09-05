# Bug: Surface Inventory Nominates Empty FIPS Category

## Status

Open. Discovered by the 2026-09-05 on-disk architecture rollout audit.

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
