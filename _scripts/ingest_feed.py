#!/usr/bin/env python3
"""Ingest LinkedIn XML feed into normalized jobs.json store.

Usage (from workspace root or this project root):
  python projects/ai-native-vacancy-service/_scripts/ingest_feed.py
  python projects/ai-native-vacancy-service/_scripts/ingest_feed.py \\
    --feed projects/job-postings-okr/doc-assets/linkedin-match-work/runs/2026-08-31-fresh-now/feed-linkedin.xml
  python projects/ai-native-vacancy-service/_scripts/ingest_feed.py --fetch
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "data" / "jobs.json"
FEED_URL = "https://vacancies.careers.epam.com/api/feed/linkedin"
WORKSPACE_FEED_CANDIDATES = [
    Path("projects/job-postings-okr/doc-assets/linkedin-match-work/inbox/feed-linkedin-live.xml"),
    Path("projects/job-postings-okr/doc-assets/linkedin-match-work/runs/2026-08-31-fresh-now/feed-linkedin.xml"),
]

BLT_RE = re.compile(r"(blt[a-z0-9]+)", re.I)
_WS = re.compile(r"\s+")


def cdata(tag: str, block: str) -> str:
    m = re.search(rf"<{tag}><!\[CDATA\[(.*?)\]\]></{tag}>", block, re.S)
    if m:
        return m.group(1).strip()
    m = re.search(rf"<{tag}>(.*?)</{tag}>", block, re.S)
    return m.group(1).strip() if m else ""


def blt_of(s: str) -> str:
    m = BLT_RE.search(s or "")
    return m.group(1).lower() if m else ""


def brand_from_pid(pid: str) -> str:
    if pid.startswith("anywhere_"):
        return "anywhere"
    if pid.startswith("careers-india_"):
        return "careers-india"
    if pid.startswith("epamgdo_"):
        return "epamgdo"
    return pid.split("_", 1)[0] or "unknown"


def strip_html(text: str) -> str:
    if not text:
        return ""
    t = re.sub(r"<[^>]+>", " ", text)
    t = unescape(t).replace("\xa0", " ")
    return _WS.sub(" ", t).strip()


def parse_mmddyyyy(s: str) -> str:
    """Convert MM/DD/YYYY (or YYYY-MM-DD) to ISO date YYYY-MM-DD; empty on failure."""
    s = (s or "").strip()
    if not s:
        return ""
    head = s[:10]
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(head, fmt).date().isoformat()
        except ValueError:
            continue
    return s


def parse_pid_geo(pid: str) -> tuple[str, str, str]:
    """Return (locale, city, country) from partnerJobId.

    Examples:
      anywhere_blt..._en-us__Argentina -> ('en-us', '', 'Argentina')
      epamgdo_blt..._en-us_Munich_Germany -> ('en-us', 'Munich', 'Germany')
      careers-india_blt..._en-us_Pune_India -> ('en-us', 'Pune', 'India')
    """
    m = re.search(r"(blt[a-z0-9]+)_(.+)$", pid or "", re.I)
    if not m:
        return "", "", ""
    rest = m.group(2)
    # locale is first segment like en-us
    parts = rest.split("_")
    if not parts:
        return "", "", ""
    locale = parts[0]
    after = parts[1:]
    if not after:
        return locale, "", ""
    # country-wide: empty city then country, or Other_Country
    if after[0] == "" or (len(after) >= 2 and after[0] == ""):
        # __Country -> ['', 'Country'] when split on _
        country = after[-1] if after else ""
        return locale, "", country
    if after[0] == "Other" and len(after) >= 2:
        return locale, "", after[-1]
    if len(after) == 1:
        return locale, "", after[0]
    # City_Country (city may contain spaces encoded as single token)
    return locale, after[0], after[-1]


def careers_url_from_parts(blt: str, locale: str, city: str, country: str) -> str:
    if not blt:
        return "https://careers.epam.com/"
    loc_short = (locale or "en-us").split("-")[0] or "en"
    url = f"https://careers.epam.com/{loc_short}/vacancy/{blt}_{loc_short}"
    qs = []
    if city and city.lower() != "other":
        qs.append(f"city={urllib_quote(city)}")
    if country:
        qs.append(f"country={urllib_quote(country)}")
    if qs:
        url += "?" + "&".join(qs)
    return url


def urllib_quote(s: str) -> str:
    from urllib.parse import quote

    return quote(s, safe="")


def guess_skills(title: str, description_text: str) -> str:
    """Lightweight skill hint from title (feed has no dedicated skills field)."""
    # Prefer title tokens that look like tech / role keywords
    title = title or ""
    # Keep short readable hint
    return title.strip()[:120]


def parse_jobs(xml: str) -> list[dict]:
    jobs: list[dict] = []
    for block in re.findall(r"<job>(.*?)</job>", xml, re.S):
        pid = cdata("partnerJobId", block)
        apply_url = cdata("applyUrl", block)
        if not pid or not apply_url:
            continue
        blt = blt_of(pid) or blt_of(apply_url)
        title = cdata("title", block)
        description_html = cdata("description", block)
        description_text = strip_html(description_html)
        location = cdata("location", block)
        locale, city_pid, country_pid = parse_pid_geo(pid)
        # Prefer pid geo; fall back to location text
        country = country_pid or location.rsplit(",", 1)[-1].strip()
        city = city_pid
        if not city and "," in location:
            city = location.split(",")[0].strip()
        workplace = cdata("workplaceTypes", block)
        is_remote = "remote" in (workplace or "").lower()
        published = cdata("publishedAt", block)
        expiration = cdata("expirationDate", block)
        job = {
            "id": pid,
            "partner_job_id": pid,
            "blt": blt,
            "brand": brand_from_pid(pid),
            "title": title,
            "company": cdata("company", block) or "EPAM Systems",
            "description_html": description_html,
            "description_text": description_text,
            "skills": guess_skills(title, description_text),
            "location": location,
            "city": city,
            "country": country,
            "locale": locale or "en-us",
            "workplace_type": workplace,
            "is_remote": is_remote,
            "job_type": cdata("jobType", block) or "FULL_TIME",
            "experience_level": cdata("experienceLevel", block),
            "job_function": cdata("jobFunction", block),
            "industry": cdata("industry", block),
            "apply_url": apply_url,
            "careers_url": careers_url_from_parts(blt, locale, city, country),
            "published_at": published,
            "expiration_date": expiration,
            "date_posted_iso": parse_mmddyyyy(published),
            "valid_through_iso": parse_mmddyyyy(expiration),
            "poster_email": cdata("posterEmail", block),
        }
        jobs.append(job)
    return jobs


def resolve_feed_path(explicit: Path | None, fetch: bool, workspace_root: Path) -> tuple[Path | None, str]:
    if fetch:
        return None, FEED_URL
    if explicit:
        return explicit, str(explicit)
    for rel in WORKSPACE_FEED_CANDIDATES:
        cand = workspace_root / rel
        if cand.is_file():
            return cand, str(cand)
        # also try relative to cwd
        if rel.is_file():
            return rel, str(rel)
    return None, ""


def download_feed(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "epam-ai-native-vacancy-ingest/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    dest.write_bytes(data)
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest LinkedIn XML feed → jobs.json")
    parser.add_argument("--feed", type=Path, default=None, help="Path to feed XML")
    parser.add_argument("--fetch", action="store_true", help=f"Download live feed from {FEED_URL}")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output jobs.json path")
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=None,
        help="Workspace root for default feed discovery (default: cwd)",
    )
    args = parser.parse_args()
    workspace_root = args.workspace_root or Path.cwd()

    feed_path, source = resolve_feed_path(args.feed, args.fetch, workspace_root)
    if args.fetch:
        snap = ROOT / "data" / "feed-linkedin-live.xml"
        try:
            download_feed(FEED_URL, snap)
        except Exception as exc:
            print(f"ERROR: fetch failed ({exc}). Use --feed with a local snapshot.", file=sys.stderr)
            return 1
        feed_path = snap
        source = FEED_URL
    elif feed_path is None:
        print(
            "ERROR: no feed found. Pass --feed PATH or --fetch, or place a snapshot under "
            "projects/job-postings-okr/doc-assets/linkedin-match-work/.",
            file=sys.stderr,
        )
        return 1

    xml = feed_path.read_text(encoding="utf-8", errors="replace")
    jobs = parse_jobs(xml)
    meta = {
        "source": source,
        "feed_path": str(feed_path),
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "job_count": len(jobs),
        "slot_definition": "feed <job> with non-empty applyUrl and partnerJobId",
        "salary_note": "baseSalary not available in LinkedIn XML feed",
    }
    last_build = re.search(r"<lastBuildDate>(.*?)</lastBuildDate>", xml)
    if last_build:
        meta["feed_last_build_date"] = last_build.group(1).strip()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = {"meta": meta, "jobs": jobs}
    with args.out.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=None)
        f.write("\n")

    countries = {}
    for j in jobs:
        c = j.get("country") or "Unknown"
        countries[c] = countries.get(c, 0) + 1
    top = sorted(countries.items(), key=lambda x: -x[1])[:8]
    print(f"Wrote {len(jobs)} jobs → {args.out}")
    print(f"Source: {source}")
    print("Top countries:", ", ".join(f"{k}={v}" for k, v in top))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
