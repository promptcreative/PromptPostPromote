from app import app, db
from sqlalchemy import text

def add_new_columns():
    with app.app_context():
        # Add post_title column if it doesn't exist
        db.session.execute(text('ALTER TABLE image ADD COLUMN IF NOT EXISTS post_title VARCHAR(255)'))
        # Add key_points column if it doesn't exist
        db.session.execute(text('ALTER TABLE image ADD COLUMN IF NOT EXISTS key_points TEXT'))
        db.session.commit()

if __name__ == '__main__':
    add_new_columns()
