"""
dashboard_service.py

Analytics service layer providing clean, chart-ready structured metrics and trends
for the GarmentsPay dashboard.

Data sections:
- Production analytics (totals, department breakdown, operation breakdown, style breakdown, trend)
- Salary analytics (gross, net, piece, shift, bonuses, deductions, department breakdown, distribution, trend)
- Expense analytics (factory expenses, by category, trend, outsourcing, security)
- Weekly financial overview (salary, commission, expenses, outsourcing, security, total cost, breakdown)
- Trend analytics (multi-week historical trajectories)
"""

from typing import Any
import sqlite3
from database import connect_database
from salary_engine import calculate_weekly_salary


class DashboardNotFoundError(Exception):
    """Raised when the requested week does not exist."""
    pass


def _verify_week_exists(connection: sqlite3.Connection, week_id: int) -> dict[str, Any]:
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id, week_start, week_end, closing_generated, created_at FROM weeks WHERE id = ?",
        (week_id,),
    )
    row = cursor.fetchone()
    if row is None:
        raise DashboardNotFoundError(f"Week {week_id} not found.")
    return {
        "id": row[0],
        "week_start": str(row[1]),
        "week_end": str(row[2]),
        "closing_generated": bool(row[3]),
        "created_at": str(row[4]) if row[4] else None,
    }


def get_production_analytics(connection: sqlite3.Connection, week_id: int, limit_trend: int = 8) -> dict[str, Any]:
    """Computes production quantity, amounts, breakdowns by department, operation, and style, plus recent trend."""
    cursor = connection.cursor()

    # Total quantity & amount
    cursor.execute(
        """
        SELECT
            COALESCE(SUM(total_qty), 0.0),
            COALESCE(SUM(total_amount), 0.0),
            COUNT(DISTINCT employee_id),
            COUNT(DISTINCT style_id)
        FROM production_records
        WHERE week_id = ?
        """,
        (week_id,),
    )
    tot_row = cursor.fetchone()
    total_qty = float(tot_row[0] or 0.0)
    total_amt = float(tot_row[1] or 0.0)
    active_workers = int(tot_row[2] or 0)
    distinct_styles = int(tot_row[3] or 0)

    # By Department
    cursor.execute(
        """
        SELECT
            d.name AS department,
            COALESCE(SUM(pr.total_qty), 0.0) AS quantity,
            COALESCE(SUM(pr.total_amount), 0.0) AS amount
        FROM production_records pr
        JOIN employees e ON pr.employee_id = e.id
        JOIN departments d ON e.department_id = d.id
        WHERE pr.week_id = ?
        GROUP BY d.id, d.name
        ORDER BY quantity DESC
        """,
        (week_id,),
    )
    dept_rows = cursor.fetchall()
    dept_labels = [r[0] for r in dept_rows]
    dept_quantities = [float(r[1]) for r in dept_rows]
    dept_amounts = [float(r[2]) for r in dept_rows]
    dept_items = [
        {"department": r[0], "quantity": float(r[1]), "amount": float(r[2])}
        for r in dept_rows
    ]

    # By Operation
    cursor.execute(
        """
        SELECT
            COALESCE(o.operation_name, 'UNSPECIFIED') AS operation,
            COALESCE(SUM(pr.total_qty), 0.0) AS quantity,
            COALESCE(SUM(pr.total_amount), 0.0) AS amount
        FROM production_records pr
        LEFT JOIN operations o ON pr.operation_id = o.id
        WHERE pr.week_id = ?
        GROUP BY COALESCE(o.operation_name, 'UNSPECIFIED')
        ORDER BY quantity DESC
        """,
        (week_id,),
    )
    op_rows = cursor.fetchall()
    op_labels = [r[0] for r in op_rows]
    op_quantities = [float(r[1]) for r in op_rows]
    op_amounts = [float(r[2]) for r in op_rows]
    op_items = [
        {"operation": r[0], "quantity": float(r[1]), "amount": float(r[2])}
        for r in op_rows
    ]

    # By Style
    cursor.execute(
        """
        SELECT
            COALESCE(s.style_no, 'UNSPECIFIED') AS style_no,
            COALESCE(s.style_name, '') AS style_name,
            COALESCE(SUM(pr.total_qty), 0.0) AS quantity,
            COALESCE(SUM(pr.total_amount), 0.0) AS amount
        FROM production_records pr
        LEFT JOIN styles s ON pr.style_id = s.id
        WHERE pr.week_id = ?
        GROUP BY s.id, s.style_no, s.style_name
        ORDER BY quantity DESC
        """,
        (week_id,),
    )
    style_rows = cursor.fetchall()
    style_labels = [r[0] for r in style_rows]
    style_quantities = [float(r[2]) for r in style_rows]
    style_amounts = [float(r[3]) for r in style_rows]
    style_items = [
        {"style_no": r[0], "style_name": r[1], "quantity": float(r[2]), "amount": float(r[3])}
        for r in style_rows
    ]

    # Historical trend up to and including week_id
    cursor.execute(
        """
        SELECT
            w.id,
            w.week_start,
            COALESCE(SUM(pr.total_qty), 0.0) AS quantity,
            COALESCE(SUM(pr.total_amount), 0.0) AS amount
        FROM (
            SELECT id, week_start
            FROM weeks
            WHERE id <= ?
            ORDER BY week_start DESC
            LIMIT ?
        ) w
        LEFT JOIN production_records pr ON w.id = pr.week_id
        GROUP BY w.id, w.week_start
        ORDER BY w.week_start ASC
        """,
        (week_id, limit_trend),
    )
    trend_rows = cursor.fetchall()
    trend_labels = [f"Week {r[0]}" for r in trend_rows]
    trend_dates = [str(r[1]) for r in trend_rows]
    trend_quantities = [float(r[2]) for r in trend_rows]
    trend_amounts = [float(r[3]) for r in trend_rows]

    return {
        "total_quantity": total_qty,
        "total_amount": total_amt,
        "active_workers": active_workers,
        "distinct_styles": distinct_styles,
        "by_department": {
            "labels": dept_labels,
            "quantities": dept_quantities,
            "amounts": dept_amounts,
            "items": dept_items,
        },
        "by_operation": {
            "labels": op_labels,
            "quantities": op_quantities,
            "amounts": op_amounts,
            "items": op_items,
        },
        "by_style": {
            "labels": style_labels,
            "quantities": style_quantities,
            "amounts": style_amounts,
            "items": style_items,
        },
        "trend": {
            "labels": trend_labels,
            "dates": trend_dates,
            "quantities": trend_quantities,
            "amounts": trend_amounts,
        },
    }


