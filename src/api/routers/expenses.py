from typing import Annotated
import sqlite3
from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_db
from api.schemas.expenses import ExpenseCreate, ExpenseResponse
from expense_manager import insert_expense, expense_exists, week_exists

router = APIRouter(prefix="/weeks", tags=["expenses"])


@router.post(
    "/{week_id}/expenses",
    response_model=ExpenseResponse,
    status_code=201,
)
def add_expense_record(
    week_id: int,
    data: ExpenseCreate,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):
    if not week_exists(connection, week_id):
        raise HTTPException(status_code=404, detail=f"Week {week_id} not found.")

    category = data.category.strip().upper()
    existing_id = expense_exists(connection, week_id, category)
    if existing_id is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Expense category '{category}' already exists for Week {week_id}.",
        )

    try:
        cursor = connection.cursor()
        insert_expense(
            connection=connection,
            week_id=week_id,
            category=category,
            amount=data.amount,
            notes=data.notes or "",
        )
        rec_id = cursor.lastrowid
        connection.commit()
    except Exception as exc:
        connection.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    return ExpenseResponse(
        id=rec_id or 0,
        week_id=week_id,
        category=category,
        amount=data.amount,
        notes=data.notes or "",
    )
