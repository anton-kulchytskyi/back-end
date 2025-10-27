# 🚀 FastAPI Application

## 📁 Project Overview

This project is a basic **FastAPI** setup following best practices.
It includes an organized module structure (`config`, `core`, `db`, `routers`, `schemas`, `services`, `utils`) and a simple **health check endpoint** for testing.
The application is fully containerized using **Docker** and **Docker Compose** with **PostgreSQL** and **Redis** databases.

### 🧩 Project Structure

```
/
├── app/
│   ├── config/
│   │   └── settings.py
│   ├── core/
│   │   ├── database.py
│   │   └── redis.py
│   ├── db/
│   ├── routers/
│   │   └── health.py
│   ├── schemas/
│   ├── services/
│   ├── utils/
│   └── main.py
├── tests/
│   └── test_health.py
├── .dockerignore
├── .env.sample
├── docker-compose.yml
├── Dockerfile
├── start.sh
├── pytest.ini
├── README.md
└── requirements.txt
```

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

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

## ▶️ Run the Application

### With Docker Compose (Recommended)

Start all services (PostgreSQL, Redis, FastAPI):

```bash
docker-compose up --build
```

Then open your browser at:
👉 [http://localhost:8000](http://localhost:8000)

### Locally (without Docker)

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

## 🧪 Run Tests

To execute tests using **pytest**:

```bash
pytest
```

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