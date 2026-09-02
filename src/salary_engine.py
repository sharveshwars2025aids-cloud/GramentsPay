from database import connect_database

from salary_queries import (
    get_piece_workers,
    get_shift_workers,
    get_employee_bonuses,
    get_employee_deductions,
    get_factory_expenses,
    get_shift_contractor_salary,
)


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


def get_valid_week_id():

    while True:

        try:
            return int(input("Week ID: "))

        except ValueError:
            print("Invalid Week ID.")


def calculate_weekly_salary(week_id):
    
    connection = connect_database()

    try:

        if not week_exists(connection, week_id):
            return None

        piece_workers = get_piece_workers(
            connection,
            week_id,
        )

        shift_workers = get_shift_workers(
            connection,
            week_id,
        )

        bonuses = get_employee_bonuses(
            connection,
            week_id,
        )

        deductions = get_employee_deductions(
            connection,
            week_id,
        )

        contractors = get_shift_contractor_salary(
            connection,
            week_id,
        )

        expenses = get_factory_expenses(
            connection,
            week_id,
        )

        salary_data = {}

        # 1. Piece workers
        for emp_id, emp_code, emp_name, pay_type, prod_salary in piece_workers:
            p_sal = float(prod_salary or 0)
            salary_data[emp_id] = {
                "employee_id": emp_id,
                "employee_code": emp_code or str(emp_id),
                "employee_name": emp_name,
                "pay_type": pay_type or "PIECE",
                "piece_salary": p_sal,
                "shift_salary": 0.0,
                "gross_salary": p_sal,
                "bonus": 0.0,
                "deduction": 0.0,
                "net_salary": 0.0,
            }

        # 2. Shift workers
        for emp_id, emp_code, emp_name, pay_type, total_shifts, shift_sal in shift_workers:
            s_sal = float(shift_sal or 0)
            if emp_id in salary_data:
                salary_data[emp_id]["shift_salary"] = s_sal
                salary_data[emp_id]["gross_salary"] += s_sal
                salary_data[emp_id]["total_shifts"] = float(total_shifts or 0)
            else:
                salary_data[emp_id] = {
                    "employee_id": emp_id,
                    "employee_code": emp_code or str(emp_id),
                    "employee_name": emp_name,
                    "pay_type": pay_type or "SHIFT",
                    "piece_salary": 0.0,
                    "shift_salary": s_sal,
                    "total_shifts": float(total_shifts or 0),
                    "gross_salary": s_sal,
                    "bonus": 0.0,
                    "deduction": 0.0,
                    "net_salary": 0.0,
                }

        # 3. Bonuses
        for emp_id, emp_code, emp_name, pay_type, amount in bonuses:
            b_val = float(amount or 0)
            if emp_id in salary_data:
                salary_data[emp_id]["bonus"] = b_val
            else:
                salary_data[emp_id] = {
                    "employee_id": emp_id,
                    "employee_code": emp_code or str(emp_id),
                    "employee_name": emp_name,
                    "pay_type": pay_type or "PIECE",
                    "piece_salary": 0.0,
                    "shift_salary": 0.0,
                    "gross_salary": 0.0,
                    "bonus": b_val,
                    "deduction": 0.0,
                    "net_salary": 0.0,
                }

        # 4. Deductions
        for emp_id, emp_code, emp_name, pay_type, amount in deductions:
            d_val = float(amount or 0)
            if emp_id in salary_data:
                salary_data[emp_id]["deduction"] = d_val
            else:
                salary_data[emp_id] = {
                    "employee_id": emp_id,
                    "employee_code": emp_code or str(emp_id),
                    "employee_name": emp_name,
                    "pay_type": pay_type or "PIECE",
                    "piece_salary": 0.0,
                    "shift_salary": 0.0,
                    "gross_salary": 0.0,
                    "bonus": 0.0,
                    "deduction": d_val,
                    "net_salary": 0.0,
                }

        # 5. Net Salary Calculation
        for employee in salary_data.values():
            employee["net_salary"] = (
                employee["piece_salary"]
                + employee["shift_salary"]
                + employee["bonus"]
                - employee["deduction"]
            )

        total_salary = sum(
            employee["net_salary"]
            for employee in salary_data.values()
        )

        total_bonus = sum(
            employee["bonus"]
            for employee in salary_data.values()
        )

        total_deduction = sum(
            employee["deduction"]
            for employee in salary_data.values()
        )

        total_contractor_commission = sum(
            float(contractor[4] or 0)
            for contractor in contractors
        )

        total_expense = sum(
            float(expense[1] or 0)
            for expense in expenses
        )

        return {
            "week_id": week_id,
            "employees": salary_data,
            "contractors": contractors,
            "expenses": expenses,
            "total_salary": total_salary,
            "total_bonus": total_bonus,
            "total_deduction": total_deduction,
            "total_contractor_commission": total_contractor_commission,
            "total_factory_expense": total_expense,
        }

    except Exception as error:

        print(f"Salary calculation failed: {error}")

        return None

    finally:

        connection.close()



if __name__ == "__main__":
    week_id = get_valid_week_id()
    calculate_weekly_salary(week_id)