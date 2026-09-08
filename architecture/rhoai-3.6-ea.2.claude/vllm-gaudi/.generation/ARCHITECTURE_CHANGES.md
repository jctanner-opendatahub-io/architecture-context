# Architecture Changes: vllm-gaudi

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | authentication | OpenAI-compatible API :: All | * | <empty> | <empty> | API server has no built-in authentication; platform-delegated to KServe/Istio | Dockerfile.konflux.gaudi:244 |
| add | integration_points | vllm (upstream) :: Build-time dependency | * | <empty> | <empty> | Core LLM framework cloned and installed during image build | Dockerfile.konflux.gaudi:206-213 |
| add | integration_points | Habana SynapseAI :: Runtime library | * | <empty> | <empty> | Intel Gaudi HPU driver stack required for hardware acceleration | Dockerfile.konflux.gaudi:94-109 |
| add | integration_points | KServe ServingRuntime :: Container image | * | <empty> | <empty> | Container image consumed by KServe serving runtime definitions | Dockerfile.konflux.gaudi:244-249 |
| add | internal_dependencies | vllm | * | <empty> | <empty> | Core LLM inference engine extended by vllm-gaudi HPU plugin | Dockerfile.konflux.gaudi:206-213 |
| add | internal_dependencies | KServe | * | <empty> | <empty> | Platform component that deploys the vllm-gaudi container as a serving runtime | Dockerfile.konflux.gaudi:244 |
