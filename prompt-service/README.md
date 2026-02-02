# Prompt Service

Returns a context-aware "today" prompt for journaling. Calls Journal Service for recent entries and uses OpenAI (if `OPENAI_API_KEY` is set) or a keyword-based fallback.

## Run

```bash
pip install -r requirements.txt
JOURNAL_SERVICE_URL=http://localhost:8080 python main.py
```

Port: **8000**. Optional: `OPENAI_API_KEY` for LLM-generated prompts.

## API

- **GET /api/v1/prompts/today** – Header: `Authorization: Bearer <token>`. Returns `{ "prompt": "..." }`.
