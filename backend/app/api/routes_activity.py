from typing import Annotated

from app.models.responses import ActivityResponse
from app.services.activity import activity_log
from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/v1", tags=["activity"])


@router.get("/activity", response_model=ActivityResponse)
def get_activity(limit: Annotated[int, Query(ge=1, le=100)] = 50):
    return {
        "events": activity_log.recent(limit),
        "capacity": activity_log.max_events,
    }