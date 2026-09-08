workspace {
    model {
        dataScientist = person "Data Scientist" "Builds and evaluates RAG pipelines using notebooks or applications"

        ai4rag = softwareSystem "ai4rag" "Python library for automatic and optimized RAG pattern generation" {
            docProcessing = container "Document Processing" "Text extraction via docling, chunking with deterministic SHA-256 IDs" "Python"
            embeddingLayer = container "Embedding Layer" "Generates embeddings via OpenAI-compatible MaaS endpoints, batches up to 1024 chunks" "Python / OpenAI SDK"
            vectorStoreLayer = container "Vector Store Layer" "Pluggable backend with BaseVectorStoreConfig contract; supports Milvus, PGVector, ChromaDB" "Python"
            evaluationLayer = container "Evaluation & Optimization" "RAG evaluation via ragas/unitxt, statistical optimization via pygam" "Python"
        }

        s3Storage = softwareSystem "S3-Compatible Storage" "Object storage for document retrieval" "External"
        maasEndpoint = softwareSystem "OpenAI-Compatible MaaS Endpoint" "Inference API for embeddings and chat completions" "External"
        milvus = softwareSystem "Milvus" "Vector database for similarity search (gRPC/HTTPS, token auth)" "External"
        pgvector = softwareSystem "PostgreSQL + pgvector" "Relational database with vector similarity extension" "External"
        chromadb = softwareSystem "ChromaDB" "Lightweight vector database (ephemeral/persistent/client-server)" "External"

        # System context relationships
        dataScientist -> ai4rag "Uses via pip install in notebooks/apps"
        ai4rag -> s3Storage "Retrieves documents" "HTTPS/443, AWS IAM"
        ai4rag -> maasEndpoint "Generates embeddings & chat completions" "HTTPS/443, API Key"
        ai4rag -> milvus "Stores/queries vectors" "gRPC/19530, MILVUS_TOKEN"
        ai4rag -> pgvector "Stores/queries vectors" "PostgreSQL/5432, password"
        ai4rag -> chromadb "Stores/queries vectors" "HTTP/8000"

        # Container relationships
        docProcessing -> s3Storage "Fetches documents via boto3" "HTTPS"
        docProcessing -> embeddingLayer "Passes chunked text"
        embeddingLayer -> maasEndpoint "POST /embeddings" "HTTPS, API Key"
        embeddingLayer -> vectorStoreLayer "Passes embedding vectors"
        vectorStoreLayer -> milvus "Store/query" "gRPC/HTTPS"
        vectorStoreLayer -> pgvector "Store/query" "PostgreSQL"
        vectorStoreLayer -> chromadb "Store/query" "HTTP"
        evaluationLayer -> maasEndpoint "Evaluation LLM calls" "HTTPS"
        evaluationLayer -> vectorStoreLayer "Retrieval for evaluation"
    }

    views {
        systemContext ai4rag "SystemContext" {
            include *
            autoLayout
        }

        container ai4rag "Containers" {
            include *
            autoLayout
        }

        styles {
            element "External" {
                background #999999
                color #ffffff
            }
            element "Person" {
                shape Person
                background #08427b
                color #ffffff
            }
            element "Software System" {
                background #1168bd
                color #ffffff
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
        }
    }
}
