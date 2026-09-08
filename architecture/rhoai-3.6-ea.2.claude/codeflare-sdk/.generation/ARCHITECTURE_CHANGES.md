# Architecture Changes: codeflare-sdk

## Change Records

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| delete | authentication | HTTP API :: All | * | <empty> | <empty> | Analyzer finding is from test file mock (test_kube_api_helpers.py), not the actual SDK authentication model; the SDK is a client library that authenticates outward, not a server | src/codeflare_sdk/common/kubernetes_cluster/auth.py:30-31 |
| add | authentication | Kubernetes API :: All | * | <empty> | <empty> | SDK authenticates to Kubernetes API via kube-authkit with auto-detection of Bearer token, kubeconfig, and in-cluster service account credentials | src/codeflare_sdk/common/kubernetes_cluster/auth.py:30-31, src/codeflare_sdk/common/kubernetes_cluster/auth.py:257-268 |
| add | authentication | Ray Dashboard API :: All | * | <empty> | <empty> | RayJobClient connects to Ray Dashboard HTTP endpoint with caller-configured headers and cookies for authentication, TLS verification enabled by default | src/codeflare_sdk/ray/client/ray_jobs.py:44-48, src/codeflare_sdk/ray/client/ray_jobs.py:58-67 |
| add | internal_dependencies | KubeRay Operator | * | <empty> | <empty> | SDK creates and manages RayJob and RayCluster CRs through vendored KubeRay Python client (RayjobApi, RayClusterApi) | src/codeflare_sdk/ray/rayjobs/rayjob.py:34-35 |
| add | internal_dependencies | Kueue | * | <empty> | <empty> | SDK integrates with Kueue for local queue default name resolution and priority class validation for batch workloads | src/codeflare_sdk/ray/rayjobs/rayjob.py:27-30 |
| add | integration_points | KubeRay Operator :: CRD watch | * | <empty> | <empty> | SDK creates and manages RayJob and RayCluster CRs through vendored KubeRay Python client | src/codeflare_sdk/ray/rayjobs/rayjob.py:34-35 |
| add | integration_points | Kueue :: API | * | <empty> | <empty> | SDK queries Kueue for default local queue names and validates priority class existence before submitting RayJob CRs | src/codeflare_sdk/ray/rayjobs/rayjob.py:27-30 |
