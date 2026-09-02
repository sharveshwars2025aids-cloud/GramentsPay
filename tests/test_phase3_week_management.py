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


def test_01_create_new_week():
    # Test A: Create new week
    payload = {
        "week_start": "2026-08-03",
        "week_end": "2026-08-09"
    }
    response = client.post("/weeks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert isinstance(data["id"], int)
    assert data["week_start"] == "2026-08-03"
    assert data["week_end"] == "2026-08-09"
    assert "Week" in data["label"]


def test_02_create_duplicate_week_returns_same_id():
    # Test B: Request the same week date range again
    payload = {
        "week_start": "2026-08-03",
        "week_end": "2026-08-09"
    }
    res1 = client.post("/weeks", json=payload)
    res2 = client.post("/weeks", json=payload)
    assert res1.status_code == 201
    assert res2.status_code in (200, 201)
    assert res1.json()["id"] == res2.json()["id"]


def test_03_get_week_by_id():
    # Test C: Get week by ID
    payload = {
        "week_start": "2026-08-03",
        "week_end": "2026-08-09"
    }
    res = client.post("/weeks", json=payload)
    week_id = res.json()["id"]

    get_res = client.get(f"/weeks/{week_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == week_id
    assert data["week_start"] == "2026-08-03"
    assert data["week_end"] == "2026-08-09"


def test_04_invalid_week_id_returns_404():
    # Test D: Try invalid ID
    res = client.get("/weeks/999999")
    assert res.status_code == 404
    assert "Week with id 999999 not found" in res.json()["detail"] or "not found" in res.json()["detail"].lower()


def test_05_update_existing_week():
    # Test E: Update existing week
    import time
    ts = int(time.time()) % 100000
    w_start = f"2099-01-01"
    w_end_init = f"2099-01-07"
    w_end_updated = f"2099-01-08"

    # Ensure clean state for test dates
    conn = database.connect_database()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM weeks WHERE week_start LIKE '2099-%'")
    conn.commit()
    conn.close()

    payload = {
        "week_start": w_start,
        "week_end": w_end_init
    }
    created = client.post("/weeks", json=payload).json()
    week_id = created["id"]

    update_payload = {
        "week_start": w_start,
        "week_end": w_end_updated,
        "closing_generated": 0
    }
    update_res = client.put(f"/weeks/{week_id}", json=update_payload)
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["id"] == week_id
    assert data["week_end"] == w_end_updated




def test_06_closing_readiness_valid_week():
    # Test F: Generate closing / readiness for existing week
    conn = database.connect_database()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM weeks LIMIT 1")
    week_id = cursor.fetchone()[0]
    conn.close()

    res = client.get(f"/weeks/{week_id}/closing-readiness")
    assert res.status_code == 200
    data = res.json()
    assert data["week_id"] == week_id


def test_07_closing_readiness_invalid_week():
    # Test G: Closing readiness for invalid week
    res = client.get("/weeks/999999/closing-readiness")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_08_production_entry_valid_week():
    # Test H: Insert production record using valid week ID
    conn = database.connect_database()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM weeks LIMIT 1")
    week_id = cursor.fetchone()[0]

    cursor.execute("SELECT id FROM styles WHERE style_no = '114569'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO styles (style_no, style_name) VALUES ('114569', 'Style 114569')")
        conn.commit()
    conn.close()


    payload = {
        "work_date": "2026-07-06",
        "employee_code": "E001",
        "style_no": "114569",
        "operation_name": "3 PEAK",
        "total_qty": 10.0,
        "rate": 5.0
    }
    res = client.post(f"/weeks/{week_id}/production", json=payload)
    assert res.status_code == 201

    assert res.json()["week_id"] == week_id


def test_09_production_entry_invalid_week():
    # Test I: Insert production record using invalid week ID
    payload = {
        "work_date": "2026-07-06",
        "employee_code": "E001",
        "style_no": "114569",
        "operation_name": "3 PEAK",
        "total_qty": 10.0,
        "rate": 5.0
    }
    res = client.post("/weeks/999999/production", json=payload)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_10_verify_no_duplicate_weeks_created():
    # Test J: Verify no duplicate week rows were created for (2026-08-03, 2026-08-09)
    conn = database.connect_database()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM weeks WHERE TRIM(week_start) = '2026-08-03' AND TRIM(week_end) = '2026-08-09'"
    )
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 1


if __name__ == "__main__":
    pytest.main(["-v", __file__])
