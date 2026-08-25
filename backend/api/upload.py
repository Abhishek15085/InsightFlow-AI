"""
InsightFlow AI — Upload API Routes
"""

import os
import io
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks

from backend.schemas.upload import UploadResponse
from backend.services import upload_service as us
from backend.services import rag_service as rs

router = APIRouter()

# ── Task 1.1 — Upload Endpoint ────────────────────────────────────────────────

@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload CSV Dataset",
    description="""
        Upload a CSV dataset.
        
        Returns metadata: filename, size, row count, column count, and a data preview.
    """,
    tags=["Upload"],
)
async def upload_csv(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # Validate content type
    filename = file.filename or ""
    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported. Please upload a .csv file.",
        )

    try:
        saved_name, df = await us.save_csv(file)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {exc}")

    # Kick off RAG dataset indexing in the background using ChromaDB!
    background_tasks.add_task(rs.index_dataset, saved_name, df)

    rows, cols = us.get_shape(df)

    return UploadResponse(
        filename=saved_name,
        rows=rows,
        columns=cols,
        column_names=us.get_column_names(df),
        dtypes=us.get_dtypes(df),
        memory_mb=us.get_memory_mb(df),
        duplicate_rows=us.get_duplicate_count(df),
        preview=us.get_preview(df, n=10),
        summary=us.get_basic_stats(df),
    )
