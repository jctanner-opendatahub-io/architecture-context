# Architecture Changes

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | integration_points | OpenAI-compatible generation service :: REST API client | * | <empty> | <empty> | Optional OpenAI-compatible generation backend conditionally enables chat/completions-detection endpoints when openai config is present | config/config.yaml:15-18, src/server/routes.rs:97-108 |
