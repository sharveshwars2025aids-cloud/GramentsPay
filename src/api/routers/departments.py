from typing import Annotated
import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_db

from api.schemas.departments import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
)

from api.services.department_service import (
    create_department,
    delete_department,
    get_all_departments,
    get_department,
    update_department,
)

router = APIRouter(
    prefix="/departments",
    tags=["Departments"],
)


@router.get(
    "",
    response_model=list[DepartmentResponse],
)
def list_departments(
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):

    return get_all_departments(connection)


@router.get(
    "/{department_id}",
    response_model=DepartmentResponse,
)
def department_details(
    department_id: int,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):

    department = get_department(
        connection,
        department_id,
    )

    if department is None:

        raise HTTPException(
            status_code=404,
            detail="Department not found.",
        )

    return department


@router.post(
    "",
    response_model=DepartmentResponse,
    status_code=201,
)
def add_department(
    department: DepartmentCreate,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):

    return create_department(
        connection,
        department,
    )


@router.put(
    "/{department_id}",
    response_model=DepartmentResponse,
)
def edit_department(
    department_id: int,
    department: DepartmentUpdate,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):

    existing = get_department(
        connection,
        department_id,
    )

    if existing is None:

        raise HTTPException(
            status_code=404,
            detail="Department not found.",
        )

    return update_department(
        connection,
        department_id,
        department,
    )


@router.delete(
    "/{department_id}",
)
def remove_department(
    department_id: int,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):

    existing = get_department(
        connection,
        department_id,
    )

    if existing is None:

        raise HTTPException(
            status_code=404,
            detail="Department not found.",
        )

    delete_department(
        connection,
        department_id,
    )

    return {
        "message": "Department marked as inactive."
    }