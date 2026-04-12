# 🗣️ Talk to Data + Database Speaks

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Docker support](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-Apache_2.0-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/Apache-2.0)

A powerful, conversational analytics system that empowers anyone to ask plain-English questions about uploaded datasets (CSV/Excel) or live SQL databases and receive clear, actionable answers along with auto-generated charts.

Built for the **NatWest Group Code for Purpose – India Hackathon**.

---

## 📖 Overview

Many people struggle to get quick, accurate, and trustworthy answers from their data. They face too many steps, confusing terminology, and lack of confidence in the results context.

**Talk to Data + Database Speaks** eliminates that friction. Whether you upload a CSV/Excel file or connect directly to a production MySQL database, you can simply ask a question the way you would ask a colleague. In return, you get:
- A plain-English answer summarizing the findings.
- An auto-generated visual chart (when applicable).
- A transparent reference indicating exactly which columns and filters produced the result.

The system is built around a **multi-agent data analyst pipeline** that understands business terminology, resolves ambiguous time expressions, detects anomalies, forecasts trends, segments data, and translates text to SQL — all seamlessly and safely.

**Intended users:** Non-technical business users, analysts, and team leads who need fast, trustworthy answers from data without learning SQL, Python, or writing complex queries.

---

## ✨ Key Features

- 🧠 **Natural Language Querying** — Ask questions exactly as you would say them.
- 🔀 **Dual Chat Modes**:
  - **Dataset Mode (`/upload` + `/query`)**: Talk dynamically to any uploaded CSV or Excel file via an intelligent Python/Pandas agent.
  - **SQL Mode (`/db/chat`)**: Talk directly to your live MySQL databases using a specialized, stateful LangChain SQL agent.
- 🎯 **Intent Classification** — Automatically routes questions to the right analytical module (compare, breakdown, what changed, summarize, statistical models).
- 📚 **Semantic Layer** — Configuration via `metrics.yaml` maps abstract business terms (e.g., "revenue" or "churn") to exact column definitions, ensuring consistent results across all queries.
- 🔍 **Source Transparency** — Every answer shows exactly which columns and filters produced it, building trust.
- ⏳ **Ambiguity Resolution** — Vague phrases like "this month" and "last week" are instantly resolved to concrete date ranges before analysis begins.
- 🧮 **Data Science Agents** — Deep analytical operations including anomaly detection (Z-score, IQR, Isolation Forest), time-series forecasting (ARIMA), and customer segmentation (KMeans).
- 📊 **Auto Chart Selection** — Automatically picks the right chart type (bar, line, scatter, pie) based on the shape of the result and returns an embedded Base64 image.
- 🛡️ **PII Safety Layer** — Raw sensitive data (customer IDs, emails) is automatically sanitized and never exposed to the LLM or returned to the user.
- 🔐 **Code Safety Guard** — All LLM-generated Python code for dataset analysis is statically scanned for dangerous patterns before safe execution.
- 🐳 **Docker & Hugging Face Ready** — Fully dockerized with an unprivileged user setup, ready for instant deployment to Hugging Face Spaces (Port 7860).

---

## 🛠️ Tech Stack

- **Backend:** Python 3.10+, FastAPI, Uvicorn, SQLAlchemy
- **AI / LLM:** Google Gemini (Flash-Lite Preview), LangChain
- **Data Processing:** Pandas, NumPy
- **Data Science:** scikit-learn (Isolation Forest, KMeans), statsmodels (ARIMA)
- **Configuration:** PyYAML (Semantic layer)
- **Containerization:** Docker

---

## 🚀 Install and Run

### Prerequisites

