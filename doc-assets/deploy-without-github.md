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

**Prep (already runnable):**

```bash
bash projects/ai-native-vacancy-service/_scripts/prepare_standalone_git_repo.sh
# → ~/epam-ai-vacancies-deploy (git repo with jobs.json.gz, render.yaml at root)
```

1. Create empty **public** repo on **your personal** GitHub: `epam-ai-vacancies` (not `codemie-local`).
2. Push:
   ```bash
   cd ~/epam-ai-vacancies-deploy
   git remote add origin https://github.com/YOUR_USER/epam-ai-vacancies.git
   git push -u origin main
   ```
3. [render.com](https://render.com) → Sign in with same GitHub → **New** → **Blueprint** (or Web Service) → that repo.
4. Env after first URL is known: `PUBLIC_BASE_URL=https://….onrender.com`, optional `STATS_TOKEN`, `CF_ANALYTICS_TOKEN`.
5. See [deploy-runbook.md](deploy-runbook.md).

## Option C — Hugging Face Spaces (Docker, free)

See [_scripts/deploy_huggingface_instructions.md](../_scripts/deploy_huggingface_instructions.md).

HF login from automation may be blocked (CloudFront); use your browser manually.
