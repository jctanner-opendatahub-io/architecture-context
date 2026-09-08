# Bug: Reuse noncanonical number literals cause conservative misses

Status: open, non-blocking P2 follow-up.

F15 informational: Python parsed JSON reserialization differs from Go raw-number canonicalization for noncanonical literals. All148 corpus inputs and real11 Go-normalized inputs agree; model has no float fields. Differences cause explicit miss, no false hit. Preserve raw Go binding if producer evolves; no hit-rate promise.

Evidence: `logs/structured-component-assembly/20260907-resume/p2-review3-report.md`.
