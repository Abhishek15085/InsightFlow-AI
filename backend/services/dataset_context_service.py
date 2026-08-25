"""
InsightFlow AI — Dataset Context Service

Generates a rich, AI-readable text context from an uploaded CSV file.
This context is sent to NVIDIA Nemotron so it can answer dataset-specific
questions (actual data values, filtering, aggregation, etc.).
"""

import os
import io
import pandas as pd
import numpy as np

DATASETS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "datasets")

# Limits to keep context within token budget
MAX_SAMPLE_ROWS = 500       # rows to include as raw CSV (increase for better coverage)
MAX_CATEGORIES  = 10        # top N values to show per categorical column
MAX_COLUMNS_FULL = 30       # if more columns than this, trim sample to save tokens


def _load_df(filename: str) -> pd.DataFrame | None:
    """Load CSV from datasets/ directory. Returns None if not found."""
    path = os.path.join(DATASETS_DIR, filename)
    if not os.path.exists(path):
        return None
    try:
        return pd.read_csv(path, low_memory=False)
    except Exception:
        return None


def build_rich_context(filename: str) -> str:
    """
    Build a comprehensive text summary of the dataset that Nemotron can reason over.

    Includes:
    - Basic info (rows, columns)
    - Column types and statistics
    - Value distributions for categorical columns
    - A sample of actual rows in CSV format
    - Missing value summary

    Args:
        filename: The CSV filename (basename only, stored in datasets/)

    Returns:
        A formatted string to be injected into the AI system prompt.
        Returns an empty string if the file cannot be loaded.
    """
    df = _load_df(filename)
    if df is None:
        return ""

    rows, cols = df.shape
    lines = []

    # ── Basic info ────────────────────────────────────────────────────────────
    lines.append(f"=== DATASET CONTEXT ===")
    lines.append(f"File      : {filename}")
    lines.append(f"Rows      : {rows:,}")
    lines.append(f"Columns   : {cols}")
    lines.append("")

    # ── Column details ────────────────────────────────────────────────────────
    lines.append("--- Column Details ---")
    for col in df.columns:
        dtype = df[col].dtype
        n_missing = int(df[col].isna().sum())
        pct_missing = round(n_missing / rows * 100, 1) if rows > 0 else 0
        n_unique = int(df[col].nunique())

        if pd.api.types.is_numeric_dtype(dtype):
            col_min  = df[col].min()
            col_max  = df[col].max()
            col_mean = round(float(df[col].mean()), 2) if not df[col].isna().all() else "N/A"
            lines.append(
                f"  {col} [numeric]: "
                f"min={col_min}, max={col_max}, mean={col_mean}, "
                f"unique={n_unique}, missing={n_missing} ({pct_missing}%)"
            )
        else:
            top_vals = df[col].value_counts(dropna=True).head(MAX_CATEGORIES)
            top_str  = ", ".join(f"{v}({c})" for v, c in top_vals.items())
            lines.append(
                f"  {col} [categorical/text]: "
                f"unique={n_unique}, missing={n_missing} ({pct_missing}%), "
                f"top values: [{top_str}]"
            )
    lines.append("")

    # ── Sample rows ───────────────────────────────────────────────────────────
    sample_rows = min(MAX_SAMPLE_ROWS, rows)
    lines.append(f"--- Sample Data ({sample_rows} rows) ---")

    # If too many columns, limit to numeric + first few categorical for readability
    display_df = df
    if cols > MAX_COLUMNS_FULL:
        numeric_cols   = df.select_dtypes(include="number").columns.tolist()
        text_cols      = df.select_dtypes(exclude="number").columns.tolist()[:5]
        display_cols   = text_cols + numeric_cols
        display_df     = df[display_cols]

    sample_csv = display_df.head(sample_rows).to_csv(index=False)
    lines.append(sample_csv)

    lines.append("=== END DATASET CONTEXT ===")
    return "\n".join(lines)


def get_context_for_chat(filename: str) -> str:
    """
    Main entry point called by the chat endpoint.

    If filename is blank or file not found, returns empty string
    (Nemotron will still work, just without data context).
    """
    if not filename:
        return ""
    return build_rich_context(filename)
