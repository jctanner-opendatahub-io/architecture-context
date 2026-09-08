# Architecture Surface Rollout Audit

Input fingerprint: `8a21066d05c68d202d07f02c5f43366c3debdd3b1935877f94b4b7928f0a1051`.

This is a read-only audit of on-disk architecture documents and analyzer artifacts. Coverage enforcement remains warning-only and component-generation workers remain disabled.

## Corpus

| Measure | Count |
|---|---:|
| Canonical component documents | 901 |
| Project arch-analyzer artifacts | 149 |
| Eligible document/project-analyzer pairs | 149 |
| Unique repository identities | 80 |
| Duplicate repository artifacts | 69 |
| Documents without project arch-analyzer artifacts | 752 |
| Invalid analyzers | 0 |
| Excluded platform aliases | 5 |

## Generation cohorts

| Cohort | Component documents |
|---|---:|
| project-arch-analyzer-valid-pairs | 149 |
| project-arch-analyzer-invalid-pairs | 0 |
| external-architecture-analyzer-full-llm | 654 |
| no-project-arch-analyzer-artifact-unclassified | 98 |

Pre-3.6 documents used an external `architecture-analyzer`, and the LLM retained full control of each generated summary. They are an incomparable legacy cohort, not missing project `arch-analyzer` outputs. Documents from rolling or 3.6-era directories without a stored project analyzer remain unclassified.

## Telemetry boundary

| Sidecar state | Count |
|---|---:|
| missing-legacy-telemetry | 149 |

Missing legacy sidecars are counted as unavailable disposition/read/merge telemetry. They are not counted as behavioral omissions.

## Platforms

| Platform | Cohort | Documents | Project analyzers | Eligible | Without project analyzer | Invalid |
|---|---|---:|---:|---:|---:|---:|
| odh | 3.6-era-or-rolling | 0 | 0 | 0 | 0 | 0 |
| rhoai-2.10 | legacy-external-analyzer-full-llm | 13 | 0 | 0 | 13 | 0 |
| rhoai-2.11 | legacy-external-analyzer-full-llm | 13 | 0 | 0 | 13 | 0 |
| rhoai-2.12 | legacy-external-analyzer-full-llm | 13 | 0 | 0 | 13 | 0 |
| rhoai-2.13 | legacy-external-analyzer-full-llm | 13 | 0 | 0 | 13 | 0 |
| rhoai-2.14 | legacy-external-analyzer-full-llm | 14 | 0 | 0 | 14 | 0 |
| rhoai-2.15 | legacy-external-analyzer-full-llm | 14 | 0 | 0 | 14 | 0 |
| rhoai-2.16 | legacy-external-analyzer-full-llm | 14 | 0 | 0 | 14 | 0 |
| rhoai-2.17 | legacy-external-analyzer-full-llm | 14 | 0 | 0 | 14 | 0 |
| rhoai-2.19 | legacy-external-analyzer-full-llm | 36 | 0 | 0 | 36 | 0 |
| rhoai-2.24 | legacy-external-analyzer-full-llm | 45 | 0 | 0 | 45 | 0 |
| rhoai-2.25 | legacy-external-analyzer-full-llm | 43 | 0 | 0 | 43 | 0 |
| rhoai-2.6 | legacy-external-analyzer-full-llm | 22 | 0 | 0 | 22 | 0 |
| rhoai-2.7 | legacy-external-analyzer-full-llm | 10 | 0 | 0 | 10 | 0 |
| rhoai-2.8 | legacy-external-analyzer-full-llm | 12 | 0 | 0 | 12 | 0 |
| rhoai-2.9 | legacy-external-analyzer-full-llm | 12 | 0 | 0 | 12 | 0 |
| rhoai-3.0 | legacy-external-analyzer-full-llm | 34 | 0 | 0 | 34 | 0 |
| rhoai-3.2 | legacy-external-analyzer-full-llm | 40 | 0 | 0 | 40 | 0 |
| rhoai-3.3 | legacy-external-analyzer-full-llm | 44 | 0 | 0 | 44 | 0 |
| rhoai-3.4 | legacy-external-analyzer-full-llm | 57 | 0 | 0 | 57 | 0 |
| rhoai-3.4-ea.1 | legacy-external-analyzer-full-llm | 0 | 0 | 0 | 0 | 0 |
| rhoai-3.4-ea.2 | legacy-external-analyzer-full-llm | 0 | 0 | 0 | 0 | 0 |
| rhoai-3.5 | legacy-external-analyzer-full-llm | 69 | 0 | 0 | 69 | 0 |
| rhoai-3.5-ea.1 | legacy-external-analyzer-full-llm | 57 | 0 | 0 | 57 | 0 |
| rhoai-3.5-ea.2 | legacy-external-analyzer-full-llm | 65 | 0 | 0 | 65 | 0 |
| rhoai-3.6-ea.1 | 3.6-era-or-rolling | 72 | 71 | 71 | 1 | 0 |
| rhoai-3.6-ea.2 | 3.6-era-or-rolling | 1 | 1 | 1 | 0 | 0 |
| rhoai-3.6-ea.2.claude | 3.6-era-or-rolling | 78 | 77 | 77 | 1 | 0 |
| rhoai.next | 3.6-era-or-rolling | 96 | 0 | 0 | 96 | 0 |

