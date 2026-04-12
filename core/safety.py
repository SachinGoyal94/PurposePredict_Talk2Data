"""
core/safety.py

Ensures:
1. The LLM never sees raw PII rows — only aggregated results pass through
2. Results are sanitised before being returned to the user
3. Dangerous code patterns are blocked from execution
"""
import re
import pandas as pd


# Columns that should NEVER be shown raw in results
PII_COLUMNS = {"customer_id", "email", "phone", "name", "address", "ssn", "dob"}

# Code patterns blocked in agent-generated code
BLOCKED_PATTERNS = [
    r"\bos\b\.",          # os.system, os.popen etc.
    r"\bsubprocess\b",
    r"\beval\b\s*\(",
    r"\bexec\b\s*\(",
    r"__import__",
    r"open\s*\(",         # file access
    r"\brequests\b",      # network calls
    r"\burllib\b",
]


def sanitise_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop PII columns before any result is returned to the user or LLM.
    Always aggregate — never return raw rows if count > 50.
    """
    # Remove known PII columns
    cols_to_drop = [c for c in df.columns if c.lower() in PII_COLUMNS]
    safe_df = df.drop(columns=cols_to_drop, errors="ignore")

    # If more than 50 rows, summarise instead of returning raw
    if len(safe_df) > 50:
        # Return column-level summary rather than raw rows
        return safe_df.describe(include="all").reset_index()

    return safe_df


def is_safe_code(code: str) -> tuple[bool, str]:
    """
    Check LLM-generated code for dangerous patterns before execution.
    Returns (is_safe, reason_if_unsafe).
    """
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, code):
            return False, f"Blocked pattern detected: {pattern}"
    return True, ""


def sanitise_result_for_display(result: dict) -> dict:
    """
    Final pass on the result dict before sending to frontend.
    Masks any residual PII-like strings.
    """
    if "data" in result and isinstance(result["data"], list):
        cleaned = []
        for row in result["data"]:
            clean_row = {
                k: v for k, v in row.items()
                if k.lower() not in PII_COLUMNS
            }
            cleaned.append(clean_row)
        result["data"] = cleaned
    return result