- Python 3.10 or higher
- An API key for Google Gemini (Get a free tier key at [Google AI Studio](https://aistudio.google.com/app/apikey))
- *Optional:* Docker Desktop

### 1. Clone the repository

```powershell
git clone <your-repo-url>
cd PurposePredict_T2Data
```

### 2. Configure Environment

Create a `.env` file in the root directory:

```env
# Required for both dataset and SQL chat modes
GOOGLE_API_KEY=your-gemini-key-here

# Optional aliases supported by the app
GEMINI_API_KEY=your-gemini-key-here

# Optional model override
GOOGLE_MODEL=gemini-2.5-flash-lite-preview

# Optional custom port for local run
PORT=8000
```

### 3. Set up locally (Without Docker)

```powershell
# Create virtual environment and install dependencies
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux

pip install -r requirements.txt

# Start the API server
python main.py
```
The API will be available at `http://localhost:8000`. You can explore all endpoints via the Swagger UI at `http://localhost:8000/docs`.

### 4. Run via Docker (Ready for Hugging Face Spaces)

```powershell
# Build the image
docker build -t talk-to-data-api .

# Run the container locally map port 7860 to 7860
docker run -p 7860:7860 --env-file .env talk-to-data-api
```
The API will be automatically accessible on port `7860`.

---

## 🔌 Comprehensive API Endpoints

### 📁 Dataset Chat Mode

#### **`POST /upload`**
Uploads a dataset to be processed in memory.
- **Input:** `multipart/form-data` with a `.csv` or `.xlsx` file.
- **Behavior:** Auto-detects schema, handles session creation, applies PII sanitization to previews.
- **Returns:** `session_id`, filename, row count, column structure, and a safe data preview.

#### **`POST /query`**
Ask a natural language question about the uploaded dataset.
- **Input:** JSON Body `{"session_id": "...", "question": "..."}`
- **Behavior:** Intent classification -> Agent Routing -> Python Execution -> Chart Generation.
- **Returns:** `answer` (plain English), `chart` (containing `image_b64` Base64 PNG), `source_ref` (columns utilized), and tabular `data`.

#### **`GET /chart/{session_id}/latest.png`**
Helper endpoint to render the natively generated PNG directly via an `<img src="...">` tag without managing base64 natively.

---

### 🗄️ Database Speaks Mode

#### **`POST /db/chat`**
Execute conversational natural language over a live MySQL Database (Powered by LangChain SQL Toolkit).
- **Input:** JSON Body
  ```json
  {
    "query": "Who are the top 10 customers by total spend in 2025?",
    "mysql_host": "localhost",
    "mysql_user": "root",
    "mysql_password": "your-password",
    "mysql_db": "sales_db",
    "mysql_port": "3306"
  }
  ```
- **Behavior:** Securely communicates with the database using SQL tooling, executes queries in the background, checks errors, automatically corrects failed queries, and sets a context-bearing HTTP-only Cookie (`db_chat_session_id`) to retain follow-up conversational history!
- **Returns:** Plain-text SQL agent `response`, generated `session_id`, and `success` boolean.

---

### ⚙️ Utility Endpoints

- **`GET /health`**: Health check, confirming the configured Gemini LLM and active features.
- **`GET /session/{session_id}`**: Validates if a dataset session exists and how many chunks of history it holds.
- **`GET /metrics`**: Serves all global semantic layer definitions mapped inside `config/metrics.yaml`.

---

## 🏗️ Project Structure

```text
PurposePredict_T2Data/
├── main.py                        # FastAPI / Uvicorn app entry point
├── Dockerfile                     # Unprivileged Docker configuration (Port 7860)
├── requirements.txt               # Python dependencies
├── agents/                        
│   ├── orchestrator.py            # Intent classifier + agent router
│   ├── analyst_agent.py           # Core Pandas analyst — generates analysis code
│   ├── ds_agent.py                # Statistical & Data Science logic
│   ├── summarizer.py              # LLM plain-English aggregation
│   └── viz_agent.py               # Auto chart-type selection & formatting
├── core/
│   ├── semantic_layer.py          # metrics.yaml query enrichment
│   ├── schema_registry.py         # Column/type/sample extraction
│   ├── session.py                 # Multi-user session & state management
│   └── safety.py                  # PII guard + code safety sandbox checker
├── config/
│   └── metrics.yaml               # Business term → column definitions
└── README.md                      # Documentation
```

---

## 🧠 Architecture Overview

### Seamless Agent Pipeline
```mermaid
User Question
      ↓
(If db/chat) ──>  LangChain SQL Agent ──> Query MySQL DB ──> Respond
      ↓
(If dataset)
Semantic Layer  →  Enriches query with specific metric definitions from `config/metrics.yaml`
      ↓
Orchestrator    →  Classifies intent (Compare / Breakdown / Trend / Summarize / Statistical Models)
      ↓
Analyst Agent   →  LLM generates Python/Pandas code → Scanned for security → Executes on in-memory DataFrame
      ↓              (or DS Agent triggers anomaly / forecast / clustering operations)
Summarizer      →  Ingests raw numerical outputs into plain English + appends source reference filters
      ↓
Viz Agent       →  Selects optimal chart structure → Returns visual Plotly/Matplotlib buffer mapped to Base64
      ↓
Frontend Response
```

### Architecture Deep Dive

**1. Semantic layer (`metrics.yaml`)**:
The core contextual differentiator. Every business term a user might type — "revenue", "sales", "turnover", "churn" — is strictly mapped to exact columns, filters, and aggregation algorithms. This ensures "revenue" *always* signifies completed transactions, preventing disparate answers based on how a question is worded.

**2. Dual Analysis Path**:
Use Pandas-centric dynamic memory execution for quick uploaded CSVs, or hook directly into live production relational tables via the specialized `SQLDatabaseToolkit` using LangChain.

**3. Data Privacy & Safety First**:
- **Sandbox execution:** Generated pandas code is subjected to strict rule-matching. Python internals like `os`, `exec`, network modules, or file path reads are immediately blocked from executing.
- **PII Concealment:** The LLM never visually touches raw sensitive details. Any detected customer IDs, granular emails, or sensitive texts are scrubbed via PII hashing before sending snippets outside the server.

---

## 🧱 Limitations

- The semantic layer (`metrics.yaml`) requires manual adjustments if the connected dataset changes primary foundational column names.
- Statistical forecasting (ARIMA) produces optimal confidence bounds when evaluating >30 distinct time series data intervals.
- Session constraints are entirely in-memory and bound by the application process lifecycle (Non-persistent on restarts/Docker container redeploys).

---

## 🔮 Future Roadmap

- Expand Data Science Agents to operate effectively against raw MySQL Queries.
- Enable cross-document operations, joining 2+ distinct dataset files on implicit keys.
- Integrate Redis for High Availability sticky sessions.
- Automatically auto-discover semantic definitions based on deep structural dataset scanning.
- Integrate role-based security & JWT OAuth flow for DB connections.

---

## 📝 License & Open-source Compliance

This project is licensed under the **Apache License 2.0**.
- Complete License text provided in the `LICENSE` file.
- Attribution notices available in `NOTICE`.

It leverages several exceptional libraries under permissive OSS licenses:
- `langchain` / `fastapi` / `pyyaml` — MIT
- `pandas` / `numpy` / `scikit-learn` / `statsmodels` — BSD
