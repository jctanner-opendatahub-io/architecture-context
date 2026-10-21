# Component: gitlab-emulator

## Purpose

GitLab Emulator is a lightweight FastAPI service that mimics the GitLab REST v4 API, GraphQL API, GitLab Runner coordinator endpoints, and Git transports (Smart HTTP and SSH). It stores data in SQLite via aiosqlite with bare git repositories on disk, and provides a web UI, an admin panel, webhooks, TLS via Caddy, and a MinIO-backed runner cache, enabling end-to-end testing of GitLab client tooling in CI or local environments.

## Architectural Analysis

GitLab Emulator is a single-process Python FastAPI application (app/main.py) that composes many routers: GitLab REST v4 API modules under app/api (projects, groups, pipelines, runner coordinator, merge requests, etc., ~550 endpoints), a Strawberry GraphQL schema under app/graphql, server-rendered web and admin UIs under app/web and app/admin, and Git Smart HTTP plus SSH transport handlers under app/git. Persistence uses SQLAlchemy async with SQLite/aiosqlite (WAL mode) plus bare git repositories on the filesystem; alembic manages schema migrations. Authentication supports personal access tokens (SHA-256 hashed), HTTP Basic, and JWT (python-jose), enforced via FastAPI dependencies in app/api/deps.py. Background asyncio workers handle pipeline schedules. Deployment is via Docker Compose with Caddy TLS termination, an optional MinIO runner-cache service, and a Vagrant three-VM topology (server, client, runner) for full glab/gitlab-runner validation. The project is a rename/scaffold of github_emulator with GitLab-specific routes still maturing (per STATUS.md).

## Architecture Components

| Component | Type | Purpose |
|----|----|-------|
| FastAPI application factory | application entrypoint | Wires routers, middleware, GraphQL, admin UI, git transports, SSH server, and pipeline schedule worker in one process. |
| REST v4 API modules | HTTP API layer | Implements GitLab REST v4 endpoints for projects, groups, pipelines, merge requests, issues, runner coordination, and more. |
| GraphQL API | HTTP API layer | Strawberry-based implementation of common GitLab GraphQL queries and mutations at /api/graphql. |
| Admin panel | web UI | Server-rendered management of users, tokens, orgs, repos, imports, CI variables, and CI Lab experiments. |
| Web UI | web UI | Browser interface for repositories, files, commits, issues, and merge-request-style review objects. |
| Git transports | protocol handler | Git Smart HTTP and SSH (port 2222) clone, fetch, and push against bare repositories on disk. |
| Database layer | persistence | Async SQLAlchemy engine over SQLite/aiosqlite with WAL mode and alembic migrations. |
| Auth dependencies | security | Validates personal access tokens, HTTP Basic, and JWT; enforces authentication per request. |
| Pipeline schedule worker | background worker | Asyncio task that materializes scheduled pipelines at a configurable interval. |
| Runner coordinator | service endpoint | GitLab-runner job request/update/trace endpoints for validating official runners. |

## Sub-Component: app/api

**API Routes:**

| Path | Methods |
|----|--------|
| /api/v4/projects | GET, POST |
| /api/v4/groups | GET, POST |
| /api/v4/pipelines | GET, POST |
| /api/v4/runner | POST |
| /admin/ci/variables | GET, POST |
| / | GET |

**Configuration:**

- GITLAB_EMULATOR_BASE_URL
- GITLAB_EMULATOR_SECRET_KEY
- GITLAB_EMULATOR_RUNNER_REGISTRATION_TOKEN

## Sub-Component: app/admin

**API Routes:**

| Path | Methods |
|----|--------|
| /admin/ | GET |
| /admin/login | GET, POST |
| /admin/ci-lab | GET |
| /admin/import | GET, POST |

## Sub-Component: app/graphql

**API Routes:**

| Path | Methods |
|----|--------|
| /api/graphql | POST, GET |

## Sub-Component: app/git

**API Routes:**

| Path | Methods |
|----|--------|
| /{owner}/{repo}.git/info/refs | GET |
| /{owner}/{repo}.git/git-upload-pack | POST |

**Configuration:**

- GITLAB_EMULATOR_SSH_ENABLED
- GITLAB_EMULATOR_SSH_PORT
- GITLAB_EMULATOR_SSH_HOST_KEY_PATH

## APIs Exposed

### HTTP Endpoints

