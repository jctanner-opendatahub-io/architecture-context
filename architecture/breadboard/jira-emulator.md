# Component: jira-emulator

## Purpose

A Python/FastAPI service backed by SQLite that emulates the Jira REST API (v2 and v3) for offline development and testing. It provides feature parity with real Jira for issues, JQL search, projects, workflows, users, attachments, webhooks, personal access tokens, and admin snapshots, plus a Jinja2 web UI and a FastMCP server exposing seven tools for Claude integration.

## Architectural Analysis

The emulator is an async-first Python service using a layered design: FastAPI routers handle HTTP concerns, a services layer encapsulates business logic, SQLAlchemy 2.0 async models (~21 tables) persist to SQLite via aiosqlite, and Pydantic schemas define API contracts. JQL search is implemented with a Lark context-free grammar, parser, and transformer. Three first-class API surfaces exist: REST v2, REST v3 (rewritten to v2 endpoints via middleware, with cursor pagination and ADF branching), and an MCP server (port 8081). A Jinja2/Pico CSS web UI offers browsing and admin functions. Auth is enforced via FastAPI dependency/middleware supporting Basic, Bearer/PAT, and cookie session modes, configurable permissive/strict/none via AUTH_MODE. Deployment is a single container (podman, port 8080) supervised by supervisord, running both API and MCP servers, with SQLite and attachments on a persistent /data volume.

## Architecture Components

| Component | Type | Purpose |
|----|----|-------|
| FastAPI REST API (v2/v3) | HTTP API layer | Jira-compatible REST endpoints for issues, search, projects, users, attachments, webhooks, tokens, and admin operations |
| Service layer | business logic | Encapsulates issue, search, import, auth, and workflow business logic behind routers |
| SQLAlchemy async models | data layer | ~21 ORM tables persisted to SQLite via aiosqlite |
| JQL engine | query engine | Lark-based JQL grammar, parser, transformer, and functions for issue search |
| Web UI | Jinja2 web application | Browser interface for browsing issues, projects, and admin operations (Pico CSS) |
| MCP server | Model Context Protocol service | FastMCP server on port 8081 exposing seven Jira tools for Claude integration |
| Auth middleware | security middleware | Enforces Basic, Bearer/PAT, and cookie session authentication per AUTH_MODE |

## Sub-Component: routers

**API Routes:**

| Path | Methods |
|----|--------|
| /rest/api/2/issue | POST, GET, PUT, DELETE |
| /rest/api/2/search | GET, POST |
| /rest/api/2/search/jql | GET, POST |
| /rest/api/2/project | GET |
| /rest/api/2/myself | GET, PUT |
| /rest/auth/1/session | GET, POST, DELETE |
| /rest/pat/latest/tokens | GET, POST |
| /rest/api/2/webhook | GET, POST, PUT, DELETE |
| /api/admin/snapshots | GET, POST |

**Configuration:**

- AUTH_MODE
- DATABASE_URL
- SEED_DATA
- IMPORT_ON_STARTUP

## Sub-Component: jql

**Upstream Dependencies:** lark

## Sub-Component: web UI

**API Routes:**

| Path | Methods |
|----|--------|
| / | GET |
| /issues | GET |
| /issue/{key} | GET, POST |
| /browse/{key} | GET |
| /admin/users | GET, POST |
| /admin/backup | POST |
| /admin/reset | POST |

**Upstream Dependencies:** jinja2

## Sub-Component: mcp_servers

**Upstream Dependencies:** mcp, jira_emulator HTTP API

**Configuration:**

- JIRA_TOKEN
- MCP port 8081

## APIs Exposed

### HTTP Endpoints

