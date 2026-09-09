# ADR-0025: Migrate through validated structured component snapshots

## Status

Proposed and implemented for independent P4 review. Default/live adoption
remains on hold pending the separate P5 review and rollout decision.

## Context

Component facts now have an accepted JSON model, but existing releases and
consumers use flat Markdown and legacy analyzer JSON. Publication must survive
process interruption, retain synthesis/evidence provenance after disposable
logs are deleted, and support mixed version directories without silently
discarding legacy-only fields.

## Decision

New publication writes four core files: nested `analyzer.json`,
`synthesis.json`, and authoritative `document.json`, plus the existing flat
`<component>.md`. Document schema `1.1.0` binds the exact analyzer/synthesis
bytes and retains the validated P3 run record and current/original evidence
bundles. Reused `synthesis.json` bytes remain unchanged. The Markdown marker
binds the exact document bytes, renderer identity, and body hash; the document
does not hash Markdown, so authority and derivative hashes are noncircular.

Publication stages per-file `.next` bytes, retains per-file `.previous` bytes,
and replaces each destination atomically while holding a component lock. On
restart, the document's sibling hashes select either a complete previous or new
authority and Markdown is rerendered locally. These temporary files are not a
published manifest or transaction subsystem. A wholly failed synthesis cannot
publish. Deterministic-only publication is separately labeled, records zero
model calls and unavailable response/dependency provenance, and is not reusable
as a producing-model snapshot.

The Python producer and reuse path performs complete producer validation,
including recomputing raw-response identities and producing-model eligibility.
The Go query and release-staging consumers validate schemas, exact published
bytes, document reconstruction, evidence revisions, and cross-artifact hash and
identity bindings. They do not independently recompute raw-response identities
or producing-model eligibility; those are producer assertions at the Go
boundary and are rechecked before Python reuse.

A valid published authority can serve typed queries without Markdown; a present
stale derivative is an error. Complete repository and release packages require
all four core files, including Markdown, so staging rejects a JSON-only snapshot.
Any invalid new-format component fails the whole version load. Legacy fallback
is used only when no structured document exists. Metadata and recovery files
are never components or diagram jobs. Structured component diagrams move under
`<component>/diagrams/`; platform and legacy diagram paths stay unchanged.
The structured path renders only through `arch-analyzer`; `arch-doc` remains a
legacy section assembler and is not a second accepted-document renderer.

Legacy conversion refuses nonempty network policies, platform webhook links,
richer Dockerfile/webhook fields, and malformed or ambiguous FIPS evidence
until a reviewed accepted schema represents them. Historical outputs are not
bulk rewritten and missing telemetry or original responses are never invented.
The platform-level `.generation/structured/preflight-diagnostic.json` is
failure-only private metadata: it is gitignored, excluded from every consumer
enumerator and published core, and may be removed after failure triage. It never
represents a component or a producing model call.

## Rollback

Before default adoption, disable the opt-in structured synthesis route; already
published valid snapshots remain readable alongside legacy components. A
repository rollback restores the previous four files from version control.
Interrupted local publication uses its per-file recovery bytes. Do not delete
only `document.json` to force legacy fallback: an inconsistent new-format
snapshot is an error by design.

## Consequences

Release staging and query loading fail early on mixed generations. Renderer-only
refreshes need no model call. Coverage remains warning-only, component workers
remain disabled, and live/default adoption requires separate evidence and
authorization. The original rejected canary remains rejected.
