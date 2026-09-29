#!/usr/bin/env bash
# Refresh vacancy index from live LinkedIn feed and push gzip to GitHub.
# Requires EPAM network (or VPN) for --fetch. Safe for launchd or Cursor Cloud Agent.
#
# Usage:
#   ./_scripts/refresh_and_push.sh
#   DEPLOY_REPO="$HOME/epam-ai-vacancies-deploy" ./_scripts/refresh_and_push.sh
#   CLOUD_MODE=1 ./_scripts/refresh_and_push.sh   # commit/push this repo (Cloud Agent)
#   ./_scripts/refresh_and_push.sh --no-push
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLOUD_MODE="${CLOUD_MODE:-0}"
if [[ "$CLOUD_MODE" == "1" ]]; then
  DEPLOY_REPO="$ROOT"
else
  DEPLOY_REPO="${DEPLOY_REPO:-$HOME/epam-ai-vacancies-deploy}"
fi
GIT_NAME="${GIT_AUTHOR_NAME:-dzmitrypysk-ctrl}"
GIT_EMAIL="${GIT_AUTHOR_EMAIL:-dzmitrypysk-ctrl@users.noreply.github.com}"
NO_PUSH=0
for arg in "$@"; do
  case "$arg" in
    --no-push) NO_PUSH=1 ;;
    --cloud) CLOUD_MODE=1; DEPLOY_REPO="$ROOT" ;;
  esac
done

cd "$ROOT"
mkdir -p "$ROOT/runs"
LOG="$ROOT/runs/refresh-$(date -u +%Y-%m-%d).log"
exec > >(tee -a "$LOG") 2>&1

echo "=== refresh start $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "ROOT=$ROOT"
echo "CLOUD_MODE=$CLOUD_MODE"
echo "DEPLOY_REPO=$DEPLOY_REPO"

PY="$ROOT/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "Creating venv..."
  python3 -m venv "$ROOT/.venv"
  PY="$ROOT/.venv/bin/python"
  "$PY" -m pip install -q -r "$ROOT/requirements.txt"
fi

if ! "$PY" "$ROOT/_scripts/ingest_feed.py" --fetch; then
  echo "ERROR: ingest --fetch failed (need EPAM network/VPN, or feed blocked from cloud). Keeping previous index." >&2
  exit 2
fi

# Reject tiny/non-XML responses masquerading as success
FEED_SNAP="$ROOT/data/feed-linkedin-live.xml"
if [[ -f "$FEED_SNAP" ]]; then
  SIZE="$(wc -c < "$FEED_SNAP" | tr -d ' ')"
  if [[ "$SIZE" -lt 100000 ]] || ! head -c 200 "$FEED_SNAP" | grep -q "<job\|<source\|<?xml"; then
    echo "ERROR: feed snapshot looks invalid (size=$SIZE). Not rebuilding." >&2
    exit 2
  fi
fi

"$PY" "$ROOT/_scripts/build_gzip_store.py"

GZ="$ROOT/data/jobs.json.gz"
if [[ ! -f "$GZ" ]]; then
  echo "ERROR: gzip missing after build: $GZ" >&2
  exit 3
fi

if [[ "$NO_PUSH" -eq 1 ]]; then
  echo "Skip push (--no-push). Local gzip ready: $GZ"
  echo "=== refresh end $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  exit 0
fi

if [[ ! -d "$DEPLOY_REPO/.git" ]]; then
  echo "ERROR: deploy git repo not found: $DEPLOY_REPO" >&2
  echo "Run: bash _scripts/prepare_standalone_git_repo.sh" >&2
  exit 4
fi

if [[ "$DEPLOY_REPO" != "$ROOT" ]]; then
  mkdir -p "$DEPLOY_REPO/data"
  cp -f "$GZ" "$DEPLOY_REPO/data/jobs.json.gz"
fi

cd "$DEPLOY_REPO"
if command -v gh >/dev/null 2>&1; then
  gh auth setup-git >/dev/null 2>&1 || true
fi

git add data/jobs.json.gz
# Include today's refresh log when present in this repo
if [[ -f "$ROOT/runs/refresh-$(date -u +%Y-%m-%d).log" ]] && [[ "$DEPLOY_REPO" == "$ROOT" ]]; then
  mkdir -p runs
  git add "runs/refresh-$(date -u +%Y-%m-%d).log" 2>/dev/null || true
fi

if git diff --cached --quiet; then
  echo "No gzip content change — nothing to commit."
else
  DAY="$(date -u +%F)"
  git -c "user.name=$GIT_NAME" -c "user.email=$GIT_EMAIL" commit -m "chore: refresh vacancy index ${DAY}"
  git push origin main
  echo "Pushed to origin/main"
fi

echo "=== refresh end $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
