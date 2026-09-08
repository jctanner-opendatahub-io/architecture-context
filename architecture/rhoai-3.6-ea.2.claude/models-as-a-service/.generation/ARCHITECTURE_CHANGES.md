# Architecture Changes: models-as-a-service

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| delete | internal_dependencies | Gateway API (data-science-gateway) | * | <empty> | <empty> | Source shows the HTTPRoute parentRef targets maas-default-gateway, not data-science-gateway | deployment/base/maas-api/networking/httproute.yaml:6-8 |
| add | internal_dependencies | Gateway API (maas-default-gateway) | * | <empty> | <empty> | HTTPRoute parentRef names the gateway as maas-default-gateway in openshift-ingress namespace | deployment/base/maas-api/networking/httproute.yaml:6-8 |
| add | internal_dependencies | PostgreSQL | * | <empty> | <empty> | maas-api depends on PostgreSQL for persistent storage; pgx/v5 client library and golang-migrate for schema management; connection via maas-db-config Secret | deployment/base/maas-api/rbac/clusterrole.yaml:1, deployment/base/maas-api/rbac/supplemental-clusterrole.yaml:10 |
| add | internal_dependencies | Kuadrant/Authorino | * | <empty> | <empty> | MaaSAuthPolicy controller creates kuadrant.io/v1/AuthPolicy resources for per-tenant gateway authentication | maas-controller/pkg/controller/maas/maasauthpolicy_controller.go:989 |
