# AI-Powered Journaling Companion

A full-stack journaling app with **context-aware prompts**, **private sentiment and theme analysis**, and **reflection summaries**. Journal entries stay in your infrastructure; AI runs on-device (e.g. Ollama) or your chosen LLM provider.
Youtube Link: https://youtu.be/B5DpggJ4APQ
Youtube Link With Face: https://youtu.be/d6KcpjjgNLE

**Stack:** React (Vite) + Tailwind · Auth (Node/Express, JWT) · Journal (Java/Spring Boot) · Prompt / Insights / Summary (Python) · PostgreSQL · Kafka.

---

## Prerequisites

- **Docker & Docker Compose** — for PostgreSQL, Zookeeper, and Kafka
- **Java 17** — Journal Service
- **Node 18+** — Auth Service, Frontend
- **Python 3.10+** — Prompt Service, AI consumer, Insights API, Summary Service

---
---

## Quick start (manual)

### 1. Start infrastructure

From the repo root:

```bash
docker-compose up -d postgres postgres_analytics zookeeper kafka
```

Wait until everything is up (Kafka can take 15–20s). Check with `docker-compose ps`.

### 2. Environment

Create a `.env` in the repo root and use the **same `JWT_SECRET`** for Auth, Journal, Insights, and Summary:

```bash
cp .env.example .env
# Edit .env: set JWT_SECRET (e.g. a 32+ character string). See .env.example.
```

In each terminal where you start a service, load it:

```bash
source .env
```

### 3. Run the app (per-service)

Open **7 terminals** (from repo root). In each, `source .env` then:

| Order | Service        | Command |
|-------|----------------|---------|
| 1     | **Auth**       | `cd auth-service && npm install && PORT=3001 npm start` |
| 2     | **Journal**    | `cd journal-service && ./mvnw spring-boot:run` |
| 3     | **Prompt**     | `cd prompt-service && pip install -r requirements.txt && JOURNAL_SERVICE_URL=${JOURNAL_SERVICE_URL:-http://localhost:8080} PORT=8000 python main.py` |
| 4     | **AI consumer**| `cd ai-services && pip install -r requirements.txt && python -c "from db import init_db; init_db()" && python consumer.py` |
| 5     | **Insights API**| `cd ai-services && ANALYTICS_DB_URL=${ANALYTICS_DB_URL:-postgresql://analytics:analytics_secret@localhost:5433/analytics_db} PORT=8001 python insights_api.py` |
| 6     | **Summary**    | `cd ai-services && ANALYTICS_DB_URL=${ANALYTICS_DB_URL:-postgresql://analytics:analytics_secret@localhost:5433/analytics_db} PORT=8002 python summary_service.py` |
| 7     | **Frontend**   | `cd frontend && npm install && npm run dev` |

Then open **http://localhost:3000**, sign up, and create an entry.

**Full step-by-step** (env details, migrations, troubleshooting, LLM/Ollama): see **[RUNBOOK.md](RUNBOOK.md)**.

---

## Services and ports

| Service         | Port | Description |
|-----------------|------|-------------|
| Frontend        | 3000 | React (Vite) + Tailwind |
| Auth            | 3001 | Sign-up, login, JWT |
| Journal         | 8080 | Entries CRUD, Kafka events |
| Prompt          | 8000 | Context-aware prompts |
| Insights API    | 8001 | Sentiment, themes, emotions |
| Summary         | 8002 | Daily / weekly / monthly summaries |
| PostgreSQL      | 5432 | Journal DB |
| PostgreSQL      | 5433 | Analytics DB |
| Zookeeper       | 2181 | For Kafka |
| Kafka           | 9092 | Entry events |

---

## Environment

- **JWT_SECRET** — Must be the same for Auth (signs tokens) and Journal/Insights/Summary (verify). Set in `.env`; 32+ chars for HS256. Default in code is dev-only.
- Optional overrides (e.g. `POSTGRES_HOST`, `KAFKA_BOOTSTRAP_SERVERS`, `ANALYTICS_DB_URL`) — see `.env.example`.

---

## One-click run

From the repo root, after creating `.env` (see [Environment](#environment) below):

```bash
make up
```

This starts infrastructure (Postgres, Zookeeper, Kafka) and all 7 app services in the background. First run installs dependencies and may take a few minutes. Open **http://localhost:3000** when ready.

To stop everything:

```bash
make down
```

Logs: `logs/*.log`. For full control (e.g. run services in separate terminals), see [Run the app (per-service)](#3-run-the-app-per-service) below.
---

## More

- **[RUNBOOK.md](RUNBOOK.md)** — Full run instructions, migrations, troubleshooting, Ollama/LLM setup
- **[ARCHITECTURE.md](ARCHITECTURE.md)** — Components, data flow, design
- **scripts/README.md** — Seed data, migrations
