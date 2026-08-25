"""
InsightFlow AI — Health Check Routes
GET /         → Root welcome
GET /health   → Backend health status
"""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/", summary="Root", description="Welcome endpoint for InsightFlow AI")
def root():
    return {
        "app": "InsightFlow AI",
        "description": "Automated Machine Learning & Data Analysis Platform",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@router.get("/health", summary="Health Check", description="Returns backend health status")
def health():
    return {
        "status": "healthy",
        "backend": "connected",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "phase": "Phase 0 — Project Setup",
    }
