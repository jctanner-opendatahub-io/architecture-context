# Promotion Repair Replay Results

The original live canary remains rejected and its retained evidence was unchanged.

| Run | Harness | Model | Result | Mapped analyzer rows | All analyzer rows | Mapped missing | All missing | Diagnostic |
|-----|---------|-------|--------|---------------------:|------------------:|---------------:|------------:|------------|
| claude-repetition-1 | claude | claude-opus-4-6 | success | 276 | 310 | 0 | 0 | - |
| claude-repetition-2 | claude | claude-opus-4-6 | failed | 276 | 310 | 0 | 0 | synthesis_subsection_parent_mismatch |
| codex-repetition-1 | codex | gpt-5.6-sol | success | 276 | 310 | 0 | 0 | - |
| codex-repetition-2 | codex | gpt-5.6-sol | success | 276 | 310 | 0 | 0 | - |
