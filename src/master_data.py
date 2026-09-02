"""
master_data.py

Manages factory master data.

Responsibilities

- Departments
- Contractors
- Employees
- Styles
- Operations
- Style Operation Rates

This module DOES NOT

- parse Excel
- calculate salary
- generate reports
"""

from __future__ import annotations

import sqlite3
from typing import Any

from database import connect_database


# ==========================================================
# DATABASE HELPERS
# ==========================================================

def execute(
    sql: str,
    parameters: tuple = (),
) -> None:
    """
    Executes INSERT / UPDATE / DELETE statements.
    """

    connection = connect_database()

    try:

        cursor = connection.cursor()

        cursor.execute(sql, parameters)

        connection.commit()

    finally:

        connection.close()


def fetch_one(
    sql: str,
    parameters: tuple = (),
) -> dict[str, Any] | None:
    """
    Returns one row as a dictionary.
    """

    connection = connect_database()

    try:

        cursor = connection.cursor()

        cursor.execute(sql, parameters)

        row = cursor.fetchone()

        if row is None:
            return None

        columns = [column[0] for column in cursor.description]

        return dict(zip(columns, row))

    finally:

        connection.close()


def fetch_all(
    sql: str,
    parameters: tuple = (),
) -> list[dict[str, Any]]:
    """
    Returns multiple rows as dictionaries.
    """

    connection = connect_database()

    try:

        cursor = connection.cursor()

        cursor.execute(sql, parameters)

        columns = [column[0] for column in cursor.description]

        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    finally:

        connection.close()


# ==========================================================
# NORMALIZATION
# ==========================================================

def normalize_name(value: str) -> str:
    """
    Standardizes names before saving/searching.
    """

    return (
        str(value)
        .strip()
        .upper()
    )

# ==========================================================
# DEPARTMENTS
# ==========================================================

def add_department(
    name: str,
) -> None:
    """
    Creates a new department.
    """

    name = normalize_name(name)

    execute(
        """
        INSERT INTO departments(name)
        VALUES(?)
        """,
        (name,),
    )


def get_department(
    name: str,
) -> dict[str, Any] | None:
    """
    Returns one department.
    """

    name = normalize_name(name)

    return fetch_one(
        """
        SELECT *
        FROM departments
        WHERE UPPER(name)=?
        """,
        (name,),
    )


def list_departments() -> list[dict[str, Any]]:
    """
    Returns every department.
    """

    return fetch_all(
        """
        SELECT *
        FROM departments
        ORDER BY name
        """
    )


def update_department(
    old_name: str,
    new_name: str,
) -> None:
    """
    Renames a department.
    """

    execute(
        """
        UPDATE departments
        SET name=?
        WHERE UPPER(name)=?
        """,
        (
            normalize_name(new_name),
            normalize_name(old_name),
        ),
    )


def delete_department(
    name: str,
) -> None:
    """
    Deletes a department.
    """

    execute(
        """
        DELETE
        FROM departments
        WHERE UPPER(name)=?
        """,
        (
            normalize_name(name),
        ),
    )

# ==========================================================
# CONTRACTORS
# ==========================================================

def add_contractor(
    name: str,
    commission_rate: float,
) -> None:
    """
    Creates a new contractor.
    """

    execute(
        """
        INSERT INTO contractors(
            name,
            commission_rate
        )
        VALUES(?, ?)
        """,
        (
            normalize_name(name),
            commission_rate,
        ),
    )


def get_contractor(
    name: str,
) -> dict[str, Any] | None:
    """
    Returns one contractor.
    """

    return fetch_one(
        """
        SELECT *
        FROM contractors
        WHERE UPPER(name)=?
        """,
        (
            normalize_name(name),
        ),
    )


def list_contractors() -> list[dict[str, Any]]:
    """
    Returns all contractors.
    """

    return fetch_all(
        """
        SELECT *
        FROM contractors
        ORDER BY name
        """
    )


def update_contractor(
    name: str,
    *,
    new_name: str | None = None,
    commission_rate: float | None = None,
) -> None:
    """
    Updates contractor information.
    """

    contractor = get_contractor(name)

    if contractor is None:
        raise LookupError(
            f"Contractor '{name}' not found."
        )

    execute(
        """
        UPDATE contractors

        SET
            name = ?,
            commission_rate = ?

        WHERE id = ?
        """,
        (
            normalize_name(
                new_name or contractor["name"]
            ),
            commission_rate
            if commission_rate is not None
            else contractor["commission_rate"],
            contractor["id"],
        ),
    )


def delete_contractor(
    name: str,
) -> None:
    """
    Deletes a contractor.
    """

    execute(
        """
        DELETE FROM contractors
        WHERE UPPER(name)=?
        """,
        (
            normalize_name(name),
        ),
    )


