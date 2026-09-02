from pydantic import BaseModel, Field
from typing import Optional


class ShiftRecordCreate(BaseModel):
    work_date: str = Field(..., description="YYYY-MM-DD format")
    employee_code: Optional[str] = Field(None, description="Employee code e.g. E016, 12EC")
    operation_name: Optional[str] = Field(None, description="Operation name e.g. NECK FOLG")
    style_no: Optional[str] = Field(None, description="Style number e.g. PEPX031A25")
    employee_id: Optional[str | int] = Field(None, description="Fallback employee code or ID")
    operation_id: Optional[int | str] = Field(None, description="Fallback operation ID or name")
    style_id: Optional[str | int] = Field(None, description="Fallback style number or ID")
    type: Optional[str] = ""
    color: Optional[str] = ""
    item: Optional[str] = ""
    shifts: float = Field(..., ge=0, description="Shifts worked (e.g. 0.5, 1.0)")
    shift_rate: float = Field(..., ge=0, description="Shift rate per shift")


class ShiftRecordResponse(BaseModel):
    id: int
    week_id: int
    work_date: str
    employee_id: str | int
    operation_id: Optional[int] = None
    style_id: Optional[str | int] = None
    type: str
    color: str
    item: str
    shifts: float
    shift_rate: float
    daily_salary: float
    message: str = "Shift record created successfully"

