# Architecture Changes: workbenches

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | services | workspaces-webhook-service | * | <empty> | <empty> | Kubernetes Service manifest defines webhook service on port 443 | workspaces/controller/manifests/kustomize/base/webhook/service.yaml:1-13 |
| add | services | workspaces-backend | * | <empty> | <empty> | Kubernetes Service manifest defines backend API service on port 4000 | workspaces/backend/manifests/kustomize/base/service.yaml:1-10 |
| add | services | workspaces-frontend | * | <empty> | <empty> | Kubernetes Service manifest defines frontend UI service on port 8080 | workspaces/frontend/manifests/kustomize/base/service.yaml:1-9 |
| add | services | workspaces-controller-metrics-service | * | <empty> | <empty> | Kubernetes Service manifest defines controller metrics service on port 8080 | workspaces/controller/manifests/kustomize/components/prometheus/service.yaml:1-14 |
| add | authentication | Backend API :: All | * | <empty> | <empty> | Backend uses request header authentication with Kubernetes SubjectAccessReview authorization for all API endpoints | workspaces/backend/internal/auth/authentication.go:31-81, workspaces/backend/internal/auth/authorization.go:41-74, workspaces/backend/api/auth.go:33-69 |
