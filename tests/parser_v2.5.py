
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
    connection = sqlite3.connect(DATABASE_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
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
            commission_rate REAL    NOT NULL CHECK(commission_rate > 0),
            status          TEXT    NOT NULL DEFAULT 'active'
                                        CHECK(status IN ('active', 'inactive')),
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
            contractor_id INTEGER,
            shift_rate    REAL,
            status        TEXT NOT NULL DEFAULT 'active'
                               CHECK(status IN ('active', 'inactive')),
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(department_id) REFERENCES departments(id),
            FOREIGN KEY(contractor_id) REFERENCES contractors(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS operations (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL UNIQUE,
            status     TEXT NOT NULL DEFAULT 'active'
                            CHECK(status IN ('active', 'inactive')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            style_id       INTEGER NOT NULL,
            operation_id   INTEGER NOT NULL,
            rate           REAL    NOT NULL CHECK(rate > 0),
            effective_from DATE,
            active         INTEGER NOT NULL DEFAULT 1
                                   CHECK(active IN (0, 1)),
            FOREIGN KEY(style_id)     REFERENCES styles(id),
            FOREIGN KEY(operation_id) REFERENCES operations(id),
            UNIQUE(style_id, operation_id, effective_from)
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
            shifts       REAL NOT NULL DEFAULT 0 CHECK(shifts >= 0),
            daily_salary REAL NOT NULL DEFAULT 0 CHECK(daily_salary >= 0),
            created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(week_id)     REFERENCES weeks(id),
            FOREIGN KEY(employee_id) REFERENCES employees(id),
            UNIQUE(week_id, employee_id, work_date)
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



def initialize_database():

    connection = connect_database()
    create_tables(connection)
    create_indexes(connection)
    connection.commit()
    connection.close()


if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully.")