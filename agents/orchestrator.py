"""
agents/orchestrator.py

Reads the user question, classifies intent, calls the right agent(s),
and assembles the final structured response.

Intent types (from the PS):
  - what_changed   → "why did X drop/rise"
  - compare        → "X vs Y", "this week vs last week"
  - breakdown      → "breakdown of X by Y", "what makes up"
  - summarise      → "weekly summary", "give me an overview"
  - ds_anomaly     → "unusual", "outlier", "spike"
  - ds_forecast    → "forecast", "predict", "next N days"
  - ds_cluster     → "segment", "cluster", "group"
  - general        → everything else
"""
import pandas as pd
from typing import Any

from agents.ds_agent import detect_ds_intent, detect_anomalies, forecast_metric, cluster_segments
from agents.viz_agent import pick_chart
from agents.summarizer import summarise_result


# ── Intent keywords ──────────────────────────────────────────────────────────

WHAT_CHANGED_KW = {"why", "drop", "fell", "declined", "rose", "spike", "cause", "reason", "changed"}
COMPARE_KW      = {" vs ", " versus ", "compare", "difference", "this week vs", "last week vs",
                   "this month vs", "vs last", "region a vs", "product a vs"}
BREAKDOWN_KW    = {"breakdown", "break down", "what makes up", "composition",
                   "by region", "by channel", "by product", "by department", "decompose", "split"}
SUMMARISE_KW    = {"summary", "summarise", "summarize", "overview", "digest",
                   "weekly", "daily", "monthly", "give me a", "what happened"}


def classify_intent(question: str) -> str:
    q = question.lower()

    # DS intents first (most specific)
    ds = detect_ds_intent(question)
    if ds:
        return f"ds_{ds}"

    if any(k in q for k in WHAT_CHANGED_KW):  return "what_changed"
    if any(k in q for k in COMPARE_KW):        return "compare"
    if any(k in q for k in BREAKDOWN_KW):      return "breakdown"
    if any(k in q for k in SUMMARISE_KW):      return "summarise"
    return "general"


class Orchestrator:
    def __init__(self, analyst_agent, llm):
        self._analyst = analyst_agent
        self._llm     = llm

    def run(
        self,
        question: str,
        df: pd.DataFrame,
        session_id: str,
        history: str = "",
    ) -> dict:
        intent = classify_intent(question)

        # ── DS intents ──────────────────────────────────────────────────────
        if intent == "ds_anomaly":
            num_cols = df.select_dtypes(include="number").columns.tolist()
            target   = num_cols[0] if num_cols else None
            if not target:
                return _error_response("No numeric column found for anomaly detection")
            ds_result = detect_anomalies(df, column=target)
            return _format_response(ds_result, intent, question, source_col=target)

        if intent == "ds_forecast":
            date_col  = _find_date_col(df)
            num_cols  = df.select_dtypes(include="number").columns.tolist()
            value_col = num_cols[0] if num_cols else None
            if not date_col or not value_col:
                return _error_response("Need a date column and a numeric column to forecast")
            ds_result = forecast_metric(df, date_col=date_col, value_col=value_col)
            return _format_response(ds_result, intent, question, source_col=value_col)

        if intent == "ds_cluster":
            num_cols = df.select_dtypes(include="number").columns.tolist()
            if not num_cols:
                return _error_response("No numeric columns found for clustering")
            ds_result = cluster_segments(df, feature_cols=num_cols)
            return _format_response(ds_result, intent, question)

        # ── Standard analysis intents → Analyst Agent ───────────────────────
        analyst_result = self._analyst.run(
            question   = question,
            df         = df,
            session_id = session_id,
        )

        if not analyst_result.get("success"):
            return _error_response(analyst_result.get("answer", "Analysis failed"))

        result_df  = analyst_result.get("result_df")
        code       = analyst_result.get("code", "")
        source_ref = analyst_result.get("source_ref", {})

        # Pick chart
        chart_spec = pick_chart(intent=intent, df=result_df) if result_df is not None else None

        # Generate plain-English summary
        answer = analyst_result.get("answer") or summarise_result(
            llm       = self._llm,
            intent    = intent,
            question  = question,
            result_df = result_df,
            source_ref= source_ref,
        )

        return {
            "success":    True,
            "intent":     intent,
            "answer":     answer,
            "chart":      chart_spec,
            "source_ref": source_ref,
            "code":       code,
            "data":       result_df.to_dict(orient="records") if result_df is not None else [],
        }


# ── Helpers ──────────────────────────────────────────────────────────────────

def _format_response(ds_result: dict, intent: str, question: str, source_col: str = "") -> dict:
    if "error" in ds_result:
        return _error_response(ds_result["error"])

    result_df = (
        ds_result.get("anomalies_df")
        or ds_result.get("forecast_df")
        or ds_result.get("profile_df")
    )
    chart_spec = pick_chart(intent=intent, df=result_df, chart_type=ds_result.get("chart_type"))

    return {
        "success":  True,
        "intent":   intent,
        "answer":   ds_result.get("summary", ""),
        "chart":    chart_spec,
        "source_ref": {
            "columns_used": [source_col] if source_col else ds_result.get("features", []),
            "description":  f"Based on column: {source_col}" if source_col else "",
        },
        "data": result_df.to_dict(orient="records") if result_df is not None else [],
    }


def _error_response(msg: str) -> dict:
    return {"success": False, "answer": msg, "chart": None, "source_ref": {}, "data": []}


def _find_date_col(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        if "date" in col.lower() or "time" in col.lower() or "day" in col.lower():
            try:
                pd.to_datetime(df[col])
                return col
            except Exception:
                continue
    return None
