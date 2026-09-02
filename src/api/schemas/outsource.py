from pydantic import BaseModel, Field
from typing import Optional


class OutsourcePaymentCreate(BaseModel):
    style: str
    item: str
    qty: float = Field(..., gt=0)
    rate: float = Field(..., gt=0)
    centre_name: Optional[str] = ""
    remarks: Optional[str] = ""


class OutsourcePaymentResponse(BaseModel):
    id: int
    week_id: int
    style: str
    item: str
    qty: float
    rate: float
    amount: float
    centre_name: str
    remarks: str
    message: str = "Outsource payment record created successfully"
