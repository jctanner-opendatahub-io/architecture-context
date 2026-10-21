# Component: gitlab-emulator

## Purpose

gitlab-emulator is a Python/FastAPI service that emulates GitLab REST API v4, a Strawberry-based GraphQL API, Git Smart HTTP and SSH transports, CI pipeline and runner coordinator endpoints, webhooks, a web UI, and an admin panel. It stores data in SQLite via aiosqlite with bare git repositories on disk, and runs as a single container (with Caddy TLS and optional MinIO runner cache) for local or CI testing.

## Architectural Analysis

The service is a single FastAPI application (app/main.py) that mounts a REST router tree under /api/v4, GraphQL under /graphql and /api/graphql, admin panel routes under /admin, a web UI under /ui, and Git Smart HTTP endpoints. Routers in app/api cover projects, groups, pipelines, jobs, runner coordination, issues, merge requests, webhooks, and more (552 registered endpoints). Cross-cutting middleware (app/middleware) handles auth, API versioning, rate limiting, ETag, request IDs, security headers, and errors. Domain logic lives in app/services (CI variables, secrets, pipelines, webhooks, imports, permissions), git storage in app/git (bare repos, smart HTTP, SSH server), and persistence in SQLAlchemy async models over SQLite/aiosqlite (app/database.py, alembic migrations). Configuration is pydantic-settings based (app/config.py), served by uvicorn under supervisord, fronted by Caddy for TLS. No CRDs, gRPC services, or Kubernetes workloads; deployment is Docker Compose or Vagrant VMs.

## Architecture Components

| Component | Type | Purpose |
|----|----|-------|
| FastAPI app (app/main.py) | service | Assembles routers, middleware, GraphQL, admin, web UI, and git endpoints into one ASGI application |
| REST API v4 routers (app/api) | api | GitLab-compatible REST endpoints for projects, groups, pipelines, jobs, runners, issues, and more |
| GraphQL API (app/graphql) | api | Strawberry-based GitLab-style GraphQL queries and mutations |
| Admin panel (app/admin) | web ui | Server-rendered UI for users, tokens, orgs, repos, CI variables, imports, and CI Lab |
| Web UI (app/web) | web ui | Repository, commit, issue, and merge-request browsing interface |
| Git transport (app/git) | service | Smart HTTP and SSH git clone/fetch/push against on-disk bare repositories |
| Services layer (app/services) | service | Domain logic: CI variables/secrets, pipelines, webhooks, imports, permissions, users |
| Persistence (app/models, app/database.py, alembic) | data | SQLAlchemy async ORM over SQLite/aiosqlite with Alembic migrations |
| Middleware (app/middleware) | middleware | Auth, API version, rate limiting, ETag, request ID, security headers, error handling |
| Runner coordinator (app/api/runner.py) | api | gitlab-runner job request, trace, artifact, and cache endpoints |

## Sub-Component: REST API v4

**API Routes:**

| Path | Methods |
|----|--------|
| /api/v4/projects/{project_ref:path} | GET, POST, PUT, DELETE |
| /api/v4/groups/{group_ref:path} | GET, POST |
| /api/v4/projects/{project_id}/pipelines | GET, POST |
| /api/v4/projects/{project_ref:path}/jobs/{job_id}/{action} | POST |
| /api/v4/jobs/request | POST |
| /api/v4/user | GET |

**Upstream Dependencies:** SQLite database via SQLAlchemy async, Bare git repositories on local disk

**Configuration:**

- GITLAB_EMULATOR_DATABASE_URL
- GITLAB_EMULATOR_DATA_DIR
- GITLAB_EMULATOR_BASE_URL

## Sub-Component: Admin panel

**API Routes:**

| Path | Methods |
|----|--------|
| /admin/ | GET |
| /admin/login | GET, POST |
| /admin/users | GET, POST |
| /admin/tokens | GET, POST |
| /admin/ci-lab/pipelines | POST |
| /admin/import | GET, POST |

**Upstream Dependencies:** REST API services layer, SQLite database

**Configuration:**

- GITLAB_EMULATOR_ADMIN_USERNAME
- GITLAB_EMULATOR_ADMIN_PASSWORD

## Sub-Component: Git transport

**API Routes:**

| Path | Methods |
|----|--------|
| /{owner}/{repo}.git/info/refs | GET |
| /{owner}/{repo}.git/git-upload-pack | POST |
| /{owner}/{repo}.git/git-receive-pack | POST |

**Upstream Dependencies:** Bare git repositories on local disk

**Configuration:**

- GITLAB_EMULATOR_SSH_ENABLED
- GITLAB_EMULATOR_SSH_PORT

## Sub-Component: GraphQL API

**API Routes:**

| Path | Methods |
|----|--------|
| /api/graphql | GET, POST |
| /graphql | GET, POST |

**Upstream Dependencies:** Strawberry GraphQL schema over service layer, SQLite database

