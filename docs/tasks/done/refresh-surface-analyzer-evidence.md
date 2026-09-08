# Task: Refresh Surface Analyzer Evidence

Status: complete on 2026-09-05. The operator identified the platform checkout
roots and authorized their use. All nine working trees were clean, their
origins matched the manifest, and their HEADs equaled the required pinned
commits.

Follow step 3 of the [plan](../../plans/architecture-surface-coverage.md).
Rebuild the analyzer, refresh pinned eligible 3.6-era/rolling inputs starting
with rhods-operator, and rerun the audit. Preserve historical artifacts and
record input/output fingerprints and unavailable inputs.

Acceptance: reviewed behavioral facts and reproducible audit for the refreshed
cohort. External-analyzer and unclassified cohorts stay distinct; absent legacy
sidecars remain unavailable telemetry, not omissions. No live agents required.

## Stored-input preflight

The reproducible [refresh input manifest](../../../evaluations/architecture-surface-coverage/refresh-input-plan.md)
pins nine inputs: `rhods-operator` first, then three total representatives for
each of the operator, service, and manifest roles. It records the repository and
exact 40-character source commit, fingerprints the stored analyzer outputs and
comparison document, and excludes three unknown-role representatives from this
cohort.

The stored analyzer artifacts use version `0.1.0-dev`, lack
`behavioral_evidence`, and do not record an exact analyzer revision or
configuration. The original architecture-only preflight therefore recorded
regeneration as `not-run-source-input-unavailable` and prohibited revision
substitution. Source access is now available; preserve that preflight record as
the before-state while recording the new analyzer identity and isolated outputs.

The completed refresh preserved that preflight record as the before-state and
recorded the new analyzer identity, configuration, and isolated outputs without
overwriting historical architecture.

## Refresh progress

- Verified all nine checkout origins, clean worktrees, and exact HEAD commits.
- Built the analyzer from repository base `39209078` plus source-diff SHA-256
  `6376b9ffdf60420986f5d34b5f55ed145cf55eb85587a9028fe52fefa6a38c84`;
  the binary SHA-256 is
  `d13d83d5229a6a708507a8932353ce10fb281b1af8c4fe125a94d2a8d34106b8`.
- Refreshed `rhods-operator` first. Source review confirmed conditional metrics
  authentication/authorization at `cmd/main.go:485-500` and the
  `models-as-a-service` and `kuadrant-system` Namespace watches at
  `internal/controller/services/auth/auth_controller.go:63-76`.
- The first cohort run exposed an encoder defect: six current zero-record
  outputs omitted `behavioral_evidence` and appeared legacy to the audit. The
  fix now emits an empty array while retaining legacy decode compatibility.
- The final isolated run completed all extract, render, and schema phases: nine
  valid analyzer artifacts, 157 schemas, 43 behavioral records, no generated
  architecture changes, and no live agents. Three Go operators contain records;
  the six remaining artifacts explicitly contain an empty list.
- The recorded refreshed audit pairs all nine documents and analyzers. It
  reports three source-observed records and 40 precise unresolved records, and
  no longer recommends refreshing freshly generated zero-record artifacts. Both
  JSON and Markdown reproduce byte-for-byte from the retained structured
  outputs and hash-pinned comparison documents.

Independent review accepted the refresh and encoder correction with no blocking
findings. The reviewer independently matched all nine checkout origins, exact
HEADs, and clean states; recomputed the analyzer source and diff fingerprints;
rebuilt a byte-identical analyzer binary; checked the three observed source
facts and all 40 unresolved records; reproduced both audit files byte-for-byte;
and passed the focused Python and full arch-analyzer Go tests. The optional
independent full `rhods-operator` static-analysis rerun was stopped after several
quiet minutes, so the reviewer did not independently regenerate the 130-schema
bundle or render hashes. The retained structured outputs, source facts, binary,
provenance fingerprints, and audit reproduction were independently verified.
