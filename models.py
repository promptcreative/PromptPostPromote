from datetime import datetime
from app import db

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text)
    hashtags = db.Column(db.Text)
    category = db.Column(db.String(255))  # New field for artwork title
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'original_filename': self.original_filename,
            'stored_filename': self.stored_filename,
            'description': self.description,
            'hashtags': self.hashtags,
            'category': self.category,
            'created_at': self.created_at.isoformat()
        }
