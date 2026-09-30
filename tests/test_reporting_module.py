import sys
from pathlib import Path
import pytest

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fastapi.testclient import TestClient
import database
import report_queries
from salary_engine import calculate_weekly_salary
from api.main import app
from tests.test_phase7_weekly_closing import setup_comprehensive_test_week

client = TestClient(app)


@pytest.fixture(scope="module")
def sample_week_id():
    """Sets up a comprehensive test week with known production, shift, bonus, deduction, expense, outsource, and security records."""
    return setup_comprehensive_test_week()


def test_salary_report(sample_week_id):
    """Verifies salary report correctly computes piece, shift, bonus, deduction, and net salary using salary engine."""
    conn = database.connect_database()
    try:
        rows = report_queries.salary(conn, sample_week_id)
        assert isinstance(rows, list)
        assert len(rows) > 0

        # Verify RAMESH has bonus, deduction, net_salary
        ramesh = next((r for r in rows if r["employee_name"] == "RAMESH"), None)
        assert ramesh is not None
        assert ramesh["piece_salary"] == 800.0
        assert ramesh["bonus"] == 150.0
        assert ramesh["deduction"] == 50.0
        assert ramesh["net_salary"] == 900.0

        # Verify SURESH has shift salary
        suresh = next((r for r in rows if r["employee_name"] == "SURESH"), None)
        assert suresh is not None
        assert suresh["shift_salary"] == 1000.0
        assert suresh["net_salary"] == 1000.0
    finally:
        conn.close()


def test_expenses_report(sample_week_id):
    """Verifies expenses report returns factory expenses."""
    conn = database.connect_database()
    try:
        rows = report_queries.expenses(conn, sample_week_id)
        assert isinstance(rows, list)
        categories = {r["expense_name"]: r["amount"] for r in rows}
        assert "TEA & SNACKS" in categories
        assert categories["TEA & SNACKS"] == 300.0
        assert "THREAD" in categories
        assert categories["THREAD"] == 450.0
    finally:
        conn.close()


def test_outsource_report(sample_week_id):
    """Verifies outsourcing report returns outsource centre details."""
    conn = database.connect_database()
    try:
        rows = report_queries.outsource(conn, sample_week_id)
        assert isinstance(rows, list)
        assert len(rows) >= 1
        emb = next((r for r in rows if r["centre_name"] == "EMBROIDERY HUB"), None)
        assert emb is not None
        assert emb["style"] == "STYLE-A"
        assert emb["salary"] == 500.0
    finally:
        conn.close()


def test_security_report(sample_week_id):
    """Verifies security payment report."""
    conn = database.connect_database()
    try:
        rows = report_queries.security(conn, sample_week_id)
        assert isinstance(rows, list)
        assert len(rows) >= 1
        sec = rows[0]
        assert sec["days"] == 7
        assert sec["salary"] == 700.0
    finally:
        conn.close()


def test_department_summary_and_operations_reports(sample_week_id):
    """Verifies department-wise salary summary and production operations."""
    conn = database.connect_database()
    try:
        dept_rows = report_queries.salary_department_summary(conn, sample_week_id)
        assert isinstance(dept_rows, list)
        assert len(dept_rows) >= 1

        op_rows = report_queries.salary_operations(conn, sample_week_id)
        assert isinstance(op_rows, list)
        assert len(op_rows) >= 1
        style_names = [r["style"] for r in op_rows]
        assert any("STYLE-A" in s for s in style_names)
    finally:
        conn.close()


