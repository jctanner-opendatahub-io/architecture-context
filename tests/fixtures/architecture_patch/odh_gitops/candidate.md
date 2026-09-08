# Component: odh-gitops

## Purpose

Packages Helm charts and Kustomize overlays for platform dependencies.

## Architecture Components

| Component | Type | Purpose |
|-----------|------|---------|
| rhai-on-openshift-chart | Helm Chart | Installs dependency operators and configurations on OpenShift |
| rhai-on-xks-chart | Helm Chart | Installs dependencies on Kubernetes without OLM |

## Dependencies

### Internal Platform Dependencies

| Component | Interaction Type | Role | Purpose |
|-----------|------------------|------|---------|
| Kueue Operator | OLM Subscription / Helm | Required | Job scheduling and resource quota management |

## Security

### Authentication & Authorization

| Endpoint | Methods | Auth Mechanism | Enforcement Point | Policy |
|----------|---------|----------------|-------------------|--------|
| Platform Services | All | Authorino | Kuadrant gateway | Cluster-wide authorization |

## Data Flows

Kustomize and Helm inputs render operator installation resources.

## Integration Points

| Component | Interaction Type | Port | Protocol | Encryption | Purpose |
|-----------|------------------|------|----------|------------|---------|
| Authorino | CRD Configuration | -- | Kubernetes API | TLS | Deploys a cluster-wide authorization service |

## Architectural Analysis

The repository packages deployment configuration rather than runtime services.
