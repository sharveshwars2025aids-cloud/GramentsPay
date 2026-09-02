from pydantic import BaseModel, Field
from typing import Optional


class DeductionCreate(BaseModel):
    employee_code: Optional[str] = Field(None, description="Employee code e.g. E016")
    employee_id: Optional[str | int] = Field(None, description="Fallback employee code or ID")
    deduction_type: str
    amount: float = Field(..., gt=0)
    notes: Optional[str] = ""


class DeductionResponse(BaseModel):
    id: int
    week_id: int
    employee_id: str | int
    deduction_type: str
    amount: float
    notes: str
    message: str = "Deduction record created successfully"

