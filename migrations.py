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
            
            collection_columns = [col['name'] for col in inspector.get_columns('collection')]
            if 'mockup_template_ids' not in collection_columns:
                print("Adding mockup_template_ids column to Collection table...")
                db.session.execute(text('ALTER TABLE collection ADD COLUMN mockup_template_ids TEXT'))
                db.session.commit()
                print("mockup_template_ids column added successfully!")
            
            if 'generated_asset' not in inspector.get_table_names():
                print("Creating GeneratedAsset table...")
                db.create_all()
                print("GeneratedAsset table created successfully!")
            
            # Add materials, size, and artist_note columns if they don't exist
            image_columns = [col['name'] for col in inspector.get_columns('image')]
            if 'materials' not in image_columns:
                print("Adding materials column to Image table...")
                db.session.execute(text('ALTER TABLE image ADD COLUMN materials TEXT'))
                db.session.commit()
                print("materials column added successfully!")
            
            if 'size' not in image_columns:
                print("Adding size column to Image table...")
                db.session.execute(text('ALTER TABLE image ADD COLUMN size VARCHAR(100)'))
                db.session.commit()
                print("size column added successfully!")
            
            if 'artist_note' not in image_columns:
                print("Adding artist_note column to Image table...")
                db.session.execute(text('ALTER TABLE image ADD COLUMN artist_note TEXT'))
                db.session.commit()
                print("artist_note column added successfully!")
            
            # Add materials, size, and artist_note columns to Collection table if they don't exist
            collection_columns_fresh = [col['name'] for col in inspector.get_columns('collection')]
            if 'materials' not in collection_columns_fresh:
                print("Adding materials column to Collection table...")
                db.session.execute(text('ALTER TABLE collection ADD COLUMN materials TEXT'))
                db.session.commit()
                print("materials column added to Collection successfully!")
            
            if 'size' not in collection_columns_fresh:
                print("Adding size column to Collection table...")
                db.session.execute(text('ALTER TABLE collection ADD COLUMN size VARCHAR(100)'))
                db.session.commit()
                print("size column added to Collection successfully!")
            
            if 'artist_note' not in collection_columns_fresh:
                print("Adding artist_note column to Collection table...")
                db.session.execute(text('ALTER TABLE collection ADD COLUMN artist_note TEXT'))
                db.session.commit()
                print("artist_note column added to Collection successfully!")
            
            # Add smart scheduler columns to Image table
            image_columns_fresh = [col['name'] for col in inspector.get_columns('image')]
            if 'calendar_source' not in image_columns_fresh:
                print("Adding calendar_source column to Image table...")
                db.session.execute(text('ALTER TABLE image ADD COLUMN calendar_source VARCHAR(50)'))
                db.session.commit()
                print("calendar_source column added successfully!")
            
            if 'calendar_event_id' not in image_columns_fresh:
                print("Adding calendar_event_id column to Image table...")
                db.session.execute(text('ALTER TABLE image ADD COLUMN calendar_event_id INTEGER'))
                db.session.commit()
                print("calendar_event_id column added successfully!")
            
            if 'pinterest_hashtags' not in image_columns_fresh:
                print("Adding pinterest_hashtags column to Image table...")
                db.session.execute(text('ALTER TABLE image ADD COLUMN pinterest_hashtags TEXT'))
                db.session.commit()
                print("pinterest_hashtags column added successfully!")
            
            if 'availability_status' not in image_columns_fresh:
                print("Adding availability_status column to Image table...")
                db.session.execute(text("ALTER TABLE image ADD COLUMN availability_status VARCHAR(20) NOT NULL DEFAULT 'Available'"))
                db.session.commit()
                print("availability_status column added successfully!")
            
            # Add smart scheduler columns to CalendarEvent table
            if 'calendar_event' in inspector.get_table_names():
                event_columns = [col['name'] for col in inspector.get_columns('calendar_event')]
                if 'assigned_image_id' not in event_columns:
                    print("Adding assigned_image_id column to CalendarEvent table...")
                    db.session.execute(text('ALTER TABLE calendar_event ADD COLUMN assigned_image_id INTEGER'))
                    db.session.commit()
                    print("assigned_image_id column added successfully!")
                
                if 'assigned_platform' not in event_columns:
                    print("Adding assigned_platform column to CalendarEvent table...")
                    db.session.execute(text('ALTER TABLE calendar_event ADD COLUMN assigned_platform VARCHAR(50)'))
                    db.session.commit()
                    print("assigned_platform column added successfully!")
            
            # Normalize workflow status values (ensure all images have valid status)
            print("Normalizing workflow status values...")
            db.session.execute(text("UPDATE image SET status = 'Draft' WHERE status IS NULL OR status = ''"))
            db.session.commit()
            print("Status normalization complete!")
            
            # Create Settings table if it doesn't exist
            if 'settings' not in inspector.get_table_names():
                print("Creating Settings table...")
                db.create_all()
                print("Settings table created successfully!")
                
                # Insert default settings row
                from models import Settings
                settings = Settings.query.first()
                if not settings:
                    print("Initializing default settings...")
                    default_settings = Settings(
                        company_name='Prompt Creative',
                        branded_hashtag='#ShopPromptCreative',
                        shop_url='',
                        instagram_hashtag_count=8,
                        pinterest_hashtag_count=4,
                        content_tone='balanced'
                    )
                    db.session.add(default_settings)
                    db.session.commit()
                    print("Default settings initialized!")
            
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
