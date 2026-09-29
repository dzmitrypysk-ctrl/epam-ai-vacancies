"""Shared job store: load normalized JSON and search/filter."""

from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STORE = ROOT / "data" / "jobs.json"
DEFAULT_STORE_GZ = ROOT / "data" / "jobs.json.gz"

_WS = re.compile(r"\s+")


def project_root() -> Path:
    return ROOT


def default_store_path() -> Path:
    env_path = os.environ.get("JOBS_STORE_PATH", "").strip()
    if env_path:
        return Path(env_path)
    if DEFAULT_STORE_GZ.is_file():
        return DEFAULT_STORE_GZ
    if DEFAULT_STORE.is_file():
        return DEFAULT_STORE
    return DEFAULT_STORE_GZ


def _read_json_store(store_path: Path) -> dict[str, Any]:
    if store_path.suffix == ".gz" or store_path.name.endswith(".json.gz"):
        with gzip.open(store_path, "rt", encoding="utf-8") as f:
            return json.load(f)
    with store_path.open(encoding="utf-8") as f:
        return json.load(f)


def load_jobs(path: Path | None = None) -> dict[str, Any]:
    store_path = path or default_store_path()
    if not store_path.is_file():
        raise FileNotFoundError(
            f"Job store not found: {store_path}. "
            "Run: python _scripts/ingest_feed.py && python _scripts/build_gzip_store.py"
        )
    data = _read_json_store(store_path)
    if not isinstance(data, dict) or "jobs" not in data:
        raise ValueError(f"Invalid store format: {store_path}")
    return data


def strip_html(text: str) -> str:
    if not text:
        return ""
    t = re.sub(r"<[^>]+>", " ", text)
    t = (
        t.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
    )
    return _WS.sub(" ", t).strip()


def _haystack(job: dict[str, Any]) -> str:
    parts = [
        job.get("title") or "",
        job.get("description_text") or "",
        job.get("skills") or "",
        job.get("city") or "",
        job.get("country") or "",
        job.get("location") or "",
        job.get("job_function") or "",
        job.get("industry") or "",
        job.get("workplace_type") or "",
    ]
    return " ".join(parts).lower()


def _token_in(hay: str, token: str) -> bool:
    """Substring match with word-ish boundaries (avoids java ⊂ javascript)."""
    if not token:
        return True
    if len(token) <= 2:
        return token in hay
    return re.search(rf"(?<![a-z0-9]){re.escape(token)}(?![a-z0-9])", hay) is not None


