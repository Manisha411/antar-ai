# Runbook – How to Run the Full System

This runbook describes the **manual** steps: start infrastructure with Docker Compose, then start each service in its own terminal. Follow the sections in order.

## Prerequisites

- Docker and Docker Compose (for PostgreSQL, Zookeeper, and Kafka)
- Java 17 (for Journal Service; or use IDE to run)
- Node 18+ (Auth, Frontend)
- Python 3.10+ (Prompt, AI consumer, Insights API, Summary Service)

## 1. Start infrastructure

**Ensure Docker is running** (Docker Desktop or `sudo systemctl start docker` on Linux). If you see “Cannot connect to the Docker daemon”, start Docker first.

From repo root (`journal-companion`):

```bash
docker-compose up -d postgres postgres_analytics zookeeper kafka
```

Wait until Postgres, Zookeeper, and Kafka are up (e.g. `docker-compose ps`). Kafka depends on Zookeeper and may take 15–20 seconds to be ready.

## 2. Environment (one place for all terminals)

**Who creates JWT_SECRET?** You do. No service generates it. It’s a shared secret you choose once (e.g. a long random string or UUID), put in `.env`, and use everywhere. Auth uses it to **sign** tokens; Journal, Insights, Summary use it to **verify** them. Use at least 32 characters for HS256.

Create a `.env` in the **repo root** so every terminal can load the same JWT secret and URLs:

```bash
# From repo root (journal-companion)
cp .env.example .env
# Edit .env: set JWT_SECRET to any long random string you choose (same value for all services).
```

**In each terminal** before starting a service, load the env so variables are exported:

```bash
# From repo root
source .env
```

Then start the service for that terminal (steps below). You only need to run `source .env` once per terminal; it exports `JWT_SECRET` (and optional vars) for that shell.

**Summary and Insights (Python)** load `journal-companion/.env` automatically when they start, so they pick up `JWT_SECRET` from the project `.env` even if you don’t run `source .env` in those terminals. Auth and Journal still need the env in their shell (or set in your IDE for Journal).

## 3. Start services (order)

**Who generates the JWT:** Only the **Auth Service** creates JWTs (when the user signs up or logs in). Journal, Insights, and Summary **only verify** the token with the same `JWT_SECRET`. So **start Auth first** (or at least have it running) before you open the app and sign up or log in.

**Recommended order:** 1 → Auth, 2 → Journal, 3 → Prompt, 4 → Consumer, 5 → Insights, 6 → Summary, 7 → Frontend. (Auth must be up before users log in; others can start in parallel once infra is up.)

**Terminal 1 – Auth Service** (start first; signup/login won’t work until Auth is running)

```bash
source .env
cd auth-service
npm install
PORT=3001 npm start
```

**Auth persistence:** Accounts are stored in `auth-service/data/users.json` so they survive Auth Service restarts. Set `AUTH_DATA_DIR` to use a different path. Do not commit `auth-service/data/` (it contains user data).

**Terminal 2 – Journal Service**

```bash
source .env
cd journal-service
mvn spring-boot:run
# Or run JournalServiceApplication from your IDE (set JWT_SECRET in env there too)
```

**Terminal 3 – Prompt Service**

```bash
source .env
cd prompt-service
pip install -r requirements.txt
JOURNAL_SERVICE_URL=${JOURNAL_SERVICE_URL:-http://localhost:8080} PORT=8000 python main.py
```

**Terminal 4 – AI consumer + Analytics DB**

```bash
source .env
cd ai-services
pip install -r requirements.txt
python -c "from db import init_db; init_db()"
python consumer.py
```

**Terminal 5 – Insights API**

```bash
source .env
cd ai-services
ANALYTICS_DB_URL=${ANALYTICS_DB_URL:-postgresql://analytics:analytics_secret@localhost:5433/analytics_db} PORT=8001 python insights_api.py
```

**Terminal 6 – Summary Service**

```bash
source .env
cd ai-services
ANALYTICS_DB_URL=${ANALYTICS_DB_URL:-postgresql://analytics:analytics_secret@localhost:5433/analytics_db} PORT=8002 python summary_service.py
```

**Terminal 7 – Frontend**

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

## 4. Demo flow

