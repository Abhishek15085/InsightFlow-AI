"""
InsightFlow AI — Validation Service
"""

import pandas as pd
from collections import Counter


# ── Missing Values Analysis ───────────────────────────────────────────────────

def missing_values_report(df: pd.DataFrame) -> list[dict]:
    """
    Return per-column missing-value analysis.

    Returns:
        [{"column": str, "missing_count": int, "missing_pct": float}, ...]
        Only columns with at least 1 missing value are included.
    """
    report = []
    total_rows = len(df)

    for col in df.columns:
        missing = int(df[col].isna().sum())
        if missing > 0:
            pct = round((missing / total_rows) * 100, 2) if total_rows else 0.0
            report.append({
                "column":       col,
                "missing_count": missing,
                "missing_pct":  pct,
            })

    # Sort by missing % descending
    report.sort(key=lambda x: x["missing_pct"], reverse=True)
    return report


def total_missing_cells(df: pd.DataFrame) -> int:
    """Return total number of missing cells across the entire DataFrame."""
    return int(df.isna().sum().sum())


# ── Duplicate Analysis ────────────────────────────────────────────────────────

def duplicate_report(df: pd.DataFrame) -> dict:
    """
    Return duplicate-row summary.

    Returns:
        {
            "total_rows":    int,
            "duplicate_rows": int,
            "unique_rows":   int,
            "duplicate_pct": float,
        }
    """
    total     = len(df)
    dupes     = int(df.duplicated().sum())
    unique    = total - dupes
    dupe_pct  = round((dupes / total) * 100, 2) if total else 0.0

    return {
        "total_rows":     total,
        "duplicate_rows": dupes,
        "unique_rows":    unique,
        "duplicate_pct":  dupe_pct,
    }


# ── Column Type Detection ────────────────────────────────────────────────────

def _is_boolean_series(series: pd.Series) -> bool:
    """Heuristic: boolean if only 2 unique non-null values that look like bool."""
    non_null = series.dropna()
    if non_null.empty:
        return False
    unique_vals = set(str(v).strip().lower() for v in non_null.unique())
    bool_sets = [
        {"true", "false"},
        {"yes", "no"},
        {"1", "0"},
        {"t", "f"},
        {"y", "n"},
    ]
    return unique_vals in bool_sets or (
        len(unique_vals) <= 2 and series.dtype == bool
    )


def _is_date_series(series: pd.Series) -> bool:
    """Try parsing a sample as dates; True if >80 % parse successfully."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    sample = series.dropna().head(50)
    if sample.empty:
        return False
    try:
        parsed = pd.to_datetime(sample, infer_datetime_format=True, errors="coerce")
        success_rate = parsed.notna().mean()
        return success_rate >= 0.80
    except Exception:
        return False


def detect_column_types(df: pd.DataFrame) -> dict:
    """
    Classify each column as Numeric | Categorical | Date | Boolean.

    Returns:
        {
            "numeric":     [col, ...],
            "categorical": [col, ...],
            "date":        [col, ...],
            "boolean":     [col, ...],
            "per_column":  {col: type_str, ...},
        }
    """
    result: dict = {
        "numeric":     [],
        "categorical": [],
        "date":        [],
        "boolean":     [],
        "per_column":  {},
    }

    for col in df.columns:
        series = df[col]

        if pd.api.types.is_bool_dtype(series) or _is_boolean_series(series):
            category = "boolean"
        elif pd.api.types.is_numeric_dtype(series):
            category = "numeric"
        elif _is_date_series(series):
            category = "date"
        else:
            category = "categorical"

        result[category].append(col)
        result["per_column"][col] = category

    return result


# ── Basic Statistics ───────────────────────────────────────────────────────

def basic_statistics(df: pd.DataFrame) -> dict:
    """
    Compute mean, median, mode, std, variance, min, max for every numeric column.

    Returns:
        {col: {"mean": ..., "median": ..., "mode": ..., "std": ...,
               "variance": ..., "min": ..., "max": ...}, ...}
    """
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    stats: dict = {}

    for col in numeric_cols:
        series = df[col].dropna()
        if series.empty:
            stats[col] = {k: None for k in
                          ["mean", "median", "mode", "std", "variance", "min", "max"]}
            continue

        mode_series = series.mode()
        stats[col] = {
            "mean":     round(float(series.mean()), 6),
            "median":   round(float(series.median()), 6),
            "mode":     round(float(mode_series.iloc[0]), 6) if len(mode_series) else None,
            "std":      round(float(series.std()), 6),
            "variance": round(float(series.var()), 6),
            "min":      round(float(series.min()), 6),
            "max":      round(float(series.max()), 6),
        }

    return stats
