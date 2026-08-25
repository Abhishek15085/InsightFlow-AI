"""
InsightFlow AI — EDA Service
         outlier detection (IQR), and EDA report generation.
"""

import os
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder

# ── Constants ─────────────────────────────────────────────────────────────────

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# Colour palette (consistent across charts)
_PALETTE = px.colors.qualitative.Vivid


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fig_to_json(fig: go.Figure) -> dict:
    """Convert a Plotly figure to a JSON-serialisable dict."""
    return json.loads(json.dumps(fig.to_dict(), cls=PlotlyJSONEncoder))


def _numeric_cols(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include="number").columns.tolist()


def _categorical_cols(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()


# ── Distribution Charts ───────────────────────────────────────────────────────────

def distribution_charts(df: pd.DataFrame) -> dict:
    """
    Generate Plotly histogram + box plot for every numeric column.

    Returns:
        {col: {"histogram": fig_json, "boxplot": fig_json, "stats": {...}}}
    """
    result: dict = {}
    num_cols = _numeric_cols(df)

    for col in num_cols:
        series = df[col].dropna()
        if series.empty:
            continue

        # Histogram
        hist_fig = go.Figure()
        hist_fig.add_trace(go.Histogram(
            x=series,
            name=col,
            marker_color="#a78bfa",
            opacity=0.85,
            nbinsx=30,
        ))
        hist_fig.update_layout(
            title=f"Distribution — {col}",
            xaxis_title=col,
            yaxis_title="Count",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,255,255,0.03)",
            font=dict(color="#e2e8f0", family="Inter"),
            title_font=dict(size=14, color="#a78bfa"),
            margin=dict(l=40, r=20, t=50, b=40),
        )

        # Box plot
        box_fig = go.Figure()
        box_fig.add_trace(go.Box(
            y=series,
            name=col,
            marker_color="#60a5fa",
            boxmean="sd",
            line_color="#60a5fa",
        ))
        box_fig.update_layout(
            title=f"Box Plot — {col}",
            yaxis_title=col,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,255,255,0.03)",
            font=dict(color="#e2e8f0", family="Inter"),
            title_font=dict(size=14, color="#60a5fa"),
            margin=dict(l=40, r=20, t=50, b=40),
        )

        result[col] = {
            "histogram": _fig_to_json(hist_fig),
            "boxplot":   _fig_to_json(box_fig),
            "stats": {
                "count":  int(series.count()),
                "mean":   round(float(series.mean()), 4),
                "std":    round(float(series.std()), 4),
                "min":    round(float(series.min()), 4),
                "q25":    round(float(series.quantile(0.25)), 4),
                "median": round(float(series.median()), 4),
                "q75":    round(float(series.quantile(0.75)), 4),
                "max":    round(float(series.max()), 4),
            },
        }

    return result


# ── Correlation Matrix ──────────────────────────────────────────────────────────

def correlation_matrix(df: pd.DataFrame) -> dict:
    """
    Compute Pearson correlation for numeric columns and return Plotly heatmap.

    Returns:
        {"heatmap": fig_json, "matrix": {col: {col: corr_val}}}
    """
    num_cols = _numeric_cols(df)
    if len(num_cols) < 2:
        return {"heatmap": None, "matrix": {}, "error": "Need ≥ 2 numeric columns"}

    corr = df[num_cols].corr(numeric_only=True)
    corr_values = corr.values

    fig = go.Figure(go.Heatmap(
        z=corr_values,
        x=num_cols,
        y=num_cols,
        colorscale=[
            [0.0,  "#1e3a5f"],
            [0.25, "#2d6a9f"],
            [0.5,  "#1f2937"],
            [0.75, "#7c3aed"],
            [1.0,  "#a78bfa"],
        ],
        zmin=-1, zmax=1,
        text=[[f"{v:.2f}" for v in row] for row in corr_values],
        texttemplate="%{text}",
        textfont={"size": 10, "color": "white"},
        hovertemplate="%{y} × %{x}: %{z:.3f}<extra></extra>",
    ))
    fig.update_layout(
        title="Pearson Correlation Matrix",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0", family="Inter"),
        title_font=dict(size=15, color="#a78bfa"),
        xaxis=dict(tickangle=-35),
        margin=dict(l=60, r=20, t=60, b=60),
    )

    return {
        "heatmap": _fig_to_json(fig),
        "matrix":  corr.round(4).to_dict(),
        "columns": num_cols,
    }


# ── Categorical Analysis ──────────────────────────────────────────────────────

