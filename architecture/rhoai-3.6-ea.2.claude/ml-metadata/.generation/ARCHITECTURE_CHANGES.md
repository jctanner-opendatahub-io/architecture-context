# Architecture Changes: ml-metadata

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | grpc_services | MetadataStoreService | * | <empty> | <empty> | gRPC service defined in proto with ENTRYPOINT exposing port 8080 | ml_metadata/proto/metadata_store_service.proto:1142, ml_metadata/tools/docker_server/Dockerfile.konflux:47 |
| add | authentication | gRPC API :: All | * | <empty> | <empty> | Server supports optional mTLS via SSLConfig.client_verify; no application-level auth | ml_metadata/proto/metadata_store.proto:860-873 |
| add | integration_points | MySQL/MariaDB :: Database client | * | <empty> | <empty> | MySQLDatabaseConfig in ConnectionConfig with bundled mariadb-connector-c | ml_metadata/proto/metadata_store.proto:607-656, ml_metadata/tools/docker_server/Dockerfile.konflux:39 |
| add | integration_points | PostgreSQL :: Database client | * | <empty> | <empty> | PostgreSQLDatabaseConfig in ConnectionConfig for alternative backend | ml_metadata/proto/metadata_store.proto:693-754 |
| add | internal_dependencies | Database (MySQL or PostgreSQL) | * | <empty> | <empty> | Server requires a database backend configured via MetadataStoreServerConfig.connection_config | ml_metadata/proto/metadata_store.proto:852-856 |
