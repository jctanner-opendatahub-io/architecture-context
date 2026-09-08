# Architecture Changes: data-science-pipelines

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | authentication | Pipeline API :: All | * | <empty> | <empty> | Apiserver uses dual authenticator chain: HTTPHeaderAuthenticator for kubeflow-userid header and TokenReviewAuthenticator for bearer token validation via Kubernetes TokenReview API | backend/src/apiserver/auth/auth.go:35-44, backend/src/apiserver/auth/authenticator_token_review.go:77-98 |
| delete | authentication | HTTP API :: All | * | <empty> | <empty> | Row was derived from sdk/python/kfp/client/auth_test.py:43, a Python SDK test file mock that patches builtins.input, not a production API endpoint; the actual apiserver authentication is bearer token + HTTP header identity | backend/src/apiserver/auth/auth.go:35-44 |
