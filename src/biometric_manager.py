import os
import io
import pandas as pd
from datetime import datetime
from database import connect_database

DEFAULT_TOLERANCE = 0.5


def get_employee_id_by_name_or_code(connection, identifier):
    """
    Finds employee_id matching employee_code or employee name.
    """
    cursor = connection.cursor()
    clean_identifier = str(identifier).strip().upper()
    clean_no_spaces = clean_identifier.replace(" ", "")

    cursor.execute(
        """
        SELECT id FROM employees
        WHERE UPPER(employee_code) = ?
           OR REPLACE(UPPER(name), ' ', '') = ?
        """,
        (clean_identifier, clean_no_spaces),
    )
    row = cursor.fetchone()
    if row:
        return row[0]

    # Partial match fallback
    cursor.execute(
        """
        SELECT id FROM employees
        WHERE REPLACE(UPPER(name), ' ', '') LIKE ?
        """,
        (f"%{clean_no_spaces}%",),
    )
    row = cursor.fetchone()
    if row:
        return row[0]

    # Numeric fallback: some biometric devices are configured with the
    # employee's raw database id rather than the human-readable
    # employee_code. Only tried if the identifier is purely numeric, so
    # it can never accidentally match a numeric-looking employee_code.
    if clean_no_spaces.isdigit():
        cursor.execute(
            "SELECT id FROM employees WHERE id = ?",
            (int(clean_no_spaces),),
        )
        row = cursor.fetchone()
        if row:
            return row[0]

    raise LookupError(f"Employee '{identifier}' not found in database.")


