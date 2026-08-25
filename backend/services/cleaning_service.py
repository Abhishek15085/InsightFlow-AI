"""
InsightFlow AI — Data Cleaning Service
         and a full cleaning pipeline.

Each function returns (cleaned_df, change_log) where change_log is a
list of human-readable strings describing every change made.
"""

import os
import io
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler, MinMaxScaler

# ── Constants ─────────────────────────────────────────────────────────────────

DATASETS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "datasets")
os.makedirs(DATASETS_DIR, exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _numeric_cols(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include="number").columns.tolist()


def _categorical_cols(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()


import threading
from backend.services import rag_service as rs

def save_cleaned_csv(df: pd.DataFrame, original_filename: str) -> str:
    """Save cleaned DataFrame as {stem}_cleaned.csv and return the filename."""
    stem = os.path.splitext(original_filename)[0]
    cleaned_name = f"{stem}_cleaned.csv"
    path = os.path.join(DATASETS_DIR, cleaned_name)
    df.to_csv(path, index=False)
    
    # Automatically kick off RAG indexing in the background for the new cleaned dataset!
    threading.Thread(target=rs.index_dataset, args=(cleaned_name, df), daemon=True).start()
    
    return cleaned_name


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Convert DataFrame to UTF-8 CSV bytes for download."""
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


# ── Missing Value Handling ──────────────────────────────────────────────────────

MISSING_STRATEGIES = {"mean", "median", "mode", "drop"}


def handle_missing(
    df: pd.DataFrame,
    strategy: str = "mean",
    columns: list[str] | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Handle missing values in the DataFrame.

    Args:
        df:       Input DataFrame.
        strategy: One of 'mean', 'median', 'mode', 'drop'.
        columns:  Subset of columns to apply to; None = all applicable columns.

    Returns:
        (cleaned_df, change_log)
    """
    if strategy not in MISSING_STRATEGIES:
        raise ValueError(f"strategy must be one of {MISSING_STRATEGIES}")

    df = df.copy()
    log: list[str] = []
    before_rows = len(df)

    if strategy == "drop":
        target_cols = columns or df.columns.tolist()
        df_before = len(df)
        df = df.dropna(subset=target_cols)
        dropped = df_before - len(df)
        if dropped:
            log.append(f"Dropped {dropped} rows containing NaN in columns: {target_cols}")
        else:
            log.append("No rows dropped (no missing values in selected columns).")
        return df, log

    # Fill strategies
    num_cols = _numeric_cols(df)
    cat_cols = _categorical_cols(df)

    if columns:
        # Only apply to specified columns
        num_targets = [c for c in columns if c in num_cols]
        cat_targets = [c for c in columns if c in cat_cols]
    else:
        num_targets = num_cols
        cat_targets = cat_cols

    for col in num_targets:
        missing = int(df[col].isna().sum())
        if missing == 0:
            continue
        if strategy == "mean":
            fill_val = df[col].mean()
        elif strategy == "median":
            fill_val = df[col].median()
        elif strategy == "mode":
            mode_vals = df[col].mode()
            fill_val = mode_vals.iloc[0] if len(mode_vals) else 0
        df[col] = df[col].fillna(fill_val)
        log.append(f"[{col}] Filled {missing} NaN(s) with {strategy} ({fill_val:.4f})")

    for col in cat_targets:
        missing = int(df[col].isna().sum())
        if missing == 0:
            continue
        # For categoricals: mode is always used regardless of strategy
        mode_vals = df[col].mode()
        fill_val = mode_vals.iloc[0] if len(mode_vals) else "Unknown"
        df[col] = df[col].fillna(fill_val)
        log.append(f"[{col}] Filled {missing} NaN(s) with mode ('{fill_val}')")

    if not log:
        log.append("No missing values found — nothing changed.")
    return df, log


# ── Encoding ───────────────────────────────────────────────────────────────────

ENCODING_METHODS = {"label", "onehot"}


def encode_columns(
    df: pd.DataFrame,
    method: str = "label",
    columns: list[str] | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Encode categorical columns.

    Args:
        df:      Input DataFrame.
        method:  'label' (Label Encoding) or 'onehot' (One-Hot Encoding).
        columns: Specific columns to encode; None = all categorical columns.

    Returns:
        (encoded_df, change_log)
    """
    if method not in ENCODING_METHODS:
        raise ValueError(f"method must be one of {ENCODING_METHODS}")

    df = df.copy()
    log: list[str] = []
    cat_cols = _categorical_cols(df)
    targets = [c for c in (columns or cat_cols) if c in df.columns]

    if not targets:
        return df, ["No categorical columns to encode."]

    if method == "label":
        le = LabelEncoder()
        for col in targets:
            if col not in cat_cols:
                log.append(f"[{col}] Skipped (not categorical).")
                continue
            unique_vals = df[col].dropna().unique().tolist()
            df[col] = le.fit_transform(df[col].astype(str))
            log.append(f"[{col}] Label encoded → {len(unique_vals)} unique values mapped to integers.")

    elif method == "onehot":
        original_cols = list(df.columns)
        df = pd.get_dummies(df, columns=targets, drop_first=False, dtype=int)
        new_cols = [c for c in df.columns if c not in original_cols]
        log.append(
            f"One-hot encoded {len(targets)} column(s): {targets}. "
            f"Added {len(new_cols)} new binary column(s)."
        )

    return df, log


# ── Scaling ───────────────────────────────────────────────────────────────────

SCALING_METHODS = {"standard", "minmax"}


def scale_columns(
    df: pd.DataFrame,
    method: str = "standard",
    columns: list[str] | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Scale numeric columns.

    Args:
        df:      Input DataFrame.
        method:  'standard' (Z-score normalisation) or 'minmax' (0–1 scaling).
        columns: Specific columns to scale; None = all numeric columns.

    Returns:
        (scaled_df, change_log)
    """
    if method not in SCALING_METHODS:
        raise ValueError(f"method must be one of {SCALING_METHODS}")

    df = df.copy()
    log: list[str] = []
    num_cols = _numeric_cols(df)
    targets = [c for c in (columns or num_cols) if c in num_cols]

    if not targets:
        return df, ["No numeric columns to scale."]

    if method == "standard":
        scaler = StandardScaler()
        label = "StandardScaler (mean=0, std=1)"
    else:
        scaler = MinMaxScaler()
        label = "MinMaxScaler (0–1 range)"

    df[targets] = scaler.fit_transform(df[targets])
    log.append(f"Applied {label} to {len(targets)} column(s): {targets}")

    return df, log


# ── Feature Selection ──────────────────────────────────────────────────────

def select_features(
    df: pd.DataFrame,
    drop_constant: bool = True,
    drop_high_missing_threshold: float | None = 50.0,
    drop_duplicate_cols: bool = True,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Remove low-value columns automatically.

    Args:
        df:                           Input DataFrame.
        drop_constant:                Remove columns with only one unique value.
        drop_high_missing_threshold:  Remove columns where missing% >= threshold (None = skip).
        drop_duplicate_cols:          Remove duplicate columns (same values, different name).

    Returns:
        (cleaned_df, change_log)
    """
    df = df.copy()
    log: list[str] = []
    to_drop: set[str] = set()

    # Constant columns
    if drop_constant:
        const_cols = [c for c in df.columns if df[c].nunique(dropna=False) <= 1]
        if const_cols:
            to_drop.update(const_cols)
            log.append(f"Constant columns removed ({len(const_cols)}): {const_cols}")
        else:
            log.append("No constant columns found.")

    # High-missing columns
    if drop_high_missing_threshold is not None:
        missing_pct = (df.isna().sum() / len(df) * 100)
        high_missing = missing_pct[missing_pct >= drop_high_missing_threshold].index.tolist()
        high_missing = [c for c in high_missing if c not in to_drop]
        if high_missing:
            to_drop.update(high_missing)
            log.append(
                f"High-missing columns removed (≥{drop_high_missing_threshold}% NaN) "
                f"({len(high_missing)}): {high_missing}"
            )
        else:
            log.append(f"No columns exceed {drop_high_missing_threshold}% missing threshold.")

    # Duplicate columns
    if drop_duplicate_cols:
        seen: dict = {}
        dup_cols: list[str] = []
        for col in df.columns:
            if col in to_drop:
                continue
            col_hash = tuple(df[col].fillna("__nan__").astype(str).values)
            if col_hash in seen:
                dup_cols.append(col)
            else:
                seen[col_hash] = col
        if dup_cols:
            to_drop.update(dup_cols)
            log.append(f"Duplicate columns removed ({len(dup_cols)}): {dup_cols}")
        else:
            log.append("No duplicate columns found.")

    if to_drop:
        df = df.drop(columns=list(to_drop))
    else:
        log.append("No columns removed by feature selection.")

    return df, log


# ── Full Pipeline ─────────────────────────────────────────────────────────────

def apply_pipeline(df: pd.DataFrame, config: dict) -> tuple[pd.DataFrame, list[str]]:
    """
    Apply a full cleaning pipeline in the recommended order:
      1. Feature selection (remove junk columns first)
      2. Missing value handling
      3. Encoding
      4. Scaling

    Config schema:
    {
      "feature_selection": {
          "drop_constant": bool,
          "drop_high_missing_threshold": float | null,
          "drop_duplicate_cols": bool
      },
      "missing": {
          "strategy": "mean"|"median"|"mode"|"drop",
          "columns": [str] | null
      },
      "encoding": {
          "method": "label"|"onehot",
          "columns": [str] | null
      },
      "scaling": {
          "method": "standard"|"minmax",
          "columns": [str] | null
      }
    }

    Any top-level key can be omitted to skip that step.
    """
    all_logs: list[str] = []

    if "feature_selection" in config:
        cfg = config["feature_selection"]
        df, logs = select_features(
            df,
            drop_constant=cfg.get("drop_constant", True),
            drop_high_missing_threshold=cfg.get("drop_high_missing_threshold", 50.0),
            drop_duplicate_cols=cfg.get("drop_duplicate_cols", True),
        )
        all_logs += ["[Feature Selection] " + l for l in logs]

    if "missing" in config:
        cfg = config["missing"]
        df, logs = handle_missing(
            df,
            strategy=cfg.get("strategy", "mean"),
            columns=cfg.get("columns"),
        )
        all_logs += ["[Missing] " + l for l in logs]

    if "encoding" in config:
        cfg = config["encoding"]
        df, logs = encode_columns(
            df,
            method=cfg.get("method", "label"),
            columns=cfg.get("columns"),
        )
        all_logs += ["[Encoding] " + l for l in logs]

    if "scaling" in config:
        cfg = config["scaling"]
        df, logs = scale_columns(
            df,
            method=cfg.get("method", "standard"),
            columns=cfg.get("columns"),
        )
        all_logs += ["[Scaling] " + l for l in logs]

    return df, all_logs


# ── Duplicate Removal ─────────────────────────────────────────────────────────

def remove_duplicates(
    df: pd.DataFrame,
    keep: str = "first",
) -> tuple[pd.DataFrame, list[str]]:
    """
    Remove duplicate rows.

    Args:
        df:   Input DataFrame.
        keep: 'first' | 'last' | False (drop all duplicates).

    Returns:
        (cleaned_df, change_log)
    """
    before = len(df)
    if keep == "none":
        df = df.drop_duplicates(keep=False)
    else:
        df = df.drop_duplicates(keep=keep)  # type: ignore[arg-type]
    removed = before - len(df)
    log = [f"Removed {removed} duplicate row(s). Remaining: {len(df)}."]
    return df.reset_index(drop=True), log


# ── Outlier Removal (IQR) ─────────────────────────────────────────────────────

def remove_outliers_iqr(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    multiplier: float = 1.5,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Remove rows that are outliers in any specified numeric column using the
    Tukey IQR fence method: [Q1 - k*IQR, Q3 + k*IQR].

    Args:
        df:          Input DataFrame.
        columns:     Columns to check; None = all numeric columns.
        multiplier:  IQR fence multiplier (default 1.5).

    Returns:
        (cleaned_df, change_log)
    """
    num_cols = _numeric_cols(df)
    cols = [c for c in (columns or num_cols) if c in df.columns and c in num_cols]
    if not cols:
        return df, ["No numeric columns to check for outliers."]

    before = len(df)
    mask = pd.Series([True] * len(df), index=df.index)
    log: list[str] = []

    for col in cols:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - multiplier * iqr
        upper = q3 + multiplier * iqr
        col_mask = df[col].between(lower, upper)
        out_count = (~col_mask).sum()
        mask &= col_mask
        if out_count:
            log.append(f"  '{col}': {out_count} outlier(s) detected (fence [{lower:.3f}, {upper:.3f}]).")

    df = df[mask].reset_index(drop=True)
    removed = before - len(df)
    log.insert(0, f"Outlier removal (IQR ×{multiplier}): removed {removed} row(s). Remaining: {len(df)}.")
    return df, log


# ── Export Clean Dataset ──────────────────────────────────────────────────────

OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "outputs")
os.makedirs(OUTPUTS_DIR, exist_ok=True)


def export_clean_dataset(df: pd.DataFrame, stem: str = "clean_dataset") -> str:
    """
    Save the cleaned DataFrame to outputs/clean_dataset.csv.

    Returns:
        Absolute path of the saved file.
    """
    filename = f"{stem}.csv"
    path = os.path.join(OUTPUTS_DIR, filename)
    df.to_csv(path, index=False)
    return path


# ── Data Quality Score ────────────────────────────────────────────────────────

def compute_quality_score(df: pd.DataFrame) -> float:
    """
    Compute a simple data-quality score (0–100) based on:
    - Missing value ratio   (40 % weight)
    - Duplicate row ratio   (20 % weight)
    - Constant column ratio (20 % weight)
    - Mixed-type column ratio (20 % weight)

    Higher is better.
    """
    if df.empty:
        return 0.0

    total_cells = df.size or 1
    missing_ratio = df.isna().sum().sum() / total_cells

    dup_ratio = df.duplicated().sum() / len(df)

    const_ratio = sum(1 for c in df.columns if df[c].nunique(dropna=False) <= 1) / (len(df.columns) or 1)

    def _is_mixed(series: pd.Series) -> bool:
        if series.dtype != object:
            return False
        types = series.dropna().map(type).nunique()
        return types > 1

    mixed_ratio = sum(1 for c in df.columns if _is_mixed(df[c])) / (len(df.columns) or 1)

    score = 100 * (
        (1 - missing_ratio) * 0.40
        + (1 - dup_ratio)   * 0.20
        + (1 - const_ratio) * 0.20
        + (1 - mixed_ratio) * 0.20
    )
    return round(min(max(score, 0.0), 100.0), 2)

