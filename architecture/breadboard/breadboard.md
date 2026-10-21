# Component: breadboard

## Purpose

Breadboard combines a Python CLI and pipeline agent (bug, RFE, and strategy phases run by Claude-agent skills) with an integrated K3s service stack in the ai-pipeline namespace. The stack includes Markov workflows, Jira/GitHub/GitLab emulators, CI runners, Observatory, MLflow, Fullsend (Mint, OpenShell, sandbox runner), Org Pulse, and Model Relay, fronted by Traefik and a Go host proxy exposing *.local routes. The dashboard aggregates tickets, pipeline jobs, artifacts, and service links; the Fullsend path runs role-specific agent work inside a sandbox boundary via GitHub Actions and OIDC.

## Architectural Analysis

Breadboard is organized around two execution paths sharing one repository. The Python path (main.py, src/cli) orchestrates bug, RFE, and strategy phases concurrently, validates outputs against schemas in src/cli/schemas.py, and launches Kubernetes jobs via the kubernetes Python SDK. The service path is fully declared in deploy/k8s: roughly 29 deployments span emulators (Jira, GitHub, GitLab), markovd with Postgres, Observatory, MLflow, Fullsend Mint and dashboards, Org Pulse with MongoDB, Model Relay, and runners, all internal ClusterIP services fronted by Traefik and a Go reverse proxy with TLS via cert-manager and *.local ingress hosts. The pipeline dashboard (Flask, src/dashboard/webapp.py) exposes ~40 HTTP endpoints for tickets, jobs, MLflow traces, events (SSE), and Kubernetes job submission. Security relies on Kubernetes RBAC roles (traefik, pipeline-orchestrator, gitlab-runner, fullsend-dashboard-readonly) and secret-mounted credentials, but application HTTP surfaces show no authentication middleware. The Fullsend flow is GitHub-first: Actions workflows use OIDC, Fullsend Mint exchanges assertions for scoped GitHub credentials, and OpenShell runs agent work in a sandbox, observed by the read-only Fullsend dashboard.

## Architecture Components

| Component | Type | Purpose |
|----|----|-------|
| pipeline-agent / claude-agent | Deployment | Runs the bug/RFE/strategy pipeline agent image with GCP credentials for Vertex-backed Claude agents. |
| pipeline-dashboard | Deployment (Flask) | Breadboard dashboard and APIs for tickets, pipeline jobs, artifacts, and service links. |
| markovd | Deployment | Declarative workflow run state, approvals, and job orchestration, backed by Postgres. |
| observatory | Deployment | Trace and artifact collection, claim extraction, verification, and quality reporting. |
| mlflow | Deployment | Agent traces and experiment data storage. |
| jira-emulator | Deployment | Jira-compatible issues, UI, snapshots, and MCP-compatible operations. |
| github-emulator | Deployment | REST/GraphQL API, Git transport, web UI, Actions, and admin APIs. |
| gitlab-emulator | Deployment | GitLab API, Git transport, issues, merge requests, and CI APIs. |
| gitlab-runner | Deployment | Kubernetes-executor runner for emulator CI jobs. |
| github-actions-runner | Deployment | Runs emulator Actions workflows, including Fullsend workflows. |
| fullsend-mint-dev | Deployment | Exchanges development OIDC assertions for scoped GitHub credentials. |
| fullsend-dashboard | Deployment (FastAPI) | Read-only operational view of Actions, jobs, pods, and events. |
| org-pulse-backend / org-pulse-frontend | Deployments | AI Engineering dashboard with MongoDB, pointed at the emulators. |
| model-relay | Deployment | Vertex/Anthropic Messages gateway with usage telemetry and managed upstream accounts. |
| traefik | Deployment (Ingress) | Internal TLS termination and routing for ai-pipeline services. |
| ingress-proxy | Deployment (Go) | Host-facing proxy exposing *.local service routes with TLS. |
| reverse-proxy | Go executable | Go host proxy entrypoint serving /healthz and proxy routes. |
| bug-bash-analyzer | Python Service (Flask) | AI-driven RHOAIENG bug bash analysis pipeline. |

## Sub-Component: src/cli

**Upstream Dependencies:** Jira API (emulator or production), Kubernetes API, Claude agent SDK, Model Relay

**Configuration:**

- var/pipeline-skills.yaml
- --model
- --max-concurrent
- --issue
- --limit
- --force
- --component

## Sub-Component: src/dashboard

**API Routes:**

