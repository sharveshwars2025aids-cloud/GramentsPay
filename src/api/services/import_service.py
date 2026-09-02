from pathlib import Path
import pandas as pd
from parser_v3 import load_and_clean_all_sheets
from database import connect_database
from importer import (
    import_workbook,
    employee_exists,
    operation_exists,
    style_exists,
    ImportErrorDetails,
)
from fastapi import HTTPException


def import_uploaded_workbook(workbook_path: Path, original_filename: str | None = None):
    try:
        week_id = import_workbook(workbook_path)
        return {
            "week_id": week_id,
            "message": "Workbook imported successfully."
        }
    except (ImportErrorDetails, ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


def preview_workbook(workbook_path: Path, original_filename: str | None = None,):

    dataframe = load_and_clean_all_sheets(workbook_path)

    dataframe["DATE"] = pd.to_datetime(
        dataframe["DATE"],
        dayfirst=True,
        errors="coerce",
    )

    dataframe = dataframe.dropna(
        subset=["DATE"]
    )

    if dataframe.empty:
        raise ValueError(
            "No valid production records found in the workbook."
        )

    workbook_name = (
        original_filename
        if original_filename
        else workbook_path.name
    )

    total_sheets = dataframe["SOURCE_SHEET"].nunique()

    date_from = dataframe["DATE"].min().date()
    date_to = dataframe["DATE"].max().date()

    connection = connect_database()

    try:

        missing_employees = set()
        missing_styles = set()
        missing_operations = set()

        for _, row in dataframe.iterrows():

            employee = str(row["NAME"]).strip()

            if employee:
                if not employee_exists(
                    connection,
                    employee,
                ):
                    missing_employees.add(
                        employee.upper()
                    )

            style = str(row["STYLE"]).strip()

            if not style or style.upper() == "NAN":
                missing_styles.add("<EMPTY STYLE>")

            elif not style_exists(
                connection,
                style,
            ):
                missing_styles.add(
                    style.upper()
                )


            operation = str(row["DESCRIPTION"]).strip()

            if not operation or operation.upper() == "NAN":
                missing_operations.add("<EMPTY OPERATION>")

            elif not operation_exists(
                connection,
                operation,
            ):
                missing_operations.add(
                    operation.upper()
                )


        return {
    "workbook_name": workbook_name,

    "summary": {
        "total_sheets": total_sheets,
        "total_rows": len(dataframe),
        "date_from": str(date_from),
        "date_to": str(date_to),
    },

    "missing": {
        "employees": sorted(missing_employees),
        "styles": sorted(missing_styles),
        "operations": sorted(missing_operations),
    },

    "ready_to_import": (
        len(missing_employees) == 0
        and len(missing_styles) == 0
        and len(missing_operations) == 0
    ),

    "message": "Workbook validation completed.",
}

    

    finally:

        connection.close()