# 🚀 FastAPI Application

## 📁 Project Overview

This is a **production-ready FastAPI backend** with modern authentication, database integration, and scalable architecture.
The application is fully containerized using **Docker** and **Docker Compose** with **PostgreSQL** and **Redis** databases.

### ✨ Key Features

- **🔐 Dual Authentication System**
- **💾 Database Integration**
- **🏗️ Clean Architecture**
- **🧪 Comprehensive Testing**
- **🐳 Full Containerization**

-----

## ⚙️ Setup Instructions

### 1. Clone the repository

```bash
git clone <repo-url>
cd back-end
```

### 2. Create environment file

```bash
cp .env.sample .env
# Edit .env if needed
```

### 3. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/Scripts/activate     # Windows
source .venv/bin/activate         # macOS / Linux
```

### 4. Install dependencies and activate code quality hooks

Install core and development dependencies (including pre-commit, Ruff, Black, and isort):

```bash
pip install -r requirements-dev.txt
```

Next, activate the Git pre-commit hooks

```bash
pre-commit install
```

### 5a. With Docker Compose (Recommended)

Start all services (PostgreSQL, Redis, FastAPI):

```bash
docker-compose up --build
```

Then open your browser at:
👉 [http://localhost:8000](http://localhost:8000)

### 5b. Locally (without Docker)

Start databases only:

```bash
docker-compose up postgres redis
```

Update `.env` for local development:
```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/fastapi_db
REDIS_URL=redis://localhost:6379/0
```

Run the application:

```bash
python -m app.main
```

-----

## 💾 Database Migrations (Alembic)

Database schema changes are managed using **Alembic**. All migration commands must be executed **inside the `fastapi_app` container** to ensure the correct environment and dependencies are used.

### 1. Generate a new migration script

Use `alembic revision --autogenerate` to automatically detect changes in your SQLAlchemy models and generate a new migration file.

```bash
docker exec -it fastapi_app alembic revision --autogenerate -m "descriptive_message_here"
```

### 2. Apply migrations

Use `alembic upgrade` to apply all pending migration scripts to the database.

```bash
docker exec -it fastapi_app alembic upgrade head
```

### 3. Downgrade migrations

To revert the last applied migration:

```bash
docker exec -it fastapi_app alembic downgrade -1
```

### 4. Check current database version

```bash
docker exec -it fastapi_app alembic current
```

-----


## 🧪 Run Tests

To execute tests using **pytest**:

```bash
pytest tests/ -v
```

-----

## 🐳 Docker Commands

### Start all services
```bash
docker-compose up --build
```

### Start in detached mode
```bash
docker-compose up -d
```

### View logs
```bash
docker-compose logs -f app
```

### Stop all services
```bash
docker-compose down
```

### Remove volumes (⚠️ deletes data)
```bash
docker-compose down -v
```

### Access PostgreSQL
```bash
docker exec -it fastapi_postgres psql -U postgres -d fastapi_db
```

### Access Redis CLI
```bash
docker exec -it fastapi_redis redis-cli
```
