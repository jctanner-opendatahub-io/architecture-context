# Component: github-emulator

## Purpose

GitHub Emulator is a lightweight, self-contained emulator of the GitHub API built with FastAPI, SQLAlchemy (async SQLite via aiosqlite), Strawberry GraphQL, and custom Git smart-HTTP/SSH transports. It lets client libraries, the gh CLI, CI automation, and GitHub Actions runners operate against a local or containerized GitHub-compatible service without touching real GitHub, including a web UI, admin panel, webhooks, GitHub Apps, OAuth/OIDC, and Actions workflow execution via bundled emulator and upstream runners.

## Architectural Analysis

The service is a single Python FastAPI application (src/app/main.py) that mounts a GitHub-compatible REST API across ~60 route modules in src/app/api (381 endpoints observed by static analysis), a Strawberry GraphQL API, Git smart-HTTP and SSH transports (src/app/git), a React web UI and admin panel, and GitHub Actions control-plane surfaces (_apis/distributedtask, _services/pipelines, runner registration). Business logic lives in src/app/services over async SQLAlchemy models (SQLite by default, no external database), with Alembic-style migrations applied at startup. Authentication is enforced via FastAPI dependencies (src/app/api/deps.py) accepting Bearer tokens, API tokens, or session cookies, backed by python-jose JWT, passlib/bcrypt, and libsodium (PyNaCl) sealed-box encryption of Actions secrets. Deployment is a single container (uvicorn) with optional Caddy TLS, an SSH transport on port 2222, and companion containers for emulator and real upstream Actions runners; docker-compose wires persistent /data storage, seeded admin credentials, and a default admin token. There are no CRDs, gRPC services, or Kubernetes workload manifests in evidence.

## Architecture Components

| Component | Type | Purpose |
|----|----|-------|
| FastAPI application core | service | Main app wiring in src/app/main.py mounting REST, GraphQL, git transports, web UI, and admin routes. |
| REST API routes | module | ~60 route modules in src/app/api implementing a GitHub REST v3 compatible subset. |
| GraphQL API | module | Strawberry-based GraphQL implementation of common GitHub queries and mutations at /api/graphql. |
| Git smart HTTP transport | module | Git clone/fetch/push over HTTP/HTTPS against bare repositories (src/app/git/smart_http.py). |
| Git SSH transport | module | asyncssh-based clone/push transport listening on port 2222 by default. |
| Actions control plane | module | Distributed-task, pipelines, and dispatch endpoints emulating GitHub Actions runner/job protocols. |
| Services layer | module | Business logic for issues, PRs, workflows, webhooks, auth, imports, secrets, and search. |
| ORM models and persistence | module | Async SQLAlchemy models with SQLite/aiosqlite storage and startup migrations. |
| Web UI and admin panel | module | React repository browser at /ui/ and API-client administration at /ui/_admin/. |
| Emulator runner | container | src/runners/emulator container that polls the emulator and executes Actions jobs. |
| Upstream runner | container | src/runners/upstream container wrapping real GitHub Actions runner binaries against the emulator. |

## Sub-Component: api

**API Routes:**

| Path | Methods |
|----|--------|
| /api/v3 | GET |
| /repos/{owner}/{repo}/actions/runs | GET |
| /repos/{owner}/{repo}/issues | GET, POST |
| /repos/{owner}/{repo}/pulls | GET, POST |
| /orgs/{org}/repos | GET, POST |
| /search/repositories | GET |

## Sub-Component: git-transport

**API Routes:**

| Path | Methods |
|----|--------|
| /{owner}/{repo}.git/info/refs | GET |
| /{owner}/{repo}.git/git-upload-pack | POST |
| /{owner}/{repo}.git/git-receive-pack | POST |

**Configuration:**

- GITHUB_EMULATOR_SSH_ENABLED
- GITHUB_EMULATOR_SSH_PORT

## Sub-Component: actions-control-plane

**API Routes:**

| Path | Methods |
|----|--------|
| /_apis/distributedtask/connect | POST |
| /_apis/distributedtask/pools/{pool_id}/agents | GET, POST |
| /_services/pipelines/{owner}/{repo}/_apis/pipelines/runs/register | POST |
| /actions/runner/register | POST |
| /actions/runner/jobs | GET |

**Configuration:**

- GITHUB_EMULATOR_TOKEN

## Sub-Component: admin

**API Routes:**

| Path | Methods |
|----|--------|
| /admin/api/users | GET, POST |
| /admin/api/tokens | GET, POST, DELETE |
| /admin/api/organizations | GET, POST |
| /admin/api/repositories | GET, DELETE |

**Configuration:**

- GITHUB_EMULATOR_ADMIN_USERNAME
- GITHUB_EMULATOR_ADMIN_PASSWORD

## Sub-Component: auth-oidc

**API Routes:**

| Path | Methods |
|----|--------|
| /.well-known/openid-configuration | GET |
| /.well-known/jwks.json | GET |
| /actions/oidc/token | GET |
| /login/oauth/authorize | GET |
| /login/oauth/access_token | POST |

## APIs Exposed

### HTTP Endpoints

