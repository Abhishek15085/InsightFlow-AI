"""
InsightFlow AI — API Routes Package
Registers all route modules into a single router.
"""

from fastapi import APIRouter
from backend.api.health    import router as health_router
from backend.api.upload    import router as upload_router
from backend.api.validate  import router as validate_router
from backend.api.eda       import router as eda_router
from backend.api.clean     import router as clean_router
from backend.api.dashboard import router as dashboard_router
from backend.api.chat      import router as chat_router

api_router = APIRouter()

api_router.include_router(health_router,     tags=["Health"])
api_router.include_router(upload_router,     tags=["Upload"])
api_router.include_router(validate_router)   # prefix="/validate"
api_router.include_router(eda_router)        # prefix="/eda"
api_router.include_router(clean_router)      # prefix="/clean"
api_router.include_router(dashboard_router)  # prefix="/dashboard"
api_router.include_router(chat_router)
