# Qoach — Backend

A production-ready **FastAPI** backend for a corporate quiz and analytics platform. Built as an internship project with a focus on clean architecture, async performance, and real-world deployment.

**Live API:** https://back-end-production-4466.up.railway.app
**Swagger UI:** https://back-end-production-4466.up.railway.app/docs

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.119 + Uvicorn |
| Database | PostgreSQL (asyncpg, SQLAlchemy 2.0 async) |
| Migrations | Alembic |
| Cache | Redis |
| Auth | JWT (access + refresh tokens), Auth0 support |
| Real-time | WebSockets |
| Scheduling | APScheduler |
| File I/O | openpyxl (Excel import/export) |
| Config | Pydantic Settings v2 |
| Testing | pytest + pytest-asyncio, aiosqlite (in-memory) |
| CI/CD | GitHub Actions (CI) + Railway (CD) |
| Containerization | Docker + Docker Compose |

---

## Features

### Users & Authentication
- Registration and login with JWT (access + refresh tokens)
- Auth0 integration support
- Profile update and account deletion

### Company Management
- Create and manage companies with role-based access (Owner / Admin / Member)
- Invitation system: owners invite users; users can also send join requests
- Admin appointment and removal
- Cascade deletion of all company data on company delete

### Quiz System
- Create quizzes with multiple questions (2–4 answers each, 1+ correct)
- Public quiz view (hides correct answers) vs. admin view (shows all)
- **Excel import** — bulk create or update quizzes from `.xlsx` files
- **Export** user or company quiz data to JSON or CSV

### Quiz Attempts & Analytics
- Submit quiz attempts with automatic score calculation
- User analytics: overall rating, per-quiz averages, last completion timestamps
- Company analytics: per-user averages, per-quiz breakdowns, last attempt tracking
- Date range filtering on all analytics endpoints

### Notifications
- In-app notifications (e.g., new quiz created in your company)
- **Real-time delivery via WebSocket**
- Mark individual or all notifications as read

### Scheduled Jobs
- Daily quiz reminders sent to company members at midnight (APScheduler cron)

---

## Architecture

```
app/
├── config/          # Pydantic Settings (database, redis, auth, app)
├── core/            # DB engine, Redis client, logger, exceptions, WebSocket manager
├── db/              # SQLAlchemy models + repositories (Repository Pattern)
├── schemas/         # Pydantic request/response schemas
├── services/        # Business logic (Service Layer)
├── routers/         # FastAPI route handlers
└── main.py          # App factory, middleware, scheduler setup
```

Key patterns used:
- **Repository Pattern** — each model has a dedicated repository with typed queries
- **Unit of Work** — atomic transactions across multiple repositories via a single session
- **Dependency Injection** — services and UoW injected via FastAPI `Depends()`
- **Async first** — all DB and Redis operations are fully async

---

## API Overview

| Resource | Endpoints |
|---|---|
| Auth | `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, `POST /auth/refresh` |
| Users | `GET /users`, `GET /users/{id}`, `PUT /users/me`, `DELETE /users/me` |
| Companies | Full CRUD + member/admin/invitation/request management |
| Quizzes | Full CRUD + Excel import + export |
| Quiz Attempts | Submit attempt, user statistics, history |
| Analytics | Company-level and user-level dashboards |
| Notifications | List, mark as read, WebSocket stream |
| Health | `GET /health/db`, `GET /health/redis`, `GET /health/all` |

Full interactive documentation: [/docs](https://back-end-production-4466.up.railway.app/docs)

### Health Endpoints

| Endpoint | Description |
|---|---|
| `GET /` | Basic liveness check — confirms the app is running |
| `GET /health/db` | PostgreSQL connectivity check (`SELECT 1`) |
| `GET /health/redis` | Redis connectivity check (`PING`) |
| `GET /health/all` | Combined check: DB + Redis in one call, with environment info |

`GET /health/all` returns a unified response showing the status, source environment, and resolved host for each service:

```json
{
  "status": "ok",
  "database": {
    "status": "ok",
    "source": "local",
    "host": "localhost"
  },
  "redis": {
    "status": "ok",
    "source": "local",
    "host": "localhost"
  }
}
```

`source` is `"local"` when connecting to Docker Compose services, and `"railway"` when connecting to managed Railway infrastructure. `status` at the top level is `"ok"` when both services are healthy, or `"degraded"` if either fails (with an `"error"` field added to the failing service).

---

## Local Development

### Prerequisites
- Docker + Docker Compose
- Python 3.13

### 1. Clone and configure

```bash
git clone <repo-url>
cd back-end
cp .env.sample .env
```

### 2. Run with Docker Compose (recommended)

```bash
docker-compose up --build
```

App available at: http://localhost:8000

### 3. Run locally (without Docker app container)

Start only databases:
```bash
docker-compose up postgres redis
```

Install dependencies and pre-commit hooks:
```bash
pip install -r requirements-dev.txt
pre-commit install
```

Run the app:
```bash
python -m app.main
```

---

## Database Migrations

```bash
# Generate migration from model changes
docker exec -it fastapi_app alembic revision --autogenerate -m "description"

# Apply all pending migrations
docker exec -it fastapi_app alembic upgrade head

# Revert last migration
docker exec -it fastapi_app alembic downgrade -1
```

---

## Testing

```bash
# Run all tests
python -m pytest --tb=short -q

# With verbose output
pytest tests/ -v
```

Tests use an **in-memory SQLite database** (aiosqlite) and mocked Redis — no external services needed.
CI runs automatically on every pull request and push to `main`/`develop` via GitHub Actions.

---

## Deployment

The application is deployed on **Railway** with managed PostgreSQL and Redis.

Environment variables required for production:

| Variable | Description |
|---|---|
| `DATABASE_URL` | Full PostgreSQL connection string (Railway injects automatically) |
| `REDIS_URL` | Full Redis connection string (Railway injects automatically) |
| `DATABASE_SSL` | Set to `True` for Railway PostgreSQL |
| `SECRET_KEY` | JWT signing secret |
| `REFRESH_SECRET_KEY` | JWT refresh signing secret |
| `BACKEND_CORS_ORIGINS` | Comma-separated list of allowed frontend origins |

On startup, the container runs `alembic upgrade head` before launching the app (`start.sh`).
