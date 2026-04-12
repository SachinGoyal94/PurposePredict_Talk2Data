"""
agents/ds_agent.py  —  YOUR data science work

Three capabilities:
  1. Anomaly detection  (Z-score + IQR + optional Isolation Forest)
  2. Forecasting        (statsmodels ARIMA / simple moving average fallback)
  3. Clustering         (KMeans segmentation)

The orchestrator calls this when the user query contains
trigger words like "unusual", "anomaly", "forecast",
"predict", "segment", "cluster".
"""
import pandas as pd
import numpy as np
from typing import Any


# ── 1. Anomaly Detection ────────────────────────────────────────────────────

def detect_anomalies(
    df: pd.DataFrame,
    column: str,
    method: str = "zscore",
    threshold: float = 2.5,
) -> dict:
    """
    Detect anomalies in a numeric column.

    method: 'zscore' | 'iqr' | 'isolation_forest'
    Returns flagged rows + a plain-English summary.
    """
    if column not in df.columns:
        return {"error": f"Column '{column}' not found"}

    series = pd.to_numeric(df[column], errors="coerce").dropna()
    result_df = df.copy()

    if method == "zscore":
        z = (series - series.mean()) / series.std()
        result_df["_anomaly"]       = z.abs() > threshold
        result_df["_anomaly_score"] = z.round(3)
        method_label = f"Z-score (threshold ±{threshold})"

    elif method == "iqr":
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr     = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        result_df["_anomaly"]       = (series < lower) | (series > upper)
        result_df["_anomaly_score"] = series.rank(pct=True).round(3)
        method_label = f"IQR (bounds: {lower:.2f}–{upper:.2f})"

    elif method == "isolation_forest":
        try:
            from sklearn.ensemble import IsolationForest
            clf    = IsolationForest(contamination=0.05, random_state=42)
            preds  = clf.fit_predict(series.values.reshape(-1, 1))
            result_df["_anomaly"]       = preds == -1
            result_df["_anomaly_score"] = clf.score_samples(series.values.reshape(-1, 1)).round(3)
            method_label = "Isolation Forest (contamination=5%)"
        except ImportError:
            return detect_anomalies(df, column, method="zscore", threshold=threshold)
    else:
        return {"error": f"Unknown method: {method}"}

    anomalies    = result_df[result_df["_anomaly"]].drop(columns=["_anomaly"])
    normal_count = (~result_df["_anomaly"]).sum()
    anom_count   = result_df["_anomaly"].sum()

    summary = (
        f"Found {anom_count} anomalies in '{column}' out of {len(df)} records "
        f"using {method_label}. "
        f"{normal_count} records are within normal range."
    )
    if anom_count > 0:
        anom_vals = anomalies[column].describe()
        summary += (
            f" Anomalous values range from {anom_vals['min']:.2f} "
            f"to {anom_vals['max']:.2f} (mean: {anom_vals['mean']:.2f})."
        )

    return {
        "anomaly_count":  int(anom_count),
        "total_records":  len(df),
        "method":         method_label,
        "anomalies_df":   anomalies.head(50),
        "summary":        summary,
        "chart_type":     "scatter",
        "chart_col":      column,
    }


# ── 2. Forecasting ──────────────────────────────────────────────────────────

