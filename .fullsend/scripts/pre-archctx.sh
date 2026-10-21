#!/usr/bin/env bash
# pre-archctx.sh — harness pre_script (runs on the RUNNER, before
# sandbox creation and target-repo upload).
#
# Ensures the target repo carries the workflow's inputs:
#   - checkouts/jctanner.head/<repo>  (component checkouts, gitignored)
#   - architecture/<platform>/.analyzer/  (committed baselines)
#   - architecture/<platform>/components.json  (committed work items)
#
# Idempotent: when the inputs exist, verifies that each checkout's HEAD
# matches the ref pinned in components.json (fail loudly on drift);
# when missing (fresh clone in CI), runs the prepare pipeline
# (scripts/archctx.sh prepare: fetch + analyze + manifest).
set -euo pipefail

REPO="${TARGET_REPO_DIR:?TARGET_REPO_DIR not set by runner}"
PLATFORM="${ARCHCTX_PLATFORM:-breadboard}"
cd "$REPO"

if [ -f "architecture/$PLATFORM/components.json" ] && [ -d checkouts/jctanner.head ]; then
	python3 - "$PLATFORM" << 'EOF'
import json, subprocess, sys

platform = sys.argv[1]
items = json.load(open(f"architecture/{platform}/components.json"))
bad = []
for item in items:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=item["repoDir"],
        capture_output=True, text=True, timeout=10,
    ).stdout.strip()
    pinned = item["promptContext"]["ref"]
    if head != pinned:
        bad.append(
            f"{item['key']}: checkout at {head[:12]}, "
            f"components.json pins {pinned[:12]} (run scripts/archctx.sh prepare)"
        )
if bad:
    sys.exit("pre-archctx: pin mismatch —\n  " + "\n  ".join(bad))
print(f"pre-archctx: {len(items)} work items verified against pinned refs")
EOF
else
	echo "pre-archctx: workflow inputs missing — running prepare"
	./scripts/archctx.sh prepare --platform "$PLATFORM"
fi
