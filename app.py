import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

# Configuration
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "dev_key_123"

# Force SQLite usage by ignoring DATABASE_URL
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///artwork_manager.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {}
print("Forcing SQLite database usage")
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db.init_app(app)

# Import models and routes
import models
import routes

# Initialize database tables
def init_db():
    """Initialize database tables"""
    try:
        with app.app_context():
            db.create_all()
            print("Database tables created successfully")
            print(f"Using database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        raise

# Don't initialize database at module level
