# Architecture Changes: guardrails-regex-detector

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| delete | authentication | /api/v1/*, /api/v2/* :: POST | * | <empty> | <empty> | Endpoint glob includes non-existent /api/v2/* path and claims Header passthrough / Application-level filtering, but source shows no auth middleware, no header inspection, and no downstream forwarding | src/main.rs:31-38, src/detectors.rs:96-137 |
| delete | authentication | /health, /info :: GET | * | <empty> | <empty> | /info endpoint does not exist in source; only /health is registered as an Axum route | src/main.rs:32 |
| add | authentication | /api/v1/text/contents :: POST | * | <empty> | <empty> | Source-verified single POST endpoint with no application-level auth middleware; handler accepts JSON directly with no header or token checks | src/main.rs:33, src/detectors.rs:96-98 |
| add | authentication | /health :: GET | * | <empty> | <empty> | Health endpoint returns static string with no authentication | src/main.rs:32 |
