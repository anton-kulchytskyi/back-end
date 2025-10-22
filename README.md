# 🚀 FastAPI Application

## 📁 Project Overview

This project is a basic **FastAPI** setup following best practices.
It includes an organized module structure (`config`, `core`, `db`, `routers`, `schemas`, `services`, `utils`) and a simple **health check endpoint** for testing.
The application is fully containerized using **Docker** for easy local development and deployment.

### 🧩 Project Structure

```
/
├── app/
│ ├── config/
│ │ ├── constants.py
│ │ └── cors.py
│ ├── core/
│ ├── db/
│ ├── routers/
│ │ └── health.py
│ ├── schemas/
│ ├── services/
│ ├── utils/
│ └── main.py
├── tests/
│ └── test_health.py
├── .dockerignore
├── .env.sample
├── Dockerfile
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

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate     # Windows
source .venv/bin/activate  # macOS / Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```


## ▶️ Run the Application locally

Start the FastAPI app with **Uvicorn** (auto-reload enabled):

```bash
uvicorn app.main:app --reload
```

Then open your browser at:
👉 [http://127.0.0.1:8000](http://127.0.0.1:8000)


## 🧪 Run Tests

To execute tests using **pytest**:

```bash
pytest
```

## 🐳 Run with Docker

### 1. Build the Docker image

```bash
docker build -t fastapi-app .
```

### 2. Run the container

```bash
docker run -d -p 8000:8000 fastapi-app
```

Then visit:
👉 [http://localhost:8000](http://localhost:8000)

### 3. Stop the container

List running containers:

```bash
docker ps
```

Then stop it by container ID or name:

```bash
docker stop <container_id>
```


