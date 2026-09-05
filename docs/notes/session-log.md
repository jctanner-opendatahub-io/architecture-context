# Session Log

- 2026-09-04: Reviewed the `praxis-proxy` checkouts for RHOAI 3.6 EA.2. Added `grid` to `rhoai-3.6-ea.2.include_components` because it is a deployable Kubernetes operator with CRDs and Helm artifacts planned for 3.6 GA, despite not yet appearing in the EA catalog.
- 2026-09-04: Added per-`extra_repos` `name_prefix` support so Praxis repositories use descriptive checkout/component aliases while preserving canonical GitHub repository identities.
- 2026-09-04: Fixed targeted pipeline discovery to resolve per-organization checkout directories from platform configuration instead of passing the checkout root into provenance analysis.
- 2026-09-04: Propagated prefixed repository aliases through component-map keys, included-repository checkout resolution, static-analysis/analyzer paths, architecture generation metadata and documents, platform aggregation, and diagrams; added migration cleanup for prior raw-name artifacts.
- 2026-09-04: Fixed Rust analyzer extraction for Cargo members using `version.workspace = true`, discovered while analyzing `praxis-policy`; added a workspace-inheritance regression test.
- 2026-09-05: Fixed analyzer rendering to resolve canonical Git repository identities back to prefixed component-map keys, and made final architecture promotion enforce the component key from the output filename.
- 2026-09-04: Added a selectable Claude/Codex agent harness, using the existing Codex login and shared checked-in skills; completed and tested the fetch plus component-discovery vertical slice.
- 2026-09-04: Changed the Codex harness to consume the public turn notification stream, flush JSONL events during execution, show live event names, preserve terminal result telemetry, and propagate cancellation with useful diagnostics.
- 2026-09-04: Replaced raw Codex event-name output with readable streamed agent messages and concise command start/completion notices; retained full command output and protocol events only in JSONL logs.
- 2026-09-04: Regenerated the pre-sync RHOAI 3.6 EA.2 component discovery map from nine checkout roots, retaining canonical Praxis repository names under prefixed component keys; validation passed with 17 discovered components and 82 exclusions.
- 2026-09-04: Added temporary Codex discovery workspaces, explicit worker instructions, staged shared skills, and parent validation/atomic promotion after the discovery trace showed pipeline exploration and reuse of the prior Claude map. Verified valid, invalid, absent, and failed candidates with mocked agent execution; live output verification remains with the operator.
