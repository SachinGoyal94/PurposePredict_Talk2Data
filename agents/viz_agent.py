"""
agents/viz_agent.py

Picks the right chart type based on intent + result shape,
then renders it to a base64 PNG using Matplotlib.

The API response chart object includes:
  image_b64 — base64 PNG, display with <img src="data:image/png;base64,...">
  type      — bar | line | scatter | pie
  data      — raw data for any JS renderer (Plotly etc.)
"""
import io
import base64
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


PURPLE = "#7F77DD"
TEAL   = "#1D9E75"
CORAL  = "#D85A30"
AMBER  = "#EF9F27"
GRAY   = "#888780"

INTENT_CHART_MAP = {
    "compare":      "bar",
    "breakdown":    "bar",
    "what_changed": "line",
    "summarise":    "bar",
    "general":      "bar",
    "ds_anomaly":   "scatter",
    "ds_forecast":  "line",
    "ds_cluster":   "bar",
}

INTENT_COLORS = {
    "compare":      PURPLE,
    "breakdown":    TEAL,
    "what_changed": CORAL,
    "summarise":    PURPLE,
    "ds_anomaly":   CORAL,
    "ds_forecast":  TEAL,
    "ds_cluster":   AMBER,
    "general":      PURPLE,
}

PALETTE = [PURPLE, TEAL, CORAL, AMBER, GRAY, "#378ADD", "#639922"]


def pick_chart(
    intent: str,
    df: pd.DataFrame | None,
    chart_type: str | None = None,
) -> dict | None:
    if df is None or df.empty:
        return None

    chosen_type = chart_type or INTENT_CHART_MAP.get(intent, _infer_from_shape(df))
    color       = INTENT_COLORS.get(intent, PURPLE)
    x_col, y_col = _pick_axes(df, chosen_type)
    if not x_col or not y_col:
        return None

    plot_df = df[[x_col, y_col]].dropna().head(20)
    if plot_df.empty:
        return None

    image_b64 = _render_chart(chosen_type, plot_df, x_col, y_col, color)

    return {
        "type":      chosen_type,
        "x_col":     x_col,
        "y_col":     y_col,
        "x_label":   x_col.replace("_", " ").title(),
        "y_label":   y_col.replace("_", " ").title(),
        "data":      plot_df.to_dict(orient="records"),
        "image_b64": image_b64,
    }


def _render_chart(
    chart_type: str,
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color: str,
) -> str | None:
    try:
        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=120)
        fig.patch.set_facecolor("#FAFAFA")
        ax.set_facecolor("#FAFAFA")

        xs_raw = df[x_col].tolist()
        xs_str = [str(x) for x in xs_raw]
        ys     = pd.to_numeric(df[y_col], errors="coerce").fillna(0).tolist()
        idx    = list(range(len(ys)))

        if chart_type == "bar":
            bars = ax.bar(idx, ys, color=color, alpha=0.85,
                          edgecolor="white", linewidth=0.5)
            ax.bar_label(bars, fmt="%.0f", padding=3, fontsize=8, color="#444")
            ax.set_xticks(idx)
            ax.set_xticklabels(xs_str, rotation=30, ha="right", fontsize=9)

        elif chart_type == "line":
            ax.plot(idx, ys, color=color, linewidth=2.5, marker="o",
                    markersize=5, markerfacecolor="white", markeredgewidth=2)
            ax.fill_between(idx, ys, alpha=0.08, color=color)
            ax.set_xticks(idx)
            ax.set_xticklabels(xs_str, rotation=30, ha="right", fontsize=9)

        elif chart_type == "scatter":
            ax.scatter(idx, ys, color=color, alpha=0.75, s=45,
                       edgecolors="white", linewidth=0.5)
            ax.set_xticks(idx)
            ax.set_xticklabels(xs_str, rotation=30, ha="right", fontsize=9)
            # Highlight outliers (beyond 2 std)
            arr = np.array(ys)
            mean, std = arr.mean(), arr.std()
            outlier_idx = [i for i, v in enumerate(ys) if abs(v - mean) > 2 * std]
            if outlier_idx:
                ax.scatter(outlier_idx, [ys[i] for i in outlier_idx],
                           color=CORAL, s=80, zorder=5, label="Anomaly")
                ax.legend(fontsize=8)

        elif chart_type == "pie":
            valid = [(x, y) for x, y in zip(xs_str, ys) if y > 0]
            if not valid:
                plt.close(fig)
                return None
            labels, values = zip(*valid)
            wedges, texts, autotexts = ax.pie(
                values, labels=labels, autopct="%1.1f%%",
                colors=PALETTE[:len(values)], startangle=90,
                wedgeprops={"edgecolor": "white", "linewidth": 1.5},
            )
            for t in autotexts:
                t.set_fontsize(8)

        # Common styling
        if chart_type != "pie":
            ax.set_xlabel(x_col.replace("_", " ").title(),
                          fontsize=10, color="#555", labelpad=8)
            ax.set_ylabel(y_col.replace("_", " ").title(),
                          fontsize=10, color="#555", labelpad=8)
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(
                lambda x, _: f"{x:,.0f}" if abs(x) >= 1000 else f"{x:.1f}"
            ))
            ax.spines[["top", "right"]].set_visible(False)
            ax.spines[["left", "bottom"]].set_color("#DDD")
            ax.tick_params(colors="#666", labelsize=9)
            ax.grid(axis="y", linestyle="--", alpha=0.4, color="#CCC")

        plt.tight_layout(pad=1.5)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode("utf-8")
        plt.close(fig)
        return b64

    except Exception as e:
        print(f"Chart render error: {e}")
        plt.close("all")
        return None


def _infer_from_shape(df: pd.DataFrame) -> str:
    date_cols = [c for c in df.columns
                 if "date" in c.lower() or "time" in c.lower()]
    if date_cols:
        return "line"
    num_cols = df.select_dtypes(include="number").columns
    cat_cols = df.select_dtypes(exclude="number").columns
    if len(num_cols) == 1 and len(cat_cols) >= 1 and len(df) <= 6:
        return "pie"
    return "bar"


def _pick_axes(df: pd.DataFrame, chart_type: str) -> tuple[str | None, str | None]:
    num_cols  = df.select_dtypes(include="number").columns.tolist()
    cat_cols  = df.select_dtypes(exclude="number").columns.tolist()
    date_cols = [c for c in df.columns
                 if "date" in c.lower() or "time" in c.lower()]

    if chart_type == "line":
        x = date_cols[0] if date_cols else (cat_cols[0] if cat_cols else None)
    else:
        x = cat_cols[0] if cat_cols else (date_cols[0] if date_cols else None)

    y = num_cols[0] if num_cols else None

    # Fallback: first two columns
    cols = df.columns.tolist()
    if not x and len(cols) >= 1:
        x = cols[0]
    if not y and len(cols) >= 2:
        y = cols[1]

    # Never let x and y be the same column
    if x == y:
        remaining = [c for c in cols if c != x]
        y = remaining[0] if remaining else None

    return x, y