## Analyzer evidence capability

| Behavioral evidence field state | Artifacts |
|---|---:|
| field-absent | 149 |
| Extracted behavioral records | 0 |

| Generic gap category | Candidate records |
|---|---:|
| authentication | 294 |
| authorization | 605 |
| configuration_lifecycle | 819 |
| egress | 330 |
| grpc_services | 45 |
| http_endpoints | 338 |
| integration_points | 185 |
| internal_dependencies | 629 |
| kubernetes_relationships | 544 |
| services | 323 |
| webhooks | 218 |

## Nominated surfaces

| Surface | Artifacts | Repositories | Exact candidates | Document path signal |
|---|---:|---:|---:|---:|
| authentication.admission-serving-identity | 34 | 17 | 34 | 27 |
| authentication.gateway-modes | 38 | 20 | 38 | 37 |
| authentication.metrics-enforcement | 76 | 41 | 42 | 32 |
| authentication.service-endpoints | 34 | 18 | 34 | 26 |
| compliance.runtime-fips | 97 | 54 | 97 | 92 |
| controller.named-resource-watches | 9 | 4 | 9 | 7 |
| dependencies.outbound-credentials | 96 | 51 | 96 | 85 |
| lifecycle.configuration-tls | 76 | 41 | 76 | 75 |
| network.workload-exposure | 8 | 4 | 8 | 8 |
| security.credential-wiring | 6 | 3 | 6 | 4 |

A document path signal only means that at least one exact analyzer candidate path appears in the Markdown. It is not semantic coverage.

## Runtime FIPS applicability

| Measure | Artifacts |
|---|---:|
| FIPS category records | 149 |
| Category records with facts | 11 |
| Category records without facts | 138 |
| Nominated runtime-FIPS surfaces | 97 |
| Nominated with category facts | 11 |
| Nominated without category facts but with a source signal | 86 |
| Nominated with uncertain applicability | 90 |
| Nominated with applicable status | 7 |
| Uncertain without nomination | 52 |

Static build, packaging, provider, crypto, or TLS signals nominate an uncertain question; they do not establish runtime compliance. Source-backed explicit runtime, policy, or negative signals make the question applicable while claim support remains uncertain. Evidence-free category records remain explicit uncertain observations without required-surface nomination.

## Same-input planning-rule delta

| Measure | Before | After | Delta |
|---|---:|---:|---:|
| required_surface_occurrences | 314 | 262 | -52 |
| runtime_fips_repository_occurrences | 80 | 54 | -26 |
| runtime_fips_surface_occurrences | 149 | 97 | -52 |
| runtime_fips_without_category_facts | 138 | 86 | -52 |
| surface_occurrences | 526 | 474 | -52 |

