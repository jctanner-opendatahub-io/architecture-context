# Architecture Changes: kube-auth-proxy

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| update | http_endpoints | GET :: /ping | Auth | Unknown | None | Health check endpoint is registered in pre-auth chain and does not require authentication | oauthproxy.go:396-408 |
| add | http_endpoints | GET :: /oauth2/sign_in | * | <empty> | <empty> | Sign-in page endpoint registered on proxy prefix subrouter | oauthproxy.go:370 |
| add | http_endpoints | GET :: /oauth2/start | * | <empty> | <empty> | OAuth2 authorization code flow initiation endpoint | oauthproxy.go:371 |
| add | http_endpoints | GET :: /oauth2/callback | * | <empty> | <empty> | OAuth2 authorization code callback endpoint | oauthproxy.go:372 |
| add | http_endpoints | GET :: /oauth2/sign_out | * | <empty> | <empty> | Session termination endpoint with session chain middleware | oauthproxy.go:379 |
| add | http_endpoints | GET :: /oauth2/userinfo | * | <empty> | <empty> | Authenticated user information endpoint with session chain middleware | oauthproxy.go:378 |
| add | http_endpoints | GET :: /oauth2/auth | * | <empty> | <empty> | Auth-only verification endpoint for ext_authz integration | oauthproxy.go:355 |
| add | http_endpoints | GET :: /robots.txt | * | <empty> | <empty> | Robots exclusion standard endpoint registered on root router | oauthproxy.go:350 |
| add | authentication | Proxied upstream requests :: All | * | <empty> | <empty> | Core authentication enforcement for all proxied requests via middleware chain | oauthproxy.go:229-234, oauthproxy.go:363 |
| add | egress | Redis/Valkey | * | <empty> | <empty> | Redis client for distributed session storage with optional TLS | pkg/sessions/redis/redis_store.go:160-178 |
| add | egress | OpenShift OAuth server | * | <empty> | <empty> | OAuth2 authorization and token exchange with OpenShift identity provider | providers/openshift.go:34-35, providers/openshift.go:70 |
| update | egress | Kubernetes API | Purpose | Kubernetes resource operations | Kubernetes resource operations and TokenReview validation | TokenReview API is the primary K8s integration for ServiceAccount token validation | pkg/authentication/k8s/tokenreview.go:227, main.go:62 |
