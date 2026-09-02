import pandas as pd
from shift_manager import insert_shift_record
from validator import validate_dataframe
from parser_v3 import load_and_clean_all_sheets
from database import connect_database


class ImportErrorDetails(ValueError):
    def __init__(self, sheet: str, table_type: str, row: int, field: str, value: str, reason: str):
        self.sheet = sheet
        self.table_type = table_type
        self.row = row
        self.field = field
        self.value = value
        self.reason = reason
        msg = f"Sheet: {sheet}, Table: {table_type}, Row: {row}, Field: {field}, Value: '{value}' - Error: {reason}" if sheet else f"Field: {field}, Value: '{value}' - Error: {reason}"
        super().__init__(msg)



def get_or_create_week(connection, dataframe):
    cursor = connection.cursor()

    dataframe["DATE"] = pd.to_datetime(
        dataframe["DATE"],
        errors="raise",
    )

    week_start = dataframe["DATE"].min().date()
    week_end = dataframe["DATE"].max().date()

    cursor.execute(
        """
        SELECT id
        FROM weeks
        WHERE week_start = ?
          AND week_end = ?
        """,
        (
            week_start,
            week_end,
        ),
    )

    result = cursor.fetchone()

    if result is not None:
        return result[0]

    cursor.execute(
        """
        INSERT INTO weeks(
            week_start,
            week_end
        )
        VALUES(?, ?)
        """,
        (
            week_start,
            week_end,
        ),
    )

    return cursor.lastrowid


def get_employee_id(connection, name, sheet="", table_type="", row_num=0):
    raw = str(name).strip()
    if not raw or raw.upper() == "NAN":
        raise ImportErrorDetails(sheet, table_type, row_num, "EMP CODE / NAME", raw, "Employee code/name cannot be empty.")

    name_clean = raw.upper().replace(" ", "")
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM employees
        WHERE UPPER(employee_code) = ?
           OR REPLACE(UPPER(name), ' ', '') = ?
           OR id = ?
        """,
        (raw.upper(), name_clean, raw),
    )

    result = cursor.fetchone()

    if result is not None:
        return result[0]

    raise ImportErrorDetails(sheet, table_type, row_num, "EMP CODE", raw, f"Employee code '{raw}' not found.")


def get_style_id(connection, style_no, sheet="", table_type="", row_num=0):
    raw = str(style_no).strip()
    style_clean = raw.upper()

    if style_clean in ("", "NAN"):
        raise ImportErrorDetails(sheet, table_type, row_num, "STYLE", raw, "Style number cannot be empty.")

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM styles
        WHERE UPPER(style_no) = ?
           OR id = ?
        """,
        (style_clean, raw),
    )

    result = cursor.fetchone()

    if result is not None:
        return result[0]

    raise ImportErrorDetails(sheet, table_type, row_num, "STYLE", raw, f"Style '{raw}' not found.")


def get_operation_id(connection, operation, sheet="", table_type="", row_num=0):
    raw = str(operation).strip()
    op_clean = raw.upper()

    if op_clean in ("", "NAN"):
        raise ImportErrorDetails(sheet, table_type, row_num, "OPERATION", raw, "Operation name cannot be empty.")

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT o.id
        FROM operation_aliases oa
        JOIN operations o
            ON oa.operation_id = o.id
        WHERE UPPER(oa.alias) = ?
        """,
        (op_clean,),
    )

    result = cursor.fetchone()

    if result is not None:
        return result[0]

    cursor.execute(
        """
        SELECT id
        FROM operations
        WHERE UPPER(operation_name) = ?
           OR id = ?
        """,
        (op_clean, raw),
    )

    result = cursor.fetchone()

    if result is not None:
        return result[0]

    raise ImportErrorDetails(sheet, table_type, row_num, "OPERATION", raw, f"Operation '{raw}' not found.")


def validate_date_in_week(work_date, week_start, week_end, sheet="", table_type="", row_num=0):
    rec_date = pd.to_datetime(work_date).date()
    start_d = pd.to_datetime(week_start).date()
    end_d = pd.to_datetime(week_end).date()
    if rec_date < start_d or rec_date > end_d:
        raise ImportErrorDetails(
            sheet, table_type, row_num, "DATE", str(rec_date),
            f"Date {rec_date} is outside week range ({start_d} to {end_d})"
        )


def is_duplicate_production(connection, week_id, work_date, employee_id, style_id, operation_id, source_sheet, source_row, workbook_name):
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT id FROM production_records
        WHERE week_id = ? AND work_date = ? AND employee_id = ? AND style_id = ? AND operation_id = ? AND source_sheet = ? AND source_row = ? AND workbook_name = ?
        """,
        (week_id, str(work_date), employee_id, style_id, operation_id, str(source_sheet), int(source_row), str(workbook_name)),
    )
    return cursor.fetchone() is not None


