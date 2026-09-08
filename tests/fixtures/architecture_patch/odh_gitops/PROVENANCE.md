# odh-gitops architecture patch replay

This fixture preserves five representative row additions from the local
`odh-gitops` evidence-gated replay at source revision
`96fedc9507b39bd38d999fdf5c9183a8f12d809b`. The full historical run used a
Markdown change table; these sanitized files encode the same merge identities
and repository-relative evidence in the versioned JSON contract.

The automated replay reads only this directory. It does not require pipeline
logs, a source checkout, or files under `architecture/`. The fixture verifies
schema validation and deterministic merge application; it does not independently
re-adjudicate the historical source claims.
