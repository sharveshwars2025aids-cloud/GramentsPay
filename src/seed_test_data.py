from database import connect_database


# ==========================================================
# TEST DATA
# ==========================================================

DEPARTMENTS = [
    "POWERTABLE",
    "POWER",
    "SINGER",
    "CHECKING",
    "IRONING",
]


# Existing piece-rate employees
# Existing + workbook piece-rate employees
PIECE_EMPLOYEES = [
    ("E001", "B.LAKSHMI"),
    ("E002", "CHANDRASEKAR"),
    ("E003", "JAYAMANI"),
    ("E004", "KALIAPPAN"),
    ("E005", "LOGANAYAKI"),
    ("E006", "MAHESWARI"),
    ("E007", "MANOHAR"),
    ("E008", "SELVARAJ"),
    ("E009", "SELVARANI"),
    ("E010", "SENTHIL KUMAR"),
    ("E011", "UMA"),

    # Employees found in daily workbook
    ("E016", "GOVINDASAMY"),
    ("E017", "KAMALA"),
    ("E018", "KARTHIK"),
    ("E019", "KUMARESAN"),
    ("E020", "LAKSHMI"),
    ("E021", "MANI"),
    ("E022", "MURUGAN"),
    ("E023", "MUTHU"),
    ("E024", "PALANI"),
    ("E025", "RAJENDRAN"),
    ("E026", "RAJI"),
    ("E027", "RAMESH"),
    ("E028", "SARASWATHI"),
    ("E029", "SELVAM"),
    ("E030", "SHANMUGAM"),
    ("E031", "THANGAM"),
    ("E032", "VIJAYA"),
]


# ==========================================================
# SHIFT WORKERS
# ==========================================================

# Company shift workers
COMPANY_SHIFT_EMPLOYEES = [
    ("E012", "RAVI", 500),
    ("E013", "KUMAR", 550),
]


# Contractor shift workers
CONTRACTOR_SHIFT_EMPLOYEES = [
    ("E014", "ARUN", 450),
    ("E015", "SURESH", 450),
]


# ==========================================================
# CONTRACTORS
# ==========================================================

CONTRACTORS = [
    ("CONTRACTOR A", 10),
]


# ==========================================================
# STYLES / ITEMS
# ==========================================================

STYLES = [
    "114569",
    "CVC",
    "K55-A6-30-402",
    "PE004A25",
    "PE203PPA25",
    "PEP004A25",
    "PEPX031A25",
    "PEPX032A25",
    "PEPX033A25",
    "PEPX033S25",
    "PEV010S26",
    "PXSR004A25",
    "R & B",
    "PE004A25 - PANT",
      "PE004A25 - ROMPER",
      "PE004A25 - S.SUIT",
      "PE004A25 - SHORTS",
      "PE004A25 - TOP",
      "PE203PPA25 - PANT",
      "PE203PPA25 - ROMPER",
      "PE203PPA25 - S.SUIT",
      "PE203PPA25 - TOP",
      "PEP004A25 - PANT",
      "PEP004A25 - S.SUIT",
      "PEP004A25 - TOP",
      "PEPX031A25 - ROMPER",
      "PEPX031A25 - S.SUIT",
      "PEPX031A25 - TOP",
      "PEPX032A25 - PANT",
      "PEPX032A25 - ROMPER",
      "PEPX032A25 - S.SUIT",
      "PEPX032A25 - SHORTS",
      "PEPX033A25 - ROMPER",
      "PEPX033A25 - S.SUIT",
      "PEPX033A25 - SHORTS",
      "PEPX033A25 - TOP",
      "PXSR004A25 - PANT",
      "PXSR004A25 - S.SUIT",
      "PXSR004A25 - TOP",
      "R & B - ROMPER",
      "R & B - S.SUIT",
      "R & B - SHORTS",
      "PEP004A25 - ROMPER",
      "PEPX031A25 - PANT",
      "PEPX031A25 - SHORTS",
      "PEPX032A25 - TOP",
      "PXSR004A25 - ROMPER",
      "PXSR004A25 - SHORTS",
      "R & B - PANT",
      "R & B - TOP"
]


# ==========================================================
# OPERATIONS
# ==========================================================

