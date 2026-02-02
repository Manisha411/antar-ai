# One-click run for Journal Companion
# Prerequisites: Docker, Java 17, Node 18+, Python 3.10+
# Copy .env.example to .env and set JWT_SECRET before 'make up'.

.PHONY: up down build

up:
	bash scripts/start-all.sh

down:
	bash scripts/stop-all.sh

# Install all dependencies only (no start). Useful before first 'make up'.
build:
	cd auth-service && npm install && cd ../frontend && npm install
	cd prompt-service && pip install -r requirements.txt
	cd ai-services && pip install -r requirements.txt
