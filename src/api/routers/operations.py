from typing import Annotated
import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_db

from api.schemas.operations import (
    OperationCreate,
    OperationResponse,
    OperationUpdate,
)

from api.services.operation_service import (
    create_operation,
    delete_operation,
    get_all_operations,
    get_operation,
    update_operation,
)

router = APIRouter(
    prefix="/operations",
    tags=["Operations"],
)


@router.get(
    "",
    response_model=list[OperationResponse],
)
def list_operations(
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):

    return get_all_operations(connection)


@router.get(
    "/{operation_id}",
    response_model=OperationResponse,
)
def operation_details(
    operation_id: int,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):

    operation = get_operation(
        connection,
        operation_id,
    )

    if operation is None:

        raise HTTPException(
            status_code=404,
            detail="Operation not found.",
        )

    return operation


@router.post(
    "",
    response_model=OperationResponse,
    status_code=201,
)
def add_operation(
    operation: OperationCreate,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):

    return create_operation(
        connection,
        operation,
    )


@router.put(
    "/{operation_id}",
    response_model=OperationResponse,
)
def edit_operation(
    operation_id: int,
    operation: OperationUpdate,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):

    existing = get_operation(
        connection,
        operation_id,
    )

    if existing is None:

        raise HTTPException(
            status_code=404,
            detail="Operation not found.",
        )

    return update_operation(
        connection,
        operation_id,
        operation,
    )


@router.delete(
    "/{operation_id}",
)
def remove_operation(
    operation_id: int,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):

    existing = get_operation(
        connection,
        operation_id,
    )

    if existing is None:

        raise HTTPException(
            status_code=404,
            detail="Operation not found.",
        )

    delete_operation(
        connection,
        operation_id,
    )

    return {
        "message": "Operation marked as inactive."
    }