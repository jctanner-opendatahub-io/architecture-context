# Architecture Changes: guardrails-detectors

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| update | authentication | HTTP API :: All | Policy | No authentication middleware registered | No authentication middleware registered; TLS configurable via ssl_ca_certs in server config | SSL/TLS support is configurable via server config yaml when ssl_ca_certs is present; enriches the authentication posture description | detectors/common/app.py:181-182 |
| add | integration_points | vLLM inference server :: HTTP client | * | <empty> | <empty> | LLM Judge detector makes outbound HTTP calls to a vLLM predictor endpoint configured via VLLM_BASE_URL environment variable | detectors/llm_judge/detector.py:25-37, detectors/llm_judge/deploy/servingruntime.yaml:34-35 |
| add | integration_points | MinIO (model storage) :: TCP client | * | <empty> | <empty> | HuggingFace detector deployment includes a MinIO service for model artifact storage on port 9000/TCP | detectors/huggingface/deploy/model_container.yaml:1-12 |
| add | integration_points | KServe :: ServingRuntime CRD | * | <empty> | <empty> | Both HuggingFace and LLM Judge detectors are packaged as KServe ServingRuntime definitions | detectors/huggingface/deploy/servingruntime.yaml:1, detectors/llm_judge/deploy/servingruntime.yaml:1 |
| add | internal_dependencies | vllm-judge | * | <empty> | <empty> | Python library dependency providing LLM-as-Judge evaluation metrics and vLLM client integration | detectors/pyproject.toml:36-37 |
| add | internal_dependencies | KServe | * | <empty> | <empty> | Detectors are deployed as KServe ServingRuntime CRDs for model serving integration | detectors/huggingface/deploy/servingruntime.yaml:1, detectors/llm_judge/deploy/servingruntime.yaml:1 |
| add | internal_dependencies | vLLM inference server | * | <empty> | <empty> | LLM Judge detector requires a running vLLM predictor endpoint at runtime | detectors/llm_judge/detector.py:25-27, detectors/llm_judge/deploy/servingruntime.yaml:34-35 |
