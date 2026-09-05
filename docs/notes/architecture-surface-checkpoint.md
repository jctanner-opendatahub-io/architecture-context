# Architecture Surface Worktree Checkpoint

Recorded 2026-09-05 before the FIPS applicability follow-up.

## Base and local checkpoint

- Branch: `regen/praxis-repos`
- Base HEAD: `28728163dde09c1007e0c2cb6d9e794cd3c06539`
- Ignored checkpoint directory:
  `tmp/checkpoints/architecture-surface-coverage-20260905/`
- The checkpoint directory contains exact path manifests, binary Git patches,
  untracked-file archives, a two-document comparison-input archive, and SHA-256
  checksums. It is a local recovery artifact and is not proposed for commit.

Restore tracked changes against the recorded base with
`git apply all-tracked.patch`. Restore an untracked group from the repository
root with `tar -xzf ARCHIVE`. The filtered surface patch excludes mixed tracked
files; use the complete patch when restoring the exact integrated state.

## Inventory

The checkpoint records 25 modified tracked paths and 2,028 untracked paths.

Eighteen tracked paths contain only architecture-surface implementation or
tests. Their exact list is in `surface-pure-tracked.txt`:

- `.claude/skills/repo-to-architecture-summary/SKILL.md`
- `lib/phases/architecture.py`
- `src/arch-analyzer/internal/extractor/evidence.go`
- `src/arch-analyzer/internal/extractor/evidence_test.go`
- `src/arch-analyzer/internal/extractor/extractor.go`
- `src/arch-analyzer/internal/gosource/gosource.go`
- `src/arch-analyzer/internal/model/document.go`
- `src/arch-analyzer/internal/model/input.go`
- `src/arch-analyzer/internal/model/input_test.go`
- `src/arch-analyzer/internal/normalize/normalize.go`
- `src/arch-analyzer/internal/normalize/normalize_test.go`
- `src/arch-analyzer/internal/renderer/evidence.go`
- `src/arch-analyzer/internal/renderer/markdown.go`
- `src/arch-analyzer/internal/renderer/markdown_test.go`
- `src/arch-analyzer/schema/component-architecture.schema.json`
- `tests/test_arch_analyzer_category_coverage.py`
- `tests/test_architecture_phase.py`
- `tests/test_repo_summary_skill.py`

Seven tracked paths are mixed and require whole-file review or hunk selection:

| Path | Mixed concerns |
|---|---|
| `PLAN.md` | Surface ledger plus other repository milestones. |
| `docs/notes/session-log.md` | Surface, Codex telemetry, and preceding session records. |
| `lib/agent_runner.py` | Surface planning-input controls and Claude read observation plus Codex postprocessing failure preservation. |
| `lib/codex_agent.py` | Codex enum/read telemetry and skill resolution plus immutable surface-planning inputs. |
| `tests/test_agent_runner.py` | Surface input/read tests and harness telemetry assertions. |
| `tests/test_codex_agent.py` | Codex telemetry regressions and surface validator/input-integrity integration. |
| `uv.lock` | Previously declared Codex harness dependency resolved into the lock file. |

The 50 planned untracked source/document paths are split into 48 surface paths
and two completed Codex telemetry ledger records. Their exact lists are in
`surface-untracked.txt` and `separate-codex-telemetry-untracked.txt`.

The following are excluded from the proposed commit scope:

- `TEST.sh`, whose ownership and purpose are not established.
- 1,977 files below `architecture/rhoai-3.6-ea.2/` and
  `architecture/rhoai-3.6-ea.2.claude/`, totaling approximately 98 MiB. They
  are generated/user-held comparison outputs and were not modified by the
  audit. The exact list is in `generated-architecture-untracked.txt`.
- The checkpoint artifacts themselves below ignored `tmp/`.

The two SHA-pinned `rhods-operator.md` comparison inputs have a separate local
archive. Archiving them does not add or authorize the generated trees.

## Proposed commit scope

Prepare one integrated commit containing the 25 tracked modifications and the
50 planned untracked paths. This keeps the completed Codex telemetry prerequisite
with the surface validation that consumes it, while retaining separate bug/task
records for review. Proposed title:

`feat: add architecture surface coverage and audit`

The user approved this exact scope on 2026-09-05. The index was verified to
contain exactly the 75 approved paths. `TEST.sh`, both generated architecture
directories, and the ignored checkpoint remained unstaged. The staged diff,
focused Python suite, repository preservation target, all Go tests/lint, scoped
Ruff, and both report-reproduction checks were inspected before committing.
