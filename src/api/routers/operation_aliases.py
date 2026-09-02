from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
import sqlite3

from api.dependencies import get_db

from api.schemas.operation_aliases import (
    OperationAliasCreate,
    OperationAliasResponse,
    OperationAliasUpdate,
)

from api.services.operation_alias_service import (
    create_operation_alias,
    delete_operation_alias,
    get_all_operation_aliases,
    get_operation_alias,
    update_operation_alias,
)

from core.exceptions import (
    DuplicateRecordError,
    RecordNotFoundError,
)


router = APIRouter(
    prefix="/operation-aliases",
    tags=["Operation Aliases"],
)


@router.get(
    "",
    response_model=list[OperationAliasResponse],
)
def list_operation_aliases(
    connection: Annotated[
        sqlite3.Connection,
        Depends(get_db),
    ],
):

    return get_all_operation_aliases(connection)


@router.get(
    "/{alias_id}",
    response_model=OperationAliasResponse,
)
def operation_alias_details(
    alias_id: int,
    connection: Annotated[
        sqlite3.Connection,
        Depends(get_db),
    ],
):

    alias = get_operation_alias(
        connection,
        alias_id,
    )

    if alias is None:

        raise HTTPException(
            status_code=404,
            detail="Operation alias not found.",
        )

    return alias


@router.post(
    "",
    response_model=OperationAliasResponse,
    status_code=201,
)
def add_operation_alias(
    operation_alias: OperationAliasCreate,
    connection: Annotated[
        sqlite3.Connection,
        Depends(get_db),
    ],
):

    try:

        return create_operation_alias(
            connection,
            operation_alias,
        )

    except DuplicateRecordError as error:

        raise HTTPException(
            status_code=409,
            detail=str(error),
        )

    except RecordNotFoundError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


@router.put(
    "/{alias_id}",
    response_model=OperationAliasResponse,
)
def edit_operation_alias(
    alias_id: int,
    operation_alias: OperationAliasUpdate,
    connection: Annotated[
        sqlite3.Connection,
        Depends(get_db),
    ],
):

    existing = get_operation_alias(
        connection,
        alias_id,
    )

    if existing is None:

        raise HTTPException(
            status_code=404,
            detail="Operation alias not found.",
        )

    try:

        return update_operation_alias(
            connection,
            alias_id,
            operation_alias,
        )

    except DuplicateRecordError as error:

        raise HTTPException(
            status_code=409,
            detail=str(error),
        )

    except RecordNotFoundError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


@router.delete(
    "/{alias_id}",
)
def remove_operation_alias(
    alias_id: int,
    connection: Annotated[
        sqlite3.Connection,
        Depends(get_db),
    ],
):

    existing = get_operation_alias(
        connection,
        alias_id,
    )

    if existing is None:

        raise HTTPException(
            status_code=404,
            detail="Operation alias not found.",
        )

    delete_operation_alias(
        connection,
        alias_id,
    )

    return {
        "message": "Operation alias marked as inactive."
    }