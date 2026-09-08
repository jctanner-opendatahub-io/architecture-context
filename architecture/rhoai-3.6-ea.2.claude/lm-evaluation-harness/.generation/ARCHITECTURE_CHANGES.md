# Architecture Changes: lm-evaluation-harness

No table-level changes are proposed for this component. The gap categories were investigated with the following outcomes:

- **authentication**: The component is a batch job with no inbound endpoints. Outbound authentication to model inference APIs is via environment-variable API keys, which are already documented in the Secrets table. The Authentication & Authorization table is correctly empty.
- **internal_dependencies**: No direct runtime dependencies on other RHOAI platform components were found. The `eval-hub-sdk` is a library dependency already captured in External Dependencies. The Internal Platform Dependencies table is correctly empty.
- **http_endpoints**: No HTTP server code found. The component is a batch job that acts only as an HTTP client. The HTTP Endpoints table is correctly empty.
- **services**: No Kubernetes Service manifests found. Consistent with the batch-job deployment model. The Services table is correctly empty.
- **fips_compliance**: FIPS Compliance subsection added under Security with evidence-backed analysis. This is a narrative addition, not a table row change.

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
