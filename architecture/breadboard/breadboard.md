# Component: breadboard

## Purpose

Breadboard combines a Python CLI and pipeline agent (bug, RFE, and strategy phases run by Claude-based agents) with an integrated local K3s service stack in the ai-pipeline namespace. The stack includes the Breadboard dashboard, Fullsend dashboards and runner path, Markov workflow engine (markovd with Postgres), Observatory, MLflow, Jira/GitHub/GitLab emulators, CI runners, Org Pulse, and Model Relay, all exposed through Traefik and a Go host proxy via *.local routes.

## Architectural Analysis

Breadboard has two execution paths. First, a Python CLI (main.py, src/cli/) runs bug, RFE, and strategy phases concurrently with Claude Code agents, validating outputs against schemas in src/cli/schemas.py and optionally launching Kubernetes jobs. Second, a resettable K3s stack (deploy/k8s/) hosts roughly 29 workloads: emulators (Jira, GitHub, GitLab), markovd plus Postgres for declarative workflows, Observatory for trace and claim verification, MLflow for traces, Model Relay as a Vertex/Anthropic gateway, Fullsend Mint and OpenShell sandbox runners, Org Pulse with MongoDB, and dashboards. Traefik and a Go reverse proxy (deploy/golang-reverse-proxy) provide TLS ingress on hosts like dashboard.local and github.local. The Breadboard dashboard (src/dashboard/webapp.py, Flask) exposes about 44 HTTP routes covering ticket browsing, job submission, SSE events, evals, and file views, and talks to the emulators and the Kubernetes API via the Python client. The Fullsend dashboard is a read-only FastAPI app with cluster-readonly RBAC. Security is largely perimeter-based: internal services have no authentication middleware, relying on cluster isolation, Kubernetes RBAC (pipeline-orchestrator, gitlab-runner, fullsend-dashboard-readonly roles), and Secrets for credentials.

## Architecture Components

| Component | Type | Purpose |
|----|----|-------|
| pipeline CLI | Python application (main.py, src/cli/) | Runs bug, RFE, and strategy phases with agent backends and schema validation |
| breadboard dashboard | Flask web application (src/dashboard/webapp.py) | Combined ticket browser, pipeline job management, artifact views, and SSE event stream |
| fullsend dashboard | FastAPI web application (src/fullsend-dashboard/app.py) | Read-only operational view of Actions, jobs, pods, and events |
| markovd | Kubernetes Deployment with nginx sidecar and Postgres | Declarative workflow engine with run state, approvals, and job orchestration |
| observatory | Kubernetes Deployment | Trace and artifact collection, claim extraction, verification, and quality reporting |
| mlflow | Kubernetes Deployment (ghcr.io/mlflow/mlflow:v3.11.1) | Agent traces and experiment data |
| jira emulator | Kubernetes Deployment | Jira-compatible issues, UI, snapshots, and MCP-compatible operations |
| github emulator | Kubernetes Deployment | REST/GraphQL GitHub API, git transport, web UI, Actions, and admin APIs |
| gitlab emulator | Kubernetes Deployment | GitLab API, git transport, issues, merge requests, and CI APIs |
| fullsend mint | Kubernetes Deployment | Exchanges development OIDC assertions for scoped GitHub credentials |
| org pulse | Kubernetes Deployments (backend, frontend, MongoDB) | AI Engineering dashboard pointed at the emulators |
| model relay | Kubernetes Deployment | Vertex/Anthropic Messages gateway with usage telemetry |
| ingress proxy | Go reverse proxy Deployment | Host-facing TLS routing for *.local service hosts |
| traefik | Kubernetes Deployment (traefik:v2.11) | Ingress controller with TLS for internal cluster routes |
| runners | Kubernetes Deployments (GitLab and GitHub Actions runners) | Execute emulator CI jobs and Fullsend workflows |

## Sub-Component: breadboard dashboard

**API Routes:**

| Path | Methods |
|----|--------|
| /api/tickets | GET |
| /api/jobs/submit | POST |
| /api/events/push | POST |
| /api/fullsend/onboard | POST |
| /api/files/list | GET |

**Upstream Dependencies:** jira emulator, github emulator, gitlab emulator, Kubernetes API, mlflow, observatory

