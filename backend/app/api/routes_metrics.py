
from datetime import date

import requests
from fastapi import APIRouter, HTTPException, Query

from app.services.analysis_service import analyse_day

router = APIRouter(prefix="/api/v1", tags=["metrics"])


@router.get("/metrics")
def get_metrics(
    day: date = Query(
        ...,
        description="UTC delivery date, formatted YYYY-MM-DD",
    ),
):
    try:
        return analyse_day(day)
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not retrieve data from Elexon",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
