import sys
from pathlib import Path
import pytest

# Add src/ to python path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fastapi.testclient import TestClient
import database
from api.main import app

client = TestClient(app)


def test_01_employee_code_resolution_and_alphanumeric_creation():
    # Test Employee Creation with alphanumeric code
    emp_payload = {
        "employee_code": "TEST-EMP-001",
        "name": "Test Worker Alpha",
        "pay_type": "PIECE",
        "worker_type": "OPERATOR"
    }
    response = client.post("/employees", json=emp_payload)
    assert response.status_code in (201, 409)
    if response.status_code == 201:
        data = response.json()
        assert data["employee_code"] == "TEST-EMP-001"
        assert isinstance(data["id"], int)

    # Verify duplicate code produces clear 409 error
    dup_response = client.post("/employees", json=emp_payload)
    assert dup_response.status_code == 409
    assert "already exists" in dup_response.json()["detail"]


def test_02_style_no_resolution_and_alphanumeric_creation():
    # Test Style Creation with alphanumeric style_no
    style_payload = {
        "style_no": "TEST-STYLE-99",
        "style_name": "Test Alphanumeric Style"
    }
    response = client.post("/styles", json=style_payload)
    assert response.status_code in (201, 409)
    if response.status_code == 201:
        data = response.json()
        assert data["style_no"] == "TEST-STYLE-99"

    # Verify duplicate style_no produces clear 409 error
    dup_response = client.post("/styles", json=style_payload)
    assert dup_response.status_code == 409
    assert "already exists" in dup_response.json()["detail"]


def test_03_operation_name_creation_and_duplicate_prevention():
    op_payload = {
        "operation_name": "TEST OP NECK"
    }
    response = client.post("/operations", json=op_payload)
    assert response.status_code in (201, 409)
    if response.status_code == 201:
        data = response.json()
        assert data["operation_name"] == "TEST OP NECK"

    # Verify duplicate operation produces clear 409 error
    dup_response = client.post("/operations", json=op_payload)
    assert dup_response.status_code == 409
    assert "already exists" in dup_response.json()["detail"]


def test_04_invalid_employee_code_returns_clear_error():
    payload = {
        "work_date": "2026-07-06",
        "employee_code": "E999_NON_EXISTENT",
        "style_no": "114569",
        "operation_name": "3 PEAK",
        "total_qty": 10.0,
        "rate": 5.0
    }
    response = client.post("/weeks/148/production", json=payload)
    assert response.status_code in (404, 400)
    detail = response.json()["detail"]
    assert "E999_NON_EXISTENT" in detail and "not found" in detail
    assert "FOREIGN KEY constraint failed" not in detail


def test_05_invalid_style_no_returns_clear_error():
    payload = {
        "work_date": "2026-07-06",
        "employee_code": "E001",
        "style_no": "STYLE_DOES_NOT_EXIST_999",
        "operation_name": "3 PEAK",
        "total_qty": 10.0,
        "rate": 5.0
    }
    response = client.post("/weeks/148/production", json=payload)
    assert response.status_code in (404, 400)
    detail = response.json()["detail"]
    assert "STYLE_DOES_NOT_EXIST_999" in detail and "not found" in detail
    assert "FOREIGN KEY constraint failed" not in detail


def test_06_invalid_operation_name_returns_clear_error():
    payload = {
        "work_date": "2026-07-06",
        "employee_code": "E001",
        "style_no": "114569",
        "operation_name": "UNKNOWN_OP_XYZ",
        "total_qty": 10.0,
        "rate": 5.0
    }
    response = client.post("/weeks/148/production", json=payload)
    assert response.status_code in (404, 400)
    detail = response.json()["detail"]
    assert "UNKNOWN_OP_XYZ" in detail and "not found" in detail
    assert "FOREIGN KEY constraint failed" not in detail


def test_07_invalid_week_id_returns_clear_error():
    payload = {
        "work_date": "2026-07-06",
        "employee_code": "E001",
        "style_no": "114569",
        "operation_name": "3 PEAK",
        "total_qty": 10.0,
        "rate": 5.0
    }
    response = client.post("/weeks/999999/production", json=payload)
    assert response.status_code == 404
    assert "Week 999999 not found" in response.json()["detail"]


def test_08_successful_production_entry():
    # First get an existing week_id
    conn = database.connect_database()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM weeks LIMIT 1")
    week_row = cursor.fetchone()

    cursor.execute("SELECT id FROM styles WHERE style_no = '114569'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO styles (style_no, style_name) VALUES ('114569', 'Style 114569')")
        conn.commit()
    conn.close()

    assert week_row is not None
    week_id = week_row[0]


    payload = {
        "work_date": "2026-07-06",
        "employee_code": "E001",
        "style_no": "114569",
        "operation_name": "3 PEAK",
        "total_qty": 20.0,
        "rate": 2.5
    }
    response = client.post(f"/weeks/{week_id}/production", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["total_amount"] == 50.0
    assert isinstance(data["employee_id"], int)
    assert isinstance(data["style_id"], int)
    assert isinstance(data["operation_id"], int)


def test_09_successful_shift_entry():
    conn = database.connect_database()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM weeks LIMIT 1")
    week_row = cursor.fetchone()
    conn.close()
    assert week_row is not None
    week_id = week_row[0]

    payload = {
        "work_date": "2026-07-06",
        "employee_code": "E001",
        "operation_name": "3 PEAK",
        "style_no": "114569",
        "shifts": 1.5,
        "shift_rate": 350.0
    }
    response = client.post(f"/weeks/{week_id}/shift", json=payload)
    assert response.status_code in (201, 400)
    if response.status_code == 201:
        data = response.json()
        assert data["daily_salary"] == 525.0
        assert isinstance(data["employee_id"], int)


if __name__ == "__main__":
    pytest.main(["-v", __file__])
