#!/usr/bin/env python3
"""Notify IndexNow about vacancy URL changes (or bootstrap hubs + inventory).

Reads key from INDEXNOW_KEY env or data/indexnow.key.
Requires PUBLIC_BASE_URL (or RENDER_EXTERNAL_URL) and a hosted key file
at https://{host}/{KEY}.txt (see doc-assets/index-submission-runbook.md).

Usage:
  PUBLIC_BASE_URL=https://epam-ai-vacancies.onrender.com \\
    python _scripts/notify_indexnow.py --bootstrap
  PUBLIC_BASE_URL=... python _scripts/notify_indexnow.py --lifecycle data/lifecycle-latest.json
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
    list_countries,
    load_jobs,
    public_base_url,
    vacancy_public_url,
)


def resolve_key() -> str:
    key = (os.environ.get("INDEXNOW_KEY") or "").strip()
    if key:
        return key
    path = ROOT / "data" / "indexnow.key"
    if path.is_file():
        return path.read_text(encoding="utf-8").strip()
    return ""


def submit(url_list: list[str], *, base: str, key: str, endpoint: str, dry_run: bool) -> int:
    seen: set[str] = set()
    deduped: list[str] = []
    for u in url_list:
        if u and u not in seen:
            seen.add(u)
            deduped.append(u)
    if not deduped:
        print("IndexNow: no URLs")
        return 0

    host = base.replace("https://", "").replace("http://", "").split("/")[0]
    payload = {
        "host": host,
        "key": key,
        "keyLocation": f"{base}/{key}.txt",
        "urlList": deduped[:10000],
    }
    print(f"IndexNow submit {len(payload['urlList'])} URLs → {endpoint}")
    if dry_run:
        print(json.dumps({**payload, "urlList": payload["urlList"][:8] + ["…"]}, indent=2)[:2500])
        return 0

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            print(f"IndexNow OK status={resp.status}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        print(f"IndexNow HTTP {exc.code}: {body}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"IndexNow error: {exc}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Submit vacancy URL changes to IndexNow")
    parser.add_argument(
        "--lifecycle",
        type=Path,
        default=ROOT / "data" / "lifecycle-latest.json",
    )
    parser.add_argument(
        "--bootstrap",
        action="store_true",
        help="Submit hubs + sitemap + all vacancy detail URLs (first IndexNow seed)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="With --bootstrap, cap vacancy URLs (0 = all, max 9900)",
    )
    parser.add_argument(
        "--endpoint",
        default=os.environ.get("INDEXNOW_ENDPOINT", "https://api.indexnow.org/indexnow"),
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    key = resolve_key()
    if not key:
        print("IndexNow skipped: INDEXNOW_KEY / data/indexnow.key not set")
        return 0

    base = public_base_url()
    if not base:
        print("IndexNow skipped: PUBLIC_BASE_URL / RENDER_EXTERNAL_URL not set", file=sys.stderr)
        return 1

    data = load_jobs()
    urls: list[str] = []

    if args.bootstrap:
        urls.extend(
            [
                f"{base}/",
                f"{base}/vacancies",
                f"{base}/vacancies?remote=true",
                f"{base}/sitemap.xml",
                f"{base}/llms.txt",
                f"{base}/robots.txt",
            ]
        )
        for country in list_countries(data["jobs"])[:40]:
            urls.append(f"{base}/vacancies?country={country['country']}")
        jobs = data["jobs"]
        if args.limit and args.limit > 0:
            jobs = jobs[: min(args.limit, 9900)]
        else:
            jobs = jobs[:9900]
        for job in jobs:
            urls.append(vacancy_public_url(job, base=base))
    else:
        if not args.lifecycle.is_file():
            print(f"IndexNow skipped: lifecycle file missing ({args.lifecycle})")
            return 0
        with args.lifecycle.open(encoding="utf-8") as f:
            life = json.load(f)
        for job_id in (life.get("added") or []) + (life.get("updated") or []):
            job = get_job_by_id(data["jobs"], job_id)
            if job:
                urls.append(vacancy_public_url(job, base=base))
        for job_id in life.get("removed") or []:
            urls.append(f"{base}/vacancies/{job_id}")
        if life.get("added") or life.get("updated") or life.get("removed"):
            urls.extend([f"{base}/", f"{base}/vacancies", f"{base}/sitemap.xml"])

    return submit(urls, base=base, key=key, endpoint=args.endpoint, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
