# Cloud Agent / Cursor Automation — vacancy index refresh

**Repo:** `dzmitrypysk-ctrl/epam-ai-vacancies`  
**Schedule (intended):** weekdays 09:00 Europe/Minsk  
**Outcome:** fresh `data/jobs.json.gz` on `main` → Render redeploys if connected.

## Cloud Agent instructions (copy into Automation)

You are refreshing the EPAM AI-native vacancy index. Work only in this repository root.

1. Ensure Python venv:
   - If `.venv` missing: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
2. Run: `CLOUD_MODE=1 bash _scripts/refresh_and_push.sh`
3. If ingest fails (network / non-XML feed): **do not** invent jobs; report the error and stop. Keep the previous committed gzip.
4. On success, summarize from store meta: `job_count`, `ingested_at`, `feed_last_build_date`.
5. Confirm `git status` is clean after push (or report push failure).

Do not edit `mcp.json`. Do not force-push. Do not amend history.

## Acceptance

- [ ] `data/jobs.json.gz` updated on `main` with today's UTC date in commit message `chore: refresh vacancy index YYYY-MM-DD`
- [ ] Meta `job_count` > 0 and `ingested_at` is today (UTC)
- [ ] On feed failure: no corrupt commit; non-zero exit explained in the agent summary

## Manual cloud smoke

In Cursor Automations → this automation → **Run now**, or start a Cloud Agent on this repo with the instructions above.

## Local fallback

Mac launchd (already installable): see [auto-refresh.md](auto-refresh.md).