| Path | Methods | Description |
|----|---------|-------------|
| /rest/api/2/issue/{issueIdOrKey} | GET, PUT, DELETE | Fetch, edit, and delete issues (v2; v3 rewritten via middleware) |
| /rest/api/2/issue | POST | Create issues |
| /rest/api/2/issue/{issueIdOrKey}/comment | GET, POST | List and add issue comments |
| /rest/api/2/issue/{issueIdOrKey}/transitions | GET, POST | List and perform workflow transitions |
| /rest/api/2/search | GET, POST | JQL search with offset pagination (v2) or cursor pagination (v3) |
| /rest/api/2/search/jql | GET, POST | JQL search endpoint variants |
| /rest/api/2/project | GET | List projects and components/versions |
| /rest/api/2/user | GET, POST, PUT | User lookup and management |
| /rest/api/2/myself | GET, PUT | Current user info and password change |
| /rest/auth/1/session | GET, POST, DELETE | Cookie session login/logout |
| /rest/pat/latest/tokens | GET, POST, DELETE | Personal access token management |
| /rest/api/2/issue/{issueIdOrKey}/attachments | POST | Attachment upload (files stored on disk) |
| /rest/api/2/webhook | GET, POST, PUT, DELETE | Webhook registration and management |
| /api/admin/snapshots | GET, POST | Database snapshot list and creation |
| /api/admin/snapshots/{name}/restore | POST | Restore database from snapshot |
| /api/admin/reset | POST | Reset emulator database |
| / | GET | Web UI dashboard |

## Dependencies

**External:** FastAPI, Uvicorn, SQLAlchemy 2.0 (aiosqlite), Pydantic 2.5+ / pydantic-settings, Lark, Jinja2, bcrypt, FastMCP (mcp), httpx, python-multipart, PyYAML, SQLite

## Deployment

Single-container service (podman/docker) supervised by supervisord, running the FastAPI API on port 8080 and the MCP server on port 8081, with SQLite database and attachments on a persistent /data volume. A healthcheck probes /rest/api/2/priority. Dev mode runs uvicorn with auto-reload via the Makefile.

**Variants:**

- **Local dev**: uv run uvicorn with auto-reload on port 8080; make serve / serve-all
- **Container (podman)**: make run builds and runs a container on port 8080 with supervisord, persistent /data volume, healthcheck
- **k3s**: Dockerfile.k3s variant with same supervisord entrypoint and healthcheck for k3s deployment

## Network Architecture

**Services:**

- **jira-emulator**: Single self-contained service exposing HTTP API on port 8080 and MCP on 8081

**Egress:**

- **webhook delivery**: Registered webhooks are delivered to external HTTP endpoints via httpx by a background worker

## Security

- **Authentication:** Basic auth (bcrypt-hashed passwords), Bearer personal access tokens, and cookie sessions; AUTH_MODE selects permissive, strict, or none
- **Authorization:** Admin-scoped routes under /api/admin and /admin are restricted to admin users; otherwise permissive Jira-like behavior
- **FIPS Compliance:** not applicable; no deterministic crypto or FIPS build signal extracted

**Secrets:**

- JIRA_TOKEN environment variable (MCP server)
- JIRA_API_TOKEN environment variable (scripts/issue-export.py)
- ADMIN credentials (default admin:admin seed)

## Multi-Tenancy

**Model:** Single-tenant emulator; no tenant isolation

**Shared Services:** SQLite database shared across all users and projects within one instance

## Data Flows

- **Issue CRUD**: REST/JQL requests flow through routers to services and SQLAlchemy into SQLite; per-project issue key sequences are maintained
- **JQL search**: Queries are parsed by the Lark grammar and transformed into filtered searches over the issue tables
- **Attachment storage**: Uploaded files are written to ATTACHMENT_DIR on the /data volume with metadata in SQLite
- **Webhook delivery**: A background worker posts registered webhook events to external HTTP endpoints via httpx
- **Snapshot/restore**: Admin snapshots copy the SQLite database; restore swaps it in for test isolation
- **MCP integration**: FastMCP server translates Claude tool calls into REST API calls against the emulator

## Integration Points

- **MCP server**: FastMCP server on port 8081 exposing seven Jira tools for Claude integration, authenticated via JIRA_TOKEN
- **Webhooks**: Outbound HTTP delivery of issue events to registered external endpoints
- **JSON import/export**: Admin import endpoints and CLI import command for seeding/restoring data from JSON files

## Concerns

- Default permissive auth mode and seeded admin:admin credentials are insecure if exposed beyond local development
- SQLite single-file database limits concurrency and provides no high availability
- Webhook worker must be coordinated with database reset (race conditions historically addressed, per commit history)
- FIPS posture and outbound webhook TLS posture not verified by analysis
- Authentication coverage is partial: many of the 113 endpoints rely on shared middleware enforcement rather than per-route policies

