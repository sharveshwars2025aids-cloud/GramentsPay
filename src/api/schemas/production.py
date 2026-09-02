from pydantic import BaseModel, Field
from typing import Optional


class ProductionRecordCreate(BaseModel):
    work_date: str = Field(..., description="YYYY-MM-DD format")
    employee_code: Optional[str] = Field(None, description="Employee code e.g. E016, 12EC")
    style_no: Optional[str] = Field(None, description="Style number e.g. PEPX031A25, STYLE-99")
    operation_name: Optional[str] = Field(None, description="Operation name e.g. NECK FOLG")
    employee_id: Optional[str | int] = Field(None, description="Fallback employee code or ID")
    style_id: Optional[str | int] = Field(None, description="Fallback style number or ID")
    operation_id: Optional[int | str] = Field(None, description="Fallback operation ID or name")
    type: Optional[str] = ""
    color: Optional[str] = ""
    total_qty: float = Field(..., gt=0)
    rate: float = Field(..., gt=0)
    sizes: Optional[dict[str, float]] = Field(
        default=None,
        description="Size name -> quantity, e.g. {'0/6': 100, 'N/B': 50}. "
                     "Must sum to total_qty, matching the same rule the Excel import enforces.",
    )


class ProductionRecordResponse(BaseModel):
    id: int
    week_id: int
    work_date: str
    employee_id: str | int
    style_id: str | int
    operation_id: int
    type: str
    color: str
    total_qty: float
    rate: float
    total_amount: float
    message: str = "Production record created successfully"

