# Talk to Data — Seamless Self-Service Intelligence

A conversational data analyst system that lets anyone ask plain-English questions about their data and instantly receive clear explanations, verified insights, and transparent source references — no SQL, no dashboards, no data skills required.

Built for the **NatWest Group Code for Purpose – India Hackathon**.

---

## Overview

Many people struggle to get quick, accurate, and trustworthy answers from data. They face too many steps, unclear terminology, and no confidence in the results.

**Talk to Data** removes that friction. Upload any CSV or Excel file, ask a question the way you would ask a colleague, and get back a plain-English answer with a chart and a reference to exactly which columns and filters produced it.

The system is built around a **multi-agent data analyst pipeline** that understands business terminology, resolves ambiguous time expressions, detects anomalies, forecasts trends, and segments data — all without exposing raw or sensitive data.

**Intended users:** Non-technical business users, analysts, and team leads who need fast, trustworthy answers from data without learning SQL or writing code.

---

## Features

- **Natural language querying** — ask questions exactly as you would say them
- **Intent classification** — automatically routes to the right analysis (compare, breakdown, what changed, summarise)
- **Semantic layer** — `metrics.yaml` maps business terms like "revenue" or "churn" to exact column definitions, ensuring consistent results across all queries
- **Source transparency** — every answer shows which columns and filters produced it
- **Ambiguity resolution** — "this month" and "last week" are resolved to concrete date ranges before analysis
- **Data Science agents** — anomaly detection (Z-score, IQR, Isolation Forest), time-series forecasting (ARIMA), and customer segmentation (KMeans)
- **Auto chart selection** — picks the right chart type (bar, line, scatter, pie) based on the result shape
- **PII safety layer** — raw sensitive data (customer IDs, emails) is never exposed to the LLM or returned to the user
- **Code safety guard** — all LLM-generated Python code is scanned for dangerous patterns before execution
- **Self-service dataset upload** — works with any CSV or Excel file, not just a hardcoded demo
- **Session management** — follow-up questions maintain context from the conversation history
- **LLM-agnostic** — works with OpenAI, Google Gemini, or a local Ollama model

---

## Tech stack

- **Python 3.10+**
- **FastAPI** — REST API backend
- **ai-data-science-team** — open-source agent library (MIT licence) used as the Pandas analyst engine
- **LangChain** — LLM abstraction layer
- **Pandas / NumPy** — data processing
- **scikit-learn** — anomaly detection (Isolation Forest) and clustering (KMeans)
- **statsmodels** — time-series forecasting (ARIMA)
- **PyYAML** — semantic layer configuration
- **React** (frontend) — chat interface and chart rendering
- **Plotly** (frontend) — auto-generated charts

---

## Install and run

### Prerequisites

- Python 3.10 or higher
- Node.js 18+ (for the frontend)
- An API key for your chosen LLM provider (or Ollama installed locally)

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd talk-to-data
```

### 2. Set up the backend

```bash
cd backend
pip install -r requirements.txt
```

Copy the environment template and fill in your API key:

```bash
cp ../.env.example .env
# Edit .env and set your LLM_PROVIDER and API key
```

Generate the sample dataset:

```bash
python ../sample_data/generate_data.py
```

Start the API server:

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. You can explore all endpoints at `http://localhost:8000/docs`.

### 3. Set up the frontend

```bash
cd ../frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`.

### 4. Using the app

1. Open `http://localhost:5173`
2. Upload any CSV or Excel file using the sidebar
3. Ask a question — for example:
   - *"Why did South region sales drop last month?"*
   - *"Compare revenue by region"*
   - *"Are there any unusual spikes in revenue?"*
   - *"Forecast sales for the next 7 days"*
   - *"Give me a weekly summary"*

---

## LLM configuration

