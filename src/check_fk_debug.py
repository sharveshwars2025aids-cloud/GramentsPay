import sqlite3

conn = sqlite3.connect("src/database/garments.db")
c = conn.cursor()

# Find all records in weeks 146 through 158
print("Record 710 in production_records:")
c.execute("SELECT * FROM production_records WHERE id=710")
print(c.fetchall())

print("Record 711 in production_records:")
c.execute("SELECT * FROM production_records WHERE id=711")
print(c.fetchall())

conn.close()
