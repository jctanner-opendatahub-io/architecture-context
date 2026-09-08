workspace {
    model {
        inferenceProxy = person "llm-d Inference Proxy" "Sends inference telemetry data and consumes latency predictions"

        latencyPredictor = softwareSystem "llm-d-latency-predictor" "Online ML-based latency prediction for llm-d inference workloads using XGBoost/LightGBM models" {
            trainingServer = container "Training Server" "Collects telemetry data, trains XGBoost and LightGBM regression models for TTFT and TPOT prediction, serves trained model artifacts" "Python FastAPI + uvicorn, Port 8000"
            predictionServer = container "Prediction Server" "Serves low-latency TTFT/TPOT prediction requests using synced ML models" "Python FastAPI + uvicorn, Port 8001"
            modelSyncer = container "ModelSyncer" "Background thread that periodically polls training server for updated model artifacts" "Python Thread"
        }

        prometheus = softwareSystem "Prometheus" "Metrics collection and monitoring" "External"
        kubernetes = softwareSystem "Kubernetes" "Container orchestration and health checking" "External"
        aipccBase = softwareSystem "AIPCC CPU Base Image" "quay.io/aipcc/base-images/cpu:3.5.0 - RHEL AI Python environment" "External"

        # Relationships
        inferenceProxy -> trainingServer "POST /add_training_data_bulk" "HTTP/8000, No Auth"
        inferenceProxy -> predictionServer "POST /predict, /predict/bulk, /predict/bulk/strict" "HTTP/80 (via ClusterIP), No Auth"

        modelSyncer -> trainingServer "GET /model/{name}/info, /model/{name}/download" "HTTP/8000, Polling every 10s"
        predictionServer -> modelSyncer "Loads synced models from local disk"

        prometheus -> trainingServer "GET /metrics" "HTTP/8000"
        kubernetes -> trainingServer "GET /healthz, /readyz" "HTTP/8000"
        kubernetes -> predictionServer "GET /healthz, /readyz" "HTTP/8001"

        trainingServer -> aipccBase "Built on" "Container base image"
        predictionServer -> aipccBase "Built on" "Container base image"
    }

    views {
        systemContext latencyPredictor "SystemContext" {
            include *
            autoLayout
        }

        container latencyPredictor "Containers" {
            include *
            autoLayout
        }

        styles {
            element "Software System" {
                background #438dd5
                color #ffffff
            }
            element "External" {
                background #999999
                color #ffffff
            }
            element "Person" {
                shape person
                background #08427b
                color #ffffff
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
        }
    }
}
