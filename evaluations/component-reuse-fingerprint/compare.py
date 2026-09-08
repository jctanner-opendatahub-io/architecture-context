"""Compare EA.1 and EA.2 analyzer outputs for semantic-fingerprint reuse."""

import collections
import hashlib
import json
import re
import sys
from pathlib import Path

S = Path(sys.argv[1])
VOL = {
    "analyzer_version",
    "commit_sha",
    "extracted_at",
    "generated_at",
    "schema_version",
}
PATH = re.compile(r"(?:/home/[^\"\s]*?)?checkouts/[^/\"\s]+/")
# Categories that are expected to churn without architectural meaning.
NOISE = {
    "coverage_findings",
    "cross_references",
    "data_coverage",
    "gap_evidence_index",
    "recent_changes",
    "summary",
    "synthesis_evidence",
}


def canon(o):
    if isinstance(o, dict):
        return {k: canon(v) for k, v in sorted(o.items()) if k not in VOL}
    if isinstance(o, list):
        return [canon(x) for x in o]
    if isinstance(o, str):
        return PATH.sub("<co>/", o)
    return o


def fp(d):
    return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()[:12]


def load(tag):
    out = {}
    for p in sorted((S / tag).glob("*.json")):
        try:
            out[p.stem] = json.load(open(p))
        except Exception:
            pass
    return out


A, B = load("ea1"), load("ea2")
common = sorted(set(A) & set(B))
print(f"extracted: ea1={len(A)} ea2={len(B)} common={len(common)}")
same_commit = same_full = same_semantic = 0
diff_keys = collections.Counter()
semantic_hits, semantic_misses = [], []
for c in common:
    a, b = canon(A[c]), canon(B[c])
    if A[c].get("commit_sha") == B[c].get("commit_sha"):
        same_commit += 1
    if fp(a) == fp(b):
        same_full += 1
    sa = {k: v for k, v in a.items() if k not in NOISE}
    sb = {k: v for k, v in b.items() if k not in NOISE}
    if fp(sa) == fp(sb):
        same_semantic += 1
        if A[c].get("commit_sha") != B[c].get("commit_sha"):
            semantic_hits.append(c)
    else:
        keys = sorted(k for k in set(sa) | set(sb) if sa.get(k) != sb.get(k))
        for k in keys:
            diff_keys[k] += 1
        semantic_misses.append((c, keys))
n = len(common)
print(f"same commit:              {same_commit:3d} ({100*same_commit//n}%)")
print(f"same full canonical JSON: {same_full:3d} ({100*same_full//n}%)")
print(f"same semantic facts:      {same_semantic:3d} ({100*same_semantic//n}%)  "
      f"[new commit but same facts: {len(semantic_hits)}]")
print("\nmost common differing categories among misses:")
for k, v in diff_keys.most_common(15):
    print(f"  {k:28s} {v}")
print("\nsemantic hits with new commits:", semantic_hits[:20])
print("\nmisses differing in exactly one category:")
for c, keys in semantic_misses:
    if len(keys) == 1:
        print(f"  {c}: {keys[0]}")
errs = list((S / "ea2").glob("*.err"))
bad = [e for e in errs if e.stat().st_size > 0 and not e.with_suffix("").exists()]
print(f"\nextraction failures: {len(bad)}")
for e in bad[:10]:
    print("  ", e.stem, open(e).read().strip()[:120])
