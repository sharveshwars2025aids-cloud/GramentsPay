import sys
from pathlib import Path
import pytest

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fastapi.testclient import TestClient
import database
from salary_engine import calculate_weekly_salary
from api.main import app

client = TestClient(app)


def setup_test_week():
    conn = database.connect_database()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM weeks LIMIT 1")
    row = cursor.fetchone()
    if row:
        conn.close()
        return row[0]

    cursor.execute("INSERT INTO weeks (week_start, week_end) VALUES ('2026-07-06', '2026-07-12')")
    week_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return week_id


def test_test_a_piece_rate_employee():
    # TEST A — PIECE-RATE EMPLOYEE (qty = 100, rate = 5 -> 500)
    week_id = setup_test_week()
    conn = database.connect_database()
    cursor = conn.cursor()

    # Get or create piece employee
    cursor.execute("SELECT id FROM employees WHERE pay_type = 'PIECE' LIMIT 1")
    emp_row = cursor.fetchone()
    if not emp_row:
        cursor.execute("INSERT INTO employees (employee_code, name, pay_type) VALUES ('E_P1', 'Piece Worker 1', 'PIECE')")
        emp_id = cursor.lastrowid
    else:
        emp_id = emp_row[0]

    cursor.execute("SELECT id FROM styles LIMIT 1")
    style_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM operations LIMIT 1")
    op_id = cursor.fetchone()[0]

    # Clean previous production for test employee in this week
    cursor.execute("DELETE FROM production_sizes WHERE production_record_id IN (SELECT id FROM production_records WHERE week_id = ? AND employee_id = ?)", (week_id, emp_id))
    cursor.execute("DELETE FROM production_records WHERE week_id = ? AND employee_id = ?", (week_id, emp_id))
    cursor.execute(
        """
        INSERT INTO production_records (week_id, work_date, employee_id, style_id, operation_id, total_qty, rate, total_amount)
        VALUES (?, '2026-07-06', ?, ?, ?, 100.0, 5.0, 500.0)
        """,
        (week_id, emp_id, style_id, op_id)
    )

    conn.commit()
    conn.close()

    result = calculate_weekly_salary(week_id)
    assert result is not None
    emp_data = result["employees"][emp_id]
    assert emp_data["piece_salary"] == 500.0


def test_test_b_shift_employee():
    # TEST B — SHIFT EMPLOYEE (shifts = 1.5, shift_rate = 500 -> 750)
    week_id = setup_test_week()
    conn = database.connect_database()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM employees WHERE pay_type = 'SHIFT' LIMIT 1")
    emp_row = cursor.fetchone()
    if not emp_row:
        cursor.execute("INSERT INTO employees (employee_code, name, pay_type, shift_rate) VALUES ('E_S1', 'Shift Worker 1', 'SHIFT', 500.0)")
        emp_id = cursor.lastrowid
    else:
        emp_id = emp_row[0]

    cursor.execute("SELECT id FROM operations LIMIT 1")
    op_id = cursor.fetchone()[0]

    cursor.execute("DELETE FROM shift_records WHERE week_id = ? AND employee_id = ?", (week_id, emp_id))
    cursor.execute(
        """
        INSERT INTO shift_records (week_id, work_date, employee_id, operation_id, shifts, shift_rate, daily_salary)
        VALUES (?, '2026-07-06', ?, ?, 1.5, 500.0, 750.0)
        """,
        (week_id, emp_id, op_id)
    )
    conn.commit()
    conn.close()

    result = calculate_weekly_salary(week_id)
    assert result is not None
    emp_data = result["employees"][emp_id]
    assert emp_data["shift_salary"] == 750.0


def test_test_c_employee_with_bonus():
    # TEST C — EMPLOYEE WITH BONUS (salary = 500, bonus = 100 -> 600)
    week_id = setup_test_week()
    conn = database.connect_database()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM employees WHERE pay_type = 'PIECE' LIMIT 1")
    emp_id = cursor.fetchone()[0]

    cursor.execute("DELETE FROM bonuses WHERE week_id = ? AND employee_id = ?", (week_id, emp_id))
    cursor.execute(
        "INSERT INTO bonuses (week_id, employee_id, bonus_type, amount) VALUES (?, ?, 'PERFORMANCE', 100.0)",
        (week_id, emp_id)
    )
    conn.commit()
    conn.close()

    result = calculate_weekly_salary(week_id)
    assert result is not None
    emp_data = result["employees"][emp_id]
    assert emp_data["bonus"] == 100.0
    assert emp_data["net_salary"] == emp_data["piece_salary"] + emp_data["shift_salary"] + 100.0 - emp_data["deduction"]


def test_test_d_employee_with_deduction():
    # TEST D — EMPLOYEE WITH DEDUCTION (salary - deduction)
    week_id = setup_test_week()
    conn = database.connect_database()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM employees WHERE pay_type = 'PIECE' LIMIT 1")
    emp_id = cursor.fetchone()[0]

    cursor.execute("DELETE FROM deductions WHERE week_id = ? AND employee_id = ?", (week_id, emp_id))
    cursor.execute(
        "INSERT INTO deductions (week_id, employee_id, deduction_type, amount) VALUES (?, ?, 'ADVANCE', 50.0)",
        (week_id, emp_id)
    )
    conn.commit()
    conn.close()

    result = calculate_weekly_salary(week_id)
    assert result is not None
    emp_data = result["employees"][emp_id]
    assert emp_data["deduction"] == 50.0


