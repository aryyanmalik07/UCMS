import sqlite3

def create_db():

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # ================= USERS TABLE =================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT,
        password TEXT,
        role TEXT
    )
    """)

    # ================= COMPLAINTS TABLE =================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        description TEXT,
        category TEXT,
        priority TEXT,
        department TEXT,
        status TEXT DEFAULT 'Pending',
        assigned_staff TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

    print("Database Created Successfully 🚀")

if __name__ == "__main__":
    create_db()