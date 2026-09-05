# Fixture Provenance

The `rhods_operator` snippets are minimal, sanitized source shapes from
`red-hat-data-services/rhods-operator` commit
`4ada791819c522a4cda54f9029ab3e4056ed31ed`:

- `metrics_authentication.go` preserves `cmd/main.go:480-500`.
- `named_namespace_watches.go` preserves
  `internal/controller/services/auth/auth_controller.go:56-87`; the expected
  event target also uses `api/services/v1alpha1/auth_types.go:24-27` and
  `api/services/v1alpha1/groupversion_info.go:18-29`.
- `gateway_auth_modes.go` preserves
  `internal/controller/services/gateway/gateway_controller_actions.go:100-188`.
- `fips_signal.yaml` preserves
  `config/rhoai/manifests/bases/rhods-operator.clusterserviceversion.yaml:1-18`.
- `analyzer_metrics_characteristics.json` preserves the source-linked manager
  metrics Service and Deployment characteristics while including the separate
  gateway proxy metrics records needed to test target isolation.

The service and manifest analyzer inputs are synthetic representative corpus
members. Historical pipeline logs and generated architecture documents are not
fixtures and are not required by these tests.
