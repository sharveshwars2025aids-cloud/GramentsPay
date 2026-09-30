from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from core.exceptions import (
    DuplicateRecordError,
    RecordNotFoundError,
    BusinessRuleError,
)

from api.routers import (
    employees,
    departments,
    contractors,
    operations,
    styles,
    operation_aliases,
    imports,
    weekly,
    production,
    shifts,
    outsource,
    security,
    expenses,
    deductions,
    bonuses,
    biometric,
    reports,
    dashboard,
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
EXPORTS_DIR = BASE_DIR.parent / "exports"

EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Garments Automation API",
    version="1.0.0",
)

app.include_router(employees.router)
app.include_router(departments.router)
app.include_router(contractors.router)
app.include_router(operations.router)
app.include_router(styles.router)
app.include_router(imports.router)
app.include_router(operation_aliases.router)
app.include_router(weekly.router)
app.include_router(production.router)
app.include_router(shifts.router)
app.include_router(outsource.router)
app.include_router(security.router)
app.include_router(expenses.router)
app.include_router(deductions.router)
app.include_router(bonuses.router)
app.include_router(biometric.router)
app.include_router(reports.router)
app.include_router(dashboard.router)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

if EXPORTS_DIR.exists():
    app.mount("/exports", StaticFiles(directory=str(EXPORTS_DIR)), name="exports")


@app.exception_handler(DuplicateRecordError)
async def duplicate_record_handler(
    request: Request,
    exc: DuplicateRecordError,
):
    return JSONResponse(
        status_code=409,
        content={
            "detail": str(exc),
        },
    )


@app.exception_handler(RecordNotFoundError)
async def record_not_found_handler(
    request: Request,
    exc: RecordNotFoundError,
):
    return JSONResponse(
        status_code=404,
        content={
            "detail": str(exc),
        },
    )


@app.exception_handler(BusinessRuleError)
async def business_rule_handler(
    request: Request,
    exc: BusinessRuleError,
):
    return JSONResponse(
        status_code=400,
        content={
            "detail": str(exc),
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(
    request: Request,
    exc: ValueError,
):
    return JSONResponse(
        status_code=409,
        content={
            "detail": str(exc),
        },
    )


@app.get("/")
def home():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "message": "Garments Automation API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "OK"
    }