"""
Calendar Database Manager - PostgreSQL-based replacement for Replit KV
"""

import json
import secrets
from datetime import datetime, timedelta
from .models import db, CalendarData, SubscriptionToken, UserProfile


class CalendarDatabaseManager:

    def save_calendar_data(self, user_email, calendar_data):
        try:
            serialized = json.dumps(calendar_data, default=str)
            existing = CalendarData.query.filter_by(
                user_email=user_email, calendar_type='dashboard'
            ).first()
            if existing:
                existing.calendar_json = json.loads(serialized)
                existing.created_at = datetime.utcnow()
            else:
                new_entry = CalendarData(
                    user_email=user_email,
                    calendar_type='dashboard',
                    date_range_start=datetime.utcnow().date(),
                    date_range_end=(datetime.utcnow() + timedelta(days=90)).date(),
                    calendar_json=json.loads(serialized),
                )
                db.session.add(new_entry)
            db.session.commit()
            return True
        except Exception as e:
            print(f"Error saving calendar data: {e}")
            db.session.rollback()
            return False

    def get_calendar_data(self, user_email):
        try:
            entry = CalendarData.query.filter_by(
                user_email=user_email, calendar_type='dashboard'
            ).order_by(CalendarData.created_at.desc()).first()
            if entry:
                return entry.calendar_json
            return None
        except Exception as e:
            print(f"Error loading calendar data: {e}")
            return None

    def clear_calendar_data(self, user_email, year=None, month=None):
        try:
            CalendarData.query.filter_by(
                user_email=user_email, calendar_type='dashboard'
            ).delete()
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    def get_subscription_token(self, user_email, calendar_type):
        return SubscriptionToken.get_or_create(user_email, calendar_type)

    def verify_subscription_token(self, user_email, calendar_type, token):
        return SubscriptionToken.verify(user_email, calendar_type, token)

    def get_user_subscriptions(self, user_email, base_url):
        calendar_types = [
            'personal', 'bird_batch', 'pti', 'combined',
            'yogi_point', 'part_of_fortune', 'microbird',
            'enhanced_pof', 'vedic', 'nogo', 'all_microtransits'
        ]
        urls = {}
        for cal_type in calendar_types:
            token = self.get_subscription_token(user_email, cal_type)
            from urllib.parse import quote
            user_id_encoded = quote(user_email, safe='')
            urls[cal_type] = f"{base_url}/calendar/{cal_type}.ics?user_id={user_id_encoded}&token={token}"
        return urls


    def update_background_days(self, user_email, background_days):
        try:
            saved = self.get_calendar_data(user_email)
            if saved is None:
                saved = {}
            saved['background_days'] = background_days
            return self.save_calendar_data(user_email, saved)
        except Exception as e:
            print(f"Error updating background days: {e}")
            return False

    def save_precision_timing(self, user_email, precision_data):
        try:
            saved = self.get_calendar_data(user_email)
            if saved is None:
                saved = {}
            saved['precision_timing'] = precision_data
            return self.save_calendar_data(user_email, saved)
        except Exception as e:
            print(f"Error saving precision timing: {e}")
            return False


db_manager = CalendarDatabaseManager()
