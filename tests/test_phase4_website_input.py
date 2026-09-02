import sys
from pathlib import Path
import pytest

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fastapi.testclient import TestClient
import database
from api.main import app

client = TestClient(app)


def get_active_week_id():
    conn = database.connect_database()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM weeks LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    # Create week if none exists
    res = client.post("/weeks", json={"week_start": "2026-08-03", "week_end": "2026-08-09"})
    return res.json()["id"]


def test_test_a_piece_employee():
    # TEST A — PIECE EMPLOYEE
    week_id = get_active_week_id()
    payload = {
        "work_date": "2026-07-06",
        "employee_code": "E001",
        "style_no": "PEPX031A25",
        "operation_name": "3 PEAK",
        "total_qty": 15.0,
        "rate": 4.5,
        "sizes": {"S": 15.0}
    }
    res = client.post(f"/weeks/{week_id}/production", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["week_id"] == week_id


def test_test_b_shift_employee():
    # TEST B — SHIFT EMPLOYEE
    week_id = get_active_week_id()
    payload = {
        "work_date": "2026-07-06",
        "employee_code": "E016",
        "operation_name": "3 PEAK",
        "shifts": 1.0,
        "shift_rate": 350.0
    }
    res = client.post(f"/weeks/{week_id}/shift", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["week_id"] == week_id


def test_test_c_alphanumeric_employee():
    # TEST C — ALPHANUMERIC EMPLOYEE
    week_id = get_active_week_id()
    # First ensure employee 12EC exists in DB or create it
    conn = database.connect_database()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM employees WHERE employee_code = '12EC'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO employees (employee_code, name, pay_type) VALUES ('12EC', 'Test Alpha Emp', 'PIECE')"
        )
        conn.commit()
    conn.close()

    payload = {
        "work_date": "2026-07-06",
        "employee_code": "12EC",
        "style_no": "PEPX031A25",
        "operation_name": "3 PEAK",
        "total_qty": 20.0,
        "rate": 5.0,
        "sizes": {"M": 20.0}
    }
    res = client.post(f"/weeks/{week_id}/production", json=payload)
    assert res.status_code == 201


def test_test_d_alphanumeric_style():
    # TEST D — ALPHANUMERIC STYLE
    week_id = get_active_week_id()
    conn = database.connect_database()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM styles WHERE style_no = 'K55-A6-30-402'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO styles (style_no, style_name) VALUES ('K55-A6-30-402', 'Alpha Style')")
        conn.commit()
    conn.close()

    payload = {
        "work_date": "2026-07-06",
        "employee_code": "E001",
        "style_no": "K55-A6-30-402",
        "operation_name": "3 PEAK",
        "total_qty": 10.0,
        "rate": 3.0,
        "sizes": {"L": 10.0}
    }
    res = client.post(f"/weeks/{week_id}/production", json=payload)
    assert res.status_code == 201


def test_test_e_operation_name():
    # TEST E — OPERATION NAME
    week_id = get_active_week_id()
    payload = {
        "work_date": "2026-07-06",
        "employee_code": "E001",
        "style_no": "PEPX031A25",
        "operation_name": "NECK FOLG",
        "total_qty": 5.0,
        "rate": 2.5,
        "sizes": {"S": 5.0}
    }
    res = client.post(f"/weeks/{week_id}/production", json=payload)
    assert res.status_code == 201


def test_test_f_invalid_employee():
    # TEST F — INVALID EMPLOYEE
    week_id = get_active_week_id()
    payload = {
        "work_date": "2026-07-06",
        "employee_code": "E999",
        "style_no": "PEPX031A25",
        "operation_name": "3 PEAK",
        "total_qty": 10.0,
        "rate": 5.0
    }
    res = client.post(f"/weeks/{week_id}/production", json=payload)
    assert res.status_code == 404
    assert "Employee code 'E999' not found" in res.json()["detail"]


def test_test_g_invalid_style():
    # TEST G — INVALID STYLE
    week_id = get_active_week_id()
    payload = {
        "work_date": "2026-07-06",
        "employee_code": "E001",
        "style_no": "STYLE-DOES-NOT-EXIST",
        "operation_name": "3 PEAK",
        "total_qty": 10.0,
        "rate": 5.0
    }
    res = client.post(f"/weeks/{week_id}/production", json=payload)
    assert res.status_code == 404
    assert "Style 'STYLE-DOES-NOT-EXIST' not found" in res.json()["detail"]


def test_test_h_invalid_operation():
    # TEST H — INVALID OPERATION
    week_id = get_active_week_id()
    payload = {
        "work_date": "2026-07-06",
        "employee_code": "E001",
        "style_no": "PEPX031A25",
        "operation_name": "UNKNOWN OPERATION",
        "total_qty": 10.0,
        "rate": 5.0
    }
    res = client.post(f"/weeks/{week_id}/production", json=payload)
    assert res.status_code == 404
    assert "Operation 'UNKNOWN OPERATION' not found" in res.json()["detail"]


def test_test_i_week_selection():
    # TEST I — WEEK SELECTION
    weeks_res = client.get("/weeks")
    assert weeks_res.status_code == 200
    weeks = weeks_res.json()
    assert len(weeks) > 0
    first_week = weeks[0]
    assert "id" in first_week
    assert "label" in first_week


def test_test_j_successful_database_entry():
    # TEST J — SUCCESSFUL DATABASE ENTRY
    week_id = get_active_week_id()
    payload = {
        "work_date": "2026-07-06",
        "employee_code": "E001",
        "style_no": "PEPX031A25",
        "operation_name": "3 PEAK",
        "total_qty": 50.0,
        "rate": 6.0,
        "sizes": {"ALL": 50.0}
    }
    res = client.post(f"/weeks/{week_id}/production", json=payload)
    assert res.status_code == 201
    rec_id = res.json()["id"]

    # Verify directly in SQLite DB that foreign keys are resolved
    conn = database.connect_database()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT employee_id, style_id, operation_id FROM production_records WHERE id = ?",
        (rec_id,)
    )
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    emp_id, style_id, op_id = row
    assert isinstance(emp_id, int)
    assert isinstance(style_id, int)
    assert isinstance(op_id, int)


if __name__ == "__main__":
    pytest.main(["-v", __file__])