| Path | Methods |
|----|--------|
| /api/tickets | GET |
| /api/jobs | GET |
| /api/jobs/submit | POST |
| /api/jobs/<job_name> | GET, DELETE |
| /api/jobs/<job_name>/stop | POST |
| /api/jobs/<job_name>/logs | GET |
| /api/events/push | POST |
| /api/events | GET |
| /api/fullsend/onboard | POST |
| /api/mlflow/runs | GET |
| /api/mlflow/traces | GET |
| /api/observatory/clear | POST |
| /api/workspace/reset | POST |
| /api/pipeline/status | GET |
| /healthz | GET |

**Upstream Dependencies:** Jira emulator, GitHub emulator, GitLab emulator, Kubernetes API, MLflow, Observatory

**Configuration:**

- port via --port
- SSE event stream
- github-token secret

## Sub-Component: src/fullsend-dashboard

**API Routes:**

| Path | Methods |
|----|--------|
| / | GET |
| /healthz | GET |
| /api/state | GET |

**Upstream Dependencies:** Kubernetes API (read-only)

**Configuration:**

- read-only service account fullsend-dashboard-readonly

## Sub-Component: deploy/golang-reverse-proxy

**API Routes:**

| Path | Methods |
|----|--------|
| /healthz | GET |
| / | GET |

**Upstream Dependencies:** traefik, ai-pipeline services

**Configuration:**

- ingress-proxy-tls secret
- host *.local routing rules

## APIs Exposed

### HTTP Endpoints

| Path | Methods | Description |
|----|---------|-------------|
| /api/tickets | GET | Combined Jira/GitHub/GitLab issue, PR, and MR browser data for the dashboard. |
| /api/jobs | GET | List Kubernetes pipeline jobs. |
| /api/jobs/submit | POST | Submit a Kubernetes pipeline job from the dashboard. |
| /api/jobs/<job_name> | GET, DELETE | Inspect or delete a specific pipeline job. |
| /api/jobs/<job_name>/stop | POST | Stop a running pipeline job. |
| /api/jobs/<job_name>/logs | GET | Fetch logs for a pipeline job. |
| /api/events | GET | Server-Sent Events stream of pipeline activity. |
| /api/events/push | POST | Push pipeline activity events to dashboard clients. |
| /api/fullsend/onboard | POST | Onboard a repository into the Fullsend development flow via Kubernetes resources. |
| /api/mlflow/runs | GET | List MLflow runs. |
| /api/mlflow/traces | GET | List agent traces from MLflow. |
| /api/observatory/clear | POST | Clear Observatory data. |
| /api/pipeline/status | GET | Pipeline status. |
| /api/pipeline/queue | GET | Pipeline queue state. |
| /healthz | GET | Liveness probe endpoint on dashboard and proxy services. |
| / | GET | Dashboard root page (Flask and FastAPI dashboards). |
| /api/state | GET | Fullsend dashboard state snapshot. |

## Dependencies

**External:** Python 3.13+ with uv, Flask >=3.0, kubernetes >=35.0.0 (Python SDK), pyjwt >=2.8, requests >=2.32, mlflow >=3.4, grpcio/protobuf, claude-agent-sdk ==0.1.61, Go 1.22 (reverse proxy), Traefik v2.11, PostgreSQL 16 (markovd), MongoDB 7.0 (org-pulse), MLflow v3.11.1 image, cert-manager, K3s and kubectl, Podman/Docker for image builds

**Internal Platform:** Kubernetes API (job submission and resource operations), Traefik ingress and cert-manager TLS, Model Relay for Vertex/Anthropic inference, Atlassian MCP server (Jira)

## Deployment

Deployed as a resettable multi-service stack in the ai-pipeline K3s namespace via deploy/k8s manifests and deploy/scripts/deploy-all.sh, with host access through a Go reverse proxy exposing *.local HTTPS routes; Python pipeline runs locally or as Kubernetes jobs.

**Variants:**

- **host-deploy-all**: Full integrated K3s deployment of all services, emulators, runners, and dashboards.
- **local Python development**: uv sync plus python main.py <command>; dashboard runs locally with python main.py dashboard --port 5000.
- **pipeline-agent job**: Pipeline phases executed as Kubernetes jobs from the pipeline-agent image.

## Network Architecture

**Services:**

- **pipeline-dashboard**: ClusterIP 5000; Breadboard dashboard UI and APIs.
- **fullsend-dashboard**: ClusterIP 5000; read-only Fullsend operations dashboard.
- **markovd / markovd-postgres**: ClusterIP 8080 workflow service backed by Postgres 5432.
- **observatory**: ClusterIP 8000; trace and artifact collection.
- **mlflow**: ClusterIP 5000; traces and experiments.
- **github-emulator / gitlab-emulator / jira-emulator**: ClusterIP services on 80/443 (plus 8080/8081 backends) for emulated source systems.
- **model-relay**: ClusterIP 8080 inference and 8081 admin gateway.
- **org-pulse-backend/frontend/mongodb**: ClusterIP 3001/8080/27017 dashboard stack.
- **fullsend-mint-dev**: ClusterIP 8080; OIDC-to-GitHub credential exchange.
- **claude-agent**: ClusterIP 8080; agent execution service.

