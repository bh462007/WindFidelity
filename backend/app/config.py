
import os

FORECAST_MIN_LEAD_MINUTES = int(
    os.getenv("FORECAST_MIN_LEAD_MINUTES", "120")
)