1. Sign up (e.g. email + password).
2. **Today**: **Quick check-in (1 min)** – Toggle "Quick check-in (1 min)" for a minimal flow: one prompt, mood slider (Rough → Great), and a short text area ("One line is enough."). Saves to the same journal; no follow-up prompts. **Full journal** – Pre-entry nudge, rotating suggestions, mood chips (Calm, Anxious, Grateful, etc.); write an entry, click Save. **Post-entry** – After save you see a streak message and 2 reflection prompts ("Want to go deeper?"). Mood is shown in **History** and **Dashboard**. First-time users with no entries see a short onboarding modal.
3. **History**: See your past entries (date + content only).
4. Wait a few seconds (consumer processes the event).
5. **Dashboard** – **Private Sentiment & Theme Analysis**: Range filter **7 / 30 / 90 days** and time-of-day (All / Morning / Afternoon / Evening). **Suggested actions** — short, actionable steps based on your entries (e.g. self-care when themes are heavy, day-of-week patterns). **Mood trend** — chart of mood tags over time from journal entries. **Stress & emotions over time** — emotions detected per day. **Sentiment over time** — bar chart (green/red/gray/purple). **Top themes & recurrence** — themes with entry counts. **Theme → sentiment breakdown** — table of each theme’s low/neutral/high sentiment counts. **Themes by mood** (tougher vs brighter days) and **Patterns** (e.g. lower on Mondays). With Ollama, analysis runs on-device for privacy.
6. **Summary**: **Reflection summaries** — reflect patterns, describe (not diagnose), highlight awareness (not advice). **Daily** — one short reflection on today’s entries. **Weekly** — structured: header (“Your Week in Reflection”), emotional snapshot (1–2 lines from sentiment + emotions), recurring themes (2–3 bullets with day names), gentle connections (“On days you mentioned X, your entries tended to feel lighter”), reflection questions (1–2, no advice). **Monthly** — header (“Your Month in Reflection”), overall tone, theme evolution (early vs later month), notable patterns, progress highlight (strength-based), looking-ahead question. Tone rules: “You often mentioned…”, “It seems like…”; never “You should…”, “You need to…”. Generate daily/weekly/monthly from the Summary page; latest is stored and shown by period.

**Test data (30 days):** To add 30 days of sample entries and sentiment/themes for Dashboard, Summary, and weekly/monthly insights, see **scripts/README.md**. Replace the placeholder user ID in `scripts/seed-journal.sql` and `scripts/seed-analytics.sql` with your user UUID (from signup response or JWT `sub`), then run the two SQL scripts against journal_db and analytics_db.

