# Architecture Diagrams for Data Science Pipelines

Generated from: `architecture/rhoai-3.6-ea.2/data-science-pipelines.md`
Date: 2026-09-04

**Note**: Diagram filenames use base component name without version (directory is already versioned).

## Available Diagrams

Mermaid diagrams are available as `.mmd` source files. Use GitHub/GitLab's built-in Mermaid rendering, or https://mermaid.live to view and edit.

### For Developers
- [Component Structure](./data-science-pipelines-component.mmd) - Internal components and microservices architecture
- [Data Flows](./data-science-pipelines-dataflow.mmd) - Sequence diagram of pipeline submission, execution, metadata, and caching flows
- [Dependencies](./data-science-pipelines-dependencies.mmd) - Component dependency graph including Argo Workflows, MySQL, S3, and K8s API

### For Architects
- [C4 Context](./data-science-pipelines-c4-context.dsl) - System context in C4 format (Structurizr) showing all containers and external systems
- [Component Overview](./data-science-pipelines-component.mmd) - High-level component view with control plane, execution engine, metadata, and data tiers

### For Security Teams
- [Security Network Diagram (Mermaid)](./data-science-pipelines-security-network.mmd) - Visual network topology with trust zones and auth details (editable)
- [Security Network Diagram (ASCII)](./data-science-pipelines-security-network.txt) - Precise text format for SAR submissions including RBAC, secrets, Istio policies, and FIPS details
- [RBAC Visualization](./data-science-pipelines-rbac.mmd) - Complete RBAC permissions map for all 10 service accounts with risk highlights

## Key Security Highlights

- **Broad RBAC risks**: `pipeline-runner` SA has `kubeflow.org: *: *` and `viewer-controller` has `*` on deployments/services
- **MySQL protected by Istio AuthorizationPolicy**: 7 specific SAs allowed
- **FIPS 140**: GOFIPS140=v1.0.0 with no_openssl build tag (Go native FIPS, not OpenSSL)
- **PQC-ready**: ubi9/ubi-minimal-pqc base images
- **Auth chain**: TokenReview + HTTP header identity → SubjectAccessReview authorization

## How to Use

### Mermaid Source Files (.mmd files)
- **In GitHub/GitLab**: Paste into markdown with ````mermaid` code blocks - renders automatically!
- **Live editor**: https://mermaid.live (paste code, edit, export)
- **Editable**: Modify and regenerate if needed

**Manual PNG generation** (if needed):
```bash
npm install -g @mermaid-js/mermaid-cli
PUPPETEER_EXECUTABLE_PATH=/usr/bin/google-chrome mmdc -i diagram.mmd -o diagram.png -w 3000
```

### C4 Diagrams (.dsl files)
- **Structurizr Lite**: `docker run -p 8080:8080 -v .:/usr/local/structurizr structurizr/lite`
- **CLI export**: `structurizr-cli export -workspace diagram.dsl -format png`

### ASCII Diagrams (.txt files)
- View in any text editor
- Include in documentation as-is
- Perfect for security reviews (precise technical details)

## Updating Diagrams

To regenerate after architecture changes:
```bash
/generate-architecture-diagrams --architecture=../data-science-pipelines.md
```
