# Structured publication test checklist

Prepared 2026-09-08 during authorized Codex-only work. This is a future test
assignment, not implemented behavior or an acceptance report. Follow the
[consolidated plan](../plans/structured-component-assembly-consolidated.md) and
[P4 review task](../tasks/pending/review-structured-publication-consumers.md).
P3 approval and the completed publication implementation remain prerequisites
for the P4 gate. Tests use temporary directories and stubbed model transports.

## Fixtures and expected results

| Case | Expected result | Requirements |
| --- | --- | --- |
| First successful publication | Three nested JSON files plus existing flat component Markdown; all refer to the same accepted inputs. | SC-02/17 |
| Replacement of existing accepted output | Each replaced file is written atomically; no silently mixed document/input generations. | SC-17 |
| Failure before and after each file replacement | Loader detects inconsistency; recovery selects a valid recoverable snapshot or reports a clear error. Never silently falls back to legacy because new files are invalid. | SC-17/18 |
| Failed or unresolved model run | Prior accepted output survives. An explicit deterministic-only route labels unavailable synthesis honestly; it never relabels a failed run as successful synthesis. | SC-10/17/22 |
| Markdown body changed but hash marker copied | Detect stale content and rerender using the single renderer without a model call. | SC-04/17/19 |
| Remove logs and private staging after successful publication | Original answers, proposal decisions, evidence identity, and reuse eligibility remain available from the published core. | SC-03/14/15/22 |
| Reuse into another version | Original response identity stays unchanged; target bindings and current validation are applied; zero synthesis calls. | SC-11/15 |
| JSON-only component and missing flat Markdown | Typed queries remain truthful about available files; raw Markdown operations fail clearly or use a documented recovery route. No nonexistent path is reported as available. | SC-18/19 |
| Mixed legacy and new components | Valid old/new formats coexist; invalid new input fails explicitly. Metadata is not interpreted as a component. | SC-18/21/23 |
| Canonical prefix, Praxis, and planned relationship fixtures | Names and citations survive; included does not become integrated, and planned does not become currently implemented. | SC-08/09/20 |
| Current renderer into arch-query | Exercise actual freshly rendered purpose/sections and RBAC variants, not just a static historical Markdown fixture. | SC-05/07/18 |
| Unsupported legacy fields or malformed FIPS parent | Explicit conversion error without silently losing data or rewriting historical artifacts. | SC-07/23 |
| Diagram generation failure | Accepted facts remain usable; derivative availability and identity accurately record the outcome. | SC-20 |

## Consumer checks

Source inspection identities are saved in
[consumer-inspection-inputs.json](../../logs/structured-component-assembly/20260908-codex-only/consumer-inspection-inputs.json).
These observations describe the inspected state, not new fixes.

| Consumer | Inspected gap or behavior | Required verification |
| --- | --- | --- |
| `lib/phases/collect.py` | Looks for legacy Markdown names and copies flat analyzer JSON. | Collect a validated accepted snapshot with core audit data, using canonical component names. |
| `scripts/collect_architectures.py` | Separate legacy checkout collector. | Exercise this entry point independently; updating the phase collector does not update this one. |
| `lib/phases/platform.py` | Selects directories using flat component Markdown. | Accepted components remain available to aggregation; stale/missing derivatives are handled explicitly. |
| `lib/phases/diagrams.py` | Flat Markdown enumeration intentionally includes PLATFORM, excludes INDEX/README. | Preserve platform diagram jobs while excluding metadata from component jobs; verify targeted and full runs. |
| `lib/version_index.py` | Existing navigation and integration-status behavior must survive. | Valid relative links, aliases, missing-document status, overlays, and planned/current relationships. |
| `scripts/lint_architecture_docs.py` | Flat Markdown checks exclude INDEX/PLATFORM/README. | Accepted snapshot checks detect broken core relationships while retaining component enumeration rules. |
| `internal/embeddeddata.Stage` | Copies allowed nested files without proving they form a complete matching snapshot. | Reject inconsistent packaged inputs before exposing a completed package. |
| `.github/workflows/release.yml` | Still shallow-copies flat files; differs from the Makefile stager. | Use the tested staging path; exercise release-equivalent packaging with nested accepted files and aliases. |

A shared accepted-snapshot loader should own integrity checks used by publication,
collection, and recovery; the test matrix should not justify duplicate validators.
Keep essential audit data within the agreed four core files, without adding a
fifth published run record. Detailed run logs may remain disposable.