Edit `.env` to choose your provider. **Gemini is the default** (free tier available at [aistudio.google.com](https://aistudio.google.com/app/apikey)).

**Google Gemini (default)**
```
LLM_PROVIDER=google
GOOGLE_API_KEY=your-key-here
GOOGLE_MODEL=gemini-1.5-flash
```

**OpenAI (alternative)**
```
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4o-mini
```

**Ollama (fully local, no API key needed)**
```bash
ollama serve
ollama pull llama3.1:8b
```
```
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1:8b
```

---

## Running tests

```bash
cd talk-to-data
python -m pytest tests/ -v
```

**74 tests** covering the semantic layer, DS agents (anomaly detection, forecasting, clustering), intent classification, safety layer, and schema registry.

---

## Project structure

```
talk-to-data/
├── backend/
│   ├── main.py                        # FastAPI app — /upload, /query endpoints
│   ├── agents/
│   │   ├── orchestrator.py            # Intent classifier + agent router
│   │   ├── analyst_agent.py           # Core analyst — wraps ai-data-science-team
│   │   ├── ds_agent.py                # Anomaly detection, forecasting, clustering
│   │   ├── viz_agent.py               # Auto chart-type selection
│   │   └── summarizer.py              # Plain-English answers + source refs
│   ├── core/
│   │   ├── semantic_layer.py          # metrics.yaml loader + query enrichment
│   │   ├── schema_registry.py         # Column/type/sample extraction
│   │   ├── session.py                 # Per-user dataframe + chat history
│   │   └── safety.py                  # PII guard + code safety checker
│   ├── config/
│   │   └── metrics.yaml               # Business term → column definitions
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx
│       └── components/
│           ├── ChatWindow.jsx
│           ├── UploadPanel.jsx
│           ├── ChartCard.jsx
│           └── SourcePanel.jsx
├── sample_data/
│   ├── generate_data.py               # Generates sales_data.csv
│   └── sales_data.csv                 # 2000-row demo dataset
├── tests/
│   ├── test_ds_agent.py
│   ├── test_semantic_layer.py
│   ├── test_orchestrator_safety.py
│   └── test_schema_registry.py
├── pytest.ini
├── .env.example
└── README.md
```

---

## Architecture

```
User question
     ↓
Semantic Layer  →  enriches query with metric definitions from metrics.yaml
     ↓
Orchestrator    →  classifies intent (compare / breakdown / what changed / summarise / DS)
     ↓
Analyst Agent   →  LLM generates Python/Pandas code → executes in sandbox → returns results
     ↓              (or DS Agent for anomaly / forecast / cluster)
Summarizer      →  turns raw numbers into plain English + appends source reference
     ↓
Viz Agent       →  picks chart type from result shape → returns Plotly spec
     ↓
Frontend        →  renders answer + chart + source panel
```

---

## Architecture notes

**Semantic layer (`metrics.yaml`)** is the core differentiator. Every business term a user might type — "revenue", "sales", "turnover", "churn" — is mapped to the exact column, filter, and aggregation method. This ensures "revenue" always means completed transactions, not gross amounts, regardless of who asks or how they phrase it.

**No SQL.** The system works entirely with Pandas on uploaded CSV/Excel files. SQL is unnecessary overhead when data comes from user uploads rather than a production database.

**PII safety.** The LLM never sees raw customer data. The safety layer strips PII columns (customer IDs, emails, etc.) before any result passes to the LLM or is returned to the user. Datasets with more than 50 rows are summarised rather than returned raw.

**Code safety.** All Python code generated by the LLM is scanned for dangerous patterns (`os`, `subprocess`, `eval`, `exec`, file access, network calls) before execution.

---

## Limitations

- The semantic layer (`metrics.yaml`) must be manually updated if the dataset has different column names from the defaults
- Forecasting works best with at least 30 data points in the time series
- The LLM fallback analyst agent requires a capable model (GPT-4o-mini or better) for reliable code generation
- Session data is stored in memory and lost on server restart (no persistent storage in this prototype)

---

## Future improvements

- Persistent storage for sessions (Redis or SQLite)
- Auto-discovery of column semantics from data samples
- Multi-dataset joins and cross-dataset queries
- User-editable metric definitions through the UI
- Streaming responses for faster perceived speed
- Role-based access control for sensitive datasets

---

## Open-source compliance

This project uses the following open-source libraries under their respective licences:

- `ai-data-science-team` — MIT
- `langchain` — MIT
- `fastapi` — MIT
- `pandas`, `numpy`, `scikit-learn`, `statsmodels` — BSD
- `pyyaml` — MIT

All commits are signed off with `git commit -s` in compliance with the Developer Certificate of Origin (DCO). A single email address is used for all commits and hackathon communication.
