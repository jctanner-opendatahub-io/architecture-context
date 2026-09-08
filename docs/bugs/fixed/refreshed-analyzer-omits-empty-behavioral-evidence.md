# Refreshed Analyzer Omits Empty Behavioral Evidence

## Status

Fixed on 2026-09-05. Found by the nine-artifact architecture-surface analyzer
refresh and accepted by independent review.

## Symptom

Six freshly extracted non-Go or behavior-free artifacts omitted the
`behavioral_evidence` property. The rollout audit consequently classifies them
as `field-absent`, the same state used for legacy analyzer artifacts that
predate behavioral extraction, and recommends refreshing artifacts that were
just refreshed.

## Cause

`model.Input.BehavioralEvidence` used `omitempty`. An empty extraction result was
therefore indistinguishable on disk from output produced before the field
existed.

## Resolution

`model.Input.BehavioralEvidence` no longer uses `omitempty`, and `EncodeInput`
normalizes a nil slice to an empty slice. Newly encoded analyzer output includes
`"behavioral_evidence": []` when no records were extracted, while legacy JSON
that omits the field still decodes successfully.

The rebuilt analyzer and repeated nine-artifact refresh report three
`present-records` artifacts and six `present-empty` artifacts with no
`field-absent` refresh recommendation. Independent review rebuilt the analyzer
byte-for-byte, verified the compatibility boundary, reproduced the refreshed
audit, and accepted the fix with no blocking findings.
