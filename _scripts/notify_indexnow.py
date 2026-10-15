#!/usr/bin/env python3
"""Notify IndexNow about added/updated/removed vacancy URLs.

No-op unless INDEXNOW_KEY is set. Does not invent credentials.
Requires PUBLIC_BASE_URL (or RENDER_EXTERNAL_URL) and a hosted key file
at https://{host}/{INDEXNOW_KEY}.txt (see doc-assets/index-submission-runbook.md).

Usage:
  INDEXNOW_KEY=... PUBLIC_BASE_URL=https://example.com \\
    python _scripts/notify_indexnow.py --lifecycle data/lifecycle-latest.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from service.store import (  # noqa: E402
    get_job_by_id,
    load_jobs,
    public_base_url,
    vacancy_public_url,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Submit vacancy URL changes to IndexNow")
    parser.add_argument(
        "--lifecycle",
        type=Path,
        default=ROOT / "data" / "lifecycle-latest.json",
    )
    parser.add_argument(
        "--endpoint",
        default=os.environ.get("INDEXNOW_ENDPOINT", "https://api.indexnow.org/indexnow"),
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    key = (os.environ.get("INDEXNOW_KEY") or "").strip()
    if not key:
        print("IndexNow skipped: INDEXNOW_KEY not set")
        return 0

    base = public_base_url()
    if not base:
        print("IndexNow skipped: PUBLIC_BASE_URL / RENDER_EXTERNAL_URL not set", file=sys.stderr)
        return 0

    if not args.lifecycle.is_file():
        print(f"IndexNow skipped: lifecycle file missing ({args.lifecycle})")
        return 0

    with args.lifecycle.open(encoding="utf-8") as f:
        life = json.load(f)

    data = load_jobs()
    urls: list[str] = []
    for job_id in (life.get("added") or []) + (life.get("updated") or []):
        job = get_job_by_id(data["jobs"], job_id)
        if job:
            urls.append(vacancy_public_url(job, base=base))
    # Removed: still notify the canonical URL pattern if we can reconstruct
    for job_id in life.get("removed") or []:
        # Without previous job object, notify catalog + a best-effort path
        urls.append(f"{base}/vacancies/{job_id}")

    # Always refresh hubs when inventory changes
    if life.get("added") or life.get("updated") or life.get("removed"):
        urls.extend([f"{base}/", f"{base}/vacancies", f"{base}/sitemap.xml"])

    # Dedupe preserve order
    seen: set[str] = set()
    url_list = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            url_list.append(u)

    if not url_list:
        print("IndexNow: no URL changes")
        return 0

    host = base.replace("https://", "").replace("http://", "").split("/")[0]
    payload = {
        "host": host,
        "key": key,
        "keyLocation": f"{base}/{key}.txt",
        "urlList": url_list[:10000],
    }
    print(f"IndexNow submit {len(payload['urlList'])} URLs → {args.endpoint}")
    if args.dry_run:
        print(json.dumps(payload, indent=2)[:2000])
        return 0

    req = urllib.request.Request(
        args.endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            print(f"IndexNow OK status={resp.status}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        print(f"IndexNow HTTP {exc.code}: {body}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"IndexNow error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
