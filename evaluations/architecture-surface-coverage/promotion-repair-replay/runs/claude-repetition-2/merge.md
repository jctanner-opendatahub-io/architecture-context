# Architecture Merge Report: rhods-operator

## Summary

| Status | Count |
|--------|------:|
| Unchanged | 276 |
| Applied | 1 |
| Rejected | 0 |
| Restored | 0 |

## Unchanged Analyzer Rows

| Category | Rows |
|----------|-----:|
| architecture_components | 12 |
| authentication | 7 |
| crds | 14 |
| egress | 1 |
| external_dependencies | 47 |
| http_endpoints | 12 |
| ingress | 3 |
| integration_points | 86 |
| internal_dependencies | 11 |
| rbac_cluster_roles | 67 |
| rbac_role_bindings | 3 |
| recent_changes | 7 |
| secrets | 3 |
| services | 3 |

## Assembly Diagnostics

- candidate synthesis subsection "FIPS Compliance" is under "Admission Webhooks" at line 355; expected parent "Security"

## Analyzer Row Preservation

- **adjudicated_expected**: 277
- **adjudicated_missing**: 0
- **adjudicated_preserved**: 277
- **all_adjudicated_expected**: 311
- **all_adjudicated_missing**: 0
- **all_adjudicated_preserved**: 311
- **all_expected**: 310
- **all_missing**: 0
- **all_preserved**: 310
- **authorized_deletes**: 0
- **expected**: 276
- **mapped_missing**: 0
- **missing**: 0
- **opaque**: 0
- **preserved**: 276
- **restored**: 0
- **stage**: assembly-rejected
- **unchanged**: 276

## Applied Changes

| Action | Category | Row Key | Column | Analyzer | Candidate | Evidence | Detail |
|--------|----------|---------|--------|----------|-----------|----------|--------|
| add | authentication | operator metrics (port 8443) :: https | * | <empty> | <empty> | cmd/main.go:485-499 | Operator metrics endpoint uses conditional controller-runtime authentication and authorization filters when MetricsSecure is enabled, applied with the OpenShift TLS profile |

## Rejected Changes

| Action | Category | Row Key | Column | Analyzer | Candidate | Evidence | Detail |
|--------|----------|---------|--------|----------|-----------|----------|--------|
| - | - | - | - | - | - | - | None |

## Restored Changes

| Action | Category | Row Key | Column | Analyzer | Candidate | Evidence | Detail |
|--------|----------|---------|--------|----------|-----------|----------|--------|
| - | - | - | - | - | - | - | None |
