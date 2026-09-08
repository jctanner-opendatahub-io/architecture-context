# Architecture Surface Rollout Audit

Input fingerprint: `b8832da64d33f481fe168cc314e04d3b8ca45536d5510ff38cf56c57ee4390c3`.

This is a read-only audit of on-disk architecture documents and analyzer artifacts. Coverage enforcement remains warning-only and component-generation workers remain disabled.

## Corpus

| Measure | Count |
|---|---:|
| Canonical component documents | 9 |
| Project arch-analyzer artifacts | 9 |
| Eligible document/project-analyzer pairs | 9 |
| Unique repository identities | 9 |
| Duplicate repository artifacts | 0 |
| Documents without project arch-analyzer artifacts | 0 |
| Invalid analyzers | 0 |
| Excluded platform aliases | 0 |

## Generation cohorts

| Cohort | Component documents |
|---|---:|
| project-arch-analyzer-valid-pairs | 9 |
| project-arch-analyzer-invalid-pairs | 0 |
| no-project-arch-analyzer-artifact-unclassified | 0 |

Pre-3.6 documents used an external `architecture-analyzer`, and the LLM retained full control of each generated summary. They are an incomparable legacy cohort, not missing project `arch-analyzer` outputs. Documents from rolling or 3.6-era directories without a stored project analyzer remain unclassified.

## Telemetry boundary

| Sidecar state | Count |
|---|---:|
| missing-legacy-telemetry | 9 |

Missing legacy sidecars are counted as unavailable disposition/read/merge telemetry. They are not counted as behavioral omissions.

## Platforms

| Platform | Cohort | Documents | Project analyzers | Eligible | Without project analyzer | Invalid |
|---|---|---:|---:|---:|---:|---:|
| rhoai-3.6-ea.2 | 3.6-era-or-rolling | 9 | 9 | 9 | 0 | 0 |

## Analyzer evidence capability

| Behavioral evidence field state | Artifacts |
|---|---:|
| present-empty | 6 |
| present-records | 3 |
| Extracted behavioral records | 43 |

| Generic gap category | Candidate records |
|---|---:|
| authentication | 35 |
| authorization | 35 |
| configuration_lifecycle | 62 |
| egress | 26 |
| http_endpoints | 48 |
| integration_points | 36 |
| internal_dependencies | 44 |
| kubernetes_relationships | 46 |
| services | 28 |
| webhooks | 28 |

## Nominated surfaces

| Surface | Artifacts | Repositories | Exact candidates | Document path signal |
|---|---:|---:|---:|---:|
| authentication.admission-serving-identity | 3 | 3 | 3 | 2 |
| authentication.gateway-modes | 3 | 3 | 3 | 3 |
| authentication.metrics-enforcement | 3 | 3 | 3 | 2 |
| authentication.service-endpoints | 3 | 3 | 3 | 3 |
| compliance.runtime-fips | 9 | 9 | 9 | 8 |
| controller.named-resource-watches | 3 | 3 | 3 | 1 |
| dependencies.outbound-credentials | 8 | 8 | 8 | 7 |
| lifecycle.configuration-tls | 3 | 3 | 3 | 3 |
| network.workload-exposure | 3 | 3 | 3 | 3 |
| security.credential-wiring | 3 | 3 | 3 | 2 |

A document path signal only means that at least one exact analyzer candidate path appears in the Markdown. It is not semantic coverage.

## Runtime FIPS applicability

| Measure | Artifacts |
|---|---:|
| FIPS category records | 9 |
| Category records with facts | 0 |
| Category records without facts | 9 |
| Nominated runtime-FIPS surfaces | 9 |
| Nominated with category facts | 0 |
| Nominated without category facts but with a source signal | 9 |
| Nominated with uncertain applicability | 9 |
| Nominated with applicable status | 0 |
| Uncertain without nomination | 0 |

Static build, packaging, provider, crypto, or TLS signals nominate an uncertain question; they do not establish runtime compliance. Source-backed explicit runtime, policy, or negative signals make the question applicable while claim support remains uncertain. Evidence-free category records remain explicit uncertain observations without required-surface nomination.

## Representative review set

| Role | Artifact | Required surfaces | Repository |
|---|---|---:|---|
| operator | `rhoai-3.6-ea.2/models-as-a-service` | 4 | `https://github.com/red-hat-data-services/models-as-a-service.git` |
| operator | `rhoai-3.6-ea.2/odh-model-controller` | 4 | `https://github.com/red-hat-data-services/odh-model-controller.git` |
| operator | `rhoai-3.6-ea.2/rhods-operator` | 4 | `https://github.com/red-hat-data-services/rhods-operator.git` |
| service | `rhoai-3.6-ea.2/llm-d-routing-sidecar` | 2 | `https://github.com/llm-d/llm-d-routing-sidecar.git` |
| service | `rhoai-3.6-ea.2/NeMo-Guardrails` | 2 | `https://github.com/red-hat-data-services/NeMo-Guardrails.git` |
| service | `rhoai-3.6-ea.2/batch-gateway` | 2 | `https://github.com/red-hat-data-services/batch-gateway.git` |
| manifest | `rhoai-3.6-ea.2/distributed-workloads` | 2 | `https://github.com/red-hat-data-services/distributed-workloads.git` |
| manifest | `rhoai-3.6-ea.2/kube-auth-proxy` | 2 | `https://github.com/red-hat-data-services/kube-auth-proxy.git` |
| manifest | `rhoai-3.6-ea.2/rhoai-mcp` | 2 | `https://github.com/red-hat-data-services/rhoai-mcp.git` |

## Prioritized follow-up

2. **refresh-runtime-fips-applicability-evidence** — 9 concrete analyzer signal(s) nominate an uncertain runtime-FIPS question; 0 empty category record(s) retain uncertainty without nomination. Refresh analyzer evidence before judging runtime-FIPS warning quality or drawing runtime-compliance conclusions.

4. **define-legacy-sidecar-adoption** — 9 eligible legacy artifact(s) have no coverage sidecar. Keep enforcement warning-only and define an adoption boundary for newly generated versus legacy documents.

## Interpretation limits

- Before the 3.6 era, an external architecture-analyzer supplied context while the LLM retained full control of the generated summary. Those documents are a distinct legacy cohort, not missing project arch-analyzer outputs.
- A missing legacy coverage sidecar means disposition, read, merge, and validator telemetry is unavailable. It is not evidence that behavior is absent from a document.
- A document mention of an analyzer candidate path is a structural signal only. It does not establish that the document expresses the behavior.
- Stored analyzer artifacts without behavioral_evidence cannot be used to estimate the new extractor's recall or false-positive rate.
- Repeated platform copies are counted as artifact occurrences and also collapsed by repository identity for recurrence estimates.
- The audit reads no source checkout, pipeline log, agent transcript, or external service and does not modify generated architecture.
- A decrease in nominated surfaces after narrowing applicability does not demonstrate better semantic recall. It only measures a planning-rule change.
