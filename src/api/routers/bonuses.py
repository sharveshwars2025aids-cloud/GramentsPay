from typing import Annotated
import sqlite3
from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_db
from api.schemas.bonuses import BonusCreate, BonusResponse
from bonus_manager import insert_bonus, bonus_exists, week_exists
from database import get_employee_id_by_code

router = APIRouter(prefix="/weeks", tags=["bonuses"])


@router.post(
    "/{week_id}/bonuses",
    response_model=BonusResponse,
    status_code=201,
)
def add_bonus_record(
    week_id: int,
    data: BonusCreate,
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

    b_type = data.bonus_type.strip().upper()

    existing_id = bonus_exists(connection, week_id, emp_id, b_type)
    if existing_id is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Bonus '{b_type}' already exists for employee code '{emp_code}' in Week {week_id}.",
        )

    try:
        cursor = connection.cursor()
        insert_bonus(
            connection=connection,
            week_id=week_id,
            employee_id=emp_id,
            bonus_type=b_type,
            amount=data.amount,
            notes=data.notes or "",
        )
        rec_id = cursor.lastrowid
        connection.commit()
    except Exception as exc:
        connection.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    return BonusResponse(
        id=rec_id or 0,
        week_id=week_id,
        employee_id=emp_id,
        bonus_type=b_type,
        amount=data.amount,
        notes=data.notes or "",
    )