def test_bank_transfer_report_applies_net_salary(sample_week_id):
    """Verifies bank transfer report correctly applies net salary (including bonuses & deductions) and includes contractors, expenses, outsource, and security."""
    conn = database.connect_database()
    try:
        rows = report_queries.bank_transfer(conn, sample_week_id)
        assert isinstance(rows, list)

        # Check RAMESH has net salary 900.0 (800 gross + 150 bonus - 50 deduction)
        ramesh = next((r for r in rows if r["name"] == "RAMESH"), None)
        assert ramesh is not None
        assert ramesh["amount"] == 900.0

        # Check separate categories exist
        contractor = next((r for r in rows if r["department"] == "CONTRACTOR"), None)
        assert contractor is not None

        expense = next((r for r in rows if r["department"] == "GENERAL EXPENSE"), None)
        assert expense is not None

        outsource = next((r for r in rows if r["department"] == "OUTSOURCE"), None)
        assert outsource is not None
        assert outsource["amount"] == 500.0

        security = next((r for r in rows if r["department"] == "SECURITY"), None)
        assert security is not None
        assert security["amount"] == 700.0
    finally:
        conn.close()


def test_summary_report(sample_week_id):
    """Verifies weekly summary report aggregates all financial sections."""
    conn = database.connect_database()
    try:
        rows = report_queries.summary(conn, sample_week_id)
        assert isinstance(rows, list)
        items = {r["item"]: r["amount"] for r in rows}
        assert "Employee Salaries" in items
        assert "Contractor Commissions" in items
        assert "Factory Expenses" in items
        assert "Outsource Payments" in items
        assert "Security Payments" in items
        assert "Grand Total" in items

        assert items["Employee Salaries"] == 3650.0
        assert items["Factory Expenses"] == 750.0
        assert items["Outsource Payments"] == 500.0
        assert items["Security Payments"] == 700.0
        assert items["Grand Total"] == (
            items["Employee Salaries"]
            + items["Contractor Commissions"]
            + items["Factory Expenses"]
            + items["Outsource Payments"]
            + items["Security Payments"]
        )
    finally:
        conn.close()


def test_reports_are_read_only(sample_week_id):
    """Verifies running reports does not alter database record counts."""
    conn = database.connect_database()
    cursor = conn.cursor()

    tables = ["weeks", "production_records", "shift_records", "bonuses", "deductions", "expenses", "outsource_payments", "security_payments"]
    counts_before = {}
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        counts_before[t] = cursor.fetchone()[0]

    # Run all reports
    report_queries.salary(conn, sample_week_id)
    report_queries.expenses(conn, sample_week_id)
    report_queries.outsource(conn, sample_week_id)
    report_queries.security(conn, sample_week_id)
    report_queries.salary_department_summary(conn, sample_week_id)
    report_queries.salary_operations(conn, sample_week_id)
    report_queries.bank_transfer(conn, sample_week_id)
    report_queries.summary(conn, sample_week_id)
    report_queries.power_table_helpers(conn, sample_week_id)
    report_queries.company_helpers(conn, sample_week_id)

    counts_after = {}
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        counts_after[t] = cursor.fetchone()[0]

    conn.close()
    assert counts_before == counts_after


def test_reports_api_endpoints(sample_week_id):
    """Verifies HTTP GET endpoints under /weeks/{week_id}/reports/."""
    # 1. Salary report
    res = client.get(f"/weeks/{sample_week_id}/reports/salary")
    assert res.status_code == 200
    assert len(res.json()) > 0

    # 2. Expenses report
    res = client.get(f"/weeks/{sample_week_id}/reports/expenses")
    assert res.status_code == 200
    assert len(res.json()) >= 2

    # 3. Outsource report
    res = client.get(f"/weeks/{sample_week_id}/reports/outsource")
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # 4. Security report
    res = client.get(f"/weeks/{sample_week_id}/reports/security")
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # 5. Department summary report
    res = client.get(f"/weeks/{sample_week_id}/reports/department-summary")
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # 6. Operations report
    res = client.get(f"/weeks/{sample_week_id}/reports/operations")
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # 7. Bank transfer report
    res = client.get(f"/weeks/{sample_week_id}/reports/bank-transfer")
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # 8. Summary report
    res = client.get(f"/weeks/{sample_week_id}/reports/summary")
    assert res.status_code == 200
    assert len(res.json()) == 6

    # 9. Invalid week id returns 404
    res = client.get("/weeks/999999/reports/salary")
    assert res.status_code == 404
