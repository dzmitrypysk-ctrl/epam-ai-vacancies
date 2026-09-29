# Auto-refresh vacancy index

Two paths keep `data/jobs.json.gz` fresh for Render (`dzmitrypysk-ctrl/epam-ai-vacancies`):

| Path | When | Where |
|------|------|--------|
| **A — launchd (Mac)** | Weekdays 09:00 local | This laptop + EPAM VPN |
| **D — Cursor Automation** | Weekdays 09:00 Europe/Minsk | Cloud Agent on GitHub repo |

**Requires for fetch:** LinkedIn feed reachable (often EPAM network). If cloud cannot reach the feed, launchd remains the backup.

## A — Install launchd (once)

```bash
cd projects/ai-native-vacancy-service
chmod +x _scripts/refresh_and_push.sh _scripts/install_launchd_refresh.sh
./_scripts/install_launchd_refresh.sh
```

### Manual run (local)

```bash
./_scripts/refresh_and_push.sh           # ingest + gzip + push deploy repo
./_scripts/refresh_and_push.sh --no-push # local only
```

### Uninstall

```bash
./_scripts/install_launchd_refresh.sh --uninstall
```

### Logs

- `runs/refresh-YYYY-MM-DD.log`
- `runs/launchd-refresh.stdout.log` / `.stderr.log`

## D — Cursor Cloud Automation

Full agent prompt and acceptance: [cloud-agent-refresh.md](cloud-agent-refresh.md).

In the **standalone GitHub repo**, the same script runs with:

```bash
CLOUD_MODE=1 bash _scripts/refresh_and_push.sh
```

That commits/pushes `data/jobs.json.gz` on **this** repo (no separate `DEPLOY_REPO`).

After scripts are on `main`, create a Cursor Automation (scheduled Cloud Agent) pointing at `dzmitrypysk-ctrl/epam-ai-vacancies`, weekdays 09:00 Europe/Minsk, with the instructions from `cloud-agent-refresh.md`. Smoke with **Run now**.

## Notes

- If `--fetch` fails (no VPN / blocked from cloud), the job exits and keeps the previous index.
- Override deploy path (local only): `DEPLOY_REPO=/path/to/repo ./_scripts/refresh_and_push.sh`
- `gh` logged in as `dzmitrypysk-ctrl` for local push; Cloud Agent uses Cursor’s GitHub app on that repo.
