from datetime import datetime
from app import db

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text)
    hashtags = db.Column(db.Text)
    category = db.Column(db.String(255))  # Field for artwork title
    post_title = db.Column(db.String(255))  # New field for post title
    key_points = db.Column(db.Text)        # New field for key points
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'original_filename': self.original_filename,
            'stored_filename': self.stored_filename,
            'description': self.description,
            'hashtags': self.hashtags,
            'category': self.category,
            'post_title': self.post_title,
            'key_points': self.key_points,
            'created_at': self.created_at.isoformat()
        }
