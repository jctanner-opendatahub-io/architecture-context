workspace {
    model {
        ciPipeline = person "CI/CD Pipeline" "Automated build system that triggers metadata collection"

        modelMetadataCollection = softwareSystem "model-metadata-collection" "Collects AI model metadata from external sources and packages it as a data-only container image for RHOAI platform consumption" {
            modelExtractor = container "model-extractor" "Fetches model metadata from HuggingFace, GitHub, and OCI registries; generates YAML catalogs" "Go CLI (build-time only)"
            metadataReport = container "metadata-report" "Generates completeness reports from extracted metadata" "Go CLI (build-time only)"
            dataVolume = container "Data Sidecar" "ubi-minimal-pqc container serving static YAML data via volume mount at /app/data" "Container (sleep infinity)"
        }

        huggingFace = softwareSystem "HuggingFace API" "AI model hosting platform providing model collections and metadata" "External"
        gitHub = softwareSystem "GitHub API" "Source code hosting platform providing agent metadata and READMEs" "External"
        ociRegistries = softwareSystem "OCI Container Registries" "Container image registries for architecture inspection" "External"
        rhoaiComponents = softwareSystem "RHOAI Platform Components" "Downstream consumers of model catalog data" "Internal RHOAI"

        ciPipeline -> modelExtractor "Executes during build"
        ciPipeline -> metadataReport "Executes during build"
        modelExtractor -> huggingFace "Fetches model collections and model cards" "HTTPS/443, Bearer Token (optional)"
        modelExtractor -> gitHub "Fetches agent metadata and README files" "HTTPS/443, Bearer Token (optional)"
        modelExtractor -> ociRegistries "Inspects image manifests for architectures" "HTTPS/443, Registry Credentials"
        modelExtractor -> dataVolume "Generated YAML packaged into container image"
        metadataReport -> dataVolume "Reads generated data for reporting"
        rhoaiComponents -> dataVolume "Mounts /app/data volume to read catalog data" "Filesystem (volume mount)"
    }

    views {
        systemContext modelMetadataCollection "SystemContext" {
            include *
            autoLayout
        }

        container modelMetadataCollection "Containers" {
            include *
            autoLayout
        }

        styles {
            element "External" {
                background #999999
                color #ffffff
            }
            element "Internal RHOAI" {
                background #7ed321
                color #ffffff
            }
            element "Person" {
                shape person
                background #4a90e2
                color #ffffff
            }
            element "Software System" {
                background #4a90e2
                color #ffffff
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
        }
    }
}
