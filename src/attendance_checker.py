import sqlite3


def check_attendance_vs_shift(
    connection: sqlite3.Connection,
    week_id: int,
):
    """
    Compares biometric attendance with shift records.

    Attendance is ONLY used for verification.
    It does NOT change salary calculations.

    Returns employees where the recorded shift
    and attendance-based presence do not match.
    """

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            e.employee_code,
            e.name,
            sr.work_date,
            sr.shifts,
            a.status,
            a.source

        FROM shift_records sr

        JOIN employees e
            ON sr.employee_id = e.id

        LEFT JOIN attendance_records a
            ON a.employee_id = sr.employee_id
            AND a.work_date = sr.work_date

        WHERE sr.week_id = ?

        ORDER BY
            sr.work_date,
            e.name
        """,
        (week_id,),
    )

    rows = cursor.fetchall()

    mismatches = []

    for row in rows:

        (
            employee_code,
            employee_name,
            work_date,
            recorded_shifts,
            attendance_status,
            attendance_source,
        ) = row

        # No attendance record
        if attendance_status is None:

            mismatches.append({
                "employee_code": employee_code,
                "employee_name": employee_name,
                "work_date": work_date,
                "recorded_shifts": recorded_shifts,
                "attendance_status": "NO RECORD",
                "attendance_source": None,
                "reason": "No attendance record found",
            })

        # Employee marked absent but shift was recorded
        elif attendance_status.upper() == "ABSENT" and recorded_shifts > 0:

            mismatches.append({
                "employee_code": employee_code,
                "employee_name": employee_name,
                "work_date": work_date,
                "recorded_shifts": recorded_shifts,
                "attendance_status": attendance_status,
                "attendance_source": attendance_source,
                "reason": "Shift recorded but attendance marked absent",
            })

    return mismatches