# AGENTS.md — ai-native-vacancy-service

## Purpose

Prototype **AI-native vacancy service**: normalize EPAM job inventory for LLM/agent discovery (REST + MCP), plus stakeholder pitch for careers-platform / VMT ownership of production GEO.

## Do

- Prefer repo-relative paths; run from `projects/ai-native-vacancy-service` with local `.venv`.
- Regenerate `data/jobs.json` via `_scripts/ingest_feed.py` before demos if feed is stale.
- Keep MCP package pin `mcp>=1.2.0,<2` (FastMCP API) unless migrating to mcp 2.x `MCPServer`.
- Never edit workspace/`mcp.json` without explicit user consent.

## Do not

- Treat LinkedIn XML as the public AI SEO surface — careers HTML + this API are the product story.
- Commit `data/jobs.json` (large; gitignored) or secrets.
- Register production MCP keys without owner approval.

## Smoke

```bash
.venv/bin/uvicorn service.app:app --host 127.0.0.1 --port 8977
.venv/bin/python _scripts/smoke_demo.py
```

## Public deploy

See [doc-assets/deploy-runbook.md](doc-assets/deploy-runbook.md) — Render free tier, `data/jobs.json.gz`, `/test` + `/stats` analytics.
