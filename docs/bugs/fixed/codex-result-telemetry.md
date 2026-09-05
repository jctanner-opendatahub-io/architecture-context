# Codex result serialization and source-read telemetry

The 20260905T030959Z rhods-operator run exposed enum serialization walking
`__dict__` into a mappingproxy, and missing source-read observations in the
normalized Codex result. A reporting failure was subsequently recovered as an
agent success by architecture postprocessing.

Fix: serialize enums by wire value, collect successful SDK read actions relative
to the resolved checkout, and preserve failed postprocessing results without retry.
Verified with 43 focused tests, Ruff, and read-only completed-log replay: six
source files, 14 observed read actions, and no justification warnings. Bounds
are recorded only when the SDK action contains a recognized bounded read;
unknown commands are not treated as evidence. Historical outputs are unchanged.
