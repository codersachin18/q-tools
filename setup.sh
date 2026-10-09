#!/usr/bin/env bash
# ============================================================
#  Q-Tools - first time setup for macOS and Linux
#
#    bash setup.sh
#
#  Does everything setup.bat does on Windows:
#    finds Python -> creates .venv -> pip install -r requirements.txt
#    -> generates the icon -> puts a Q-Tools launcher on the Desktop
# ============================================================
set -u

PROJECT="$(cd "$(dirname "$0")" && pwd)"
VENV="$PROJECT/.venv"
VERSION="2.0.1"
PYTHON_MIN="3.10"

step() { printf '\n[%s] %s\n' "$1" "$2"; }
fail() {
  printf '\n[ERROR] %s\n' "$1"
  [ "${2:-}" ] && printf '       %s\n' "$2"
  exit 1
}

printf '\n==================================================\n'
printf '  Q-Tools setup  v%s\n' "$VERSION"
printf '==================================================\n'

# --------------------------------------------------
# platform
# --------------------------------------------------
case "$(uname -s)" in
  Darwin)                       PLATFORM=macos ;;
  Linux)                        PLATFORM=linux ;;
  MINGW*|MSYS*|CYGWIN*|Windows) PLATFORM=windows ;;
  *)                            PLATFORM=unknown ;;
esac
# internal/testing hook: QTOOLS_FORCE_PLATFORM=macos|linux
PLATFORM="${QTOOLS_FORCE_PLATFORM:-$PLATFORM}"

if [ "$PLATFORM" = "windows" ]; then
  fail "Windows detected - run setup.bat instead of setup.sh." \
       "Right click setup.bat -> Run (double click works too)."
fi
if [ "$PLATFORM" = "unknown" ]; then
  fail "Unsupported system: $(uname -s)" "Run the manual steps in README.md"
fi

# --------------------------------------------------
# 1/5  Python
# --------------------------------------------------
step "1/5" "Looking for Python $PYTHON_MIN+"
PY=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    if "$candidate" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
      PY="$candidate"
      break
    fi
  fi
done
if [ -z "$PY" ]; then
  if [ "$PLATFORM" = "macos" ]; then
    fail "Python $PYTHON_MIN+ not found." \
         "Install it:  brew install python3   (or download from python.org)"
  else
    fail "Python $PYTHON_MIN+ not found." \
         "Install it:  sudo apt install python3 python3-venv"
  fi
fi
printf '       %s\n' "$("$PY" --version 2>&1)"

# --------------------------------------------------
# 2/5  virtual environment
# --------------------------------------------------
step "2/5" "Creating virtual environment"
if [ -x "$VENV/bin/python" ]; then
  printf '       already exists\n'
else
  "$PY" -m venv "$VENV" || fail "Could not create .venv" \
        "Make sure the venv module is installed (apt install python3-venv)."
  printf '       OK\n'
fi
VPY="$VENV/bin/python"

# --------------------------------------------------
# 3/5  dependencies
# --------------------------------------------------
step "3/5" "Installing required packages (first run only, please wait)"
"$VPY" -m pip install --upgrade pip --disable-pip-version-check -q \
  || printf '       (pip upgrade skipped)\n'
if ! "$VPY" -m pip install -r "$PROJECT/requirements.txt" \
      --disable-pip-version-check -q; then
  fail "Installing packages failed." "Check your internet connection and re-run setup.sh"
fi
printf '       OK\n'

# --------------------------------------------------
# 4/5  icon
# --------------------------------------------------
step "4/5" "Generating app icon"
if [ -f "$PROJECT/assets/make_icon.py" ]; then
  "$VPY" "$PROJECT/assets/make_icon.py" >/dev/null 2>&1 || true
fi
printf '       OK\n'

# --------------------------------------------------
# 5/5  Desktop shortcut
# --------------------------------------------------
step "5/5" "Creating Desktop shortcut"

DESKTOP="$HOME/Desktop"
[ -d "$DESKTOP" ] || DESKTOP="$HOME"

create_macos_app() {
  APP="$DESKTOP/Q-Tools.app"
  rm -rf "$APP"
  mkdir -p "$APP/Contents/MacOS" || return 1

  cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Q-Tools</string>
    <key>CFBundleDisplayName</key>
    <string>Q-Tools</string>
    <key>CFBundleIdentifier</key>
    <string>com.codersachin18.qtools</string>
    <key>CFBundleVersion</key>
    <string>$VERSION</string>
    <key>CFBundleShortVersionString</key>
    <string>$VERSION</string>
    <key>CFBundleExecutable</key>
    <string>Q-Tools</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST

  cat > "$APP/Contents/MacOS/Q-Tools" <<LAUNCHER
#!/bin/bash
cd "$PROJECT" || exit 1
exec "$VENV/bin/python" "$PROJECT/app.py"
LAUNCHER
  chmod +x "$APP/Contents/MacOS/Q-Tools"

  # files downloaded from a browser carry the quarantine flag
  command -v xattr >/dev/null 2>&1 && \
    xattr -dr com.apple.quarantine "$APP" 2>/dev/null

  printf '       %s\n' "$APP"
}

create_linux_desktop() {
  ICON="$PROJECT/assets/qtools.png"
  [ -f "$ICON" ] || ICON="$PROJECT/assets/qtools.ico"
  ENTRY="$DESKTOP/Q-Tools.desktop"

  cat > "$ENTRY" <<ENTRY_FILE
[Desktop Entry]
Version=1.0
Type=Application
Name=Q-Tools
Comment=27 everyday utilities in one window
Exec="$VENV/bin/python" "$PROJECT/app.py"
Path=$PROJECT
Icon=$ICON
Terminal=false
StartupNotify=true
Categories=Utility;
ENTRY_FILE
  chmod +x "$ENTRY" 2>/dev/null

  # GNOME/Nautilus: mark the launcher trusted
  command -v gio >/dev/null 2>&1 && \
    gio set "$ENTRY" metadata::trusted true 2>/dev/null

  # also add it to the application menu
  APPDIR="$HOME/.local/share/applications"
  mkdir -p "$APPDIR" 2>/dev/null && \
    cp "$ENTRY" "$APPDIR/q-tools.desktop" 2>/dev/null
  command -v update-desktop-database >/dev/null 2>&1 && \
    update-desktop-database "$APPDIR" 2>/dev/null

  printf '       %s\n' "$ENTRY"
}

case "$PLATFORM" in
  macos) create_macos_app   || fail "Could not create the app shortcut." ;;
  linux) create_linux_desktop || fail "Could not create the .desktop launcher." ;;
esac

printf '\n==================================================\n'
printf '  Setup complete!\n\n'
printf '  * Double click the "Q-Tools" icon on your Desktop\n'
printf '  * Or run:  %s/start.sh\n' "$PROJECT"
printf '==================================================\n\n'
exit 0
