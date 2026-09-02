from pathlib import Path
import shutil
import tempfile

from fastapi import APIRouter, File, UploadFile

from api.schemas.imports import (
    ImportPreviewResponse,
    ImportResponse,
)

from api.services.import_service import (
    preview_workbook,
    import_uploaded_workbook,
)

router = APIRouter(
    prefix="/import",
    tags=["Import"],
)


@router.post(
    "/preview",
    response_model=ImportPreviewResponse,
)
def preview_import(
    file: UploadFile = File(...),
):

    suffix = Path(file.filename).suffix

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    ) as temp:

        shutil.copyfileobj(file.file, temp)

        temp_path = Path(temp.name)

    return preview_workbook(
        temp_path,
        original_filename=file.filename,
    )


@router.post(
    "",
    response_model=ImportResponse,
)
def import_workbook_api(
    file: UploadFile = File(...),
):

    suffix = Path(file.filename).suffix

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    ) as temp:

        shutil.copyfileobj(file.file, temp)

        temp_path = Path(temp.name)

    return import_uploaded_workbook(temp_path)