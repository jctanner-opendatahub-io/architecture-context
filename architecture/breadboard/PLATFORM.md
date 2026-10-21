# Platform Architecture — breadboard

## Metadata

- Components analyzed: 5/5
- Complete: true
- Components: breadboard, jira-emulator, github-emulator, gitlab-emulator, entra-id-emulator

## Platform Overview

Breadboard is an AI-native software engineering platform combining a Python CLI/pipeline agent with a resettable local K3s service stack in the ai-pipeline namespace. The pipeline runs bug, RFE, and strategy phases with Claude-based agents, while the stack hosts roughly 29 workloads: the Breadboard dashboard, markovd workflow engine with Postgres, Observatory, MLflow, Model Relay, Org Pulse, Fullsend runners, and API emulators for Jira, GitHub, GitLab, and Entra ID. The emulators provide offline, high-fidelity stand-ins for external SaaS systems, enabling end-to-end testing of clients, CI runners, OIDC flows, and agent integrations without touching production services. Everything is exposed through Traefik and a Go host proxy via *.local routes.

## Component Relationships

### Internal Dependencies

- breadboard -> Kubernetes API (jobs, pods, configmaps, secrets via Python SDK)
- breadboard -> Vertex AI / Anthropic model endpoints via Model Relay
- breadboard -> Jira production API (optional)

### Central Components

- **breadboard**
- **jira-emulator**
- **github-emulator**
- **gitlab-emulator**
- **entra-id-emulator**

### Integration Patterns

- **emulator-backed development**: Pipeline and dashboard target local Jira, GitHub, and GitLab emulators instead of production SaaS APIs
- **MCP tool integration**: Jira emulator exposes a FastMCP server so Claude agents manipulate issues via tool calls
- **CI runner coordination**: gitlab-runner registers with the GitLab emulator to execute CI jobs triggered by agent workflows
- **OIDC identity federation**: Entra ID emulator issues OIDC/OAuth2 tokens, e.g., for oauth2-proxy and GitHub Actions OIDC in the Fullsend flow
- **model gateway**: Agents call Model Relay, which forwards to Vertex/Anthropic and records telemetry and MLflow traces
- **Kubernetes job orchestration**: Dashboard and markovd submit Kubernetes jobs; runners execute and stream logs back via SSE

## Network Architecture

Traefik and the Go ingress-proxy LoadBalancer terminate TLS on ports 80/443 for *.local hosts, routing to ClusterIP services. Cross-repo ingress maps github-emulator.ai-pipeline.svc.cluster.local to github-emulator backends, gitlab-emulator.ai-pipeline.svc.cluster.local to gitlab-emulator-backend, jira-emulator.ai-pipeline.svc.cluster.local to jira-emulator-backend, dashboard.ai-pipeline.svc.cluster.local to pipeline-dashboard, plus TLS routes to fullsend-dashboard, markovd, observatory, org-pulse-frontend, and model-relay. Host routes include dashboard.local, fullsend.local, github.local, gitlab.local, jira.local, markovd.local, observatory.local, orgpulse.local, and relay.local; jira-simple (jira.local) and github-simple (github.local) are non-TLS. Egress includes webhook delivery from emulators, Vertex/Anthropic inference via Model Relay, and in-cluster Kubernetes API calls.

### Analyzer-Detected Service Wiring

| Ingress | Host | Paths | Backend | TLS |
|----|----|----|----|----|
| github-emulator | github-emulator.ai-pipeline.svc.cluster.local | / | github-emulator-backend | true |
| gitlab-emulator | gitlab-emulator.ai-pipeline.svc.cluster.local | / | gitlab-emulator-backend | true |
| jira-emulator | jira-emulator.ai-pipeline.svc.cluster.local | / | jira-emulator-backend | true |
| pipeline-dashboard | dashboard.ai-pipeline.svc.cluster.local | / | pipeline-dashboard | true |
| github-emulator-https | github-emulator.ai-pipeline.svc.cluster.local | / | github-emulator | true |
| jira-emulator-https | jira-emulator.ai-pipeline.svc.cluster.local | / | jira-emulator | true |
| dashboard-https | dashboard.ai-pipeline.svc.cluster.local | / | pipeline-dashboard | true |
| fullsend-dashboard-https | fullsend-dashboard.ai-pipeline.svc.cluster.local | / | fullsend-dashboard | true |
| markovd-https | markovd.ai-pipeline.svc.cluster.local | / | markovd | true |
| observatory-https | observatory.ai-pipeline.svc.cluster.local | / | observatory | true |
| org-pulse-https | org-pulse-frontend.ai-pipeline.svc.cluster.local | / | org-pulse-frontend | true |
| model-relay-https | model-relay.ai-pipeline.svc.cluster.local | / | model-relay | true |
| markovd | markovd.ai-pipeline.svc.cluster.local | / | markovd | true |
| jira-simple | jira.local | / | jira-emulator | false |
| github-simple | github.local | / | github-emulator | false |

