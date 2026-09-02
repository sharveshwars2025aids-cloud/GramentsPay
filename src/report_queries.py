"""
report_queries.py

Reads data from the database and prepares
datasets for the weekly closing report.

This module DOES NOT
- read Excel
- write Excel
- use openpyxl
- know worksheet layouts

Responsibilities

Database
    ↓
SQL Queries
    ↓
Python Dictionaries
    ↓
Excel Generator
"""

from __future__ import annotations

import sqlite3
from typing import Any

from template_mapper import QueryName
from salary_engine import calculate_weekly_salary


# ==========================================================
# DATABASE HELPERS
# ==========================================================

def rows_to_dicts(cursor: sqlite3.Cursor) -> list[dict[str, Any]]:
    """
    Converts sqlite rows into dictionaries.

    Returns
    [
        {
            "employee": "RAVI",
            "qty": 120,
            "amount": 840,
        }
    ]
    """

    columns = [column[0] for column in cursor.description]

    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def fetch_all(
    connection: sqlite3.Connection,
    sql: str,
    parameters: tuple = (),
) -> list[dict[str, Any]]:
    """
    Executes a SELECT query that returns
    multiple rows.
    """

    cursor = connection.cursor()
    cursor.execute(sql, parameters)

    return rows_to_dicts(cursor)


def fetch_one(
    connection: sqlite3.Connection,
    sql: str,
    parameters: tuple = (),
) -> dict[str, Any] | None:
    """
    Executes a SELECT query that returns
    one row.
    """

    cursor = connection.cursor()
    cursor.execute(sql, parameters)

    row = cursor.fetchone()

    if row is None:
        return None

    columns = [column[0] for column in cursor.description]

    return dict(zip(columns, row))


# ==========================================================
# COMMON QUERY HELPERS
# ==========================================================

def get_week(
    connection: sqlite3.Connection,
    week_id: int,
) -> dict[str, Any]:

    """
    Returns one week's information.
    """

    return fetch_one(
        connection,
        """
        SELECT *
        FROM weeks
        WHERE id = ?
        """,
        (week_id,),
    )


def get_department_id(
    connection: sqlite3.Connection,
    department_name: str,
) -> int:

    """
    Returns department id.
    """

    row = fetch_one(
        connection,
        """
        SELECT id
        FROM departments
        WHERE UPPER(name)=UPPER(?)
        """,
        (department_name,),
    )

    if row is None:
        raise LookupError(
            f"Department '{department_name}' not found."
        )

    return row["id"]


def get_contractor_id(
    connection: sqlite3.Connection,
    contractor_name: str,
) -> int:

    """
    Returns contractor id.
    """

    row = fetch_one(
        connection,
        """
        SELECT id
        FROM contractors
        WHERE UPPER(name)=UPPER(?)
        """,
        (contractor_name,),
    )

    if row is None:
        raise LookupError(
            f"Contractor '{contractor_name}' not found."
        )

    return row["id"]


# ==========================================================
# REPORT FUNCTIONS
# ==========================================================

def power_table_helpers(
    connection: sqlite3.Connection,
    week_id: int,
):
    raise NotImplementedError


def company_helpers(
    connection: sqlite3.Connection,
    week_id: int,
):
    raise NotImplementedError


def power_pc_rate(
    connection: sqlite3.Connection,
    week_id: int,
):
    raise NotImplementedError


def singer_pc_rate(
    connection: sqlite3.Connection,
    week_id: int,
):
    raise NotImplementedError


def checking_shift(
    connection: sqlite3.Connection,
    week_id: int,
):
    raise NotImplementedError


def checking_pc_rate(
    connection: sqlite3.Connection,
    week_id: int,
):
    raise NotImplementedError


def ironing_pc_rate(
    connection: sqlite3.Connection,
    week_id: int,
):
    raise NotImplementedError


def salary(
    connection: sqlite3.Connection,
    week_id: int,
):
    raise NotImplementedError