## APIs Exposed

### HTTP Endpoints

| Path | Methods | Description |
|----|---------|-------------|
| /api/v4/{...} | GET, POST, PUT, PATCH, DELETE | GitLab REST API v4 emulation: projects, groups, pipelines, jobs, runners, issues, merge requests, variables, webhooks, etc. |
| /api/graphql | GET, POST | Strawberry-based GitLab-compatible GraphQL endpoint |
| /admin/ | GET, POST | Admin panel UI for users, tokens, orgs, repos, CI variables, and imports |
| /ui/ | GET | Web UI for browsing repositories, commits, issues, and reviews |
| /jobs/request | POST | Runner coordinator endpoint for job requests from gitlab-runner |
| /login/oauth/authorize | GET | OAuth authorize emulation endpoint |
| /login/oauth/access_token | POST | OAuth token issuance emulation endpoint |

## Dependencies

**External:** fastapi, uvicorn, sqlalchemy (async), aiosqlite, pydantic-settings, python-jose (JWT/OAuth), passlib (bcrypt), strawberry-graphql, jinja2, httpx, PyYAML, Caddy (TLS reverse proxy, container), MinIO (runner cache, container), gitlab-runner (validation, external)

## Deployment

Single Python container running uvicorn under supervisord, fronted by Caddy for TLS, deployed via Docker Compose with MinIO for runner cache; a Vagrant three-VM setup (server, client, runner) exists for full glab/runner validation. No Kubernetes manifests.

**Variants:**

- **Docker Compose**: gitlab-emulator service exposing 80/443/8000/2222 with persistent volume, plus MinIO and minio-init services
- **Vagrant three-VM**: server VM (Docker emulator with TLS at glemu.local), client VM (glab/git smoke tests), runner VM (gitlab-runner with Docker executor)
- **Local development**: uvicorn/pip run directly from pyproject.toml with SQLite in local data directory

## Network Architecture

**Services:**

- **gitlab-emulator**: Single HTTP service exposing REST API, GraphQL, admin, web UI, and git Smart HTTP on ports 80/443/8000, plus SSH on 2222

**Ingress:**

- **Caddy**: Reverse proxy providing automatic HTTPS with a local CA for realistic glab/git testing

**Egress:**

- **GitLab import**: Outbound cloning of repositories from real GitLab by URL or bulk user/org import via admin panel

## Security

- **Authentication:** Bearer tokens / personal access tokens and API keys validated in app/api/deps.py; JWT sessions via python-jose; admin session login; runner registration token for gitlab-runner.
- **Authorization:** Source-defined role and permission checks via app/services/permissions.py and route-level dependencies
- **FIPS Compliance:** not applicable

**Secrets:**

- GITLAB_EMULATOR_SECRET_KEY (JWT/session signing)
- GITLAB_EMULATOR_ADMIN_PASSWORD
- RUNNER_REGISTRATION_TOKEN
- CI variables and group/project secrets stored in database
- MinIO root credentials in docker-compose.yml

## Multi-Tenancy

**Model:** Single-instance emulator shared by test clients; users, organizations/groups, and projects are modeled within one database

**Isolation Mechanisms:**

- Per-user and per-group permission checks in app/services/permissions.py
- Token-scoped access via personal access tokens

**Shared Services:** Single shared SQLite database, Shared bare repository storage on the data volume

## Data Flows

- **API request handling**: Client requests pass middleware chain (auth, rate limit, versioning) to FastAPI routers, which call services layer and persist via SQLAlchemy async to SQLite
- **Git operations**: Smart HTTP/SSH git clone, fetch, and push operate directly on bare repositories stored under the data directory
- **CI runner coordination**: gitlab-runner polls /jobs/request, updates job traces, and uploads artifacts and cache (MinIO) back to the emulator
- **GitLab import**: Admin-triggered jobs clone upstream GitLab repos into local bare repositories and record job status
- **Webhook delivery**: Event service records webhook payloads and delivers them to registered hook URLs

## Integration Points

- **GitLab clients**: REST v4, GraphQL, OAuth, and git HTTP/SSH endpoints compatible with glab CLI, git, and client libraries
- **gitlab-runner**: Official runner connects as coordinator for job requests, traces, artifacts, and S3-style cache
- **Real GitLab**: Import service clones repositories from upstream GitLab instances
- **Webhook consumers**: Registered group and project hook URLs receive event payloads

## Concerns

- Default admin credentials (admin/admin) and placeholder secret key must be changed before any shared use
- Project is a scaffold preserving github_emulator architecture; GitLab-specific routes and schemas are still in progress per STATUS.md
- No Kubernetes deployment manifests, probes, or HA story — single container with SQLite is single-point-of-failure by design
- Very large route surface (552 endpoints) with many admin routes using POST-based form actions rather than REST verbs
- Runner coordinator compatibility and CI behavior are still being implemented (GITLAB_STATUS.md)

