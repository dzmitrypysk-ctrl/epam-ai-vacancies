#!/usr/bin/env bash
# Ping Render free-tier service so it does not sleep (~15m idle).
# Safe to run from launchd, cron, or manually.
set -euo pipefail
BASE="${KEEPALIVE_BASE_URL:-https://epam-ai-vacancies.onrender.com}"
curl -fsS --retry 2 --retry-delay 5 --max-time 90 "${BASE}/health" >/dev/null
curl -fsS --retry 2 --retry-delay 5 --max-time 90 -o /dev/null "${BASE}/llms.txt"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) ok ${BASE}"
