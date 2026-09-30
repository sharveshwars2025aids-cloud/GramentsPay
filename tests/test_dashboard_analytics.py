"""
test_dashboard_analytics.py

Tests for Priority 3: Charts / Dashboard Analytics Backend.
Verifies all required analytics areas:
1. Dashboard endpoint returns successfully.
2. Production totals are correct.
3. Salary totals are correct.
4. Bonus/deduction values are correct.
5. Expense totals are correct.
6. Outsourcing/security values are correctly separated.
7. Department/operation summaries are correct.
8. Trend data is correctly generated from actual records.
9. Empty/no-data week is handled safely.
10. Existing reporting endpoints still work.
"""

import sys
from pathlib import Path
import pytest

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fastapi.testclient import TestClient
import database
from api.main import app
from tests.test_phase7_weekly_closing import setup_comprehensive_test_week

client = TestClient(app)


@pytest.fixture(scope="module")
def sample_week_id():
    """Sets up a comprehensive test week with verified production, shift, expense, outsource, and security records."""
    return setup_comprehensive_test_week()


@pytest.fixture(scope="module")
def empty_week_id():
    """Creates a clean week with zero records to test safe empty-state handling."""
    conn = database.connect_database()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM weeks WHERE week_start = '2090-01-01' LIMIT 1")
    row = cursor.fetchone()
    if row:
        w_id = row[0]
    else:
        cursor.execute("INSERT INTO weeks (week_start, week_end) VALUES ('2090-01-01', '2090-01-07')")
        w_id = cursor.lastrowid
        conn.commit()
    conn.close()
    return w_id


def test_01_dashboard_endpoint_success(sample_week_id):
    """1. Dashboard endpoint returns HTTP 200 with all structured chart sections."""
    res = client.get(f"/weeks/{sample_week_id}/dashboard")
    assert res.status_code == 200
    data = res.json()

    # Check top-level keys
    assert "week_id" in data
    assert "week_start" in data
    assert "week_end" in data
    assert "production" in data
    assert "salary" in data
    assert "expenses" in data
    assert "outsourcing" in data
    assert "security" in data
    assert "weekly_financials" in data


def test_02_production_totals(sample_week_id):
    """2. Production totals match underlying database records."""
    res = client.get(f"/weeks/{sample_week_id}/dashboard")
    assert res.status_code == 200
    prod = res.json()["production"]

    # In setup_comprehensive_test_week: 50.0 (SHIRT @ 10.0) + 20.0 (PANT @ 15.0) = 70.0 qty, 800.0 amount
    assert prod["total_quantity"] == 70.0
    assert prod["total_amount"] == 800.0
    assert prod["distinct_styles"] == 2
    assert prod["active_workers"] >= 1


def test_03_salary_totals(sample_week_id):
    """3. Salary totals match salary engine calculation."""
    res = client.get(f"/weeks/{sample_week_id}/dashboard")
    assert res.status_code == 200
    sal = res.json()["salary"]

    # Piece: 800.0
    # Shift: Suresh (1000.0) + Kumar (1350.0) + Govindasamy (400.0) = 2750.0
    # Gross: 800 + 2750 = 3550.0
    # Net: 3550 + 150 (bonus) - 50 (deduction) = 3650.0
    assert sal["piece_salary"] == 800.0
    assert sal["shift_salary"] == 2750.0
    assert sal["total_gross_salary"] == 3550.0
    assert sal["total_net_salary"] == 3650.0
    assert sal["worker_count"] == 4


def test_04_bonus_and_deduction_values(sample_week_id):
    """4. Bonuses and deductions are accurately aggregated."""
    res = client.get(f"/weeks/{sample_week_id}/dashboard")
    assert res.status_code == 200
    sal = res.json()["salary"]
    fin = res.json()["weekly_financials"]

    # Bonus: 150.0 (ATTENDANCE on Ramesh)
    # Deduction: 50.0 (ADVANCE on Ramesh)
    assert sal["total_bonuses"] == 150.0
    assert sal["total_deductions"] == 50.0
    assert fin["total_bonuses"] == 150.0
    assert fin["total_deductions"] == 50.0


def test_05_expense_totals(sample_week_id):
    """5. Factory expense totals match recorded expense entries."""
    res = client.get(f"/weeks/{sample_week_id}/dashboard")
    assert res.status_code == 200
    exp = res.json()["expenses"]

    # TEA & SNACKS (300.0) + THREAD (450.0) = 750.0
    assert exp["total_factory_expenses"] == 750.0
    cats = exp["by_category"]
    assert "TEA & SNACKS" in cats["labels"]
    assert "THREAD" in cats["labels"]
    assert 300.0 in cats["values"]
    assert 450.0 in cats["values"]


