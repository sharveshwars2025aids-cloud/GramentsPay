"""
router.py

Controlled Intent Router for GarmentsPay AI query layer.
Dispatches validated intents and resolved entities to existing, verified backend logic.
DOES NOT calculate salaries independently or execute arbitrary SQL.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Tuple

from ai.schemas import IntentNames, StructuredInterpretation
from ai.resolver import (
    resolve_employee,
    resolve_week,
    resolve_department,
    parse_date_string,
    EmployeeNotFoundError,
    AmbiguousEmployeeError,
    WeekResolutionError,
)
from salary_engine import calculate_weekly_salary
from api.services.report_service import (
    get_expenses_report,
    get_outsource_report,
    get_security_report,
    get_department_summary_report,
)
from api.services.dashboard_service import (
    get_production_analytics,
    get_salary_analytics,
    get_expense_analytics,
    get_week_dashboard,
)


def route_query(
    connection: sqlite3.Connection,
    interpretation: StructuredInterpretation,
) -> Tuple[dict[str, Any], str]:
    """
    Routes structured interpretation to verified backend services.
    Returns:
        (data_dict, fallback_natural_response)
    """
    intent = interpretation.intent

    # 1. EMPLOYEE_SALARY
    if intent == IntentNames.EMPLOYEE_SALARY:
        if not interpretation.employee:
            raise EmployeeNotFoundError("the requested employee")

        emp = resolve_employee(connection, interpretation.employee)
        week = resolve_week(connection, interpretation.week, employee_id=emp["id"])
        salary_result = calculate_weekly_salary(week["id"])

        emp_salary = None
        if salary_result and "employees" in salary_result:
            emp_salary = salary_result["employees"].get(emp["id"])

        if not emp_salary:
            data = {
                "employee_id": emp["id"],
                "employee_code": emp["employee_code"],
                "employee_name": emp["name"],
                "week_id": week["id"],
                "week_start": week["week_start"],
                "week_end": week["week_end"],
                "piece_salary": 0.0,
                "shift_salary": 0.0,
                "gross_salary": 0.0,
                "bonus": 0.0,
                "deduction": 0.0,
                "net_salary": 0.0,
                "has_records": False,
            }
            msg = f"{emp['name']} ({emp['employee_code']}) has no recorded salary data for Week {week['id']} ({week['week_start']} to {week['week_end']})."
            return data, msg

        data = {
            "employee_id": emp["id"],
            "employee_code": emp["employee_code"],
            "employee_name": emp["name"],
            "week_id": week["id"],
            "week_start": week["week_start"],
            "week_end": week["week_end"],
            "pay_type": emp_salary.get("pay_type", emp["pay_type"]),
            "piece_salary": float(emp_salary.get("piece_salary", 0.0)),
            "shift_salary": float(emp_salary.get("shift_salary", 0.0)),
            "gross_salary": float(emp_salary.get("gross_salary", 0.0)),
            "bonus": float(emp_salary.get("bonus", 0.0)),
            "deduction": float(emp_salary.get("deduction", 0.0)),
            "net_salary": float(emp_salary.get("net_salary", 0.0)),
            "total_shifts": float(emp_salary.get("total_shifts", 0.0)),
            "has_records": True,
        }
        breakdown_parts = []
        if data["shift_salary"] > 0:
            breakdown_parts.append(f"₹{data['shift_salary']:,.2f} shift salary")
        if data["piece_salary"] > 0:
            breakdown_parts.append(f"₹{data['piece_salary']:,.2f} piece salary")
        if data["bonus"] > 0:
            breakdown_parts.append(f"₹{data['bonus']:,.2f} bonus")
        if data["deduction"] > 0:
            breakdown_parts.append(f"₹{data['deduction']:,.2f} deduction")

        detail = f", including {', '.join(breakdown_parts)}" if breakdown_parts else ""
        msg = f"{emp['name']}'s salary for Week {week['id']} ({week['week_start']} to {week['week_end']}) is ₹{data['net_salary']:,.2f}{detail}."
        return data, msg

    # 2. EMPLOYEE_PRODUCTION
    if intent == IntentNames.EMPLOYEE_PRODUCTION:
        if not interpretation.employee:
            raise EmployeeNotFoundError("the requested employee")

        emp = resolve_employee(connection, interpretation.employee)
        target_date = parse_date_string(interpretation.date) if interpretation.date else None
        cursor = connection.cursor()

        if target_date:
            cursor.execute(
                """
                SELECT
                    pr.work_date,
                    s.style_no,
                    COALESCE(o.operation_name, 'UNSPECIFIED'),
                    pr.total_qty,
                    pr.rate,
                    pr.total_amount
                FROM production_records pr
                JOIN styles s ON pr.style_id = s.id
                LEFT JOIN operations o ON pr.operation_id = o.id
                WHERE pr.employee_id = ? AND pr.work_date = ?
                ORDER BY pr.id ASC
                """,
                (emp["id"], target_date),
            )
            rows = cursor.fetchall()
            date_label = target_date
        else:
            week = resolve_week(connection, interpretation.week, employee_id=emp["id"])
            cursor.execute(
                """
                SELECT
                    pr.work_date,
                    s.style_no,
                    COALESCE(o.operation_name, 'UNSPECIFIED'),
                    pr.total_qty,
                    pr.rate,
                    pr.total_amount
                FROM production_records pr
                JOIN styles s ON pr.style_id = s.id
                LEFT JOIN operations o ON pr.operation_id = o.id
                WHERE pr.employee_id = ? AND pr.week_id = ?
                ORDER BY pr.work_date ASC, pr.id ASC
                """,
                (emp["id"], week["id"]),
            )
            rows = cursor.fetchall()
            date_label = f"Week {week['id']} ({week['week_start']} to {week['week_end']})"

        items = [
            {
                "date": str(r[0]),
                "style": r[1],
                "operation": r[2],
                "qty": float(r[3]),
                "rate": float(r[4]),
                "amount": float(r[5]),
            }
            for r in rows
        ]
        total_qty = sum(i["qty"] for i in items)
        total_amt = sum(i["amount"] for i in items)

        data = {
            "employee_id": emp["id"],
            "employee_code": emp["employee_code"],
            "employee_name": emp["name"],
            "period": date_label,
            "total_qty": total_qty,
            "total_amount": total_amt,
            "items": items,
        }

        if total_qty > 0:
            msg = f"{emp['name']} ({emp['employee_code']}) produced {total_qty:,.0f} pieces totaling ₹{total_amt:,.2f} on {date_label}."
        else:
            msg = f"{emp['name']} ({emp['employee_code']}) has no recorded production on {date_label}."
        return data, msg

    # 3. EMPLOYEE_WORK_HISTORY
    if intent == IntentNames.EMPLOYEE_WORK_HISTORY:
        if not interpretation.employee:
            raise EmployeeNotFoundError("the requested employee")

        emp = resolve_employee(connection, interpretation.employee)
        cursor = connection.cursor()

        # Production history
        cursor.execute(
            """
            SELECT pr.work_date, s.style_no, pr.total_qty, pr.total_amount
            FROM production_records pr
            JOIN styles s ON pr.style_id = s.id
            WHERE pr.employee_id = ?
            ORDER BY pr.work_date DESC LIMIT 10
            """,
            (emp["id"],),
        )
        prod_rows = cursor.fetchall()

        # Shift history
        cursor.execute(
            """
            SELECT work_date, shifts, shift_rate, daily_salary
            FROM shift_records
            WHERE employee_id = ?
            ORDER BY work_date DESC LIMIT 10
            """,
            (emp["id"],),
        )
        shift_rows = cursor.fetchall()

        # Lifetime totals
        cursor.execute(
            "SELECT COALESCE(SUM(total_qty), 0), COALESCE(SUM(total_amount), 0) FROM production_records WHERE employee_id = ?",
            (emp["id"],),
        )
        p_tot = cursor.fetchone()
        cursor.execute(
            "SELECT COALESCE(SUM(shifts), 0), COALESCE(SUM(daily_salary), 0) FROM shift_records WHERE employee_id = ?",
            (emp["id"],),
        )
        s_tot = cursor.fetchone()

        data = {
            "employee_id": emp["id"],
            "employee_code": emp["employee_code"],
            "employee_name": emp["name"],
            "pay_type": emp["pay_type"],
            "total_pieces_produced": float(p_tot[0]),
            "total_piece_earnings": float(p_tot[1]),
            "total_shifts_worked": float(s_tot[0]),
            "total_shift_earnings": float(s_tot[1]),
            "recent_production": [
                {"date": str(r[0]), "style": r[1], "qty": float(r[2]), "amount": float(r[3])}
                for r in prod_rows
            ],
            "recent_shifts": [
                {"date": str(r[0]), "shifts": float(r[1]), "rate": float(r[2]), "salary": float(r[3])}
                for r in shift_rows
            ],
        }

        total_earnings = data["total_piece_earnings"] + data["total_shift_earnings"]
        msg = (
            f"Work history for {emp['name']} ({emp['employee_code']}, {emp['pay_type']}): "
            f"{data['total_pieces_produced']:,.0f} pieces produced, {data['total_shifts_worked']:,.1f} shifts worked, "
            f"totaling ₹{total_earnings:,.2f} recorded earnings."
        )
        return data, msg

    # 4. EMPLOYEE_DEDUCTION
    if intent == IntentNames.EMPLOYEE_DEDUCTION:
        if not interpretation.employee:
            raise EmployeeNotFoundError("the requested employee")

        emp = resolve_employee(connection, interpretation.employee)
        cursor = connection.cursor()

        if interpretation.week:
            week = resolve_week(connection, interpretation.week, employee_id=emp["id"])
            cursor.execute(
                """
                SELECT deduction_type, amount, notes, week_id
                FROM deductions
                WHERE employee_id = ? AND week_id = ?
                """,
                (emp["id"], week["id"]),
            )
            period_label = f"Week {week['id']}"
        else:
            cursor.execute(
                """
                SELECT deduction_type, amount, notes, week_id
                FROM deductions
                WHERE employee_id = ?
                ORDER BY id DESC LIMIT 10
                """,
                (emp["id"],),
            )
            period_label = "all recorded weeks"

        rows = cursor.fetchall()
        items = [
            {"type": r[0], "amount": float(r[1]), "notes": r[2] or "", "week_id": r[3]}
            for r in rows
        ]
        total_deduction = sum(i["amount"] for i in items)

        data = {
            "employee_id": emp["id"],
            "employee_code": emp["employee_code"],
            "employee_name": emp["name"],
            "period": period_label,
            "total_deduction": total_deduction,
            "deductions": items,
        }

        if total_deduction > 0:
            types_str = ", ".join(f"₹{i['amount']:,.2f} for {i['type']}" for i in items)
            msg = f"{emp['name']} has total deductions of ₹{total_deduction:,.2f} ({types_str}) in {period_label}."
        else:
            msg = f"{emp['name']} has no recorded deductions in {period_label}."
        return data, msg

    # 5. EMPLOYEE_BONUS
    if intent == IntentNames.EMPLOYEE_BONUS:
        if not interpretation.employee:
            raise EmployeeNotFoundError("the requested employee")

        emp = resolve_employee(connection, interpretation.employee)
        cursor = connection.cursor()

        if interpretation.week:
            week = resolve_week(connection, interpretation.week, employee_id=emp["id"])
            cursor.execute(
                """
                SELECT bonus_type, amount, notes, week_id
                FROM bonuses
                WHERE employee_id = ? AND week_id = ?
                """,
                (emp["id"], week["id"]),
            )
            period_label = f"Week {week['id']}"
        else:
            cursor.execute(
                """
                SELECT bonus_type, amount, notes, week_id
                FROM bonuses
                WHERE employee_id = ?
                ORDER BY id DESC LIMIT 10
                """,
                (emp["id"],),
            )
            period_label = "all recorded weeks"

        rows = cursor.fetchall()
        items = [
            {"type": r[0], "amount": float(r[1]), "notes": r[2] or "", "week_id": r[3]}
            for r in rows
        ]
        total_bonus = sum(i["amount"] for i in items)

        data = {
            "employee_id": emp["id"],
            "employee_code": emp["employee_code"],
            "employee_name": emp["name"],
            "period": period_label,
            "total_bonus": total_bonus,
            "bonuses": items,
        }

        if total_bonus > 0:
            types_str = ", ".join(f"₹{i['amount']:,.2f} for {i['type']}" for i in items)
            msg = f"{emp['name']} received a total bonus of ₹{total_bonus:,.2f} ({types_str}) in {period_label}."
        else:
            msg = f"{emp['name']} did not receive any bonuses in {period_label}."
        return data, msg

    # 6. WEEKLY_EXPENSE
    if intent == IntentNames.WEEKLY_EXPENSE:
        week = resolve_week(connection, interpretation.week)
        expenses_report = get_expenses_report(week["id"])
        analytics = get_expense_analytics(connection, week["id"])

        total_expense = float(analytics.get("total_factory_expenses", analytics.get("factory_expenses_total", 0.0)))
        by_category = analytics.get("factory_by_category", {})

        data = {
            "week_id": week["id"],
            "week_start": week["week_start"],
            "week_end": week["week_end"],
            "factory_expenses_total": total_expense,
            "by_category": by_category,
            "outsourcing_total": float(analytics.get("outsourcing_total", 0.0)),
            "security_total": float(analytics.get("security_total", 0.0)),
        }

        cat_breakdown = ", ".join(f"{c}: ₹{v:,.2f}" for c, v in by_category.items())
        detail = f" Breakdown: {cat_breakdown}." if cat_breakdown else ""
        msg = f"Factory expenses for Week {week['id']} ({week['week_start']} to {week['week_end']}) total ₹{total_expense:,.2f}.{detail}"
        return data, msg

    # 7. WEEKLY_OUTSOURCING
    if intent == IntentNames.WEEKLY_OUTSOURCING:
        week = resolve_week(connection, interpretation.week)
        outsource_items = get_outsource_report(week["id"])
        total_amount = sum(float(item.get("amount", 0.0)) for item in outsource_items)

        data = {
            "week_id": week["id"],
            "week_start": week["week_start"],
            "week_end": week["week_end"],
            "total_amount": total_amount,
            "item_count": len(outsource_items),
            "items": outsource_items,
        }

        if total_amount > 0:
            msg = f"Outsourced work for Week {week['id']} totals ₹{total_amount:,.2f} across {len(outsource_items)} items."
        else:
            msg = f"No outsourced work was recorded for Week {week['id']} ({week['week_start']} to {week['week_end']})."
        return data, msg

    # 8. WEEKLY_SECURITY
    if intent == IntentNames.WEEKLY_SECURITY:
        week = resolve_week(connection, interpretation.week)
        sec_items = get_security_report(week["id"])
        total_amount = sum(float(item.get("amount", 0.0)) for item in sec_items)

        data = {
            "week_id": week["id"],
            "week_start": week["week_start"],
            "week_end": week["week_end"],
            "total_amount": total_amount,
            "items": sec_items,
        }

        if total_amount > 0:
            msg = f"Security payments for Week {week['id']} total ₹{total_amount:,.2f}."
        else:
            msg = f"No security payments were recorded for Week {week['id']} ({week['week_start']} to {week['week_end']})."
        return data, msg

    # 9. DEPARTMENT_SUMMARY
    if intent == IntentNames.DEPARTMENT_SUMMARY:
        week = resolve_week(connection, interpretation.week)
        dept = resolve_department(connection, interpretation.department) if interpretation.department else None
        prod_analytics = get_production_analytics(connection, week["id"])
        sal_analytics = get_salary_analytics(connection, week["id"])

        dept_items = prod_analytics.get("by_department", {}).get("items", [])
        sal_dept_items = sal_analytics.get("department_breakdown", {}).get("items", [])

        if dept:
            target_name = dept["name"].upper()
            filtered_prod = [d for d in dept_items if d["department"].upper() == target_name]
            filtered_sal = [d for d in sal_dept_items if d["department"].upper() == target_name]
            qty = filtered_prod[0]["quantity"] if filtered_prod else 0.0
            amt = filtered_prod[0]["amount"] if filtered_prod else 0.0
            sal = filtered_sal[0]["amount"] if filtered_sal else 0.0

            data = {
                "week_id": week["id"],
                "department": dept["name"],
                "quantity": qty,
                "production_amount": amt,
                "salary_amount": sal,
            }
            msg = (
                f"{dept['name']} Department for Week {week['id']}: "
                f"{qty:,.0f} pieces produced (value: ₹{amt:,.2f}), salary: ₹{sal:,.2f}."
            )
            return data, msg

        data = {
            "week_id": week["id"],
            "departments": dept_items,
            "salary_by_department": sal_dept_items,
        }
        dept_str = ", ".join(f"{d['department']}: {d['quantity']:,.0f} pcs (₹{d['amount']:,.2f})" for d in dept_items)
        msg = f"Department summary for Week {week['id']}: {dept_str or 'No department production recorded.'}"
        return data, msg

    # 10. PRODUCTION_SUMMARY
    if intent == IntentNames.PRODUCTION_SUMMARY:
        week = resolve_week(connection, interpretation.week)
        prod = get_production_analytics(connection, week["id"])

        data = {
            "week_id": week["id"],
            "week_start": week["week_start"],
            "week_end": week["week_end"],
            "total_quantity": prod.get("total_quantity", 0.0),
            "total_amount": prod.get("total_amount", 0.0),
            "active_workers": prod.get("active_workers", 0),
            "distinct_styles": prod.get("distinct_styles", 0),
        }

        msg = (
            f"Production summary for Week {week['id']} ({week['week_start']} to {week['week_end']}): "
            f"{data['total_quantity']:,.0f} pieces completed across {data['distinct_styles']} styles "
            f"by {data['active_workers']} active workers, totaling ₹{data['total_amount']:,.2f}."
        )
        return data, msg

    # 11. SALARY_SUMMARY
    if intent == IntentNames.SALARY_SUMMARY:
        week = resolve_week(connection, interpretation.week)
        sal = get_salary_analytics(connection, week["id"])

        data = {
            "week_id": week["id"],
            "week_start": week["week_start"],
            "week_end": week["week_end"],
            "net_salary": sal.get("total_net_salary", sal.get("net_salary", 0.0)),
            "gross_salary": sal.get("total_gross_salary", sal.get("gross_salary", 0.0)),
            "piece_salary": sal.get("piece_salary", 0.0),
            "shift_salary": sal.get("shift_salary", 0.0),
            "bonuses": sal.get("bonuses", 0.0),
            "deductions": sal.get("deductions", 0.0),
            "contractor_commission": sal.get("contractor_commission", 0.0),
            "active_workers": sal.get("active_workers", 0),
        }

        msg = (
            f"Salary summary for Week {week['id']} ({week['week_start']} to {week['week_end']}): "
            f"Total net salary is ₹{data['net_salary']:,.2f} across {data['active_workers']} workers "
            f"(Piece: ₹{data['piece_salary']:,.2f}, Shift: ₹{data['shift_salary']:,.2f}, "
            f"Bonus: ₹{data['bonuses']:,.2f}, Deduction: ₹{data['deductions']:,.2f}, Commission: ₹{data['contractor_commission']:,.2f})."
        )
        return data, msg

    # 12. WEEK_COMPARISON
    if intent == IntentNames.WEEK_COMPARISON:
        week1 = resolve_week(connection, interpretation.week or "current")
        week2 = resolve_week(connection, interpretation.compare_week or "last week")

        dash1 = get_week_dashboard(week1["id"])
        dash2 = get_week_dashboard(week2["id"])

        p1 = dash1["production"]["total_quantity"]
        p2 = dash2["production"]["total_quantity"]
        s1 = dash1["salary"].get("total_net_salary", dash1["salary"].get("net_salary", 0.0))
        s2 = dash2["salary"].get("total_net_salary", dash2["salary"].get("net_salary", 0.0))
        e1 = dash1["expenses"].get("total_factory_expenses", dash1["expenses"].get("factory_expenses_total", 0.0))
        e2 = dash2["expenses"].get("total_factory_expenses", dash2["expenses"].get("factory_expenses_total", 0.0))
        tot1 = dash1["weekly_financials"].get("total_weekly_cost", dash1["weekly_financials"].get("total_factory_cost", 0.0))
        tot2 = dash2["weekly_financials"].get("total_weekly_cost", dash2["weekly_financials"].get("total_factory_cost", 0.0))

        data = {
            "week_1": {
                "id": week1["id"],
                "start": week1["week_start"],
                "end": week1["week_end"],
                "production_qty": p1,
                "net_salary": s1,
                "factory_expenses": e1,
                "total_factory_cost": tot1,
            },
            "week_2": {
                "id": week2["id"],
                "start": week2["week_start"],
                "end": week2["week_end"],
                "production_qty": p2,
                "net_salary": s2,
                "factory_expenses": e2,
                "total_factory_cost": tot2,
            },
            "comparison": {
                "production_qty_diff": p1 - p2,
                "net_salary_diff": s1 - s2,
                "expenses_diff": e1 - e2,
                "total_cost_diff": tot1 - tot2,
            },
        }

        diff_cost = data["comparison"]["total_cost_diff"]
        diff_prod = data["comparison"]["production_qty_diff"]
        cost_dir = "higher" if diff_cost >= 0 else "lower"
        prod_dir = "higher" if diff_prod >= 0 else "lower"

        msg = (
            f"Comparing Week {week1['id']} vs Week {week2['id']}: "
            f"Total factory cost was ₹{tot1:,.2f} vs ₹{tot2:,.2f} (₹{abs(diff_cost):,.2f} {cost_dir}). "
            f"Production was {p1:,.0f} pcs vs {p2:,.0f} pcs ({abs(diff_prod):,.0f} pcs {prod_dir}). "
            f"Payroll was ₹{s1:,.2f} vs ₹{s2:,.2f}."
        )
        return data, msg

    # Fallback
    return {}, "I am not able to answer this question. Please ask about salaries, production, work history, deductions, bonuses, expenses, outsourcing, security payments, department summaries, production summaries, salary summaries, or week comparisons."
