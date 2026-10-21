# Component: jira-emulator

## Purpose

The jira-emulator is a Python/FastAPI service backed by SQLite that emulates the Jira REST API v2 and v3 surfaces (issues, JQL search, projects, workflows, auth, attachments, webhooks, tokens) plus an administrative web UI and a Model Context Protocol (MCP) server. It exists to let tooling and AI agents that target Jira run offline against seeded, disposable data instead of a real Jira instance.

## Architectural Analysis

jira-emulator is a single async Python service built on FastAPI and uvicorn with SQLAlchemy 2.0 over aiosqlite for persistence. It follows a service-layer pattern: routers under src/jira_emulator/routers handle HTTP concerns across Jira-compatible surfaces (/rest/api/2, /rest/api/3 via middleware rewrite, /rest/auth/1, /rest/pat), a services layer encapsulates business logic, models define about 21 ORM tables, and Pydantic schemas define API contracts. A Jinja2 web UI (web/routes.py) provides browsing and admin screens, and a separate FastMCP server (mcp_servers/) exposes tools for Claude integration. JQL search is implemented with a Lark context-free grammar, parser, transformer, and function library. Middleware handles authentication (permissive/strict/none modes, Basic, Bearer PAT, and cookie sessions with bcrypt-hashed passwords) and rewrites v3 requests to v2 endpoints. The container image runs supervisord to launch both the API (port 8080) and MCP (port 8081) servers, with a urlopen-based healthcheck. State lives in SQLite plus a file-system attachment directory; admin snapshot/restore/reset endpoints support test isolation. Recent work focused on JQL date/ORDER BY fidelity, serving Jira-style page URLs, and coordinating webhook workers with database resets.

## Architecture Components

| Component | Type | Purpose |
|----|----|-------|
| FastAPI application | service | App factory, lifespan, exception handlers, v3-to-v2 middleware in app.py |
| Routers layer | module | Jira-compatible REST route handlers for issues, search, projects, auth, attachments, users, webhooks, admin |
| Services layer | module | Business logic for issues, search, import, auth, workflow, attachments |
| JQL engine | module | Lark-based JQL parser, transformer, and function evaluation for search |
| SQLAlchemy models | data layer | Async ORM over SQLite via aiosqlite, ~21 tables |
| Web UI | module | Jinja2/Pico CSS templates and routes for browsing and admin screens |
| MCP server | service | FastMCP server exposing Jira tools for Claude integration on port 8081 |

## Sub-Component: REST API v2/v3

**API Routes:**

| Path | Methods |
|----|--------|
| /rest/api/2/issue | POST |
| /rest/api/2/issue/{issueIdOrKey} | GET, PUT, DELETE |
| /rest/api/2/issue/{issueIdOrKey}/comment | GET, POST |
| /rest/api/2/issue/{issueIdOrKey}/transitions | GET, POST |
| /rest/api/2/search | GET, POST |
| /rest/api/2/search/jql | GET, POST |
| /rest/api/2/project | GET |
| /rest/api/2/project/{projectIdOrKey} | GET |
| /rest/api/2/user | GET, POST, PUT |
| /rest/api/2/issue/{issueIdOrKey}/attachments | POST |

**Configuration:**

- AUTH_MODE
- DATABASE_URL
- SEED_DATA
- IMPORT_ON_STARTUP
- ATTACHMENT_DIR
- PORT

## Sub-Component: Auth API

**API Routes:**

| Path | Methods |
|----|--------|
| /rest/auth/1/session | GET, POST, DELETE |
| /rest/api/2/myself | GET |
| /rest/api/2/myself/password | PUT |
| /rest/pat/latest/tokens | GET, POST |
| /rest/pat/latest/tokens/{tokenId} | DELETE |

**Configuration:**

- AUTH_MODE

## Sub-Component: Admin API

**API Routes:**