def get_salary_analytics(connection: sqlite3.Connection, week_id: int, limit_trend: int = 8) -> dict[str, Any]:
    """Computes salary aggregates, bonuses, deductions, department breakdowns, and trends using the salary engine."""
    salary_res = calculate_weekly_salary(week_id)
    if salary_res is None or not salary_res.get("employees"):
        total_net = 0.0
        total_bonuses = 0.0
        total_deductions = 0.0
        piece_sal = 0.0
        shift_sal = 0.0
        gross_sal = 0.0
        dept_labels = []
        dept_values = []
        dept_items = []
        worker_count = 0
    else:
        total_net = float(salary_res.get("total_salary", 0.0))
        total_bonuses = float(salary_res.get("total_bonus", 0.0))
        total_deductions = float(salary_res.get("total_deduction", 0.0))

        employees = salary_res["employees"]
        worker_count = len(employees)
        piece_sal = sum(float(e.get("piece_salary", 0.0)) for e in employees.values())
        shift_sal = sum(float(e.get("shift_salary", 0.0)) for e in employees.values())
        gross_sal = piece_sal + shift_sal

        # Map employee departments
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT e.id, d.name AS department
            FROM employees e
            LEFT JOIN departments d ON e.department_id = d.id
            """
        )
        emp_dept_map = {r[0]: (r[1] or "GENERAL") for r in cursor.fetchall()}

        dept_acc: dict[str, dict[str, float]] = {}
        for emp_id, emp in employees.items():
            dept = emp_dept_map.get(emp_id, "GENERAL")
            if dept not in dept_acc:
                dept_acc[dept] = {
                    "department": dept,
                    "gross_salary": 0.0,
                    "net_salary": 0.0,
                    "piece_salary": 0.0,
                    "shift_salary": 0.0,
                    "bonus": 0.0,
                    "deduction": 0.0,
                }
            dept_acc[dept]["gross_salary"] += float(emp.get("gross_salary", 0.0))
            dept_acc[dept]["net_salary"] += float(emp.get("net_salary", 0.0))
            dept_acc[dept]["piece_salary"] += float(emp.get("piece_salary", 0.0))
            dept_acc[dept]["shift_salary"] += float(emp.get("shift_salary", 0.0))
            dept_acc[dept]["bonus"] += float(emp.get("bonus", 0.0))
            dept_acc[dept]["deduction"] += float(emp.get("deduction", 0.0))

        sorted_depts = sorted(dept_acc.values(), key=lambda d: d["net_salary"], reverse=True)
        dept_labels = [d["department"] for d in sorted_depts]
        dept_values = [d["net_salary"] for d in sorted_depts]
        dept_items = sorted_depts

    # Component distribution for donut/bar charts
    dist_labels = ["Piece Rate Salary", "Shift Salary", "Bonuses", "Deductions"]
    dist_values = [piece_sal, shift_sal, total_bonuses, total_deductions]

    # Historical salary trend
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT id, week_start
        FROM weeks
        WHERE id <= ?
        ORDER BY week_start DESC
        LIMIT ?
        """,
        (week_id, limit_trend),
    )
    trend_weeks = sorted(cursor.fetchall(), key=lambda x: x[1])

    trend_labels = []
    trend_dates = []
    trend_net_salaries = []
    trend_gross_salaries = []
    for w in trend_weeks:
        w_id = w[0]
        trend_labels.append(f"Week {w_id}")
        trend_dates.append(str(w[1]))
        w_sal = calculate_weekly_salary(w_id)
        if w_sal:
            net = float(w_sal.get("total_salary", 0.0))
            gross = sum(float(e.get("piece_salary", 0.0)) + float(e.get("shift_salary", 0.0)) for e in w_sal.get("employees", {}).values())
            trend_net_salaries.append(net)
            trend_gross_salaries.append(gross)
        else:
            trend_net_salaries.append(0.0)
            trend_gross_salaries.append(0.0)

    return {
        "total_gross_salary": gross_sal,
        "total_net_salary": total_net,
        "piece_salary": piece_sal,
        "shift_salary": shift_sal,
        "total_bonuses": total_bonuses,
        "total_deductions": total_deductions,
        "worker_count": worker_count,
        "by_department": {
            "labels": dept_labels,
            "values": dept_values,
            "items": dept_items,
        },
        "distribution": {
            "labels": dist_labels,
            "values": dist_values,
        },
        "trend": {
            "labels": trend_labels,
            "dates": trend_dates,
            "net_salaries": trend_net_salaries,
            "gross_salaries": trend_gross_salaries,
        },
    }


