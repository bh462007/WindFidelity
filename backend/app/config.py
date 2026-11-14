
import os
from datetime import time
from pathlib import Path

# Default: Nord Pool GB day-ahead gate closure, 09:50 GMT. In January UK time equals UTC.
FORECAST_CUTOFF_UTC = time.fromisoformat(
    os.getenv("FORECAST_CUTOFF_UTC", "09:50")
)


# Built frontend (npm run build). Absent in a plain backend checkout; the API works without it.
FRONTEND_DIST = Path(
    os.getenv("FRONTEND_DIST", str(Path(__file__).resolve().parents[2] / "frontend" / "dist"))
)