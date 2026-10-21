# Component: github-emulator

## Purpose

github-emulator implements a GitHub-compatible REST, GraphQL, Git smart HTTP/SSH, GitHub Actions, GitHub App, and OAuth/OIDC surface backed by a local SQLite (or configurable) SQLAlchemy database, so that tools and CI systems that target github.com can be tested end-to-end without real GitHub. It includes an admin web UI, webhook delivery, repository import, and bundled or upstream Actions runners.

## Architectural Analysis

github-emulator is a single Python FastAPI service (src/app/main.py) that wires together roughly 40 API routers under /api/v3 plus /graphql, OAuth, OIDC, admin, browser-UI, Git smart HTTP, and Azure DevOps-style distributed-task/Actions endpoints — 381 HTTP routes total. Middleware layers handle authentication (personal access tokens, GitHub App JWT/installation tokens, OAuth tokens, job tokens via src/app/api/deps.py and middleware/auth.py), rate limiting, ETags, security headers, and request IDs. Persistence uses SQLAlchemy async with a default SQLite (aiosqlite) database and Alembic migrations; Git repositories are stored as bare repos on disk under DATA_DIR and served via smart HTTP and an asyncssh SSH server. Business logic lives in ~30 service modules (workflows, actions, issues, PRs, search, webhooks, import, secrets crypto with libsodium). Two runner variants (emulator and upstream) execute Actions jobs. The service is stateful and single-instance (in-memory caches, SQLite default, local disk), exposed via supervisord-managed container on ports 80/443/8000/2222.

## Architecture Components

| Component | Type | Purpose |
|----|----|-------|
| FastAPI app factory | application entrypoint | Wires routers, middleware, GraphQL schema, admin frontend, and Git smart HTTP handler (src/app/main.py) |
| API routers | HTTP API layer | ~40 routers in src/app/api implementing GitHub-compatible REST v3, Actions, distributed task, pipelines, admin, and UI endpoints |
| GraphQL schema | API layer | Strawberry GraphQL router mounted at /graphql and /api/graphql |
| Auth middleware and dependencies | security layer | Token authentication (PATs, app JWTs, installation and job tokens) via middleware/auth.py and api/deps.py |
| Cross-cutting middleware | middleware layer | Rate limiting, ETag, security headers, request IDs, error handling, API versioning, memory watch |
| Service layer | business logic | ~30 services for workflows, actions scheduling, issues, PRs, reviews, search, webhooks, imports, secrets |
| ORM models and migrations | data layer | SQLAlchemy async models in src/app/models with Alembic migrations |
| Git transport | protocol handlers | Smart HTTP and SSH (asyncssh) serving of on-disk bare repositories |
| Admin and web UI | frontend | Admin dashboard routes and templates for users, tokens, orgs, repos, jobs, runners |
| Actions runners | worker processes | Emulator-native and upstream GitHub runner containers that poll for and execute workflow jobs |

## Sub-Component: api

**API Routes:**

