from app import app, init_db
from migrations import migrate_schema
import os

if __name__ == "__main__":
    # Initialize database tables first
    init_db()
    # Run schema migration to add any missing columns
    migrate_schema()
    
    # Migrate data from SQLite to PostgreSQL (one-time operation)
    if os.path.exists("artwork_manager.db") and os.environ.get("DATABASE_URL"):
        print("Found existing SQLite database - running migration...")
        try:
            from migrate_to_postgres import migrate_data
            migrate_data()
            # Rename SQLite file to prevent re-migration
            os.rename("artwork_manager.db", "artwork_manager.db.migrated")
            print("Migration successful! SQLite database renamed to .migrated")
        except Exception as e:
            print(f"Migration error: {e}")
            print("Continuing with PostgreSQL (may be empty)...")
    
    app.run(host="0.0.0.0", port=5000)
