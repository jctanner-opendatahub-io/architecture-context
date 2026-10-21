# Component: entra-id-emulator

## Purpose

A Flask-based mock of Microsoft Entra ID that emulates OIDC/OAuth2 flows including authorization code with PKCE, refresh token, resource owner password, and hybrid flows. It exposes tenant-scoped endpoints for discovery, authorization, token issuance, JWKS, userinfo, and logout, backed by SQLite storage. A REST admin API and password-protected web UI allow CRUD management of tenants, users, groups, and clients, with YAML-based seeding on startup.

## Architectural Analysis

entra-id-emulator is a single-process Flask application (run.py -> create_app) that emulates Microsoft Entra ID for testing. The app factory loads YAML configuration, initializes and seeds a SQLite database (tenants, users, groups, clients), generates a 2048-bit RSA signing key persisted in the database, and registers route blueprints. Routes are split into tenant-scoped OIDC endpoints (discovery, authorize, token, JWKS, userinfo, logout), an unauthenticated landing page, and an admin REST API plus web UI guarded by HTTP Basic Auth against a configured admin password. JWTs are signed with PyJWT/jwcrypto using stored RSA keys; pairwise subject identifiers and per-tenant token lifetime overrides are supported. Deployment is a simple container (python:3.11-slim, CMD python run.py, port 8080) with source mounted at runtime; there is no ingress, HA, or orchestration configuration. No CRDs, gRPC services, or external dependencies beyond the Flask ecosystem and SQLite.

## Architecture Components

| Component | Type | Purpose |
|----|----|-------|
| entra_mock app | Flask application | App factory that loads config, initializes database, ensures signing keys, and registers routes |
| OIDC routes | HTTP route blueprints | Tenant-scoped discovery, authorize, token, JWKS, userinfo, and logout endpoints |
| admin_api | HTTP REST API | CRUD management of tenants, users, groups, and clients with HTTP Basic Auth |
| admin web UI | Server-rendered templates | Password-protected admin console at /admin/ |
| db | SQLite storage layer | Schema creation, seeding from YAML, and helper queries |
| keys | Crypto module | RSA key generation, storage, JWKS building, and JWT signing |
| tokens | Token service | Access, ID, and refresh token issuance with lifetime overrides |

## Sub-Component: entra_mock/routes

**API Routes:**

| Path | Methods |
|----|--------|
| /<tenant>/v2.0/.well-known/openid-configuration | GET |
| /<tenant>/discovery/v2.0/keys | GET |
| /<tenant>/oauth2/v2.0/authorize | GET, POST |
| /<tenant>/oauth2/v2.0/token | POST |
| /<tenant>/oauth2/v2.0/logout | GET, POST |
| /oidc/userinfo | GET, POST |
| / | GET |
| /api/tenants | GET, POST |
| /api/tenants/<tenant_id> | PUT, DELETE |
| /api/users | GET, POST |
| /api/users/<user_id> | PUT, DELETE |
| /api/groups | GET, POST |
| /api/groups/<group_id> | PUT, DELETE |
| /api/clients | GET, POST |
| /api/clients/<client_id> | PUT, DELETE |

**Configuration:**

- config.yaml (server settings, seed tenants/users/groups/clients, token lifetimes)
- ENTRA_MOCK_DB environment variable (SQLite path)
- FLASK_SECRET_KEY environment variable (session secret)

## APIs Exposed

### HTTP Endpoints

| Path | Methods | Description |
|----|---------|-------------|
| /<tenant>/v2.0/.well-known/openid-configuration | GET | OIDC discovery document |
| /<tenant>/discovery/v2.0/keys | GET | JWKS public signing keys |
| /<tenant>/oauth2/v2.0/authorize | GET, POST | Authorization endpoint (code, hybrid flows, PKCE) |
| /<tenant>/oauth2/v2.0/token | POST | Token endpoint (code, refresh, password grants) |
| /<tenant>/oauth2/v2.0/logout | GET, POST | Logout endpoint |
| /oidc/userinfo | GET, POST | OIDC userinfo endpoint |
| / | GET | Landing page linking to admin console |
| /api/tenants | GET, POST | List/create tenants |
| /api/tenants/<tenant_id> | PUT, DELETE | Update/delete a tenant |
| /api/users | GET, POST | List/create users |
| /api/users/<user_id> | PUT, DELETE | Update/delete a user |
| /api/groups | GET, POST | List/create groups |
| /api/groups/<group_id> | PUT, DELETE | Update/delete a group |
| /api/clients | GET, POST | List/create OAuth clients |
| /api/clients/<client_id> | PUT, DELETE | Update/delete a client |

## Dependencies

**External:** flask, pyjwt, cryptography, jwcrypto, pyyaml, SQLite (stdlib)

## Deployment

Single-container Python service: python:3.11-slim image running 'python run.py' on port 8080 with source mounted at runtime; SQLite file and config.yaml provided by the environment. Example compose files in examples/.

**Variants:** Local Python (pip install -r requirements.txt; python run.py), Docker/Podman container via compose examples

## Network Architecture

**Services:**

- entra-id-emulator HTTP server on configurable port (default 8080, 0.0.0.0)

## Security

- **Authentication:** OIDC/OAuth2 flows are emulated: user passwords and client secrets are stored as hashes and checked during flows; admin API/UI uses HTTP Basic Auth against a configured admin password (disabled if no password configured).
- **Authorization:** OAuth2 client authorization via client secrets and allowed scopes; admin surface gated by shared admin password.
- **FIPS Compliance:** not applicable — emulator for local testing; no FIPS posture verified

**Secrets:**

- FLASK_SECRET_KEY (session secret, env; random fallback)
- admin_password (config.yaml)
- user password hashes (SQLite)
- client secret hashes (SQLite)
- RSA signing keys (SQLite, unencrypted PEM)

## Multi-Tenancy

**Model:** Multi-tenant emulation: tenants, users, groups, and clients are scoped by tenant_id with tenant-scoped URL paths

**Isolation Mechanisms:**

- Tenant-scoped route paths (/<tenant>/...)
- Per-tenant salts for pairwise subject identifiers
- Per-tenant token lifetime overrides

**Shared Services:** Single shared SQLite database and HTTP server process

## Data Flows

- **OIDC authorization flow**: Client redirects user to /<tenant>/oauth2/v2.0/authorize; user authenticates against seeded credentials; authorization code is issued and exchanged at the token endpoint for JWTs signed with the stored RSA key.
- **Admin management**: Admin UI/API performs CRUD on tenants, users, groups, and clients persisted in SQLite; config.yaml seeds data on startup.
- **Key publication**: RSA public keys are published via the JWKS endpoint for token verification by relying parties.

## Integration Points

- **OAuth2 relying parties**: Any OIDC client (e.g., oauth2-proxy per example config) can use the emulator as its identity provider via discovery and token endpoints.

## Concerns

- No authentication middleware on OIDC endpoints by design (emulator); unsafe if exposed beyond local testing
- Default admin password and seeded credentials (changeme1234) committed in config.yaml
- Signing keys and SQLite database stored locally with unencrypted PEM private keys
- No TLS, ingress, HA, or orchestrated deployment configuration
- Source not baked into container image; mounted at runtime, complicating reproducibility

