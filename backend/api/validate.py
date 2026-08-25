"""
InsightFlow AI — Validation API Routes
         memory usage, and invalid value detection.
"""

import pandas as pd
import numpy as np
from fastapi import APIRouter, Query, HTTPException

from backend.services import upload_service as us
from backend.services import validation_service as vs

router = APIRouter(prefix="/validate", tags=["Validation"])


# ── Shared Helper ─────────────────────────────────────────────────────────────

def _load_df(filename: str) -> pd.DataFrame:
    """Load a dataset by filename or raise 404."""
    try:
        return us.load_csv(filename)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ── Missing Values ────────────────────────────────────────────────────────────

@router.get(
    "/missing",
    summary="Missing Values Analysis",
    description="Returns per-column missing value counts and percentages.",
)
def get_missing_values(
    filename: str = Query(..., description="Filename of the uploaded CSV in datasets/")
):
    df = _load_df(filename)
    report = vs.missing_values_report(df)
    return {
        "filename":             filename,
        "total_rows":           len(df),
        "total_missing_cells":  vs.total_missing_cells(df),
        "columns_with_missing": len(report),
        "report":               report,
    }


# ── Duplicate Analysis ────────────────────────────────────────────────────────

@router.get(
    "/duplicates",
    summary="Duplicate Row Analysis",
    description="Returns total duplicate rows, unique rows, and duplicate percentage.",
)
def get_duplicates(
    filename: str = Query(..., description="Filename of the uploaded CSV in datasets/")
):
    df = _load_df(filename)
    return {"filename": filename, **vs.duplicate_report(df)}


# ── Column Type Detection ─────────────────────────────────────────────────────

@router.get(
    "/column-types",
    summary="Column Type Detection",
    description="Classifies each column as Numeric | Categorical | Date | Boolean.",
)
def get_column_types(
    filename: str = Query(..., description="Filename of the uploaded CSV in datasets/")
):
    df = _load_df(filename)
    type_info = vs.detect_column_types(df)
    return {"filename": filename, **type_info}


# ── Basic Statistics ──────────────────────────────────────────────────────────

@router.get(
    "/statistics",
    summary="Basic Statistics",
    description="Returns mean, median, mode, std, variance, min, max for all numeric columns.",
)
def get_statistics(
    filename: str = Query(..., description="Filename of the uploaded CSV in datasets/")
):
    df = _load_df(filename)
    stats = vs.basic_statistics(df)
    return {
        "filename":        filename,
        "numeric_columns": list(stats.keys()),
        "statistics":      stats,
    }


# ── Memory Usage ──────────────────────────────────────────────────────────────

@router.get(
    "/memory",
    summary="Memory Usage",
    description="Returns per-column and total memory usage of the dataset in bytes and KB.",
)
def get_memory_usage(
    filename: str = Query(..., description="Filename of the uploaded CSV in datasets/")
):
    df = _load_df(filename)
    mem = df.memory_usage(deep=True)
    per_column = {
        col: {"bytes": int(mem[col]), "kb": round(mem[col] / 1024, 3)}
        for col in df.columns
    }
    total_bytes = int(mem.sum())
    return {
        "filename":    filename,
        "total_bytes": total_bytes,
        "total_kb":    round(total_bytes / 1024, 3),
        "total_mb":    round(total_bytes / (1024 ** 2), 4),
        "per_column":  per_column,
        "rows":        len(df),
        "columns":     len(df.columns),
    }


# ── Invalid Values Detection ──────────────────────────────────────────────────

@router.get(
    "/invalid",
    summary="Invalid Values Detection",
    description=(
        "Detects potential invalid values per column: "
        "negative values in non-negative columns, empty strings, "
        "whitespace-only strings, and values that look like placeholders "
        "(e.g. 'N/A', 'none', 'null', '?', '-')."
    ),
)
def get_invalid_values(
    filename: str = Query(..., description="Filename of the uploaded CSV in datasets/")
):
    df = _load_df(filename)
    PLACEHOLDER_PATTERNS = {"n/a", "na", "none", "null", "nan", "?", "-", "", " ", "unknown", "nil"}
    results = []

    for col in df.columns:
        series = df[col]
        issues: list[str] = []
        count = 0

        if series.dtype in (object, "string"):
            # Empty / whitespace strings
            empty_mask = series.dropna().astype(str).str.strip() == ""
            empty_count = int(empty_mask.sum())
            if empty_count:
                issues.append(f"{empty_count} empty/whitespace value(s)")
                count += empty_count

            # Placeholder strings
            placeholder_mask = series.dropna().astype(str).str.lower().str.strip().isin(PLACEHOLDER_PATTERNS)
            ph_count = int(placeholder_mask.sum())
            if ph_count:
                issues.append(f"{ph_count} placeholder value(s) (e.g. 'N/A', 'null')")
                count += ph_count

        elif np.issubdtype(series.dtype, np.number):
            # Negative values in columns whose name suggests non-negative
            non_neg_hints = ("age", "count", "qty", "quantity", "price", "amount", "salary", "score", "rate")
            if any(h in col.lower() for h in non_neg_hints):
                neg_count = int((series < 0).sum())
                if neg_count:
                    issues.append(f"{neg_count} negative value(s) in likely non-negative column")
                    count += neg_count

            # Infinity
            inf_count = int(np.isinf(series).sum())
            if inf_count:
                issues.append(f"{inf_count} infinite value(s)")
                count += inf_count

        if issues:
            results.append({
                "column":      col,
                "dtype":       str(series.dtype),
                "issue_count": count,
                "issues":      issues,
            })

    return {
        "filename":          filename,
        "columns_checked":   len(df.columns),
        "columns_with_issues": len(results),
        "total_issue_count": sum(r["issue_count"] for r in results),
        "details":           results,
    }
