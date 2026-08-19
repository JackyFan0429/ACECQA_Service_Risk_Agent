#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data" / "policy" / "policy_chunks.jsonl"

if not CORPUS.exists():
    raise SystemExit("Policy corpus missing. Run: python scripts/ingest_policy.py")

items = [json.loads(line) for line in CORPUS.read_text(encoding="utf-8").splitlines() if line.strip()]
by_source = Counter(item["source_id"] for item in items)
missing = [key for key in ["chunk_id", "source_id", "source_title", "source_url", "text"] if any(not x.get(key) for x in items)]
print(f"Chunks: {len(items)}")
print(f"Sources: {len(by_source)}")
for source_id, count in sorted(by_source.items()):
    print(f"- {source_id}: {count}")
if missing:
    raise SystemExit("Missing required fields: " + ", ".join(missing))
print("Corpus integrity: PASS")