def get_expense_analytics(connection: sqlite3.Connection, week_id: int, limit_trend: int = 8) -> dict[str, Any]:
    """Computes factory expenses, categories, outsourcing totals, security totals, and trends."""
    cursor = connection.cursor()

    # Factory expenses
    cursor.execute(
        """
        SELECT category, COALESCE(SUM(amount), 0.0) AS amount
        FROM expenses
        WHERE week_id = ?
        GROUP BY category
        ORDER BY amount DESC
        """,
        (week_id,),
    )
    exp_rows = cursor.fetchall()
    exp_labels = [r[0] for r in exp_rows]
    exp_values = [float(r[1]) for r in exp_rows]
    exp_items = [{"category": r[0], "amount": float(r[1])} for r in exp_rows]
    total_factory_expenses = sum(exp_values)

    # Outsourcing total & items
    cursor.execute(
        """
        SELECT
            centre_name,
            COALESCE(SUM(amount), 0.0) AS amount,
            COALESCE(SUM(qty), 0.0) AS total_qty
        FROM outsource_payments
        WHERE week_id = ?
        GROUP BY centre_name
        ORDER BY amount DESC
        """,
        (week_id,),
    )
    outsource_rows = cursor.fetchall()
    outsource_total = sum(float(r[1]) for r in outsource_rows)
    outsource_items = [
        {"centre_name": r[0], "amount": float(r[1]), "quantity": float(r[2])}
        for r in outsource_rows
    ]

    # Security total & items
    cursor.execute(
        """
        SELECT
            e.name,
            COALESCE(SUM(sp.amount), 0.0) AS amount,
            COALESCE(SUM(sp.days), 0) AS days
        FROM security_payments sp
        JOIN employees e ON sp.employee_id = e.id
        WHERE sp.week_id = ?
        GROUP BY e.id, e.name
        ORDER BY amount DESC
        """,
        (week_id,),
    )
    sec_rows = cursor.fetchall()
    security_total = sum(float(r[1]) for r in sec_rows)
    security_items = [
        {"name": r[0], "amount": float(r[1]), "days": int(r[2])}
        for r in sec_rows
    ]

    # Expense trend across recent weeks
    cursor.execute(
        """
        SELECT id, week_start
        FROM weeks
        WHERE id <= ?
        ORDER BY week_start DESC
        LIMIT ?
        """,
        (week_id, limit_trend),
    )
    trend_weeks = sorted(cursor.fetchall(), key=lambda x: x[1])

    trend_labels = []
    trend_dates = []
    trend_factory_exp = []
    trend_outsource = []
    trend_security = []
    trend_total_exp = []

    for w in trend_weeks:
        w_id = w[0]
        trend_labels.append(f"Week {w_id}")
        trend_dates.append(str(w[1]))

        cursor.execute("SELECT COALESCE(SUM(amount), 0.0) FROM expenses WHERE week_id = ?", (w_id,))
        fe = float(cursor.fetchone()[0] or 0.0)

        cursor.execute("SELECT COALESCE(SUM(amount), 0.0) FROM outsource_payments WHERE week_id = ?", (w_id,))
        op = float(cursor.fetchone()[0] or 0.0)

        cursor.execute("SELECT COALESCE(SUM(amount), 0.0) FROM security_payments WHERE week_id = ?", (w_id,))
        sp = float(cursor.fetchone()[0] or 0.0)

        trend_factory_exp.append(fe)
        trend_outsource.append(op)
        trend_security.append(sp)
        trend_total_exp.append(fe + op + sp)

    return {
        "total_factory_expenses": total_factory_expenses,
        "outsourcing_total": outsource_total,
        "security_total": security_total,
        "total_non_payroll_expenses": total_factory_expenses + outsource_total + security_total,
        "by_category": {
            "labels": exp_labels,
            "values": exp_values,
            "items": exp_items,
        },
        "outsourcing_breakdown": {
            "labels": [r["centre_name"] for r in outsource_items],
            "values": [r["amount"] for r in outsource_items],
            "items": outsource_items,
        },
        "security_breakdown": {
            "labels": [r["name"] for r in security_items],
            "values": [r["amount"] for r in security_items],
            "items": security_items,
        },
        "trend": {
            "labels": trend_labels,
            "dates": trend_dates,
            "factory_expenses": trend_factory_exp,
            "outsourcing": trend_outsource,
            "security": trend_security,
            "total_expenses": trend_total_exp,
        },
    }


