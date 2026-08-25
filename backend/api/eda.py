"""
InsightFlow AI — EDA API Routes
         categorical analysis, outlier detection, and the EDA report.

All endpoints accept a `filename` query param matching a previously uploaded
CSV stored in datasets/.
"""

import pandas as pd
from fastapi import APIRouter, Query, HTTPException

from backend.services import upload_service as us
from backend.services import eda_service as es

router = APIRouter(prefix="/eda", tags=["EDA"])


# ── Shared Helper ─────────────────────────────────────────────────────────────

def _load_df(filename: str) -> pd.DataFrame:
    """Load a dataset by filename or raise 404."""
    try:
        return us.load_csv(filename)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ── Distribution Charts ─────────────────────────────────────────────────

@router.get(
    "/distributions",
    summary="Distribution Charts",
    description=(
        "Returns Plotly histogram + box-plot JSON for every numeric column, "
        "plus descriptive statistics (count, mean, std, min, quartiles, max)."
    ),
)
def get_distributions(
    filename: str = Query(..., description="Filename of the uploaded CSV in datasets/"),
):
    df = _load_df(filename)
    charts = es.distribution_charts(df)
    return {
        "filename": filename,
        "numeric_columns": list(charts.keys()),
        "charts": charts,
    }


# ── Correlation Matrix ──────────────────────────────────────────────────

@router.get(
    "/correlation",
    summary="Correlation Matrix",
    description=(
        "Computes the Pearson correlation matrix for numeric columns and returns "
        "a Plotly heatmap JSON plus the raw correlation values."
    ),
)
def get_correlation(
    filename: str = Query(..., description="Filename of the uploaded CSV in datasets/"),
):
    df = _load_df(filename)
    result = es.correlation_matrix(df)
    return {"filename": filename, **result}


# ── Categorical Analysis ────────────────────────────────────────────────

@router.get(
    "/categorical",
    summary="Categorical Analysis",
    description=(
        "For each categorical column returns a top-N frequency bar chart "
        "and a table of top values with counts and percentages."
    ),
)
def get_categorical(
    filename: str = Query(..., description="Filename of the uploaded CSV in datasets/"),
    top_n: int = Query(10, ge=1, le=50, description="Number of top values to show"),
):
    df = _load_df(filename)
    result = es.categorical_analysis(df, top_n=top_n)
    return {
        "filename": filename,
        "categorical_columns": list(result.keys()),
        "analysis": result,
    }


# ── Outlier Detection (IQR) ──────────────────────────────────────────────

@router.get(
    "/outliers",
    summary="Outlier Detection (IQR)",
    description=(
        "Detects outliers in every numeric column using the Tukey IQR fence method. "
        "Returns per-column outlier counts, percentages, and fence bounds."
    ),
)
def get_outliers(
    filename: str = Query(..., description="Filename of the uploaded CSV in datasets/"),
):
    df = _load_df(filename)
    result = es.outlier_detection(df)
    return {"filename": filename, **result}


# ── EDA Report ────────────────────────────────────────────────────────

@router.post(
    "/report",
    summary="Generate EDA Report",
    description=(
        "Compiles a full EDA report and saves it to `reports/{stem}_eda.json`. "
        "Returns a lightweight summary (chart data excluded from the response)."
    ),
)
def generate_report(
    filename: str = Query(..., description="Filename of the uploaded CSV in datasets/"),
):
    df = _load_df(filename)
    result = es.generate_eda_report(df, filename)
    return {"filename": filename, **result}
