# Architecture Changes: training-hub

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | integration_points | MLflow Tracking Server :: REST Client | * | <empty> | <empty> | MLflow GEPA backend uses mlflow.genai.optimize_prompts with tracking, prompt registry, and scorer framework | src/training_hub/algorithms/gepa.py:150-159, src/training_hub/algorithms/gepa.py:173-174 |
| add | integration_points | OpenAI-compatible Inference API :: REST Client | * | <empty> | <empty> | GEPA backends set OPENAI_API_BASE env var to route inference via LiteLLM to OpenAI-compatible endpoints | src/training_hub/algorithms/gepa.py:63-71, src/training_hub/algorithms/gepa.py:182-190 |
| add | integration_points | vLLM (via ART) :: In-process / Subprocess | * | <empty> | <empty> | GRPO backend uses ART LocalBackend with co-located vLLM AsyncLLM engine for inference during training | src/training_hub/algorithms/lora_grpo.py:60-78 |
| add | integration_points | ITS Hub :: Library | * | <empty> | <empty> | ITSRollout adapter uses ITS Hub generation algorithms (BestOfN, SelfConsistency) as rollout functions for GRPO | src/training_hub/algorithms/its_rollout.py:36-67 |
| add | internal_dependencies | instructlab-training | * | <empty> | <empty> | SFT backend imports and delegates to instructlab.training.run_training with TorchrunArgs and TrainingArgs | src/training_hub/algorithms/sft.py:3-8 |
| add | internal_dependencies | rhai-innovation-mini-trainer | * | <empty> | <empty> | OSFT backend depends on mini-trainer as declared in pyproject.toml core dependencies | pyproject.toml:17 |
| add | internal_dependencies | openpipe-art | * | <empty> | <empty> | GRPO backend uses ART framework for co-located vLLM + Unsloth LoRA training with time-shared GPU | src/training_hub/algorithms/lora_grpo.py:60-78 |
