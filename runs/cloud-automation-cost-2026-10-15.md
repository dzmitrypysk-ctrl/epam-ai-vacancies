# Cloud Automation cost & smoke — 2026-10-15

## Cost (summary)

- No separate Automation fee; billed as Cloud Agent usage ([Cursor Automations](https://cursor.com/docs/cloud-agent/automations)).
- Requires plan with Cloud agents & automations: Premium+ **or Enterprise** (not Free/Plus).
- **Confirmed 2026-10-15 (user):** account is **Enterprise** — Automations are available; no individual Premium upgrade needed.
- Per weekday run (cheap model, short prompt): often ~$0.05–0.50 or drawn from Enterprise pooled usage; third-party models may also incur Cursor Token Rate on Teams/Enterprise.
- ~20 weekdays/mo: often low incremental cost if cheap model + pool; expensive models still wasteful for this bash job.
- **Mac launchd remains $0/run** and is already loaded (`com.epam.ai-native-vacancy.refresh`, weekdays 09:00 local).

## Plan gate (check-plan)

- **Status: PASS** — user confirmed **Enterprise** (2026-10-15).
- Remaining before schedule: Cursor GitHub App on `dzmitrypysk-ctrl/epam-ai-vacancies` + one **Run now** smoke (see below).

## Feed / cloud smoke (smoke-cloud)

| Probe | Result |
|-------|--------|
| GET `https://vacancies.careers.epam.com/api/feed/linkedin` from this Mac | **OK** — HTTP 200, `application/xml`, ~46.8 MB, valid `<source>` XML (2026-10-15) |
| HEAD same URL | Misleading — short HTML; do not use HEAD for health checks |
| Cloud Agent Task on vault git root (`Моя работа`) | **Blocked** — `Cursor app needs to be installed on your repository` |
| Implied gate for Automation on `dzmitrypysk-ctrl/epam-ai-vacancies` | Install Cursor GitHub App on that repo, then **Run now** once with prompt from `doc-assets/cloud-agent-refresh.md` |

**Do not** enable daily Cloud schedule until that repo smoke succeeds. Keep launchd as primary until then.

## Model / fallback (cheap-model)

- Automation model: cheapest capable agent (e.g. Composer / fast tier) — bash-only job.
- Primary: Mac launchd ([auto-refresh.md](../doc-assets/auto-refresh.md)).
- Cloud: optional when Mac off at 09:00 **and** Enterprise (confirmed) **and** feed smoke on GitHub repo passed.
