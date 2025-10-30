# 🚀 FastAPI Application

## 📁 Project Overview

This project is a basic **FastAPI** setup following best practices.
It includes an organized module structure (`config`, `core`, `db`, `models`, `routers`, `schemas`, `services`, `utils`) and a simple **health check endpoint** for testing.
The application is fully containerized using **Docker** and **Docker Compose** with **PostgreSQL** and **Redis** databases.

### 🧩 Project Structure

```
/
├── alembic/
├── app/
│   ├── config/
│   │   └── settings.py
│   ├── core/
│   │   ├── database.py
│   │   └── redis.py
│   ├── db/
│   │   └── base.py
│   ├── models/
│   │   └── user.py
│   ├── routers/
│   │   └── health.py
│   ├── schemas/
│   │   └── user.py
│   ├── services/
│   ├── utils/
│   └── main.py
├── tests/
│   └── test_health.py
├── .dockerignore
├── .env.sample
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── pytest.ini
├── README.md
├── requirements-dev.txt
├── requirements.txt
└── start.sh
```

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
pytest
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



Це чудова і дуже важлива таска\! Додавання міграцій Alembic значно підвищує професійний рівень вашого проєкту.

Я адаптував ваш `README.md`, додавши новий розділ **Database Migrations (Alembic)**, який детально описує, як керувати міграціями, що є ключовим елементом вашого завдання.

-----

## Адаптований `README.md`

```markdown
# 🚀 FastAPI Application

## 📁 Project Overview

This project is a basic **FastAPI** setup following best practices.
It includes an organized module structure (`config`, `core`, `db`, `routers`, `schemas`, `services`, `utils`) and a simple **health check endpoint** for testing.
The application is fully containerized using **Docker** and **Docker Compose** with **PostgreSQL** and **Redis** databases.

### 🧩 Project Structure

```

/
├── alembic/              \# NEW: Alembic migration environment
├── app/
│   ├── config/
│   │   └── settings.py
│   ├── core/
│   │   ├── database.py
│   │   └── redis.py
│   ├── db/
│   │   └── models/       \# NEW: Where SQLAlchemy models (like User) reside
│   ├── routers/
│   │   └── health.py
│   ├── schemas/          \# NEW: Pydantic schemas (User, SignUp, etc.)
│   ├── services/
│   ├── utils/
│   └── main.py
├── tests/
│   └── test\_health.py
├── .dockerignore
├── .env.sample
├── docker-compose.yml
├── Dockerfile
├── start.sh
├── pytest.ini
├── alembic.ini           \# NEW: Alembic configuration file
├── README.md
├── requirements-dev.txt
└── requirements.txt

````

## ⚙️ Setup Instructions

### 1. Clone the repository

```bash
git clone <repo-url>
cd back-end
````

### 2\. Create environment file

```bash
cp .env.sample .env
# Edit .env if needed
```

### 3\. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/Scripts/activate     # Windows
source .venv/bin/activate         # macOS / Linux
```

### 3\. Install dependencies and activate code quality hooks

Install core and development dependencies (including pre-commit, Ruff, Black, and isort):

```bash
pip install -r requirements-dev.txt
```

Next, activate the Git pre-commit hooks

```bash
pre-commit install
```

### With Docker Compose (Recommended)

Start all services (PostgreSQL, Redis, FastAPI):

```bash
docker-compose up --build
```

Then open your browser at:
👉 [http://localhost:8000](https://www.google.com/search?q=http://localhost:8000)

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

-----

## 💾 Database Migrations (Alembic)

Database schema changes are managed using **Alembic**. All migration commands must be executed **inside the `fastapi_app` container** to ensure the correct environment and dependencies are used.

### 1\. Generate a new migration script

Use `alembic revision --autogenerate` to automatically detect changes in your SQLAlchemy models and generate a new migration file.

```bash
docker exec -it fastapi_app alembic revision --autogenerate -m "descriptive_message_here"
```

### 2\. Apply migrations

Use `alembic upgrade` to apply all pending migration scripts to the database.

```bash
docker exec -it fastapi_app alembic upgrade head
```

### 3\. Downgrade migrations

To revert the last applied migration:

```bash
docker exec -it fastapi_app alembic downgrade -1
```

### 4\. Check current database version

```bash
docker exec -it fastapi_app alembic current
```

-----

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

````

---

## 📝 Коміт за Конвенцією

Оскільки ваше завдання охоплювало створення моделей, схем та налаштування міграцій, відповідний тип коміту — це **`feat`** (feature).

Використовуйте цю команду для створення коміту (з англійською мовою):

```bash
git commit -m "feat(auth): add User model, Pydantic schemas, and Alembic migrations setup"
````

### Пояснення

  * **`feat`**: Вказує, що це нова функціональність або можливість.
  * **`(auth)`**: Необов'язкова область (scope), яка вказує, що зміни стосуються підсистеми **аутентифікації** або **користувачів**.
  * **`add User model, Pydantic schemas, and Alembic migrations setup`**: Короткий і чіткий опис того, що було зроблено.

Цей коміт охоплює всі ключові аспекти вашого завдання (моделі, схеми, міграції) і відповідає загальноприйнятим конвенціям комітів.