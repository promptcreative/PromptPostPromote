from app import app, db
from sqlalchemy import text, inspect
import sys

def check_column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    with app.app_context():
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns

def migrate_schema():
    """Migrate database schema to new Publer-compatible structure"""
    with app.app_context():
        inspector = inspect(db.engine)
        
        if 'image' not in inspector.get_table_names():
            print("Image table doesn't exist. Creating all tables from scratch...")
            db.create_all()
            print("All tables created successfully!")
            return
        
        print("Starting schema migration...")
        
        existing_columns = [col['name'] for col in inspector.get_columns('image')]
        print(f"Existing columns: {existing_columns}")
        
        if 'title' in existing_columns:
            print("Schema already migrated. Checking for collection support...")
            
            if 'calendar' not in inspector.get_table_names():
                print("Creating Calendar tables...")
                db.create_all()
            
            if 'collection' not in inspector.get_table_names():
                print("Creating Collection table...")
                db.create_all()
            
            if 'collection_id' not in existing_columns:
                print("Adding collection_id column to Image table with foreign key...")
                try:
                    db.session.execute(text(
                        'ALTER TABLE image ADD COLUMN collection_id INTEGER '
                        'REFERENCES collection(id) ON DELETE SET NULL'
                    ))
                    db.session.commit()
                    print("collection_id column with FK constraint added successfully!")
                except Exception as e:
                    print(f"Note: FK constraint may not be supported in this database ({e})")
                    print("Adding column without FK constraint...")
                    db.session.rollback()
                    db.session.execute(text('ALTER TABLE image ADD COLUMN collection_id INTEGER'))
                    db.session.commit()
                    print("collection_id column added (FK will be enforced at ORM level)")
            
            print("Migration complete!")
            return
        
        print("Old schema detected. Migrating data...")
        
        results = db.session.execute(text('SELECT * FROM image')).fetchall()
        old_data = []
        for row in results:
            old_data.append({
                'id': row[0],
                'original_filename': row[1] if len(row) > 1 else '',
                'stored_filename': row[2] if len(row) > 2 else '',
                'description': row[3] if len(row) > 3 else None,
                'hashtags': row[4] if len(row) > 4 else None,
                'category': row[5] if len(row) > 5 else None,
                'post_title': row[6] if len(row) > 6 else None,
                'key_points': row[7] if len(row) > 7 else None,
                'created_at': row[8] if len(row) > 8 else None
            })
        
        print(f"Backing up {len(old_data)} records...")
        
        db.session.execute(text('DROP TABLE IF EXISTS image'))
        db.session.commit()
        
        print("Creating new schema...")
        db.create_all()
        
        print(f"Restoring {len(old_data)} records with ALL legacy fields mapped...")
        for data in old_data:
            insert_sql = text("""
                INSERT INTO image (
                    original_filename, stored_filename, painting_name, title,
                    text, seo_tags, reminder, status, media, created_at
                ) VALUES (
                    :original_filename, :stored_filename, :painting_name, :title,
                    :text, :seo_tags, :reminder, :status, :media, :created_at
                )
            """)
            
            db.session.execute(insert_sql, {
                'original_filename': data['original_filename'],
                'stored_filename': data['stored_filename'],
                'painting_name': data.get('category', ''),
                'title': data.get('post_title', ''),
                'text': data.get('description', ''),
                'seo_tags': data.get('hashtags', ''),
                'reminder': data.get('key_points', ''),
                'status': 'Draft',
                'media': data.get('stored_filename', ''),
                'created_at': data.get('created_at')
            })
        
        db.session.commit()
        print(f"Migration complete! Migrated {len(old_data)} records with ALL legacy data preserved.")
        print("Legacy field mapping:")
        print("  - category → painting_name")
        print("  - post_title → title")
        print("  - description → text")
        print("  - hashtags → seo_tags")
        print("  - key_points → reminder")

def reset_database():
    """Reset database - use with caution!"""
    with app.app_context():
        print("WARNING: This will delete all data!")
        response = input("Type 'yes' to continue: ")
        if response.lower() == 'yes':
            db.drop_all()
            db.create_all()
            print("Database reset complete!")
        else:
            print("Reset cancelled.")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'reset':
        reset_database()
    else:
        migrate_schema()
