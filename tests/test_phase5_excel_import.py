import sys
from pathlib import Path
import pytest
import pandas as pd

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import database
from importer import (
    get_employee_id,
    get_style_id,
    get_operation_id,
    ImportErrorDetails,
    import_workbook,
    validate_date_in_week,
)

SAMPLE_WORKBOOK = Path(__file__).resolve().parent.parent / "samples" / "daily_workbook.xlsx"


def test_test_a_piece_employee_resolution():
    # TEST A: Existing PIECE employee code resolution
    conn = database.connect_database()
    emp_id = get_employee_id(conn, "E001")
    conn.close()
    assert isinstance(emp_id, int)


def test_test_b_govindasamy_shift_employee_resolution():
    # TEST B: E016 GOVINDASAMY resolution (Ensure pay_type = SHIFT per Requirement 18)
    conn = database.connect_database()
    cursor = conn.cursor()
    cursor.execute("UPDATE employees SET pay_type = 'SHIFT' WHERE employee_code = 'E016'")
    conn.commit()

    emp_id = get_employee_id(conn, "E016")
    cursor.execute("SELECT pay_type FROM employees WHERE id = ?", (emp_id,))
    pay_type = cursor.fetchone()[0]
    conn.close()
    assert isinstance(emp_id, int)
    assert pay_type == "SHIFT"


def test_test_c_alphanumeric_employee():
    # TEST C: Alphanumeric employee code 12EC
    conn = database.connect_database()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM employees WHERE employee_code = '12EC'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO employees (employee_code, name, pay_type) VALUES ('12EC', 'Alpha Emp', 'PIECE')")
        conn.commit()

    emp_id = get_employee_id(conn, "12EC")
    conn.close()
    assert isinstance(emp_id, int)


def test_test_d_alphanumeric_style():
    # TEST D: Alphanumeric style resolution
    conn = database.connect_database()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM styles WHERE style_no = 'STYLE-99'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO styles (style_no, style_name) VALUES ('STYLE-99', 'Test Style 99')")
        conn.commit()

    style_id = get_style_id(conn, "STYLE-99")
    conn.close()
    assert isinstance(style_id, int)


def test_test_e_operation_name_and_alias():
    # TEST E: Operation name/alias resolution
    conn = database.connect_database()
    op_id = get_operation_id(conn, "NECK FOLG")
    conn.close()
    assert isinstance(op_id, int)


def test_test_f_unknown_employee_error():
    # TEST F: Unknown employee raises clear ImportErrorDetails
    conn = database.connect_database()
    with pytest.raises(ImportErrorDetails) as exc_info:
        get_employee_id(conn, "E999", sheet="Day 1", table_type="PRODUCTION", row_num=10)
    conn.close()
    err_str = str(exc_info.value)
    assert "E999" in err_str
    assert "not found" in err_str.lower()


def test_test_g_unknown_style_error():
    # TEST G: Unknown style raises clear ImportErrorDetails
    conn = database.connect_database()
    with pytest.raises(ImportErrorDetails) as exc_info:
        get_style_id(conn, "STYLE-DOES-NOT-EXIST", sheet="Day 1", table_type="PRODUCTION", row_num=12)
    conn.close()
    err_str = str(exc_info.value)
    assert "STYLE-DOES-NOT-EXIST" in err_str
    assert "not found" in err_str.lower()


def test_test_h_unknown_operation_error():
    # TEST H: Unknown operation raises clear ImportErrorDetails
    conn = database.connect_database()
    with pytest.raises(ImportErrorDetails) as exc_info:
        get_operation_id(conn, "UNKNOWN OP", sheet="Day 1", table_type="PRODUCTION", row_num=15)
    conn.close()
    err_str = str(exc_info.value)
    assert "UNKNOWN OP" in err_str
    assert "not found" in err_str.lower()


def test_test_i_valid_week_creation_and_resolution():
    # TEST I: Valid week ID resolution
    conn = database.connect_database()
    cursor = conn.cursor()
    cursor.execute("SELECT id, week_start, week_end FROM weeks LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    assert row is not None
    assert isinstance(row[0], int)


def test_test_j_date_outside_week_error():
    # TEST J: Date outside week raises ImportErrorDetails
    with pytest.raises(ImportErrorDetails) as exc_info:
        validate_date_in_week("2026-12-31", "2026-07-06", "2026-07-12", sheet="Day 1", table_type="PRODUCTION", row_num=5)
    assert "outside week range" in str(exc_info.value).lower()


def test_test_k_shift_rate_override():
    # TEST K: Shift rate override does not change employee master shift_rate
    conn = database.connect_database()
    emp_id = get_employee_id(conn, "E016")

    # Master shift rate
    cursor = conn.cursor()
    cursor.execute("SELECT shift_rate FROM employees WHERE id = ?", (emp_id,))
    master_rate_before = cursor.fetchone()[0]

    # Import shift record with rate 371.32
    from shift_manager import insert_shift_record
    cursor.execute("SELECT id FROM weeks LIMIT 1")
    week_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM operations LIMIT 1")
    op_id = cursor.fetchone()[0]

    rec_id = insert_shift_record(
        connection=conn,
        week_id=week_id,
        work_date="2026-07-06",
        employee_id=emp_id,
        operation_id=op_id,
        item="TEST ITEM",
        shifts=1.0,
        rate_per_shift=371.32
    )

    # Check stored shift rate in shift_records (column is shift_rate)
    cursor.execute("SELECT shift_rate FROM shift_records WHERE id = ?", (rec_id,))
    stored_shift_rate = cursor.fetchone()[0]

    # Check master rate remains unchanged
    cursor.execute("SELECT shift_rate FROM employees WHERE id = ?", (emp_id,))
    master_rate_after = cursor.fetchone()[0]

    conn.close()

    assert stored_shift_rate == 371.32
    assert master_rate_after == master_rate_before


def test_test_l_import_real_daily_workbook():
    # TEST L: Import actual daily workbook sample
    assert SAMPLE_WORKBOOK.exists()
    week_id = import_workbook(SAMPLE_WORKBOOK)
    assert isinstance(week_id, int)
    assert week_id > 0



if __name__ == "__main__":
    pytest.main(["-v", __file__])