def get_weekly_financial_overview(
    connection: sqlite3.Connection,
    week_id: int,
    salary_data: dict[str, Any],
    expense_data: dict[str, Any],
) -> dict[str, Any]:
    """Consolidates complete weekly financial overview and cost breakdown chart data."""
    salary_res = calculate_weekly_salary(week_id)

    emp_sal_total = float(salary_data.get("total_net_salary", 0.0))
    comm_total = float(salary_res.get("total_contractor_commission", 0.0)) if salary_res else 0.0
    fac_exp_total = float(expense_data.get("total_factory_expenses", 0.0))
    outsource_total = float(expense_data.get("outsourcing_total", 0.0))
    sec_total = float(expense_data.get("security_total", 0.0))

    total_cost = emp_sal_total + comm_total + fac_exp_total + outsource_total + sec_total
    total_bonuses = float(salary_data.get("total_bonuses", 0.0))
    total_deductions = float(salary_data.get("total_deductions", 0.0))

    cost_labels = [
        "Employee Salaries",
        "Contractor Commissions",
        "Factory Expenses",
        "Outsourcing",
        "Security",
    ]
    cost_values = [
        emp_sal_total,
        comm_total,
        fac_exp_total,
        outsource_total,
        sec_total,
    ]

    return {
        "employee_salary_total": emp_sal_total,
        "contractor_commission_total": comm_total,
        "factory_expense_total": fac_exp_total,
        "outsourcing_total": outsource_total,
        "security_total": sec_total,
        "total_bonuses": total_bonuses,
        "total_deductions": total_deductions,
        "total_weekly_cost": total_cost,
        "cost_breakdown": {
            "labels": cost_labels,
            "values": cost_values,
        },
    }