def test_test_e_bonus_and_deduction_combined():
    # TEST E — EMPLOYEE WITH BOTH BONUS AND DEDUCTION
    week_id = setup_test_week()
    conn = database.connect_database()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM employees WHERE pay_type = 'PIECE' LIMIT 1")
    emp_id = cursor.fetchone()[0]
    conn.close()

    result = calculate_weekly_salary(week_id)
    assert result is not None
    emp_data = result["employees"][emp_id]
    expected_net = emp_data["piece_salary"] + emp_data["shift_salary"] + emp_data["bonus"] - emp_data["deduction"]
    assert emp_data["net_salary"] == expected_net


def test_test_f_govindasamy_shift_pay_type():
    # TEST F — GOVINDASAMY E016 treated as SHIFT
    week_id = setup_test_week()
    conn = database.connect_database()
    cursor = conn.cursor()
    cursor.execute("UPDATE employees SET pay_type = 'SHIFT' WHERE employee_code = 'E016'")
    cursor.execute("SELECT id FROM employees WHERE employee_code = 'E016'")
    emp_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()

    result = calculate_weekly_salary(week_id)
    assert result is not None
    if emp_id in result["employees"]:
        assert result["employees"][emp_id]["pay_type"] == "SHIFT"


def test_test_g_contractor_shift_worker_commission_separation():
    # TEST G — Contractor shift worker salary vs commission separation
    week_id = setup_test_week()
    conn = database.connect_database()
    cursor = conn.cursor()

    # Get or create contractor
    cursor.execute("SELECT id FROM contractors LIMIT 1")
    c_row = cursor.fetchone()
    if not c_row:
        cursor.execute("INSERT INTO contractors (name, commission_amount, status) VALUES ('Test Contractor', 50.0, 'active')")
        c_id = cursor.lastrowid
    else:
        c_id = c_row[0]

    # Create shift worker assigned to contractor
    cursor.execute("SELECT id FROM employees WHERE contractor_id = ? LIMIT 1", (c_id,))
    emp_row = cursor.fetchone()
    if not emp_row:
        cursor.execute(
            "INSERT INTO employees (employee_code, name, pay_type, shift_rate, contractor_id) VALUES ('E_C1', 'Contract Worker 1', 'SHIFT', 400.0, ?)",
            (c_id,)
        )
        emp_id = cursor.lastrowid
    else:
        emp_id = emp_row[0]

    cursor.execute("SELECT id FROM operations LIMIT 1")
    op_id = cursor.fetchone()[0]

    cursor.execute("DELETE FROM shift_records WHERE week_id = ? AND employee_id = ?", (week_id, emp_id))
    cursor.execute(
        """
        INSERT INTO shift_records (week_id, work_date, employee_id, operation_id, shifts, shift_rate, daily_salary)
        VALUES (?, '2026-07-06', ?, ?, 2.0, 400.0, 800.0)
        """,
        (week_id, emp_id, op_id)
    )
    conn.commit()
    conn.close()

    result = calculate_weekly_salary(week_id)
    assert result is not None
    # Worker salary
    emp_data = result["employees"][emp_id]
    assert emp_data["shift_salary"] == 800.0

    # Contractor commission is separate
    assert "total_contractor_commission" in result
    assert result["total_contractor_commission"] > 0.0


def test_test_h_factory_expenses_separate_from_net_salary():
    # TEST H — Factory expenses contribute to total_factory_expense but NOT employee net salary
    week_id = setup_test_week()
    conn = database.connect_database()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM expenses WHERE week_id = ?", (week_id,))
    cursor.execute("INSERT INTO expenses (week_id, category, amount, notes) VALUES (?, 'TEA', 250.0, 'Tea snacks')", (week_id,))
    conn.commit()
    conn.close()

    result = calculate_weekly_salary(week_id)
    assert result is not None
    assert result["total_factory_expense"] == 250.0

    # Ensure expense is NOT subtracted from any employee's net_salary
    for emp_data in result["employees"].values():
        expected = emp_data["piece_salary"] + emp_data["shift_salary"] + emp_data["bonus"] - emp_data["deduction"]
        assert emp_data["net_salary"] == expected


def test_test_i_historical_rate_preserved_after_master_rate_change():
    # TEST I — Changing employee master rate does NOT change historical calculation
    week_id = setup_test_week()
    conn = database.connect_database()
    cursor = conn.cursor()

    cursor.execute("SELECT id, shift_rate FROM employees WHERE pay_type = 'SHIFT' LIMIT 1")
    emp_id, orig_rate = cursor.fetchone()

    cursor.execute("SELECT id FROM operations LIMIT 1")
    op_id = cursor.fetchone()[0]

    cursor.execute("DELETE FROM shift_records WHERE week_id = ? AND employee_id = ?", (week_id, emp_id))
    cursor.execute(
        """
        INSERT INTO shift_records (week_id, work_date, employee_id, operation_id, shifts, shift_rate, daily_salary)
        VALUES (?, '2026-07-06', ?, ?, 1.0, 300.0, 300.0)
        """,
        (week_id, emp_id, op_id)
    )
    conn.commit()

    # Change master rate to 999.0
    cursor.execute("UPDATE employees SET shift_rate = 999.0 WHERE id = ?", (emp_id,))
    conn.commit()
    conn.close()

    result = calculate_weekly_salary(week_id)
    assert result is not None
    assert result["employees"][emp_id]["shift_salary"] == 300.0


def test_test_j_invalid_week_id_api_response():
    # TEST J — Invalid week_id returns clean HTTP 404 response
    res = client.get("/weeks/999999/salary")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


if __name__ == "__main__":
    pytest.main(["-v", __file__])
