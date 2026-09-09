# Proposed future structured-component live canary (not authorized or run)

Status: proposal only. Adoption remains HOLD. This packet is deliberately
separate from the P5 offline gate and needs explicit model, cost, network, and
execution authorization.

## Frozen candidate set

The execution owner must re-verify these identities immediately before a run
and stop if any differ. A refreshed analyzer build and clean source checkout
identity must be added to each live run manifest; the P5 offline binary is
evidence for offline replay, not automatic authority for a future run.

Three analyzer identities have distinct evidence roles and none is automatic
authority for a future live run:

- The P4 replay used dirty-worktree binary SHA-256
  `98fa820c2224d0b8ad733f4bfbf09a9da86ecf6a6961a5fd2a79d603058a1ab7`
  from head `e0f6f367` with the recorded modified-state source identity
  `sha256:7202f951f6f48df39a9de3330f03385511f56ed82774150b015547c24c2b2e4b`.
- The old fresh comparison used committed-archive binary SHA-256
  `458c04cb0387fe70b3dab8d5e0aedb88dccd0ee444d8cfc6bfce14ae6606f4e7`
  from the verified `e0f6f367` archive SHA-256
  `5f753cdb2ed40b3207c16985ca3dd83a839be578c8276bc31203e03bdfad4afa`.
  Its extractor ordering varied; its 31/37 and 30/36 observations are samples.
- The ordering repair used dirty-source `-buildvcs=false` binary SHA-256
  `2ffc6dd7f567a941162cfa842cc7c20a5c8b4c56678b87073ffd90a9b5f92be8`
  with source-manifest SHA-256
  `86c1661ee978025117119934116c1777a84dfa1f70f16f8281f7f140844a6d40`.
  It produced stable 32/38 results in two 184-side runs and awaits cycle-2
  independent review.

The rejected interim `reuse-comparison.json` is retained only as superseded
attempt evidence; it is not the manifest of record. Build manifests, diffs,
commands, and raw repaired outputs are under
`logs/structured-component-assembly/20260909-ordering-repair/`. A future run
must build and freeze its own reviewed analyzer identity.

| Candidate | Purpose | Frozen input identity |
|---|---|---|
| `rhods-operator` | Large operator and comparison with the rejected historical canary | repo `red-hat-data-services/rhods-operator`, commit `4ada791819c522a4cda54f9029ab3e4056ed31ed`; saved canary analyzer SHA-256 `e3f697d7f7e38ed5a93e50df4919158f8a566ebfe8cd79ac0d618dccfb72285e` |
| `batch-gateway` | Representative service | repo `red-hat-data-services/batch-gateway`, commit `455370eac43cd9923754897e04339ad7e9377a04`; saved analyzer SHA-256 `805e0ebecb267e084000a7d7cff902b43c03b66d01fa7acc068a8f6ddc3988fb` |
| `example-chart` | Manifest-shaped structural fixture; not a substitute for source quality review | `tests/fixtures/architecture_surface_coverage/manifest/component-architecture.json`, SHA-256 `57015d4d4228f48cc677c0fd8fdacd95d71f125dca5df30318dccc8a41a80f74`; corpus SHA-256 `594323470f99ab583bfd337834a23a8d95e558caa3e5d344f2ea19a5cdfdc8a3` |
| `praxis-policy` | Prefixed, explicitly not-integrated identity | repo `praxis-proxy/policy`, commit `9ee972ff37dfd7771650540eeffd8edab04b1a49`; saved analyzer SHA-256 `d026baba2cc7f67ed3b9d2c8249bfd196e761bcd19fb1b6864a2eb4bed53e151`; component-map SHA-256 `63919cfe029c22fd2e7635d0afdfc2c2ed1ab05e74248279bbeb15bb13416140`; accepted not-integrated consumer fixture SHA-256 `edf8d93c634cefd9ec2b30697a3d328f6ab4d871391d9b19b6eb99371c760267` |

`example-chart` tests the manifest role and schema shape only. A future request
for semantic quality evidence must name and freeze a real manifest-only source
repository; this proposal does not invent one from the current component map.

## Proposed hard bounds

- One repetition per candidate for one explicitly authorized model/harness;
  no automatic second model, fallback, retry, or substitution.
- One initial synthesis call, at most one evidence follow-up, and at most one
  structural repair per candidate: 3 calls per candidate and 12 calls total.
- Maximum 30 minutes wall time per candidate and 2 hours total.
- Maximum approved spend: USD 20 for the packet. Stop before a request that
  could cross the remaining bound. Record provider-reported cost; if the
  provider does not expose cost, stop after the first candidate and request a
  revised authorization rather than estimating it as measured.
- On any actual rate limit, stop immediately and retain the pending step. Do
  not retry, change models, or fall back.
- Keep every live output under a new run directory. Never overwrite the P5
  offline evidence or the original canary.

The run manifest must bind repository commit and tree, dirty/untracked state,
component map and overlays, analyzer source manifest and binary, schemas,
prompt/evidence bundle, settings, requested and resolved model when exposed,
raw responses, call sequence, and every published artifact hash.

## Acceptance

All four candidates must meet every applicable condition:

1. Complete valid four-file authority; zero candidate-Markdown parsing; zero
   unexplained repair or fallback; no stale or mismatched derivative.
2. Exact analyzer fact accounting, including resource, non-resource, mixed and
   legacy RBAC; FIPS only under Security; no silent unsupported legacy fields.
3. Independent source review finds zero unsupported accepted claims and records
   supported, omitted, unresolved, and not-applicable surfaces separately.
4. `praxis-policy` retains its prefix, source component `policy`, repository,
   alias, version scope, and `not-integrated` uncertainty.
5. JSON-only typed query, complete four-file repository/package checks,
   mixed-format consumers, log-deletion audit, interruption/recovery, and
   rollback probes all pass on the exact candidate bytes.
6. Calls, follow-ups, repairs, tokens (including cache creation/read), latency,
   provider cost when exposed, warnings, unsupported claims, and consumer
   regressions are reported without combining implementation-review usage.

The packet fails closed on any unmet condition or unavailable semantic review.
A passing packet is evidence for a later adoption decision, not automatic
permission to make the route default.

## Rollback

Keep the structured route opt-in through review. On failure, retain the run and
rejected proposal, leave the last accepted snapshots untouched, disable the
opt-in route, and remove only disposable new-run staging after it is archived.
For an accepted four-file snapshot, restore all four files together from
version control or use the tested recovery protocol. Never delete only the
document authority to force legacy fallback. Warning-only coverage and disabled
subsection workers are outside this canary and remain unchanged.
