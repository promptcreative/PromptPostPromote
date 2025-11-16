#!/usr/bin/env python3
"""
Migration script to copy data from SQLite to PostgreSQL
"""
import os
import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database URLs
SQLITE_PATH = "artwork_manager.db"
POSTGRES_URL = os.environ.get("DATABASE_URL")

def migrate_data():
    """Migrate all data from SQLite to PostgreSQL"""
    
    if not os.path.exists(SQLITE_PATH):
        print(f"SQLite database not found at {SQLITE_PATH}")
        print("Nothing to migrate - starting fresh!")
        return
    
    print(f"Migrating data from SQLite to PostgreSQL...")
    print(f"Source: {SQLITE_PATH}")
    print(f"Target: {POSTGRES_URL}")
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    
    # Connect to PostgreSQL
    pg_engine = create_engine(POSTGRES_URL)
    
    # Tables to migrate (in dependency order)
    tables_to_migrate = [
        'settings',
        'collection',
        'calendar',
        'calendar_event',
        'image',
        'event_assignment',
        'generated_asset'
    ]
    
    with pg_engine.begin() as pg_conn:
        for table_name in tables_to_migrate:
            try:
                # Check if table exists in SQLite
                cursor = sqlite_conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table_name,)
                )
                if not cursor.fetchone():
                    print(f"  ⏭️  Skipping {table_name} (doesn't exist in SQLite)")
                    continue
                
                # Get all rows from SQLite
                rows = sqlite_conn.execute(f"SELECT * FROM {table_name}").fetchall()
                
                if not rows:
                    print(f"  ⏭️  Skipping {table_name} (no data)")
                    continue
                
                # Get column names
                columns = [description[0] for description in rows[0].keys()]
                
                # Clear existing data in PostgreSQL
                pg_conn.execute(text(f"DELETE FROM {table_name}"))
                
                # Insert rows
                placeholders = ', '.join([f':{col}' for col in columns])
                insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                
                for row in rows:
                    row_dict = dict(row)
                    pg_conn.execute(text(insert_sql), row_dict)
                
                print(f"  ✅ Migrated {len(rows)} rows to {table_name}")
                
            except Exception as e:
                print(f"  ❌ Error migrating {table_name}: {e}")
                continue
    
    sqlite_conn.close()
    print("\n✨ Migration complete!")

if __name__ == "__main__":
    migrate_data()
