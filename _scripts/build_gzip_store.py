#!/usr/bin/env python3
"""Compress jobs.json to jobs.json.gz for deploy (Git-friendly bundle)."""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IN = ROOT / "data" / "jobs.json"
DEFAULT_OUT = ROOT / "data" / "jobs.json.gz"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build gzip job store for deploy")
    parser.add_argument("--in", dest="inp", type=Path, default=DEFAULT_IN)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    if not args.inp.is_file():
        print(f"ERROR: input not found: {args.inp}", file=sys.stderr)
        print("Run: python _scripts/ingest_feed.py --fetch", file=sys.stderr)
        return 1

    raw = args.inp.read_bytes()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(args.out, "wb", compresslevel=9) as gz:
        gz.write(raw)

    # Validate round-trip metadata
    with gzip.open(args.out, "rt", encoding="utf-8") as gz:
        data = json.load(gz)
    job_count = data.get("meta", {}).get("job_count", len(data.get("jobs") or []))

    raw_mb = len(raw) / (1024 * 1024)
    gz_mb = args.out.stat().st_size / (1024 * 1024)
    ratio = (1 - args.out.stat().st_size / len(raw)) * 100 if raw else 0

    print(f"Wrote {args.out}")
    print(f"Jobs: {job_count}")
    print(f"Size: {raw_mb:.1f} MB raw -> {gz_mb:.1f} MB gzip ({ratio:.0f}% smaller)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
