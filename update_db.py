import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

# Add assigned_staff column
try:
    cur.execute("""
    ALTER TABLE complaints
    ADD COLUMN assigned_staff TEXT
    """)
    print("assigned_staff column added ✅")

except:
    print("Column already exists ✅")

conn.commit()
conn.close()