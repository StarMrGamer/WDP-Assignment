"""
Create test accounts for all roles and remove old account
"""
import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

# Connect to database
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Delete the old "text" account
print("Removing old 'text' account...")
cursor.execute('DELETE FROM users WHERE username = ?', ('text',))
print("[OK] Removed\n")

# Test accounts to create
test_accounts = [
    {
        'username': 'senior1',
        'password': 'senior123',
        'email': 'senior1@gencon.sg',
        'full_name': 'Margaret Tan',
        'phone': '91234567',
        'age': 65,
        'role': 'senior',
        'profile_picture': 'default-avatar.png',
        'accessibility_settings_json': '{"font_size": "large", "high_contrast": false, "color_blind_friendly": false}'
    },
    {
        'username': 'youth1',
        'password': 'youth123',
        'email': 'youth1@gencon.sg',
        'full_name': 'Ryan Lee',
        'phone': '82345678',
        'age': 20,
        'role': 'youth',
        'profile_picture': 'default-avatar.png',
        'accessibility_settings_json': '{"font_size": "normal", "high_contrast": false, "color_blind_friendly": false}'
    },
    {
        'username': 'admin1',
        'password': 'admin123',
        'email': 'admin1@gencon.sg',
        'full_name': 'System Administrator',
        'phone': '93456789',
        'age': 30,
        'role': 'admin',
        'profile_picture': 'default-avatar.png',
        'accessibility_settings_json': '{"font_size": "normal", "high_contrast": false, "color_blind_friendly": false}'
    }
]

print("Creating test accounts...\n")
print("=" * 80)

for account in test_accounts:
    # Hash the password
    password = account.pop('password')
    password_hash = generate_password_hash(password)

    # Insert user
    cursor.execute('''
        INSERT INTO users (
            username, password_hash, email, full_name, phone, age, role,
            profile_picture, accessibility_settings_json, created_at, last_active, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        account['username'],
        password_hash,
        account['email'],
        account['full_name'],
        account['phone'],
        account['age'],
        account['role'],
        account['profile_picture'],
        account['accessibility_settings_json'],
        datetime.now(),
        datetime.now(),
        1
    ))

    print(f"[OK] Created {account['role'].upper()} account:")
    print(f"  Username: {account['username']}")
    print(f"  Password: {password}")
    print(f"  Email: {account['email']}")
    print(f"  Full Name: {account['full_name']}")
    print(f"  Age: {account['age']}")
    print("-" * 80)

# Commit changes
conn.commit()

# Show final count
cursor.execute('SELECT COUNT(*) FROM users')
total = cursor.fetchone()[0]

print(f"\n[OK] Setup complete! Total accounts: {total}")
print("=" * 80)

conn.close()