def contractor_exists(
    name: str,
) -> bool:
    """
    Returns True if contractor exists.
    """

    return (
        get_contractor(name)
        is not None
    )

# ==========================================================
# EMPLOYEES
# ==========================================================

def add_employee(
    *,
    employee_code: str | None,
    name: str,
    pay_type: str,
    department_id: int,
    worker_type: str,
    contractor_id: int | None = None,
    shift_rate: float | None = None,
) -> None:
    """
    Creates a new employee.
    """

    execute(
        """
        INSERT INTO employees(
            employee_code,
            name,
            pay_type,
            department_id,
            contractor_id,
            shift_rate,
            worker_type
        )
        VALUES(?,?,?,?,?,?,?)
        """,
        (
            employee_code,
            normalize_name(name),
            pay_type.upper(),
            department_id,
            contractor_id,
            shift_rate,
            worker_type.upper(),
        ),
    )


def get_employee(
    name: str,
) -> dict[str, Any] | None:
    """
    Returns one employee.
    """

    return fetch_one(
        """
        SELECT *

        FROM employees

        WHERE UPPER(name)=?
        """,
        (
            normalize_name(name),
        ),
    )


def list_employees() -> list[dict[str, Any]]:
    """
    Returns all employees.
    """

    return fetch_all(
        """
        SELECT

            e.*,

            d.name AS department,

            c.name AS contractor

        FROM employees e

        LEFT JOIN departments d
            ON e.department_id=d.id

        LEFT JOIN contractors c
            ON e.contractor_id=c.id

        ORDER BY e.name
        """
    )


def search_employee(
    keyword: str,
) -> list[dict[str, Any]]:
    """
    Searches employees by name.
    """

    keyword = f"%{normalize_name(keyword)}%"

    return fetch_all(
        """
        SELECT

            e.*,

            d.name AS department,

            c.name AS contractor

        FROM employees e

        LEFT JOIN departments d
            ON e.department_id = d.id

        LEFT JOIN contractors c
            ON e.contractor_id = c.id

        WHERE UPPER(e.name) LIKE ?

        ORDER BY e.name
        """,
        (
            keyword,
        ),
    )


def update_employee(
    current_name: str,
    *,
    new_name: str | None = None,
    employee_code: str | None = None,
    pay_type: str | None = None,
    department_id: int | None = None,
    contractor_id: int | None = None,
    worker_type: str | None = None,
    shift_rate: float | None = None,
    status: str | None = None,
) -> None:
    """
    Updates employee information.
    """

    employee = get_employee(current_name)

    if employee is None:
        raise LookupError(
            f"Employee '{current_name}' not found."
        )

    execute(
        """
        UPDATE employees

        SET

            employee_code=?,

            name=?,

            pay_type=?,

            department_id=?,

            contractor_id=?,

            worker_type=?,

            shift_rate=?,

            status=?
        WHERE id=?
        """,
        (
            employee_code
            if employee_code is not None
            else employee["employee_code"],

            normalize_name(new_name)
            if new_name is not None
            else employee["name"],

            pay_type.upper()
            if pay_type is not None
            else employee["pay_type"],

            department_id
            if department_id is not None
            else employee["department_id"],

            contractor_id
            if contractor_id is not None
            else employee["contractor_id"],

            worker_type.upper()
            if worker_type is not None
            else employee["worker_type"],

            shift_rate
            if shift_rate is not None
            else employee["shift_rate"],

            status
            if status is not None
            else employee["status"],

            employee["id"],
        ),
    )


def disable_employee(
    name: str,
) -> None:
    """
    Marks an employee as inactive.
    """

    execute(
        """
        UPDATE employees

        SET status='inactive'

        WHERE UPPER(name)=?
        """,
        (
            normalize_name(name),
        ),
    )


def employee_exists(
    name: str,
) -> bool:
    """
    Returns True if employee exists.
    """

    return (
        get_employee(name)
        is not None
    )


def assign_contractor(
    employee_name: str,
    contractor_id: int | None,
) -> None:
    """
    Assigns or removes a contractor
    for an employee.
    """

    execute(
        """
        UPDATE employees

        SET contractor_id=?

        WHERE UPPER(name)=?
        """,
        (
            contractor_id,
            normalize_name(employee_name),
        ),
    )


def change_department(
    employee_name: str,
    department_id: int,
) -> None:
    """
    Moves an employee to another department.
    """

    execute(
        """
        UPDATE employees

        SET department_id=?

        WHERE UPPER(name)=?
        """,
        (
            department_id,
            normalize_name(employee_name),
        ),
    )

