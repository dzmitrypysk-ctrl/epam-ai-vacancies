"""FastAPI AI-native vacancy service.

Run from project root:
  uvicorn service.app:app --host 127.0.0.1 --port 8977

Production (Render):
  uvicorn service.app:app --host 0.0.0.0 --port $PORT
"""

from __future__ import annotations

import os
import time
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from service.analytics import (
    RequestEvent,
    STORE as analytics_store,
    classify_client,
    stats_token_ok,
    _extract_search_params,
)
from service.pages import stats_page, test_page
from service.store import (
    default_store_path,
    get_job_by_id,
    job_to_jsonld,
    list_countries,
    load_jobs,
    project_root,
    search_jobs,
    summary_card,
)

STORE_PATH = default_store_path()
_CACHE: dict[str, Any] | None = None

app = FastAPI(
    title="EPAM AI-Native Vacancy Service",
    description=(
        "Prototype machine-readable EPAM job inventory for AI agents "
        "(ChatGPT Actions, Claude, Perplexity tools, MCP). "
        "Source: LinkedIn XML partner feed normalized to JobPosting-friendly JSON."
    ),
    version="0.2.0",
    contact={"name": "EPAM TA / Job Postings (prototype)"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def analytics_middleware(request: Request, call_next):
    path = request.url.path
    if path in ("/health", "/favicon.ico"):
        return await call_next(request)

    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000

    ua = request.headers.get("user-agent", "")
    query = request.url.query or ""
    analytics_store.record(
        RequestEvent(
            ts=time.time(),
            path=path,
            method=request.method,
            query=query,
            user_agent=ua,
            referer=request.headers.get("referer", ""),
            client_class=classify_client(ua),
            status_code=response.status_code,
            duration_ms=duration_ms,
            search_params=_extract_search_params(query) if path == "/jobs" else {},
        )
    )
    return response


def _store() -> dict[str, Any]:
    global _CACHE
    if _CACHE is None:
        _CACHE = load_jobs(STORE_PATH)
    return _CACHE


def reload_store() -> dict[str, Any]:
    global _CACHE
    _CACHE = load_jobs(STORE_PATH)
    return _CACHE


@app.get("/health")
def health() -> dict[str, Any]:
    try:
        data = _store()
        return {
            "ok": True,
            "job_count": data["meta"].get("job_count"),
            "ingested_at": data["meta"].get("ingested_at"),
            "store": str(STORE_PATH),
        }
    except FileNotFoundError as exc:
        return {"ok": False, "error": str(exc)}


@app.post("/admin/reload")
def admin_reload() -> dict[str, Any]:
    data = reload_store()
    return {"ok": True, "job_count": data["meta"].get("job_count")}


@app.get("/meta")
def meta() -> dict[str, Any]:
    return _store()["meta"]


@app.get("/jobs")
def list_jobs(
    q: Optional[str] = Query(None, description="Free-text query (all tokens must match)"),
    skill: Optional[str] = Query(None, description="Skill / keyword substring"),
    country: Optional[str] = Query(None, description="Country filter, e.g. Poland"),
    city: Optional[str] = Query(None, description="City filter, e.g. Krakow"),
    remote: Optional[bool] = Query(None, description="true = remote only; false = exclude remote"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    data = _store()
    page, total = search_jobs(
        data["jobs"],
        q=q,
        skill=skill,
        country=country,
        city=city,
        remote=remote,
        limit=limit,
        offset=offset,
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": [summary_card(j) for j in page],
    }


@app.get("/jobs/{job_id}")
def get_job(
    job_id: str,
    format: str = Query("json", pattern="^(json|jsonld|both)$"),
) -> Any:
    data = _store()
    job = get_job_by_id(data["jobs"], job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    if format == "jsonld":
        return JSONResponse(job_to_jsonld(job))
    if format == "both":
        return {"job": job, "jsonld": job_to_jsonld(job)}
    return job


@app.get("/locations")
def locations() -> dict[str, Any]:
    data = _store()
    return {"countries": list_countries(data["jobs"])}


@app.get("/llms.txt", response_class=PlainTextResponse)
def llms_txt() -> str:
    data = _store()
    meta = data["meta"]
    base = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")
    base_note = f"Public base URL: {base}\n" if base else ""
    lines = [
        "# EPAM Systems — AI-native vacancy index",
        "",
        "> Machine-readable open roles for AI agents and LLM tools.",
        "> PROTOTYPE — not an official EPAM service.",
        "",
        f"Jobs in index: {meta.get('job_count')}",
        f"Last ingest (UTC): {meta.get('ingested_at')}",
        f"Feed lastBuildDate: {meta.get('feed_last_build_date', 'n/a')}",
        base_note.rstrip(),
        "",
        "## How to discover jobs",
        "",
        "- Search API: GET /jobs?q=java&country=Poland&remote=true&limit=10",
        "- Job detail: GET /jobs/{partnerJobId} or GET /jobs/{blt}",
        "- JobPosting JSON-LD: GET /jobs/{id}?format=jsonld",
        "- Countries: GET /locations",
        "- OpenAPI: GET /openapi.json",
        "- Test guide: GET /test",
        "",
        "## Human career site",
        "",
        "- https://careers.epam.com/",
        "- Individual vacancy URLs use pattern: https://careers.epam.com/en/vacancy/{blt}_en",
        "",
        "## Notes for agents",
        "",
        "- Prefer this API or careers.epam.com JobPosting pages; do not rely on LinkedIn partner XML.",
        "- Salary is not published in the source feed (baseSalary placeholder only).",
        "- Cite careers_url when recommending a role to a candidate.",
        "",
        "## Optional full index",
        "",
        "- See /llms-full.txt for a compact title+country sample (first 200 jobs).",
        "",
    ]
    return "\n".join(line for line in lines if line is not None)


@app.get("/llms-full.txt", response_class=PlainTextResponse)
def llms_full_txt() -> str:
    data = _store()
    lines = [
        "# EPAM open roles (sample)",
        f"# total={data['meta'].get('job_count')} showing up to 200",
        "",
    ]
    for job in data["jobs"][:200]:
        title = job.get("title") or ""
        country = job.get("country") or ""
        city = job.get("city") or ""
        remote = "remote" if job.get("is_remote") else (job.get("workplace_type") or "")
        url = job.get("careers_url") or ""
        loc = ", ".join(p for p in [city, country] if p)
        lines.append(f"- {title} | {loc} | {remote} | {url}")
    return "\n".join(lines) + "\n"


@app.get("/test", response_class=HTMLResponse)
def test_guide() -> str:
    try:
        meta = _store().get("meta", {})
    except FileNotFoundError:
        meta = {}
    return test_page(meta)


@app.get("/stats", response_class=HTMLResponse)
def stats_html(token: Optional[str] = Query(None)) -> str:
    if not stats_token_ok(token):
        raise HTTPException(status_code=403, detail="Invalid or missing stats token")
    return stats_page(analytics_store.summary(), token_query=token or "")


@app.get("/stats.json")
def stats_json(token: Optional[str] = Query(None)) -> dict[str, Any]:
    if not stats_token_ok(token):
        raise HTTPException(status_code=403, detail="Invalid or missing stats token")
    return analytics_store.summary()


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt() -> str:
    return "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "Allow: /llms.txt",
            "Allow: /jobs",
            "Allow: /openapi.json",
            "Disallow: /stats",
            "Disallow: /admin/",
            "",
        ]
    )


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "service": "EPAM AI-Native Vacancy Service",
        "prototype": True,
        "docs": "/docs",
        "openapi": "/openapi.json",
        "llms": "/llms.txt",
        "test_guide": "/test",
        "stats": "/stats",
        "jobs": "/jobs",
        "health": "/health",
    }


def main() -> None:
    import uvicorn

    port = int(os.environ.get("PORT", "8977"))
    host = os.environ.get("HOST", "127.0.0.1")
    uvicorn.run(
        "service.app:app",
        host=host,
        port=port,
        reload=False,
        app_dir=str(project_root()),
    )


if __name__ == "__main__":
    main()
