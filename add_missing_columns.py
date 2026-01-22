from app import app, db
from sqlalchemy import text
import sys

with app.app_context():
    print("Adding missing columns to 'users' table...")
    
    with db.engine.connect() as conn:
        trans = conn.begin()
        try:
            # Add 'bio' column
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN bio TEXT"))
                print("- Added 'bio' column.")
            except Exception as e:
                # Check for various forms of "column already exists" errors across DB drivers
                err_str = str(e).lower()
                if "duplicate column" in err_str or "already exists" in err_str:
                    print("- 'bio' column already exists.")
                else:
                    print(f"- Error adding 'bio': {e}")

            # Add 'school' column
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN school VARCHAR(255)"))
                print("- Added 'school' column.")
            except Exception as e:
                err_str = str(e).lower()
                if "duplicate column" in err_str or "already exists" in err_str:
                    print("- 'school' column already exists.")
                else:
                    print(f"- Error adding 'school': {e}")
            
            trans.commit()
            print("Database update complete.")
            
        except Exception as e:
            trans.rollback()
            print(f"Transaction failed: {e}")
