"""
resolver.py

Resolves extracted entities (employee name, week reference, date, department)
against actual master data in the GarmentsPay database.
"""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime, date, timedelta
from typing import Any, Optional


class EmployeeResolutionError(Exception):
    """Base exception for employee resolution failures."""
    pass


class EmployeeNotFoundError(EmployeeResolutionError):
    """Raised when no employee matches the search term."""
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"I couldn't find an employee matching {name}.")


class AmbiguousEmployeeError(EmployeeResolutionError):
    """Raised when multiple employees match the search term."""
    def __init__(self, name: str, matches: list[dict[str, Any]]):
        self.name = name
        self.matches = matches
        super().__init__(f"I found multiple employees matching {name}. Please provide the employee code.")


class WeekResolutionError(Exception):
    """Raised when a referenced week cannot be identified in the database."""
    def __init__(self, week_ref: str):
        self.week_ref = week_ref
        super().__init__(f"I couldn't find a week matching '{week_ref}'. Please provide a valid week ID or date range.")


def resolve_employee(
    connection: sqlite3.Connection,
    query: str,
) -> dict[str, Any]:
    """
    Resolves an employee name or code against the employee master records.
    Returns employee dict with id, employee_code, name, pay_type, department_id, status.
    Raises EmployeeNotFoundError or AmbiguousEmployeeError.
    """
    clean_query = query.strip()
    cursor = connection.cursor()

    # 1. Exact match on employee_code
    cursor.execute(
        """
        SELECT id, employee_code, name, pay_type, department_id, status
        FROM employees
        WHERE UPPER(TRIM(employee_code)) = UPPER(?)
        """,
        (clean_query,),
    )
    rows = cursor.fetchall()
    if len(rows) == 1:
        return _format_employee_row(cursor, rows[0])

    # 2. Exact match on name
    cursor.execute(
        """
        SELECT id, employee_code, name, pay_type, department_id, status
        FROM employees
        WHERE UPPER(TRIM(name)) = UPPER(?)
        """,
        (clean_query,),
    )
    rows = cursor.fetchall()
    if len(rows) == 1:
        return _format_employee_row(cursor, rows[0])

    # 3. Substring / partial matches on name or code
    cursor.execute(
        """
        SELECT id, employee_code, name, pay_type, department_id, status
        FROM employees
        WHERE UPPER(name) LIKE UPPER(?) OR UPPER(employee_code) LIKE UPPER(?)
        ORDER BY status ASC, name ASC
        """,
        (f"%{clean_query}%", f"%{clean_query}%"),
    )
    rows = cursor.fetchall()

    if not rows:
        raise EmployeeNotFoundError(clean_query)

    if len(rows) == 1:
        return _format_employee_row(cursor, rows[0])

    # Check if exactly one has word boundary match
    word_pattern = rf"\b{re.escape(clean_query.upper())}\b"
    exact_word_matches = [r for r in rows if re.search(word_pattern, r[2].upper())]
    if len(exact_word_matches) == 1:
        return _format_employee_row(cursor, exact_word_matches[0])

    # Multiple candidates remain ambiguous
    matches_list = [_format_employee_row(cursor, r) for r in rows]
    raise AmbiguousEmployeeError(clean_query, matches_list)


def _format_employee_row(cursor: sqlite3.Cursor, row: tuple) -> dict[str, Any]:
    return {
        "id": row[0],
        "employee_code": row[1] or str(row[0]),
        "name": row[2],
        "pay_type": row[3],
        "department_id": row[4],
        "status": row[5],
    }


