import sqlite3
import warnings


def check_attendance_vs_shift(
    connection: sqlite3.Connection,
    week_id: int,
):
    """
    Compares biometric attendance with shift records.
    Updated to use active biometric_attendance and attendance_overrides tables.

    Attendance is ONLY used for verification.
    It does NOT change salary calculations.

    Returns employees where the recorded shift
    and attendance-based presence do not match.
    """
    cursor = connection.cursor()

    # Query shift records joined with employees
    cursor.execute(
        """
        SELECT
            e.id,
            e.employee_code,
            e.name,
            sr.work_date,
            SUM(sr.shifts) AS total_shifts
        FROM shift_records sr
        JOIN employees e
            ON sr.employee_id = e.id
        WHERE sr.week_id = ?
        GROUP BY e.id, e.employee_code, e.name, sr.work_date
        ORDER BY
            sr.work_date,
            e.name
        """,
        (week_id,),
    )
    rows = cursor.fetchall()

    mismatches = []

    for row in rows:
        emp_id, employee_code, employee_name, work_date, recorded_shifts = row

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

        # Check biometric attendance record
        cursor.execute(
            """
            SELECT SUM(computed_shift_value)
            FROM biometric_attendance
            WHERE week_id = ? AND employee_id = ? AND work_date = ?
            """,
            (week_id, emp_id, work_date),
        )
        bio_row = cursor.fetchone()
        biometric_shift = bio_row[0] if (bio_row and bio_row[0] is not None) else None

        if biometric_shift is None:
            mismatches.append({
                "employee_code": employee_code,
                "employee_name": employee_name,
                "work_date": str(work_date),
                "recorded_shifts": float(recorded_shifts or 0.0),
                "attendance_status": "NO RECORD",
                "attendance_source": "BIOMETRIC",
                "reason": "No attendance record found",
            })
        elif biometric_shift == 0.0 and recorded_shifts > 0:
            mismatches.append({
                "employee_code": employee_code,
                "employee_name": employee_name,
                "work_date": str(work_date),
                "recorded_shifts": float(recorded_shifts or 0.0),
                "attendance_status": "ABSENT",
                "attendance_source": "BIOMETRIC",
                "reason": "Shift recorded but attendance marked absent",
            })

    return mismatches