# ==========================================================
# STYLES
# ==========================================================

def add_style(
    style_no: str,
    style_name: str | None = None,
) -> None:
    """
    Creates a new style.
    """

    execute(
        """
        INSERT INTO styles(
            style_no,
            style_name
        )
        VALUES(?,?)
        """,
        (
            style_no.strip().upper(),
            style_name.strip()
            if style_name
            else None,
        ),
    )




def get_style(
    style_no: str,
) -> dict[str, Any] | None:
    """
    Returns one style.
    """

    return fetch_one(
        """
        SELECT *

        FROM styles

        WHERE UPPER(style_no)=?
        """,
        (
            normalize_name(style_no),
        ),
    )


def list_styles() -> list[dict[str, Any]]:
    """
    Returns every style.
    """

    return fetch_all(
        """
        SELECT *

        FROM styles

        ORDER BY style_no
        """
    )


def search_style(
    keyword: str,
) -> list[dict[str, Any]]:
    """
    Searches styles.
    """

    keyword = f"%{normalize_name(keyword)}%"

    return fetch_all(
        """
        SELECT *

        FROM styles

        WHERE UPPER(style_no)
        LIKE ?

        ORDER BY style_no
        """,
        (
            keyword,
        ),
    )


def update_style(
    style_no: str,
    *,
    new_style_no: str | None = None,
    style_name: str | None = None,
    status: str | None = None,
) -> None:
    """
    Updates a style.
    """

    style = get_style(style_no)

    if style is None:

        raise LookupError(
            f"Style '{style_no}' not found."
        )

    execute(
        """
        UPDATE styles

        SET

            style_no=?,

            style_name=?,

            status=?

        WHERE id=?
        """,
        (
            new_style_no.strip().upper()
            if new_style_no is not None
            else style["style_no"],

            style_name.strip()
            if style_name is not None
            else style["style_name"],

            status
            if status is not None
            else style["status"],

            style["id"],
        ),
    )


def disable_style(
    style_no: str,
) -> None:
    """
    Marks a style as inactive.
    """

    execute(
        """
        UPDATE styles

        SET status='inactive'

        WHERE UPPER(style_no)=?
        """,
        (
            style_no.strip().upper(),
        ),
    )


def style_exists(
    style_no: str,
) -> bool:
    """
    Returns True if the style exists.
    """

    return (
        get_style(style_no)
        is not None
    )

# ==========================================================
# STYLE OPERATION RATES
# ==========================================================

def add_style_operation_rate(
    *,
    style_no: str,
    operation_name: str,
    rate: float,
) -> None:
    """
    Adds or updates the rate of an operation
    for a style.
    """

    style = get_style(style_no)

    if style is None:
        raise LookupError(
            f"Style '{style_no}' not found."
        )

    operation = fetch_one(
        """
        SELECT id
        FROM operations
        WHERE UPPER(operation_name)=?
        """,
        (
            normalize_name(operation_name),
        ),
    )

    if operation is None:
        raise LookupError(
            f"Operation '{operation_name}' not found."
        )

        operation = fetch_one(
            """
            SELECT id
            FROM operations
            WHERE UPPER(operation_name)=?
            """,
            (
                normalize_name(operation_name),
            ),
        )

    execute(
        """
        INSERT OR REPLACE INTO style_operation_rates(
            style_id,
            operation_id,
            rate
        )
        VALUES(?,?,?)
        """,
        (
            style["id"],
            operation["id"],
            rate,
        ),
    )


def get_style_operation_rates(
    style_no: str,
) -> list[dict[str, Any]]:
    """
    Returns all operation rates
    configured for a style.
    """

    style = get_style(style_no)

    if style is None:
        raise LookupError(
            f"Style '{style_no}' not found."
        )

    return fetch_all(
        """
        SELECT

            o.operation_name AS operation,

            sor.rate

        FROM style_operation_rates sor

        JOIN operations o
            ON sor.operation_id=o.id

        WHERE sor.style_id=?

        ORDER BY o.operation_name
        """,
        (
            style["id"],
        ),
    )


def update_style_operation_rate(
    *,
    style_no: str,
    operation_name: str,
    new_rate: float,
) -> None:
    """
    Updates one operation rate.
    """

    style = get_style(style_no)

    if style is None:
        raise LookupError(
            f"Style '{style_no}' not found."
        )

    operation = fetch_one(
        """
        SELECT id
        FROM operations
        WHERE UPPER(operation_name)=?
        """,
        (
            normalize_name(operation_name),
        ),
    )

    if operation is None:
        raise LookupError(
            f"Operation '{operation_name}' not found."
        )

    execute(
        """
        UPDATE style_operation_rates

        SET rate=?

        WHERE style_id=?
        AND operation_id=?
        """,
        (
            new_rate,
            style["id"],
            operation["id"],
        ),
    )


