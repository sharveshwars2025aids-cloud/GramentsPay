def get_piece_workers(connection, week_id):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT 
            e.id,
            e.employee_code,
            e.name,
            e.pay_type,
            SUM(pr.total_amount) AS production_salary
        FROM production_records pr
        JOIN employees e
            ON pr.employee_id = e.id
        WHERE 
            pr.week_id = ?
            AND e.pay_type = 'PIECE'
        GROUP BY 
            e.id,
            e.employee_code,
            e.name,
            e.pay_type
        ORDER BY
            e.name
        """,
        (week_id,)
    )

    result = cursor.fetchall()
    return result


def get_shift_contractor_salary(connection, week_id):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            c.id,
            c.name,
            SUM(sr.shifts) AS total_shifts,
            c.commission_amount,
            SUM(sr.shifts * c.commission_amount) AS commission
        FROM shift_records sr
        JOIN employees e
            ON sr.employee_id = e.id
        JOIN contractors c
            ON e.contractor_id = c.id
        WHERE
            sr.week_id = ?
            AND e.contractor_id IS NOT NULL
        GROUP BY
            c.id,
            c.name,
            c.commission_amount
        ORDER BY
            c.name
        """,
        (week_id,)
    )

    return cursor.fetchall()


def get_shift_workers(connection, week_id):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            e.id,
            e.employee_code,
            e.name,
            e.pay_type,
            SUM(sr.shifts) AS total_shifts,
            SUM(sr.daily_salary) AS shift_salary
        FROM shift_records sr
        JOIN employees e
            ON sr.employee_id = e.id
        WHERE
            sr.week_id = ?
            AND e.pay_type = 'SHIFT'
        GROUP BY
            e.id,
            e.employee_code,
            e.name,
            e.pay_type
        ORDER BY
            e.name
        """,
        (week_id,)
    )

    result = cursor.fetchall()
    return result


def get_employee_bonuses(connection, week_id):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            b.employee_id,
            e.employee_code,
            e.name,
            e.pay_type,
            SUM(b.amount) AS total_bonus
        FROM bonuses b
        JOIN employees e
            ON b.employee_id = e.id
        WHERE b.week_id = ?
        GROUP BY
            b.employee_id,
            e.employee_code,
            e.name,
            e.pay_type
        """,
        (week_id,)
    )

    result = cursor.fetchall()
    return result


def get_employee_deductions(connection, week_id):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            d.employee_id,
            e.employee_code,
            e.name,
            e.pay_type,
            SUM(d.amount) AS total_deduction
        FROM deductions d
        JOIN employees e
            ON d.employee_id = e.id
        WHERE d.week_id = ?
        GROUP BY
            d.employee_id,
            e.employee_code,
            e.name,
            e.pay_type
        """,
        (week_id,)
    )

    result = cursor.fetchall()
    return result


def get_factory_expenses(connection, week_id):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            category,
            amount,
            notes
        FROM expenses
        WHERE week_id = ?
        ORDER BY category
        """,
        (week_id,)
    )

    result = cursor.fetchall()
    return result


def get_contractor_commissions(connection):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            c.id,
            c.name,
            c.commission_amount
        FROM contractors c
        WHERE c.status = 'active'
        ORDER BY c.name
        """
    )

    result = cursor.fetchall()
    return result