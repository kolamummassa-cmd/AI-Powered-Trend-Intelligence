#!/usr/bin/env bash
# Runs backend + frontend together in a single terminal for local dev.
# First run installs dependencies (venv + pip, npm install); later runs
# skip straight to starting both. Ctrl+C stops both cleanly.
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# --- Backend ---
cd "$ROOT_DIR/backend"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements/dev.txt

export DJANGO_SETTINGS_MODULE=config.settings.dev
export DATABASE_URL="${DATABASE_URL:-sqlite:///db.sqlite3}"

python manage.py migrate

python manage.py runserver > "$ROOT_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "Backend running at http://localhost:8000 (pid $BACKEND_PID) — logs in backend.log"

cleanup() {
  echo ""
  echo "Stopping backend (pid $BACKEND_PID)..."
  kill "$BACKEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# --- Frontend (runs in the foreground; Ctrl+C here triggers cleanup above) ---
cd "$ROOT_DIR/frontend"
if [ ! -d "node_modules" ]; then
  npm install
fi
npm run dev
