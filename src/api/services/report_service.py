"""
report_service.py

Service layer for reading factory reports for any given week.
Ensures reports are strictly read-only and delegates calculations
to report_queries and salary_engine.
"""

from typing import Any
from database import connect_database
import report_queries
from template_mapper import QueryName


class ReportNotFoundError(Exception):
    """Raised when the requested week does not exist."""
    pass


def _verify_week_exists(connection, week_id: int) -> None:
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM weeks WHERE id = ?", (week_id,))
    if cursor.fetchone() is None:
        raise ReportNotFoundError(f"Week {week_id} not found.")


def get_salary_report(week_id: int) -> list[dict[str, Any]]:
    """Returns employee salary breakdown using salary engine."""
    conn = connect_database()
    try:
        _verify_week_exists(conn, week_id)
        return report_queries.salary(conn, week_id)
    finally:
        conn.close()


def get_expenses_report(week_id: int) -> list[dict[str, Any]]:
    """Returns general factory expenses for the week."""
    conn = connect_database()
    try:
        _verify_week_exists(conn, week_id)
        return report_queries.expenses(conn, week_id)
    finally:
        conn.close()


def get_outsource_report(week_id: int) -> list[dict[str, Any]]:
    """Returns outsource payments breakdown for the week."""
    conn = connect_database()
    try:
        _verify_week_exists(conn, week_id)
        return report_queries.outsource(conn, week_id)
    finally:
        conn.close()


def get_security_report(week_id: int) -> list[dict[str, Any]]:
    """Returns security payments for the week."""
    conn = connect_database()
    try:
        _verify_week_exists(conn, week_id)
        return report_queries.security(conn, week_id)
    finally:
        conn.close()


def get_department_summary_report(week_id: int) -> list[dict[str, Any]]:
    """Returns department-wise salary summary."""
    conn = connect_database()
    try:
        _verify_week_exists(conn, week_id)
        return report_queries.salary_department_summary(conn, week_id)
    finally:
        conn.close()


def get_operations_report(week_id: int) -> list[dict[str, Any]]:
    """Returns production details by style and type."""
    conn = connect_database()
    try:
        _verify_week_exists(conn, week_id)
        return report_queries.salary_operations(conn, week_id)
    finally:
        conn.close()


def get_bank_transfer_report(week_id: int) -> list[dict[str, Any]]:
    """Returns bank transfer transactions list for the week."""
    conn = connect_database()
    try:
        _verify_week_exists(conn, week_id)
        return report_queries.bank_transfer(conn, week_id)
    finally:
        conn.close()


def get_weekly_summary_report(week_id: int) -> list[dict[str, Any]]:
    """Returns high-level financial summary for the week."""
    conn = connect_database()
    try:
        _verify_week_exists(conn, week_id)
        return report_queries.summary(conn, week_id)
    finally:
        conn.close()