| Path | Methods |
|----|--------|
| /api/admin/import | POST |
| /api/admin/import/file | POST |
| /api/admin/projects | POST |
| /api/admin/projects/{project_key} | DELETE |
| /api/admin/reset | POST |
| /api/admin/snapshots | GET, POST |
| /api/admin/snapshots/{name}/restore | POST |
| /api/admin/snapshots/{name} | DELETE |

## Sub-Component: Web UI

**API Routes:**

| Path | Methods |
|----|--------|
| / | GET |
| /issues | GET |
| /issue/{key} | GET |
| /issue/create | POST |
| /project/{key} | GET |
| /browse/{key} | GET |
| /admin/users | POST |
| /admin/backup | POST |
| /admin/restore/{name} | POST |
| /admin/reset | POST |

## Sub-Component: MCP server

**Configuration:**

- JIRA_TOKEN
- JIRA_MCP_URL

## APIs Exposed

### HTTP Endpoints

| Path | Methods | Description |
|----|---------|-------------|
| /rest/api/2/issue | POST | Create issue |
| /rest/api/2/issue/{issueIdOrKey} | GET, PUT, DELETE | Get, edit, delete issue |
| /rest/api/2/issue/{issueIdOrKey}/comment | GET, POST | List or add issue comments |
| /rest/api/2/issue/{issueIdOrKey}/transitions | GET, POST | Workflow transitions for an issue |
| /rest/api/2/issue/{issueIdOrKey}/properties | GET | Issue entity properties |
| /rest/api/2/issue/{issueIdOrKey}/watchers | GET, POST, DELETE | Watcher management |
| /rest/api/2/issue/{issueIdOrKey}/attachments | POST | Upload issue attachments |
| /rest/api/2/issue/{issue_key}/remotelink | GET, POST, PUT, DELETE | Remote link management |
| /rest/api/2/issueLink | POST | Create issue link |
| /rest/api/2/issueLink/{link_id} | DELETE | Delete issue link |
| /rest/api/2/issueLinkType | GET | List issue link types |
| /rest/api/2/search | GET, POST | JQL search with offset pagination |
| /rest/api/2/search/jql | GET, POST | JQL search endpoint variants |
| /rest/api/3/search | GET, POST | v3 JQL search with cursor pagination, rewritten internally to v2 |
| /rest/api/2/project | GET | List projects |
| /rest/api/2/project/{projectIdOrKey} | GET | Get project |
| /rest/api/2/project/{projectIdOrKey}/components | GET | Project components |
| /rest/api/2/component | GET, POST | List or create components |
| /rest/api/2/component/{component_id} | GET, PUT, DELETE | Component CRUD |
| /rest/api/2/version | POST | Create project version |
| /rest/api/2/user | GET, POST, PUT | User lookup and management |
| /rest/api/2/user/assignable/search | GET | Search assignable users |
| /rest/api/2/myself | GET | Current user |
| /rest/api/2/myself/password | PUT | Change own password |
| /rest/auth/1/session | GET, POST, DELETE | Cookie session login, current session, logout |
| /rest/pat/latest/tokens | GET, POST | Personal access token management |
| /rest/pat/latest/tokens/{tokenId} | DELETE | Revoke personal access token |
| /rest/api/2/attachment/{attachment_id} | GET, DELETE | Get or delete attachment metadata |
| /rest/api/2/attachment/content/{attachment_id} | GET | Download attachment content |
| /rest/api/2/attachment/thumbnail/{attachment_id} | GET | Download attachment thumbnail |
| /rest/api/2/webhook | GET, POST, PUT, DELETE | Webhook registration and management |
| /rest/api/2/webhook/failed | GET | List failed webhook deliveries |
| /rest/api/2/field | GET | List fields |
| /rest/api/2/issuetype | GET | List issue types |
| /rest/api/2/status | GET | List statuses |
| /rest/api/2/priority | GET | List priorities |
| /rest/api/2/resolution | GET | List resolutions |
| /rest/api/2/serverInfo | GET | Server information |
| /api/admin/import | POST | Import JSON data |
| /api/admin/import/file | POST | Import JSON from uploaded file |
| /api/admin/projects | POST | Create project |
| /api/admin/projects/{project_key} | DELETE | Delete project |
| /api/admin/reset | POST | Reset database to seed state |
| /api/admin/snapshots | GET, POST | List or create database snapshots |
| /api/admin/snapshots/{name}/restore | POST | Restore database snapshot |
| /api/admin/snapshots/{name} | DELETE | Delete snapshot |
| / | GET | Web UI dashboard |
| /issue/{key} | GET, POST | Web UI issue view and edit |
| /browse/{key} | GET | Jira-style issue browse URL |
| /admin/users | POST | Web UI user administration |

