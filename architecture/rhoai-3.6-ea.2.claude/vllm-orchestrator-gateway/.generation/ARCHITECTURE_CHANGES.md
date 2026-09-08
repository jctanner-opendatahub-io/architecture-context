# Architecture Changes: vllm-orchestrator-gateway

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | http_endpoints | POST :: /{route_name}/v1/chat/completions | * | <empty> | <empty> | Gateway dynamically creates POST endpoints per configured route at /{name}/v1/chat/completions on port 8090 | src/main.rs:84-109, src/main.rs:111-112, config/config.yaml:12-18 |
| add | authentication | /{route_name}/v1/chat/completions :: POST | * | <empty> | <empty> | Gateway forwards Authorization headers to orchestrator backend without gateway-level enforcement | src/main.rs:422-433, src/main.rs:492-502 |
| add | integration_points | TrustyAI Orchestrator :: HTTP Client | * | <empty> | <empty> | Gateway proxies all chat completion requests to orchestrator at /api/v2/chat/completions-detection with optional mTLS | src/main.rs:218-231, src/main.rs:351-406, src/config.rs:15-27 |
| add | internal_dependencies | TrustyAI Orchestrator (vllm-orchestrator) | * | <empty> | <empty> | Backend orchestrator service for content safety detection; configured via orchestrator.host/port in gateway config | src/config.rs:7-27, config/config.yaml:1-3, src/main.rs:218-231 |