**Ingress:**

- **traefik**: LoadBalancer 80/443 TLS ingress for ai-pipeline services, including *.local hosts like dashboard.local, github.local, gitlab.local, jira.local, fullsend.local, observatory.local, relay.local.
- **ingress-proxy**: Go LoadBalancer proxy on 80/443 routing host *.local names to internal services with TLS.
- **dashboard-https / fullsend-dashboard-https / markovd-https / observatory-https / org-pulse-https / model-relay-https**: TLS Ingress resources for cluster-internal service hostnames.

**Egress:**

- **Kubernetes API**: Python SDK calls for job submission and resource operations.
- **gitlab.local**: HTTPS outbound calls for runner registration smoke tests.
- **Vertex/Anthropic via Model Relay**: LLM inference egress using GCP credentials.
- **Production Jira API**: Optional Jira credentials for non-emulator operation.

## Security

- **Authentication:** No authentication middleware detected on dashboard HTTP APIs; healthz endpoints are unauthenticated probes. PyJWT is a dependency for JWT/OAuth flows; Fullsend Mint exchanges development OIDC assertions for scoped GitHub credentials.
- **Authorization:** Kubernetes RBAC roles: traefik (ingress read), pipeline-orchestrator (jobs, pods, configmaps bound to markovd, pipeline-agent, pipeline-dashboard), gitlab-runner (pods, secrets, services), fullsend-dashboard-readonly (read-only pods, jobs, events), openshell-sandbox.
- **FIPS Compliance:** not applicable

**Secrets:**

- pipeline-secrets
- gcp-credentials
- github-token
- fullsend-mint-role-apps
- fullsend-onboarding-app
- github-actions-runner-credentials
- model-relay-admin
- org-pulse-mongodb
- org-pulse-forge-credentials
- observatory-secrets
- gitlab-runner-ca
- runner tokens
- JIRA_TOKEN / GITLAB_TOKEN / GITHUB_TOKEN environment variables
- GITLAB_ADMIN_PASSWORD / JIRA_ADMIN_PASSWORD environment variables

## Multi-Tenancy

**Model:** Single-tenant local development platform; all services share the ai-pipeline Kubernetes namespace.

**Isolation Mechanisms:**

- Kubernetes namespace separation (ai-pipeline, traefik, gitlab-runner)
- RBAC roles per service account
- Sandbox boundary around Fullsend OpenShell agent work
- Scoped GitHub credentials from Fullsend Mint

**Shared Services:** Model Relay inference gateway, MLflow, Observatory, Emulated Jira, GitHub, and GitLab, Traefik and ingress proxy

## Data Flows

- **Ticket aggregation**: Dashboard queries Jira, GitHub, and GitLab emulators, combines issues, PRs, and MRs across all pages, then filters (closed work hidden by default).
- **Pipeline execution**: CLI phases fetch issues, run Claude-agent skills in per-issue workspaces, validate YAML outputs against src/cli/schemas.py, and retain invalid outputs with .invalid suffix.
- **Job submission**: Dashboard submits Kubernetes jobs in ai-pipeline; pipeline activity streams back via Server-Sent Events.
- **Fullsend flow**: GitHub Actions in fullsend-dev/triage-target use OIDC, Fullsend Mint credential exchange, and OpenShell sandbox runners; Fullsend dashboard observes read-only.
- **Telemetry**: Agent traces flow to MLflow and Observatory; Model Relay records LLM usage telemetry.

## Integration Points

- **Emulated source systems**: Jira, GitHub, and GitLab emulators provide compatible REST, Git transport, CI, and MCP interfaces.
- **Kubernetes API**: Python SDK used by dashboard and onboarding for job and resource operations.
- **Model Relay**: Vertex/Anthropic Messages gateway for agent inference.
- **Atlassian MCP server**: MCP-compatible Jira operations via ATLASSIAN_MCP_URL.
- **Claude Code skills**: Local .claude/skills and external skills configured in var/pipeline-skills.yaml drive phase behavior.

## Concerns

- No authentication middleware on dashboard HTTP APIs; dashboards are effectively unauthenticated behind local ingress.
- Broad pipeline-orchestrator RBAC (pods/exec, secrets) shared across markovd, pipeline-agent, and pipeline-dashboard.
- Secrets and admin passwords passed via environment variables; emulator admin passwords in manifests/env risk leakage.
- Large single-namespace deployment with mixed trust levels (emulators, runners, agent sandbox) increases blast radius.
- No high-availability or supply-chain evidence extracted by the analyzer; single-instance deployments assumed.

