"""Unit tests for independent GEO vacancy surface."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from service.store import (  # noqa: E402
    get_job_by_id,
    job_to_jsonld,
    vacancy_path,
    vacancy_slug,
)

# ingest_feed is a script module (not a package)
import importlib.util

_ingest_path = ROOT / "_scripts" / "ingest_feed.py"
_spec = importlib.util.spec_from_file_location("ingest_feed", _ingest_path)
_ingest = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_ingest)
compute_lifecycle = _ingest.compute_lifecycle


SAMPLE_JOBS = [
    {
        "id": "epamgdo_bltabc123_en-us_Krakow_Poland",
        "partner_job_id": "epamgdo_bltabc123_en-us_Krakow_Poland",
        "blt": "bltabc123",
        "title": "Senior Java Engineer",
        "company": "EPAM Systems",
        "description_html": "<p>Build Java services.</p>",
        "description_text": "Build Java services.",
        "skills": "Senior Java Engineer",
        "location": "Krakow, Poland",
        "city": "Krakow",
        "country": "Poland",
        "locale": "en-us",
        "workplace_type": "Remote",
        "is_remote": True,
        "job_type": "FULL_TIME",
        "experience_level": "MID_SENIOR_LEVEL",
        "job_function": "",
        "industry": "Information Technology and Services",
        "apply_url": "https://careers.epam.com/en/vacancy/bltabc123_en?country=Poland",
        "careers_url": "https://careers.epam.com/en/vacancy/bltabc123_en?country=Poland",
        "published_at": "09/28/2026",
        "expiration_date": "12/31/2026",
        "date_posted_iso": "2026-09-28",
        "valid_through_iso": "2026-12-31",
    },
    {
        "id": "anywhere_bltdef456_en-us__India",
        "partner_job_id": "anywhere_bltdef456_en-us__India",
        "blt": "bltdef456",
        "title": "Python Developer",
        "company": "EPAM Systems",
        "description_html": "<p>Python role.</p>",
        "description_text": "Python role.",
        "skills": "Python Developer",
        "location": "India",
        "city": "",
        "country": "India",
        "locale": "en-us",
        "workplace_type": "On-site",
        "is_remote": False,
        "job_type": "FULL_TIME",
        "experience_level": "ASSOCIATE",
        "job_function": "",
        "industry": "Information Technology and Services",
        "apply_url": "https://careers.epam.com/en/vacancy/bltdef456_en?country=India",
        "careers_url": "https://careers.epam.com/en/vacancy/bltdef456_en?country=India",
        "published_at": "09/29/2026",
        "expiration_date": "12/31/2026",
        "date_posted_iso": "2026-09-29",
        "valid_through_iso": "2026-12-31",
    },
]


@pytest.fixture()
def client(tmp_path, monkeypatch):
    store = {
        "meta": {
            "job_count": 2,
            "ingested_at": "2026-10-15T12:00:00+00:00",
            "feed_last_build_date": "Wed, 15 Oct 2026 12:00:00 GMT",
        },
        "jobs": SAMPLE_JOBS,
    }
    jobs_path = tmp_path / "jobs.json"
    removed_path = tmp_path / "removed_ids.json"
    jobs_path.write_text(json.dumps(store), encoding="utf-8")
    removed_path.write_text(
        json.dumps({"ids": ["bltgone999"], "removed_at": {"bltgone999": "2026-10-14T00:00:00+00:00"}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("JOBS_STORE_PATH", str(jobs_path))
    monkeypatch.setenv("REMOVED_IDS_PATH", str(removed_path))
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://epam-ai-vacancies.onrender.com")

    # Fresh import / reload caches
    import service.app as app_mod

    app_mod._CACHE = None
    app_mod._REMOVED_CACHE = None
    app_mod.STORE_PATH = jobs_path
    return TestClient(app_mod.app)


def test_slug_and_jsonld_canonical():
    job = SAMPLE_JOBS[0]
    slug = vacancy_slug(job)
    assert "bltabc123" in slug
    assert vacancy_path(job).startswith("/vacancies/")
    ld = job_to_jsonld(job, base="https://example.com")
    assert ld["@type"] == "JobPosting"
    assert ld["url"].startswith("https://example.com/vacancies/")
    assert "careers.epam.com" not in ld["url"]
    assert "baseSalary" not in ld
    assert ld.get("directApply") is True
    assert ld["validThrough"].endswith("Z")


def test_get_job_by_slug():
    job = get_job_by_id(SAMPLE_JOBS, vacancy_slug(SAMPLE_JOBS[0]))
    assert job is not None
    assert job["blt"] == "bltabc123"
    assert get_job_by_id(SAMPLE_JOBS, "bltabc123")["title"].startswith("Senior Java")


def test_lifecycle_diff():
    previous = SAMPLE_JOBS
    current = [SAMPLE_JOBS[0]]  # India role removed
    current = [
        {
            **SAMPLE_JOBS[0],
            "title": "Lead Java Engineer",  # updated
        },
        {
            **SAMPLE_JOBS[1],
            "id": "new_bltzzz001_en-us__Mexico",
            "partner_job_id": "new_bltzzz001_en-us__Mexico",
            "blt": "bltzzz001",
            "title": "New Role",
            "country": "Mexico",
        },
    ]
    # previous had bltdef456; current replaced India with Mexico new id → removed India, added Mexico, updated Java
    life = compute_lifecycle(previous, current)
    assert "bltzzz001" in life["added"]
    assert "bltdef456" in life["removed"]
    assert "bltabc123" in life["updated"]


def test_html_home_and_detail(client):
    r = client.get("/", headers={"Accept": "text/html"})
    assert r.status_code == 200
    assert "vacancy index" in r.text.lower()
    assert 'rel="canonical"' in r.text

    slug = vacancy_slug(SAMPLE_JOBS[0])
    r2 = client.get(f"/vacancies/{slug}")
    assert r2.status_code == 200
    assert "Senior Java Engineer" in r2.text
    assert "application/ld+json" in r2.text
    assert "JobPosting" in r2.text
    assert "https://epam-ai-vacancies.onrender.com/vacancies/" in r2.text
    assert "Apply on careers.epam.com" in r2.text


def test_catalog_and_hub(client):
    r = client.get("/vacancies?country=Poland")
    assert r.status_code == 200
    assert "Senior Java Engineer" in r.text
    r2 = client.get("/vacancies?remote=true")
    assert r2.status_code == 200


def test_sitemap_and_robots(client):
    r = client.get("/sitemap.xml")
    assert r.status_code == 200
    assert "<urlset" in r.text
    assert "/vacancies/" in r.text
    assert "bltabc123" in r.text

    robots = client.get("/robots.txt")
    assert robots.status_code == 200
    assert "OAI-SearchBot" in robots.text
    assert "Sitemap:" in robots.text
    assert "PerplexityBot" in robots.text


def test_llms_points_to_html(client):
    r = client.get("/llms.txt")
    assert r.status_code == 200
    assert "/vacancies" in r.text
    assert "/sitemap.xml" in r.text
    assert "Canonical JobPosting" in r.text


def test_removed_returns_410(client):
    r = client.get("/vacancies/bltgone999")
    assert r.status_code == 410
    r2 = client.get("/jobs/bltgone999")
    assert r2.status_code == 410


def test_head_vacancy_ok(client):
    slug = vacancy_slug(SAMPLE_JOBS[0])
    r = client.head(f"/vacancies/{slug}")
    assert r.status_code == 200


def test_crawler_classification():
    from service.analytics import classify_client

    assert classify_client("Mozilla/5.0 compatible; OAI-SearchBot/1.0") == "oai-searchbot"
    assert classify_client("Mozilla/5.0 compatible; bingbot/2.0") == "bingbot"
    assert classify_client("Mozilla/5.0 compatible; Perplexity-User/1.0") == "perplexity-user"
    assert classify_client("Mozilla/5.0 compatible; Claude-SearchBot/1.0") == "claude-searchbot"