def bank_transfer(
    connection: sqlite3.Connection,
    week_id: int,
):
    raise NotImplementedError


def pt_shift(
    connection: sqlite3.Connection,
    week_id: int,
):
    raise NotImplementedError


def expenses(
    connection: sqlite3.Connection,
    week_id: int,
):
    raise NotImplementedError


def outsource(
    connection: sqlite3.Connection,
    week_id: int,
):
    raise NotImplementedError


def security(
    connection: sqlite3.Connection,
    week_id: int,
):
    raise NotImplementedError


# ==========================================================
# GENERIC REPORT BUILDERS
# ==========================================================

def get_piece_rate_workers(
    connection: sqlite3.Connection,
    *,
    week_id: int,
    department: str,
    contractor_only: bool = False,
    company_only: bool = False,
    worker_type: str | None = None,
    group_by_item: bool = False,
) -> list[dict[str, Any]]:

    """
    Returns piece-rate production grouped by employee.
    """

    sql = """
    SELECT
        e.id AS employee_id,
        e.name AS employee_name,
        d.name AS department,
        c.name AS contractor,
        pr.type AS item,
        SUM(pr.total_qty) AS total_qty,
        AVG(pr.rate) AS rate,
        SUM(pr.total_amount) AS total_amount

    FROM production_records pr

    JOIN employees e
        ON pr.employee_id = e.id

    JOIN departments d
        ON e.department_id = d.id

    LEFT JOIN contractors c
        ON e.contractor_id = c.id

    WHERE
        pr.week_id = ?
        AND UPPER(d.name)=UPPER(?)
        AND e.pay_type='PIECE'
    """

    parameters = [week_id, department]

    if contractor_only:

        sql += """
        AND e.contractor_id IS NOT NULL
        """

    if company_only:

        sql += """
        AND e.contractor_id IS NULL
        """

    if worker_type is not None:

        sql += """
        AND e.worker_type = ?
        """

        parameters.append(worker_type)

    sql += """
        GROUP BY
            e.id
        """

    if group_by_item:

        sql += """
            , pr.type
        """

    sql += """
        ORDER BY
            e.name
        """

    return fetch_all(
        connection,
        sql,
        tuple(parameters),
    )


def get_shift_workers(
    connection: sqlite3.Connection,
    *,
    week_id: int,
    department: str,
    contractor_only: bool = False,
    company_only: bool = False,
    worker_type: str | None = None,
) -> list[dict[str, Any]]:

    """
    Returns shift workers grouped by employee and item.
    """

    sql = """
    SELECT

        e.id AS employee_id,

        e.name AS employee_name,

        d.name AS department,

        COALESCE(
            o.operation_name,
            ''
        ) AS operation,

        c.name AS contractor,

        COALESCE(
            sr.item,
            ''
        ) AS item,

        SUM(sr.shifts) AS total_shifts,

        SUM(sr.daily_salary) / NULLIF(SUM(sr.shifts), 0) AS shift_rate,

        SUM(sr.daily_salary) AS total_salary

    FROM shift_records sr

    JOIN employees e
        ON sr.employee_id = e.id

    JOIN departments d
        ON e.department_id = d.id

    LEFT JOIN contractors c
        ON e.contractor_id = c.id

    LEFT JOIN operations o
        ON sr.operation_id = o.id

    WHERE
        sr.week_id = ?
        AND UPPER(d.name) = UPPER(?)
        AND e.pay_type = 'SHIFT'
    """

    parameters = [week_id, department]

    if contractor_only:

        sql += """
        AND e.contractor_id IS NOT NULL
        """

    if company_only:

        sql += """
        AND e.contractor_id IS NULL
        """

    if worker_type is not None:

        sql += """
        AND e.worker_type = ?
        """

        parameters.append(worker_type)

    sql += """
    GROUP BY
        e.id,
        e.name,
        d.name,
        o.operation_name,
        c.name,
        sr.item,
        e.shift_rate

    ORDER BY
        c.name,
        e.name,
        sr.item
    """

    return fetch_all(
        connection,
        sql,
        tuple(parameters),
    )


