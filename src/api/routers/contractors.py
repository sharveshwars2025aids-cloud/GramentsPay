from typing import Annotated
import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_db

from api.schemas.contractors import (
    ContractorCreate,
    ContractorResponse,
    ContractorUpdate,
)

from api.services.contractor_service import (
    create_contractor,
    delete_contractor,
    get_all_contractors,
    get_contractor,
    update_contractor,
)

router = APIRouter(
    prefix="/contractors",
    tags=["Contractors"],
)


@router.get(
    "",
    response_model=list[ContractorResponse],
)
def list_contractors(
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):

    return get_all_contractors(connection)


@router.get(
    "/{contractor_id}",
    response_model=ContractorResponse,
)
def contractor_details(
    contractor_id: int,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):

    contractor = get_contractor(
        connection,
        contractor_id,
    )

    if contractor is None:

        raise HTTPException(
            status_code=404,
            detail="Contractor not found.",
        )

    return contractor


@router.post(
    "",
    response_model=ContractorResponse,
    status_code=201,
)
def add_contractor(
    contractor: ContractorCreate,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):

    return create_contractor(
        connection,
        contractor,
    )


@router.put(
    "/{contractor_id}",
    response_model=ContractorResponse,
)
def edit_contractor(
    contractor_id: int,
    contractor: ContractorUpdate,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):

    existing = get_contractor(
        connection,
        contractor_id,
    )

    if existing is None:

        raise HTTPException(
            status_code=404,
            detail="Contractor not found.",
        )

    return update_contractor(
        connection,
        contractor_id,
        contractor,
    )


@router.delete(
    "/{contractor_id}",
)
def remove_contractor(
    contractor_id: int,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):

    existing = get_contractor(
        connection,
        contractor_id,
    )

    if existing is None:

        raise HTTPException(
            status_code=404,
            detail="Contractor not found.",
        )

    delete_contractor(
        connection,
        contractor_id,
    )

    return {
        "message": "Contractor marked as inactive."
    }