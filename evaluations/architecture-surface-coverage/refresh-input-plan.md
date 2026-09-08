# Architecture Surface Analyzer Refresh Inputs

This manifest establishes identity and reproducibility for a future refresh. It is not a refreshed analyzer result and supplies no new behavioral-recall or generated-document-quality evidence.

## Boundary and status

Selected artifacts: **9**.

All selected source inputs are `unavailable-under-architecture-only-constraint`; regeneration was not run. No source checkout, pipeline log, network service, or live agent was used, and generated architecture was not modified.

Rollout-audit architecture fingerprint: `8a21066d05c68d202d07f02c5f43366c3debdd3b1935877f94b4b7928f0a1051`.
Selected comparison-input fingerprint: `1867e63fb2b72b2d2a938a2ffefa0dd77313964a30b61a9b4459a0dc4c38aa82`.

## Pinned cohort

| Stage | Role | Artifact | Source commit | Evidence | Refresh |
|---|---|---|---|---|---|
| rhods-operator-first | operator | `rhoai-3.6-ea.2/rhods-operator` | `4ada791819c522a4cda54f9029ab3e4056ed31ed` | field-absent | not-run-source-input-unavailable |
| representative-cohort | operator | `rhoai-3.6-ea.2.claude/models-as-a-service` | `b5bc98727a7e77dc427cb658de061745e3e04795` | field-absent | not-run-source-input-unavailable |
| representative-cohort | operator | `rhoai-3.6-ea.2.claude/odh-model-controller` | `8ff72dd9da97b577d1bc33a3cce6e1cd3e4b89b5` | field-absent | not-run-source-input-unavailable |
| representative-cohort | service | `rhoai-3.6-ea.1/llm-d-routing-sidecar` | `78051b86ff13c4511fb1c8c7def56e04b0850b67` | field-absent | not-run-source-input-unavailable |
| representative-cohort | service | `rhoai-3.6-ea.2.claude/NeMo-Guardrails` | `0740bef72f485e79aef20b237c5903c44ff838c1` | field-absent | not-run-source-input-unavailable |
| representative-cohort | service | `rhoai-3.6-ea.2.claude/batch-gateway` | `455370eac43cd9923754897e04339ad7e9377a04` | field-absent | not-run-source-input-unavailable |
| representative-cohort | manifest | `rhoai-3.6-ea.2.claude/distributed-workloads` | `8dd512b732609464f74d38b83b5c50cbf7151276` | field-absent | not-run-source-input-unavailable |
| representative-cohort | manifest | `rhoai-3.6-ea.2.claude/kube-auth-proxy` | `0969a391dd59a3df56e969f57ea83b6914a1c40a` | field-absent | not-run-source-input-unavailable |
| representative-cohort | manifest | `rhoai-3.6-ea.2.claude/rhoai-mcp` | `d3498af571e6f2551b4ef33a19f628506aaae456` | field-absent | not-run-source-input-unavailable |

## Unavailable metadata

The stored artifacts record analyzer version but do not record an exact analyzer source revision or configuration. Those values must be captured from the future rebuild and cannot be reconstructed from these files.

## Representatives outside this cohort

- `rhoai-3.6-ea.2.claude/odh-cli` (unknown): outside-requested-operator-service-manifest-cohort.
- `rhoai-3.6-ea.2.claude/llama-stack-provider-trustyai-garak` (unknown): outside-requested-operator-service-manifest-cohort.
- `rhoai-3.6-ea.2.claude/pipelines-components` (unknown): outside-requested-operator-service-manifest-cohort.

## Requirements before regeneration

- Provide each repository at its exact pinned commit; do not replace a missing commit with a branch, tag, or newer release.
- Record the rebuilt arch-analyzer revision and configuration before creating isolated refreshed outputs.
- Review conditional metrics enforcement and named watch predicates in rhods-operator before expanding beyond the first stage.
- Rerun the rollout audit against an explicitly selected refreshed input root while preserving these historical comparison files.
