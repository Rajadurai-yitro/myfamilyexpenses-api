from datetime import datetime
from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/")
def root():
    return {
        "status": "ok",
        "service": "expense-tracker-api",
        "health": "/health",
        "docs": "/docs",
    }


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "expense-tracker-api",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }
