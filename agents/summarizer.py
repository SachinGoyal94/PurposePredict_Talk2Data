"""
agents/summarizer.py

Takes raw analysis results and produces:
- A plain-English answer (non-technical, jargon-free)
- Source references (which columns, which filters)

This directly addresses the PS pillars of Clarity and Trust.
"""
import pandas as pd


INTENT_PROMPTS = {
    "what_changed": (
        "Explain what changed and why, in 2-3 sentences. "
        "Identify the biggest driver. Use simple language for non-experts."
    ),
    "compare": (
        "Summarise the comparison clearly. Highlight which is higher/lower and by how much. "
        "Keep it to 2-3 sentences."
    ),
    "breakdown": (
        "Explain what the biggest contributors are. "
        "Give proportions if available. 2-3 sentences, no jargon."
    ),
    "summarise": (
        "Give a concise summary of the key trends and anomalies. "
        "What truly matters? Keep to 3-4 bullet points."
    ),
    "general": (
        "Answer the question directly and concisely. 2-3 sentences."
    ),
}


def summarise_result(
    llm,
    intent: str,
    question: str,
    result_df: pd.DataFrame | None,
    source_ref: dict,
) -> str:
    """
    Ask the LLM to summarise the result_df in plain English.
    Appends a source reference line automatically.
    """
    instruction = INTENT_PROMPTS.get(intent, INTENT_PROMPTS["general"])

    data_preview = ""
    if result_df is not None and not result_df.empty:
        data_preview = result_df.head(10).to_string(index=False)

    prompt = f"""
You are a data analyst explaining results to a non-technical business user.

Original question: {question}

Analysis result:
{data_preview}

Task: {instruction}

Rules:
- No technical jargon (no "DataFrame", "groupby", "filter")
- Use plain business language
- Mention specific numbers from the data
- Keep it under 100 words
- Do NOT mention the code or how you calculated it
"""

    try:
        response = llm.invoke(prompt)
        answer   = response.content if hasattr(response, "content") else response
    except Exception as e:
        answer = f"The analysis completed but I could not generate a summary: {e}"

    answer = _coerce_text(answer)

    # Append source reference
    src = source_ref.get("description", "")
    if src:
        answer += f"\n\n📌 *{src}*"

    return answer.strip()


def _coerce_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")
    if isinstance(value, (list, tuple)):
        return "\n".join(_coerce_text(item) for item in value if _coerce_text(item))
    if isinstance(value, dict):
        if "content" in value:
            return _coerce_text(value["content"])
        if "text" in value:
            return _coerce_text(value["text"])
        return "\n".join(f"{key}: {_coerce_text(item)}" for key, item in value.items() if _coerce_text(item))
    return str(value)