**Suggested actions (how they're calculated):** The Dashboard "Suggested actions" are **pattern-based, not a judgment**. (1) **Theme + low sentiment** — If a theme (e.g. work stress) appears in entries where the sentiment score is below -0.2 at least twice in the range, we suggest an optional self-care step (e.g. a short break or kindness after journaling — only if it feels right). If you have at least 2 low-sentiment entries but no valid theme name, we show a generic gentle suggestion. (2) **Day of week** — If your average sentiment on a given weekday is at least 0.2 below your overall average (with at least 2 entries on that day), we suggest an optional light ritual on that day — no pressure. (3) **Theme + high sentiment** — If a theme often appears on brighter days (score > 0.2), we gently suggest leaning into it when it feels natural. Wording is intentionally non-invasive and optional.

**How to get Suggested actions to show:** (1) **Consumer must be running** — Entries are processed by the AI consumer (sentiment + themes written to the analytics DB). If the consumer isn’t running or fails, no patterns are stored. (2) **Enough data** — Use the **30 days** (or 7/90) range; you need at least 2 entries with **low sentiment** (e.g. stress, worry, tired) and/or 2+ entries on a **weekday** that tends to be harder, and/or 2+ entries with **high sentiment** (e.g. grateful, good day) that share a theme. (3) **Mix of moods** — Write some entries on tougher days and some on brighter days so the system can see “this theme shows up when you’re lower” or “this weekday is often harder.” (4) **Valid themes** — Themes are extracted from your text (keywords or LLM); avoid only very generic words so at least one meaningful theme (e.g. work, family, sleep) appears. If you still see no actions, check that the Insights API and consumer are up and that you have entries in the selected date range.

## 5. Ports summary

| Service        | Port |
|----------------|------|
| Frontend       | 3000 |
| Auth           | 3001 |
| Journal        | 8080 |
| Prompt         | 8000 |
| Insights API   | 8001 |
| Summary        | 8002 |
| PostgreSQL     | 5432 (journal), 5433 (analytics) |
| Zookeeper      | 2181 |
| Kafka          | 9092 |

## 6. Analytics DB migrations (upgrades)

If you are upgrading an existing analytics DB (e.g. after pulling Phase 2 changes: emotion tags, time-of-day), run the migration scripts **before** starting the consumer and Insights API:

```bash
psql -h localhost -p 5433 -U analytics -d analytics_db -f scripts/migrations/analytics-add-emotions.sql
psql -h localhost -p 5433 -U analytics -d analytics_db -f scripts/migrations/analytics-add-entry-reflection.sql
psql -h localhost -p 5433 -U analytics -d analytics_db -f scripts/migrations/analytics-add-entry-created-at.sql
```

New setups: `init_db()` creates tables; migrations add columns/tables for newer features. See **scripts/README.md** for details.

## 7. Troubleshooting

**“Session invalid. Please sign out and sign in again.”**

- The **Journal service** returned 401 or 403 when saving an entry, so it rejected your token. Usually this is a **JWT_SECRET mismatch**: Auth signed the token with one secret, Journal is verifying with another.
- **Fix:** Use the **same JWT_SECRET** for Auth and Journal.
  - If you start Journal from a **terminal**: run `source .env` from repo root in that terminal, then start Journal (e.g. `mvn spring-boot:run`). That way Journal gets the same `JWT_SECRET` as in `.env`.
  - If you start Journal from an **IDE** (e.g. IntelliJ): add `JWT_SECRET` to the run configuration’s environment. Set it to the same value as in your `.env` (e.g. `your-256-bit-secret-for-jwt-signing-change-in-production` or whatever you put in `.env`).
- After fixing, **sign out** in the app and **sign in again** so you get a new token; then try saving again.

**“401 Unauthorized” on Summary or Insights API**

- Start Summary (and Insights) with the **same JWT_SECRET** as Auth Service. Example in the same shell:  
  `export JWT_SECRET=your-256-bit-secret-for-jwt-signing-change-in-production`  
  then start the service. If the secret differs, token verification fails and you get 401.

**“Journal service error. Check that it is running.”**

- Journal service is reachable but returned 5xx when saving. Check:
  1. **PostgreSQL** is running and healthy: `docker-compose ps` (postgres should be “Up”). Journal service needs `journal_db` on port 5432.
  2. **Journal service** was started *after* Postgres (and Kafka). Restart journal-service so it connects to DB.
  3. **Kafka** – If Kafka (or Zookeeper) is down, saving still works; the entry is saved but the “entry.created” event is not published (AI/insights won’t see it until Kafka is up). Start Zookeeper and Kafka with `docker-compose up -d zookeeper kafka`, then restart journal-service if you need events.

**Dashboard / Summary show no data (“No sentiment data yet”, “No themes yet”)**

1. **Start Kafka and the consumer** – Dashboard and Summary read from the analytics DB. Data is written by the **AI consumer** when it processes `entry.created` events from Kafka. Start infra: `docker-compose up -d postgres postgres_analytics zookeeper kafka`. Start the consumer: `source .env && cd ai-services && python consumer.py`. You should see: `Consumer started. Waiting for entry.created events...`
2. **Trigger a new event** – Save a **new** entry on **Today**. Within a few seconds the consumer terminal should show: `Processed entry <id> for user <id>`. If you see an error instead, fix it (e.g. missing DB column → run migrations in scripts/migrations/).
3. **Check analytics DB** – Your user id is the JWT `sub`. Check: `psql -h localhost -p 5433 -U analytics -d analytics_db -c "SELECT user_id, COUNT(*) FROM sentiment_result GROUP BY user_id;"` If your user_id has 0 rows, the consumer never wrote (events not received or processing failed).
4. **Restart Journal after Kafka** – If Kafka was down when Journal started, restart Journal, then save a new entry.
5. **Run analytics migrations** – If the consumer logs a missing table/column error, run scripts in `scripts/migrations/` (see scripts/README.md), then restart the consumer.

## 8. Optional: LLM (prompts, summaries, reflections)

The app uses a **generic LLM layer** so you can plug in any OpenAI-compatible provider (OpenAI, Ollama, or others). Same env vars work for **Prompt Service** and **ai-services** (one `.env` for both).

**Option A – OpenAI (cloud, paid)**

In `.env` (or in the shell before starting services):

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
# Optional: OPENAI_BASE_URL (e.g. for Groq), OPENAI_MODEL (default gpt-3.5-turbo)
```

**Option B – Ollama (local, free)**

1. Install [Ollama](https://ollama.com) and pull a model: `ollama pull llama3.2`
2. In `.env`:

```bash
LLM_PROVIDER=ollama
# Optional: OLLAMA_BASE_URL=http://localhost:11434/v1, OLLAMA_MODEL=llama3.2
```

You can omit `LLM_PROVIDER` and **auto-detect**: if `OPENAI_BASE_URL` contains `11434` or `OLLAMA_BASE_URL` is set, Ollama is used; else if `OPENAI_API_KEY` is set, OpenAI is used.

**Run it now (Ollama step-by-step)**

1. **Install Ollama** (if not already):
   - macOS: [ollama.com](https://ollama.com) → Download, or `brew install ollama`
   - Linux: `curl -fsSL https://ollama.com/install.sh | sh`
   - Or use the installer from [ollama.com](https://ollama.com).

2. **Start Ollama** (it runs in the background; API on `http://localhost:11434`):
   ```bash
   ollama serve
   ```
   Leave this running in a terminal, or start the Ollama app from the menu so it runs in the background.

3. **Pull a model** (one-time; ~2GB for llama3.2):
   ```bash
   ollama pull llama3.2
   ```
   Other options: `ollama pull mistral`, `ollama pull llama3.1`, etc.

4. **Point the app at Ollama** – in your repo-root `.env` add (and keep your existing `JWT_SECRET`, etc.):
   ```bash
   LLM_PROVIDER=ollama
   ```
   If Ollama is on another host/port: `OLLAMA_BASE_URL=http://your-host:11434/v1`. Default model is `llama3.2`; override with `OLLAMA_MODEL=mistral` (or whatever you pulled).

5. **Start the app** – from repo root, load env and start services as in §3 (Auth, Journal, Prompt, Consumer, Insights, Summary, Frontend). Use `source .env` in each terminal before starting Prompt Service and ai-services so they see `LLM_PROVIDER=ollama`.
   - Prompt Service and ai-services will call `http://localhost:11434/v1` for prompts, follow-ups, sentiment, themes, reflections, and summaries.

**Verify Ollama is working**

1. **Ollama itself** – check the server and model list:
   ```bash
   curl -s http://localhost:11434/v1/models
   ```
   You should see JSON listing your pulled model(s). If connection refused, start Ollama (`ollama serve` or open the Ollama app).

2. **App → Ollama** – from repo root, run the check script (uses same LLM config as Prompt Service):
   ```bash
   source .env
   ./scripts/verify-ollama.sh
   ```
   Or manually:
   ```bash
   source .env
   cd prompt-service && python -c "
   from llm import is_available, chat
   print('LLM available:', is_available())
   r = chat([{'role':'user','content':'Reply with one word: OK'}], max_tokens=5)
   print('Response:', r or '(none)')
   "
   ```
   You should see `LLM available: True` and a short response. If `False` or `(none)`, check `LLM_PROVIDER=ollama` in `.env` and that Ollama is running.

3. **In the app** – open **Today**, write and save an entry; after save you should see a follow-up prompt under "Want to go deeper?" (from Ollama). If you only see generic fallbacks, the Prompt Service may not have `LLM_PROVIDER=ollama` in its environment (restart it after `source .env`).

**What uses the LLM**

- **Prompt Service** – **Pre-entry nudge**: "today" prompt references recurring themes from recent entries (e.g. "You've mentioned work a few times this week. Want to write about how it felt today?"). **Post-entry**: 2 reflection prompts after save – the AI reads what they wrote and suggests two context-aware questions (different angles). Keyword fallback when the LLM is unavailable or fails.
- **ai-services** – sentiment (LLM path), themes, weekly summary, one-line reflection per entry.

Without any LLM configured, keyword-based sentiment and fallback prompts/summaries still work.

**Weekly summary stuck or 500 after long wait (Ollama)**  
Ollama can be slow on long prompts (e.g. weekly summary). The app uses a 90s timeout for the summary LLM then falls back to instant summary. If you want the LLM summary to have more time, set `SUMMARY_LLM_TIMEOUT=120` in `.env`. If Ollama returns 500, try a smaller model or more RAM.

**Faster Ollama responses**

To get replies in seconds instead of minutes:

1. **Use a smaller/faster model** – In `.env` set `OLLAMA_MODEL` to one of these (pull first with `ollama pull <name>`):
   - **smollm2:1.7b** – very fast, good for short answers (~1.7B params).
   - **llama3.2:3b** – fast, decent quality (`ollama pull llama3.2:3b`).
   - **phi3:mini** – small and quick.
   - **tinyllama** – fastest, ~1.1B params (~638MB).
   Larger models (e.g. llama3.1:8b) are slower; use them only if you have a strong GPU.

2. **Use the GPU** – On Mac with Apple Silicon or a machine with an NVIDIA GPU, Ollama uses it by default and is much faster. On Linux you may need `ollama run` with the right drivers.

3. **More CPU threads (CPU-only)** – Before starting Ollama, set:
   ```bash
   export OLLAMA_NUM_THREADS=8
   ollama serve
   ```
   Use a number close to your CPU core count.

4. **Keep the model loaded** – Ollama unloads models after a few minutes of inactivity. To avoid the first request being slow, either keep using the app or set a longer keep-alive (see Ollama docs).
