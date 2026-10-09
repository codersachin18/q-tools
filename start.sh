#!/usr/bin/env bash
# Q-Tools launcher (macOS / Linux) - double click or run from a terminal.
cd "$(dirname "$0")" || exit 1

if [ -x ".venv/bin/python" ]; then
  exec .venv/bin/python app.py
fi

if command -v python3 >/dev/null 2>&1; then
  exec python3 app.py
fi

echo
echo "  Python was not found. Run setup.sh first."
echo
exit 1
