import os
import sys
from pathlib import Path

# Ensure src is in path
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import openpyxl
from fastapi.testclient import TestClient
from api.main import app

def run_e2e_regression():
    client = TestClient(app)

    # 1. Create a dedicated test week with unique timestamp
    import time
    ts = int(time.time()) % 100000
    w_year = 2085
    week_start = f"{w_year}-05-06"
    week_end = f"{w_year}-05-12"

    # Ensure clean state for this specific test week
    import database
    conn = database.connect_database()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM weeks WHERE week_start = ?", (week_start,))
    existing_row = cursor.fetchone()
    if existing_row:
        old_id = existing_row[0]
        cursor.execute("DELETE FROM production_records WHERE week_id = ?", (old_id,))
        cursor.execute("DELETE FROM shift_records WHERE week_id = ?", (old_id,))
        cursor.execute("DELETE FROM salary_deductions WHERE week_id = ?", (old_id,))
        cursor.execute("DELETE FROM salary_bonuses WHERE week_id = ?", (old_id,))
        cursor.execute("DELETE FROM expenses WHERE week_id = ?", (old_id,))
        cursor.execute("DELETE FROM weeks WHERE id = ?", (old_id,))
        conn.commit()
    conn.close()

    week_res = client.post("/weeks", json={"week_start": week_start, "week_end": week_end})
    assert week_res.status_code in (200, 201), f"Failed to create week: {week_res.text}"
    week = week_res.json()
    week_id = week["id"]
    print(f"1. Week created: ID={week_id}, {week['week_start']} to {week['week_end']}")

    # 2. Add production: E001 (B.LAKSHMI) - 100 qty * 2.50 = 250
    prod_payload = {
        "work_date": f"{w_year}-05-07",
        "employee_code": "E001",
        "style_no": "114569",
        "operation_name": "3 PEAK",
        "total_qty": 100.0,
        "rate": 2.50
    }
    prod_res = client.post(f"/weeks/{week_id}/production", json=prod_payload)
    assert prod_res.status_code == 201, f"Failed to add production: {prod_res.text}"
    print(f"2. Production added: E001, 100 qty @ 2.50 = 250")

    # 3. Add shift: E012 (RAVI) - 6 shifts * 500 = 3000
    shift_payload = {
        "work_date": f"{w_year}-05-07",
        "employee_code": "E012",
        "shifts": 6.0,
        "shift_rate": 500.0
    }
    shift_res = client.post(f"/weeks/{week_id}/shift", json=shift_payload)
    assert shift_res.status_code == 201, f"Failed to add shift: {shift_res.text}"
    print(f"3. Shift added: E012, 6 shifts @ 500 = 3000")

    # 4. Add deduction: E001 - 50
    ded_payload = {
        "employee_code": "E001",
        "deduction_type": "Uniform",
        "amount": 50.0,
        "notes": "Uniform deduction"
    }
    ded_res = client.post(f"/weeks/{week_id}/deductions", json=ded_payload)
    assert ded_res.status_code == 201, f"Failed to add deduction: {ded_res.text}"
    print(f"4. Deduction added: E001, 50")

    # 5. Add bonus: E012 - 100
    bon_payload = {
        "employee_code": "E012",
        "bonus_type": "Overtime",
        "amount": 100.0,
        "notes": "Overtime bonus"
    }
    bon_res = client.post(f"/weeks/{week_id}/bonuses", json=bon_payload)
    assert bon_res.status_code == 201, f"Failed to add bonus: {bon_res.text}"
    print(f"5. Bonus added: E012, 100")

    # 6. Add expense: Factory expense - 150
    exp_payload = {
        "category": "TEA/SNACK",
        "amount": 150.0,
        "notes": "Factory refreshments"
    }
    exp_res = client.post(f"/weeks/{week_id}/expenses", json=exp_payload)
    assert exp_res.status_code == 201, f"Failed to add expense: {exp_res.text}"
    print(f"6. Expense added: 150")

    # 7. Calculate salary
    from salary_engine import calculate_weekly_salary
    sal_calc = calculate_weekly_salary(week_id)
    print(f"7. Salary calculated:")
    emp_e001 = [e for e in sal_calc['employees'].values() if e['employee_code'] == 'E001'][0]
    emp_e012 = [e for e in sal_calc['employees'].values() if e['employee_code'] == 'E012'][0]
    print(f"   Piece worker: {emp_e001['employee_code']} / {emp_e001['employee_name']}")
    print(f"   - Gross = {emp_e001['gross_salary']}, Deduction = {emp_e001['deduction']}, Net = {emp_e001['net_salary']}")
    print(f"   Shift worker: {emp_e012['employee_code']} / {emp_e012['employee_name']}")
    print(f"   - Shifts = {emp_e012['total_shifts']}, Gross = {emp_e012['gross_salary']}, Bonus = {emp_e012['bonus']}, Net = {emp_e012['net_salary']}")
    print(f"   Factory expense = {sal_calc['total_factory_expense']}")
    grand_total = emp_e001['net_salary'] + emp_e012['net_salary'] + sal_calc['total_factory_expense']
    print(f"   Grand total = {grand_total}")

    # 8. Generate weekly closing
    closing_res = client.post(f"/weeks/{week_id}/closing")
    assert closing_res.status_code == 200, f"Failed to generate closing: {closing_res.text}"
    closing_data = closing_res.json()
    excel_path = closing_data.get("file_path") or closing_data.get("filePath") or closing_data.get("excel_path")
    print(f"8. Weekly closing generated: {excel_path}")

    # 9. Verify generated Excel with openpyxl
    assert os.path.exists(excel_path), f"Generated file not found on disk: {excel_path}"
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    sheet_names = wb.sheetnames
    print(f"9. Excel workbook verified. Sheets found: {sheet_names}")
    
    # Check sheet contents
    for sheet_name in sheet_names:
        sheet = wb[sheet_name]
        print(f"   Sheet '{sheet_name}': max_row={sheet.max_row}, max_column={sheet.max_column}")

    print("\nSUCCESS: Complete End-to-End Regression Test Passed Successfully!")
    return {
        "week_id": week_id,
        "week_start": week_start,
        "week_end": week_end,
        "emp_e001": emp_e001,
        "emp_e012": emp_e012,
        "factory_expense": sal_calc['total_factory_expense'],
        "grand_total": grand_total,
        "excel_path": excel_path,
        "sheet_names": sheet_names
    }

if __name__ == "__main__":
    run_e2e_regression()
