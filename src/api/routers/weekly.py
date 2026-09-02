from typing import Annotated
import sqlite3
from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_db
from api.schemas.weekly import (
    ClosingReadinessResponse,
    WeekCreate,
    WeekResponse,
    WeekUpdate,
    WeeklyClosingResponse,
    WeeklySalaryResponse,
)
from api.services.weekly_service import (
    WeekNotFoundError,
    check_closing_readiness,
    create_or_get_week_service,
    generate_weekly_closing,
    get_all_weeks,
    get_week_by_id_service,
    get_weekly_salary,
    update_week_service,
)

router = APIRouter(prefix="/weeks", tags=["weekly"])


@router.get(
    "",
    response_model=list[WeekResponse],
    summary="List all weeks sorted by start date",
)
def list_weeks(
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):
    return get_all_weeks(connection)


@router.get(
    "/{week_id}",
    response_model=WeekResponse,
    summary="Get week details by database ID",
)
def get_week_details(
    week_id: int,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):
    try:
        return get_week_by_id_service(connection, week_id)
    except WeekNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Week with id {week_id} not found",
        )


@router.post(
    "",
    response_model=WeekResponse,
    status_code=201,
    summary="Create or retrieve week by date range (prevents duplicate creation)",
)
def create_or_get_week(
    data: WeekCreate,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):
    try:
        return create_or_get_week_service(connection, data.week_start, data.week_end)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put(
    "/{week_id}",
    response_model=WeekResponse,
    summary="Update week by database ID",
)
def update_week(
    week_id: int,
    data: WeekUpdate,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):
    try:
        return update_week_service(connection, week_id, data)
    except HTTPException:
        raise
    except WeekNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Week with id {week_id} not found",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))



@router.get(
    "/{week_id}/closing-readiness",
    response_model=ClosingReadinessResponse,
    summary=(
        "Check which manual-input categories (Outsource, Security, "
        "Expenses, Deductions, Bonuses) still have no data for this "
        "week. Call this the moment 'Generate Weekly Closing' is "
        "pressed -- for each category listed in pending_categories, "
        "show that category's popup before calling generate-closing."
    ),
)
def get_closing_readiness(week_id: int) -> ClosingReadinessResponse:
    try:
        result = check_closing_readiness(week_id)
    except WeekNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Week with id {week_id} not found",
        )

    return ClosingReadinessResponse(**result)


@router.get(
    "/{week_id}/salary",
    response_model=WeeklySalaryResponse,
    summary="Get the calculated salary breakdown for a given week",
)
def get_week_salary(week_id: int) -> WeeklySalaryResponse:
    try:
        result = get_weekly_salary(week_id)
    except WeekNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Week with id {week_id} not found or has no salary data.",
        )

    return WeeklySalaryResponse(**result)


@router.post(
    "/{week_id}/closing",
    response_model=WeeklyClosingResponse,
    summary="Generate the Weekly Closing workbook for a given week",
)
@router.post(
    "/{week_id}/generate-closing",
    response_model=WeeklyClosingResponse,
    summary="Generate the Weekly Closing workbook for a given week",
)
def create_week_closing(week_id: int) -> WeeklyClosingResponse:
    try:
        result = generate_weekly_closing(week_id)
    except WeekNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Week with id {week_id} not found or has no salary data.",
        )

    return WeeklyClosingResponse(**result)