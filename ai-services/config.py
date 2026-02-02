import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from repo root (journal-companion/.env) so JWT_SECRET is shared
_repo_root = Path(__file__).resolve().parent.parent
load_dotenv(_repo_root / ".env")
# Then cwd so ai-services/.env can override
load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC_ENTRY_CREATED = os.getenv("KAFKA_TOPIC_ENTRY_CREATED", "journal.entry.created")

ANALYTICS_DB_URL = os.getenv(
    "ANALYTICS_DB_URL",
    "postgresql://analytics:analytics_secret@localhost:5433/analytics_db"
)

# LLM: use ai_services.llm (get_client, get_model, is_available, chat). Configure via LLM_PROVIDER=openai|ollama and provider env vars.
