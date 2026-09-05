# Analyzer Renderer Drops Component Alias

## Status

Fixed locally on 2026-09-05; awaiting normal repository integration.

## Symptom

The prefixed output `praxis-policy.md` was generated with the heading
`# Component: policy` even though `component-map.json` keyed the component as
`praxis-policy`.

## Cause

Extraction correctly retained the canonical Git repository name (`policy`).
Rendering copied that name directly into the architecture document and used
the component map only for provenance. It did not reverse-match the canonical
`repo_org/repo_name` identity to the component-map key.

## Resolution

During analyzer normalization, resolve a unique component-map entry by its
canonical repository identity and use the map key as the rendered component
identity. Preserve the raw repository name when no match—or multiple matches—
exists. Architecture promotion also enforces the final H1 from the canonical
output filename.
