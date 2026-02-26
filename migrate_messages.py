"""
migrate_messages.py
Adds reply_to_id and edited_at columns to the messages table.
Run once: python migrate_messages.py
"""
from app import app, db
from sqlalchemy import text

with app.app_context():
    with db.engine.connect() as conn:
        # Add edited_at column if it doesn't exist
        try:
            conn.execute(text('ALTER TABLE messages ADD COLUMN edited_at DATETIME'))
            print('[OK] Added column: messages.edited_at')
        except Exception as e:
            print(f'[SKIP] messages.edited_at already exists or error: {e}')

        # Add reply_to_id column if it doesn't exist
        try:
            conn.execute(text('ALTER TABLE messages ADD COLUMN reply_to_id INTEGER REFERENCES messages(id)'))
            print('[OK] Added column: messages.reply_to_id')
        except Exception as e:
            print(f'[SKIP] messages.reply_to_id already exists or error: {e}')

        conn.commit()

    print('Migration complete.')
