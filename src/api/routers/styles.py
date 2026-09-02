from typing import Annotated
import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_db

from api.schemas.styles import (
    StyleCreate,
    StyleResponse,
    StyleUpdate,
)

from api.services.styles_service import (
    create_style,
    delete_style,
    get_all_styles,
    get_style,
    update_style,
)

router = APIRouter(
    prefix="/styles",
    tags=["Styles"],
)


@router.get(
    "",
    response_model=list[StyleResponse],
)
def list_styles(
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):

    return get_all_styles(connection)


@router.get(
    "/{style_id}",
    response_model=StyleResponse,
)
def style_details(
    style_id: str,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):

    style = get_style(
        connection,
        style_id,
    )

    if style is None:

        raise HTTPException(
            status_code=404,
            detail="Style not found.",
        )

    return style


@router.post(
    "",
    response_model=StyleResponse,
    status_code=201,
)
def add_style(
    style: StyleCreate,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):

    return create_style(
        connection,
        style,
    )


@router.put(
    "/{style_id}",
    response_model=StyleResponse,
)
def edit_style(
    style_id: str,
    style: StyleUpdate,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):

    existing = get_style(
        connection,
        style_id,
    )

    if existing is None:

        raise HTTPException(
            status_code=404,
            detail="Style not found.",
        )

    return update_style(
        connection,
        style_id,
        style,
    )


@router.delete(
    "/{style_id}",
)
def remove_style(
    style_id: str,
    connection: Annotated[sqlite3.Connection, Depends(get_db)],
):

    existing = get_style(
        connection,
        style_id,
    )

    if existing is None:

        raise HTTPException(
            status_code=404,
            detail="Style not found.",
        )

    delete_style(
        connection,
        style_id,
    )

    return {
        "message": "Style marked as inactive."
    }