# AI-native vacancy service (prototype)

Independent **GEO + AI-agent** vacancy index for EPAM open roles: crawlable HTML pages with JobPosting JSON-LD, plus REST / OpenAPI / MCP for tools (ChatGPT Actions, Claude, Cursor).

**PROTOTYPE** — not an official EPAM service. Canonical vacancy URLs live on **this host**; apply CTAs go to careers.epam.com. See [doc-assets/deploy-runbook.md](doc-assets/deploy-runbook.md) and [doc-assets/index-submission-runbook.md](doc-assets/index-submission-runbook.md).

## What this is

| Surface | Purpose |
|---------|---------|
| **HTML GEO** | `/`, `/vacancies`, `/vacancies/{slug}` — indexable pages for Google/Bing/AI search |
| **Discovery files** | `/sitemap.xml`, `/robots.txt`, `/llms.txt` |
| **API** | `/jobs`, `/openapi.json`, MCP tools for agents |

Careers.epam.com is the **apply destination**, not a dependency for discovery of this prototype.

## Quick start (local)

```bash
cd projects/ai-native-vacancy-service
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Build store from a local LinkedIn XML snapshot (or --fetch on EPAM network)
.venv/bin/python _scripts/ingest_feed.py \
  --feed ../job-postings-okr/doc-assets/linkedin-match-work/runs/2026-08-31-fresh-now/feed-linkedin.xml
.venv/bin/python _scripts/build_gzip_store.py   # optional: deploy bundle

# API + HTML
PUBLIC_BASE_URL=http://127.0.0.1:8977 \
  .venv/bin/uvicorn service.app:app --host 127.0.0.1 --port 8977

# Smoke (API must be up)
.venv/bin/python _scripts/smoke_demo.py

# Unit tests
.venv/bin/python -m pytest tests/ -q
```

### Useful URLs (local)

- Home (HTML): http://127.0.0.1:8977/  
- Catalog: http://127.0.0.1:8977/vacancies  
- Sitemap: http://127.0.0.1:8977/sitemap.xml  
- Agent index: http://127.0.0.1:8977/llms.txt  
- Test guide: http://127.0.0.1:8977/test  
- Analytics: http://127.0.0.1:8977/stats  
- Docs / OpenAPI: http://127.0.0.1:8977/docs  
- Search API: http://127.0.0.1:8977/jobs?q=java&country=Poland&remote=true  

### Public deploy (Render free)

1. Commit `data/jobs.json.gz` (+ `data/removed_ids.json` when present).
2. **GitHub:** use [deploy-without-github.md](doc-assets/deploy-without-github.md) if needed.
3. Render: connect **personal** GitHub → [doc-assets/deploy-runbook.md](doc-assets/deploy-runbook.md).
4. Set `PUBLIC_BASE_URL` to the public host.
5. Index submission (GSC/Bing/IndexNow) only after explicit approval — [index-submission-runbook.md](doc-assets/index-submission-runbook.md).

Live prototype: https://epam-ai-vacancies.onrender.com/

### MCP (stdio)

```bash
.venv/bin/python mcp_server/server.py
```

Tools: `search_vacancies`, `get_vacancy`, `list_locations`.

**Do not** add this to Cursor `mcp.json` without explicit user consent.

## Layout

```
_scripts/ingest_feed.py          # XML → jobs.json + lifecycle diff + removed_ids
_scripts/build_gzip_store.py     # jobs.json → jobs.json.gz
_scripts/notify_indexnow.py      # optional IndexNow (INDEXNOW_KEY)
_scripts/smoke_demo.py           # REST + HTML + MCP smoke
_scripts/refresh_and_push.sh     # weekday refresh → deploy repo
_scripts/install_launchd_refresh.sh  # ASCII-path launchd wrapper
service/store.py                 # search + JobPosting JSON-LD + slugs
service/geo_pages.py             # SSR HTML catalog/detail
service/analytics.py             # bot classes + crawler stdout log
service/pages.py                 # /test and /stats HTML
service/app.py                   # FastAPI
tests/test_geo_surface.py
doc-assets/index-submission-runbook.md
data/jobs.json.gz                # deploy bundle
data/removed_ids.json            # closed roles → HTTP 410
data/lifecycle-latest.json       # added/updated/removed diff
```

## Data note

Source rows = LinkedIn partner feed slots (`partnerJobId` + non-empty `applyUrl`). Salary is **not** in the feed — JSON-LD **omits** `baseSalary` (no null placeholders). Prefer citing this host’s vacancy URL for discovery; send applicants to `careers_url` / `apply_url`.

## Related workspace

- Feed mechanics / slot definition: [projects/job-postings-okr/AGENTS.md](../job-postings-okr/AGENTS.md)
- Careers site SEO audit (separate): [projects/careers-seo-audit/](../careers-seo-audit/)
- Live feed URL: `https://vacancies.careers.epam.com/api/feed/linkedin`
