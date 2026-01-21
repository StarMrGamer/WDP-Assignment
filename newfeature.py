from app import app, db
from sqlalchemy import text

with app.app_context():
    print("Adding 'disable_reason' column to 'users' table...")
    
    with db.engine.connect() as conn:
        trans = conn.begin()
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN disable_reason TEXT"))
            trans.commit()
            print("Success: Added 'disable_reason' column.")
        except Exception as e:
            trans.rollback()
            if "duplicate column" in str(e).lower():
                print("Column already exists.")
            else:
                print(f"Error: {e}")