from app import app, db
from sqlalchemy import text, inspect


def migrate_schema():
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        db.create_all()

        if 'calendar' in tables:
            cols = [c['name'] for c in inspector.get_columns('calendar')]
            if 'ics_url' not in cols:
                db.session.execute(text('ALTER TABLE calendar ADD COLUMN ics_url TEXT'))
                db.session.commit()

        if 'calendar_event' in tables:
            cols = [c['name'] for c in inspector.get_columns('calendar_event')]
            if 'publer_status' not in cols:
                db.session.execute(text("ALTER TABLE calendar_event ADD COLUMN publer_status VARCHAR(20) DEFAULT 'pending'"))
                db.session.commit()
            if 'publer_post_id' not in cols:
                db.session.execute(text('ALTER TABLE calendar_event ADD COLUMN publer_post_id VARCHAR(100)'))
                db.session.commit()
            if 'social_copy' not in cols:
                db.session.execute(text('ALTER TABLE calendar_event ADD COLUMN social_copy TEXT'))
                db.session.commit()

        if 'settings' in tables:
            cols = [c['name'] for c in inspector.get_columns('settings')]
            if 'publer_workspace_id' not in cols:
                db.session.execute(text('ALTER TABLE settings ADD COLUMN publer_workspace_id VARCHAR(100)'))
                db.session.commit()

        print("Schema migration complete!")
