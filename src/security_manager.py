from database import connect_database


def week_exists(connection, week_id):
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT id
        FROM weeks
        WHERE id = ?
        """,
        (week_id,)
    )
    return cursor.fetchone() is not None


def insert_security_payment(
    connection,
    week_id: int,
    employee_id: int,
    days: float,
    amount: float,
    remarks: str = "",
) -> int:
    """
    Inserts a security payment record.
    Reused by web API and CLI.
    """
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO security_payments(
            week_id,
            employee_id,
            days,
            amount,
            remarks
        )
        VALUES(?, ?, ?, ?, ?)
        """,
        (
            week_id,
            employee_id,
            days,
            amount,
            remarks,
        )
    )
    return cursor.lastrowid