def is_duplicate_shift(connection, week_id, work_date, employee_id, operation_id, source_sheet, source_row, workbook_name):
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT id FROM shift_records
        WHERE week_id = ? AND work_date = ? AND employee_id = ? AND operation_id = ? AND source_sheet = ? AND source_row = ? AND workbook_name = ?
        """,
        (week_id, str(work_date), employee_id, operation_id, str(source_sheet), int(source_row), str(workbook_name)),
    )
    return cursor.fetchone() is not None


def insert_production_record(
    connection,
    week_id,
    employee_id,
    style_id,
    operation_id,
    row,
):
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO production_records(
            week_id,
            work_date,
            employee_id,
            style_id,
            operation_id,
            type,
            color,
            total_qty,
            rate,
            total_amount,
            source_sheet,
            workbook_name,
            source_row
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            week_id,
            pd.to_datetime(row["DATE"]).date(),
            employee_id,
            style_id,
            operation_id,
            row.get("TYPE", ""),
            row.get("COLOR", ""),
            float(row["QTY"]),
            float(row["RATE"]),
            float(row["AMT"]),
            row["SOURCE_SHEET"],
            row["WORKBOOK_NAME"],
            int(row["SOURCE_ROW"]),
        ),
    )

    return cursor.lastrowid


def insert_production_sizes(
    connection,
    production_record_id,
    row,
):
    cursor = connection.cursor()

    for column_name, qty in row.items():

        if not column_name.startswith("SIZE_"):
            continue

        if pd.isna(qty):
            continue

        if str(qty).strip() == "":
            continue

        try:
            qty = float(qty)
        except (ValueError, TypeError):
            continue

        if qty <= 0:
            continue

        size_name = column_name.replace(
            "SIZE_",
            "",
            1,
        )

        cursor.execute(
            """
            INSERT INTO production_sizes(
                production_record_id,
                size_name,
                qty
            )
            VALUES(?, ?, ?)
            """,
            (
                production_record_id,
                size_name,
                qty,
            ),
        )


def employee_exists(connection, name):
    try:
        get_employee_id(connection, name)
        return True
    except (ValueError, LookupError):
        return False


def operation_exists(connection, operation):
    try:
        get_operation_id(connection, operation)
        return True
    except (ValueError, LookupError):
        return False


def style_exists(connection, style_no):
    try:
        get_style_id(connection, style_no)
        return True
    except (ValueError, LookupError):
        return False


def import_workbook(workbook_path):

    dataframe = load_and_clean_all_sheets(
        workbook_path
    )

    validate_dataframe(dataframe)

    required_importer_columns = [
        "SOURCE_SHEET",
        "WORKBOOK_NAME",
        "SOURCE_ROW",
    ]

    missing_columns = [
        column
        for column in required_importer_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            "Parser output is missing required source columns: "
            + ", ".join(missing_columns)
        )

    connection = connect_database()

    try:

        week_id = get_or_create_week(
            connection,
            dataframe,
        )

        # Get week dates for date validation
        cursor = connection.cursor()
        cursor.execute("SELECT week_start, week_end FROM weeks WHERE id = ?", (week_id,))
        week_row = cursor.fetchone()
        week_start, week_end = week_row[0], week_row[1]

        for _, row in dataframe.iterrows():

            sheet_name = str(row.get("SOURCE_SHEET", "")).strip()
            source_row_num = int(row.get("SOURCE_ROW", 0))

            # ------------------------------------------
            # Ignore rows without employee name
            # ------------------------------------------

            if (
                pd.isna(row["NAME"])
                or str(row["NAME"]).strip() == ""
            ):
                continue

            # ------------------------------------------
            # Identify table type
            # ------------------------------------------

            table_type = str(
                row.get("TABLE_TYPE", "")
            ).strip().upper()

            # Date validation
            validate_date_in_week(
                row["DATE"],
                week_start,
                week_end,
                sheet=sheet_name,
                table_type=table_type,
                row_num=source_row_num,
            )

            # ==========================================
            # PRODUCTION ROW
            # ==========================================

            if table_type == "PRODUCTION":

                style_value = row["STYLE"]

                if (
                    pd.isna(style_value)
                    or str(style_value).strip() == ""
                ):
                    continue

                employee_id = get_employee_id(
                    connection,
                    row["NAME"],
                    sheet=sheet_name,
                    table_type=table_type,
                    row_num=source_row_num,
                )

                style_id = get_style_id(
                    connection,
                    style_value,
                    sheet=sheet_name,
                    table_type=table_type,
                    row_num=source_row_num,
                )

                operation_id = get_operation_id(
                    connection,
                    row["DESCRIPTION"],
                    sheet=sheet_name,
                    table_type=table_type,
                    row_num=source_row_num,
                )

                work_date = pd.to_datetime(row["DATE"]).date()

                # Duplicate check
                if is_duplicate_production(
                    connection,
                    week_id,
                    work_date,
                    employee_id,
                    style_id,
                    operation_id,
                    sheet_name,
                    source_row_num,
                    row["WORKBOOK_NAME"],
                ):
                    continue

                production_record_id = insert_production_record(
                    connection,
                    week_id,
                    employee_id,
                    style_id,
                    operation_id,
                    row,
                )

                insert_production_sizes(
                    connection,
                    production_record_id,
                    row,
                )

            # ==========================================
            # SHIFT ROW
            # ==========================================

            elif table_type == "SHIFT":

                employee_id = get_employee_id(
                    connection,
                    row["NAME"],
                    sheet=sheet_name,
                    table_type=table_type,
                    row_num=source_row_num,
                )

                operation_id = get_operation_id(
                    connection,
                    row["DESCRIPTION"],
                    sheet=sheet_name,
                    table_type=table_type,
                    row_num=source_row_num,
                )

                shifts = pd.to_numeric(
                    row.get("SHIFT"),
                    errors="coerce",
                )

                shift_rate = pd.to_numeric(
                    row.get("SHIFT RATE"),
                    errors="coerce",
                )

                if pd.isna(shifts) or pd.isna(shift_rate):
                    continue

                work_date = pd.to_datetime(row["DATE"]).date()

                # Duplicate check
                if is_duplicate_shift(
                    connection,
                    week_id,
                    work_date,
                    employee_id,
                    operation_id,
                    sheet_name,
                    source_row_num,
                    row["WORKBOOK_NAME"],
                ):
                    continue

                insert_shift_record(
                    connection=connection,
                    week_id=week_id,
                    work_date=work_date,
                    employee_id=employee_id,
                    operation_id=operation_id,
                    item=row.get("TYPE", ""),
                    shifts=float(shifts),
                    rate_per_shift=float(shift_rate),
                )

            # ==========================================
            # UNKNOWN TABLE TYPE
            # ==========================================

            else:

                continue

        connection.commit()

        return week_id

    except Exception as error:

        connection.rollback()

        if isinstance(error, ImportErrorDetails):
            raise error

        raise RuntimeError(
            f"Workbook import failed: {error}"
        ) from error

    finally:

        connection.close()


if __name__ == "__main__":
    from parser_v3 import WORKBOOK_PATH

    import_workbook(WORKBOOK_PATH)