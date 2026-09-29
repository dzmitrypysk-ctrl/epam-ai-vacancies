#!/usr/bin/env bash
# Public URL via Cloudflare quick tunnel (no GitHub). Laptop + API must stay running.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${PORT:-8977}"
cd "$ROOT"

if ! curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
  echo "Starting API on :${PORT} ..."
  .venv/bin/uvicorn service.app:app --host 127.0.0.1 --port "$PORT" &
  sleep 3
fi

echo "Local: http://127.0.0.1:${PORT}/test"
echo "Starting Cloudflare quick tunnel..."
echo "Set PUBLIC_BASE_URL to the printed trycloudflare.com URL in another terminal if needed."
echo ""

exec npx --yes cloudflared tunnel --url "http://127.0.0.1:${PORT}"
