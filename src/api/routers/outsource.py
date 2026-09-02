from typing import Annotated
import sqlite3
from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_db
from api.schemas.outsource import OutsourcePaymentCreate, OutsourcePaymentResponse
from outsource_manager import insert_outsource_payment, week_exists

router = APIRouter(prefix="/weeks", tags=["outsource"])


@router.post(
    "/{week_id}/outsource",
    response_model=OutsourcePaymentResponse,
    status_code=201,
)
def add_outsource_record(
    week_id: int,
    data: OutsourcePaymentCreate,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):
    if not week_exists(connection, week_id):
        raise HTTPException(status_code=404, detail=f"Week {week_id} not found.")

    # Calculate amount = qty * rate
    amount = float(data.qty) * float(data.rate)

    try:
        rec_id = insert_outsource_payment(
            connection=connection,
            week_id=week_id,
            style=data.style,
            item=data.item,
            qty=data.qty,
            rate=data.rate,
            amount=amount,
            centre_name=data.centre_name or "",
            remarks=data.remarks or "",
        )
        connection.commit()
    except Exception as exc:
        connection.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    return OutsourcePaymentResponse(
        id=rec_id,
        week_id=week_id,
        style=data.style,
        item=data.item,
        qty=data.qty,
        rate=data.rate,
        amount=amount,
        centre_name=data.centre_name or "",
        remarks=data.remarks or "",
    )
