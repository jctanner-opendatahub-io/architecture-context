# Architecture Changes: training-operator

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| delete | integration_points | Kubeflow Notebooks :: CRD CRUD | * | <empty> | <empty> | The kubeflow.org RBAC rules grant access to training job CRDs (jaxjobs, mpijobs, paddlejobs, pytorchjobs, tfjobs, xgboostjobs), not notebook CRDs. No notebooks.kubeflow.org resource appears in the RBAC role. | manifests/base/rbac/role.yaml:87-241 |
| delete | integration_points | Kubeflow Notebooks (kubeflow.org) :: CRD CRUD | * | <empty> | <empty> | Duplicate of the Kubeflow Notebooks row with same mislabeling. The kubeflow.org resources in the RBAC role are exclusively training job CRDs owned by this operator, not external notebook dependencies. | manifests/base/rbac/role.yaml:87-241 |
| delete | internal_dependencies | Kubeflow Notebooks (kubeflow.org) | * | <empty> | <empty> | The kubeflow.org RBAC grants cover the operator's own training job CRDs (jaxjobs, mpijobs, etc.), not an external Kubeflow Notebooks dependency. No notebooks resource or controller reference exists in the codebase. | manifests/base/rbac/role.yaml:87-241 |
