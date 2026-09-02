from typing import Annotated
import sqlite3
from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_db
from api.schemas.production import ProductionRecordCreate, ProductionRecordResponse
from database import (
    get_employee_id_by_code,
    get_style_id_by_number,
    get_operation_id_by_name,
)
from importer import insert_production_record, insert_production_sizes

router = APIRouter(prefix="/weeks", tags=["production"])


@router.post(
    "/{week_id}/production",
    response_model=ProductionRecordResponse,
    status_code=201,
)
def add_production_record(
    week_id: int,
    data: ProductionRecordCreate,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM weeks WHERE id = ?", (week_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail=f"Week {week_id} not found.")

    if data.sizes:
        size_sum = sum(float(v) for v in data.sizes.values())
        if abs(size_sum - float(data.total_qty)) > 0.01:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"total_qty ({data.total_qty}) does not match the sum of "
                    f"the size quantities ({size_sum})."
                ),
            )

    emp_code = data.employee_code or (str(data.employee_id) if data.employee_id is not None else "")
    if not emp_code:
        raise HTTPException(status_code=400, detail="Employee code is required.")
    emp_id = get_employee_id_by_code(connection, emp_code)
    if emp_id is None:
        raise HTTPException(status_code=404, detail=f"Employee code '{emp_code}' not found.")

    style_num = data.style_no or (str(data.style_id) if data.style_id is not None else "")
    if not style_num:
        raise HTTPException(status_code=400, detail="Style number is required.")
    style_id = get_style_id_by_number(connection, style_num)
    if style_id is None:
        raise HTTPException(status_code=404, detail=f"Style '{style_num}' not found.")

    op_input = data.operation_name or (str(data.operation_id) if data.operation_id is not None else "")
    if not op_input:
        raise HTTPException(status_code=400, detail="Operation name is required.")
    
    op_id = None
    if isinstance(data.operation_id, int) and data.operation_name is None:
        cursor.execute("SELECT id FROM operations WHERE id = ?", (data.operation_id,))
        row_op = cursor.fetchone()
        if row_op:
            op_id = row_op[0]
    if op_id is None:
        op_id = get_operation_id_by_name(connection, op_input)
    if op_id is None:
        raise HTTPException(status_code=404, detail=f"Operation '{op_input}' not found.")

    total_amount = float(data.total_qty) * float(data.rate)

    row_data = {
        "DATE": data.work_date,
        "TYPE": data.type or "",
        "COLOR": data.color or "",
        "QTY": data.total_qty,
        "RATE": data.rate,
        "AMT": total_amount,
        "SOURCE_SHEET": "Manual Entry",
        "WORKBOOK_NAME": "Web Portal",
        "SOURCE_ROW": 0,
    }

    try:
        rec_id = insert_production_record(
            connection=connection,
            week_id=week_id,
            employee_id=emp_id,
            style_id=style_id,
            operation_id=op_id,
            row=row_data,
        )

        if data.sizes:
            size_row = {f"SIZE_{name}": qty for name, qty in data.sizes.items()}
            insert_production_sizes(
                connection=connection,
                production_record_id=rec_id,
                row=size_row,
            )

        connection.commit()
    except Exception as exc:
        connection.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    return ProductionRecordResponse(
        id=rec_id,
        week_id=week_id,
        work_date=data.work_date,
        employee_id=emp_id,
        style_id=style_id,
        operation_id=op_id,
        type=data.type or "",
        color=data.color or "",
        total_qty=data.total_qty,
        rate=data.rate,
        total_amount=total_amount,
    )

