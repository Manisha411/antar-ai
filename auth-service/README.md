# Auth Service

Simple Auth Service for the AI-Powered Journaling Companion. Sign-up and login return a JWT; `sub` claim is the userId used by Journal Service and others.

## Run

```bash
npm install
npm start
```

Port: **3001** (or set `PORT`).

## API

- **POST /api/v1/auth/signup** – body: `{ "email": "...", "password": "..." }` → `{ token, userId, email }`
- **POST /api/v1/auth/login** – body: `{ "email": "...", "password": "..." }` → `{ token, userId, email }`
- **GET /health** – health check

Use `Authorization: Bearer <token>` when calling Journal Service and other backend APIs.