def categorical_analysis(df: pd.DataFrame, top_n: int = 10) -> dict:
    """
    For each categorical column return top-N frequency bar chart + value counts.

    Returns:
        {col: {"bar_chart": fig_json, "top_values": [{value, count, pct}], "unique_count": int}}
    """
    result: dict = {}
    cat_cols = _categorical_cols(df)

    for i, col in enumerate(cat_cols):
        series = df[col].dropna().astype(str)
        if series.empty:
            continue

        value_counts = series.value_counts().head(top_n)
        total = len(series)

        labels = value_counts.index.tolist()
        counts = value_counts.values.tolist()
        color  = _PALETTE[i % len(_PALETTE)]

        fig = go.Figure(go.Bar(
            x=labels,
            y=counts,
            marker_color=color,
            opacity=0.85,
            text=[f"{c:,}" for c in counts],
            textposition="outside",
        ))
        fig.update_layout(
            title=f"Top {top_n} Values — {col}",
            xaxis_title=col,
            yaxis_title="Frequency",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,255,255,0.03)",
            font=dict(color="#e2e8f0", family="Inter"),
            title_font=dict(size=14, color=color),
            xaxis=dict(tickangle=-30),
            margin=dict(l=40, r=20, t=55, b=60),
        )

        result[col] = {
            "bar_chart":    _fig_to_json(fig),
            "top_values": [
                {
                    "value": str(v),
                    "count": int(c),
                    "pct":   round(int(c) / total * 100, 2),
                }
                for v, c in zip(labels, counts)
            ],
            "unique_count": int(series.nunique()),
            "total_non_null": int(total),
        }

    return result


# ── Outlier Detection (IQR) ────────────────────────────────────────────────────

def outlier_detection(df: pd.DataFrame) -> dict:
    """
    Detect outliers in numeric columns using the IQR (Tukey fences) method.

    Returns:
        {
          "summary": [{col, outlier_count, outlier_pct, q1, q3, iqr, lower, upper}],
          "total_outlier_rows": int,
        }
    """
    num_cols = _numeric_cols(df)
    summary  = []
    outlier_row_flags = pd.Series([False] * len(df))

    for col in num_cols:
        series = df[col].dropna()
        if series.empty:
            continue

        q1  = series.quantile(0.25)
        q3  = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        is_outlier = (df[col] < lower) | (df[col] > upper)
        outlier_count = int(is_outlier.sum())
        outlier_row_flags = outlier_row_flags | is_outlier.fillna(False)

        if outlier_count > 0:
            summary.append({
                "column":        col,
                "outlier_count": outlier_count,
                "outlier_pct":   round(outlier_count / len(df) * 100, 2),
                "q1":            round(float(q1), 4),
                "q3":            round(float(q3), 4),
                "iqr":           round(float(iqr), 4),
                "lower_fence":   round(float(lower), 4),
                "upper_fence":   round(float(upper), 4),
            })

    # Sort by outlier count desc
    summary.sort(key=lambda x: x["outlier_count"], reverse=True)

    return {
        "summary":            summary,
        "total_outlier_rows": int(outlier_row_flags.sum()),
        "total_rows":         len(df),
        "outlier_pct_overall": round(outlier_row_flags.sum() / max(len(df), 1) * 100, 2),
    }


# ── EDA Report ─────────────────────────────────────────────────────────────

def generate_eda_report(df: pd.DataFrame, filename: str) -> dict:
    """
    Compile a full EDA report dict and save to reports/{stem}_eda.json.

    Returns a lightweight summary (chart data excluded for file size).
    """
    stem = os.path.splitext(filename)[0]
    report_path = os.path.join(REPORTS_DIR, f"{stem}_eda.json")

    num_cols  = _numeric_cols(df)
    cat_cols  = _categorical_cols(df)
    dup_count = int(df.duplicated().sum())
    missing   = int(df.isna().sum().sum())

    # Lightweight stats (no chart JSON to keep file small)
    col_stats = {}
    for col in num_cols:
        s = df[col].dropna()
        col_stats[col] = {
            "type":   "numeric",
            "count":  int(s.count()),
            "missing": int(df[col].isna().sum()),
            "mean":   round(float(s.mean()), 6) if len(s) else None,
            "std":    round(float(s.std()), 6)  if len(s) else None,
            "min":    round(float(s.min()), 6)  if len(s) else None,
            "max":    round(float(s.max()), 6)  if len(s) else None,
        }
    for col in cat_cols:
        s = df[col].dropna()
        col_stats[col] = {
            "type":        "categorical",
            "count":       int(s.count()),
            "missing":     int(df[col].isna().sum()),
            "unique":      int(s.nunique()),
            "top_value":   str(s.mode().iloc[0]) if len(s) else None,
            "top_freq":    int(s.value_counts().iloc[0]) if len(s) else None,
        }

    outliers = outlier_detection(df)

    report = {
        "filename":         filename,
        "generated_at":     pd.Timestamp.utcnow().isoformat() + "Z",
        "shape":            {"rows": len(df), "columns": len(df.columns)},
        "numeric_columns":  num_cols,
        "categorical_columns": cat_cols,
        "total_missing_cells": missing,
        "duplicate_rows":   dup_count,
        "column_stats":     col_stats,
        "outlier_summary":  outliers["summary"],
        "total_outlier_rows": outliers["total_outlier_rows"],
    }

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    return {
        "report_file":      f"{stem}_eda.json",
        "report_path":      report_path,
        "rows":             len(df),
        "columns":          len(df.columns),
        "numeric_columns":  len(num_cols),
        "categorical_columns": len(cat_cols),
        "total_missing_cells": missing,
        "duplicate_rows":   dup_count,
        "total_outlier_rows": outliers["total_outlier_rows"],
    }
