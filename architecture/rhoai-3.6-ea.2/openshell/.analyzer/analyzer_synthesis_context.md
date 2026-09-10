# Analyzer Synthesis Context: openshell

This file is a bounded, source-linked projection. Read it before the full analyzer JSON. It does not replace the authoritative JSON.

## Coverage Findings

- **crds (not-verified)**: 0 crds facts extracted; absence is not proven by the available coverage
- **grpc_services (observed)**: 102 grpc_services facts extracted [source: proto/compute_driver.proto:25, proto/compute_driver.proto:30, proto/compute_driver.proto:37, proto/compute_driver.proto:41, proto/compute_driver.proto:45, proto/compute_driver.proto:48, proto/compute_driver.proto:51, proto/compute_driver.proto:54, proto/compute_driver.proto:57, proto/compute_driver.proto:60, proto/compute_driver.proto:63, proto/compute_driver.proto:67, proto/compute_driver.proto:70, proto/credential_driver.proto:18, proto/credential_driver.proto:22, proto/credential_driver.proto:25, proto/credential_driver.proto:28, proto/credential_driver.proto:32, proto/gateway_interceptor.proto:16, proto/gateway_interceptor.proto:20, proto/gateway_interceptor.proto:25, proto/inference.proto:14, proto/inference.proto:25, proto/inference.proto:35, proto/inference.proto:45, proto/openshell.proto:104, proto/openshell.proto:114, proto/openshell.proto:124, proto/openshell.proto:134, proto/openshell.proto:144, proto/openshell.proto:153, proto/openshell.proto:162, proto/openshell.proto:171, proto/openshell.proto:180, proto/openshell.proto:189, proto/openshell.proto:198, proto/openshell.proto:207, proto/openshell.proto:216, proto/openshell.proto:225, proto/openshell.proto:234, proto/openshell.proto:24, proto/openshell.proto:245, proto/openshell.proto:254, proto/openshell.proto:263, proto/openshell.proto:272, proto/openshell.proto:281, proto/openshell.proto:291, proto/openshell.proto:301, proto/openshell.proto:31, proto/openshell.proto:311, proto/openshell.proto:321, proto/openshell.proto:331, proto/openshell.proto:340, proto/openshell.proto:350, proto/openshell.proto:360, proto/openshell.proto:370, proto/openshell.proto:38, proto/openshell.proto:380, proto/openshell.proto:389, proto/openshell.proto:399, proto/openshell.proto:415, proto/openshell.proto:424, proto/openshell.proto:434, proto/openshell.proto:444, proto/openshell.proto:454, proto/openshell.proto:462, proto/openshell.proto:47, proto/openshell.proto:471, proto/openshell.proto:479, proto/openshell.proto:488, proto/openshell.proto:501, proto/openshell.proto:508, proto/openshell.proto:515, proto/openshell.proto:533, proto/openshell.proto:545, proto/openshell.proto:558, proto/openshell.proto:56, proto/openshell.proto:566, proto/openshell.proto:575, proto/openshell.proto:585, proto/openshell.proto:595, proto/openshell.proto:605, proto/openshell.proto:614, proto/openshell.proto:623, proto/openshell.proto:633, proto/openshell.proto:646, proto/openshell.proto:65, proto/openshell.proto:658, proto/openshell.proto:670, proto/openshell.proto:679, proto/openshell.proto:688, proto/openshell.proto:697, proto/openshell.proto:706, proto/openshell.proto:715, proto/openshell.proto:724, proto/openshell.proto:74, proto/openshell.proto:84, proto/openshell.proto:94, proto/supervisor_middleware.proto:16, proto/supervisor_middleware.proto:19, proto/supervisor_middleware.proto:23, proto/supervisor_middleware.proto:32]
- **http_endpoints (observed)**: 10 http_endpoints facts extracted [source: crates/openshell-server/src/auth/http.rs:60, crates/openshell-server/src/auth/http.rs:61, crates/openshell-server/src/auth/http.rs:62, crates/openshell-server/src/auth/http.rs:63, crates/openshell-server/src/http.rs:163, crates/openshell-server/src/http.rs:164, crates/openshell-server/src/http.rs:165, crates/openshell-server/src/http.rs:172, crates/openshell-server/src/ws_tunnel.rs:37, sdk/go/openshell/v1/oidc/authcode.go:99]
- **services (observed)**: 2 services facts extracted
- **ingress (confirmed-empty)**: 0 ingress facts extracted
- **webhooks (not-verified)**: 0 webhooks facts extracted; absence is not proven by the available coverage

