# Structured synthesis flag help describes the former private-only route

Status: open, documentation follow-up.
Found while answering the user's feature-flag question, 2026-09-09.

`lib/cli.py` defines `--structured-synthesis` with default False, but its help
still says the route is private and does not publish component artifacts.
The accepted publication work integrated artifact publication into this route.
The help needs to describe current behavior while retaining opt-in defaults.

Acceptance: reconcile the help with the current architecture phase and public
documentation; verify the relevant CLI help output. This is not a request to
enable the route by default or execute a live run. No code was changed during
the pending final review.
