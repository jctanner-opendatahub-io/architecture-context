# Rust Analyzer Rejects Inherited Cargo Package Version

## Status

Fixed locally on 2026-09-04; awaiting normal repository integration.

## Symptom

Static analysis of `praxis-proxy/policy` failed before producing
`component-architecture.json` or `analyzer_architecture.md`:

```text
parse workspace member Cargo.toml ".../crates/ppe/Cargo.toml":
unhandled kv part: string
```

## Cause

The Rust manifest model declared `package.version` as a Go string. Standard
Cargo workspace inheritance represents `version.workspace = true` as a table,
which the TOML decoder cannot assign to that string field. The analyzer did not
otherwise consume the package version.

## Resolution

Remove the unused scalar version field so both literal package versions and
workspace-inherited versions decode successfully. Cover the inherited form with
a Rust workspace extraction test.
