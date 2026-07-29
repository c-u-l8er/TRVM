#!/usr/bin/env python3
"""Inject bench/results.json into site/benchmarks.html.

The conformance matrix on the page is derived from the recorded run, never
typed by hand. Re-run after `python3 bench/bench.py --json bench/results.json`:

    python3 site/build_benchmarks.py

It rewrites the contents of <script id="bench-data"> in place and refuses to
run if that element is missing.
"""
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "bench" / "results.json"
PAGE = ROOT / "site" / "benchmarks.html"

BLOCK = re.compile(
    r'(<script id="bench-data" type="application/json">)(.*?)(</script>)',
    re.S,
)


def main() -> int:
    raw = RESULTS.read_bytes()
    src = json.loads(raw)

    rows = []
    for r in src["results"]:
        cells = {}
        for name, b in r["backends"].items():
            status = b["status"]
            cells[name] = {
                "ok": status == "OK",
                "status": status,
                "itr": b.get("interactions"),
                "ms": round(b["wall_ms"], 3) if b.get("wall_ms") is not None else None,
            }
        rows.append(
            {
                "name": r["name"],
                "group": r["group"],
                "want": r["want"],
                "bytes": r["term_bytes"],
                "timed": r["timed"],
                "verdict": r["verdict"],
                "nf": r["nf_agreement"],
                "itr_agree": r["interactions_agree"],
                "note": r.get("note", ""),
                "cells": cells,
            }
        )

    payload = {
        "source": "bench/results.json",
        "sha256": hashlib.sha256(raw).hexdigest(),
        "backends": src["backends"],
        "families": src["families"],
        "startup_ms": {k: round(v, 2) for k, v in src["startup_ms"].items()},
        "depth": src["depth_ceiling"],
        "rows": rows,
    }

    page = PAGE.read_text()
    if not BLOCK.search(page):
        print("no <script id=\"bench-data\"> block in benchmarks.html", file=sys.stderr)
        return 1
    blob = json.dumps(payload, separators=(",", ":"))
    PAGE.write_text(BLOCK.sub(lambda m: m.group(1) + blob + m.group(3), page, count=1))
    print(f"{len(rows)} workloads x {len(payload['backends'])} runtimes -> {PAGE}")
    print(f"results.json sha256 {payload['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
