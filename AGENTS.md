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

## Cursor Cloud specific instructions

- Run from the repository root. `.venv` sits next to `requirements.txt`, `service/`, and `_scripts/`.
- The default image needs the `python3.12-venv` apt package before `python3 -m venv .venv`. Environment install: `sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3.12-venv && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.
- The committed index is `data/jobs.json.gz`. Local smoke uses that file. `data/jobs.json` stays gitignored.
- The environment start command runs `.venv/bin/uvicorn service.app:app --host 0.0.0.0 --port 8977` and leaves it attached on port 8977. If the API is down, run that same command.
- End-to-end check: `.venv/bin/python _scripts/smoke_demo.py` (REST on 127.0.0.1:8977 plus in-process MCP). This repo has no separate lint or unit-test suite.
- Keep the MCP pin `mcp>=1.2.0,<2`. Leave workspace `mcp.json` unchanged.
