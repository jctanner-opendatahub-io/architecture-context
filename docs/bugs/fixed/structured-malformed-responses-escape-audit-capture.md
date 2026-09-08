# Bug: Some malformed structured responses escape normal failure recording

Status: open; saved interrupted P3 review probes, pending resumed independent assessment.

The saved probe_py_edges.out and probe_py_edges2.out show nonfinite numbers,
unpaired Unicode surrogates, and extreme JSON nesting can raise uncaught
exceptions while retaining zero responses in the failure envelope. Original
model output must remain auditable, and malformed output must receive bounded,
explicit failure handling. Validate reproduction and repair without accepting
invalid JSON or losing exact returned text.

Evidence: logs/structured-component-assembly/20260907-resume/p3-review1-partial-evidence/
probe_py_edges.out, probe_py_edges2.out, and their saved probe scripts.

Independent repair criteria met: P3 cycle2, Fable/high session8e971bcc-9390-4b38-b213-4faa03d218a4; see p3-review2-report.md. Whole P3 gate remains open on new F6/F7.
