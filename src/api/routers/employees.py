from typing import Annotated
import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_db

from api.schemas.employees import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
)

from api.services.employee_service import (
    create_employee,
    delete_employee,
    get_all_employees,
    get_employee,
    update_employee,
)

router = APIRouter(
    prefix="/employees",
    tags=["Employees"],
)


@router.get(
    "",
    response_model=list[EmployeeResponse],
)
def list_employees(
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):

    return get_all_employees(connection)


@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse,
)
def employee_details(
    employee_id: str,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):

    employee = get_employee(connection, employee_id)

    if employee is None:

        raise HTTPException(
            status_code=404,
            detail="Employee not found.",
        )

    return employee


@router.post(
    "",
    response_model=EmployeeResponse,
    status_code=201,
)
def add_employee(
    employee: EmployeeCreate,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):

    return create_employee(connection, employee)


@router.put(
    "/{employee_id}",
    response_model=EmployeeResponse,
)
def edit_employee(
    employee_id: str,
    employee: EmployeeUpdate,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):

    existing = get_employee(connection, employee_id)

    if existing is None:

        raise HTTPException(
            status_code=404,
            detail="Employee not found.",
        )

    return update_employee(
        connection,
        employee_id,
        employee,
    )


@router.delete(
    "/{employee_id}",
)
def remove_employee(
    employee_id: str,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):

    existing = get_employee(connection, employee_id)

    if existing is None:

        raise HTTPException(
            status_code=404,
            detail="Employee not found.",
        )

    delete_employee(
        connection,
        employee_id,
    )

    return {
        "message": "Employee marked as inactive."
    }