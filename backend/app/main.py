from app.api.routes_health import router as health_router
from app.api.routes_metrics import router as metrics_router
from app.errors import ApiError
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

app = FastAPI(
    title="GridBricks",
    description="Wind generation forecast accuracy monitoring",
    version="0.1.0",
)


@app.exception_handler(ApiError)
async def handle_api_error(request, exc: ApiError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request, exc: RequestValidationError):
    problems = "; ".join(
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
        for error in exc.errors()
    )
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "invalid_request", "message": problems}},
    )


app.include_router(metrics_router)
app.include_router(health_router)