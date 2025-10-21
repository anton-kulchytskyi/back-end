# 🚀 FastAPI Application

## 📁 Project Overview

This project is a basic **FastAPI** setup following best practices.
It includes an organized module structure (`core`, `db`, `routers`, `schemas`, `services`, `utils`) and a simple **health check endpoint** for testing.

### 🧩 Project Structure

```
app/
├── core/
├── db/
├── routers/
│   └── health.py
├── schemas/
├── services/
├── utils/
└── main.py
tests/
└── test_health.py
```

## ⚙️ Setup Instructions

### 1. Clone the repository

```bash
git clone <your-repo-url>
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


## ▶️ Run the Application

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

