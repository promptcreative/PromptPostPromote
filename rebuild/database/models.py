"""
Database models for Astrobatching
PostgreSQL with SQLAlchemy - no Replit KV dependency
"""

import os
import secrets
import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class UserProfile(db.Model):
    __tablename__ = 'user_profiles'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    calendar_range_days = db.Column(db.Integer, default=60)

    birth_date = db.Column(db.Date, nullable=True)
    birth_time = db.Column(db.Time, nullable=True)
    birth_latitude = db.Column(db.Float, nullable=True)
    birth_longitude = db.Column(db.Float, nullable=True)
    birth_timezone = db.Column(db.Float, default=-5.0)
    birth_timezone_name = db.Column(db.String(100), nullable=True)
    birth_location_name = db.Column(db.String(255), nullable=True)

    current_latitude = db.Column(db.Float, default=19.076)
    current_longitude = db.Column(db.Float, default=72.8777)
    current_location_name = db.Column(db.String(255), default="Mumbai, India")

    def __repr__(self):
        return f'<UserProfile {self.email}>'

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'calendar_range_days': self.calendar_range_days,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'birth_time': self.birth_time.isoformat() if self.birth_time else None,
            'birth_latitude': self.birth_latitude,
            'birth_longitude': self.birth_longitude,
            'birth_timezone': self.birth_timezone,
            'birth_timezone_name': self.birth_timezone_name,
            'birth_location_name': self.birth_location_name,
            'current_latitude': self.current_latitude,
            'current_longitude': self.current_longitude,
            'current_location_name': self.current_location_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Client(db.Model):
    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)
    owner_email = db.Column(db.String(255), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    birth_date = db.Column(db.Date, nullable=True)
    birth_time = db.Column(db.Time, nullable=True)
    birth_latitude = db.Column(db.Float, nullable=True)
    birth_longitude = db.Column(db.Float, nullable=True)
    birth_timezone = db.Column(db.Float, default=-5.0)
    birth_location_name = db.Column(db.String(255), nullable=True)

    current_latitude = db.Column(db.Float, nullable=True)
    current_longitude = db.Column(db.Float, nullable=True)
    current_location_name = db.Column(db.String(255), nullable=True)

    calendar_range_days = db.Column(db.Integer, default=60)
    last_generated_at = db.Column(db.DateTime, nullable=True)
    calendar_status = db.Column(db.String(50), default='pending')

    def __repr__(self):
        return f'<Client {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'owner_email': self.owner_email,
            'name': self.name,
            'email': self.email,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'birth_time': self.birth_time.isoformat() if self.birth_time else None,
            'birth_latitude': self.birth_latitude,
            'birth_longitude': self.birth_longitude,
            'birth_timezone': self.birth_timezone,
            'birth_location_name': self.birth_location_name,
            'current_latitude': self.current_latitude,
            'current_longitude': self.current_longitude,
            'current_location_name': self.current_location_name,
            'calendar_range_days': self.calendar_range_days,
            'last_generated_at': self.last_generated_at.isoformat() if self.last_generated_at else None,
            'calendar_status': self.calendar_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'has_birth_data': bool(self.birth_date and self.birth_time),
        }


class CalendarData(db.Model):
    __tablename__ = 'calendar_data'

    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(255), nullable=False, index=True)
    calendar_type = db.Column(db.String(50), nullable=False)
    date_range_start = db.Column(db.Date, nullable=False)
    date_range_end = db.Column(db.Date, nullable=False)
    calendar_json = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<CalendarData {self.user_email} {self.calendar_type}>'


class SubscriptionToken(db.Model):
    __tablename__ = 'subscription_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(255), nullable=False, index=True)
    calendar_type = db.Column(db.String(50), nullable=False)
    token = db.Column(db.String(32), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_email', 'calendar_type', name='uq_user_cal_type'),
    )

    @staticmethod
    def get_or_create(user_email, calendar_type):
        existing = SubscriptionToken.query.filter_by(
            user_email=user_email, calendar_type=calendar_type
        ).first()
        if existing and len(existing.token) == 32:
            return existing.token
        token_val = secrets.token_hex(16)
        if existing:
            existing.token = token_val
        else:
            new_token = SubscriptionToken(
                user_email=user_email,
                calendar_type=calendar_type,
                token=token_val
            )
            db.session.add(new_token)
        db.session.commit()
        return token_val

    @staticmethod
    def verify(user_email, calendar_type, token):
        if not token or len(token) != 32:
            return False
        try:
            int(token, 16)
        except ValueError:
            return False
        existing = SubscriptionToken.query.filter_by(
            user_email=user_email, calendar_type=calendar_type
        ).first()
        if not existing or len(existing.token) != 32:
            return False
        return token == existing.token


def init_database(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()
        print("Database tables created successfully")

    return db
