#!/usr/bin/env bash
# Install or uninstall macOS LaunchAgent for weekday vacancy refresh (09:00 local).
# Wrapper lives under ~/Library/Application Support/... (ASCII path) because
# launchd often fails with Operation not permitted / exit 126 on Cyrillic workspace paths.
#
# Usage:
#   ./_scripts/install_launchd_refresh.sh
#   ./_scripts/install_launchd_refresh.sh --uninstall
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="com.epam.ai-native-vacancy.refresh"
KEEP_DIR="$HOME/Library/Application Support/epam-ai-vacancies"
WRAPPER="$KEEP_DIR/refresh_and_push_wrapper.sh"
PLIST_DST="$HOME/Library/LaunchAgents/${LABEL}.plist"
LOG_DIR="$HOME/Library/Logs"
STDOUT_LOG="$LOG_DIR/epam-ai-vacancies-refresh.stdout.log"
STDERR_LOG="$LOG_DIR/epam-ai-vacancies-refresh.stderr.log"

# Prefer ASCII symlink ($HOME/work) when present; else absolute ROOT.
WORK_LINK="$HOME/work"
if [[ -d "$WORK_LINK/projects/ai-native-vacancy-service" ]]; then
  PROJECT_ROOT="$WORK_LINK/projects/ai-native-vacancy-service"
else
  PROJECT_ROOT="$ROOT"
fi

if [[ "${1:-}" == "--uninstall" ]]; then
  launchctl bootout "gui/$(id -u)/${LABEL}" 2>/dev/null || true
  rm -f "$PLIST_DST"
  echo "Uninstalled $LABEL"
  exit 0
fi

chmod +x "$ROOT/_scripts/refresh_and_push.sh"
mkdir -p "$KEEP_DIR" "$HOME/Library/LaunchAgents" "$LOG_DIR" "$ROOT/runs"

# ASCII-path wrapper that cds into project and runs refresh
cat > "$WRAPPER" <<EOF
#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/usr/local/bin:\$HOME/.local/bin"
PROJECT_ROOT="${PROJECT_ROOT}"
# Fallback: resolve via work symlink if primary path is missing
if [[ ! -d "\$PROJECT_ROOT" ]] && [[ -d "\$HOME/work/projects/ai-native-vacancy-service" ]]; then
  PROJECT_ROOT="\$HOME/work/projects/ai-native-vacancy-service"
fi
cd "\$PROJECT_ROOT"
exec /bin/bash "\$PROJECT_ROOT/_scripts/refresh_and_push.sh" "\$@"
EOF
chmod +x "$WRAPPER"

cat > "$PLIST_DST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>${WRAPPER}</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${KEEP_DIR}</string>
  <key>StartCalendarInterval</key>
  <array>
    <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Weekday</key><integer>2</integer><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Weekday</key><integer>3</integer><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Weekday</key><integer>4</integer><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Weekday</key><integer>5</integer><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>
  </array>
  <key>StandardOutPath</key>
  <string>${STDOUT_LOG}</string>
  <key>StandardErrorPath</key>
  <string>${STDERR_LOG}</string>
  <key>RunAtLoad</key>
  <false/>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)/${LABEL}" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_DST"
launchctl enable "gui/$(id -u)/${LABEL}" 2>/dev/null || true

echo "Installed $LABEL (weekdays 09:00 local time)"
echo "Wrapper (ASCII): $WRAPPER"
echo "Project root:    $PROJECT_ROOT"
echo "Logs:            $STDOUT_LOG"
echo "Uninstall:       $0 --uninstall"
echo "Manual run:      $WRAPPER"
echo "Hint: ln -s \"\$HOME/Documents/\$'Моя работа'\" \"\$HOME/work\" if full disk access blocks Cyrillic paths"
