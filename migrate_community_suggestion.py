import sqlite3

conn = sqlite3.connect('database.db')
cur = conn.cursor()

cur.execute("PRAGMA table_info(communities)")
columns = [row[1] for row in cur.fetchall()]

if 'status' not in columns:
    cur.execute("ALTER TABLE communities ADD COLUMN status VARCHAR(20) DEFAULT 'active'")
    conn.commit()
    print("[OK] status column added to communities.")
else:
    print("[OK] status column already exists.")

if 'justification' not in columns:
    cur.execute("ALTER TABLE communities ADD COLUMN justification TEXT")
    conn.commit()
    print("[OK] justification column added to communities.")
else:
    print("[OK] justification column already exists.")

conn.close()
