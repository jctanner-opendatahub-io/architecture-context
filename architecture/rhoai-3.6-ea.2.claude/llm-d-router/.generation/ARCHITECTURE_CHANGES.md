# Architecture Changes: llm-d-router

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | authentication | Metrics endpoint (EPP) :: HTTP | * | <empty> | <empty> | EPP metrics endpoint supports optional client-certificate authentication and authorization via controller-runtime flags | pkg/epp/server/options.go:122-124 |
