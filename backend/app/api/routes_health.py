from app.api import routes_metrics
from app.models.responses import HealthResponse, ReadyResponse
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health():
    return {"status": "healthy"}


@router.get("/ready", response_model=ReadyResponse)
def ready():
    cached_days = routes_metrics.cache.size()
    return {
        "status": "ready" if cached_days else "warming",
        "cached_days": cached_days,
    }