"""
InsightFlow AI — Dashboard API Routes

All endpoints work on a cleaned CSV file (or raw if no cleaning done yet).
"""

import os
import glob
import json
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fastapi import APIRouter, Query, HTTPException

from backend.services import upload_service as us
from backend.services import cleaning_service as cs

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_df(filename: str) -> pd.DataFrame:
    try:
        return us.load_csv(filename)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


def _numeric_cols(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include="number").columns.tolist()


def _categorical_cols(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()


# ── Dataset Overview ──────────────────────────────────────────────────────────

@router.get(
    "/overview",
    summary="Dataset Overview",
    description=(
        "Returns dataset shape, missing values, duplicate count, memory usage, "
        "and data quality score for the specified CSV file."
    ),
)
def get_overview(
    filename: str = Query(..., description="CSV filename in datasets/"),
):
    df = _load_df(filename)

    total_cells  = df.size or 1
    missing_cells = int(df.isna().sum().sum())
    duplicate_rows = int(df.duplicated().sum())
    mem_bytes    = int(df.memory_usage(deep=True).sum())
    quality      = cs.compute_quality_score(df)

    numeric_cols = _numeric_cols(df)
    cat_cols     = _categorical_cols(df)

    return {
        "filename":        filename,
        "rows":            len(df),
        "columns":         len(df.columns),
        "numeric_columns": len(numeric_cols),
        "categorical_columns": len(cat_cols),
        "missing_cells":   missing_cells,
        "missing_pct":     round(missing_cells / total_cells * 100, 2),
        "duplicate_rows":  duplicate_rows,
        "duplicate_pct":   round(duplicate_rows / len(df) * 100, 2) if len(df) else 0,
        "memory_bytes":    mem_bytes,
        "memory_kb":       round(mem_bytes / 1024, 2),
        "quality_score":   quality,
    }


# ── Data Quality Score (Before / After) ───────────────────────────────────────

@router.get(
    "/quality_score",
    summary="Data Quality Score — Before vs After",
    description=(
        "Returns the quality score for both the raw and cleaned versions of the dataset. "
        "Pass `raw_filename` (original) and `clean_filename` (cleaned). "
        "If clean_filename is omitted the raw score is returned for both."
    ),
)
def get_quality_score(
    raw_filename:   str = Query(..., description="Original CSV filename"),
    clean_filename: str | None = Query(None, description="Cleaned CSV filename (optional)"),
):
    raw_df   = _load_df(raw_filename)
    raw_score = cs.compute_quality_score(raw_df)

    if clean_filename:
        clean_df    = _load_df(clean_filename)
        clean_score = cs.compute_quality_score(clean_df)
    else:
        clean_df    = raw_df
        clean_score = raw_score

    improvement = round(clean_score - raw_score, 2)

    return {
        "raw_filename":   raw_filename,
        "clean_filename": clean_filename or raw_filename,
        "raw_score":      raw_score,
        "clean_score":    clean_score,
        "improvement":    improvement,
        "raw_rows":       len(raw_df),
        "clean_rows":     len(clean_df),
    }


# ── Numerical Analysis ────────────────────────────────────────────────────────

@router.get(
    "/numerical",
    summary="Numerical Analysis Charts",
    description=(
        "Returns Plotly histogram and box-plot JSON for every numeric column, "
        "plus descriptive statistics."
    ),
)
def get_numerical(
    filename: str = Query(..., description="CSV filename in datasets/"),
):
    df = _load_df(filename)
    num_cols = _numeric_cols(df)

    if not num_cols:
        return {"filename": filename, "numeric_columns": [], "charts": []}

    charts = []
    for col in num_cols:
        series = df[col].dropna()

        hist_fig = px.histogram(
            df, x=col, nbins=30,
            title=f"Distribution — {col}",
            color_discrete_sequence=["#a78bfa"],
        )
        hist_fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0",
        )

        box_fig = px.box(
            df, y=col,
            title=f"Box Plot — {col}",
            color_discrete_sequence=["#60a5fa"],
        )
        box_fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0",
        )

        stats = {
            "count":  int(series.count()),
            "mean":   round(float(series.mean()), 4),
            "median": round(float(series.median()), 4),
            "std":    round(float(series.std()), 4),
            "min":    round(float(series.min()), 4),
            "max":    round(float(series.max()), 4),
            "q25":    round(float(series.quantile(0.25)), 4),
            "q75":    round(float(series.quantile(0.75)), 4),
        }

        charts.append({
            "column":    col,
            "histogram": json.loads(hist_fig.to_json()),
            "boxplot":   json.loads(box_fig.to_json()),
            "stats":     stats,
        })

    return {"filename": filename, "numeric_columns": num_cols, "charts": charts}


