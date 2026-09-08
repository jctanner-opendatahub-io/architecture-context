# Bug: Input mutation can leave a completed reuse record inconsistent

Status: open; saved interrupted P3 review probe, pending resumed independent assessment.

The saved probe_seam_window.out reports a successful zero-call reuse after an
input mutation, but the persisted evidence analyzer fingerprint differs from
the accepted document fingerprint. A run record is written and later fails to
reload. The actual supplied inputs and accepted output must remain bound across
the run; a completed result must not persist internally inconsistent state.

Evidence: logs/structured-component-assembly/20260907-resume/p3-review1-partial-evidence/
probe_seam_window.out and probes/probe_seam_window.py. No source repair while
review inputs remain frozen; await independent diagnosis and exact scope.

Independent repair criteria met: P3 cycle2, Fable/high session8e971bcc-9390-4b38-b213-4faa03d218a4; see p3-review2-report.md. Whole P3 gate remains open on new F6/F7.
