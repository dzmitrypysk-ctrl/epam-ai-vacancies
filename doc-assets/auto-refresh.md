# Auto-refresh vacancy index

Two paths keep `data/jobs.json.gz` fresh for Render (`dzmitrypysk-ctrl/epam-ai-vacancies`):

| Path | When | Where | Cost |
|------|------|--------|------|
| **A — launchd (Mac)** — **primary** | Weekdays 09:00 local | This laptop | **$0/run** (already installable) |
| **D — Cursor Automation** — optional | Weekdays 09:00 Europe/Minsk | Cloud Agent on GitHub repo | Premium+ plan + Cloud Agent usage; cheap model only — see [cloud-agent-refresh.md](cloud-agent-refresh.md) |

**Requires for fetch:** LinkedIn feed reachable via GET (public XML observed 2026-10-15 from Mac; Cloud still needs its own smoke). **Keep launchd as backup** even if Automation is enabled. Cost/smoke log: [runs/cloud-automation-cost-2026-10-15.md](../runs/cloud-automation-cost-2026-10-15.md).

## A — Install launchd (once)

launchd often fails with `Operation not permitted` / exit **126** when `ProgramArguments` point into a Cyrillic workspace path. The installer copies an **ASCII-path wrapper** under `~/Library/Application Support/epam-ai-vacancies/` and prefers `$HOME/work/...` when that symlink exists.

```bash
# Optional but recommended on macOS with non-ASCII Documents path:
# ln -s "$HOME/Documents/Моя работа" "$HOME/work"

cd projects/ai-native-vacancy-service
chmod +x _scripts/refresh_and_push.sh _scripts/install_launchd_refresh.sh
./_scripts/install_launchd_refresh.sh
```

### Manual run (local)

```bash
./_scripts/refresh_and_push.sh           # ingest + gzip + push deploy repo
./_scripts/refresh_and_push.sh --no-push # local only
# or ASCII wrapper:
bash "$HOME/Library/Application Support/epam-ai-vacancies/refresh_and_push_wrapper.sh" --no-push
```

### Uninstall

```bash
./_scripts/install_launchd_refresh.sh --uninstall
```

### Logs

- `runs/refresh-YYYY-MM-DD.log` (when run from project)
- `~/Library/Logs/epam-ai-vacancies-refresh.stdout.log` / `.stderr.log` (launchd)

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
