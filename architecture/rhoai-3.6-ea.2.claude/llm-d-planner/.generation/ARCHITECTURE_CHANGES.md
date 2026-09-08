# Architecture Changes: llm-d-planner

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | authentication | Database Admin API :: POST | * | <empty> | <empty> | Database admin endpoints implement optional HMAC password check via X-Admin-Password header when DB_ADMIN_PASSWORD is set | src/planner/api/routes/database.py:23-34 |
| add | integration_points | Ollama API :: Python SDK client | * | <empty> | <empty> | Ollama is the default LLM provider, accessed via Python SDK on port 11434 | src/planner/llm/factory.py:34-42 |
| add | integration_points | Vertex AI (Claude) :: AnthropicVertex SDK | * | <empty> | <empty> | Vertex AI provider uses AnthropicVertex SDK for Claude inference via GCP credentials | src/planner/llm/vertex_client.py:38-43 |
| add | internal_dependencies | Ollama (local deployment) | * | <empty> | <empty> | Ollama is deployed as a co-located Kubernetes Deployment and serves as the default local LLM inference backend | deploy/kubernetes/ollama.yaml:1, src/planner/llm/factory.py:34-42 |