OPERATIONS = [
    "3 PEAK",
    "4 PEAK",
    "6 PEAK",
    "BACK S/N",
    "BODY TOWER",
    "Bottom Hem",
    "CROTCH FOLDG",
    "Checking",
    "Final Checking",
    "Folding & Packing",
    "General Power Table Work",
    "Ironing",
    "LEG TOWER",
    "Label Attach",
    "Line Support",
    "Machine Assist",
    "Measurement Check",
    "NECK +U FOLG",
    "NECK FOLG",
    "Overlock",
    "Overlock Assist",
    "PATTI F/L",
    "POCKET S/N",
    "Pocket Attach",
    "Quality Check",
    "SLEEVE ELS CVRG",
    "Side Seam",
    "Sleeve Attach",
    "Steam Press",
    "Waist Band",
     "NECK+BOTTOM FOLG",
]


# ==========================================================
# DEPARTMENTS
# ==========================================================

def seed_departments(connection):

    cursor = connection.cursor()

    for department_name in DEPARTMENTS:

        cursor.execute(
            """
            SELECT id
            FROM departments
            WHERE UPPER(name) = UPPER(?)
            """,
            (department_name,),
        )

        if cursor.fetchone() is not None:
            print(f"Department already exists: {department_name}")
            continue

        cursor.execute(
            """
            INSERT INTO departments (
                name,
                status
            )
            VALUES (?, ?)
            """,
            (
                department_name,
                "active",
            ),
        )

        print(f"Added department: {department_name}")


# ==========================================================
# CONTRACTORS
# ==========================================================

def seed_contractors(connection):

    cursor = connection.cursor()

    for contractor_name, commission_amount in CONTRACTORS:

        cursor.execute(
            """
            SELECT id
            FROM contractors
            WHERE UPPER(name) = UPPER(?)
            """,
            (contractor_name,),
        )

        if cursor.fetchone() is not None:
            print(f"Contractor already exists: {contractor_name}")
            continue

        cursor.execute(
            """
            INSERT INTO contractors (
                name,
                commission_amount,
                status
            )
            VALUES (?, ?, ?)
            """,
            (
                contractor_name,
                commission_amount,
                "active",
            ),
        )

        print(
            f"Added contractor: "
            f"{contractor_name}"
        )


# ==========================================================
# OPERATIONS
# ==========================================================

def seed_operations(connection):

    cursor = connection.cursor()

    for operation_name in OPERATIONS:

        cursor.execute(
            """
            SELECT id
            FROM operations
            WHERE UPPER(operation_name) = UPPER(?)
            """,
            (operation_name,),
        )

        if cursor.fetchone() is not None:
            print(f"Operation already exists: {operation_name}")
            continue

        cursor.execute(
            """
            INSERT INTO operations (
                operation_name,
                status
            )
            VALUES (?, ?)
            """,
            (
                operation_name,
                "active",
            ),
        )

        print(f"Added operation: {operation_name}")


# ==========================================================
# STYLES
# ==========================================================

def seed_styles(connection):

    cursor = connection.cursor()

    for style_no in STYLES:

        cursor.execute(
            """
            SELECT id
            FROM styles
            WHERE UPPER(style_no) = UPPER(?)
            """,
            (style_no,),
        )

        if cursor.fetchone() is not None:
            print(f"Style already exists: {style_no}")
            continue

        cursor.execute(
            """
            INSERT INTO styles (
                style_no,
                style_name,
                status
            )
            VALUES (?, ?, ?)
            """,
            (
                style_no,
                "Test Style",
                "active",
            ),
        )

        print(f"Added style: {style_no}")


# ==========================================================
# PIECE EMPLOYEES
# ==========================================================

def seed_piece_employees(connection):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM departments
        WHERE UPPER(name) = UPPER(?)
        """,
        ("POWER",),
    )

    department_row = cursor.fetchone()

    if department_row is None:
        raise RuntimeError(
            "POWER department was not found."
        )

    power_department_id = department_row[0]

    for employee_code, name in PIECE_EMPLOYEES:

        cursor.execute(
            """
            SELECT id
            FROM employees
            WHERE employee_code = ?
               OR UPPER(name) = UPPER(?)
            """,
            (
                employee_code,
                name,
            ),
        )

        if cursor.fetchone() is not None:
            print(f"Employee already exists: {name}")
            continue

        cursor.execute(
            """
            INSERT INTO employees (
                employee_code,
                name,
                pay_type,
                department_id,
                default_operation_id,
                contractor_id,
                shift_rate,
                worker_type
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                employee_code,
                name,
                "PIECE",
                power_department_id,
                None,
                None,
                None,
                "OPERATOR",
            ),
        )

        print(
            f"Added piece employee: "
            f"{employee_code} - {name}"
        )


# ==========================================================
# SHIFT EMPLOYEES
# ==========================================================

