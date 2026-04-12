"""
core/schema_registry.py

Extracts column names, types, and sample values from any uploaded
dataframe. This context is injected into every LLM prompt so the
agent always knows exactly what data it's working with.
"""
import pandas as pd
import json
from typing import Any


class SchemaRegistry:
    def __init__(self):
        self._schemas: dict[str, dict] = {}   # session_id → schema

    def register(self, session_id: str, df: pd.DataFrame) -> dict:
        """Extract and store schema for a dataframe."""
        schema = self._extract_schema(df)
        self._schemas[session_id] = schema
        return schema

    def get(self, session_id: str) -> dict | None:
        return self._schemas.get(session_id)

    def get_prompt_context(self, session_id: str) -> str:
        """Return a formatted string to inject into LLM prompts."""
        schema = self._schemas.get(session_id)
        if not schema:
            return ""

        lines = [
            f"[DATASET SCHEMA — {schema['row_count']} rows, {schema['col_count']} columns]"
        ]
        for col in schema["columns"]:
            samples = ", ".join(str(s) for s in col["samples"])
            lines.append(
                f"  • {col['name']} ({col['dtype']}): e.g. {samples}"
                + (f"  — nulls: {col['null_pct']}%" if col["null_pct"] > 0 else "")
            )
        return "\n".join(lines)

    def _extract_schema(self, df: pd.DataFrame) -> dict:
        columns = []
        for col in df.columns:
            sample_vals = (
                df[col].dropna()
                       .drop_duplicates()
                       .head(4)
                       .tolist()
            )
            null_pct = round(df[col].isna().mean() * 100, 1)
            columns.append({
                "name":     col,
                "dtype":    str(df[col].dtype),
                "samples":  sample_vals,
                "null_pct": null_pct,
            })

        return {
            "row_count": len(df),
            "col_count": len(df.columns),
            "columns":   columns,
        }


# Singleton
_registry = None

def get_schema_registry() -> SchemaRegistry:
    global _registry
    if _registry is None:
        _registry = SchemaRegistry()
    return _registry
