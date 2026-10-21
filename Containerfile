# Sandbox image for the arch-context harness (ladder rung 2+).
# Pattern from the workflow-engine PoC's Containerfile: the pi process
# runs in the container with its own config state; nothing from the
# host ~/.pi is mounted. pi pinned to the version under test — match
# the host this port was verified on (1.3.0; the PoC used 1.1.0).
#
# The plugin tree is NOT baked in: the fullsend runtime uploads declared
# plugins to a runner-owned extensions dir at sandbox setup (ADR 0094).
# This image only provides the runtime prerequisites.
#
# Build (rung 2, from the repo root):
#   podman build -t localhost/fullsend-archctx:v1 -f Containerfile .
FROM docker.io/library/node:24-bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       bash ca-certificates git ripgrep python3 \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g --ignore-scripts @earendil-works/pi-coding-agent@1.3.0

WORKDIR /workspace
