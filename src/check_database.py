import sqlite3

connection = sqlite3.connect("database/garments.db")
cursor = connection.cursor()

print("\n=== TABLES ===")

tables = cursor.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
ORDER BY name
""").fetchall()

for table in tables:
    print(table[0])

print("\n=== EMPLOYEES SCHEMA ===")

for row in cursor.execute("""
PRAGMA table_info(employees)
"""):
    print(row)

print("\n=== OPERATIONS SCHEMA ===")

for row in cursor.execute("""
PRAGMA table_info(operations)
"""):
    print(row)

print("\n=== OPERATION ALIASES SCHEMA ===")

for row in cursor.execute("""
PRAGMA table_info(operation_aliases)
"""):
    print(row)

connection.close()