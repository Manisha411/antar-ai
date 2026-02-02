#!/usr/bin/env bash
# One-click start: infrastructure + all app services.
# Run from repo root: ./scripts/start-all.sh   or: make up

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "Missing .env. Copy .env.example to .env and set JWT_SECRET."
  exit 1
fi

# Export .env for all child processes
set -a
source .env
set +a

echo "== Starting infrastructure (Postgres, Zookeeper, Kafka)..."
docker-compose up -d postgres postgres_analytics zookeeper kafka

echo "== Waiting for infrastructure..."
wait_for_port() {
  local host="${1:-localhost}" port="$2" name="$3" max=60 n=0
  until nc -z "$host" "$port" 2>/dev/null; do
    n=$((n + 1))
    if [[ $n -ge $max ]]; then
      echo "Timeout waiting for $name ($host:$port)"
      exit 1
    fi
    sleep 1
  done
}
wait_for_port localhost 5432 "Postgres (journal)"
wait_for_port localhost 5433 "Postgres (analytics)"
# Kafka can take longer
for i in $(seq 1 30); do
  nc -z localhost 9092 2>/dev/null && break
  sleep 1
done
nc -z localhost 9092 2>/dev/null || { echo "Kafka (9092) not ready; continuing anyway."; }

mkdir -p logs .pids

echo "== Installing dependencies (first run may take a few minutes)..."
(cd auth-service && npm install --silent)
(cd frontend && npm install --silent)
(cd prompt-service && pip install -q -r requirements.txt)
(cd ai-services && pip install -q -r requirements.txt)

echo "== Initializing analytics DB..."
(cd ai-services && python -c "from db import init_db; init_db()")

echo "== Starting services..."
_start() {
  local name="$1" dir="$2" cmd="$3" log="$ROOT/logs/${name}.log" pidfile="$ROOT/.pids/${name}.pid"
  (cd "$ROOT/$dir" && eval "exec $cmd") >> "$log" 2>&1 &
  echo $! > "$pidfile"
  echo "  started $name (PID $(cat "$pidfile"), log: logs/${name}.log)"
}

_start auth auth-service "PORT=3001 npm start"
sleep 1
_start journal journal-service "./mvnw -q spring-boot:run"
sleep 2
_start prompt prompt-service "JOURNAL_SERVICE_URL=\${JOURNAL_SERVICE_URL:-http://localhost:8080} PORT=8000 python main.py"
_start consumer ai-services "python consumer.py"
_start insights ai-services "ANALYTICS_DB_URL=\${ANALYTICS_DB_URL:-postgresql://analytics:analytics_secret@localhost:5433/analytics_db} PORT=8001 python insights_api.py"
_start summary ai-services "ANALYTICS_DB_URL=\${ANALYTICS_DB_URL:-postgresql://analytics:analytics_secret@localhost:5433/analytics_db} PORT=8002 python summary_service.py"
_start frontend frontend "npm run dev"

echo ""
echo "All services started. Frontend: http://localhost:3000"
echo "Logs: logs/*.log   Stop: ./scripts/stop-all.sh  or  make down"
