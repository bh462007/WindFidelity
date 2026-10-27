
from fastapi import FastAPI

from app.api.routes_metrics import router as metrics_router

app = FastAPI(
    title="GridBricks",
    description="Wind generation forecast accuracy monitoring",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {"status": "healthy"}


app.include_router(metrics_router)