# ── Categorical Analysis ──────────────────────────────────────────────────────

@router.get(
    "/categorical",
    summary="Categorical Analysis Charts",
    description=(
        "Returns a bar chart (count plot) and pie chart JSON for every categorical column, "
        "plus frequency table."
    ),
)
def get_categorical(
    filename: str = Query(..., description="CSV filename in datasets/"),
    top_n: int = Query(10, description="Show top-N categories"),
):
    df = _load_df(filename)
    cat_cols = _categorical_cols(df)

    if not cat_cols:
        return {"filename": filename, "categorical_columns": [], "charts": []}

    charts = []
    for col in cat_cols:
        vc = df[col].value_counts().head(top_n)
        labels = vc.index.astype(str).tolist()
        values = vc.values.tolist()

        bar_fig = px.bar(
            x=labels, y=values,
            title=f"Count Plot — {col}",
            labels={"x": col, "y": "Count"},
            color_discrete_sequence=["#34d399"],
        )
        bar_fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0",
        )

        pie_fig = px.pie(
            names=labels, values=values,
            title=f"Distribution — {col}",
        )
        pie_fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0",
        )

        total = df[col].count()
        freq_table = [
            {"value": lbl, "count": cnt, "pct": round(cnt / total * 100, 2)}
            for lbl, cnt in zip(labels, values)
        ]

        charts.append({
            "column":      col,
            "unique":      int(df[col].nunique()),
            "bar_chart":   json.loads(bar_fig.to_json()),
            "pie_chart":   json.loads(pie_fig.to_json()),
            "freq_table":  freq_table,
        })

    return {"filename": filename, "categorical_columns": cat_cols, "charts": charts}


# ── Correlation Heatmap ───────────────────────────────────────────────────────

@router.get(
    "/correlation",
    summary="Correlation Heatmap",
    description="Returns a Plotly heatmap of the Pearson correlation matrix for numeric columns.",
)
def get_correlation(
    filename: str = Query(..., description="CSV filename in datasets/"),
):
    df = _load_df(filename)
    num_cols = _numeric_cols(df)

    if len(num_cols) < 2:
        return {
            "filename": filename,
            "message": "Need at least 2 numeric columns for correlation.",
            "chart": None,
        }

    corr = df[num_cols].corr()

    fig = px.imshow(
        corr,
        text_auto=".2f",
        title="Correlation Heatmap",
        color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1,
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e2e8f0",
    )

    return {
        "filename":     filename,
        "columns":      num_cols,
        "correlation":  corr.round(4).to_dict(),
        "chart":        json.loads(fig.to_json()),
    }


# ── Outlier Summary (Before / After) ─────────────────────────────────────────

@router.get(
    "/outlier_summary",
    summary="Outlier Summary — Before vs After Cleaning",
    description=(
        "Returns per-column outlier counts using the Tukey IQR method "
        "for both the raw and cleaned datasets."
    ),
)
def get_outlier_summary(
    raw_filename:   str = Query(..., description="Original CSV filename"),
    clean_filename: str | None = Query(None, description="Cleaned CSV filename (optional)"),
    multiplier: float = Query(1.5, description="IQR fence multiplier"),
):
    raw_df = _load_df(raw_filename)
    clean_df = _load_df(clean_filename) if clean_filename else raw_df

    def _outlier_counts(df: pd.DataFrame) -> dict[str, int]:
        counts: dict[str, int] = {}
        for col in _numeric_cols(df):
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower, upper = q1 - multiplier * iqr, q3 + multiplier * iqr
            counts[col] = int((~df[col].between(lower, upper)).sum())
        return counts

    raw_counts   = _outlier_counts(raw_df)
    clean_counts = _outlier_counts(clean_df)

    all_cols = sorted(set(raw_counts) | set(clean_counts))
    rows = [
        {
            "column":         col,
            "raw_outliers":   raw_counts.get(col, 0),
            "clean_outliers": clean_counts.get(col, 0),
            "removed":        max(0, raw_counts.get(col, 0) - clean_counts.get(col, 0)),
        }
        for col in all_cols
    ]

    return {
        "raw_filename":        raw_filename,
        "clean_filename":      clean_filename or raw_filename,
        "multiplier":          multiplier,
        "total_raw_outliers":  sum(raw_counts.values()),
        "total_clean_outliers": sum(clean_counts.values()),
        "per_column":          rows,
    }
