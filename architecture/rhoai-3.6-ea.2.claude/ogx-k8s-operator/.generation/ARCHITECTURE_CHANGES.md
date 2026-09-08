# Architecture Changes: ogx-k8s-operator

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | authentication | Metrics endpoint :: GET | * | <empty> | <empty> | Metrics endpoint uses controller-runtime WithAuthenticationAndAuthorization filter for TokenReview and SubjectAccessReview when --metrics-cert-path is set | main.go:265-276 |
