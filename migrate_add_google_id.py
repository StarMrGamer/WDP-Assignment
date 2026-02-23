import sqlite3

conn = sqlite3.connect('database.db')
cur = conn.cursor()

# Check if column already exists
cur.execute("PRAGMA table_info(users)")
columns = [row[1] for row in cur.fetchall()]

if 'google_id' not in columns:
    cur.execute("ALTER TABLE users ADD COLUMN google_id VARCHAR(255)")
    conn.commit()
    print("[OK] google_id column added successfully.")
else:
    print("[OK] google_id column already exists, nothing to do.")

conn.close()