## Dependencies

**External:** fastapi, uvicorn, sqlalchemy, aiosqlite, pydantic, pydantic-settings, lark, jinja2, pyyaml, bcrypt, httpx, python-multipart, mcp (FastMCP)

## Deployment

Runs as a single container (Docker/Podman) using supervisord to launch both the FastAPI app on port 8080 and the MCP server on port 8081, with an HTTP urlopen healthcheck against /rest/api/2/priority. Data persists in a /data volume (SQLite database, attachments, snapshots).

**Variants:**

- **container (podman/docker)**: Make run builds and runs the image with supervisord managing API and MCP servers; k3s variant Dockerfile also provided
- **local dev**: make serve / serve-mcp / serve-all run uvicorn with auto-reload on ports 8080/8081

## Network Architecture

**Services:**

- **jira-emulator**: FastAPI REST + web UI service listening on port 8080
- **MCP server**: FastMCP service for Claude integration on port 8081

**Ingress:**

- **HTTP on port 8080**: Direct HTTP access to API and web UI; no ingress controller or TLS termination defined in-repo

**Egress:**

- **webhook delivery**: Registered webhooks are delivered outbound to external URLs via httpx

## Security

- **Authentication:** Auth middleware supports Basic (bcrypt-hashed passwords), Bearer personal access tokens, and cookie sessions; AUTH_MODE selects permissive (default, seeded admin:admin), strict, or none.
- **Authorization:** Source-defined, coarse-grained; admin surfaces require admin credentials in strict mode. No RBAC framework.
- **FIPS Compliance:** not applicable

**Secrets:**

- JIRA_TOKEN (MCP server env var)
- JIRA_API_TOKEN (issue-export script env var)

## Multi-Tenancy

**Model:** Single-tenant emulator; all projects and users share one SQLite database.

**Isolation Mechanisms:**

- Per-project issue key sequences
- Fresh in-memory database per test via fixtures

**Shared Services:** Shared SQLite database and attachment directory

## Data Flows

- **issue CRUD**: REST/web requests flow through routers to services to async SQLAlchemy models in SQLite, returning Jira-format JSON or ADF
- **JQL search**: JQL strings are parsed by the Lark grammar, transformed, and evaluated against the database to return paginated results
- **attachment upload/download**: Multipart uploads stored under ATTACHMENT_DIR; downloads served via /rest/api/2/attachment/content
- **webhook delivery**: Issue events enqueue webhook deliveries dispatched outbound via httpx, with retry and failed-delivery tracking
- **import and snapshots**: Admin JSON import loads data; snapshots copy and restore the SQLite database for test isolation

## Integration Points

- **Jira REST API v2/v3 clients**: Any Jira client or SDK can target the emulator's Jira-compatible endpoints
- **MCP / Claude**: FastMCP server exposes Jira tools (issue read/write, search) for AI agents
- **webhooks**: Outbound webhook registration and delivery emulating Jira webhooks

## Concerns

- Default permissive AUTH_MODE with seeded admin:admin credentials is insecure if exposed beyond local development
- SQLite single-file database limits concurrency and provides no high-availability story
- Analyzer found no TLS termination, ingress, or FIPS posture defined in-repo; encryption is configurable/external
- Two declared dependencies (e.g. honcho, mypy) are unused in shipped source per analyzer import analysis