def get_week_dashboard(week_id: int) -> dict[str, Any]:
    """Primary dashboard entrypoint providing full chart-ready analytics for a single week."""
    connection = connect_database()
    try:
        week_info = _verify_week_exists(connection, week_id)
        prod = get_production_analytics(connection, week_id)
        sal = get_salary_analytics(connection, week_id)
        exp = get_expense_analytics(connection, week_id)
        financials = get_weekly_financial_overview(connection, week_id, sal, exp)

        return {
            "week_id": week_id,
            "week_start": week_info["week_start"],
            "week_end": week_info["week_end"],
            "closing_generated": week_info["closing_generated"],
            "production": prod,
            "salary": sal,
            "expenses": exp,
            "outsourcing": {
                "total_amount": exp["outsourcing_total"],
                "by_centre": exp["outsourcing_breakdown"]["items"],
            },
            "security": {
                "total_amount": exp["security_total"],
                "items": exp["security_breakdown"]["items"],
            },
            "weekly_financials": financials,
        }
    finally:
        connection.close()


def get_multi_week_trends(limit: int = 10) -> dict[str, Any]:
    """Returns multi-week comparative trajectories for production, payroll, expenses, and total factory cost."""
    connection = connect_database()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT id, week_start, week_end
            FROM weeks
            ORDER BY week_start ASC
            """
        )
        all_weeks = cursor.fetchall()
        if limit and len(all_weeks) > limit:
            all_weeks = all_weeks[-limit:]

        labels = []
        dates = []
        production_quantities = []
        production_amounts = []
        net_salaries = []
        gross_salaries = []
        factory_expenses = []
        outsourcing_amounts = []
        security_amounts = []
        total_costs = []

        for w in all_weeks:
            w_id = w[0]
            labels.append(f"Week {w_id}")
            dates.append(str(w[1]))

            # Production
            cursor.execute(
                "SELECT COALESCE(SUM(total_qty), 0.0), COALESCE(SUM(total_amount), 0.0) FROM production_records WHERE week_id = ?",
                (w_id,),
            )
            p_row = cursor.fetchone()
            pq = float(p_row[0] or 0.0)
            pa = float(p_row[1] or 0.0)
            production_quantities.append(pq)
            production_amounts.append(pa)

            # Salary
            s_res = calculate_weekly_salary(w_id)
            if s_res:
                net_sal = float(s_res.get("total_salary", 0.0))
                comm = float(s_res.get("total_contractor_commission", 0.0))
                gross = sum(float(e.get("piece_salary", 0.0)) + float(e.get("shift_salary", 0.0)) for e in s_res.get("employees", {}).values())
            else:
                net_sal = 0.0
                comm = 0.0
                gross = 0.0
            net_salaries.append(net_sal)
            gross_salaries.append(gross)

            # Expenses
            cursor.execute("SELECT COALESCE(SUM(amount), 0.0) FROM expenses WHERE week_id = ?", (w_id,))
            fe = float(cursor.fetchone()[0] or 0.0)
            cursor.execute("SELECT COALESCE(SUM(amount), 0.0) FROM outsource_payments WHERE week_id = ?", (w_id,))
            op = float(cursor.fetchone()[0] or 0.0)
            cursor.execute("SELECT COALESCE(SUM(amount), 0.0) FROM security_payments WHERE week_id = ?", (w_id,))
            sp = float(cursor.fetchone()[0] or 0.0)

            factory_expenses.append(fe)
            outsourcing_amounts.append(op)
            security_amounts.append(sp)

            total_costs.append(net_sal + comm + fe + op + sp)

        return {
            "labels": labels,
            "dates": dates,
            "production": {
                "quantities": production_quantities,
                "amounts": production_amounts,
            },
            "salary": {
                "net_salaries": net_salaries,
                "gross_salaries": gross_salaries,
            },
            "expenses": {
                "factory_expenses": factory_expenses,
                "outsourcing": outsourcing_amounts,
                "security": security_amounts,
            },
            "total_costs": total_costs,
        }
    finally:
        connection.close()