| Path | Methods |
|----|--------|
| /api/v3/{rest of GitHub v3 surface} | GET, POST, PATCH, PUT, DELETE |
| /graphql | GET, POST |
| /repos/{owner}/{repo}/info/lfs | POST |
| /_apis/distributedtask/* | GET, POST, PATCH, PUT, DELETE, OPTIONS |
| /_services/pipelines/* | GET, POST, DELETE |

**Upstream Dependencies:** SQLite database (aiosqlite), on-disk bare git repositories, libgit2/git CLI operations, upstream GitHub Actions runner images

**Configuration:**

- GITHUB_EMULATOR_ prefixed pydantic settings (src/app/config.py)
- GITHUB_EMULATOR_DATABASE_URL
- GITHUB_EMULATOR_DATA_DIR
- GITHUB_EMULATOR_SEED_DATA
- GITHUB_EMULATOR_BASE_URL

## Sub-Component: git transport

**API Routes:**

| Path | Methods |
|----|--------|
| /{owner}/{repo}.git/info/refs | GET |
| /{owner}/{repo}.git/git-upload-pack | POST |
| /{owner}/{repo}.git/git-receive-pack | POST |

**Upstream Dependencies:** bare repository storage on local filesystem

**Configuration:**

- SSH server settings (port 2222)
- DATA_DIR repos directory

## Sub-Component: admin UI

**API Routes:**

| Path | Methods |
|----|--------|
| /admin/api/* | GET, POST, PATCH, DELETE |
| /admin | GET |

**Upstream Dependencies:** service layer, database

**Configuration:**

- GITHUB_EMULATOR_UI_PASSWORD
- admin user seeding

## Sub-Component: runners

**API Routes:**

| Path | Methods |
|----|--------|
| /actions/runner/register | POST |
| /actions/runner/jobs | GET |
| /actions/runner/heartbeat | POST |

**Upstream Dependencies:** github-emulator service for job dispatch and logs

**Configuration:**

- GITHUB_EMULATOR_TOKEN
- runner registration tokens

## APIs Exposed

### HTTP Endpoints

| Path | Methods | Description |
|----|---------|-------------|
| /api/v3 | GET | GitHub v3 REST API root; ~40 routers cover repos, issues, pulls, actions, orgs, users, gists, search, and more |
| /graphql | GET, POST | Strawberry GraphQL API mirroring GitHub GraphQL surface |
| /login/oauth/authorize | GET | OAuth authorization endpoint for the OAuth device/web flow |
| /login/oauth/access_token | POST | OAuth token exchange endpoint |
| /.well-known/openid-configuration | GET | OIDC discovery document for Actions OIDC |
| /.well-known/jwks.json | GET | JWKS endpoint for OIDC token signing keys |
| /actions/oidc/token | GET | OIDC token issuance for Actions jobs |
| /app/installations/{installation_id}/access_tokens | POST | GitHub App installation access token creation |
| /repos/{owner}/{repo}/info/lfs | POST | Git smart HTTP protocol (info/refs, upload-pack, receive-pack) served from local bare repos |
| /_apis/distributedtask/* | GET, POST, PATCH, PUT, DELETE | Azure DevOps-style distributed task endpoints used by GitHub Actions runners (pools, agents, messages, plans, timelines) |
| /_services/pipelines/{owner}/{repo}/_apis/pipelines/runs | GET, POST | Actions pipelines run registration and listing for runners |
| /admin/api/* | GET, POST, PATCH, DELETE | Admin management API for users, tokens, orgs, repositories, jobs, runners, imports |
| /api/_ui/* | GET, POST, DELETE | Browser web UI session and repository browsing endpoints |

## Dependencies

**External:** FastAPI and uvicorn, SQLAlchemy 2 (async) with aiosqlite, Alembic migrations, python-jose (JWT/OAuth), strawberry-graphql, asyncssh, passlib/bcrypt, httpx, PyYAML, libsodium sealed boxes for Actions secrets

## Deployment

Deployed as a single container (Dockerfile, Dockerfile.k3s) running supervisord, which starts uvicorn on port 8000, an SSH git server on 2222, and web proxies on 80/443; docker-compose and Caddy reverse proxy configurations are provided. No Kubernetes manifests or HA topology exist.

**Variants:**

- **docker-compose**: docker-compose.yml / podman-compose.local.yml running the emulator container with Caddy reverse proxy
- **k3s container**: Dockerfile.k3s variant for k3s-based local deployments
- **local dev**: uv run uvicorn app.main:app --reload with Procfile.dev/honcho
- **runner containers**: src/runners/emulator and src/runners/upstream Dockerfiles for Actions runner executors

## Network Architecture

**Services:**

- **github-emulator**: Single FastAPI service exposing HTTP API (8000, proxied on 80/443) and SSH git transport (2222)

**Ingress:**

- **Caddy reverse proxy**: Caddyfile-configured proxy terminating HTTP/HTTPS (ports 80/443) in front of uvicorn

**Egress:**

- **webhook delivery**: Emulator pushes webhook events to registered external receiver URLs via httpx
- **repository import**: Import service clones/fetches source repositories from remote git hosts during admin-triggered imports
- **upstream runners**: Upstream runner variant pulls job archives and actions from the emulator and may fetch public actions

## Security

- **Authentication:** Bearer or token-authorization personal access tokens, GitHub App JWTs and installation tokens, OAuth tokens, and Actions job tokens, resolved per-request in src/app/api/deps.py and middleware/auth.py; seeded default admin token ghp_admin_default_token.
- **Authorization:** Repository visibility, collaborator permissions, fine-grained token permissions, and job-token route permissions (job_permissions.py) checked per route; anonymous access allowed for public data.
- **FIPS Compliance:** not applicable

**Secrets:**

- GITHUB_EMULATOR_DEFAULT_ADMIN_TOKEN
- GITHUB_EMULATOR_SECRET_SALT
- GITHUB_EMULATOR_UI_PASSWORD
- GITHUB_EMULATOR_ADMIN_PASSWORD
- GITHUB_EMULATOR_TOKEN (runner)

## Multi-Tenancy

**Model:** Single-tenant emulator instance; multi-user accounts, organizations, and repositories within one shared database.

**Isolation Mechanisms:**

- Repository visibility (public/private) and collaborator permission checks
- Fine-grained token permission scopes
- Organization/team membership checks

**Shared Services:** Shared SQLite/database and shared filesystem Git storage across all users and repositories

## Data Flows

- **API request flow**: Request hits middleware (auth, rate limit, ETag) then a route handler, which calls service-layer logic against the async SQLAlchemy database and on-disk git storage.
- **Git push/pull flow**: Git clients use smart HTTP or SSH against bare repositories in DATA_DIR/repos; hooks and services update commit, ref, and status records.
- **Actions execution flow**: Workflow triggers create runs/jobs in the database; runners poll distributed-task endpoints, execute jobs, and post back logs, timelines, and completion records.
- **Webhook delivery flow**: Event service records events and webhook_service pushes signed payloads to registered external webhook URLs asynchronously.
- **Repository import flow**: Admin import jobs clone remote repositories into local storage and index their contents for the emulator.

## Integration Points

- **GitHub-compatible REST/GraphQL clients**: Any github.com-targeting client (gh CLI, SDKs) pointed at the emulator base URL
- **Git clients**: Standard git push/fetch over HTTPS smart HTTP and SSH
- **GitHub Actions runners**: Emulator and upstream runner agents registering via distributed-task/pipelines endpoints
- **GitHub Apps and OAuth apps**: App JWT signing, installation tokens, and OAuth flows for integration testing
- **Webhook receivers**: External services receiving signed webhook event deliveries

## Concerns

- Single-instance, stateful design (SQLite default, local filesystem, in-memory caches) precludes horizontal scaling and high availability
- Default seeded admin credentials and token create security risk if defaults are not overridden in exposed deployments
- Very large API surface (381 endpoints) with some duplicated responsibility between API routes and git/service code, increasing maintenance burden
- Broad egress (webhooks, imports) from a testing tool could be abused if deployed outside a trusted network

