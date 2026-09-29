# Deploy runbook — free Render.com + analytics

**Prototype:** not official EPAM infrastructure. Public careers feed snapshot.

## Prerequisites

1. GitHub repo with this project (Render deploys from Git).
2. [`data/jobs.json.gz`](data/jobs.json.gz) committed (build locally — see below).
3. Optional: [Cloudflare Web Analytics](https://developers.cloudflare.com/web-analytics/) token (free).

## 1. Build deploy bundle (local)

On EPAM network (for live feed):

```bash
cd projects/ai-native-vacancy-service
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python _scripts/ingest_feed.py --fetch
.venv/bin/python _scripts/build_gzip_store.py
```

Or from existing snapshot:

```bash
.venv/bin/python _scripts/build_gzip_store.py
```

Commit `data/jobs.json.gz` (raw `jobs.json` stays gitignored).

## 2. Create Render Web Service

1. [render.com](https://render.com) → **New** → **Web Service** → connect GitHub repo.
2. **Root directory:** `projects/ai-native-vacancy-service`
3. **Runtime:** Python 3 (or use Blueprint from [`render.yaml`](render.yaml)).
4. **Build:** `pip install -r requirements.txt`
5. **Start:** `uvicorn service.app:app --host 0.0.0.0 --port $PORT`
6. **Plan:** Free

### Environment variables

| Variable | Required | Example |
|----------|----------|---------|
| `PUBLIC_BASE_URL` | Yes (for /test links) | `https://epam-ai-vacancies.onrender.com` |
| `STATS_TOKEN` | Recommended | random string — protects `/stats` |
| `CF_ANALYTICS_TOKEN` | Optional | from Cloudflare Web Analytics |
| `HOST` | Auto | `0.0.0.0` |

After first deploy, set `PUBLIC_BASE_URL` to the Render URL and redeploy (or update once in dashboard).

## 3. Smoke test (public URL)

```bash
.venv/bin/python _scripts/smoke_demo.py --base https://YOUR-APP.onrender.com
```

Manual:

- `https://YOUR-APP.onrender.com/test` — test guide
- `https://YOUR-APP.onrender.com/stats?token=YOUR_STATS_TOKEN` — analytics
- `https://YOUR-APP.onrender.com/llms.txt` — agent index

## 4. How to test AI discovery

| Step | Action | Check in `/stats` |
|------|--------|-------------------|
| 1 | Open `/test`, click smoke links | `browser` + hits on `/jobs`, `/llms.txt` |
| 2 | Run curl block from `/test` | `curl` or `smoke` client class |
| 3 | `curl -A GPTBot …/llms.txt` | `gptbot` |
| 4 | Ask Perplexity with your `/llms.txt` URL | `perplexitybot` or browser |
| 5 | ChatGPT Custom GPT → import `/openapi.json` | API calls to `/jobs` |

**Page views** on `/test` (human visits): Cloudflare Web Analytics dashboard (if token set).

**API/bot traffic:** in-memory `/stats` (resets on redeploy).

## 5. Refresh vacancy data

1. Local ingest (EPAM VPN): `ingest_feed.py --fetch`
2. `build_gzip_store.py`
3. `git add data/jobs.json.gz && git push`
4. Render auto-redeploys (or Manual Deploy)

## Free tier limits

- **Sleep:** ~15 min idle → cold start ~30–60 s on first request.
- **RAM:** 512 MB — full gzip store (~50 MB raw) loads into memory; if OOM, contact owner to trim snapshot.
- **Analytics:** ring buffer 2000 events — not persistent across redeploys.

## Docker (optional)

```bash
docker build -t epam-ai-vacancies projects/ai-native-vacancy-service
docker run -p 8977:8977 -e PUBLIC_BASE_URL=http://localhost:8977 epam-ai-vacancies
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `/health` ok=false, store missing | Ensure `data/jobs.json.gz` in repo and deployed |
| `/stats` 403 | Add `?token=` matching `STATS_TOKEN` |
| Slow first request | Free tier waking from sleep — normal |
| Feed fetch fails locally | Use `--feed` with local XML snapshot |