def get_expense_items(
    connection: sqlite3.Connection,
    *,
    week_id: int,
) -> list[dict[str, Any]]:

    """
    Returns general expenses.
    """

    return fetch_all(
        connection,
        """
        SELECT
            category AS expense_name,
            amount

        FROM expenses

        WHERE week_id = ?

        ORDER BY id
        """,
        (week_id,),
    )


def get_outsource_payments(
    connection: sqlite3.Connection,
    *,
    week_id: int,
) -> list[dict[str, Any]]:

    return fetch_all(
        connection,
        """
        SELECT
            centre_name,
            style,
            item,
            qty,
            rate,
            amount AS salary

        FROM outsource_payments

        WHERE week_id = ?

        ORDER BY centre_name, style, item
        """,
        (week_id,),
    )


def get_bank_transfers(
    connection: sqlite3.Connection,
    *,
    week_id: int,
) -> list[dict[str, Any]]:

    return fetch_all(
        connection,
        """
        SELECT
            bt.*,
            e.name AS employee_name

        FROM bank_transfers bt

        JOIN employees e
            ON bt.employee_id = e.id

        WHERE bt.week_id=?

        ORDER BY e.name
        """,
        (week_id,),
    )


def get_security_payment(
    connection: sqlite3.Connection,
    *,
    week_id: int,
) -> list[dict[str, Any]]:

    return fetch_all(
        connection,
        """
        SELECT
            e.name AS name,
            sp.days AS days,
            sp.amount AS salary

        FROM security_payments sp

        JOIN employees e
            ON sp.employee_id = e.id

        WHERE sp.week_id = ?

        ORDER BY e.name
        """,
        (week_id,),
    )


