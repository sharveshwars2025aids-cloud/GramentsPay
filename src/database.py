
import sqlite3
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent
DATABASE_DIR = PROJECT_ROOT / "database"
DATABASE_PATH = DATABASE_DIR / "garments.db"


VALID_PAY_TYPES = ("PIECE", "SHIFT")
VALID_STATUSES = ("active", "inactive")


def connect_database():

    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, timeout=30.0)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def create_tables(connection):
   
    cursor = connection.cursor()


    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS departments (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            name   TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'active'
                        CHECK(status IN ('active', 'inactive'))
        )
        """
    )


    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS contractors (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT    NOT NULL UNIQUE,
            commission_amount REAL    NOT NULL CHECK(commission_amount > 0),
            status          TEXT    NOT NULL DEFAULT 'active'
                                        CHECK(status IN ('active', 'inactive')),
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
            CREATE TABLE IF NOT EXISTS operations (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            operation_name  TEXT NOT NULL UNIQUE,
            status          TEXT NOT NULL DEFAULT 'active'
                    CHECK(status IN ('active','inactive')),
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


    cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS employees (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_code TEXT UNIQUE,
        name          TEXT NOT NULL UNIQUE,
        pay_type      TEXT NOT NULL
                           CHECK(pay_type IN ('PIECE', 'SHIFT')),
        department_id INTEGER,
        default_operation_id INTEGER,
        contractor_id INTEGER,
        shift_rate    REAL,
        status        TEXT NOT NULL DEFAULT 'active'
                           CHECK(status IN ('active', 'inactive')),
        worker_type   TEXT
                           CHECK(worker_type IN ('HELPER', 'OPERATOR')),
        created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(department_id) REFERENCES departments(id),
        FOREIGN KEY(default_operation_id) REFERENCES operations(id),
        FOREIGN KEY(contractor_id) REFERENCES contractors(id)
    )
    """
)

    
    cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS operation_aliases (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    operation_id INTEGER NOT NULL,

    alias TEXT NOT NULL UNIQUE,

    status TEXT NOT NULL DEFAULT 'active'
        CHECK(status IN ('active','inactive')),

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(operation_id)
        REFERENCES operations(id)
)
    """
)


    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS styles (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            style_no   TEXT NOT NULL UNIQUE,
            style_name TEXT,
            status     TEXT NOT NULL DEFAULT 'active'
                            CHECK(status IN ('active', 'inactive')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS style_operation_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            style_id INTEGER NOT NULL,

            operation_id INTEGER NOT NULL,

            rate REAL NOT NULL,

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(style_id, operation_id),

            FOREIGN KEY(style_id)
            REFERENCES styles(id),

            FOREIGN KEY(operation_id)
            REFERENCES operations(id)
)
        """
    )


    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS weeks (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start        DATE NOT NULL,
            week_end          DATE NOT NULL,
            closing_generated INTEGER NOT NULL DEFAULT 0
                                      CHECK(closing_generated IN (0, 1)),
            created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
            CHECK(week_end >= week_start),
            UNIQUE(week_start, week_end)
        )
        """
    )


    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS production_records (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            week_id       INTEGER,
            work_date     DATE NOT NULL,
            employee_id   INTEGER NOT NULL,
            style_id      INTEGER NOT NULL,
            operation_id  INTEGER,
            type          TEXT,
            color         TEXT,
            total_qty     REAL    NOT NULL DEFAULT 0,
            rate          REAL    NOT NULL DEFAULT 0,
            total_amount  REAL    NOT NULL DEFAULT 0,
            source_sheet  TEXT,
            workbook_name TEXT,
            source_row    INTEGER,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(week_id)      REFERENCES weeks(id),
            FOREIGN KEY(employee_id)  REFERENCES employees(id),
            FOREIGN KEY(style_id)     REFERENCES styles(id),
            FOREIGN KEY(operation_id) REFERENCES operations(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS production_sizes (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            production_record_id INTEGER NOT NULL,
            size_name            TEXT    NOT NULL,
            qty                  REAL    NOT NULL DEFAULT 0,
            FOREIGN KEY(production_record_id) REFERENCES production_records(id),
            UNIQUE(production_record_id, size_name)
        )
        """
    )

    cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS shift_records (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,

        week_id      INTEGER,
        work_date    DATE NOT NULL,

        employee_id  INTEGER NOT NULL,

        style_id     INTEGER,
        operation_id INTEGER,

        type         TEXT,
        color        TEXT,
        item         TEXT,

        shifts       REAL NOT NULL DEFAULT 0
                           CHECK(shifts >= 0),

        shift_rate   REAL NOT NULL DEFAULT 0
                           CHECK(shift_rate >= 0),

        daily_salary REAL NOT NULL DEFAULT 0
                           CHECK(daily_salary >= 0),

        source_sheet  TEXT,
        workbook_name TEXT,
        source_row    INTEGER,

        created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(week_id)
            REFERENCES weeks(id),

        FOREIGN KEY(employee_id)
            REFERENCES employees(id),

        FOREIGN KEY(style_id)
            REFERENCES styles(id),

        FOREIGN KEY(operation_id)
            REFERENCES operations(id),

        UNIQUE(
            week_id,
            employee_id,
            work_date,
            style_id,
            operation_id,
            item
        )
    )
    """
)

 
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS deductions (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            week_id        INTEGER NOT NULL,
            employee_id    INTEGER NOT NULL,
            deduction_type TEXT    NOT NULL,
            amount         REAL    NOT NULL CHECK(amount > 0),
            notes          TEXT,
            created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(week_id)     REFERENCES weeks(id),
            FOREIGN KEY(employee_id) REFERENCES employees(id)
        )
        """
    )


    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS bonuses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            week_id     INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            bonus_type  TEXT    NOT NULL,
            amount      REAL    NOT NULL CHECK(amount > 0),
            notes       TEXT,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(week_id)     REFERENCES weeks(id),
            FOREIGN KEY(employee_id) REFERENCES employees(id)
        )
        """
    )


    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            week_id    INTEGER NOT NULL,
            category   TEXT    NOT NULL,
            amount     REAL    NOT NULL CHECK(amount > 0),
            notes      TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(week_id) REFERENCES weeks(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS bank_transfers (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        week_id INTEGER NOT NULL,

        employee_id INTEGER NOT NULL,

        amount REAL NOT NULL,

        status TEXT DEFAULT 'PENDING',

        transaction_reference TEXT,

        account_no TEXT,

        ifsc TEXT,

        remarks TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (week_id)
        REFERENCES weeks(id),

        FOREIGN KEY (employee_id)
        REFERENCES employees(id)

        )
        """
    )

    cursor.execute(
        """
       CREATE TABLE IF NOT EXISTS outsource_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            week_id INTEGER NOT NULL,

            style TEXT NOT NULL,

            item TEXT NOT NULL,

            qty REAL NOT NULL DEFAULT 0,

            rate REAL NOT NULL DEFAULT 0,

            amount REAL NOT NULL DEFAULT 0,

            centre_name TEXT,

            remarks TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (week_id)
            REFERENCES weeks(id)

        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS security_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            week_id INTEGER NOT NULL,

            employee_id INTEGER NOT NULL,

            days REAL NOT NULL DEFAULT 0,

            amount REAL NOT NULL DEFAULT 0,

            remarks TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (week_id)
                REFERENCES weeks(id),

            FOREIGN KEY (employee_id)
                REFERENCES employees(id)
        )
    """
)

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS weekly_closings (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            week_id      INTEGER NOT NULL UNIQUE,
            generated_by TEXT,
            generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            file_path    TEXT,
            FOREIGN KEY(week_id) REFERENCES weeks(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS biometric_attendance (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            week_id              INTEGER NOT NULL,
            employee_id          INTEGER NOT NULL,
            work_date            DATE NOT NULL,
            tap_in_time          DATETIME,
            tap_out_time         DATETIME,
            computed_shift_value REAL,
            device_id            TEXT,
            source_file          TEXT,
            created_at           DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(week_id)     REFERENCES weeks(id),
            FOREIGN KEY(employee_id) REFERENCES employees(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance_overrides (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            week_id               INTEGER NOT NULL,
            employee_id           INTEGER NOT NULL,
            work_date             DATE NOT NULL,
            biometric_shift_value REAL,
            entered_shift_value   REAL,
            overridden_by         TEXT NOT NULL,
            overridden_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
            reason                TEXT,
            FOREIGN KEY(week_id)     REFERENCES weeks(id),
            FOREIGN KEY(employee_id) REFERENCES employees(id)
        )
        """
    )




def create_indexes(connection):

    cursor = connection.cursor()

 
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_employee_name
        ON employees(name)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_employee_code
        ON employees(employee_code)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_style_no
        ON styles(style_no)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_work_date
        ON production_records(work_date)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_week_dates
        ON weeks(week_start, week_end)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_shift_employee
        ON shift_records(employee_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_production_employee
        ON production_records(employee_id)
        """
    )


    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_production_week
        ON production_records(week_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_shift_week
        ON shift_records(week_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_bonus_week
        ON bonuses(week_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_deduction_week
        ON deductions(week_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_expense_week
        ON expenses(week_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_bank_transfer_week
        ON bank_transfers(week_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_bank_transfer_employee
        ON bank_transfers(employee_id)
        """
    ) 

    cursor.execute(
    """
    CREATE INDEX IF NOT EXISTS idx_operation_alias
    ON operation_aliases(alias)
    """
)

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_outsource_week
        ON outsource_payments(week_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_security_week
        ON security_payments(week_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_biometric_week_employee
        ON biometric_attendance(week_id, employee_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_overrides_week_employee
        ON attendance_overrides(week_id, employee_id)
        """
    )




def initialize_database():

    connection = connect_database()
    create_tables(connection)
    create_indexes(connection)
    connection.commit()
    connection.close()


def get_employee_id_by_code(connection, employee_code):
    if employee_code is None:
        return None
    raw = str(employee_code).strip()
    if not raw:
        return None
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id FROM employees WHERE id = ? OR LOWER(TRIM(employee_code)) = LOWER(?)",
        (raw, raw),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def get_style_id_by_number(connection, style_no):
    if style_no is None:
        return None
    raw = str(style_no).strip()
    if not raw:
        return None
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id FROM styles WHERE id = ? OR LOWER(TRIM(style_no)) = LOWER(?)",
        (raw, raw),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def get_operation_id_by_name(connection, operation_name):
    if operation_name is None:
        return None
    raw = str(operation_name).strip()
    if not raw:
        return None
    cursor = connection.cursor()
    # Check primary operations table first
    cursor.execute(
        "SELECT id FROM operations WHERE id = ? OR LOWER(TRIM(operation_name)) = LOWER(?)",
        (raw, raw),
    )
    row = cursor.fetchone()
    if row:
        return row[0]
    # Check operation aliases table
    cursor.execute(
        "SELECT operation_id FROM operation_aliases WHERE LOWER(TRIM(alias)) = LOWER(?) AND status = 'active'",
        (raw,),
    )
    row_alias = cursor.fetchone()
    return row_alias[0] if row_alias else None


def get_week_id(connection, week_start, week_end):
    if not week_start or not week_end:
        return None
    w_start = str(week_start).strip()
    w_end = str(week_end).strip()
    if not w_start or not w_end:
        return None
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id FROM weeks WHERE TRIM(week_start) = ? AND TRIM(week_end) = ?",
        (w_start, w_end)
    )
    row = cursor.fetchone()
    return row[0] if row else None


def get_week_by_id(connection, week_id):
    if week_id is None:
        return None
    try:
        w_id = int(week_id)
    except (ValueError, TypeError):
        return None
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id, week_start, week_end, closing_generated, created_at FROM weeks WHERE id = ?",
        (w_id,)
    )
    row = cursor.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "week_start": row[1],
        "week_end": row[2],
        "closing_generated": row[3],
        "created_at": row[4]
    }


def get_department_id_by_name(connection, name):
    if not name or not isinstance(name, str):
        return None
    dept_name = name.strip()
    if not dept_name:
        return None
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id FROM departments WHERE LOWER(TRIM(name)) = LOWER(?)",
        (dept_name,)
    )
    row = cursor.fetchone()
    return row[0] if row else None


def get_contractor_id_by_name(connection, name):
    if not name or not isinstance(name, str):
        return None
    c_name = name.strip()
    if not c_name:
        return None
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id FROM contractors WHERE LOWER(TRIM(name)) = LOWER(?)",
        (c_name,)
    )
    row = cursor.fetchone()
    return row[0] if row else None


if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully.")