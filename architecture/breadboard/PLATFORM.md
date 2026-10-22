# Platform Architecture — breadboard

## Metadata

- Components analyzed: 5/5
- Complete: true
- Components: breadboard, jira-emulator, github-emulator, gitlab-emulator, entra-id-emulator

## Platform Overview

Breadboard is an AI-native software engineering platform combining a Python CLI/pipeline agent with a resettable local K3s service stack on a developer workstation. The platform emulates real source systems (Jira, GitHub, GitLab, Entra ID) so agents, CI runners, and dashboards can operate offline against realistic APIs. Pipeline agents run bug, RFE, and strategy phases orchestrated by markovd workflows, execute through Fullsend agents and sandbox runners, and call Claude models via Model Relay. The Breadboard dashboard aggregates tickets across emulators, submits Kubernetes jobs, and surfaces MLflow and Observatory traces.

## Component Relationships

### Internal Dependencies

- breadboard -> jira-emulator
- breadboard -> github-emulator
- breadboard -> gitlab-emulator
- breadboard -> markovd
- breadboard -> observatory
- breadboard -> fullsend-mint-dev
- breadboard -> model-relay
- breadboard -> org-pulse
- breadboard -> openshell
- breadboard -> github-actions-runner
- breadboard -> gitlab-runner

### Central Components

- **breadboard**

### Integration Patterns

- **Emulator-as-source-system**: FastAPI/Flask emulators replace Jira, GitHub, GitLab, and Entra ID, each persisted in SQLite and exposed via cluster-local HTTPS routes.
- **Kubernetes service mesh by convention**: All components deploy into the ai-pipeline namespace; dashboard and orchestrators interact via in-cluster Services and the Kubernetes API.
- **Ingress edge via Traefik and ingress-proxy**: Traefik plus a Go ingress-proxy terminate TLS and route *.local hosts to backend Services like github-emulator, jira-emulator, and pipeline-dashboard.
- **Model Relay gateway**: Agents call Model Relay, which fronts Vertex/Anthropic inference with usage telemetry and managed upstream accounts.
- **MCP tool integration**: The jira-emulator FastMCP server on port 8081 exposes Jira operations as tools for Claude integration.
- **OIDC credential exchange**: GitHub Actions in the emulator trigger Fullsend Mint to exchange OIDC assertions for scoped GitHub credentials used by sandbox runners.

## Network Architecture

Traefik (LoadBalancer 80/443) and the Go ingress-proxy expose *.local HTTPS hosts into the ai-pipeline namespace. The inventory shows cross-repo TLS ingress wiring github-emulator.ai-pipeline.svc.cluster.local to github-emulator-backend, gitlab-emulator to gitlab-emulator-backend, jira-emulator to jira-emulator-backend, dashboard to pipeline-dashboard, plus markovd, observatory, org-pulse-frontend, model-relay, and fullsend-dashboard routes. Non-TLS simple routes jira.local and github.local point at jira-emulator and github-emulator. Emulators also terminate their own TLS via internal Caddy proxies with local CAs. Egress goes to Vertex/Anthropic inference and optional real Jira or GitLab/GitHub import.

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

Authentication is largely absent at HTTP surfaces: dashboards expose admin and destructive endpoints unauthenticated, Traefik runs with --api.insecure=true, and emulator OIDC endpoints are intentionally unauthenticated. Default credentials and tokens (admin/admin, changeme1234, change-me secrets) ship in manifests and compose files. Secrets like observatory-secrets and org-pulse credentials are provisioned directly in Kubernetes manifests. Access control relies on Kubernetes RBAC (read-only Fullsend ClusterRole, broad gitlab-runner namespace rights) rather than per-request auth on services.

## Data Flows

- **Ticket aggregation**: Breadboard dashboard fetches issues, PRs, and MRs from Jira, GitHub, and GitLab emulators, combines and filters them across emulated source systems.
- **Pipeline job lifecycle**: Dashboard submits and monitors Kubernetes Jobs via the Python client; pipeline events stream to the dashboard via Server-Sent Events from /api/events/push.
- **Markov workflow orchestration**: markovd reads declarative workflow definitions, tracks run state and approvals in PostgreSQL, and orchestrates jobs following the RFE to quality gate to strategy to review to epics flow.
- **Fullsend agent flow**: GitHub Actions in the emulator trigger OIDC assertion exchange at Fullsend Mint, issuing scoped credentials for sandbox runner agent work via OpenShell.
- **Model inference**: Agents call Model Relay, which fronts Vertex/Anthropic with usage telemetry; entra-id-emulator can supply OIDC identity for relying parties like oauth2-proxy.
- **Observability**: Observatory collects traces and artifacts with claim verification while MLflow stores experiment runs, both queried by the Breadboard dashboard.

## Deployment Topology

A local K3s cluster in the ai-pipeline namespace runs 21 workloads and 22 Services defined by breadboard deploy/k8s manifests: dashboards (Flask, FastAPI), markovd with PostgreSQL, observatory, MLflow, model-relay, org-pulse with MongoDB, fullsend-mint, OpenShell, and CI runners. Emulators run as containers (supervisord managing uvicorn, Caddy, sshd) and are wired in via cross-repo ingress. The Python CLI/pipeline agent and Go ingress-proxy run outside the cluster; cert-manager supplies internal certificates and Traefik plus ingress-proxy expose *.local hosts.

## Cross-Cutting Concerns

- No authentication middleware on dashboard HTTP surfaces; admin and destructive endpoints (/admin, /api/jobs/all, workspace reset) appear unauthenticated
- Default credentials and tokens ship across emulators and manifests (admin/admin, jira-emulator-default-token, changeme1234, change-me secret keys)
- Traefik deployed with --api.insecure=true
- Broad gitlab-runner RBAC including secret access within its namespace
- Single-replica, single-SQLite storage in emulators limits concurrency and horizontal scaling; no HA story platform-wide
- Secrets provisioned directly in Kubernetes manifests (observatory-secrets, org-pulse credentials)
- RSA private keys stored unencrypted in SQLite without documented rotation (entra-id-emulator)
- Flask development server used instead of production WSGI server (entra-id-emulator)
- Very large API surface areas (552 gitlab-emulator, 381 github-emulator, 113 jira-emulator endpoints) create broad maintenance and test burden
- gitlab-emulator is an explicit scaffold with incomplete GitLab-specific routes and CI API coverage
- Emulated CI runners execute arbitrary workflow code, unsafe if exposed beyond trusted environments
- Many services run without dedicated service accounts (empty service account names)
- No supply-chain or high-availability evidence found by the analyzer

## Analyzer Inventory

| Component | Endpoints | Services | Deployments | Entrypoints |
|----|----|----|----|----|
| breadboard | 44 | 22 | 21 | 8 |
| jira-emulator | 113 | 1 | 0 | 5 |
| github-emulator | 381 | 1 | 0 | 7 |
| gitlab-emulator | 552 | 1 | 0 | 3 |
| entra-id-emulator | 26 | 1 | 0 | 1 |