def get_all_transaction_details(
    connection: sqlite3.Connection,
    *,
    week_id: int,
) -> list[dict[str, Any]]:

    """
    Returns all weekly financial transactions
    for the Bank Transfer report.

    Includes:
        - Employee salaries
        - Contractor commissions
        - General expenses
        - Outsource payments
        - Security payments
    """

    transactions = []

    # ------------------------------------------------------
    # 1. EMPLOYEE SALARIES
    # ------------------------------------------------------

    employee_salary = fetch_all(
        connection,
        """
        SELECT
            e.name AS name,
            d.name AS department,
            SUM(pr.total_amount) AS amount

        FROM production_records pr

        JOIN employees e
            ON pr.employee_id = e.id

        JOIN departments d
            ON e.department_id = d.id

        WHERE
            pr.week_id = ?
            AND e.pay_type = 'PIECE'

        GROUP BY
            e.id,
            e.name,
            d.name

        ORDER BY
            e.name
        """,
        (week_id,),
    )

    transactions.extend(employee_salary)

    # ------------------------------------------------------
    # 2. SHIFT EMPLOYEE SALARIES
    # ------------------------------------------------------

    shift_salary = fetch_all(
        connection,
        """
        SELECT
            e.name AS name,
            d.name AS department,
            SUM(sr.daily_salary) AS amount

        FROM shift_records sr

        JOIN employees e
            ON sr.employee_id = e.id

        JOIN departments d
            ON e.department_id = d.id

        WHERE
            sr.week_id = ?

        GROUP BY
            e.id,
            e.name,
            d.name

        ORDER BY
            e.name
        """,
        (week_id,),
    )

    transactions.extend(shift_salary)

    # ------------------------------------------------------
    # 3. CONTRACTOR COMMISSIONS
    # ------------------------------------------------------

    contractor_commissions = fetch_all(
        connection,
        """
        SELECT
            c.name AS name,
            'CONTRACTOR' AS department,
            SUM(sr.shifts) * c.commission_amount AS amount

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
        (week_id,),
    )

    transactions.extend(contractor_commissions)

    # ------------------------------------------------------
    # 4. GENERAL EXPENSES
    # ------------------------------------------------------

    expenses = fetch_all(
        connection,
        """
        SELECT
            category AS name,
            'GENERAL EXPENSE' AS department,
            amount

        FROM expenses

        WHERE week_id = ?

        ORDER BY id
        """,
        (week_id,),
    )

    transactions.extend(expenses)

    # ------------------------------------------------------
    # 5. OUTSOURCE PAYMENTS
    # ------------------------------------------------------

    outsource = fetch_all(
        connection,
        """
        SELECT
            centre_name AS name,
            'OUTSOURCE' AS department,
            SUM(amount) AS amount

        FROM outsource_payments

        WHERE week_id = ?

        GROUP BY
            centre_name

        ORDER BY
            centre_name
        """,
        (week_id,),
    )

    transactions.extend(outsource)

    # ------------------------------------------------------
    # 6. SECURITY PAYMENTS
    # ------------------------------------------------------

    security = fetch_all(
        connection,
        """
        SELECT
            e.name AS name,
            'SECURITY' AS department,
            SUM(sp.amount) AS amount

        FROM security_payments sp

        JOIN employees e
            ON sp.employee_id = e.id

        WHERE sp.week_id = ?

        GROUP BY
            e.id,
            e.name

        ORDER BY
            e.name
        """,
        (week_id,),
    )

    transactions.extend(security)

    return transactions


# ==========================================================
# REPORT FUNCTIONS
# ==========================================================

def power_table_contractor(
    connection: sqlite3.Connection,
    week_id: int,
):

    """
    Power Table - Contractor Shift Workers.
    """

    return get_shift_workers(
        connection,
        week_id=week_id,
        department="POWERTABLE",
        contractor_only=True,
        worker_type="OPERATOR",
    )


def power_table_company(
    connection: sqlite3.Connection,
    week_id: int,
):

    """
    Power Table - Company Shift Workers.
    """

    return get_shift_workers(
        connection,
        week_id=week_id,
        department="POWERTABLE",
        company_only=True,
        worker_type="OPERATOR",
    )


# ==========================================================
# SHEET 1 - TALRS HELPERS
# ==========================================================

def get_helper_shift_workers(
    connection: sqlite3.Connection,
    *,
    week_id: int,
    contractor_only: bool = False,
    company_only: bool = False,
) -> list[dict[str, Any]]:
    """
    Returns helper shift workers for TALRS-HELPERS.

    Sheet 1 output:

        name
        operation
        item
        shift
        rate_per_shift
        salary
        contractor

    Operation comes from employee.worker_type.

    Shift rate comes from employee.shift_rate.
    """

    sql = """
    SELECT

        e.name AS employee_name,

        COALESCE(
            o.operation_name,
            ''
        ) AS operation,

        COALESCE(
            pr.type,
            sr.item,
            ''
        ) AS item,

        SUM(sr.shifts) AS total_shifts,

        SUM(sr.daily_salary) / NULLIF(SUM(sr.shifts), 0) AS shift_rate,

        SUM(sr.daily_salary) AS total_salary,

        COALESCE(
            c.name,
            'COMPANY'
        ) AS contractor

    FROM shift_records sr

    JOIN employees e
        ON sr.employee_id = e.id

    JOIN departments d
        ON e.department_id = d.id

    LEFT JOIN contractors c
        ON e.contractor_id = c.id

    LEFT JOIN operations o
        ON sr.operation_id = o.id

    LEFT JOIN production_records pr
        ON pr.employee_id = sr.employee_id
        AND pr.week_id = sr.week_id
        AND pr.work_date = sr.work_date

    WHERE

        sr.week_id = ?

        AND UPPER(d.name) = UPPER(?)

        AND e.pay_type = 'SHIFT'

        AND UPPER(e.worker_type) = UPPER('HELPER')
    """

    parameters = [
        week_id,
        "POWERTABLE",
    ]

    if contractor_only:
        sql += """
        AND e.contractor_id IS NOT NULL
        """

    if company_only:
        sql += """
        AND e.contractor_id IS NULL
        """

    sql += """
    GROUP BY

        e.id,
        e.name,
        o.operation_name,
        pr.type,
        sr.item,
        e.shift_rate,
        c.name

    ORDER BY

        c.name,
        e.name,
        pr.type,
        sr.item
    """

    return fetch_all(
        connection,
        sql,
        tuple(parameters),
    )

def helpers_contractor(
    connection: sqlite3.Connection,
    week_id: int,
):
    """
    TALRS-HELPERS - Contractor Helpers.
    """
    return get_helper_shift_workers(
        connection,
        week_id=week_id,
        contractor_only=True,
    )


def helpers_company(
    connection: sqlite3.Connection,
    week_id: int,
):
    """
    TALRS-HELPERS - Company Helpers.
    """
    return get_helper_shift_workers(
        connection,
        week_id=week_id,
        company_only=True,
    )


def power_pc_rate(
    connection: sqlite3.Connection,
    week_id: int,
):

    """
    Power PC Rate.

    Output:
        name
        item
        salary
    """

    return fetch_all(
        connection,
        """
        SELECT
            e.name AS name,
            pr.type AS item,
            SUM(pr.total_amount) AS salary

        FROM production_records pr

        JOIN employees e
            ON pr.employee_id = e.id

        JOIN departments d
            ON e.department_id = d.id

        WHERE
            pr.week_id = ?

            AND UPPER(d.name) = UPPER(?)

            AND e.pay_type = 'PIECE'

        GROUP BY
            e.id,
            pr.type

        ORDER BY
            e.name,
            pr.type
        """,
        (
            week_id,
            "POWER",
        ),
    )


def singer_pc_rate(
    connection: sqlite3.Connection,
    week_id: int,
):

    """
    Singer PC Rate.

    Output:
        name
        item
        salary
    """

    return fetch_all(
        connection,
        """
        SELECT
            e.name AS name,
            pr.type AS item,
            SUM(pr.total_amount) AS salary

        FROM production_records pr

        JOIN employees e
            ON pr.employee_id = e.id

        JOIN departments d
            ON e.department_id = d.id

        WHERE
            pr.week_id = ?

            AND UPPER(d.name) = UPPER(?)

            AND e.pay_type = 'PIECE'

        GROUP BY
            e.id,
            pr.type

        ORDER BY
            e.name,
            pr.type
        """,
        (
            week_id,
            "SINGER",
        ),
    )


def checking_shift(
    connection: sqlite3.Connection,
    week_id: int,
):

    """
    Checking Shift.

    Output:
        name
        shift
        salary
    """

    return fetch_all(
        connection,
        """
        SELECT
            e.name AS name,
            SUM(sr.shifts) AS shifts,
            SUM(sr.daily_salary) AS salary

        FROM shift_records sr

        JOIN employees e
            ON sr.employee_id = e.id

        JOIN departments d
            ON e.department_id = d.id

        WHERE
            sr.week_id = ?

            AND UPPER(d.name) = UPPER(?)

            AND e.pay_type = 'SHIFT'

        GROUP BY e.id

        ORDER BY e.name
        """,
        (
            week_id,
            "CHECKING",
        ),
    )


def checking_pc_rate(
    connection: sqlite3.Connection,
    week_id: int,
):

    """
    Checking PC Rate.

    Output:
        name
        item
        salary
    """

    return fetch_all(
        connection,
        """
        SELECT
            e.name AS name,
            pr.type AS item,
            SUM(pr.total_amount) AS salary

        FROM production_records pr

        JOIN employees e
            ON pr.employee_id = e.id

        JOIN departments d
            ON e.department_id = d.id

        WHERE
            pr.week_id = ?

            AND UPPER(d.name) = UPPER(?)

            AND e.pay_type = 'PIECE'

        GROUP BY
            e.id,
            pr.type

        ORDER BY
            e.name,
            pr.type
        """,
        (
            week_id,
            "CHECKING",
        ),
    )


def ironing_pc_rate(
    connection: sqlite3.Connection,
    week_id: int,
):

    """
    Ironing PC Rate.

    Output:
        name
        item
        salary
    """

    return fetch_all(
        connection,
        """
        SELECT
            e.name AS name,
            pr.type AS item,
            SUM(pr.total_amount) AS salary

        FROM production_records pr

        JOIN employees e
            ON pr.employee_id = e.id

        JOIN departments d
            ON e.department_id = d.id

        WHERE
            pr.week_id = ?

            AND UPPER(d.name) = UPPER(?)

            AND e.pay_type = 'PIECE'

        GROUP BY
            e.id,
            pr.type

        ORDER BY
            e.name,
            pr.type
        """,
        (
            week_id,
            "IRONING",
        ),
    )


def expenses(
    connection: sqlite3.Connection,
    week_id: int,
):

    """
    General Expenses.
    """

    return get_expense_items(
        connection,
        week_id=week_id,
    )


def outsource(
    connection: sqlite3.Connection,
    week_id: int,
):

    """
    Outsource Work Centres.
    """

    return get_outsource_payments(
        connection,
        week_id=week_id,
    )


def security(
    connection: sqlite3.Connection,
    week_id: int,
):

    """
    Security Payment.
    """

    return get_security_payment(
        connection,
        week_id=week_id,
    )


def bank_transfer(
    connection: sqlite3.Connection,
    week_id: int,
):

    """
    Bank Transfer report.

    Includes all weekly financial transactions:

        - Employee salaries
        - Contractor commissions
        - General expenses
        - Outsource payments
        - Security payments
    """

    return get_all_transaction_details(
        connection,
        week_id=week_id,
    )


def salary(
    connection: sqlite3.Connection,
    week_id: int,
):

    """
    Salary report.
    """

    result = calculate_weekly_salary(
        week_id,
    )

    if result is None:
        return []

    return list(
        result["employees"].values()
    )


def salary_department_summary(
    connection: sqlite3.Connection,
    week_id: int,
):

    """
    Salary Table 1:

    S.No | Department | Salary
    """

    return fetch_all(
        connection,
        """
        SELECT
            d.name AS department,
            SUM(salary_amount) AS salary

        FROM (

            -- PC RATE WORKERS

            SELECT
                e.department_id,
                SUM(pr.total_amount) AS salary_amount

            FROM production_records pr

            JOIN employees e
                ON pr.employee_id = e.id

            WHERE
                pr.week_id = ?
                AND e.pay_type = 'PIECE'

            GROUP BY
                e.department_id

            UNION ALL

            -- SHIFT WORKERS

            SELECT
                e.department_id,
                SUM(sr.daily_salary) AS salary_amount

            FROM shift_records sr

            JOIN employees e
                ON sr.employee_id = e.id

            WHERE
                sr.week_id = ?
                AND e.pay_type = 'SHIFT'

            GROUP BY
                e.department_id

        ) salary_data

        JOIN departments d
            ON salary_data.department_id = d.id

        GROUP BY
            d.id,
            d.name

        ORDER BY
            d.name
        """,
        (
            week_id,
            week_id,
        ),
    )


def salary_operations(
    connection: sqlite3.Connection,
    week_id: int,
):

    """
    Salary Table 2:

    Style | Qty | Rate | Amt

    Grouped by style + garment type, matching the
    factory's existing "PRODUCTION DETAILS" sheet format,
    e.g. "PEV007S26 (ROMPER)".
    """

    return fetch_all(
        connection,
        """
        SELECT
            s.style_no
                || ' ('
                || pr.type
                || ')' AS style,

            SUM(pr.total_qty) AS qty,

            AVG(pr.rate) AS rate,

            SUM(pr.total_amount) AS amt

        FROM production_records pr

        JOIN styles s
            ON pr.style_id = s.id

        WHERE
            pr.week_id = ?

        GROUP BY
            s.id,
            s.style_no,
            pr.type

        ORDER BY
            s.style_no,
            pr.type
        """,
        (week_id,),
    )


def pt_shift(
    connection: sqlite3.Connection,
    week_id: int,
):

    """
    PT Shift report.

    Returns:
        name
        operation
        shift
        rate_per_shift
        salary
        contractor
    """

    return fetch_all(
        connection,
        """
        SELECT
            e.name AS name,

            COALESCE(
                o.operation_name,
                ''
            ) AS operation,

            COALESCE(
                sr.item,
                ''
            ) AS item,

            SUM(sr.shifts) AS shift,

            SUM(sr.daily_salary) / NULLIF(SUM(sr.shifts), 0) AS rate_per_shift,

            SUM(sr.daily_salary) AS salary,

            COALESCE(
                c.name,
                'COMPANY'
            ) AS contractor

        FROM shift_records sr

        JOIN employees e
            ON sr.employee_id = e.id

        LEFT JOIN departments d
            ON e.department_id = d.id

        LEFT JOIN operations o
            ON sr.operation_id = o.id

        LEFT JOIN contractors c
            ON e.contractor_id = c.id

        WHERE
            sr.week_id = ?

            AND e.pay_type = 'SHIFT'

        GROUP BY
            e.id,
            e.name,
            o.operation_name,
            sr.item,
            c.name

        ORDER BY
            c.name,
            e.name,
            o.operation_name,
            sr.item
        """,
        (
            week_id,
        ),
    )



def summary(
    connection: sqlite3.Connection,
    week_id: int,
):

    """
    Weekly Summary.

    Implemented after salary engine.
    """

    raise NotImplementedError(
        "Summary engine not implemented yet."
    )


# ==========================================================
# QUERY DISPATCHER
# ==========================================================

QUERY_MAP = {

    QueryName.POWER_TABLE_CONTRACTOR:
        power_table_contractor,

    QueryName.POWER_TABLE_COMPANY:
        power_table_company,

    QueryName.HELPERS_CONTRACTOR:
        helpers_contractor,

    QueryName.HELPERS_COMPANY:
        helpers_company,

    QueryName.POWER_PC_RATE:
        power_pc_rate,

    QueryName.SINGER_PC_RATE:
        singer_pc_rate,

    QueryName.CHECKING_SHIFT:
        checking_shift,

    QueryName.CHECKING_PC_RATE:
        checking_pc_rate,

    QueryName.IRONING_PC_RATE:
        ironing_pc_rate,

    QueryName.EXPENSES:
        expenses,

    QueryName.OUTSOURCE:
        outsource,

    QueryName.SECURITY:
        security,

    QueryName.BANK_TRANSFER:
        bank_transfer,

    QueryName.PT_SHIFT:
        pt_shift,

    QueryName.SALARY_DEPARTMENT_SUMMARY:
        salary_department_summary,

    QueryName.SALARY_OPERATIONS:
        salary_operations,

    QueryName.SALARY:
        salary,

    QueryName.SUMMARY:
        summary,
}


# ==========================================================
# REPORT EXECUTOR
# ==========================================================

def run_report_query(
    connection: sqlite3.Connection,
    query_name: QueryName,
    week_id: int,
):

    """
    Executes a report query by QueryName.
    """

    try:

        report_function = QUERY_MAP[query_name]

    except KeyError:

        raise ValueError(
            f"Unknown report query: {query_name}"
        )

    return report_function(
        connection,
        week_id,
    )


# ==========================================================
# VALIDATION
# ==========================================================

def validate_query_map() -> None:

    """
    Ensures every QueryName
    has an implementation.
    """

    missing = []

    for query in QueryName:

        if query not in QUERY_MAP:
            missing.append(query.name)

    if missing:

        raise RuntimeError(
            "Missing report implementations:\n"
            + "\n".join(missing)
        )


# ==========================================================
# MODULE INITIALIZATION
# ==========================================================

validate_query_map()