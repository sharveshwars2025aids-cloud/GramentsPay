from pydantic import BaseModel, Field
from typing import Optional


class ExpenseCreate(BaseModel):
    category: str
    amount: float = Field(..., gt=0)
    notes: Optional[str] = ""


class ExpenseResponse(BaseModel):
    id: int
    week_id: int
    category: str
    amount: float
    notes: str
    message: str = "Expense record created successfully"
