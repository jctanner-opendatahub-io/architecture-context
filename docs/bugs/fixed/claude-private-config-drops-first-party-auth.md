# Claude Private Config Drops First-Party Authentication

## Status

Fixed on 2026-09-05 while preparing the repeated architecture-surface live
canary. No model call was launched.

## Symptom

The host Claude CLI reports a logged-in first-party `claude.ai` subscription,
but the same read-only authentication preflight with the pipeline's empty
private `CLAUDE_CONFIG_DIR` reports `loggedIn: false`. A Claude pipeline run
would therefore fail before synthesis when Vertex and API-key authentication
are unavailable.

## Cause

`run_agent` gives every Claude invocation an empty temporary config directory
to isolate mutable session state. It does not stage the host config's
`.credentials.json`, so first-party authentication is lost with that state.

## Resolution

When `CLAUDE_AUTH_CONFIG_DIR` explicitly selects a source config directory, the
runner copies only `.credentials.json` into the private directory with
owner-only permissions. It does not copy settings, projects, history, plugins,
or other mutable Claude state. With no explicit source, API-key and
provider-specific operation remain unchanged. Credential contents are never
logged, and the private directory is still removed after each run.

Unit tests cover the staged and absent-credential paths. A read-only preflight
using the staged private directory, with all Vertex selection variables removed,
reported `loggedIn: true`, `authMethod: claude.ai`, and
`apiProvider: firstParty`.
