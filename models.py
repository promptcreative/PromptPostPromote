from datetime import datetime
from app import db

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    
    title = db.Column(db.String(500))
    painting_name = db.Column(db.String(500))
    post_subtype = db.Column(db.String(100))
    platform = db.Column(db.String(100))
    date = db.Column(db.String(50))
    time = db.Column(db.String(20))
    status = db.Column(db.String(100))
    labels = db.Column(db.Text)
    post_url = db.Column(db.Text)
    alt_text = db.Column(db.Text)
    cta = db.Column(db.Text)
    comments = db.Column(db.Text)
    cover_image_url = db.Column(db.Text)
    
    etsy_description = db.Column(db.Text)
    etsy_listing_title = db.Column(db.String(500))
    etsy_price = db.Column(db.String(50))
    etsy_quantity = db.Column(db.String(50))
    etsy_sku = db.Column(db.String(100))
    
    instagram_first_comment = db.Column(db.Text)
    
    links = db.Column(db.Text)
    media = db.Column(db.String(255))
    media_source = db.Column(db.String(255))
    media_urls = db.Column(db.Text)
    
    pin_board_fb_album_google_category = db.Column(db.String(500))
    
    pinterest_description = db.Column(db.Text)
    pinterest_link_url = db.Column(db.Text)
    
    reminder = db.Column(db.Text)
    
    seo_description = db.Column(db.Text)
    seo_tags = db.Column(db.Text)
    seo_title = db.Column(db.String(500))
    
    text = db.Column(db.Text)
    video_pin_pdf_title = db.Column(db.String(500))
    
    calendar_selection = db.Column(db.String(100))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'original_filename': self.original_filename,
            'stored_filename': self.stored_filename,
            'title': self.title or '',
            'painting_name': self.painting_name or '',
            'post_subtype': self.post_subtype or '',
            'platform': self.platform or '',
            'date': self.date or '',
            'time': self.time or '',
            'status': self.status or '',
            'labels': self.labels or '',
            'post_url': self.post_url or '',
            'alt_text': self.alt_text or '',
            'cta': self.cta or '',
            'comments': self.comments or '',
            'cover_image_url': self.cover_image_url or '',
            'etsy_description': self.etsy_description or '',
            'etsy_listing_title': self.etsy_listing_title or '',
            'etsy_price': self.etsy_price or '',
            'etsy_quantity': self.etsy_quantity or '',
            'etsy_sku': self.etsy_sku or '',
            'instagram_first_comment': self.instagram_first_comment or '',
            'links': self.links or '',
            'media': self.media or '',
            'media_source': self.media_source or '',
            'media_urls': self.media_urls or '',
            'pin_board_fb_album_google_category': self.pin_board_fb_album_google_category or '',
            'pinterest_description': self.pinterest_description or '',
            'pinterest_link_url': self.pinterest_link_url or '',
            'reminder': self.reminder or '',
            'seo_description': self.seo_description or '',
            'seo_tags': self.seo_tags or '',
            'seo_title': self.seo_title or '',
            'text': self.text or '',
            'video_pin_pdf_title': self.video_pin_pdf_title or '',
            'calendar_selection': self.calendar_selection or '',
            'created_at': self.created_at.isoformat() if self.created_at else '',
            'updated_at': self.updated_at.isoformat() if self.updated_at else ''
        }


class Calendar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    calendar_type = db.Column(db.String(50), nullable=False, unique=True)
    calendar_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    events = db.relationship('CalendarEvent', backref='calendar', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        from sqlalchemy import select, func
        event_count = db.session.scalar(select(func.count()).select_from(CalendarEvent).where(CalendarEvent.calendar_id == self.id)) or 0
        return {
            'id': self.id,
            'calendar_type': self.calendar_type,
            'calendar_name': self.calendar_name,
            'event_count': event_count,
            'created_at': self.created_at.isoformat() if self.created_at else '',
            'updated_at': self.updated_at.isoformat() if self.updated_at else ''
        }


class CalendarEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    calendar_id = db.Column(db.Integer, db.ForeignKey('calendar.id'), nullable=False)
    
    summary = db.Column(db.String(500))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    midpoint_time = db.Column(db.DateTime, nullable=False)
    
    event_type = db.Column(db.String(100))
    is_assigned = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'calendar_id': self.calendar_id,
            'summary': self.summary or '',
            'start_time': self.start_time.isoformat() if self.start_time else '',
            'end_time': self.end_time.isoformat() if self.end_time else '',
            'midpoint_time': self.midpoint_time.isoformat() if self.midpoint_time else '',
            'event_type': self.event_type or '',
            'is_assigned': self.is_assigned,
            'created_at': self.created_at.isoformat() if self.created_at else ''
        }
