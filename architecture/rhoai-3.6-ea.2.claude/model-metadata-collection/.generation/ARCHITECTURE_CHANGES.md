# Architecture Changes: model-metadata-collection

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | integration_points | HuggingFace API :: REST | * | <empty> | <empty> | model-extractor CLI fetches model collections and cards via HuggingFace REST API at build time | internal/huggingface/client.go:57 |
| add | integration_points | GitHub API :: REST | * | <empty> | <empty> | model-extractor CLI fetches agent metadata and READMEs via GitHub REST API at build time | internal/github/client.go:79 |
| add | integration_points | OCI Container Registries :: OCI Registry | * | <empty> | <empty> | model-extractor CLI inspects container image manifests via containers/image library at build time | internal/registry/registry.go:79 |
| add | authentication | HuggingFace API :: GET | * | <empty> | <empty> | HuggingFace client uses optional Bearer token from HF_TOKEN env var for authenticated API requests | internal/huggingface/client.go:36-51 |
| add | authentication | GitHub API :: GET | * | <empty> | <empty> | GitHub client uses optional Bearer token from GITHUB_TOKEN env var for authenticated API requests | internal/github/client.go:30-46 |
| add | authentication | OCI Container Registries :: GET | * | <empty> | <empty> | Registry access uses containers/image credential chain for container registry authentication | internal/registry/registry.go:14-15 |
