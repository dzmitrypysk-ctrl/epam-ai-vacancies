#!/usr/bin/env bash
# Install LaunchAgent that pings the Render service every 5 minutes
# while this Mac is awake/logged in.
# Script is copied to ~/Library/Application Support/... (ASCII path)
# because launchd often fails on Cyrillic workspace paths.
set -euo pipefail

LABEL="com.epam.ai-vacancies.keepalive"
KEEP_DIR="$HOME/Library/Application Support/epam-ai-vacancies"
PING_ABS="$KEEP_DIR/keepalive_ping.sh"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
LOG="$HOME/Library/Logs/epam-ai-vacancies-keepalive.log"

mkdir -p "$KEEP_DIR" "$HOME/Library/LaunchAgents" "$(dirname "$LOG")"

cat > "$PING_ABS" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
BASE="${KEEPALIVE_BASE_URL:-https://epam-ai-vacancies.onrender.com}"
export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/usr/local/bin"
curl -fsS --retry 2 --retry-delay 5 --max-time 90 "${BASE}/health" >/dev/null
curl -fsS --retry 2 --retry-delay 5 --max-time 90 -o /dev/null "${BASE}/llms.txt"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) ok ${BASE}"
EOF
chmod +x "$PING_ABS"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>${PING_ABS}</string>
  </array>
  <key>StartInterval</key>
  <integer>300</integer>
  <key>RunAtLoad</key>
  <true/>
  <key>StandardOutPath</key>
  <string>${LOG}</string>
  <key>StandardErrorPath</key>
  <string>${LOG}</string>
</dict>
</plist>
EOF

UID_NUM="$(id -u)"
launchctl bootout "gui/${UID_NUM}/${LABEL}" 2>/dev/null || true
launchctl bootstrap "gui/${UID_NUM}" "$PLIST"
launchctl kickstart -k "gui/${UID_NUM}/${LABEL}" 2>/dev/null || true

echo "Installed ${LABEL}"
echo "Ping script: ${PING_ABS}"
echo "Log: ${LOG}"
echo "Interval: 300s"
sleep 1
tail -n 5 "$LOG" 2>/dev/null || true