## Deterministic Cross-References


## Behavioral Evidence

No bounded behavioral evidence was extracted.

## Gap Evidence Index

### authentication

- **Question:** Where is authentication enforced for this surface, and is it conditional?
  **Expected signal:** middleware, filter, policy, or enforcement branch
  **Candidate:** `crates/openshell-server/src/auth/http.rs`:62 (/api/v1/*, /api/v2/*, Header passthrough)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** Where is authentication enforced for this surface, and is it conditional?
  **Expected signal:** middleware, filter, policy, or enforcement branch
  **Candidate:** `crates/openshell-server/src/auth/http.rs`:62 (/health, /info, None)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
### configuration_lifecycle

- **Question:** What lifecycle, command, probes, and deployment configuration surround this entrypoint?
  **Expected signal:** main command, startup path, probe, signal handling, or workload mapping
  **Candidate:** `deploy/docker/Dockerfile.cli`:27 (deploy/docker/Dockerfile.cli:ENTRYPOINT)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** What lifecycle, command, probes, and deployment configuration surround this entrypoint?
  **Expected signal:** main command, startup path, probe, signal handling, or workload mapping
  **Candidate:** `deploy/docker/Dockerfile.gateway`:23 (deploy/docker/Dockerfile.gateway:ENTRYPOINT)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** What lifecycle, command, probes, and deployment configuration surround this entrypoint?
  **Expected signal:** main command, startup path, probe, signal handling, or workload mapping
  **Candidate:** `deploy/docker/Dockerfile.gateway`:24 (deploy/docker/Dockerfile.gateway:CMD)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** What lifecycle, command, probes, and deployment configuration surround this entrypoint?
  **Expected signal:** main command, startup path, probe, signal handling, or workload mapping
  **Candidate:** `deploy/docker/Dockerfile.konflux.cli`:95 (deploy/docker/Dockerfile.konflux.cli:ENTRYPOINT)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** What lifecycle, command, probes, and deployment configuration surround this entrypoint?
  **Expected signal:** main command, startup path, probe, signal handling, or workload mapping
  **Candidate:** `deploy/docker/Dockerfile.konflux.gateway`:83 (deploy/docker/Dockerfile.konflux.gateway:ENTRYPOINT)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** What lifecycle, command, probes, and deployment configuration surround this entrypoint?
  **Expected signal:** main command, startup path, probe, signal handling, or workload mapping
  **Candidate:** `deploy/docker/Dockerfile.konflux.gateway`:84 (deploy/docker/Dockerfile.konflux.gateway:CMD)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** What lifecycle, command, probes, and deployment configuration surround this entrypoint?
  **Expected signal:** main command, startup path, probe, signal handling, or workload mapping
  **Candidate:** `deploy/docker/Dockerfile.konflux.supervisor`:107 (deploy/docker/Dockerfile.konflux.supervisor:ENTRYPOINT)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** What lifecycle, command, probes, and deployment configuration surround this entrypoint?
  **Expected signal:** main command, startup path, probe, signal handling, or workload mapping
  **Candidate:** `deploy/docker/Dockerfile.supervisor`:21 (deploy/docker/Dockerfile.supervisor:ENTRYPOINT)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** What lifecycle, command, probes, and deployment configuration surround this entrypoint?
  **Expected signal:** main command, startup path, probe, signal handling, or workload mapping
  **Candidate:** `e2e/docker/Dockerfile.external-kubernetes-gateway`:29 (e2e/docker/Dockerfile.external-kubernetes-gateway:ENTRYPOINT)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** What lifecycle, command, probes, and deployment configuration surround this entrypoint?
  **Expected signal:** main command, startup path, probe, signal handling, or workload mapping
  **Candidate:** `e2e/docker/Dockerfile.external-kubernetes-gateway`:30 (e2e/docker/Dockerfile.external-kubernetes-gateway:CMD)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** What lifecycle, command, probes, and deployment configuration surround this entrypoint?
  **Expected signal:** main command, startup path, probe, signal handling, or workload mapping
  **Candidate:** `e2e/gpu/images/cuda-basic/Dockerfile`:72 (e2e/gpu/images/cuda-basic/Dockerfile:ENTRYPOINT)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** What lifecycle, command, probes, and deployment configuration surround this entrypoint?
  **Expected signal:** main command, startup path, probe, signal handling, or workload mapping
  **Candidate:** `e2e/gpu/images/smoke-fail/Dockerfile`:15 (e2e/gpu/images/smoke-fail/Dockerfile:ENTRYPOINT)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
### grpc_services

- **Question:** Where is this gRPC service registered and which interceptors or credentials apply?
  **Expected signal:** service registration, interceptor, TLS, or credential configuration
  **Candidate:** `proto/compute_driver.proto`:25 (openshell.compute.v1.ComputeDriver/GetCapabilities)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** Where is this gRPC service registered and which interceptors or credentials apply?
  **Expected signal:** service registration, interceptor, TLS, or credential configuration
  **Candidate:** `proto/compute_driver.proto`:30 (openshell.compute.v1.ComputeDriver/AuthenticateSandbox)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** Where is this gRPC service registered and which interceptors or credentials apply?
  **Expected signal:** service registration, interceptor, TLS, or credential configuration
  **Candidate:** `proto/compute_driver.proto`:37 (openshell.compute.v1.ComputeDriver/GetGatewayListenerRequirements)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** Where is this gRPC service registered and which interceptors or credentials apply?
  **Expected signal:** service registration, interceptor, TLS, or credential configuration
  **Candidate:** `proto/compute_driver.proto`:41 (openshell.compute.v1.ComputeDriver/ValidateSandboxCreate)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** Where is this gRPC service registered and which interceptors or credentials apply?
  **Expected signal:** service registration, interceptor, TLS, or credential configuration
  **Candidate:** `proto/compute_driver.proto`:45 (openshell.compute.v1.ComputeDriver/GetSandbox)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** Where is this gRPC service registered and which interceptors or credentials apply?
  **Expected signal:** service registration, interceptor, TLS, or credential configuration
  **Candidate:** `proto/compute_driver.proto`:48 (openshell.compute.v1.ComputeDriver/ListSandboxes)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** Where is this gRPC service registered and which interceptors or credentials apply?
  **Expected signal:** service registration, interceptor, TLS, or credential configuration
  **Candidate:** `proto/compute_driver.proto`:51 (openshell.compute.v1.ComputeDriver/CreateSandbox)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** Where is this gRPC service registered and which interceptors or credentials apply?
  **Expected signal:** service registration, interceptor, TLS, or credential configuration
  **Candidate:** `proto/compute_driver.proto`:54 (openshell.compute.v1.ComputeDriver/StopSandbox)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** Where is this gRPC service registered and which interceptors or credentials apply?
  **Expected signal:** service registration, interceptor, TLS, or credential configuration
  **Candidate:** `proto/compute_driver.proto`:57 (openshell.compute.v1.ComputeDriver/StartSandbox)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** Where is this gRPC service registered and which interceptors or credentials apply?
  **Expected signal:** service registration, interceptor, TLS, or credential configuration
  **Candidate:** `proto/compute_driver.proto`:60 (openshell.compute.v1.ComputeDriver/DeleteSandbox)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** Where is this gRPC service registered and which interceptors or credentials apply?
  **Expected signal:** service registration, interceptor, TLS, or credential configuration
  **Candidate:** `proto/compute_driver.proto`:67 (openshell.compute.v1.ComputeDriver/EnsureWorkspace)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** Where is this gRPC service registered and which interceptors or credentials apply?
  **Expected signal:** service registration, interceptor, TLS, or credential configuration
  **Candidate:** `proto/compute_driver.proto`:70 (openshell.compute.v1.ComputeDriver/DeleteWorkspace)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
### http_endpoints

- **Question:** Does this endpoint have additional dynamic routes or a concrete handler/owner?
  **Expected signal:** route registration, handler binding, middleware, or owner symbol
  **Candidate:** `crates/openshell-server/src/auth/http.rs`:60 (/auth/connect, GET)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** Does this endpoint have additional dynamic routes or a concrete handler/owner?
  **Expected signal:** route registration, handler binding, middleware, or owner symbol
  **Candidate:** `crates/openshell-server/src/auth/http.rs`:61 (/auth/oidc-config, GET)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** Does this endpoint have additional dynamic routes or a concrete handler/owner?
  **Expected signal:** route registration, handler binding, middleware, or owner symbol
  **Candidate:** `crates/openshell-server/src/auth/http.rs`:62 (/.well-known/jwks.json, GET)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** Does this endpoint have additional dynamic routes or a concrete handler/owner?
  **Expected signal:** route registration, handler binding, middleware, or owner symbol
  **Candidate:** `crates/openshell-server/src/auth/http.rs`:63 (/.well-known/openid-configuration, GET)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** Does this endpoint have additional dynamic routes or a concrete handler/owner?
  **Expected signal:** route registration, handler binding, middleware, or owner symbol
  **Candidate:** `crates/openshell-server/src/http.rs`:163 (/health, GET)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** Does this endpoint have additional dynamic routes or a concrete handler/owner?
  **Expected signal:** route registration, handler binding, middleware, or owner symbol
  **Candidate:** `crates/openshell-server/src/http.rs`:164 (/healthz, GET)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** Does this endpoint have additional dynamic routes or a concrete handler/owner?
  **Expected signal:** route registration, handler binding, middleware, or owner symbol
  **Candidate:** `crates/openshell-server/src/http.rs`:165 (/readyz, GET)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** Does this endpoint have additional dynamic routes or a concrete handler/owner?
  **Expected signal:** route registration, handler binding, middleware, or owner symbol
  **Candidate:** `crates/openshell-server/src/http.rs`:172 (/metrics, GET)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** Does this endpoint have additional dynamic routes or a concrete handler/owner?
  **Expected signal:** route registration, handler binding, middleware, or owner symbol
  **Candidate:** `crates/openshell-server/src/ws_tunnel.rs`:37 (/_ws_tunnel, GET)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
- **Question:** Does this endpoint have additional dynamic routes or a concrete handler/owner?
  **Expected signal:** route registration, handler binding, middleware, or owner symbol
  **Candidate:** `sdk/go/openshell/v1/oidc/authcode.go`:99 (/callback, Unknown, openshell/v1/oidc)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship
### services

- **Question:** Which container listener, probe, and service mapping expose this workload?
  **Expected signal:** container port, probe, service account, or lifecycle configuration
  **Candidate:** `e2e/helm-plugins/openshell-external-compute-driver/workload-patch.yaml`:4 (openshell)
  **Status:** candidate; **Limitations:** candidate location only; source inspection is required to establish the relationship

## Section Evidence

### authentication

- /api/v1/*, /api/v2/* methods=POST mechanism=Header passthrough enforcement=Application-level filtering policy=Configured headers are forwarded to downstream services [source: crates/openshell-server/src/auth/http.rs:62]
- /health, /info methods=GET mechanism=None enforcement=None policy=Unauthenticated health server [source: crates/openshell-server/src/auth/http.rs:62]
### http_endpoints

- GET /.well-known/jwks.json on port ; transport= encryption=TLS 1.2+ (optional) auth=Passthrough headers owner= [source: crates/openshell-server/src/auth/http.rs:62]
- GET /.well-known/openid-configuration on port ; transport= encryption=TLS 1.2+ (optional) auth=Passthrough headers owner= [source: crates/openshell-server/src/auth/http.rs:63]
- GET /_ws_tunnel on port ; transport= encryption=TLS 1.2+ (optional) auth=Passthrough headers owner= [source: crates/openshell-server/src/ws_tunnel.rs:37]
- GET /auth/connect on port ; transport= encryption=TLS 1.2+ (optional) auth=Passthrough headers owner= [source: crates/openshell-server/src/auth/http.rs:60]
- GET /auth/oidc-config on port ; transport= encryption=TLS 1.2+ (optional) auth=Passthrough headers owner= [source: crates/openshell-server/src/auth/http.rs:61]
- GET /health on port ; transport= encryption=None auth=None owner= [source: crates/openshell-server/src/http.rs:163]
- GET /healthz on port ; transport= encryption=None auth=None owner= [source: crates/openshell-server/src/http.rs:164]
- GET /metrics on port ; transport= encryption=TLS 1.2+ (optional) auth=Passthrough headers owner= [source: crates/openshell-server/src/http.rs:172]
- GET /readyz on port ; transport= encryption=None auth=None owner= [source: crates/openshell-server/src/http.rs:165]
- Unknown /callback on port ; transport=HTTP/1.1 encryption= auth= owner=openshell/v1/oidc [source: sdk/go/openshell/v1/oidc/authcode.go:99]

## Cross-Cutting Evidence

### deployment_topology

- **observed**: StatefulSet workload openshell uses service account  and 2 container(s) [source: e2e/helm-plugins/openshell-external-compute-driver/workload-patch.yaml:4]
### disconnected_deployment

- **unresolved**: No complete deterministic evidence family was extracted; targeted source/configuration review may be required [source: coverage:disconnected_deployment]
### high_availability

- **unresolved**: No complete deterministic evidence family was extracted; targeted source/configuration review may be required [source: coverage:high_availability]
### ingress

- **observed**: HTTP Unknown /callback is owned by openshell/v1/oidc [source: sdk/go/openshell/v1/oidc/authcode.go:99]
### security

- **observed**: GET /health, /info uses None at None; policy=Unauthenticated health server [source: crates/openshell-server/src/auth/http.rs:62]
- **observed**: POST /api/v1/*, /api/v2/* uses Header passthrough at Application-level filtering; policy=Configured headers are forwarded to downstream services [source: crates/openshell-server/src/auth/http.rs:62]
- **dependency-signal**: crypto-library targets rustls: Rust TLS dependency is present; the cryptographic provider and FIPS mode require configuration or lockfile verification [source: Cargo.toml:38]
- **dependency-signal**: crypto-library targets tokio-rustls: Rust TLS dependency is present; the cryptographic provider and FIPS mode require configuration or lockfile verification [source: Cargo.toml:38]
- **dependency-signal**: crypto-provider targets aws-lc-rs: Cargo.lock selects this cryptographic provider; FIPS validation depends on build and runtime configuration [source: Cargo.lock:301]
- **dependency-signal**: crypto-provider targets ring: Cargo.lock selects ring as a cryptographic provider; ring is not a FIPS-validated provider [source: Cargo.lock:5726]
- **not-extracted**: fips-posture targets FIPS validation: FIPS validation and runtime provider selection are not fully determined by static dependency/build signals [source: Cargo.toml:38]
- **dependency-signal**: tls-config targets crypto/tls: TLS configuration import [source: sdk/go/openshell/v1/edge/tunnel.go, sdk/go/openshell/v1/internal/grpc/conn.go]
- **dependency-signal**: tls-config targets google.golang.org/grpc/credentials: TLS configuration import [source: sdk/go/openshell/v1/internal/grpc/conn.go]
### supply_chain

- **unresolved**: No complete deterministic evidence family was extracted; targeted source/configuration review may be required [source: coverage:supply_chain]
