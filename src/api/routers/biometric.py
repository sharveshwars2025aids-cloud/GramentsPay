from typing import Annotated, List
import sqlite3
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from api.dependencies import get_db
from api.schemas.biometric import (
    BiometricImportResponse,
    BiometricMismatchItem,
    OverrideRequest,
    BulkOverrideRequest,
    OverrideResponse,
)
from biometric_manager import (
    parse_and_import_biometric_file,
    get_attendance_mismatches,
    override_mismatch,
    override_all_mismatches,
)
from shift_manager import week_exists

router = APIRouter(prefix="/weeks", tags=["biometric"])


@router.post(
    "/{week_id}/biometric-import",
    response_model=BiometricImportResponse,
    status_code=201,
)
async def import_biometric_data(
    week_id: int,
    file: UploadFile = File(...),
    connection: Annotated[sqlite3.Connection, Depends(get_db)] = None,
):
    if not week_exists(connection, week_id):
        raise HTTPException(status_code=404, detail=f"Week {week_id} not found.")

    content = await file.read()
    filename = file.filename or "uploaded_biometric.csv"

    try:
        count = parse_and_import_biometric_file(
            connection=connection,
            week_id=week_id,
            file_content_or_path=content,
            filename=filename,
        )
        connection.commit()
    except Exception as exc:
        connection.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to import biometric file: {str(exc)}")

    return BiometricImportResponse(
        week_id=week_id,
        filename=filename,
        records_inserted=count,
    )


@router.get(
    "/{week_id}/attendance-mismatches",
    response_model=List[BiometricMismatchItem],
)
def list_attendance_mismatches(
    week_id: int,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):
    if not week_exists(connection, week_id):
        raise HTTPException(status_code=404, detail=f"Week {week_id} not found.")

    mismatches = get_attendance_mismatches(connection, week_id)
    return [BiometricMismatchItem(**item) for item in mismatches]


@router.post(
    "/{week_id}/attendance-mismatches/override",
    response_model=OverrideResponse,
)

@router.post(
    "/{week_id}/attendance-mismatches/{id}/override",
    response_model=OverrideResponse,
)
def override_single_mismatch(
    week_id: int,
    data: OverrideRequest,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):
    if not week_exists(connection, week_id):
        raise HTTPException(status_code=404, detail=f"Week {week_id} not found.")

    emp_id = None
    if data.employee_code:
        from database import get_employee_id_by_code
        emp_id = get_employee_id_by_code(connection, data.employee_code)
        if emp_id is None:
            raise HTTPException(status_code=404, detail=f"Employee code '{data.employee_code}' not found.")
    elif data.employee_id is not None:
        emp_id = data.employee_id
    else:
        raise HTTPException(status_code=400, detail="Employee code or ID is required.")

    try:
        override_id = override_mismatch(
            connection=connection,
            week_id=week_id,
            employee_id=emp_id,
            work_date=data.work_date,
            biometric_shift_value=data.biometric_shift_value,
            entered_shift_value=data.entered_shift_value,
            overridden_by=data.overridden_by or "Accountant",
            reason=data.reason or "Manual verification override",
        )
        connection.commit()
    except Exception as exc:
        connection.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    return OverrideResponse(
        status="success",
        message=f"Override audit record #{override_id} created successfully for employee {emp_id} on {data.work_date}.",
    )



@router.post(
    "/{week_id}/attendance-mismatches/override-all",
    response_model=OverrideResponse,
)
def override_all_remaining(
    week_id: int,
    data: BulkOverrideRequest,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):
    if not week_exists(connection, week_id):
        raise HTTPException(status_code=404, detail=f"Week {week_id} not found.")

    try:
        count = override_all_mismatches(
            connection=connection,
            week_id=week_id,
            overridden_by=data.overridden_by or "Accountant",
            reason=data.reason or "Bulk verification override",
        )
        connection.commit()
    except Exception as exc:
        connection.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    return OverrideResponse(
        status="success",
        message=f"Successfully recorded audit overrides for {count} remaining mismatch(es).",
    )
