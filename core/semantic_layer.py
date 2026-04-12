"""
core/semantic_layer.py

Loads metrics.yaml and enriches every user query with:
- Resolved column names for any business term they used
- Metric definitions so the LLM knows exactly what "revenue" means
- Time expression resolution ("this month" → actual date range)
"""
import yaml
import re
from pathlib import Path
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


METRICS_PATH = Path(__file__).parent.parent / "config" / "metrics.yaml"


class SemanticLayer:
    def __init__(self):
        with open(METRICS_PATH, "r") as f:
            config = yaml.safe_load(f)
        self.metrics    = config.get("metrics", {})
        self.dimensions = config.get("dimensions", {})
        self.time_expr  = config.get("time_expressions", {})
        self._build_alias_map()

    def _build_alias_map(self):
        """Build a flat alias → canonical_name map for fast lookup."""
        self.alias_map = {}
        for name, meta in {**self.metrics, **self.dimensions}.items():
            self.alias_map[name.lower()] = name
            for alias in meta.get("aliases", []):
                self.alias_map[alias.lower()] = name

    def resolve_term(self, term: str) -> dict | None:
        """Return metric/dimension metadata for any term or alias."""
        canonical = self.alias_map.get(term.lower().strip())
        if canonical:
            return {
                "canonical": canonical,
                **{**self.metrics, **self.dimensions}.get(canonical, {})
            }
        return None

    def resolve_time_expressions(self, query: str) -> str:
        """
        Replace vague time phrases with concrete date ranges.
        "this month" → "April 2026 (2026-04-01 to 2026-04-30)"
        """
        today = date.today()
        replacements = {
            r"\bthis month\b": (
                f"{today.strftime('%B %Y')} "
                f"({today.replace(day=1)} to "
                f"{(today.replace(day=1) + relativedelta(months=1) - relativedelta(days=1))})"
            ),
            r"\blast month\b": (
                f"{(today - relativedelta(months=1)).strftime('%B %Y')} "
                f"({(today - relativedelta(months=1)).replace(day=1)} to "
                f"{today.replace(day=1) - relativedelta(days=1)})"
            ),
            r"\bthis week\b": (
                f"week of {today - relativedelta(days=today.weekday())} "
                f"to {today - relativedelta(days=today.weekday()) + relativedelta(days=6)}"
            ),
            r"\blast week\b": (
                f"week of {today - relativedelta(days=today.weekday() + 7)} "
                f"to {today - relativedelta(days=today.weekday() + 1)}"
            ),
            r"\bthis year\b":  f"{today.year} (2026-01-01 to today {today})",
            r"\bytd\b":        f"year to date (2026-01-01 to {today})",
        }
        resolved = query
        for pattern, replacement in replacements.items():
            resolved = re.sub(pattern, replacement, resolved, flags=re.IGNORECASE)
        return resolved

    def enrich_query(self, user_query: str) -> str:
        """
        Take the raw user question and prepend a context block
        so the LLM knows exactly what every business term means.
        """
        resolved_query = self.resolve_time_expressions(user_query)

        # Find which metrics/dimensions are mentioned
        mentioned = []
        for alias, canonical in self.alias_map.items():
            if alias in resolved_query.lower():
                meta = {**self.metrics, **self.dimensions}.get(canonical, {})
                mentioned.append((canonical, meta))

        if not mentioned:
            return resolved_query  # nothing to enrich

        context_lines = ["[METRIC DEFINITIONS — use these exact columns]"]
        seen = set()
        for canonical, meta in mentioned:
            if canonical in seen:
                continue
            seen.add(canonical)
            col   = meta.get("column", canonical)
            desc  = meta.get("description", "")
            filt  = meta.get("filters", "")
            unit  = meta.get("unit", "")
            line  = f"  • {canonical}: column='{col}'"
            if desc:  line += f", meaning='{desc}'"
            if filt:  line += f", filter='{filt}'"
            if unit:  line += f", unit={unit}"
            context_lines.append(line)

        context = "\n".join(context_lines)
        return f"{context}\n\nUser question: {resolved_query}"

    def get_metric_definitions(self) -> dict:
        """Return all metrics for display in the UI source panel."""
        return self.metrics

    def get_all_terms(self) -> list[str]:
        """Return every known term/alias — used for query suggestions."""
        return list(self.alias_map.keys())


# Singleton
_semantic_layer = None

def get_semantic_layer() -> SemanticLayer:
    global _semantic_layer
    if _semantic_layer is None:
        _semantic_layer = SemanticLayer()
    return _semantic_layer
