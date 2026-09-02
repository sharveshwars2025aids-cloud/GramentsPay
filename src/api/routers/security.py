from typing import Annotated
import sqlite3
from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_db
from api.schemas.security import SecurityPaymentCreate, SecurityPaymentResponse
from security_manager import insert_security_payment, week_exists
from database import get_employee_id_by_code

router = APIRouter(prefix="/weeks", tags=["security"])


@router.post(
    "/{week_id}/security",
    response_model=SecurityPaymentResponse,
    status_code=201,
)
def add_security_record(
    week_id: int,
    data: SecurityPaymentCreate,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):
    if not week_exists(connection, week_id):
        raise HTTPException(status_code=404, detail=f"Week {week_id} not found.")

    emp_code = data.employee_code or (str(data.employee_id) if data.employee_id is not None else "")
    if not emp_code:
        raise HTTPException(status_code=400, detail="Employee code is required.")
    emp_id = get_employee_id_by_code(connection, emp_code)
    if emp_id is None:
        raise HTTPException(status_code=404, detail=f"Employee code '{emp_code}' not found.")

    try:
        rec_id = insert_security_payment(
            connection=connection,
            week_id=week_id,
            employee_id=emp_id,
            days=data.days,
            amount=data.amount,
            remarks=data.remarks or "",
        )
        connection.commit()
    except Exception as exc:
        connection.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    return SecurityPaymentResponse(
        id=rec_id,
        week_id=week_id,
        employee_id=emp_id,
        days=data.days,
        amount=data.amount,
        remarks=data.remarks or "",
    )

