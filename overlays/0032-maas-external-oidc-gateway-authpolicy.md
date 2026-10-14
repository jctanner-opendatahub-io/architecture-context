---
id: "0032"
title: MaaS external OIDC authentication is gateway-enforced
status: active
created: 2026-10-14
affects:
  - models-as-a-service
release:
  - "all"
provenance:
  - https://github.com/opendatahub-io/models-as-a-service
author: Lindani Phiri
superseded_by: null
---

## Fact

MaaS supports external OIDC authentication as a gateway concern, not as local JWT cryptographic validation inside `maas-api`. The controller converts tenant OIDC configuration into a Kuadrant `AuthPolicy`; Authorino validates the JWT at the gateway and injects a trusted identity into `maas-api`.

The generated authentication rules use three methods in priority order:

1. MaaS API keys matching `Bearer sk-oai-*`
2. External OIDC JWT validation for non-API-key, three-segment Bearer JWTs
3. Kubernetes `TokenReview` for OpenShift bearer tokens

The `oidc-identities` rule passes only `issuerUrl` and JWKS cache `ttl` to Authorino's JWT authenticator. Authorino discovers the issuer's OIDC metadata and JWKS, validates the presented JWT, and caches keys according to the TTL. After successful authentication, the `oidc-client-bound` authorization rule compares the token's `azp` claim with the configured `clientId`; the `has(auth.identity.azp)` guard prevents this rule from denying OpenShift TokenReview identities. OIDC group claims are checked against a safe group-name pattern before they are used for subscription or model authorization. For MaaS management routes, the gateway injects `X-MaaS-Username` and `X-MaaS-Group` from the verified Authorino identity and rejects client-supplied identity headers. `maas-api` trusts those headers on strict routes and converts them into its internal `UserContext`; it does not perform local JWT signature, issuer, expiry, or JWKS validation.

## Impact on Strategies

- Treat external OIDC as a MaaS gateway integration through Kuadrant `AuthPolicy` and Authorino, not as a `maas-api` local JWT validation feature.
- Use the controller's `AuthPolicy` generation path when designing tenant-specific or provider-admin OIDC onboarding flows.
- Preserve the three-method priority order so MaaS API keys, external OIDC JWTs, and OpenShift `TokenReview` remain distinguishable.
- Use `issuerUrl`, `clientId`, and JWKS cache TTL as the primary OIDC configuration inputs; do not invent a separate client-secret or audience constraint in `maas-api`.
- Rely on `azp == clientId` for client binding and on Authorino-injected identity headers for downstream authorization.
- Do not treat the unverified claims parser in `maas-api/internal/token/jwt.go` as part of the external OIDC trust path.

## Context

The generated architecture docs describe the MaaS gateway as accepting API keys or OAuth/OIDC tokens but omit the controller-generated `AuthPolicy` mechanics, the three-method priority order, Authorino's JWT validation role, `azp` client binding, and the trusted-header boundary between the gateway and `maas-api`. This overlay makes those mechanics explicit so strategy reviews and downstream design work do not mistakenly assume that MaaS requires new `maas-api` JWT validation code or that the gateway already trusts arbitrary bearer tokens without tenant-specific issuer configuration.
