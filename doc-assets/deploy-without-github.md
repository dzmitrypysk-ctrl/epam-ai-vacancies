# Public URL without GitHub (codemie-local / Cursor app)

Cursor GitHub App fails on `codemie-local/workspace-root`. Use one of these instead.

## Option A — Instant test (Cloudflare tunnel, ~2 min)

**Requires:** laptop on + API running.

```bash
cd projects/ai-native-vacancy-service
.venv/bin/uvicorn service.app:app --host 127.0.0.1 --port 8977   # terminal 1
./_scripts/start_public_tunnel.sh                                 # terminal 2
```

Copy the `https://….trycloudflare.com` URL. Then open:

- `{URL}/test` — test guide
- `{URL}/stats` — analytics
- `{URL}/llms.txt` — for Perplexity / ChatGPT

**Current session (2026-09-02):** tunnel must be restarted to get a fresh URL.

## Option B — Persistent free (Render + personal GitHub)

1. Fork/copy `projects/ai-native-vacancy-service` to **your personal** GitHub repo (not codemie-local).
2. [render.com](https://render.com) → Sign in with **personal** GitHub → New Web Service.
3. Root dir: `projects/ai-native-vacancy-service` (or repo root if standalone).
4. Env: `PUBLIC_BASE_URL`, optional `STATS_TOKEN`, `CF_ANALYTICS_TOKEN`.
5. See [deploy-runbook.md](deploy-runbook.md).

## Option C — Hugging Face Spaces (Docker, free)

See [_scripts/deploy_huggingface_instructions.md](../_scripts/deploy_huggingface_instructions.md).

HF login from automation may be blocked (CloudFront); use your browser manually.