The delta isolates the FIPS planning-rule change on identical on-disk inputs. Fewer nominations do not demonstrate improved semantic recall.

## Representative review set

| Role | Artifact | Required surfaces | Repository |
|---|---|---:|---|
| operator | `rhoai-3.6-ea.2.claude/models-as-a-service` | 4 | `https://github.com/red-hat-data-services/models-as-a-service.git` |
| operator | `rhoai-3.6-ea.2.claude/odh-model-controller` | 4 | `https://github.com/red-hat-data-services/odh-model-controller.git` |
| operator | `rhoai-3.6-ea.2/rhods-operator` | 4 | `https://github.com/red-hat-data-services/rhods-operator.git` |
| service | `rhoai-3.6-ea.1/llm-d-routing-sidecar` | 2 | `https://github.com/llm-d/llm-d-routing-sidecar.git` |
| service | `rhoai-3.6-ea.2.claude/NeMo-Guardrails` | 2 | `https://github.com/red-hat-data-services/NeMo-Guardrails.git` |
| service | `rhoai-3.6-ea.2.claude/batch-gateway` | 2 | `https://github.com/red-hat-data-services/batch-gateway.git` |
| manifest | `rhoai-3.6-ea.2.claude/distributed-workloads` | 2 | `https://github.com/red-hat-data-services/distributed-workloads.git` |
| manifest | `rhoai-3.6-ea.2.claude/kube-auth-proxy` | 2 | `https://github.com/red-hat-data-services/kube-auth-proxy.git` |
| manifest | `rhoai-3.6-ea.2.claude/rhoai-mcp` | 2 | `https://github.com/red-hat-data-services/rhoai-mcp.git` |
| unknown | `rhoai-3.6-ea.2.claude/odh-cli` | 1 | `https://github.com/red-hat-data-services/odh-cli.git` |
| unknown | `rhoai-3.6-ea.2.claude/llama-stack-provider-trustyai-garak` | 1 | `https://github.com/red-hat-data-services/llama-stack-provider-trustyai-garak.git` |
| unknown | `rhoai-3.6-ea.2.claude/pipelines-components` | 1 | `https://github.com/red-hat-data-services/pipelines-components.git` |

## Prioritized follow-up

1. **refresh-stored-behavioral-evidence** — 149 analyzer artifact(s) do not expose a usable behavioral_evidence field. Refresh stored analyzer artifacts before using this corpus to judge behavioral-extractor warning quality.

2. **refresh-runtime-fips-applicability-evidence** — 90 concrete analyzer signal(s) nominate an uncertain runtime-FIPS question; 52 empty category record(s) retain uncertainty without nomination. Refresh analyzer evidence before judging runtime-FIPS warning quality or drawing runtime-compliance conclusions.

3. **improve-role-classification** — 27 eligible artifact(s) retain the unknown role. Add deterministic role signals before expanding role-specific surface rules.

4. **define-legacy-sidecar-adoption** — 149 eligible legacy artifact(s) have no coverage sidecar. Keep enforcement warning-only and define an adoption boundary for newly generated versus legacy documents.

## Interpretation limits

- Before the 3.6 era, an external architecture-analyzer supplied context while the LLM retained full control of the generated summary. Those documents are a distinct legacy cohort, not missing project arch-analyzer outputs.
- A missing legacy coverage sidecar means disposition, read, merge, and validator telemetry is unavailable. It is not evidence that behavior is absent from a document.
- A document mention of an analyzer candidate path is a structural signal only. It does not establish that the document expresses the behavior.
- Stored analyzer artifacts without behavioral_evidence cannot be used to estimate the new extractor's recall or false-positive rate.
- Repeated platform copies are counted as artifact occurrences and also collapsed by repository identity for recurrence estimates.
- The audit reads no source checkout, pipeline log, agent transcript, or external service and does not modify generated architecture.
- A decrease in nominated surfaces after narrowing applicability does not demonstrate better semantic recall. It only measures a planning-rule change.
