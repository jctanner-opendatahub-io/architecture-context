# Reuse observation scope edge cases

Status: fixed. Found by independent P2 review cycle 1 on 2026-09-07.

Severity/requirements: Low; SC-14/SC-25.

F4: porcelain -z rename parsing creates bogus dirty path. F5: ignored files and rg options expanding beyond tracked search trees are not consistently accounted. F6: shell redirections become bogus rg roots. Repair with meaningful Git/search tests or conservative explicit misses. F7 safe alternation-pattern rejection and predecessor-dependency replay semantics also need clear documentation.

Evidence: `logs/structured-component-assembly/20260907-resume/p2-review-report.md`,
reviewer session `7d385b28-9ec6-4a62-9488-3e49a02fe58e`, Fable 5.1/high.
No phase-two acceptance. Bounded Python repair and fresh re-review required.

Coordinator follow-up probe (2026-09-07): changing a committed parent `.gitignore`
from ignoring tracked `src/a.txt` to empty changed `rg -n secret-marker src` from
exit 1/no matches to exit 0/a match, while frozen P2
`directory_tree_identity(root, "src")` remained identical. Script and actual
output: `20260907-resume/search-ignore-probe.py` and
`search-ignore-probe-result.json`. This proves a missing search-configuration
input in the scoped tree identity, not an executed full reuse-hit claim.

Before re-review, require relevant ancestor ignore/config dependencies to be
recorded and compared, actual search replay with sufficient identity, or a
conservative miss when completeness cannot be established. Also consider explicit
include globs and external `RG_CONFIG_PATH` when defining the supported subset.
The active repair handoff predates this probe; coordinator must explicitly route
this follow-up after the worker returns if its F5 repair does not cover it.

Independent acceptance: Fable cycle 3 PASS, session b7b8d76a-e126-4874-be29-36c2433fe4eb. Evidence: `logs/structured-component-assembly/20260907-resume/p2-review3-report.md`. All prior evidence and limitations retained. P3 producer/publication integration remains separate.
