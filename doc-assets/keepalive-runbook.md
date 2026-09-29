# Keep Render free tier warm

Render free web services sleep after ~15 minutes without traffic.
Cold start often exceeds Perplexity/AI fetch timeouts.

## Primary: GitHub Actions (24/7)

Workflow: `.github/workflows/keepalive.yml`  
Schedule: every 5 minutes + manual `workflow_dispatch`.

Needs GitHub auth scope `workflow` to push the file:

```bash
gh auth refresh -h github.com -s repo,workflow,gist,read:org
# then push .github/workflows/keepalive.yml to dzmitrypysk-ctrl/epam-ai-vacancies
```

Check runs: https://github.com/dzmitrypysk-ctrl/epam-ai-vacancies/actions

## Backup: Mac launchd (while laptop is awake)

```bash
# from workspace root
bash projects/ai-native-vacancy-service/_scripts/install_macos_keepalive.sh
```

Logs: `~/Library/Logs/epam-ai-vacancies-keepalive.log`

Unload:

```bash
launchctl bootout "gui/$(id -u)/com.epam.ai-vacancies.keepalive"
```

## Manual ping

```bash
bash projects/ai-native-vacancy-service/_scripts/keepalive_ping.sh
# or
curl -fsS https://epam-ai-vacancies.onrender.com/health
```
