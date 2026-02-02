#!/usr/bin/env bash
# Verify Ollama (or configured LLM) is reachable from the app.
# Run from repo root: ./scripts/verify-ollama.sh
# (Script loads .env from repo root if present.)

set -e
cd "$(dirname "$0")/.."
REPO_ROOT="$PWD"

# Load .env from repo root so LLM_PROVIDER=ollama is set even if you didn't source it
if [ -f "$REPO_ROOT/.env" ]; then
  set -a
  source "$REPO_ROOT/.env"
  set +a
fi

echo "1. Checking Ollama server (http://localhost:11434)..."
if curl -s -f -o /dev/null http://localhost:11434/v1/models 2>/dev/null; then
  echo "   OK – Ollama is running."
  MODELS=$(curl -s http://localhost:11434/v1/models | python3 -c "import sys,json; d=json.load(sys.stdin); print(' '.join(m.get('name','') for m in d.get('models',[])))" 2>/dev/null || echo "")
  if [ -z "$MODELS" ]; then
    echo "   Models: (none) – run: ollama pull llama3.2"
  else
    echo "   Models: $MODELS"
  fi
else
  echo "   FAIL – Cannot reach Ollama. Start it with: ollama serve"
  exit 1
fi

echo ""
echo "2. Checking app LLM config (prompt-service)..."
cd prompt-service
python3 -c "
from llm import is_available, get_model, LLM_PROVIDER
print('   LLM_PROVIDER:', LLM_PROVIDER)
print('   is_available():', is_available())
print('   model:', get_model())
if is_available():
    from llm import chat
    r = chat([{'role':'user','content':'Reply with one word: OK'}], max_tokens=5)
    print('   test response:', repr(r) if r else '(none)')
    if r:
        print('   OK – LLM is working.')
    else:
        print('   WARN – No response from model (check model name).')
else:
    print('   FAIL – LLM not available. Add LLM_PROVIDER=ollama to repo root .env')
    exit(1)
"
