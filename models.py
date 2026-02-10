from datetime import datetime
from app import db


class Calendar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    calendar_type = db.Column(db.String(50), nullable=False, unique=True)
    calendar_name = db.Column(db.String(255), nullable=False)
    ics_url = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    events = db.relationship('CalendarEvent', backref='calendar', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        from sqlalchemy import select, func
        event_count = db.session.scalar(
            select(func.count()).select_from(CalendarEvent).where(CalendarEvent.calendar_id == self.id)
        ) or 0
        return {
            'id': self.id,
            'calendar_type': self.calendar_type,
            'calendar_name': self.calendar_name,
            'ics_url': self.ics_url or '',
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
    publer_status = db.Column(db.String(20), default='pending')
    publer_post_id = db.Column(db.String(100))
    social_copy = db.Column(db.Text)

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
            'publer_status': self.publer_status or 'pending',
            'publer_post_id': self.publer_post_id or '',
            'social_copy': self.social_copy or '',
            'created_at': self.created_at.isoformat() if self.created_at else ''
        }


class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(255), default='Prompt Creative')
    branded_hashtag = db.Column(db.String(100), default='#ShopPromptCreative')
    shop_url = db.Column(db.Text, default='')
    publer_workspace_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'company_name': self.company_name or '',
            'branded_hashtag': self.branded_hashtag or '',
            'shop_url': self.shop_url or '',
            'publer_workspace_id': self.publer_workspace_id or '',
            'updated_at': self.updated_at.isoformat() if self.updated_at else ''
        }
