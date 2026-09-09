# ADR-0026: Reuse Unchanged Component Generations by Deterministic Input Fingerprint

## Status

**Rejected 2026-09-09, same day as drafting.** Superseded by adoption of the
structured four-file layout as the actual objective. Retained as history because
it records a real analysis and a real misreading.

The rejection reason: this ADR treated "the structured route only pays off after
one full regeneration" as a disqualifying cost. It is not. Migrating to the
structured layout requires that regeneration regardless, so the precondition is
already accepted work, not an objection. Once a version is generated through the
structured route, its runs record the read and search observations that reuse
eligibility needs, and structured reuse becomes effective from the following
version onward. A second, weaker reuse mechanism on the legacy route would add a
parallel path to maintain while the layout it applies to is being retired.

The analysis below remains accurate on its own terms and would apply if the
layout migration were ever abandoned.

## Date

2026-09-09

## Context

The originating requirement was ordinary: do not pay to regenerate a component
whose inputs have not changed. The delivered structured-assembly mechanism
satisfies that requirement only inside its own route, and only between two runs
of that route.

Observed facts:

- Whole-component structured reuse (SC-11 through SC-15, SC-25) is eligible only
  when the *producing* run recorded complete read and search observations. No
  historical generation recorded them.
- Three independent runs across 92 component pairs and 184 source versions
  produced **zero verified historical reuse**
  ([completion record](../notes/structured-component-assembly-completion.md)).
  Missing historical model, read and search records were correctly not invented.
- The structured route cannot run without a hand-authored input file.
  `_load_pipeline_inputs` raises when `--structured-inputs` is absent
  (`lib/structured_component_synthesis.py:3013`), and the seam requires a record
  for every selected component (`:3134`). No deterministic producer for that
  file exists; the guard stands where a builder was never written.
- Default adoption of the structured route is HOLD pending the SC-24 live canary,
  which has not run and requires separate model and spending authorization.
- On the current default route, reuse is `arch_file.exists()` and nothing else
  (`lib/phases/architecture.py:200`). `--force` deletes and regenerates
  everything.

The operator therefore has two settings: regenerate nothing, or regenerate
everything. The requested middle — regenerate exactly what changed — does not
exist on any route that can run today.

## Decision

Adopt a deterministic input-fingerprint reuse mechanism on the current default
generation route. It is independent of structured synthesis, structured
publication, and the live-canary gate.

Each component generation records a declared input fingerprint. On a later run
the fingerprint is recomputed from current inputs and compared:

- **Equal** — retain the existing published bytes untouched and make no model
  call. Reuse does not rewrite, re-render, or reformat output.
- **Different or absent** — regenerate normally.

The fingerprint is a set of separately named input identities, not one opaque
hash, so a miss states which input moved:

- analyzer payload bytes (`.analyzer/component-architecture.json`);
- source identity — HEAD, tracked tree identity, and working-tree identity, via
  the existing `capture_source_snapshot` in `lib/structured_component_reuse.py`;
- the component's own `component-map.json` record;
- applicable overlay identities;
- platform configuration values that reach generation;
- route identity — generation route, prompt/skill identity, generator version,
  and requested model.

Records are stored at
`architecture/<version>/<component>/.generation/input-fingerprint.json` and are
committed. Sibling `.generation` artifacts are already tracked; only
`.generation/structured/` is gitignored.

Comparison is per named identity. A missing identity is a miss except under the
backfill rule below.

### Backfill

Fingerprints for the existing corpus are computed from the 149 committed
analyzer payloads without a checkout, and are labeled analyzer-derived. Source
tree identities are unavailable at backfill time and are not invented.

An analyzer-derived record is reuse-eligible only when a checkout is present, is
clean, and its HEAD equals the analyzer's recorded `commit_sha`. That condition
establishes that the working tree matches the commit the analyzer observed.
Otherwise the record is an explicit miss. A hit rewrites the record as a complete
observed fingerprint.

### Operator control

Fingerprint reuse is the default. An explicit documented option restores the
previous skip-if-exists behavior. `--force` keeps its current meaning.

## Trust model and what this does not claim

The trust boundary is the *declared input set*, not verified model behavior.

This mechanism does not verify what the generating model read or searched, makes
no producing-model eligibility claim, and is not evidence that a reused document
is correct. An input that is not declared cannot invalidate a record. Source
content is covered by tree identities, so the residual risk is undeclared
non-source inputs and undeclared configuration, not unnoticed source edits.

It is deliberately weaker than ADR-0025 structured reuse, which independently
verifies reads, searches, and producing-model identity. The two coexist:
structured reuse governs the structured route, fingerprint reuse governs the
default route. Neither is evidence for the other, and a fingerprint record never
satisfies a structured reuse eligibility check.

## Consequences

- The ordinary command gains the requested middle setting. Unchanged components
  cost nothing; changed components regenerate.
- The cost profile changes in both directions. A run that previously skipped every
  existing component may now spend model calls on components whose inputs moved.
  That is the intended behavior, and it is why the skip-if-exists opt-out is
  required rather than optional.
- The committed analyzer payloads make the mechanism useful on the existing
  corpus with no bootstrap regeneration.
- Structured publication, its schemas, its reuse path, and the live canary are
  unaffected. They remain opt-in and HOLD. Nothing is deleted.
- Rollback is the skip-if-exists option plus deleting fingerprint records. The
  records are inert to every other consumer.
- Enumerators, linters, packaging, diagram jobs, and `arch-query` must exclude
  the new file exactly as they exclude other `.generation` metadata. A
  fingerprint record is never a component or a fact.
