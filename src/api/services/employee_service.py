from database import connect_database


def get_all_employees(connection):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            employee_code,
            name,
            pay_type,
            department_id,
            default_operation_id,
            contractor_id,
            shift_rate,
            status,
            worker_type
        FROM employees
        ORDER BY name
        """
    )

    columns = [column[0] for column in cursor.description]

    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def get_employee(connection, employee_id):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            employee_code,
            name,
            pay_type,
            department_id,
            default_operation_id,
            contractor_id,
            shift_rate,
            status,
            worker_type
        FROM employees
        WHERE id = ? OR employee_code = ?
        """,
        (employee_id, str(employee_id)),
    )

    row = cursor.fetchone()

    if row is None:
        return None

    columns = [column[0] for column in cursor.description]

    return dict(zip(columns, row))


def create_employee(connection, employee):
    from fastapi import HTTPException

    code = employee.employee_code.strip() if employee.employee_code else None
    name = employee.name.strip() if employee.name else ""

    if not name:
        raise HTTPException(status_code=400, detail="Employee name is required.")

    cursor = connection.cursor()

    if code:
        cursor.execute(
            "SELECT id FROM employees WHERE LOWER(TRIM(employee_code)) = LOWER(?)",
            (code,),
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=409,
                detail=f"Employee code '{code}' already exists.",
            )

    cursor.execute(
        "SELECT id FROM employees WHERE LOWER(TRIM(name)) = LOWER(?)",
        (name,),
    )
    if cursor.fetchone():
        raise HTTPException(
            status_code=409,
            detail=f"Employee name '{name}' already exists.",
        )

    try:
        cursor.execute(
            """
            INSERT INTO employees (
                employee_code,
                name,
                pay_type,
                department_id,
                default_operation_id,
                contractor_id,
                shift_rate,
                worker_type
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                code,
                name,
                employee.pay_type,
                employee.department_id,
                employee.default_operation_id,
                employee.contractor_id,
                employee.shift_rate,
                employee.worker_type,
            ),
        )
        connection.commit()
        last_id = cursor.lastrowid
    except HTTPException:
        connection.rollback()
        raise
    except Exception as exc:
        connection.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    return get_employee(connection, last_id)



def update_employee(connection, employee_id, employee):

    existing = get_employee(connection, employee_id)
    if existing is None:
        return None

    actual_id = existing["id"]

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE employees
        SET
            employee_code = ?,
            name = ?,
            pay_type = ?,
            department_id = ?,
            default_operation_id = ?,
            contractor_id = ?,
            shift_rate = ?,
            worker_type = ?,
            status = ?
        WHERE id = ?
        """,
        (
            employee.employee_code,
            employee.name,
            employee.pay_type,
            employee.department_id,
            employee.default_operation_id,
            employee.contractor_id,
            employee.shift_rate,
            employee.worker_type,
            employee.status,
            actual_id,
        ),
    )

    connection.commit()

    return get_employee(connection, actual_id)


def delete_employee(connection, employee_id):

    existing = get_employee(connection, employee_id)
    if existing is None:
        return

    actual_id = existing["id"]

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE employees
        SET status = 'inactive'
        WHERE id = ?
        """,
        (actual_id,),
    )

    connection.commit()