**Configuration:**

- GITHUB_TOKEN
- JIRA_TOKEN
- GITLAB_TOKEN
- GITHUB_EMULATOR_TOKEN

## Sub-Component: fullsend dashboard

**API Routes:**

| Path | Methods |
|----|--------|
| / | GET |
| /api/state | GET |
| /healthz | GET |

**Upstream Dependencies:** Kubernetes API

**Configuration:**

- none

## Sub-Component: pipeline agent

**Upstream Dependencies:** Kubernetes API, Vertex AI (Claude models), Jira API

**Configuration:**

- CLAUDE_CODE_USE_VERTEX
- ANTHROPIC_VERTEX_PROJECT_ID
- JIRA_SERVER
- JIRA_USER
- JIRA_TOKEN

## APIs Exposed

### HTTP Endpoints

| Path | Methods | Description |
|----|---------|-------------|
| /api/tickets | GET | Combined issue, pull request, and merge request browser data |
| /api/issues | GET | List fetched issue data |
| /api/jobs/submit | POST | Submit Kubernetes pipeline jobs |
| /api/jobs/<job_name> | GET, DELETE | Inspect or delete a pipeline job |
| /api/jobs/<job_name>/stop | POST | Stop a running pipeline job |
| /api/events/push | POST | Push pipeline activity events for SSE |
| /api/fullsend/onboard | POST | Onboard Fullsend repositories and runners |
| /api/mlflow/traces | GET | List MLflow agent traces |
| /api/observatory/clear | POST | Clear Observatory collected data |
| /healthz | GET | Liveness probe endpoint |

## Dependencies

**External:** Flask, FastAPI/Starlette, kubernetes Python SDK, pyjwt, requests, mlflow, elasticsearch, grpcio, protobuf, pyyaml, Go 1.22 (reverse proxy), Traefik v2.11, PostgreSQL 16, MongoDB 7.0, mlflow v3.11.1 image, gitlab-runner v19.1.1

**Internal Platform:** Kubernetes API (jobs, pods, configmaps, secrets via Python SDK), Vertex AI / Anthropic model endpoints via Model Relay, Jira production API (optional)

## Deployment

Deployed as a resettable local K3s stack in the ai-pipeline namespace, built and applied through deploy/k8s manifests and deploy/scripts/deploy-all.sh, with images built via Podman.

**Variants:**

- **host-deploy-all**: Full stack deployment via Makefile target applying all Kubernetes manifests
- **local development**: Python CLI and dashboard run directly with uv and python main.py dashboard
- **pipeline jobs**: Pipeline agent runs as Kubernetes jobs from the pipeline-agent image

## Network Architecture

**Services:**

- **traefik**: LoadBalancer ingress controller for TLS cluster routes on ports 80/443
- **ingress-proxy**: Go LoadBalancer proxy exposing *.local hosts on ports 80/443
- **pipeline-dashboard**: ClusterIP service for the Breadboard dashboard on port 5000
- **fullsend-dashboard**: ClusterIP service for the Fullsend dashboard on port 5000
- **markovd**: ClusterIP service for the workflow daemon on port 8080
- **markovd-postgres**: ClusterIP service for workflow state storage on port 5432
- **github-emulator**: ClusterIP services for GitHub emulator API and git transport
- **gitlab-emulator**: ClusterIP services for GitLab emulator API and git transport
- **jira-emulator**: ClusterIP services for Jira emulator API and MCP endpoint
- **observatory**: ClusterIP service for trace collection and verification on port 8000
- **mlflow**: ClusterIP service for MLflow on port 5000
- **model-relay**: ClusterIP services for inference (8080), admin (8081), and telemetry (8082)
- **org-pulse-backend**: ClusterIP service for Org Pulse API on port 3001
- **org-pulse-mongodb**: ClusterIP service for Org Pulse storage on port 27017

**Ingress:**

- **dashboard.local**: HTTPS route to the pipeline-dashboard service
- **fullsend.local**: HTTPS route to the fullsend-dashboard service
- **github.local**: Route to the GitHub emulator including /ui/ web views
- **gitlab.local**: Route to the GitLab emulator
- **jira.local**: Route to the Jira emulator
- **markovd.local**: HTTPS route to the markovd service
- **observatory.local**: HTTPS route to the observatory service
- **orgpulse.local**: HTTPS route to the org-pulse-frontend service
- **relay.local**: HTTPS routes to model-relay console and relay-api inference

