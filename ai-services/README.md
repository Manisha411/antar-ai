# AI Services

- **Consumer**: Consumes `EntryCreated` from Kafka; computes sentiment and themes; stores in Analytics DB.
- **Insights API**: GET /api/v1/insights/sentiment, GET /api/v1/insights/themes (JWT or X-User-Id).

## Prerequisites

- PostgreSQL (analytics): port 5433, user analytics, db analytics_db (see docker-compose postgres_analytics).
- Kafka: port 9092. Journal Service publishes to topic `journal.entry.created`.

## Run

1. Create Analytics DB and tables:
   ```bash
   pip install -r requirements.txt
   python -c "from db import init_db; init_db()"
   ```

2. Start consumer (in one terminal):
   ```bash
   python consumer.py
   ```

3. Start Insights API (in another terminal):
   ```bash
   PORT=8001 python insights_api.py
   ```

Env: `ANALYTICS_DB_URL`, `JWT_SECRET` (match Auth Service). Optional LLM: `LLM_PROVIDER=openai` + `OPENAI_API_KEY`, or `LLM_PROVIDER=ollama` (see RUNBOOK §8).
