
from datetime import time
import os

FORECAST_CUTOFF_UTC = time.fromisoformat(
    os.getenv("FORECAST_CUTOFF_UTC", "12:00")
)
