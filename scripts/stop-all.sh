#!/usr/bin/env bash
# Stop all app services and infrastructure.
# Run from repo root: ./scripts/stop-all.sh   or: make down

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PIDDIR="$ROOT/.pids"
if [[ -d "$PIDDIR" ]]; then
  echo "== Stopping app services..."
  for f in "$PIDDIR"/*.pid; do
    [[ -f "$f" ]] || continue
    name=$(basename "$f" .pid)
    pid=$(cat "$f")
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      echo "  stopped $name (PID $pid)"
    fi
    rm -f "$f"
  done
fi

echo "== Stopping infrastructure..."
docker-compose down 2>/dev/null || true
echo "Done."
