
import os
from datetime import time

# Default: Nord Pool GB day-ahead gate closure, 09:50 GMT. In January UK time equals UTC.
FORECAST_CUTOFF_UTC = time.fromisoformat(
    os.getenv("FORECAST_CUTOFF_UTC", "09:50")
)
