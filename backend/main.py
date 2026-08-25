"""
InsightFlow AI — FastAPI Backend Entry Point

Run:
    uvicorn backend.main:app --reload --port 8000

Swagger UI:
    http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import api_router

# ── App Initialization ────────────────────────────────────────────────────────

app = FastAPI(
    title="InsightFlow AI",
    description="""
## 🔍 InsightFlow AI — Intelligent Data Cleaning, Exploration & Visualization Platform

Upload a CSV dataset and the platform will:
- **Validate** data quality (missing values, duplicates, types, statistics, memory)
- **Clean & preprocess** the data (handle missing values, encode, scale, remove outliers, remove duplicates)
- **Explore** the data automatically (distributions, correlation, categorical analysis, outlier detection)
- **Visualize** the cleaned dataset in an interactive dashboard with quality scoring
- **Export** the clean dataset as a downloadable CSV

No ML. No authentication. No prediction.
""",
    version="1.0.0",
    contact={
        "name": "InsightFlow AI",
        "email": "contact@insightflow.ai",
    },
    license_info={"name": "MIT"},
)

# ── CORS Middleware ───────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501", "http://127.0.0.1:8501",
        "http://localhost:5173", "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routers ──────────────────────────────────────────────────────────

app.include_router(api_router)
