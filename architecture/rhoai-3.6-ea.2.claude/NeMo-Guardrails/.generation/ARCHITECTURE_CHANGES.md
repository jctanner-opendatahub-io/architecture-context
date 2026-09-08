# Architecture Changes: NeMo-Guardrails

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| update | authentication | HTTP API :: All | Auth Mechanism | Bearer token or API key | None (platform-delegated) | Server FastAPI app has no authentication middleware, Depends(), or Security() decorators; the analyzer reference (prompt_security/actions.py:47) is an outbound API call, not inbound auth enforcement | nemoguardrails/server/api.py:225-261, nemoguardrails/library/prompt_security/actions.py:67-68 |
| update | authentication | HTTP API :: All | Enforcement Point | Python API dependency or middleware | None | Only ExceptionMiddleware and optional CORSMiddleware are registered; no auth middleware exists in the server | nemoguardrails/server/api.py:237, nemoguardrails/server/api.py:244-260 |
| update | authentication | HTTP API :: All | Policy | Source-defined authentication | Platform-delegated; no in-app authentication middleware | No source-defined authentication policy exists; all endpoints are unauthenticated at the application level | nemoguardrails/server/api.py:225-261 |
