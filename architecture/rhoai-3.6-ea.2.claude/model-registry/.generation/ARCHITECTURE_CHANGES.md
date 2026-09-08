# Architecture Changes: model-registry

## Change Record

No table-level changes to analyzer-owned architecture tables are proposed. The gaps were resolved as follows:

- **grpc_services**: Confirmed empty — no `.proto` files or gRPC service registration found in the repository. The empty gRPC Services table is correct.
- **authentication**: The existing 7 authentication rows are complete and accurate. BFF auth configuration verified via `clients/ui/bff/cmd/main.go:56-58`.
- **integration_points**: The existing 14 integration point rows are complete. No additional platform integration points identified.
- **internal_dependencies**: The 3 KServe InferenceService entries correctly represent the platform-level internal dependencies. Kubernetes API resource interactions (SubjectAccessReview, ConfigMap, etc.) are integration points, not platform dependencies.
- **fips_compliance**: New FIPS Compliance subsection added under Security (synthesis section). No table rows changed.

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
