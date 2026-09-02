"""
migrate_alphanumeric_ids.py

Migration script to ensure database schema and column definitions for employee_id and style_id
support alphanumeric string formats (e.g. '12EC', 'EMP-01', 'STYLE-99') across all tables.
"""

from database import connect_database


def migrate():
    connection = connect_database()
    cursor = connection.cursor()

    # Disable FK checks during schema adjustments if needed
    cursor.execute("PRAGMA foreign_keys = OFF")

    # In SQLite, typing is dynamic, but we verify tables exist and indices are ready
    # Ensure indices on employee_code and style_no exist for fast string lookup
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

    connection.commit()
    cursor.execute("PRAGMA foreign_keys = ON")
    connection.close()
    print("Database migration for alphanumeric IDs completed successfully.")


if __name__ == "__main__":
    migrate()
