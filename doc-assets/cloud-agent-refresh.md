# Cloud Agent / Cursor Automation — vacancy index refresh

**Repo:** `dzmitrypysk-ctrl/epam-ai-vacancies`  
**Schedule (intended):** weekdays 09:00 Europe/Minsk  
**Outcome:** fresh `data/jobs.json.gz` on `main` → Render redeploys if connected.

## Cost & plan gate (2026-10)

- **Subscription:** Cloud Agents / Automations need Premium+ **or Enterprise** (not Free/Plus). **This account: Enterprise (confirmed 2026-10-15)** — no Premium upgrade required.
- **Billing:** no separate Automation fee — each run uses Cloud Agent usage (Enterprise pooled usage / on-demand). Third-party models may incur Cursor Token Rate. VM build is free.
- **Estimate for this job** (short prompt + `refresh_and_push.sh`, ~20 weekdays/mo):
  - cheap / fast model: often ~$0.05–0.50 per run or mostly covered by pool;
  - heavy model (Opus / high GPT): easily $1–5+ per run — **do not use** for this bash job.
- **Primary path stays free:** Mac launchd — see [auto-refresh.md](auto-refresh.md). Use Cloud only when the Mac is often off at 09:00 **and** the smoke below passes.
- Evidence log: [runs/cloud-automation-cost-2026-10-15.md](../runs/cloud-automation-cost-2026-10-15.md).

## Model for Automation

Pick the **cheapest capable** Cloud Agent model (Composer / fast tier). Instructions are bash-only; model quality does not improve the feed.

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

## Manual cloud smoke (required before schedule)

1. Install the **Cursor GitHub App** on `dzmitrypysk-ctrl/epam-ai-vacancies` (vault monorepo alone is not enough).
2. Plan gate: **Enterprise confirmed** — OK for Automations.
3. In Cursor Automations on that repo → **Run now** with the instructions above (cheapest model).
4. Acceptance for smoke: script exits 0, commit `chore: refresh vacancy index YYYY-MM-DD` on `main`, or a clear feed/network error with **no** corrupt gzip commit.
5. **Feed note (2026-10-15):** GET of the LinkedIn feed returned valid XML (~47 MB) from the Mac; use GET not HEAD. If Cloud Run now fails on network, **do not** enable daily schedule — keep launchd only.

## Local fallback (keep enabled)

Mac launchd remains the **default / backup** even if Cloud is scheduled: see [auto-refresh.md](auto-refresh.md). Do not uninstall launchd when adding Automation.
