# Architecture Changes: pipelines-components

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | internal_dependencies | CodeFlare SDK | * | <empty> | <empty> | CodeFlare SDK is imported and used for RayJob submission in distributed document processing | components/data_processing/parse_and_chunk/component.py:576 |
| add | internal_dependencies | SDG Hub SDK | * | <empty> | <empty> | SDG Hub SDK is a packages_to_install dependency used for synthetic data generation | components/data_processing/sdg/component.py:12 |
| add | internal_dependencies | ai4rag | * | <empty> | <empty> | ai4rag is used for RAG search space construction and optimization in autorag components | components/training/autorag/rag_templates_optimization/component.py:35-37 |
| add | authentication | S3-compatible storage :: All | * | <empty> | <empty> | S3 authentication via AWS env var credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) is used in pipeline components | components/data_processing/automl/tabular_data_loader/component.py:161-164 |
| add | authentication | Kubernetes API :: All | * | <empty> | <empty> | Kubernetes API authentication via in-cluster service account token (load_incluster_config) is used in pipeline components | components/data_processing/parse_and_chunk/component.py:571-574 |