**Egress:**

- **gitlab.local:443**: HTTPS calls to register CI runners with the GitLab emulator
- **Kubernetes API**: In-cluster API calls for job, pod, and configmap operations
- **Vertex AI / Anthropic**: Model inference egress through Model Relay using GCP credentials

## Security

- **Authentication:** No authentication middleware on internal dashboard APIs; perimeter TLS via Traefik and the Go proxy; external system auth uses tokens (Jira, GitHub, GitLab) and GCP credentials; Fullsend Mint exchanges OIDC assertions for scoped credentials.
- **Authorization:** Kubernetes RBAC: pipeline-orchestrator role (jobs, pods, configmaps) bound to markovd, pipeline-agent, and pipeline-dashboard; fullsend-dashboard-readonly role grants read-only pod, event, and job access; gitlab-runner role for CI execution; openshell-sandbox role for sandboxed agent work.
- **FIPS Compliance:** not applicable

**Secrets:**

- pipeline-secrets
- gcp-credentials
- github-token
- github-actions-runner-credentials
- github-emulator-tls
- gitlab-emulator-tls
- jira-emulator-tls
- ingress-proxy-tls
- observatory-secrets
- org-pulse-mongodb
- org-pulse-forge-credentials
- model-relay-admin
- fullsend-mint-role-apps
- fullsend-onboarding-app
- JIRA_TOKEN
- GITHUB_TOKEN
- GITLAB_TOKEN
- FULLSEND_ONBOARD_APP_SECRET

## Multi-Tenancy

**Model:** Single-tenant local development and demonstration platform in one ai-pipeline namespace

**Isolation Mechanisms:**

- Kubernetes namespaces (ai-pipeline, traefik, gitlab-runner)
- Kubernetes RBAC roles and bindings per service account
- Fullsend sandbox boundary with OpenShell and scoped minted credentials
- Resettable demo scenarios under var/demos/

**Shared Services:** Traefik and ingress proxy, Model Relay, MLflow, Observatory, Emulators (Jira, GitHub, GitLab)

## Data Flows

- **ticket aggregation**: Dashboard queries Jira, GitHub, and GitLab emulators, merges issues, PRs, and MRs, then filters and renders the ticket browser
- **pipeline execution**: CLI phases fetch issues, run agents, validate outputs against schemas, and store artifacts in issues/ and workspace/
- **job orchestration**: Dashboard or markovd submits Kubernetes jobs; runners execute and logs stream back via API and SSE
- **fullsend flow**: GitHub emulator Actions trigger OIDC, Mint exchanges assertions for scoped credentials, OpenShell runs agent work in the sandbox runner
- **model inference**: Agents call Model Relay, which forwards to Vertex/Anthropic and records usage telemetry and MLflow traces
- **observability**: Observatory collects traces and artifacts, extracts claims, verifies them, and reports quality

## Integration Points

- **Jira**: Production Jira API or local emulator for RHOAIENG, RHAIRFE, RHAISTRAT projects
- **GitHub emulator**: REST/GraphQL API, git transport, Actions workflows, and admin APIs
- **GitLab emulator**: GitLab API, git transport, merge requests, and CI runner APIs
- **Kubernetes API**: Python SDK used by dashboard and pipeline for jobs, pods, and configmaps
- **Model Relay**: Vertex/Anthropic Messages gateway with managed upstream accounts
- **MLflow**: Trace and experiment storage queried by the dashboard
- **Atlassian MCP**: MCP-compatible operations through the Jira emulator or ATLASSIAN_MCP_URL

## Concerns

- Internal dashboard APIs have no authentication middleware; security relies entirely on cluster and host-network isolation
- No high-availability design; single-replica deployments with single Postgres and MongoDB instances
- Many services in one namespace with broad shared secrets such as pipeline-secrets and gcp-credentials
- Mixed plaintext and TLS ingress paths (test-simple-ingress) could expose emulators without encryption
- Supply chain posture unresolved: images from multiple registries and pinned agent SDK versions with no SBOM evidence

