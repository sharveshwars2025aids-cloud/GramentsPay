from typing import Any

from database import connect_database
from salary_engine import calculate_weekly_salary
from biometric_manager import get_attendance_mismatches
from excel_generator import (
    generate_weekly_closing as build_weekly_closing_workbook,
)
from template_mapper import WEEKLY_CLOSING_TEMPLATE


class WeekNotFoundError(Exception):
    """
    Raised when the requested week does not exist
    or has no calculable salary data.
    """

    def __init__(self, week_id: int):
        self.week_id = week_id
        super().__init__(
            f"Week {week_id} not found or has no salary data."
        )


# The 5 manually-collected categories (never Excel-driven), each with
# the table that holds it. Order matches the collection flow the
# accountant already follows: Outsource -> Security -> Expenses ->
# Deductions -> Bonuses.
MANUAL_INPUT_CATEGORIES = (
    ("outsource", "outsource_payments"),
    ("security", "security_payments"),
    ("expenses", "expenses"),
    ("deductions", "deductions"),
    ("bonuses", "bonuses"),
)


def check_closing_readiness(week_id: int) -> dict[str, Any]:
    """
    Called the moment "Generate Weekly Closing" is pressed.

    Reports which of the 5 manually-collected categories still have
    NO rows for this week, so the frontend knows exactly which
    popups to show the accountant before actually generating the
    workbook -- mirroring the review step the Excel import path
    already has.

    Also reports biometric_mismatch_count separately.
    IMPORTANT: this is advisory only, by design (see
    biometric_manager.py) -- it never appears in pending_categories
    and never affects "ready", so it can never block closing
    generation the way the other 5 categories can. The frontend
    should still surface it as a review screen in the same
    post-click flow, just not as a required popup.

    Does not block or auto-generate anything itself; it only reports.
    Categories with existing rows are treated as already answered
    (e.g. "no outsource work this week" should be recorded as zero
    rows only after the popup was shown and answered "No" -- an
    empty category the accountant hasn't been asked about yet looks
    the same as one that they answered "None", by design; the
    frontend only needs to ask once per week).
    """

    connection = connect_database()

    try:

        cursor = connection.cursor()

        cursor.execute("SELECT id FROM weeks WHERE id = ?", (week_id,))
        if cursor.fetchone() is None:
            raise WeekNotFoundError(week_id)

        pending = []

        for category, table in MANUAL_INPUT_CATEGORIES:

            cursor.execute(
                f"SELECT COUNT(*) FROM {table} WHERE week_id = ?",
                (week_id,),
            )

            count = cursor.fetchone()[0]

            if count == 0:
                pending.append(category)

        mismatches = get_attendance_mismatches(connection, week_id)

        return {
            "week_id": week_id,
            "ready": len(pending) == 0,
            "pending_categories": pending,
            "biometric_mismatch_count": len(mismatches),
        }

    finally:

        connection.close()


def get_weekly_salary(week_id: int) -> dict[str, Any]:
    """
    Get salary information for an existing week.

    Delegates salary calculation to the existing salary engine.
    No salary logic is duplicated here.
    """

    result = calculate_weekly_salary(week_id)

    if result is None:
        raise WeekNotFoundError(week_id)

    return result


def get_all_weeks(connection) -> list[dict[str, Any]]:
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT id, week_start, week_end, closing_generated, created_at
        FROM weeks
        ORDER BY week_start DESC
        """
    )
    results = []
    for row in cursor.fetchall():
        results.append({
            "id": row[0],
            "label": f"Week {row[0]}",
            "week_start": row[1],
            "week_end": row[2],
            "closing_generated": row[3],
            "created_at": str(row[4]) if row[4] else None,
        })
    return results


def get_week_by_id_service(connection, week_id: int) -> dict[str, Any]:
    try:
        w_id = int(week_id)
    except (ValueError, TypeError):
        raise WeekNotFoundError(week_id)

    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT id, week_start, week_end, closing_generated, created_at
        FROM weeks
        WHERE id = ?
        """,
        (w_id,),
    )
    row = cursor.fetchone()
    if row is None:
        raise WeekNotFoundError(week_id)

    return {
        "id": row[0],
        "label": f"Week {row[0]}",
        "week_start": row[1],
        "week_end": row[2],
        "closing_generated": row[3],
        "created_at": str(row[4]) if row[4] else None,
    }