def seed_shift_employees(connection):

    cursor = connection.cursor()

    # ------------------------------------------
    # POWERTABLE DEPARTMENT
    # ------------------------------------------

    cursor.execute(
        """
        SELECT id
        FROM departments
        WHERE UPPER(name) = UPPER(?)
        """,
        ("POWERTABLE",),
    )

    department_row = cursor.fetchone()

    if department_row is None:
        raise RuntimeError(
            "POWERTABLE department was not found."
        )

    power_table_department_id = department_row[0]

    # ------------------------------------------
    # CONTRACTOR
    # ------------------------------------------

    cursor.execute(
        """
        SELECT id
        FROM contractors
        WHERE UPPER(name) = UPPER(?)
        """,
        ("CONTRACTOR A",),
    )

    contractor_row = cursor.fetchone()

    if contractor_row is None:
        raise RuntimeError(
            "CONTRACTOR A was not found."
        )

    contractor_id = contractor_row[0]

    # ------------------------------------------
    # COMPANY WORKERS
    # ------------------------------------------

    for employee_code, name, shift_rate in COMPANY_SHIFT_EMPLOYEES:

        cursor.execute(
            """
            SELECT id
            FROM employees
            WHERE employee_code = ?
               OR UPPER(name) = UPPER(?)
            """,
            (
                employee_code,
                name,
            ),
        )

        if cursor.fetchone() is not None:
            print(f"Employee already exists: {name}")
            continue

        cursor.execute(
            """
            INSERT INTO employees (
                employee_code,
                name,
                pay_type,
                department_id,
                default_operation_id,
                contractor_id,
                shift_rate,
                worker_type
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                employee_code,
                name,
                "SHIFT",
                power_table_department_id,
                None,
                None,
                shift_rate,
                "OPERATOR",
            ),
        )

        print(
            f"Added company shift worker: "
            f"{employee_code} - {name}"
        )

    # ------------------------------------------
    # CONTRACTOR WORKERS
    # ------------------------------------------

    for employee_code, name, shift_rate in CONTRACTOR_SHIFT_EMPLOYEES:

        cursor.execute(
            """
            SELECT id
            FROM employees
            WHERE employee_code = ?
               OR UPPER(name) = UPPER(?)
            """,
            (
                employee_code,
                name,
            ),
        )

        if cursor.fetchone() is not None:
            print(f"Employee already exists: {name}")
            continue

        cursor.execute(
            """
            INSERT INTO employees (
                employee_code,
                name,
                pay_type,
                department_id,
                default_operation_id,
                contractor_id,
                shift_rate,
                worker_type
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                employee_code,
                name,
                "SHIFT",
                power_table_department_id,
                None,
                contractor_id,
                shift_rate,
                "OPERATOR",
            ),
        )

        print(
            f"Added contractor shift worker: "
            f"{employee_code} - {name}"
        )


# ==========================================================
# WEEK
# ==========================================================

def seed_week(connection):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM weeks
        WHERE week_start = ?
          AND week_end = ?
        """,
        (
            "2026-07-06",
            "2026-07-12",
        ),
    )

    row = cursor.fetchone()

    if row is not None:
        print(f"Week already exists: ID {row[0]}")
        return

    cursor.execute(
        """
        INSERT INTO weeks (
            week_start,
            week_end
        )
        VALUES (?, ?)
        """,
        (
            "2026-07-06",
            "2026-07-12",
        ),
    )

    print("Added test Week 1")


# ==========================================================
# MAIN
# ==========================================================

def main():

    connection = connect_database()

    try:

        print("=" * 60)
        print("SEEDING TEST DATA")
        print("=" * 60)

        # ------------------------------------------
        # BASE DATA
        # ------------------------------------------

        seed_departments(connection)

        print()

        seed_contractors(connection)

        print()

        seed_operations(connection)

        print()

        seed_styles(connection)

        print()

        # ------------------------------------------
        # EMPLOYEES
        # ------------------------------------------

        seed_piece_employees(connection)

        print()

        seed_shift_employees(connection)

        print()

        # ------------------------------------------
        # WEEK
        # ------------------------------------------

        seed_week(connection)

        connection.commit()

        print()
        print("=" * 60)
        print("TEST DATA SEEDED SUCCESSFULLY")
        print("=" * 60)

    except Exception as error:

        connection.rollback()

        print()
        print("=" * 60)
        print("SEEDING FAILED")
        print("=" * 60)
        print(error)

        raise

    finally:

        connection.close()


if __name__ == "__main__":
    main()