| Path | Methods | Description |
|----|---------|-------------|
| /api/v4/* | GET, POST, PUT, DELETE | GitLab REST API v4 surface covering projects, groups, pipelines, merge requests, issues, runners, and more (~550 routes). |
| /api/graphql | POST, GET | Strawberry GraphQL API for common GitLab queries and mutations. |
| /ui/ | GET | Web UI for browsing repositories, commits, issues, and reviews. |
| /admin/ | GET, POST | Admin panel for users, tokens, orgs, repos, imports, CI variables, and CI Lab. |
| / | GET | Service root endpoint identifying gitlab-emulator. |

## Dependencies

**External:** fastapi, uvicorn, sqlalchemy, aiosqlite, alembic, strawberry-graphql, python-jose, pydantic-settings, caddy (TLS proxy), minio (runner cache, optional), gitlab-runner (validation, external)

## Deployment

Runs as a single container via Docker Compose with Caddy TLS on 443, HTTP on 80, API on 8000, and SSH on 2222, persisting SQLite and repos in a Docker volume; a Vagrant three-VM setup supports full glab/gitlab-runner validation.

**Variants:**

- **docker-compose**: Single gitlab-emulator service plus optional MinIO runner-cache and minio-init services; TLS via Caddy with hostname glemu.local.
- **vagrant-three-vm**: server (emulator in Docker), client (glab and git smoke tests), and runner (official gitlab-runner with Docker executor) VMs.
- **local/uvicorn**: Direct uvicorn execution of the FastAPI app per pyproject.toml for development.

## Network Architecture

**Services:**

- **gitlab-emulator**: Main service exposing REST, GraphQL, web UI, admin, Git HTTP on 8000 and Git SSH on 2222.
- **minio**: Optional S3-compatible runner cache backend on ports 9000/9001.

**Ingress:**

- **Caddy**: TLS termination and automatic HTTPS with local CA on ports 80/443 for glemu.local.

**Egress:**

- **GitLab import**: Admin-driven clone of remote GitLab repos by URL or bulk user/org import.
- **CI remote includes**: Pipeline YAML include:remote fetches restricted by CI_REMOTE_INCLUDE_ALLOWED_HOSTS allowlist.

## Security

- **Authentication:** Supports personal access tokens (SHA-256 hashed lookup), HTTP Basic, and JWT/OAuth via python-jose, enforced through FastAPI dependencies; admin sessions use username/password login.
- **Authorization:** Source-defined per-route authentication requirements; admin panel gated by session login; no fine-grained RBAC beyond basic user scoping.
- **FIPS Compliance:** not applicable

**Secrets:**

- GITLAB_EMULATOR_SECRET_KEY (JWT/session signing, default change-me-in-production)
- GITLAB_EMULATOR_ADMIN_USERNAME/ADMIN_PASSWORD (default admin/admin)
- GITLAB_EMULATOR_RUNNER_REGISTRATION_TOKEN

## Multi-Tenancy

**Model:** Single-tenant emulator instance with multiple simulated users, organisations/groups, and repositories sharing one database.

**Isolation Mechanisms:**

- Owner/org namespacing of repositories
- Per-user personal access tokens

**Shared Services:** Shared SQLite database, Shared filesystem data directory for bare repositories

## Data Flows

- **REST/GraphQL request flow**: Client requests hit FastAPI routers, are authenticated via deps.py, and read/write SQLite through async SQLAlchemy sessions.
- **Git transport flow**: git clone/fetch/push over Smart HTTP or SSH operate directly on bare repositories under DATA_DIR/repos.
- **Runner coordination flow**: gitlab-runner polls the coordinator API for jobs, updates statuses and traces, and uses MinIO as cache/artifact store.
- **Webhook delivery flow**: Emulator records event payloads and delivers webhooks to registered consumer endpoints.
- **Import flow**: Admin panel clones remote GitLab repositories into local bare storage for local browsing and testing.

## Integration Points

- **glab CLI**: Intended compatibility target for GitLab CLI workflows against REST and GraphQL APIs.
- **gitlab-runner**: Official runner validates via coordinator endpoints, registration token, and MinIO cache.
- **Git clients**: Standard git over Smart HTTP and SSH for clone, fetch, and push.
- **Webhook consumers**: External services receive recorded event payloads from the emulator.

## Concerns

- Project is an in-progress rename/scaffold of github_emulator; GitLab-specific routes and schemas are incomplete per STATUS.md.
- Default secrets and admin credentials (change-me-in-production, admin/admin) are insecure if deployed beyond testing.
- Very large flat REST surface (~550 routes) in a single service with no HA or ingress evidence.
- SQLite storage limits concurrency and scale, acceptable only for an emulator.

