from pydantic import BaseModel, Field
from typing import Optional, List


class BiometricMismatchItem(BaseModel):
    week_id: int
    employee_id: int
    employee_name: str
    work_date: str
    entered_shift_value: float
    biometric_shift_value: float
    diff: float
    headline: str
    message: str


class OverrideRequest(BaseModel):
    work_date: str
    employee_code: Optional[str] = None
    employee_id: Optional[int] = None
    biometric_shift_value: float
    entered_shift_value: float
    overridden_by: str = "Accountant"
    reason: Optional[str] = "Manual verification override"



class BulkOverrideRequest(BaseModel):
    overridden_by: str = "Accountant"
    reason: Optional[str] = "Bulk verification override"


class BiometricImportResponse(BaseModel):
    week_id: int
    filename: str
    records_inserted: int
    message: str = "Biometric attendance file imported successfully"


class OverrideResponse(BaseModel):
    status: str = "success"
    message: str
