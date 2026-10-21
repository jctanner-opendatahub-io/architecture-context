# Platform Architecture — breadboard

- Components analyzed: 5/5
- Complete: true

- Stage: analyze
- Stage: generate
- Stage: collect
- Stage: platform

## breadboard

Integration and deployment repository for an AI-native software engineering platform combining a Python pipeline, dashboards, and a resettable local Kubernetes service stack.

**Concerns:**

- No authentication middleware on dashboard HTTP APIs; dashboards are effectively unauthenticated behind local ingress.
- Broad pipeline-orchestrator RBAC (pods/exec, secrets) shared across markovd, pipeline-agent, and pipeline-dashboard.
- Secrets and admin passwords passed via environment variables; emulator admin passwords in manifests/env risk leakage.
- Large single-namespace deployment with mixed trust levels (emulators, runners, agent sandbox) increases blast radius.
- No high-availability or supply-chain evidence extracted by the analyzer; single-instance deployments assumed.

## jira-emulator

A lightweight Jira REST API emulator for offline development, testing, CI/CD, and Claude AI integration via MCP.

**Concerns:**

- Default permissive AUTH_MODE with seeded admin:admin credentials is insecure if exposed beyond local development
- SQLite single-file database limits concurrency and provides no high-availability story
- Analyzer found no TLS termination, ingress, or FIPS posture defined in-repo; encryption is configurable/external
- Two declared dependencies (e.g. honcho, mypy) are unused in shipped source per analyzer import analysis

## github-emulator

A self-contained FastAPI service that emulates the GitHub REST, GraphQL, and Git transport APIs for integration testing.

**Concerns:**

- Default seeded admin credentials (admin/admin) and default token make production exposure risky; intended for testing only.
- SQLite single-file storage limits concurrency and horizontal scaling; no HA story observed.
- Encryption is configurable/deployment-dependent (Caddy TLS) rather than enforced in-app.
- Large duplicated API surface (381 endpoints) across many route modules increases maintenance burden.
- Repository and git behavior is split between API routes and git helpers with some duplicated responsibilities, noted in project guidance.

## gitlab-emulator

A self-contained GitLab API emulator for integration testing of clients, glab CLI workflows, and automation without touching real GitLab.

**Concerns:**

- Project is an in-progress rename/scaffold of github_emulator; GitLab-specific routes and schemas are incomplete per STATUS.md.
- Default secrets and admin credentials (change-me-in-production, admin/admin) are insecure if deployed beyond testing.
- Very large flat REST surface (~550 routes) in a single service with no HA or ingress evidence.
- SQLite storage limits concurrency and scale, acceptable only for an emulator.

## entra-id-emulator

A lightweight Entra ID (Azure AD) emulator providing OIDC/OAuth2 endpoints and a management API for local development and testing.

**Concerns:**

- Emulator only: emulated authentication, plaintext secrets in config.yaml, and no production hardening; must not be exposed publicly
- Single-instance, stateful SQLite storage with no high-availability or replication path
- Admin API has no authentication unless admin_password is explicitly configured; default credentials are committed in config.yaml
- No TLS by default (scheme http); encryption depends on external ingress
- No health probes, resource limits, or Kubernetes manifests; Dockerfile omits source, requiring runtime volume mounts

