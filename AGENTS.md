# AGENTS.md — ai-native-vacancy-service

## Purpose

Prototype **independent GEO + AI-native vacancy service**: crawlable HTML JobPosting pages on this host, plus REST/MCP for agents. careers.epam.com is apply destination only.

## Do

- Prefer repo-relative paths; run from `projects/ai-native-vacancy-service` with local `.venv`.
- Regenerate `data/jobs.json` via `_scripts/ingest_feed.py` before demos if feed is stale.
- Keep MCP package pin `mcp>=1.2.0,<2` (FastMCP API) unless migrating to mcp 2.x `MCPServer`.
- Never edit workspace/`mcp.json` without explicit user consent.
- Canonical JobPosting `url` = this host `/vacancies/{slug}`; never invent `baseSalary`.
- External index submission (GSC/Bing/IndexNow) only after explicit user approval — see `doc-assets/index-submission-runbook.md`.

## Do not

- Treat LinkedIn XML as the public AI SEO surface.
- Depend on careers.epam.com for discovery of this prototype.
- Commit `data/jobs.json` (large; gitignored) or secrets.
- Register production MCP keys without owner approval.

## Smoke

```bash
PUBLIC_BASE_URL=http://127.0.0.1:8977 \
  .venv/bin/uvicorn service.app:app --host 127.0.0.1 --port 8977
.venv/bin/python _scripts/smoke_demo.py
.venv/bin/python -m pytest tests/ -q
```

## Public deploy

See [doc-assets/deploy-runbook.md](doc-assets/deploy-runbook.md) — Render free tier, `data/jobs.json.gz`, HTML `/vacancies`, `/sitemap.xml`, `/test` + `/stats`.

## Auto-refresh (Mac launchd)

Weekday 09:00 local via ASCII-path wrapper (avoids Cyrillic path exit 126). EPAM network required for `--fetch`.

```bash
./_scripts/install_launchd_refresh.sh
```

Details: [doc-assets/auto-refresh.md](doc-assets/auto-refresh.md).
