from pydantic import BaseModel


class ImportSummary(BaseModel):
    total_sheets: int
    total_rows: int
    date_from: str
    date_to: str


class MissingRecords(BaseModel):
    employees: list[str]
    styles: list[str]
    operations: list[str]


class ImportPreviewResponse(BaseModel):
    workbook_name: str
    summary: ImportSummary
    missing: MissingRecords
    ready_to_import: bool
    message: str


class ImportResponse(BaseModel):
    week_id: int
    message: str