from pydantic import BaseModel


class EmployeeResponse(BaseModel):
    id: str | int
    employee_code: str | None = None
    name: str
    pay_type: str
    department_id: int | None = None
    default_operation_id: int | None = None
    contractor_id: int | None = None
    shift_rate: float | None = None
    status: str
    worker_type: str | None = None


class EmployeeCreate(BaseModel):
    employee_code: str | None = None
    name: str
    pay_type: str
    department_id: int | None = None
    default_operation_id: int | None = None
    contractor_id: int | None = None
    shift_rate: float | None = None
    worker_type: str | None = None


class EmployeeUpdate(BaseModel):
    employee_code: str | None = None
    name: str
    pay_type: str
    department_id: int | None = None
    default_operation_id: int | None = None
    contractor_id: int | None = None
    shift_rate: float | None = None
    worker_type: str | None = None
    status: str | None = None