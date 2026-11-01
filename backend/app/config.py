
import os
from datetime import time

FORECAST_CUTOFF_UTC = time.fromisoformat(
    os.getenv("FORECAST_CUTOFF_UTC", "12:00")
)
