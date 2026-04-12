"""
agents/analyst_agent.py

Our own Data Analyst Agent — no external agent libraries.

Flow:
  1. Enrich question with metric definitions (semantic layer)
  2. Inject schema context (column names, types, samples)
  3. Ask Gemini to write Pandas analysis code
  4. Safety-check the generated code
  5. Execute in a sandboxed namespace
  6. Return result + source reference
"""
import re
import pandas as pd
from core.semantic_layer import get_semantic_layer
from core.schema_registry import get_schema_registry
from core.safety import is_safe_code, sanitise_dataframe


class DataAnalystAgent:
    """
    Core analyst agent. Uses Gemini to generate Pandas code,
    executes it safely, and returns structured results.
    """

    SYSTEM_PROMPT = """You are an expert data analyst. You have a pandas DataFrame called `df`.
Your job is to write Python code that answers the user's question using pandas.

Rules:
- Only use pandas (imported as `pd`) and standard Python
- Store your final answer in a variable called `result`
- `result` must be a Python dict with exactly these keys:
    - "answer": a string — plain English explanation of the finding (no jargon, no mention of code)
    - "data": a list of dicts representing the key rows/aggregations (or None if no tabular data)
- Keep "answer" under 80 words, written for a non-technical business user
- Always include specific numbers in the answer
- Reference which columns/filters you used at the end of the answer with: [Source: column_name filtered by X]
- Output ONLY a Python code block wrapped in ```python ... ```, nothing else
"""

    def __init__(self, llm):
        self._llm      = llm
        self._semantic = get_semantic_layer()
        self._registry = get_schema_registry()

    def run(self, question: str, df: pd.DataFrame, session_id: str) -> dict:
        enriched_question = self._semantic.enrich_query(question)
        schema_ctx = self._registry.get_prompt_context(session_id)
        prompt = self._build_prompt(enriched_question, schema_ctx)

        try:
            response = self._llm.invoke(prompt)
            raw      = response.content if hasattr(response, "content") else response
        except Exception as e:
            return self._error(f"LLM call failed: {e}")

        code = self._extract_code(raw)
        if not code:
            return self._error("No valid code returned by the model")

        safe, reason = is_safe_code(code)
        if not safe:
            return self._error(f"Unsafe code blocked: {reason}")

        namespace = {"df": df.copy(), "pd": pd}
        try:
            exec(code, namespace)
        except Exception as e:
            return self._error(f"Code execution failed: {e}", code=code)

        result = namespace.get("result", {})
        if not isinstance(result, dict):
            return self._error("Model did not return a valid result dict", code=code)

        raw_data  = result.get("data")
        result_df = pd.DataFrame(raw_data) if raw_data else None
        safe_df   = sanitise_dataframe(result_df) if result_df is not None else None

        return {
            "success":    True,
            "answer":     result.get("answer", ""),
            "result_df":  safe_df,
            "code":       code,
            "source_ref": self._extract_source_ref(code, df),
        }

    def _build_prompt(self, enriched_question: str, schema_ctx: str) -> str:
        return f"""{self.SYSTEM_PROMPT}\n\n{schema_ctx}\n\n{enriched_question}\n"""

    def _extract_code(self, text) -> str:
        text = self._coerce_text(text)
        match = re.search(r"```(?:python)?\n?(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return text.strip()

    def _coerce_text(self, value) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="ignore")
        if isinstance(value, (list, tuple)):
            return "\n".join(self._coerce_text(item) for item in value if self._coerce_text(item))
        if isinstance(value, dict):
            if "content" in value:
                return self._coerce_text(value["content"])
            if "text" in value:
                return self._coerce_text(value["text"])
            return "\n".join(
                f"{key}: {self._coerce_text(item)}"
                for key, item in value.items()
                if self._coerce_text(item)
            )
        return str(value)

    def _extract_source_ref(self, code: str, df: pd.DataFrame) -> dict:
        cols_used = [col for col in df.columns
                     if f"'{col}'" in code or f'"{col}"' in code]
        filter_matches = re.findall(
            r"""df\[df\[['"](\w+)['"]]\s*[=!<>]+\s*['"]?([^'")\s]+)""", code
        )
        filter_strs = [f"{col} = {val}" for col, val in filter_matches]
        description = (
            f"Based on column{'s' if len(cols_used) > 1 else ''}: "
            f"{', '.join(cols_used)}"
            + (f" | Filtered by: {'; '.join(filter_strs)}" if filter_strs else "")
        ) if cols_used else "Based on full dataset"
        return {"columns_used": cols_used, "filters": filter_strs, "description": description}

    def _error(self, msg: str, code: str = "") -> dict:
        return {
            "success":    False,
            "answer":     f"I could not complete the analysis: {msg}",
            "result_df":  None,
            "code":       code,
            "source_ref": {},
        }


def build_analyst_agent(llm) -> DataAnalystAgent:
    """Factory — returns our own agent, no external libraries needed."""
    return DataAnalystAgent(llm)
