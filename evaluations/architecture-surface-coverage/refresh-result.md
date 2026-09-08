# Architecture Surface Analyzer Refresh Result

Status: **complete**.

Analyzer base revision: `39209078846f15f1909373c106d2d665a907a509`.
Analyzer source diff: `6376b9ffdf60420986f5d34b5f55ed145cf55eb85587a9028fe52fefa6a38c84`.
Analyzer source tree: `a6a9cb810949c275f7650074fe02b6adefe2495123a24348e70e015ba93bb6a7`.
Analyzer binary: `d13d83d5229a6a708507a8932353ce10fb281b1af8c4fe125a94d2a8d34106b8`.

Refreshed 9 pinned artifacts with 43 behavioral evidence records and 157 extracted CRD schemas.

| Component | Role | Commit | Behavioral evidence | Records | Schemas |
|---|---|---|---|---:|---:|
| `rhods-operator` | operator | `4ada791819c522a4cda54f9029ab3e4056ed31ed` | present-records | 21 | 130 |
| `models-as-a-service` | operator | `b5bc98727a7e77dc427cb658de061745e3e04795` | present-records | 16 | 9 |
| `odh-model-controller` | operator | `8ff72dd9da97b577d1bc33a3cce6e1cd3e4b89b5` | present-records | 6 | 18 |
| `llm-d-routing-sidecar` | service | `78051b86ff13c4511fb1c8c7def56e04b0850b67` | present-empty | 0 | 0 |
| `NeMo-Guardrails` | service | `0740bef72f485e79aef20b237c5903c44ff838c1` | present-empty | 0 | 0 |
| `batch-gateway` | service | `455370eac43cd9923754897e04339ad7e9377a04` | present-empty | 0 | 0 |
| `distributed-workloads` | manifest | `8dd512b732609464f74d38b83b5c50cbf7151276` | present-empty | 0 | 0 |
| `kube-auth-proxy` | manifest | `0969a391dd59a3df56e969f57ea83b6914a1c40a` | present-empty | 0 | 0 |
| `rhoai-mcp` | manifest | `d3498af571e6f2551b4ef33a19f628506aaae456` | present-empty | 0 | 0 |

The structured analyzer outputs are stored under `refreshed-analyzers/`. Historical documents remain comparison-only; generated architecture was not modified and no live agent ran.
