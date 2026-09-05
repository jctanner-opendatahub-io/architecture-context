# On-Disk Output Source Review

The current canary uses only the two `rhods-operator.md` outputs under
`architecture/`. They are comparison inputs and must never be supplied to an
architecture synthesis run. Review each file against the pinned source checkout;
do not give credit for a keyword or an unsupported generator assertion alone.

For each surface, `supported` means the promoted document expresses every
listed claim and the cited evidence is one of the exact references in
`experiment.json`:

- `authentication.metrics-enforcement`: the controller-runtime metrics serving
  surface installs `filters.WithAuthenticationAndAuthorization` only when
  `oconfig.MetricsSecure` is true (`cmd/main.go:485-500`).
- `controller.named-resource-watches`: the package-qualified auth service
  controller watches Namespace events for both `models-as-a-service` and
  `kuadrant-system`, routing them to the Auth instance. The two source ranges
  are `auth_controller.go:63-69` and `auth_controller.go:70-76`.
- `authentication.gateway-modes`: integrated OpenShift OAuth, configured
  external OIDC, and externally managed authentication have distinct lifecycle
  behavior in `gateway_controller_actions.go:100-188`.
- `compliance.runtime-fips`: the selected CSV marks FIPS compliance false, so
  runtime FIPS compliance is not established. Strict-FIPS build flags, a UBI
  base, TLS profiles, or dependencies do not override that limitation.

Record `partial` when only part of a multi-claim surface is present, `omitted`
when the output does not account for it, and `unsupported` when the treatment
conflicts with source. List every source-refuted statement under
`unsupported_claims`; in particular reject
claims that all Namespace events trigger Auth, OAuth and OIDC share one client
lifecycle, or strict-FIPS/TLS signals establish runtime compliance.

Keep one result for every surface and pin each architecture file's SHA-256.
Source review bases must be numeric repository-relative references from the
manifest. A single Markdown output cannot establish agent latency, cost,
token/cache usage, source reads, discovery calls, analyzer preservation, merge
rejection/loss, or run-to-run variability; leave those measurements `null`.
