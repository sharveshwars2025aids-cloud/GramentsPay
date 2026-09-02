from typing import Annotated
import sqlite3
from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_db
from api.schemas.shifts import ShiftRecordCreate, ShiftRecordResponse
from database import (
    get_employee_id_by_code,
    get_style_id_by_number,
    get_operation_id_by_name,
)
from shift_manager import insert_shift_record, week_exists

router = APIRouter(prefix="/weeks", tags=["shifts"])


@router.post(
    "/{week_id}/shift",
    response_model=ShiftRecordResponse,
    status_code=201,
)
def add_shift_record(
    week_id: int,
    data: ShiftRecordCreate,
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

    op_input = data.operation_name or (str(data.operation_id) if data.operation_id is not None else "")
    op_id = None
    if op_input:
        if isinstance(data.operation_id, int) and data.operation_name is None:
            cursor = connection.cursor()
            cursor.execute("SELECT id FROM operations WHERE id = ?", (data.operation_id,))
            row_op = cursor.fetchone()
            if row_op:
                op_id = row_op[0]
        if op_id is None:
            op_id = get_operation_id_by_name(connection, op_input)
        if op_id is None:
            raise HTTPException(status_code=404, detail=f"Operation '{op_input}' not found.")

    style_num = data.style_no or (str(data.style_id) if data.style_id is not None else "")
    style_id = None
    if style_num:
        style_id = get_style_id_by_number(connection, style_num)
        if style_id is None:
            raise HTTPException(status_code=404, detail=f"Style '{style_num}' not found.")

    daily_salary = float(data.shifts) * float(data.shift_rate)

    try:
        rec_id = insert_shift_record(
            connection=connection,
            week_id=week_id,
            work_date=data.work_date,
            employee_id=emp_id,
            operation_id=op_id,
            item=data.item or "",
            shifts=data.shifts,
            rate_per_shift=data.shift_rate,
            style_id=style_id,
            type=data.type or "",
            color=data.color or "",
        )
        connection.commit()
    except Exception as exc:
        connection.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    return ShiftRecordResponse(
        id=rec_id,
        week_id=week_id,
        work_date=data.work_date,
        employee_id=emp_id,
        operation_id=op_id,
        style_id=style_id,
        type=data.type or "",
        color=data.color or "",
        item=data.item or "",
        shifts=data.shifts,
        shift_rate=data.shift_rate,
        daily_salary=daily_salary,
    )

