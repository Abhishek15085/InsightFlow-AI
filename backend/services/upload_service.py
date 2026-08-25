"""
InsightFlow AI — Upload Service
"""

import os
import hashlib
import pandas as pd
from fastapi import UploadFile

# ── Constants ────────────────────────────────────────────────────────────────

DATASETS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "datasets")
os.makedirs(DATASETS_DIR, exist_ok=True)


# ── File I/O ─────────────────────────────────────────────────────────────────

async def save_csv(file: UploadFile) -> tuple[str, pd.DataFrame]:
    """
    Save the uploaded CSV to the datasets/ directory.

    Returns:
        (saved_filepath, dataframe)
    """
    contents = await file.read()
    # Derive a safe filename
    safe_name = os.path.basename(file.filename or "upload.csv")
    filepath = os.path.join(DATASETS_DIR, safe_name)

    with open(filepath, "wb") as f:
        f.write(contents)

    # Parse into DataFrame
    import io
    df = pd.read_csv(io.BytesIO(contents))
    return safe_name, df


def load_csv(filename: str) -> pd.DataFrame:
    """Load a previously saved CSV by filename."""
    filepath = os.path.join(DATASETS_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset '{filename}' not found in datasets/")
    return pd.read_csv(filepath)


# ── Metadata Helpers ─────────────────────────────────────────────────────────

def get_shape(df: pd.DataFrame) -> tuple[int, int]:
    """Return (rows, columns)."""
    return df.shape[0], df.shape[1]


def get_column_names(df: pd.DataFrame) -> list[str]:
    """Return list of column names."""
    return df.columns.tolist()


def get_dtypes(df: pd.DataFrame) -> dict[str, str]:
    """Return {column_name: dtype_string} mapping."""
    return {col: str(dtype) for col, dtype in df.dtypes.items()}


def get_memory_mb(df: pd.DataFrame) -> float:
    """Return memory usage of the DataFrame in MB (2 dp)."""
    mem_bytes = df.memory_usage(deep=True).sum()
    return round(mem_bytes / (1024 ** 2), 4)


def get_duplicate_count(df: pd.DataFrame) -> int:
    """Return number of fully duplicated rows."""
    return int(df.duplicated().sum())


# ── Preview ───────────────────────────────────────────────────────────────────

def get_preview(df: pd.DataFrame, n: int = 10) -> list[dict]:
    """Return top-n rows as a list of dicts (JSON-serialisable)."""
    return df.head(n).to_dict(orient="records")


# ── Basic Statistics ──────────────────────────────────────────────────────────

def get_basic_stats(df: pd.DataFrame) -> dict:
    """
    Compute descriptive statistics for numeric columns.

    Returns:
        {
            "numeric_stats": {col: {mean, median, mode, std, variance, min, max}},
        }
    """
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    stats: dict = {}

    for col in numeric_cols:
        series = df[col].dropna()
        mode_vals = series.mode()
        stats[col] = {
            "mean":     round(float(series.mean()), 6)     if len(series) else None,
            "median":   round(float(series.median()), 6)   if len(series) else None,
            "mode":     round(float(mode_vals.iloc[0]), 6) if len(mode_vals) else None,
            "std":      round(float(series.std()), 6)      if len(series) else None,
            "variance": round(float(series.var()), 6)      if len(series) else None,
            "min":      round(float(series.min()), 6)      if len(series) else None,
            "max":      round(float(series.max()), 6)      if len(series) else None,
        }

    return {"numeric_stats": stats}
