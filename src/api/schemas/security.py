from pydantic import BaseModel, Field
from typing import Optional


class SecurityPaymentCreate(BaseModel):
    employee_code: Optional[str] = Field(None, description="Employee code e.g. E016")
    employee_id: Optional[str | int] = Field(None, description="Fallback employee code or ID")
    days: float = Field(..., ge=0)
    amount: float = Field(..., gt=0)
    remarks: Optional[str] = ""


class SecurityPaymentResponse(BaseModel):
    id: int
    week_id: int
    employee_id: str | int
    days: float
    amount: float
    remarks: str
    message: str = "Security payment record created successfully"

