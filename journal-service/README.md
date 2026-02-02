# Journal Service

Spring Boot 3 service for the AI-Powered Journaling Companion. Handles CRUD for journal entries, JWT auth, and publishes `EntryCreated` events to Kafka.

## Prerequisites

- Java 17+
- Maven 3.8+
- Docker (for PostgreSQL and Kafka)

## Run infrastructure

From the project root (`journal-companion`):

```bash
docker-compose up -d postgres rabbitmq
```

## Run the service

```bash
cd journal-service
./mvnw spring-boot:run
```

Or with explicit env (optional):

```bash
export POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=journal_db
export POSTGRES_USER=journal POSTGRES_PASSWORD=journal_secret
export RABBITMQ_HOST=localhost RABBITMQ_PORT=5672
./mvnw spring-boot:run
```

Default port: **8080**.

## API (require auth)

- **JWT**: `Authorization: Bearer <token>` (token from Auth Service, `sub` = userId).
- **Dev**: `X-User-Id: <userId>` when `ALLOW_X_USER_ID=true` (default for local).

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/entries | Create entry (body: `{"content":"..."}`) |
| GET | /api/v1/entries | List entries (query: page, size, from, to) |
| GET | /api/v1/entries/recent?limit=10 | Last N entries (for Prompt Service) |
| GET | /api/v1/entries/{id} | Get one entry |
| PUT | /api/v1/entries/{id} | Update entry |
| DELETE | /api/v1/entries/{id} | Delete entry |

### Example (with X-User-Id)

```bash
# Create entry
curl -s -X POST http://localhost:8080/api/v1/entries \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user-123" \
  -d '{"content":"Today I felt calm after a short walk."}'

# List entries
curl -s http://localhost:8080/api/v1/entries \
  -H "X-User-Id: user-123"
```

## Health

- `GET /actuator/health` – includes DB and Kafka.

## OpenAPI

- Swagger UI: http://localhost:8080/swagger-ui.html
- JSON: http://localhost:8080/v3/api-docs