## Platform Security

Security is perimeter-based. Internal services and dashboards lack authentication middleware, relying on cluster isolation, Kubernetes RBAC (pipeline-orchestrator, gitlab-runner, fullsend-dashboard-readonly), and Secrets like pipeline-secrets and gcp-credentials. Emulators ship insecure defaults: permissive AUTH_MODE with admin:admin (Jira, GitLab), changeme1234 admin password (Entra ID), and public OIDC endpoints by design. Public OIDC endpoints on the Entra ID emulator are intentional for an emulator but unsafe beyond localhost.

## Data Flows

- **ticket aggregation**: Dashboard queries Jira, GitHub, and GitLab emulators, merges issues, PRs, and MRs, then filters and renders the ticket browser
- **pipeline execution**: CLI phases fetch issues from emulators, run Claude agents, validate outputs against schemas, and store artifacts in issues/ and workspace/
- **job orchestration**: Dashboard or markovd submits Kubernetes jobs; runners execute and logs stream back via the API and SSE
- **fullsend flow**: GitHub emulator Actions trigger OIDC, Mint exchanges assertions for scoped credentials, OpenShell runs agent work in the sandbox runner
- **model inference**: Agents call Model Relay, which forwards to Vertex/Anthropic and records usage telemetry and MLflow traces
- **CI runner flow**: gitlab-runner polls the GitLab emulator coordinator for jobs, executes them, and uploads traces, artifacts, and cache
- **OIDC authentication**: Relying parties redirect to Entra ID emulator authorize endpoints; tokens are issued, signed, and validated via JWKS/userinfo
- **observability**: Observatory collects traces and artifacts, extracts claims, verifies them, and reports quality

## Deployment Topology

Breadboard deploys a K3s stack (deploy/k8s) with ~29 workloads in the ai-pipeline namespace, fronted by Traefik and a Go host proxy. Emulators each run as single self-contained containers (Docker Compose or podman with supervisord, Caddy TLS, SQLite and bare git repos on persistent volumes). Single-replica deployments throughout; no high-availability design.

## Cross-Cutting Concerns

- No authentication middleware on internal dashboard APIs; security relies entirely on cluster and host-network isolation
- Single-instance, stateful emulator design (SQLite, local disk, in-memory caches) precludes horizontal scaling and high availability
- Default seeded admin credentials (admin:admin, changeme1234) across emulators are insecure if exposed beyond local development
- Many services share one namespace with broad secrets like pipeline-secrets and gcp-credentials
- Mixed plaintext and TLS ingress paths (jira-simple, github-simple) could expose emulators without encryption
- Broad emulator egress (webhooks, repository imports) could be abused if deployed outside a trusted network
- Very large API surfaces (552 GitLab, 381 GitHub endpoints) increase maintenance burden
- Supply chain posture unresolved: multiple image registries, pinned SDK versions, no SBOM evidence
- GitLab emulator is still a scaffold preserving github_emulator architecture; runner coordination compatibility in progress

## Analyzer Inventory

| Component | Endpoints | Services | Deployments | Entrypoints |
|----|----|----|----|----|
| breadboard | 44 | 22 | 21 | 8 |
| jira-emulator | 113 | 1 | 0 | 5 |
| github-emulator | 381 | 1 | 0 | 7 |
| gitlab-emulator | 552 | 1 | 0 | 3 |
| entra-id-emulator | 26 | 1 | 0 | 1 |

