# Architecture Changes: llm-d-latency-predictor

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | integration_points | training-service :: HTTP client | * | <empty> | <empty> | Prediction server connects to training-service via HTTP to sync ML models; discovered in ModelSyncer class | prediction/prediction_server.py:68, prediction/prediction_server.py:162, prediction/prediction_server.py:178 |
| add | internal_dependencies | training-service (self) | * | <empty> | <empty> | Prediction server depends on the co-deployed training server for model artifacts via HTTP polling | prediction/prediction_server.py:68, prediction/prediction_server.py:132-179 |