def search_jobs(
    jobs: list[dict[str, Any]],
    *,
    q: str | None = None,
    skill: str | None = None,
    country: str | None = None,
    city: str | None = None,
    remote: bool | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    """Filter jobs. Returns (page, total_matching)."""
    limit = max(1, min(int(limit or 20), 100))
    offset = max(0, int(offset or 0))
    q_l = (q or "").strip().lower()
    skill_l = (skill or "").strip().lower()
    country_l = (country or "").strip().lower()
    city_l = (city or "").strip().lower()

    matched: list[dict[str, Any]] = []
    for job in jobs:
        if country_l:
            c = (job.get("country") or "").lower()
            loc = (job.get("location") or "").lower()
            if country_l not in c and country_l not in loc:
                continue
        if city_l:
            cj = (job.get("city") or "").lower()
            loc = (job.get("location") or "").lower()
            if city_l not in cj and city_l not in loc:
                continue
        if remote is True:
            wt = (job.get("workplace_type") or "").lower()
            if "remote" not in wt and not job.get("is_remote"):
                continue
        if remote is False:
            wt = (job.get("workplace_type") or "").lower()
            if "remote" in wt or job.get("is_remote"):
                continue
        if skill_l:
            hay = _haystack(job)
            if not _token_in(hay, skill_l):
                continue
        if q_l:
            tokens = [t for t in re.split(r"[\s,/]+", q_l) if t]
            hay = _haystack(job)
            if not all(_token_in(hay, tok) for tok in tokens):
                continue
        matched.append(job)

    page = matched[offset : offset + limit]
    return page, len(matched)


def get_job_by_id(jobs: list[dict[str, Any]], job_id: str) -> dict[str, Any] | None:
    jid = (job_id or "").strip()
    if not jid:
        return None
    jid_l = jid.lower()
    for job in jobs:
        if job.get("id") == jid or job.get("partner_job_id") == jid:
            return job
        if (job.get("blt") or "").lower() == jid_l:
            return job
    return None


def list_countries(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for job in jobs:
        c = (job.get("country") or "").strip() or "Unknown"
        counts[c] = counts.get(c, 0) + 1
    return [
        {"country": k, "count": counts[k]}
        for k in sorted(counts.keys(), key=lambda x: (-counts[x], x))
    ]


def job_to_jsonld(job: dict[str, Any]) -> dict[str, Any]:
    """Build schema.org JobPosting JSON-LD (AI / Google for Jobs friendly)."""
    is_remote = bool(job.get("is_remote")) or "remote" in (
        job.get("workplace_type") or ""
    ).lower()
    employment = job.get("job_type") or "FULL_TIME"
    # Map LinkedIn-style enums to schema.org
    emp_map = {
        "FULL_TIME": "FULL_TIME",
        "PART_TIME": "PART_TIME",
        "CONTRACT": "CONTRACTOR",
        "CONTRACTOR": "CONTRACTOR",
        "TEMPORARY": "TEMPORARY",
        "INTERN": "INTERN",
    }
    employment_type = emp_map.get(employment.upper().replace(" ", "_"), employment)

    posting: dict[str, Any] = {
        "@context": "https://schema.org/",
        "@type": "JobPosting",
        "title": job.get("title") or "",
        "description": job.get("description_html")
        or job.get("description_text")
        or "",
        "datePosted": job.get("date_posted_iso") or job.get("published_at") or "",
        "validThrough": job.get("valid_through_iso") or job.get("expiration_date") or "",
        "employmentType": employment_type,
        "hiringOrganization": {
            "@type": "Organization",
            "name": job.get("company") or "EPAM Systems",
            "sameAs": "https://www.epam.com/",
            "logo": "https://careers.epam.com/static/assets/logo/EPAM_Systems.svg",
        },
        "identifier": {
            "@type": "PropertyValue",
            "name": "EPAM Systems",
            "value": job.get("blt") or job.get("id") or "",
        },
        "url": job.get("careers_url") or job.get("apply_url") or "",
        "directApply": True,
        "industry": job.get("industry") or "Information Technology and Services",
    }
    if job.get("skills"):
        posting["skills"] = job["skills"]

    # Salary intentionally omitted — not in feed (see stakeholder note).
    posting["baseSalary"] = {
        "@type": "MonetaryAmount",
        "currency": "USD",
        "value": {
            "@type": "QuantitativeValue",
            "value": None,
            "unitText": "YEAR",
            "description": "Salary not published in source feed; placeholder for AI agents",
        },
    }

    country = (job.get("country") or "").strip()
    city = (job.get("city") or "").strip()
    if is_remote:
        posting["jobLocationType"] = "TELECOMMUTE"
        if country:
            posting["applicantLocationRequirements"] = {
                "@type": "Country",
                "name": country,
            }
    else:
        address: dict[str, Any] = {
            "@type": "PostalAddress",
            "addressCountry": country or "Unknown",
        }
        if city:
            address["addressLocality"] = city
        posting["jobLocation"] = {
            "@type": "Place",
            "address": address,
        }

    return posting


def summary_card(job: dict[str, Any]) -> dict[str, Any]:
    """Compact card for search results."""
    return {
        "id": job.get("id"),
        "blt": job.get("blt"),
        "title": job.get("title"),
        "country": job.get("country"),
        "city": job.get("city"),
        "workplace_type": job.get("workplace_type"),
        "is_remote": job.get("is_remote"),
        "job_type": job.get("job_type"),
        "experience_level": job.get("experience_level"),
        "skills": job.get("skills"),
        "careers_url": job.get("careers_url"),
        "apply_url": job.get("apply_url"),
        "date_posted_iso": job.get("date_posted_iso"),
        "snippet": (job.get("description_text") or "")[:280],
    }
