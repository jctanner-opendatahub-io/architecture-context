# Architecture Changes: llama-stack-provider-trustyai-garak

No table-level architecture fact changes were identified. The four routed gap categories were resolved as follows:

- **authentication**: The Authentication & Authorization table remains empty because this component is a Kubernetes Job adapter with no inbound endpoints. Authentication is relevant only for outbound integrations and is documented in the Secrets table (analyzer-owned).
- **http_endpoints**: The HTTP Endpoints table remains empty. Source inspection confirmed no FastAPI, Starlette, or other route definitions exist in this codebase. The adapter runs as a batch K8s Job, not an HTTP server.
- **services**: The Services table remains empty. No Kubernetes Service manifests or kustomize resources exist. The component runs as a K8s Job.
- **fips_compliance**: A new FIPS Compliance subsection was added under Security as agent-authored synthesis. This does not change any architecture table rows.

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