def delete_style_operation_rate(
    *,
    style_no: str,
    operation_name: str,
) -> None:
    """
    Deletes one operation rate
    from a style.
    """

    style = get_style(style_no)

    if style is None:
        raise LookupError(
            f"Style '{style_no}' not found."
        )

    operation = fetch_one(
        """
        SELECT id
        FROM operations
        WHERE UPPER(operation_name)=?
        """,
        (
            normalize_name(operation_name),
        ),
    )

    if operation is None:
        return

    execute(
        """
        DELETE FROM style_operation_rates

        WHERE style_id=?
        AND operation_id=?
        """,
        (
            style["id"],
            operation["id"],
        ),
    )

# ==========================================================
# OPERATIONS
# ==========================================================

def add_operation(
    operation_name: str,
) -> None:
    """
    Creates a new operation.
    """

    execute(
        """
        INSERT INTO operations(
            operation_name
        )
        VALUES(?)
        """,
        (
            normalize_name(operation_name),
        ),
    )


def get_operation(
    operation_name: str,
) -> dict[str, Any] | None:

    return fetch_one(
        """
        SELECT *

        FROM operations

        WHERE UPPER(operation_name)=?
        """,
        (
            normalize_name(operation_name),
        ),
    )

def operation_exists(
    operation_name: str,
) -> bool:
    """
    Returns True if operation exists.
    """

    return (
        get_operation(operation_name)
        is not None
    )


def list_operations() -> list[dict[str, Any]]:

    return fetch_all(
        """
        SELECT *

        FROM operations

        ORDER BY operation_name
        """
    )

def search_operation(
    keyword: str,
) -> list[dict[str, Any]]:

    keyword = f"%{normalize_name(keyword)}%"

    return fetch_all(
        """
        SELECT *

        FROM operations

        WHERE UPPER(operation_name) LIKE ?

        ORDER BY operation_name
        """,
        (
            keyword,
        ),
    )

def update_operation(
    operation_name: str,
    *,
    new_operation_name: str | None = None,
    status: str | None = None,
) -> None:

    operation = get_operation(operation_name)

    if operation is None:
        raise LookupError(
            f"Operation '{operation_name}' not found."
        )

    execute(
        """
        UPDATE operations

        SET

            operation_name=?,

            status=?

        WHERE id=?
        """,
        (
            normalize_name(new_operation_name)
            if new_operation_name is not None
            else operation["operation_name"],

            status
            if status is not None
            else operation["status"],

            operation["id"],
        ),
    )


def disable_operation(
    operation_name: str,
) -> None:
    """
    Marks an operation as inactive.
    """

    execute(
        """
        UPDATE operations

        SET status='inactive'

        WHERE UPPER(operation_name)=?
        """,
        (
            normalize_name(operation_name),
        ),
    )

# ==========================================================
# OPERATION ALIASES
# ==========================================================

def add_operation_alias(
    operation_name: str,
    alias: str,
) -> None:
    """
    Adds an alias for an operation.
    """

    operation = get_operation(operation_name)

    if operation is None:
        raise LookupError(
            f"Operation '{operation_name}' not found."
        )

    execute(
        """
        INSERT INTO operation_aliases(
            operation_id,
            alias
        )
        VALUES(?,?)
        """,
        (
            operation["id"],
            normalize_name(alias),
        ),
    )

def get_operation_alias(
    alias: str,
) -> dict[str, Any] | None:
    """
    Returns one operation alias.
    """

    return fetch_one(
        """
        SELECT

            oa.*,

            o.operation_name

        FROM operation_aliases oa

        JOIN operations o
            ON oa.operation_id = o.id

        WHERE UPPER(oa.alias)=?
        """,
        (
            normalize_name(alias),
        ),
    )

def list_operation_aliases() -> list[dict[str, Any]]:
    """
    Returns all operation aliases.
    """

    return fetch_all(
        """
        SELECT

            oa.id,

            oa.alias,

            o.operation_name

        FROM operation_aliases oa

        JOIN operations o
            ON oa.operation_id = o.id

        ORDER BY o.operation_name,
                 oa.alias
        """
    )

def delete_operation_alias(
    alias: str,
) -> None:
    """
    Deletes an operation alias.
    """

    execute(
        """
        DELETE FROM operation_aliases

        WHERE UPPER(alias)=?
        """,
        (
            normalize_name(alias),
        ),
    )

def operation_alias_exists(
    alias: str,
) -> bool:
    """
    Returns True if alias exists.
    """

    return (
        get_operation_alias(alias)
        is not None
    )