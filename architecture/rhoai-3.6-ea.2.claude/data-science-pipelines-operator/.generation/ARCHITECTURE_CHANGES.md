# Architecture Changes: data-science-pipelines-operator

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | services | controller-manager metrics | * | <empty> | <empty> | Operator controller-manager exposes metrics service on port 8080 with TLS from OpenShift TLS profile | config/manager/manager-service.yaml:1-13 |
| add | services | ds-pipeline-{name} (API Server) | * | <empty> | <empty> | DSPA reconciler creates API server service with HTTP port 8888 per DSPA instance | config/internal/apiserver/default/service.yaml.tmpl:1-30 |
| add | services | ds-pipeline-{name} (gRPC) | * | <empty> | <empty> | DSPA reconciler creates API server gRPC service on port 8887 per DSPA instance | config/internal/apiserver/default/service.yaml.tmpl:25-26 |
| add | services | ds-pipeline-{name} (proxy) | * | <empty> | <empty> | DSPA reconciler creates OAuth proxy service on port 8443 conditional on EnableRoute | config/internal/apiserver/default/service.yaml.tmpl:13-18 |
| add | services | ml-pipeline | * | <empty> | <empty> | Fixed-name ml-pipeline service created for API server with proxy, HTTP, and gRPC ports | config/internal/apiserver/default/service.ml-pipeline.yaml.tmpl:1-26 |
| add | services | ml-pipeline (gRPC) | * | <empty> | <empty> | ml-pipeline gRPC endpoint on port 8887 | config/internal/apiserver/default/service.ml-pipeline.yaml.tmpl:19-22 |
| add | services | ml-pipeline (proxy) | * | <empty> | <empty> | ml-pipeline OAuth proxy endpoint on port 8443 with service-serving cert | config/internal/apiserver/default/service.ml-pipeline.yaml.tmpl:11-14 |
| add | services | mariadb-{name} | * | <empty> | <empty> | DSPA reconciler creates MariaDB service on port 3306 with optional pod-to-pod TLS | config/internal/mariadb/default/service.yaml.tmpl:1-21 |
| add | services | minio-{name} | * | <empty> | <empty> | DSPA reconciler creates MinIO service on port 9000 with kfp-ui compatibility port 80 | config/internal/minio/default/service.yaml.tmpl:1-26 |
| add | services | minio-{name} (kfp-ui) | * | <empty> | <empty> | MinIO kfp-ui-http port 80 maps to 9000 for KFP UI artifact viewer compatibility | config/internal/minio/default/service.yaml.tmpl:18-22 |
| add | services | webhook service | * | <empty> | <empty> | Webhook service on port 8443 with service-serving cert TLS for PipelineVersion validation | config/internal/webhook/service.yaml.tmpl:1-19 |
| add | services | workflow-controller-metrics-{name} | * | <empty> | <empty> | Argo workflow controller metrics service on port 9090 per DSPA instance | config/internal/workflow-controller/service.yaml.tmpl:1-27 |
| add | authentication | :8080/metrics :: GET | * | <empty> | <empty> | Metrics endpoint TLS-secured via OpenShift TLS profile; no application-level auth | main.go:267-269, tls_profile.go:22-64 |
| add | authentication | :9443 webhook :: POST | * | <empty> | <empty> | Webhook server TLS-secured via cluster TLS profile; invoked only by kube-apiserver | main.go:271-274, tls_profile.go:22-64 |
| add | authentication | DSPA API (proxy :8443) :: All | * | <empty> | <empty> | OAuth proxy conditional on EnableRoute; service-serving cert TLS | config/internal/apiserver/default/service.yaml.tmpl:7, config/internal/apiserver/default/service.yaml.tmpl:13-18 |
| add | authentication | DSPA CRD API :: Kubernetes API | * | <empty> | <empty> | RBAC aggregation via aggregate-dspa-admin-edit/view ClusterRoles for DSPA and Pipeline resources | config/rbac/aggregate_dspa_role_edit.yaml:1, config/rbac/aggregate_dspa_role_view.yaml:1 |