def test_06_outsourcing_and_security_separation(sample_week_id):
    """6. Outsourcing and security are kept strictly separated from factory expenses and salaries."""
    res = client.get(f"/weeks/{sample_week_id}/dashboard")
    assert res.status_code == 200
    data = res.json()

    outsource = data["outsourcing"]
    security = data["security"]
    fin = data["weekly_financials"]

    # Embroidery Hub: 500.0
    assert outsource["total_amount"] == 500.0
    assert fin["outsourcing_total"] == 500.0

    # Suresh Security: 700.0 (7 days)
    assert security["total_amount"] == 700.0
    assert fin["security_total"] == 700.0

    # Total weekly cost: salaries (3650) + commission (20) + factory expenses (750) + outsource (500) + security (700) = 5620.0
    assert fin["total_weekly_cost"] == 5620.0

    # Breakdown components for chart
    breakdown = fin["cost_breakdown"]
    assert "Employee Salaries" in breakdown["labels"]
    assert "Outsourcing" in breakdown["labels"]
    assert "Security" in breakdown["labels"]
    assert 3650.0 in breakdown["values"]
    assert 500.0 in breakdown["values"]
    assert 700.0 in breakdown["values"]


def test_07_department_and_operation_summaries(sample_week_id):
    """7. Department, operation, and style summaries are correctly computed."""
    res = client.get(f"/weeks/{sample_week_id}/dashboard")
    assert res.status_code == 200
    prod = res.json()["production"]
    sal = res.json()["salary"]

    # Production by department
    assert len(prod["by_department"]["labels"]) >= 1
    assert "POWER" in prod["by_department"]["labels"]

    # Production by style
    style_labels = prod["by_style"]["labels"]
    assert any("STYLE-A" in s for s in style_labels)
    assert any("STYLE-B" in s for s in style_labels)

    # Salary by department
    assert len(sal["by_department"]["labels"]) >= 1
    dept_names = sal["by_department"]["labels"]
    assert "POWER" in dept_names or "POWERTABLE" in dept_names


def test_08_trend_data_generated_from_actual_records(sample_week_id):
    """8. Trend data contains real database trajectories and labels."""
    res = client.get(f"/weeks/{sample_week_id}/dashboard")
    assert res.status_code == 200
    data = res.json()

    prod_trend = data["production"]["trend"]
    assert len(prod_trend["labels"]) >= 1
    assert len(prod_trend["quantities"]) == len(prod_trend["labels"])

    sal_trend = data["salary"]["trend"]
    assert len(sal_trend["labels"]) >= 1
    assert len(sal_trend["net_salaries"]) == len(sal_trend["labels"])

    # Multi-week trends endpoint
    trend_res = client.get("/dashboard/trends?limit=5")
    assert trend_res.status_code == 200
    trend_data = trend_res.json()
    assert "labels" in trend_data
    assert "production" in trend_data
    assert "salary" in trend_data
    assert "expenses" in trend_data
    assert "total_costs" in trend_data
    assert len(trend_data["labels"]) <= 5


def test_09_empty_week_handled_safely(empty_week_id):
    """9. Empty week with zero records returns clean zeros and empty collections without errors."""
    res = client.get(f"/weeks/{empty_week_id}/dashboard")
    assert res.status_code == 200
    data = res.json()

    assert data["production"]["total_quantity"] == 0.0
    assert data["production"]["total_amount"] == 0.0
    assert data["production"]["by_department"]["labels"] == []
    assert data["salary"]["total_net_salary"] == 0.0
    assert data["salary"]["total_gross_salary"] == 0.0
    assert data["expenses"]["total_factory_expenses"] == 0.0
    assert data["outsourcing"]["total_amount"] == 0.0
    assert data["security"]["total_amount"] == 0.0
    assert data["weekly_financials"]["total_weekly_cost"] == 0.0


def test_10_nonexistent_week_returns_404():
    """10. Requesting an invalid week ID returns 404."""
    res = client.get("/weeks/999999/dashboard")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_11_sub_dashboard_endpoints(sample_week_id):
    """11. Granular sub-dashboard endpoints return their corresponding sections."""
    r_prod = client.get(f"/weeks/{sample_week_id}/dashboard/production")
    assert r_prod.status_code == 200
    assert "total_quantity" in r_prod.json()

    r_sal = client.get(f"/weeks/{sample_week_id}/dashboard/salary")
    assert r_sal.status_code == 200
    assert "total_net_salary" in r_sal.json()

    r_exp = client.get(f"/weeks/{sample_week_id}/dashboard/expenses")
    assert r_exp.status_code == 200
    assert "total_factory_expenses" in r_exp.json()

    r_fin = client.get(f"/weeks/{sample_week_id}/dashboard/financials")
    assert r_fin.status_code == 200
    assert "total_weekly_cost" in r_fin.json()


def test_12_existing_reporting_endpoints_still_work(sample_week_id):
    """12. Verified that Priority 2 reporting endpoints remain fully intact."""
    r_sal = client.get(f"/weeks/{sample_week_id}/reports/salary")
    assert r_sal.status_code == 200

    r_exp = client.get(f"/weeks/{sample_week_id}/reports/expenses")
    assert r_exp.status_code == 200

    r_out = client.get(f"/weeks/{sample_week_id}/reports/outsource")
    assert r_out.status_code == 200

    r_sec = client.get(f"/weeks/{sample_week_id}/reports/security")
    assert r_sec.status_code == 200

    r_bank = client.get(f"/weeks/{sample_week_id}/reports/bank-transfer")
    assert r_bank.status_code == 200

    r_sum = client.get(f"/weeks/{sample_week_id}/reports/summary")
    assert r_sum.status_code == 200
