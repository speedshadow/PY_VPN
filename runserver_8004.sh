#!/usr/bin/env bash
# Simple helper to always serve Django on port 8004.
# 1. Kills any process listening on the port.
# 2. Activates the project virtual-environment if it exists.
# 3. Starts the development server on port 8004.

set -e
PORT=8004

# Find and kill any process bound to the desired port
if command -v lsof >/dev/null 2>&1; then
  PIDS=$(lsof -ti tcp:$PORT || true)
elif command -v ss >/dev/null 2>&1; then
  PIDS=$(ss -ltnp "sport = :$PORT" 2>/dev/null | awk -F',' '{print $2}' | awk '{print $1}')
else
  echo "Neither lsof nor ss found; cannot automatically free port $PORT" >&2
  exit 1
fi

if [ -n "$PIDS" ]; then
  echo "Killing process(es) using port $PORT: $PIDS"
  kill -9 $PIDS || true
fi

# Activate virtual environment if present
if [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
fi

# Run the Django development server
exec python manage.py runserver $PORT