def parse_and_import_biometric_file(
    connection,
    week_id: int,
    file_content_or_path,
    filename: str,
):
    """
    Parses biometric export (CSV/Excel) and inserts into biometric_attendance table.
    """
    if isinstance(file_content_or_path, (bytes, bytearray)):
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_content_or_path))
        else:
            df = pd.read_excel(io.BytesIO(file_content_or_path))
    elif isinstance(file_content_or_path, pd.DataFrame):
        df = file_content_or_path
    else:
        if str(file_content_or_path).endswith(".csv"):
            df = pd.read_csv(file_content_or_path)
        else:
            df = pd.read_excel(file_content_or_path)

    # Normalize column headers
    df.columns = [str(col).strip().upper().replace(" ", "_") for col in df.columns]

    # Determine column mapping
    emp_col = None
    for candidate in ["EMPLOYEE_CODE", "EMP_CODE", "EMPLOYEE_ID", "EMP_ID", "EMPLOYEE_NAME", "NAME", "EMPLOYEE", "WORKER"]:
        if candidate in df.columns:
            emp_col = candidate
            break

    if not emp_col:
        raise ValueError("Could not find Employee ID or Name column in biometric file.")

    date_col = None
    for candidate in ["WORK_DATE", "DATE", "TAP_DATE", "LOG_DATE"]:
        if candidate in df.columns:
            date_col = candidate
            break

    tap_in_col = None
    for candidate in ["TAP_IN_TIME", "TAP_IN", "IN_TIME", "TIME_IN", "CHECK_IN"]:
        if candidate in df.columns:
            tap_in_col = candidate
            break

    tap_out_col = None
    for candidate in ["TAP_OUT_TIME", "TAP_OUT", "OUT_TIME", "TIME_OUT", "CHECK_OUT"]:
        if candidate in df.columns:
            tap_out_col = candidate
            break

    shift_val_col = None
    for candidate in ["COMPUTED_SHIFT_VALUE", "SHIFT_VALUE", "SHIFTS", "HOURS_WORKED", "HOURS"]:
        if candidate in df.columns:
            shift_val_col = candidate
            break

    device_col = None
    for candidate in ["DEVICE_ID", "DEVICE", "TERMINAL"]:
        if candidate in df.columns:
            device_col = candidate
            break

    cursor = connection.cursor()
    inserted_count = 0

    for _, row in df.iterrows():
        raw_emp = row[emp_col]
        if pd.isna(raw_emp) or str(raw_emp).strip() == "":
            continue

        try:
            employee_id = get_employee_id_by_name_or_code(connection, raw_emp)
        except LookupError:
            # Skip or handle unknown employee
            continue

        # Parse date
        if date_col and not pd.isna(row[date_col]):
            work_date = pd.to_datetime(row[date_col]).date()
        elif tap_in_col and not pd.isna(row[tap_in_col]):
            work_date = pd.to_datetime(row[tap_in_col]).date()
        else:
            continue

        tap_in_time = None
        if tap_in_col and not pd.isna(row[tap_in_col]):
            tap_in_time = str(pd.to_datetime(row[tap_in_col]))

        tap_out_time = None
        if tap_out_col and not pd.isna(row[tap_out_col]):
            tap_out_time = str(pd.to_datetime(row[tap_out_col]))

        computed_shift = 0.0
        if shift_val_col and not pd.isna(row[shift_val_col]):
            val = float(row[shift_val_col])
            if "HOUR" in shift_val_col:
                computed_shift = round((val / 8.0) * 2) / 2.0
            else:
                computed_shift = val
        elif tap_in_time and tap_out_time:
            t_in = pd.to_datetime(tap_in_time)
            t_out = pd.to_datetime(tap_out_time)
            duration_hours = (t_out - t_in).total_seconds() / 3600.0
            if duration_hours > 0:
                computed_shift = round((duration_hours / 8.0) * 2) / 2.0

        device_id = str(row[device_col]) if device_col and not pd.isna(row[device_col]) else "BIOMETRIC_DEVICE_1"

        cursor.execute(
            """
            INSERT INTO biometric_attendance (
                week_id,
                employee_id,
                work_date,
                tap_in_time,
                tap_out_time,
                computed_shift_value,
                device_id,
                source_file
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                week_id,
                employee_id,
                str(work_date),
                tap_in_time,
                tap_out_time,
                computed_shift,
                device_id,
                filename,
            ),
        )
        inserted_count += 1

    return inserted_count


def get_attendance_mismatches(connection, week_id: int, tolerance: float = DEFAULT_TOLERANCE):
    """
    Compares entered shift_records against biometric_attendance.
    Excludes rows already present in attendance_overrides.
    """
    cursor = connection.cursor()

    # Query shift_records total shifts per (employee_id, work_date)
    cursor.execute(
        """
        SELECT 
            sr.employee_id,
            e.name AS employee_name,
            sr.work_date,
            SUM(sr.shifts) AS entered_shifts
        FROM shift_records sr
        JOIN employees e ON sr.employee_id = e.id
        WHERE sr.week_id = ?
        GROUP BY sr.employee_id, sr.work_date
        """,
        (week_id,),
    )
    shift_rows = cursor.fetchall()

    mismatches = []

    for emp_id, emp_name, work_date, entered_shifts in shift_rows:
        # Check if already overridden
        cursor.execute(
            """
            SELECT id FROM attendance_overrides
            WHERE week_id = ? AND employee_id = ? AND work_date = ?
            """,
            (week_id, emp_id, work_date),
        )
        if cursor.fetchone():
            continue

        # Get biometric shift sum for this employee and work_date
        cursor.execute(
            """
            SELECT SUM(computed_shift_value)
            FROM biometric_attendance
            WHERE week_id = ? AND employee_id = ? AND work_date = ?
            """,
            (week_id, emp_id, work_date),
        )
        bio_row = cursor.fetchone()
        biometric_shifts = bio_row[0] if (bio_row and bio_row[0] is not None) else 0.0

        diff = abs((entered_shifts or 0.0) - biometric_shifts)
        if diff >= tolerance:
            message = (
                f"{emp_name} isn't tapping properly on {work_date}. "
                f"Entered: {entered_shifts:.1f} shift. Biometric: {biometric_shifts:.1f} shift."
            )
            mismatches.append(
                {
                    "week_id": week_id,
                    "employee_id": emp_id,
                    "employee_name": emp_name,
                    "work_date": str(work_date),
                    "entered_shift_value": float(entered_shifts or 0.0),
                    "biometric_shift_value": float(biometric_shifts),
                    "diff": float(diff),
                    "headline": f"{emp_name} isn't tapping properly on {work_date}",
                    "message": message,
                }
            )

    return mismatches


def override_mismatch(
    connection,
    week_id: int,
    employee_id: int,
    work_date: str,
    biometric_shift_value: float,
    entered_shift_value: float,
    overridden_by: str,
    reason: str = "Accountant manual override",
):
    """
    Inserts audit row into attendance_overrides for a single mismatch.
    """
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO attendance_overrides (
            week_id,
            employee_id,
            work_date,
            biometric_shift_value,
            entered_shift_value,
            overridden_by,
            reason
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            week_id,
            employee_id,
            work_date,
            biometric_shift_value,
            entered_shift_value,
            overridden_by,
            reason,
        ),
    )
    return cursor.lastrowid


def override_all_mismatches(
    connection,
    week_id: int,
    overridden_by: str,
    reason: str = "Accountant bulk override",
    tolerance: float = DEFAULT_TOLERANCE,
):
    """
    Bulk overrides all remaining mismatches for a week.
    """
    mismatches = get_attendance_mismatches(connection, week_id, tolerance=tolerance)
    overridden_ids = []
    for item in mismatches:
        override_id = override_mismatch(
            connection=connection,
            week_id=week_id,
            employee_id=item["employee_id"],
            work_date=item["work_date"],
            biometric_shift_value=item["biometric_shift_value"],
            entered_shift_value=item["entered_shift_value"],
            overridden_by=overridden_by,
            reason=reason,
        )
        overridden_ids.append(override_id)
    return len(overridden_ids)