| Path | Methods | Description |
|----|---------|-------------|
| /api/v3 | GET | GitHub REST v3 compatible API root (meta, rate_limit). |
| /repos/{owner}/{repo} | GET, PATCH, DELETE | Repository CRUD plus issues, pulls, branches, contents, releases, actions subresources. |
| /api/graphql | POST | Strawberry-based GitHub GraphQL API. |
| /api/v3/rate_limit | GET | Rate limit status endpoint. |
| /_apis/distributedtask/* | GET, POST, PATCH, PUT, DELETE | Azure DevOps-style distributed task protocol used by Actions runners. |
| /_services/pipelines/{owner}/{repo}/_apis/pipelines/runs | GET, POST, DELETE | Pipeline run registration and lifecycle for Actions. |
| /actions/runner/register | POST | Runner registration and heartbeat endpoints. |
| /app/installations/{installation_id}/access_tokens | POST | GitHub Apps installation access token issuance. |
| /login/oauth/access_token | POST | OAuth token exchange. |
| /.well-known/openid-configuration | GET | OIDC discovery for Actions tokens. |
| /actions/oidc/token | GET | OIDC token issuance for workflow jobs. |
| /admin/api/* | GET, POST, PATCH, DELETE | Admin panel API for users, tokens, orgs, repos, runners, imports, jobs. |
| /{owner}/{repo}.git/info/refs | GET | Git smart-HTTP protocol endpoints for clone, fetch, and push. |
| /webhooks | GET, POST, PATCH, DELETE | Webhook configuration and recorded payload delivery. |

## Dependencies

**External:** fastapi, uvicorn, sqlalchemy[asyncio], aiosqlite, alembic, pydantic-settings, passlib[bcrypt], python-jose[cryptography], strawberry-graphql[fastapi], httpx, pyyaml, asyncssh, pynacl, caddy (TLS, optional), GitHub Actions runner binaries (upstream runner container)

## Deployment

Deployed as a single Dockerized FastAPI/uvicorn service with persistent /data volume for SQLite, optional Caddy TLS, SSH port 2222, and companion Actions runner containers; also runnable locally via uv or a Vagrant two-VM setup with TLS. A Dockerfile.k3s variant exists for k3s-based testing.

**Variants:**

- **docker-compose**: github-emulator service plus emulator runner, with an optional real-runner profile using upstream Actions runner binaries.
- **local uvicorn**: uv run uvicorn app.main:app --reload for development, with Honcho for API+frontend coordination.
- **Vagrant TLS**: Two-VM setup (server 192.168.123.10 ghemu.local with Docker + Caddy HTTPS) and client VM for gh CLI testing.
- **k3s**: Dockerfile.k3s image variant for k3s-based deployments.

## Network Architecture

**Services:**

- **github-emulator**: Main FastAPI service exposing REST, GraphQL, web UI, Git smart-HTTP on port 8000, and SSH on 2222.

**Ingress:**

- **Caddy reverse proxy**: Automatic HTTPS with local CA terminating TLS on ports 80/443 in Docker/Vagrant setups.

**Egress:**

- **GitHub import**: Admin-driven cloning of repositories from real github.com by URL or bulk user/org import.

## Security

- **Authentication:** FastAPI dependencies in src/app/api/deps.py accept Bearer/API tokens or sessions; OAuth, GitHub App JWTs (python-jose), and Actions OIDC tokens are also supported; seed admin user with default token ghp_admin_default_token.
- **Authorization:** Source-defined per-route checks: repository access, collaborator permissions, admin-scoped /admin endpoints, and job/runner token permissions.
- **FIPS Compliance:** not applicable

**Secrets:**

- GITHUB_EMULATOR_SECRET_KEY
- GITHUB_EMULATOR_SECRET_SALT
- GITHUB_EMULATOR_ADMIN_PASSWORD
- GITHUB_EMULATOR_TOKEN
- GITHUB_EMULATOR_UI_PASSWORD
- GITHUB_EMULATOR_DEFAULT_ADMIN_TOKEN

## Multi-Tenancy

**Model:** Single-instance, GitHub-style multi-organization/user model within one shared SQLite database.

**Isolation Mechanisms:**

- Per-user and per-organization repository scoping enforced in route/service permission checks

**Shared Services:** Single shared web service, database, and Actions runner pools shared across all users and organizations

## Data Flows

- **API request handling**: Client (gh CLI, libraries, tests) sends REST/GraphQL request; deps.py authenticates; services layer reads/writes SQLite; GitHub-compatible JSON is returned.
- **Git push/clone**: git clients use smart-HTTP or SSH transports; git service updates bare repositories under the data directory, triggering workflow events.
- **Actions execution**: Workflow triggers create jobs in the distributed-task control plane; runner containers poll for jobs, execute steps, and post records, logs, and artifacts back.
- **GitHub import**: Admin panel import jobs clone external GitHub repositories into the emulator's local git storage.
- **Webhook delivery**: Repository events are recorded and delivered to configured webhook endpoints with payloads.

## Integration Points

- **gh CLI**: Operable as a GH_HOST target, including TLS via Caddy and ghemu.local.
- **GitHub Actions runners**: Both a custom emulator runner and real upstream runner binaries register and execute jobs.
- **GitHub Apps and OAuth**: App installations, installation tokens, and OAuth flows for client compatibility.
- **Webhooks**: Outbound event delivery with recorded payloads for test assertions.
- **Web UI and admin panel**: React UIs for repository browsing and administration of users, tokens, and runners.

## Concerns

- Default seeded admin credentials (admin/admin) and default token make production exposure risky; intended for testing only.
- SQLite single-file storage limits concurrency and horizontal scaling; no HA story observed.
- Encryption is configurable/deployment-dependent (Caddy TLS) rather than enforced in-app.
- Large duplicated API surface (381 endpoints) across many route modules increases maintenance burden.
- Repository and git behavior is split between API routes and git helpers with some duplicated responsibilities, noted in project guidance.

