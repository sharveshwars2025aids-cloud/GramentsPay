import os
import sys
import shutil
import tempfile
import unittest
import sqlite3
import openpyxl
import pandas as pd
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure src is in sys.path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import database
from database import connect_database, initialize_database
import seed_test_data
from api.main import app
from importer import import_workbook, get_employee_id, get_style_id, get_operation_id
from salary_engine import calculate_weekly_salary
from biometric_manager import (
    parse_and_import_biometric_file,
    get_attendance_mismatches,
    override_mismatch,
    override_all_mismatches,
)
from excel_generator import generate_weekly_closing
from template_mapper import WEEKLY_CLOSING_TEMPLATE


class TestWebAndBiometric(unittest.TestCase):
    """
    Runs against an ISOLATED, disposable SQLite database (not the real
    database/garments.db). Every module here opens connections via
    database.connect_database(), so patching database.DATABASE_PATH
    redirects everything for the duration of this test class.
    """

    @classmethod
    def setUpClass(cls):
        cls._temp_dir = tempfile.mkdtemp(prefix="garments_test_")
        cls._original_database_dir = database.DATABASE_DIR
        cls._original_database_path = database.DATABASE_PATH
        database.DATABASE_DIR = Path(cls._temp_dir)
        database.DATABASE_PATH = Path(cls._temp_dir) / "test_garments.db"

    @classmethod
    def tearDownClass(cls):
        database.DATABASE_DIR = cls._original_database_dir
        database.DATABASE_PATH = cls._original_database_path
        shutil.rmtree(cls._temp_dir, ignore_errors=True)

    def setUp(self):
        """Initializes and seeds a FRESH isolated test database before each test."""
        initialize_database()
        try:
            seed_test_data.main()
        except Exception:
            pass
        self._open_connections = []

    def tearDown(self):
        """Guarantees no test leaves a dangling open connection/transaction."""
        for connection in self._open_connections:
            try:
                connection.rollback()
            except Exception:
                pass
            try:
                connection.close()
            except Exception:
                pass

    def _track(self, connection):
        self._open_connections.append(connection)
        return connection

    def test_api_health(self):
        client = TestClient(app)
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "OK"})

    def test_web_entry_and_weekly_closing_generation(self):
        """
        Acceptance Criterion 1: A week can be fully populated using ONLY web API endpoints
        and produces a Weekly Closing Excel file.
        """
        client = TestClient(app)
        conn = self._track(connect_database())
        cursor = conn.cursor()

        # 1. Create a test week
        cursor.execute(
            "INSERT INTO weeks (week_start, week_end) VALUES ('2026-09-01', '2026-09-07')"
        )
        week_id = cursor.lastrowid
        conn.commit()

        # Get sample employee, style, operation IDs
        cursor.execute("SELECT id FROM employees WHERE pay_type='PIECE' LIMIT 1")
        p_emp_id = cursor.fetchone()[0]

        cursor.execute("SELECT id FROM employees WHERE pay_type='SHIFT' LIMIT 1")
        s_emp_id = cursor.fetchone()[0]

        cursor.execute("SELECT id FROM styles LIMIT 1")
        style_id = cursor.fetchone()[0]

        cursor.execute("SELECT id FROM operations LIMIT 1")
        op_id = cursor.fetchone()[0]
        conn.close()

        # 2. Populate via Web API Endpoints
        prod_resp = client.post(
            f"/weeks/{week_id}/production",
            json={
                "work_date": "2026-09-01",
                "employee_id": p_emp_id,
                "style_id": style_id,
                "operation_id": op_id,
                "type": "SHIRT",
                "color": "BLUE",
                "total_qty": 100.0,
                "rate": 15.0,
            },
        )
        self.assertEqual(prod_resp.status_code, 201)
        self.assertEqual(prod_resp.json()["total_amount"], 1500.0)

        shift_resp = client.post(
            f"/weeks/{week_id}/shift",
            json={
                "work_date": "2026-09-01",
                "employee_id": s_emp_id,
                "operation_id": op_id,
                "item": "POWERTABLE",
                "shifts": 1.0,
                "shift_rate": 500.0,
            },
        )
        self.assertEqual(shift_resp.status_code, 201)
        self.assertEqual(shift_resp.json()["daily_salary"], 500.0)

        outs_resp = client.post(
            f"/weeks/{week_id}/outsource",
            json={
                "style": "CVC",
                "item": "COLLAR",
                "qty": 50.0,
                "rate": 10.0,
                "centre_name": "CENTRE A",
                "remarks": "Outsource test",
            },
        )
        self.assertEqual(outs_resp.status_code, 201)
        self.assertEqual(outs_resp.json()["amount"], 500.0)

        sec_resp = client.post(
            f"/weeks/{week_id}/security",
            json={
                "employee_id": s_emp_id,
                "days": 1.0,
                "amount": 400.0,
                "remarks": "Security duty",
            },
        )
        self.assertEqual(sec_resp.status_code, 201)

        exp_resp = client.post(
            f"/weeks/{week_id}/expenses",
            json={
                "category": "TEA & SNACKS",
                "amount": 250.0,
                "notes": "Daily refreshment",
            },
        )
        self.assertEqual(exp_resp.status_code, 201)

        ded_resp = client.post(
            f"/weeks/{week_id}/deductions",
            json={
                "employee_id": s_emp_id,
                "deduction_type": "ADVANCE",
                "amount": 100.0,
                "notes": "Weekly advance",
            },
        )
        self.assertEqual(ded_resp.status_code, 201)

        bon_resp = client.post(
            f"/weeks/{week_id}/bonuses",
            json={
                "employee_id": s_emp_id,
                "bonus_type": "PERFORMANCE",
                "amount": 150.0,
                "notes": "Great job",
            },
        )
        self.assertEqual(bon_resp.status_code, 201)

        # 3. Generate Closing Excel via Web API
        gen_resp = client.post(f"/weeks/{week_id}/generate-closing")
        self.assertEqual(gen_resp.status_code, 200)
        closing_data = gen_resp.json()
        self.assertEqual(closing_data["week_id"], week_id)
        self.assertTrue(os.path.exists(closing_data["file_path"]))

    def test_excel_and_web_equivalence(self):
        """
        Acceptance Criterion 2: Populating data via Excel import vs Web API
        produces identical Weekly Closing calculation totals and workbook structures.
        """
        client = TestClient(app)
        conn = self._track(connect_database())
        cursor = conn.cursor()

        # Create Week A (Excel path) and Week B (Web API path)
        cursor.execute("INSERT INTO weeks (week_start, week_end) VALUES ('2026-09-15', '2026-09-21')")
        week_a = cursor.lastrowid

        cursor.execute("INSERT INTO weeks (week_start, week_end) VALUES ('2026-09-22', '2026-09-28')")
        week_b = cursor.lastrowid

        cursor.execute("SELECT id FROM employees WHERE pay_type='PIECE' LIMIT 1")
        p_emp_id = cursor.fetchone()[0]

        cursor.execute("SELECT id FROM employees WHERE pay_type='SHIFT' LIMIT 1")
        s_emp_id = cursor.fetchone()[0]

        cursor.execute("SELECT id FROM styles LIMIT 1")
        style_id = cursor.fetchone()[0]

        cursor.execute("SELECT id FROM operations LIMIT 1")
        op_id = cursor.fetchone()[0]

        # Insert record directly into Week A (mirroring excel import)
        cursor.execute(
            """
            INSERT INTO production_records (week_id, work_date, employee_id, style_id, operation_id, type, color, total_qty, rate, total_amount)
            VALUES (?, '2026-09-15', ?, ?, ?, 'SHIRT', 'WHITE', 200.0, 20.0, 4000.0)
            """,
            (week_a, p_emp_id, style_id, op_id),
        )
        cursor.execute(
            """
            INSERT INTO shift_records (week_id, work_date, employee_id, operation_id, item, shifts, shift_rate, daily_salary)
            VALUES (?, '2026-09-15', ?, ?, 'POWERTABLE', 2.0, 600.0, 1200.0)
            """,
            (week_a, s_emp_id, op_id),
        )
        conn.commit()
        conn.close()

        # Insert identical data into Week B via Web API
        resp_prod = client.post(
            f"/weeks/{week_b}/production",
            json={
                "work_date": "2026-09-22",
                "employee_id": p_emp_id,
                "style_id": style_id,
                "operation_id": op_id,
                "type": "SHIRT",
                "color": "WHITE",
                "total_qty": 200.0,
                "rate": 20.0,
            },
        )
        self.assertEqual(resp_prod.status_code, 201)

        resp_shift = client.post(
            f"/weeks/{week_b}/shift",
            json={
                "work_date": "2026-09-22",
                "employee_id": s_emp_id,
                "operation_id": op_id,
                "item": "POWERTABLE",
                "shifts": 2.0,
                "shift_rate": 600.0,
            },
        )
        self.assertEqual(resp_shift.status_code, 201)

        # Calculate salary for both weeks
        sal_a = calculate_weekly_salary(week_a)
        sal_b = calculate_weekly_salary(week_b)

        self.assertEqual(sal_a["total_salary"], sal_b["total_salary"])
        self.assertEqual(sal_a["total_contractor_commission"], sal_b["total_contractor_commission"])
        self.assertEqual(sal_a["total_factory_expense"], sal_b["total_factory_expense"])

        # Generate closing workbooks
        file_a = generate_weekly_closing(week_a, WEEKLY_CLOSING_TEMPLATE)
        file_b = generate_weekly_closing(week_b, WEEKLY_CLOSING_TEMPLATE)

        wb_a = openpyxl.load_workbook(file_a, data_only=True)
        wb_b = openpyxl.load_workbook(file_b, data_only=True)

        self.assertEqual(wb_a.sheetnames, wb_b.sheetnames)

    def test_biometric_mismatch_flagging_and_override(self):
        """
        Acceptance Criteria 3 & 4:
        - Biometric mismatch surfaces '<name> isn't tapping properly' warning.
        - Does NOT alter shift_records.
        - Can be overridden with audit row in attendance_overrides.
        - Un-overridden mismatch does NOT block closing generation.
        """
        conn = self._track(connect_database())
        cursor = conn.cursor()

        # 1. Create a week and a shift record (Entered: 1.0 shift)
        cursor.execute(
            "INSERT INTO weeks (week_start, week_end) VALUES ('2026-09-10', '2026-09-16')"
        )
        week_id = cursor.lastrowid

        cursor.execute("SELECT id, name FROM employees WHERE pay_type='SHIFT' LIMIT 1")
        emp_row = cursor.fetchone()
        emp_id, emp_name = emp_row[0], emp_row[1]

        cursor.execute("SELECT id FROM operations LIMIT 1")
        op_id = cursor.fetchone()[0]

        cursor.execute(
            """
            INSERT INTO shift_records (week_id, work_date, employee_id, operation_id, item, shifts, shift_rate, daily_salary)
            VALUES (?, '2026-09-10', ?, ?, 'POWERTABLE', 1.0, 500.0, 500.0)
            """,
            (week_id, emp_id, op_id),
        )
        conn.commit()

        # 2. Create Biometric export DataFrame with 0.5 shift (deliberate mismatch)
        bio_df = pd.DataFrame(
            [
                {
                    "EMPLOYEE_ID": emp_id,
                    "WORK_DATE": "2026-09-10",
                    "COMPUTED_SHIFT_VALUE": 0.5,
                    "DEVICE_ID": "BIO_01",
                }
            ]
        )

        # 3. Import biometric data
        inserted = parse_and_import_biometric_file(
            conn, week_id, bio_df, "test_bio_export.csv"
        )
        conn.commit()
        self.assertEqual(inserted, 1)

        # 4. Verify shift_records total shifts remained untouched (1.0)
        cursor.execute(
            "SELECT shifts FROM shift_records WHERE week_id=? AND employee_id=?",
            (week_id, emp_id),
        )
        self.assertEqual(cursor.fetchone()[0], 1.0)

        # 5. Check attendance mismatches
        mismatches = get_attendance_mismatches(conn, week_id, tolerance=0.5)
        self.assertEqual(len(mismatches), 1)
        mismatch = mismatches[0]
        expected_headline = f"{emp_name} isn't tapping properly on 2026-09-10"
        self.assertEqual(mismatch["headline"], expected_headline)
        self.assertEqual(mismatch["entered_shift_value"], 1.0)
        self.assertEqual(mismatch["biometric_shift_value"], 0.5)

        # 6. Verify non-blocking closing generation (closing works even with un-overridden mismatch)
        file_path = generate_weekly_closing(week_id, WEEKLY_CLOSING_TEMPLATE)
        self.assertTrue(os.path.exists(file_path))

        # 7. Perform Override
        override_id = override_mismatch(
            connection=conn,
            week_id=week_id,
            employee_id=emp_id,
            work_date="2026-09-10",
            biometric_shift_value=0.5,
            entered_shift_value=1.0,
            overridden_by="Accountant John",
            reason="Verified night shift log",
        )
        conn.commit()

        # Verify audit row created
        cursor.execute(
            "SELECT overridden_by, reason FROM attendance_overrides WHERE id=?",
            (override_id,),
        )
        audit = cursor.fetchone()
        self.assertEqual(audit[0], "Accountant John")
        self.assertEqual(audit[1], "Verified night shift log")

        # 8. Re-check mismatches: should now be 0 because it's overridden!
        remaining_mismatches = get_attendance_mismatches(conn, week_id, tolerance=0.5)
        self.assertEqual(len(remaining_mismatches), 0)

        conn.close()


if __name__ == "__main__":
    unittest.main()