def create_or_get_week_service(connection, week_start: str, week_end: str) -> dict[str, Any]:
    from datetime import datetime

    w_start = str(week_start).strip()
    w_end = str(week_end).strip()

    try:
        start_dt = datetime.strptime(w_start, "%Y-%m-%d")
        end_dt = datetime.strptime(w_end, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Invalid date format. Use YYYY-MM-DD.")

    if end_dt < start_dt:
        raise ValueError("week_end cannot be before week_start.")

    cursor = connection.cursor()
    cursor.execute(
        "SELECT id, week_start, week_end, closing_generated, created_at FROM weeks WHERE TRIM(week_start) = ? AND TRIM(week_end) = ?",
        (w_start, w_end),
    )
    row = cursor.fetchone()
    if row:
        return {
            "id": row[0],
            "label": f"Week {row[0]}",
            "week_start": row[1],
            "week_end": row[2],
            "closing_generated": row[3],
            "created_at": str(row[4]) if row[4] else None,
        }

    cursor.execute(
        "INSERT INTO weeks (week_start, week_end, closing_generated) VALUES (?, ?, 0)",
        (w_start, w_end),
    )
    connection.commit()
    new_id = cursor.lastrowid

    cursor.execute(
        "SELECT id, week_start, week_end, closing_generated, created_at FROM weeks WHERE id = ?",
        (new_id,),
    )
    row = cursor.fetchone()
    return {
        "id": row[0],
        "label": f"Week {row[0]}",
        "week_start": row[1],
        "week_end": row[2],
        "closing_generated": row[3],
        "created_at": str(row[4]) if row[4] else None,
    }


def update_week_service(connection, week_id: int, week_data) -> dict[str, Any]:
    existing = get_week_by_id_service(connection, week_id)
    actual_id = existing["id"]

    new_start = week_data.week_start.strip() if week_data.week_start else existing["week_start"]
    new_end = week_data.week_end.strip() if week_data.week_end else existing["week_end"]
    new_closing = week_data.closing_generated if week_data.closing_generated is not None else existing["closing_generated"]

    from datetime import datetime
    try:
        start_dt = datetime.strptime(new_start, "%Y-%m-%d")
        end_dt = datetime.strptime(new_end, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Invalid date format. Use YYYY-MM-DD.")

    if end_dt < start_dt:
        raise ValueError("week_end cannot be before week_start.")

    cursor = connection.cursor()
    cursor.execute(
        "SELECT id FROM weeks WHERE TRIM(week_start) = ? AND TRIM(week_end) = ? AND id != ?",
        (new_start, new_end, actual_id),
    )
    if cursor.fetchone():
        from fastapi import HTTPException
        raise HTTPException(
            status_code=409,
            detail=f"Another week with range {new_start} to {new_end} already exists.",
        )

    cursor.execute(
        """
        UPDATE weeks
        SET week_start = ?, week_end = ?, closing_generated = ?
        WHERE id = ?
        """,
        (new_start, new_end, new_closing, actual_id),
    )
    connection.commit()

    return get_week_by_id_service(connection, actual_id)



def generate_weekly_closing(week_id: int) -> dict[str, Any]:
    """
    Calculate salary and generate the Weekly Closing workbook.

    Importing the workbook is intentionally NOT done here because
    the API already receives an existing week_id.
    """

    salary_result = calculate_weekly_salary(week_id)

    if salary_result is None:
        raise WeekNotFoundError(week_id)

    file_path = build_weekly_closing_workbook(
        week_id=week_id,
        template=WEEKLY_CLOSING_TEMPLATE,
    )

    total_salary = salary_result["total_salary"]
    total_contractor_commission = (
        salary_result["total_contractor_commission"]
    )
    total_factory_expense = salary_result["total_factory_expense"]

    grand_total = (
        total_salary
        + total_contractor_commission
        + total_factory_expense
    )

    return {
        "week_id": week_id,
        "employees_count": len(
            salary_result["employees"]
        ),
        "total_salary": total_salary,
        "total_contractor_commission": total_contractor_commission,
        "total_factory_expense": total_factory_expense,
        "grand_total": grand_total,
        "file_path": str(file_path),
    }