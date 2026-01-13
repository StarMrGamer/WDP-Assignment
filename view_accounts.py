"""
Simple script to view all user accounts in the database
Usage: python view_accounts.py
"""
import sqlite3
import os

# Connect to database
db_path = os.path.join(os.path.dirname(__file__), 'database.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get table structure
cursor.execute('PRAGMA table_info(users)')
columns = cursor.fetchall()

print("=" * 80)
print("GENCON SG - USER ACCOUNTS")
print("=" * 80)

# Get all users
cursor.execute('SELECT * FROM users')
users = cursor.fetchall()

print(f"\nTotal Accounts: {len(users)}\n")

if users:
    for user in users:
        print("-" * 80)
        for i, col in enumerate(columns):
            col_name = col[1]
            value = user[i]

            # Don't display password hash for security
            if col_name == 'password_hash':
                value = '[HIDDEN]'

            print(f"{col_name:20s}: {value}")
        print("-" * 80)
        print()
else:
    print("No accounts found in database.\n")

conn.close()
