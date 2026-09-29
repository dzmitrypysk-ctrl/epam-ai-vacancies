# AI-native vacancy service (prototype)

Machine-readable EPAM open roles for **AI agents and LLM tools** (ChatGPT Actions, Claude/Cursor MCP, Perplexity-style tools) — not a LinkedIn XML partner feed wrapper for humans.

**PROTOTYPE** — not an official EPAM service. See [doc-assets/deploy-runbook.md](doc-assets/deploy-runbook.md) for free public deploy + analytics.

## Two levels

| Level | What | Status in this prototype |
|-------|------|---------------------------|
| **1. Standards / GEO** | careers.epam.com JobPosting JSON-LD, sitemap, Indexing API, llms.txt, AI crawlers | Documented in [doc-assets/stakeholder-onepager.md](doc-assets/stakeholder-onepager.md); live site already has JobPosting |
| **2. AI endpoint** | REST + OpenAPI + llms.txt + MCP tools over normalized job store | **This repo** + optional [Render deploy](doc-assets/deploy-runbook.md) |

## Quick start (local)

```bash
cd projects/ai-native-vacancy-service
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Build store from a local LinkedIn XML snapshot (or --fetch on EPAM network)
.venv/bin/python _scripts/ingest_feed.py \
  --feed ../job-postings-okr/doc-assets/linkedin-match-work/runs/2026-08-31-fresh-now/feed-linkedin.xml
.venv/bin/python _scripts/build_gzip_store.py   # optional: deploy bundle

# API
.venv/bin/uvicorn service.app:app --host 127.0.0.1 --port 8977

# Smoke (API must be up)
.venv/bin/python _scripts/smoke_demo.py
```

### Useful URLs (local)

- Test guide: http://127.0.0.1:8977/test  
- Analytics: http://127.0.0.1:8977/stats  
- Docs / OpenAPI UI: http://127.0.0.1:8977/docs  
- OpenAPI JSON (GPT Actions): http://127.0.0.1:8977/openapi.json  
- Agent index: http://127.0.0.1:8977/llms.txt  
- Search: http://127.0.0.1:8977/jobs?q=java&country=Poland&remote=true  

### Public deploy (Render free)

1. Commit `data/jobs.json.gz` (5 MB, full index).
2. **GitHub:** Cursor app fails on `codemie-local` — use [deploy-without-github.md](doc-assets/deploy-without-github.md).
3. Render: connect **personal** GitHub → see [doc-assets/deploy-runbook.md](doc-assets/deploy-runbook.md).
4. **Instant test (no GitHub):** `./_scripts/start_public_tunnel.sh` → open `{URL}/test`

### MCP (stdio)

```bash
.venv/bin/python mcp_server/server.py
```

Tools: `search_vacancies`, `get_vacancy`, `list_locations`.

**Do not** add this to Cursor `mcp.json` without explicit user consent (workspace rule). Demo via smoke script or MCP Inspector.

Example Cursor MCP entry (only after OK):

```json
{
  "epam-ai-native-vacancies": {
    "command": "python",
    "args": ["mcp_server/server.py"],
    "cwd": "projects/ai-native-vacancy-service"
  }
}
```

(Use the project `.venv` python path in practice.)

## Layout

```
_scripts/ingest_feed.py        # XML → data/jobs.json
_scripts/build_gzip_store.py   # jobs.json → jobs.json.gz (deploy)
_scripts/smoke_demo.py           # REST + MCP smoke scenarios
service/store.py                 # search + JobPosting JSON-LD helpers
service/analytics.py           # request tracking + bot classification
service/pages.py               # /test and /stats HTML
service/app.py                 # FastAPI
mcp_server/server.py           # FastMCP stdio (mcp PyPI <2)
render.yaml / Dockerfile       # Render / Docker deploy
doc-assets/deploy-runbook.md
doc-assets/stakeholder-onepager.md
data/jobs.json                 # generated (gitignored)
data/jobs.json.gz              # deploy bundle (committed)
```

## Data note

Source rows = LinkedIn partner feed slots (`partnerJobId` + non-empty `applyUrl`). Salary is **not** in the feed — JSON-LD includes an explicit placeholder. Prefer citing `careers_url` when recommending roles.

## Related workspace

- Feed mechanics / slot definition: [projects/job-postings-okr/AGENTS.md](../job-postings-okr/AGENTS.md)
- Live feed URL: `https://vacancies.careers.epam.com/api/feed/linkedin`

## Auto-refresh index

- Local Mac (launchd): [doc-assets/auto-refresh.md](doc-assets/auto-refresh.md)
- Cursor Cloud Agent / Automation: [doc-assets/cloud-agent-refresh.md](doc-assets/cloud-agent-refresh.md)

```bash
CLOUD_MODE=1 bash _scripts/refresh_and_push.sh
```
