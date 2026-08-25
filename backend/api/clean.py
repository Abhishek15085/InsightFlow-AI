"""
InsightFlow AI — Data Cleaning API Routes
         duplicate removal, outlier removal, export, and download.
"""

import os
import pandas as pd
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field
import io

from backend.services import upload_service as us
from backend.services import cleaning_service as cs

router = APIRouter(prefix="/clean", tags=["Cleaning"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_df(filename: str) -> pd.DataFrame:
    """Load a dataset by filename or raise 404."""
    try:
        return us.load_csv(filename)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


def _df_preview(df: pd.DataFrame, n: int = 10) -> list[dict]:
    return df.head(n).fillna("NaN").astype(str).to_dict(orient="records")


# ── Pydantic Request Bodies ───────────────────────────────────────────────────

class MissingRequest(BaseModel):
    strategy: str = Field("mean", description="mean | median | mode | drop")
    columns: list[str] | None = Field(None, description="Specific columns; null = all")


class EncodeRequest(BaseModel):
    method: str = Field("label", description="label | onehot")
    columns: list[str] | None = Field(None, description="Specific columns; null = all categorical")


class ScaleRequest(BaseModel):
    method: str = Field("standard", description="standard | minmax")
    columns: list[str] | None = Field(None, description="Specific columns; null = all numeric")


class FeatureRequest(BaseModel):
    drop_constant: bool = Field(True, description="Remove constant-value columns")
    drop_high_missing_threshold: float | None = Field(
        50.0, description="Remove columns with >= this % missing; null = skip"
    )
    drop_duplicate_cols: bool = Field(True, description="Remove duplicate columns")


class DuplicateRequest(BaseModel):
    keep: str = Field("first", description="first | last | none (drop all)")


class OutlierRequest(BaseModel):
    columns: list[str] | None = Field(None, description="Numeric columns to check; null = all")
    multiplier: float = Field(1.5, description="IQR fence multiplier (default 1.5)")


class PipelineConfig(BaseModel):
    feature_selection: FeatureRequest | None = None
    missing: MissingRequest | None = None
    encoding: EncodeRequest | None = None
    scaling: ScaleRequest | None = None
    save_cleaned: bool = Field(True, description="Save result to datasets/{stem}_cleaned.csv")


# ── Missing Value Handling ────────────────────────────────────────────────────

@router.post(
    "/missing",
    summary="Handle Missing Values",
    description="Fill or drop missing values. Strategies: `mean`, `median`, `mode`, `drop`.",
)
def handle_missing(
    body: MissingRequest,
    filename: str = Query(..., description="Filename of the uploaded CSV in datasets/"),
):
    df = _load_df(filename)
    try:
        cleaned_df, log = cs.handle_missing(df, strategy=body.strategy, columns=body.columns)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    cleaned_name = cs.save_cleaned_csv(cleaned_df, filename)
    return {
        "filename": filename,
        "cleaned_filename": cleaned_name,
        "strategy": body.strategy,
        "original_shape": {"rows": len(df), "columns": len(df.columns)},
        "cleaned_shape": {"rows": len(cleaned_df), "columns": len(cleaned_df.columns)},
        "change_log": log,
        "preview": _df_preview(cleaned_df),
    }


# ── Encoding ──────────────────────────────────────────────────────────────────

@router.post(
    "/encode",
    summary="Encode Categorical Columns",
    description="Encode categorical columns using Label Encoding or One-Hot Encoding.",
)
def encode_columns(
    body: EncodeRequest,
    filename: str = Query(..., description="Filename of the uploaded CSV in datasets/"),
):
    df = _load_df(filename)
    try:
        cleaned_df, log = cs.encode_columns(df, method=body.method, columns=body.columns)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    cleaned_name = cs.save_cleaned_csv(cleaned_df, filename)
    return {
        "filename": filename,
        "cleaned_filename": cleaned_name,
        "method": body.method,
        "original_shape": {"rows": len(df), "columns": len(df.columns)},
        "cleaned_shape": {"rows": len(cleaned_df), "columns": len(cleaned_df.columns)},
        "change_log": log,
        "preview": _df_preview(cleaned_df),
    }


# ── Scaling ───────────────────────────────────────────────────────────────────

@router.post(
    "/scale",
    summary="Scale Numeric Columns",
    description="Scale numeric columns using StandardScaler (Z-score) or MinMaxScaler (0–1).",
)
def scale_columns(
    body: ScaleRequest,
    filename: str = Query(..., description="Filename of the uploaded CSV in datasets/"),
):
    df = _load_df(filename)
    try:
        cleaned_df, log = cs.scale_columns(df, method=body.method, columns=body.columns)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    cleaned_name = cs.save_cleaned_csv(cleaned_df, filename)
    return {
        "filename": filename,
        "cleaned_filename": cleaned_name,
        "method": body.method,
        "original_shape": {"rows": len(df), "columns": len(df.columns)},
        "cleaned_shape": {"rows": len(cleaned_df), "columns": len(cleaned_df.columns)},
        "change_log": log,
        "preview": _df_preview(cleaned_df),
    }


# ── Feature Selection ─────────────────────────────────────────────────────────

@router.post(
    "/features",
    summary="Feature Selection",
    description="Automatically remove constant columns, high-missing columns, and duplicate columns.",
)
def select_features(
    body: FeatureRequest,
    filename: str = Query(..., description="Filename of the uploaded CSV in datasets/"),
):
    df = _load_df(filename)
    cleaned_df, log = cs.select_features(
        df,
        drop_constant=body.drop_constant,
        drop_high_missing_threshold=body.drop_high_missing_threshold,
        drop_duplicate_cols=body.drop_duplicate_cols,
    )

    cleaned_name = cs.save_cleaned_csv(cleaned_df, filename)
    return {
        "filename": filename,
        "cleaned_filename": cleaned_name,
        "original_shape": {"rows": len(df), "columns": len(df.columns)},
        "cleaned_shape": {"rows": len(cleaned_df), "columns": len(cleaned_df.columns)},
        "columns_removed": len(df.columns) - len(cleaned_df.columns),
        "change_log": log,
        "preview": _df_preview(cleaned_df),
    }


# ── Duplicate Removal ─────────────────────────────────────────────────────────

@router.post(
    "/duplicates",
    summary="Remove Duplicate Rows",
    description="Remove duplicate rows. Strategy: `first` (keep first), `last` (keep last), `none` (drop all).",
)
def remove_duplicates(
    body: DuplicateRequest,
    filename: str = Query(..., description="Filename of the uploaded CSV in datasets/"),
):
    df = _load_df(filename)
    before_rows = len(df)
    cleaned_df, log = cs.remove_duplicates(df, keep=body.keep)

    cleaned_name = cs.save_cleaned_csv(cleaned_df, filename)
    return {
        "filename": filename,
        "cleaned_filename": cleaned_name,
        "keep": body.keep,
        "original_rows": before_rows,
        "cleaned_rows": len(cleaned_df),
        "duplicates_removed": before_rows - len(cleaned_df),
        "change_log": log,
        "preview": _df_preview(cleaned_df),
    }


# ── Outlier Removal (IQR) ─────────────────────────────────────────────────────

@router.post(
    "/outliers",
    summary="Remove Outliers (IQR)",
    description=(
        "Remove rows that are outliers in numeric columns using the Tukey IQR fence. "
        "Leave columns null to check all numeric columns."
    ),
)
def remove_outliers(
    body: OutlierRequest,
    filename: str = Query(..., description="Filename of the uploaded CSV in datasets/"),
):
    df = _load_df(filename)
    before_rows = len(df)
    cleaned_df, log = cs.remove_outliers_iqr(df, columns=body.columns, multiplier=body.multiplier)

    cleaned_name = cs.save_cleaned_csv(cleaned_df, filename)
    return {
        "filename": filename,
        "cleaned_filename": cleaned_name,
        "multiplier": body.multiplier,
        "original_rows": before_rows,
        "cleaned_rows": len(cleaned_df),
        "outliers_removed": before_rows - len(cleaned_df),
        "change_log": log,
        "preview": _df_preview(cleaned_df),
    }


# ── Export Clean Dataset ──────────────────────────────────────────────────────

@router.post(
    "/export",
    summary="Export Clean Dataset",
    description="Save the current cleaned CSV to `outputs/clean_dataset.csv`.",
)
def export_dataset(
    filename: str = Query(..., description="Cleaned CSV filename in datasets/"),
    stem: str = Query("clean_dataset", description="Output filename stem (without .csv)"),
):
    df = _load_df(filename)
    path = cs.export_clean_dataset(df, stem=stem)
    return {
        "filename": filename,
        "exported_to": path,
        "rows": len(df),
        "columns": len(df.columns),
        "message": f"Clean dataset saved to outputs/{stem}.csv",
    }


# ── Full Pipeline ─────────────────────────────────────────────────────────────

@router.post(
    "/pipeline",
    summary="Full Cleaning Pipeline",
    description=(
        "Apply all cleaning steps in one call: feature selection → missing handling → "
        "encoding → scaling. Any step can be omitted."
    ),
)
def run_pipeline(
    body: PipelineConfig,
    filename: str = Query(..., description="Filename of the uploaded CSV in datasets/"),
):
    df = _load_df(filename)

    config = {}
    if body.feature_selection:
        config["feature_selection"] = body.feature_selection.model_dump()
    if body.missing:
        config["missing"] = body.missing.model_dump()
    if body.encoding:
        config["encoding"] = body.encoding.model_dump()
    if body.scaling:
        config["scaling"] = body.scaling.model_dump()

    cleaned_df, log = cs.apply_pipeline(df, config)

    cleaned_name = None
    if body.save_cleaned:
        cleaned_name = cs.save_cleaned_csv(cleaned_df, filename)

    return {
        "filename": filename,
        "cleaned_filename": cleaned_name,
        "original_shape": {"rows": len(df), "columns": len(df.columns)},
        "cleaned_shape": {"rows": len(cleaned_df), "columns": len(cleaned_df.columns)},
        "steps_applied": list(config.keys()),
        "change_log": log,
        "preview": _df_preview(cleaned_df),
    }


# ── Download Cleaned CSV ──────────────────────────────────────────────────────

@router.get(
    "/download",
    summary="Download Cleaned CSV",
    description=(
        "Stream the cleaned CSV file as a downloadable attachment. "
        "Use the `cleaned_filename` returned by any cleaning endpoint."
    ),
    response_class=StreamingResponse,
)
def download_cleaned(
    filename: str = Query(..., description="Cleaned filename (e.g. titanic_cleaned.csv)"),
):
    df = _load_df(filename)
    csv_bytes = cs.df_to_csv_bytes(df)
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Download Output ───────────────────────────────────────────────────────────

@router.get(
    "/download_output",
    summary="Download Exported Output CSV",
    description="Download the file saved to outputs/ by /clean/export.",
)
def download_output(
    stem: str = Query("clean_dataset", description="Output filename stem (without .csv)"),
):
    outputs_dir = os.path.join(os.path.dirname(__file__), "..", "..", "outputs")
    file_path = os.path.abspath(os.path.join(outputs_dir, f"{stem}.csv"))
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"Output file '{stem}.csv' not found. Run /clean/export first.",
        )
    return FileResponse(path=file_path, media_type="text/csv", filename=f"{stem}.csv")
