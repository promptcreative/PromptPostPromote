from app import app, init_db
from migrations import migrate_schema

if __name__ == "__main__":
    # Run schema migration to add any missing columns
    migrate_schema()
    app.run(host="0.0.0.0", port=5000)
