from typing import Annotated
import sqlite3
from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_db
from api.schemas.deductions import DeductionCreate, DeductionResponse
from deduction_manager import insert_deduction, deduction_exists, week_exists
from database import get_employee_id_by_code

router = APIRouter(prefix="/weeks", tags=["deductions"])


@router.post(
    "/{week_id}/deductions",
    response_model=DeductionResponse,
    status_code=201,
)
def add_deduction_record(
    week_id: int,
    data: DeductionCreate,
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

    ded_type = data.deduction_type.strip().upper()

    existing_id = deduction_exists(connection, week_id, emp_id, ded_type)
    if existing_id is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Deduction '{ded_type}' already exists for employee code '{emp_code}' in Week {week_id}.",
        )

    try:
        cursor = connection.cursor()
        insert_deduction(
            connection=connection,
            week_id=week_id,
            employee_id=emp_id,
            deduction_type=ded_type,
            amount=data.amount,
            notes=data.notes or "",
        )
        rec_id = cursor.lastrowid
        connection.commit()
    except Exception as exc:
        connection.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    return DeductionResponse(
        id=rec_id or 0,
        week_id=week_id,
        employee_id=emp_id,
        deduction_type=ded_type,
        amount=data.amount,
        notes=data.notes or "",
    )

