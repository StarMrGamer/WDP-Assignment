from app import app, db
from sqlalchemy import text

def fix_database():
    """
    Updates the database schema to match the current models.
    Specifically adds the missing photo_url column to community_posts.
    """
    print("Attempting to update database schema...")
    
    with app.app_context():
        with db.engine.connect() as conn:
            try:
                # Add the missing column
                conn.execute(text("ALTER TABLE community_posts ADD COLUMN photo_url VARCHAR(255)"))
                conn.commit()
                print("Success: Added 'photo_url' column to 'community_posts' table.")
            except Exception as e:
                print(f"Note: {e}")
                print("The column might already exist or another error occurred.")

if __name__ == "__main__":
    fix_database()