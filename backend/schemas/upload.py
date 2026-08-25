"""
InsightFlow AI — Upload & Validation Schemas
"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional



class UploadResponse(BaseModel):
    """Response returned by POST /upload"""
    filename:       str
    rows:           int
    columns:        int
    column_names:   List[str]
    dtypes:         Dict[str, str]
    memory_mb:      float
    duplicate_rows: int
    preview:        List[Dict[str, Any]]    # top 10 rows as list of dicts
    summary:        Dict[str, Any]          # descriptive stats snapshot


class DatasetInfo(BaseModel):
    """Lightweight info returned when fetching stored dataset metadata"""
    filename:       str
    rows:           int
    columns:        int
    column_names:   List[str]
    dtypes:         Dict[str, str]
    memory_mb:      float
    duplicate_rows: int
    target_column:  Optional[str] = None



class MissingColumnInfo(BaseModel):
    """Single column's missing value summary"""
    column:        str
    missing_count: int
    missing_pct:   float


class MissingValuesReport(BaseModel):
    """Response for GET /validate/missing"""
    filename:              str
    total_rows:            int
    total_missing_cells:   int
    columns_with_missing:  int
    report:                List[MissingColumnInfo]


class DuplicateReport(BaseModel):
    """Response for GET /validate/duplicates"""
    filename:       str
    total_rows:     int
    duplicate_rows: int
    unique_rows:    int
    duplicate_pct:  float


class ColumnTypesReport(BaseModel):
    """Response for GET /validate/column-types"""
    filename:    str
    numeric:     List[str]
    categorical: List[str]
    date:        List[str]
    boolean:     List[str]
    per_column:  Dict[str, str]


class ColumnStats(BaseModel):
    """Statistics for a single numeric column"""
    mean:     Optional[float]
    median:   Optional[float]
    mode:     Optional[float]
    std:      Optional[float]
    variance: Optional[float]
    min:      Optional[float]
    max:      Optional[float]


class StatisticsReport(BaseModel):
    """Response for GET /validate/statistics"""
    filename:        str
    numeric_columns: List[str]
    statistics:      Dict[str, ColumnStats]

