from typing import Any, Optional
from pydantic import BaseModel, Field


class WeekBase(BaseModel):
    week_start: str = Field(..., description="YYYY-MM-DD format")
    week_end: str = Field(..., description="YYYY-MM-DD format")


class WeekCreate(WeekBase):
    pass


class WeekUpdate(BaseModel):
    week_start: Optional[str] = None
    week_end: Optional[str] = None
    closing_generated: Optional[int] = None


class WeekResponse(WeekBase):
    id: int
    label: str
    closing_generated: int = 0
    created_at: Optional[str] = None


class WeeklySalaryResponse(BaseModel):
    week_id: int
    employees: dict[int, dict[str, Any]]
    contractors: list[Any]
    expenses: list[Any]

    total_salary: float
    total_contractor_commission: float
    total_factory_expense: float


class WeeklyClosingResponse(BaseModel):
    week_id: int

    employees_count: int

    total_salary: float
    total_contractor_commission: float
    total_factory_expense: float

    grand_total: float

    file_path: str


class ClosingReadinessResponse(BaseModel):
    week_id: int
    ready: bool
    pending_categories: list[str]
    biometric_mismatch_count: int