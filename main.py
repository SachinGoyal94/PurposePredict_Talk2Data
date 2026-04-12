"""
main.py — FastAPI entry point

Endpoints:
  POST /upload          Upload CSV/Excel → session_id + schema
  POST /query           NL question → answer + chart image (base64) + source ref
  POST /db/chat         NL question → SQL agent response from MySQL
  GET  /health          Health check
  GET  /session/{id}    Session info
  GET  /metrics         All metric definitions
"""
import os
import io
import base64
from urllib.parse import quote_plus
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Response as ApiResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import create_engine
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase

from core.session import get_session_store
from core.schema_registry import get_schema_registry
from core.semantic_layer import get_semantic_layer
from core.safety import sanitise_dataframe
from agents.analyst_agent import build_analyst_agent
from agents.orchestrator import Orchestrator
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().with_name(".env"))

app = FastAPI(
    title="Talk to Data API",
    description="Talk to datasets and SQL databases with natural language",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_llm():
    """Initialise Gemini LLM via LangChain."""
    from langchain_google_genai import ChatGoogleGenerativeAI

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_KEY")
    if not api_key:
        raise RuntimeError(
            "Gemini API key not found. Set GOOGLE_API_KEY or GEMINI_API_KEY in .env or your environment."
        )

    return ChatGoogleGenerativeAI(
        model=os.getenv("GOOGLE_MODEL", "gemini-2.5-flash-lite-preview"),
        api_key=api_key,
        temperature=0,
        convert_system_message_to_human=True,
    )


_llm           = None
_analyst_agent = None
_orchestrator  = None


@app.on_event("startup")
async def startup():
    global _llm, _analyst_agent, _orchestrator
    _llm           = get_llm()
    _analyst_agent = build_analyst_agent(_llm)
    _orchestrator  = Orchestrator(_analyst_agent, _llm)
    print(f"✅ Gemini ({os.getenv('GOOGLE_MODEL', 'gemini-2.5-flash-lite-preview')}) ready")


# ── Models ────────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    session_id: str
    question: str

class ChartSpec(BaseModel):
    type: str
    x_col: str
    y_col: str
    x_label: str
    y_label: str
    data: list
    image_b64: Optional[str] = None   # base64 PNG — embed as <img src="data:image/png;base64,...">

class QueryResponse(BaseModel):
    success: bool
    intent: str = ""
    answer: str
    chart: Optional[ChartSpec] = None
    source_ref: dict = {}
    data: list = []
    session_id: str


class DatabaseChatRequest(BaseModel):
    query: str
    mysql_host: str | None = None
    mysql_user: str | None = None
    mysql_password: str | None = None
    mysql_db: str | None = None
    mysql_port: str | None = None


class DatabaseChatResponse(BaseModel):
    success: bool
    session_id: str
    query: str
    response: str


def configure_db(req: DatabaseChatRequest) -> SQLDatabase:
    required = [req.mysql_host, req.mysql_user, req.mysql_password, req.mysql_db]
    if not all(required):
        raise HTTPException(status_code=400, detail="Missing MySQL connection parameters.")

    port = req.mysql_port or "3306"
    user = quote_plus(req.mysql_user or "")
    password = quote_plus(req.mysql_password or "")
    host = req.mysql_host
    db_name = req.mysql_db
    conn_str = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{db_name}"

    try:
        return SQLDatabase(create_engine(conn_str))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MySQL connection failed: {e}")


def get_sql_agent(db: SQLDatabase):
    try:
        toolkit = SQLDatabaseToolkit(db=db, llm=_llm)
        base_kwargs = {
            "llm": _llm,
            "toolkit": toolkit,
            "verbose": True,
            "handle_parsing_errors": True,
            "top_k": 20,
            "max_iterations": 30,
            "max_execution_time": 30,
            "early_stopping_method": "force",
        }
        try:
            return create_sql_agent(agent_type="tool-calling", **base_kwargs)
        except TypeError:
            # Backward compatibility for older LangChain versions.
            return create_sql_agent(**base_kwargs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent setup failed: {e}")


def _extract_agent_answer(result) -> str:
    import ast
    import re

    out = result.get("output", "") if isinstance(result, dict) else result

    if isinstance(out, str):
        # If the output string is a stringified raw dictionary/list from the LLM, 
        # normally happens when the agent uses force early_stopping and truncates.
        if out.strip().startswith("[{") and ("'text'" in out or '"text"' in out):
            try:
                out = ast.literal_eval(out)
            except Exception:
                # Handle malformed/truncated stringified lists
                matches = re.findall(r"['\"]text['\"]\s*:\s*(['\"])(.*?)\1(?:,|\})", out)
                if matches:
                    # match is a tuple (quote_char, text_content)
                    return "\n".join(m[1].replace("\\n", "\n") for m in matches)
                return out

    if isinstance(out, list):
        extracted = []
        for item in out:
            if isinstance(item, dict) and "text" in item:
                extracted.append(item["text"])
            elif hasattr(item, "text"):
                extracted.append(item.text)
            else:
                extracted.append(str(item))
        return "\n".join(extracted)

    return str(out)


def _is_output_parsing_error(err: Exception) -> bool:
    msg = str(err)
    lowered = msg.lower()
    return (
        "output_parsing_failure" in lowered
        or "could not parse llm output" in lowered
        or "output parsing error" in lowered
    )


def run_sql_agent_with_retry(agent, agent_input: str, plain_query: str) -> str:
    try:
        return _extract_agent_answer(agent.invoke({"input": agent_input}))
    except AttributeError:
        return _extract_agent_answer(agent.run(agent_input))
    except Exception as first_error:
        if not _is_output_parsing_error(first_error):
            raise

        retry_input = (
            "Answer this database question using SQL tools. "
            "Return only the final answer text.\n"
            f"Question: {plain_query}"
        )
        try:
            return _extract_agent_answer(agent.invoke({"input": retry_input}))
        except AttributeError:
            return _extract_agent_answer(agent.run(retry_input))


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "ok",
        "model":  os.getenv("GOOGLE_MODEL", "gemini-2.5-flash-lite-preview"),
        "features": ["talk_to_dataset", "talk_to_database_sql"],
    }


@app.get("/")
def root():
    return {
        "message": "Welcome to Talk to Data API",
        "features": ["talk_to_dataset", "talk_to_database_sql"],
    }


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Accept any CSV or Excel file.
    No hardcoded columns — schema is auto-detected from whatever the file contains.
    Returns session_id, detected schema, and a safe preview.
    """
    if not file.filename.endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(400, "Only CSV and Excel files are supported")

    contents = await file.read()
    try:
        df = (
            pd.read_csv(io.BytesIO(contents))
            if file.filename.endswith(".csv")
            else pd.read_excel(io.BytesIO(contents))
        )
    except Exception as e:
        raise HTTPException(400, f"Could not parse file: {e}")

    store   = get_session_store()
    session = store.create()
    session.set_dataframe(df, file.filename)

    registry = get_schema_registry()
    schema   = registry.register(session.session_id, df)

    safe_preview = sanitise_dataframe(df.head(5)).to_dict(orient="records")

    return {
        "session_id": session.session_id,
        "filename":   file.filename,
        "row_count":  schema["row_count"],
        "col_count":  schema["col_count"],
        "columns":    schema["columns"],
        "preview":    safe_preview,
    }


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Main endpoint.
    Works with any dataset — crime data, sales data, HR data, anything.
    Schema is read dynamically from the uploaded file.

    Returns:
      answer     — plain English explanation
      chart      — includes image_b64 (base64 PNG) for direct display
      source_ref — which columns + filters produced this answer
    """
    store   = get_session_store()
    session = store.get(request.session_id)

    if not session:
        raise HTTPException(404, "Session not found. Please upload a dataset first.")
    if not session.has_data():
        raise HTTPException(400, "No dataset uploaded for this session.")

    session.add_message("user", request.question)

    result = _orchestrator.run(
        question   = request.question,
        df         = session.df,
        session_id = request.session_id,
        history    = session.get_history_text(),
    )

    session.add_message("assistant", result.get("answer", ""))

    # Build chart object safely
    raw_chart = result.get("chart")
    chart_obj = None
    if raw_chart and isinstance(raw_chart, dict):
        chart_obj = ChartSpec(
            type      = raw_chart.get("type", "bar"),
            x_col     = raw_chart.get("x_col", ""),
            y_col     = raw_chart.get("y_col", ""),
            x_label   = raw_chart.get("x_label", ""),
            y_label   = raw_chart.get("y_label", ""),
            data      = raw_chart.get("data", []),
            image_b64 = raw_chart.get("image_b64"),
        )

    session.last_chart_b64 = chart_obj.image_b64 if chart_obj else None

    return QueryResponse(
        success    = result.get("success", False),
        intent     = result.get("intent", "general"),
        answer     = result.get("answer", "Something went wrong"),
        chart      = chart_obj,
        source_ref = result.get("source_ref", {}),
        data       = result.get("data", []),
        session_id = request.session_id,
    )


@app.post("/db/chat", response_model=DatabaseChatResponse)
def chat_with_database(req: DatabaseChatRequest, request: Request, response: ApiResponse):
    try:
        store = get_session_store()
        cookie_session_id = request.cookies.get("db_chat_session_id")
        session = store.get_or_create(cookie_session_id)

        db = configure_db(req)
        agent = get_sql_agent(db)

        history_text = session.get_db_history_text(last_n=8)
        if history_text:
            agent_input = (
                "Use the recent conversation context for follow-up SQL questions when relevant.\n"
                f"{history_text}\n"
                f"USER: {req.query}"
            )
        else:
            agent_input = req.query

        session.add_db_message("user", req.query)

        answer = run_sql_agent_with_retry(agent, agent_input=agent_input, plain_query=req.query)

        session.add_db_message("assistant", answer)

        response.set_cookie(
            key="db_chat_session_id",
            value=session.session_id,
            httponly=True,
            samesite="lax",
        )

        return DatabaseChatResponse(
            success=True,
            session_id=session.session_id,
            query=req.query,
            response=answer,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


@app.get("/chart/{session_id}/latest.png")
async def get_latest_chart_image(session_id: str):
    """
    Returns the latest chart as a raw PNG image.
    Use this URL directly in <img src="..."> tags.
    Store the latest chart b64 in the session for this endpoint.
    """
    store   = get_session_store()
    session = store.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    b64 = getattr(session, "last_chart_b64", None)
    if not b64:
        raise HTTPException(404, "No chart generated yet for this session")

    img_bytes = base64.b64decode(b64)
    return Response(content=img_bytes, media_type="image/png")


@app.get("/session/{session_id}")
def get_session_info(session_id: str):
    store   = get_session_store()
    session = store.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return {
        "session_id":    session_id,
        "filename":      session.filename,
        "has_data":      session.has_data(),
        "message_count": len(session.history),
    }


@app.get("/metrics")
def get_metrics():
    """
    Returns all defined metrics from metrics.yaml.
    Used by frontend to show metric definitions panel.
    Note: if user's dataset doesn't match these metrics,
    the system still works — it just uses raw column names.
    """
    sl = get_semantic_layer()
    return {"metrics": sl.get_metric_definitions()}

if __name__ == "__main__":
    import uvicorn
    # Default port 7860 is commonly used on Hugging Face Spaces
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

