from database import connect_database


def get_employee_attendance(connection, employee_id, work_date):
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            a.id,
            e.employee_code,
            e.name,
            a.work_date,
            a.entry_time,
            a.exit_time,
            a.status,
            a.source,
            a.override_reason,
            a.overridden_by
        FROM attendance_records a
        JOIN employees e
            ON a.employee_id = e.id
        WHERE
            a.employee_id = ?
            AND a.work_date = ?
        """,
        (
            employee_id,
            work_date,
        ),
    )

    return cursor.fetchone()



def get_week_attendance(connection, week_id):
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            e.employee_code,
            e.name,
            a.work_date,
            a.entry_time,
            a.exit_time,
            a.status,
            a.source
        FROM attendance_records a
        JOIN employees e
            ON a.employee_id = e.id
        JOIN weeks w
            ON a.work_date BETWEEN w.week_start AND w.week_end
        WHERE w.id = ?
        ORDER BY
            a.work_date,
            e.name
        """,
        (week_id,),
    )

    return cursor.fetchall()