def forecast_metric(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    periods: int = 7,
    freq: str = "D",
) -> dict:
    """
    Forecast a time-series metric N periods into the future.
    Tries ARIMA first, falls back to exponential smoothing.
    """
    if date_col not in df.columns or value_col not in df.columns:
        return {"error": "Date or value column not found"}

    ts = (
        df[[date_col, value_col]]
        .copy()
        .assign(**{date_col: pd.to_datetime(df[date_col])})
        .groupby(date_col)[value_col]
        .sum()
        .sort_index()
        .asfreq(freq, method="pad")
    )

    method_used = "ARIMA"
    try:
        from statsmodels.tsa.arima.model import ARIMA
        model  = ARIMA(ts, order=(2, 1, 2))
        fitted = model.fit()
        forecast_vals = fitted.forecast(steps=periods)
        conf_int      = fitted.get_forecast(steps=periods).conf_int()
    except Exception:
        method_used   = "Exponential smoothing (ARIMA unavailable)"
        alpha         = 0.3
        smoothed      = ts.ewm(alpha=alpha).mean()
        last_val      = smoothed.iloc[-1]
        trend         = smoothed.diff().mean()
        future_idx    = pd.date_range(ts.index[-1], periods=periods + 1, freq=freq)[1:]
        forecast_vals = pd.Series(
            [last_val + trend * i for i in range(1, periods + 1)],
            index=future_idx,
        )
        conf_int = None

    forecast_df = pd.DataFrame({
        "date":          forecast_vals.index.strftime("%Y-%m-%d"),
        "forecast":      forecast_vals.values.round(2),
        "lower_bound":   conf_int.iloc[:, 0].round(2).values if conf_int is not None else None,
        "upper_bound":   conf_int.iloc[:, 1].round(2).values if conf_int is not None else None,
    })

    summary = (
        f"Forecast for '{value_col}' over the next {periods} {freq}-periods "
        f"using {method_used}. "
        f"Predicted range: {forecast_df['forecast'].min():.2f} – "
        f"{forecast_df['forecast'].max():.2f}. "
        f"Trend direction: {'upward' if forecast_df['forecast'].iloc[-1] > forecast_df['forecast'].iloc[0] else 'downward'}."
    )

    return {
        "forecast_df":  forecast_df,
        "history_df":   ts.reset_index().rename(columns={date_col: "date", value_col: "actual"}),
        "method":       method_used,
        "summary":      summary,
        "chart_type":   "line",
    }


# ── 3. Clustering / Segmentation ────────────────────────────────────────────

def cluster_segments(
    df: pd.DataFrame,
    feature_cols: list[str],
    n_clusters: int = 4,
    label_col: str | None = None,
) -> dict:
    """
    KMeans segmentation on numeric features.
    Returns cluster assignments + per-cluster profile.
    """
    numeric_cols = [c for c in feature_cols if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
    if not numeric_cols:
        return {"error": "No numeric columns found for clustering"}

    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans

    X      = df[numeric_cols].dropna()
    scaler = StandardScaler()
    X_sc   = scaler.fit_transform(X)

    km     = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = km.fit_predict(X_sc)

    result_df           = X.copy()
    result_df["segment"] = [f"Segment {l + 1}" for l in labels]

    if label_col and label_col in df.columns:
        result_df[label_col] = df.loc[X.index, label_col]

    profile = result_df.groupby("segment")[numeric_cols].mean().round(2)

    summary_lines = [f"Identified {n_clusters} customer segments based on {', '.join(numeric_cols)}:"]
    for seg, row in profile.iterrows():
        top_feat = row.idxmax()
        summary_lines.append(f"  • {seg}: highest in {top_feat} ({row[top_feat]:.2f})")

    return {
        "segments_df":  result_df.head(200),
        "profile_df":   profile.reset_index(),
        "n_clusters":   n_clusters,
        "features":     numeric_cols,
        "summary":      "\n".join(summary_lines),
        "chart_type":   "bar",
    }


# ── Intent detection helper ─────────────────────────────────────────────────

ANOMALY_TRIGGERS  = {"unusual", "anomaly", "outlier", "abnormal", "weird", "strange"}
FORECAST_TRIGGERS = {"forecast", "predict", "next", "future", "projection", "trend"}
CLUSTER_TRIGGERS  = {"segment", "cluster", "group", "classify", "categorise", "categorize"}


def detect_ds_intent(question: str) -> str | None:
    """Return 'anomaly' | 'forecast' | 'cluster' | None."""
    q = question.lower()
    if any(t in q for t in ANOMALY_TRIGGERS):  return "anomaly"
    if any(t in q for t in FORECAST_TRIGGERS): return "forecast"
    if any(t in q for t in CLUSTER_TRIGGERS):  return "cluster"
    return None