def parse_date_string(date_text: str) -> Optional[str]:
    """
    Parses common date representations into YYYY-MM-DD.
    Supports YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY, and relative 'today'/'yesterday'.
    """
    if not date_text:
        return None
    d = date_text.strip().lower()
    if d == "today":
        return date.today().strftime("%Y-%m-%d")
    if d == "yesterday":
        return (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    # Try common formats
    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
    ]
    for fmt in formats:
        try:
            parsed = datetime.strptime(d, fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            pass

    return None


def resolve_week(
    connection: sqlite3.Connection,
    week_ref: Optional[str] = None,
    employee_id: Optional[int] = None,
) -> dict[str, Any]:
    """
    Resolves a week reference (e.g. 'current', 'this week', 'last week', '147', date)
    to a verified row from the `weeks` table.
    Returns:
        {"id": week_id, "week_start": ..., "week_end": ..., "closing_generated": ...}
    Raises WeekResolutionError.
    """
    cursor = connection.cursor()

    # Check if empty database
    cursor.execute("SELECT COUNT(*) FROM weeks")
    if cursor.fetchone()[0] == 0:
        raise WeekResolutionError(week_ref or "current")

    ref = (week_ref or "current").strip().lower()

    # Case 1: Specific week ID mentioned (e.g. "week 147", "147", "week #147")
    id_match = re.search(r"\b(?:week\s*#?\s*)?(\d+)\b", ref)
    if id_match and ref not in ("current", "this week", "last week", "today", "yesterday"):
        potential_id = int(id_match.group(1))
        cursor.execute(
            "SELECT id, week_start, week_end, closing_generated FROM weeks WHERE id = ?",
            (potential_id,),
        )
        row = cursor.fetchone()
        if row:
            return _format_week_row(row)
        # If user explicitly requested a specific number that doesn't exist:
        raise WeekResolutionError(ref)

    # Case 2: Specific Date mentioned
    parsed_date = parse_date_string(ref)
    if parsed_date:
        cursor.execute(
            """
            SELECT id, week_start, week_end, closing_generated
            FROM weeks
            WHERE week_start <= ? AND week_end >= ?
            ORDER BY id DESC LIMIT 1
            """,
            (parsed_date, parsed_date),
        )
        row = cursor.fetchone()
        if row:
            return _format_week_row(row)
        raise WeekResolutionError(ref)

    # Case 3: "last week" / "previous week"
    if "last" in ref or "prev" in ref:
        cursor.execute(
            """
            SELECT id, week_start, week_end, closing_generated
            FROM weeks
            ORDER BY week_end DESC, id DESC
            """
        )
        all_weeks = cursor.fetchall()
        if len(all_weeks) >= 2:
            return _format_week_row(all_weeks[1])
        if all_weeks:
            return _format_week_row(all_weeks[0])
        raise WeekResolutionError(ref)

    # Case 4: "this week" / "current week" / default
    # If an employee_id is provided, check if the employee has records in a specific week
    if employee_id is not None:
        # Check shift_records
        cursor.execute(
            """
            SELECT w.id, w.week_start, w.week_end, w.closing_generated
            FROM weeks w
            JOIN shift_records sr ON sr.week_id = w.id
            WHERE sr.employee_id = ?
            ORDER BY w.week_end DESC, w.id DESC LIMIT 1
            """,
            (employee_id,),
        )
        row = cursor.fetchone()
        if row:
            return _format_week_row(row)

        # Check production_records
        cursor.execute(
            """
            SELECT w.id, w.week_start, w.week_end, w.closing_generated
            FROM weeks w
            JOIN production_records pr ON pr.week_id = w.id
            WHERE pr.employee_id = ?
            ORDER BY w.week_end DESC, w.id DESC LIMIT 1
            """,
            (employee_id,),
        )
        row = cursor.fetchone()
        if row:
            return _format_week_row(row)

    # Otherwise return the latest active week with records or latest week
    # Prioritize weeks that have production or shift records
    cursor.execute(
        """
        SELECT w.id, w.week_start, w.week_end, w.closing_generated
        FROM weeks w
        WHERE EXISTS (SELECT 1 FROM shift_records WHERE week_id = w.id)
           OR EXISTS (SELECT 1 FROM production_records WHERE week_id = w.id)
        ORDER BY w.week_end DESC, w.id DESC LIMIT 1
        """
    )
    row = cursor.fetchone()
    if row:
        return _format_week_row(row)

    # Fallback to absolute latest week
    cursor.execute(
        """
        SELECT id, week_start, week_end, closing_generated
        FROM weeks
        ORDER BY week_end DESC, id DESC LIMIT 1
        """
    )
    row = cursor.fetchone()
    if row:
        return _format_week_row(row)

    raise WeekResolutionError(ref)


def _format_week_row(row: tuple) -> dict[str, Any]:
    return {
        "id": row[0],
        "week_start": str(row[1]),
        "week_end": str(row[2]),
        "closing_generated": bool(row[3]),
    }


def resolve_department(
    connection: sqlite3.Connection,
    dept_name: str,
) -> Optional[dict[str, Any]]:
    """
    Resolves department name against the departments table.
    """
    cursor = connection.cursor()
    clean = dept_name.strip()
    cursor.execute(
        "SELECT id, name, status FROM departments WHERE UPPER(name) = UPPER(?)",
        (clean,),
    )
    row = cursor.fetchone()
    if row:
        return {"id": row[0], "name": row[1], "status": row[2]}

    cursor.execute(
        "SELECT id, name, status FROM departments WHERE UPPER(name) LIKE UPPER(?)",
        (f"%{clean}%",),
    )
    row = cursor.fetchone()
    if row:
        return {"id": row[0], "name": row[1], "status": row[2]}

    return None
