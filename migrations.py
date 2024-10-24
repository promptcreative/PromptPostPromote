from app import app, db
from sqlalchemy import text

def add_category_column():
    with app.app_context():
        db.session.execute(text('ALTER TABLE image ADD COLUMN IF NOT EXISTS category VARCHAR(255)'))
        db.session.commit()

if __name__ == '__main__':
    add_category_column()
