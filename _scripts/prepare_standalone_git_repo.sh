#!/usr/bin/env bash
# Create a standalone git repo for Render deploy (personal GitHub, not codemie-local).
# Usage (from workspace root):
#   bash projects/ai-native-vacancy-service/_scripts/prepare_standalone_git_repo.sh
set -euo pipefail

SRC="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${STANDALONE_DIR:-$HOME/epam-ai-vacancies-deploy}"

rm -rf "$DEST"
mkdir -p "$DEST"

rsync -a \
  --exclude '.venv' \
  --exclude 'venv' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.pytest_cache' \
  --exclude 'data/jobs.json' \
  --exclude 'data/feed-linkedin-live.xml' \
  --exclude 'runs/' \
  "$SRC/" "$DEST/"

# Ensure gzip store is present
if [[ ! -f "$DEST/data/jobs.json.gz" ]]; then
  echo "ERROR: data/jobs.json.gz missing in $DEST" >&2
  exit 1
fi

cd "$DEST"
git init -b main
git add .
git -c user.email="deploy@local" -c user.name="Deploy" commit -m "EPAM AI-native vacancy service prototype for Render"

echo ""
echo "Standalone repo ready: $DEST"
echo "Next:"
echo "  1. Create empty public repo on YOUR personal GitHub: epam-ai-vacancies"
echo "  2. cd $DEST"
echo "  3. git remote add origin https://github.com/YOUR_USER/epam-ai-vacancies.git"
echo "  4. git push -u origin main"
echo "  5. Render → New Web Service → that repo (Blueprint render.yaml)"
echo ""
du -sh "$DEST" "$DEST/data/jobs.json.gz"
