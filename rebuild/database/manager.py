"""
Calendar Database Manager - PostgreSQL-based replacement for Replit KV
"""

import json
import secrets
from datetime import datetime, timedelta
from .models import db, CalendarData, SubscriptionToken, UserProfile, ManualCalendarEntry


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


    def get_manual_calendar(self, calendar_type, category, start_date, end_date):
        try:
            entries = ManualCalendarEntry.query.filter(
                ManualCalendarEntry.calendar_type == calendar_type,
                ManualCalendarEntry.category == category,
                ManualCalendarEntry.date >= start_date,
                ManualCalendarEntry.date <= end_date,
            ).order_by(ManualCalendarEntry.date).all()
            return [e.to_dict() for e in entries]
        except Exception as e:
            print(f"Error loading manual calendar: {e}")
            return []

    def get_manual_calendar_months(self, calendar_type):
        try:
            from sqlalchemy import func, extract
            results = db.session.query(
                extract('year', ManualCalendarEntry.date).label('year'),
                extract('month', ManualCalendarEntry.date).label('month'),
                ManualCalendarEntry.category,
                func.count(ManualCalendarEntry.id).label('count')
            ).filter(
                ManualCalendarEntry.calendar_type == calendar_type
            ).group_by(
                extract('year', ManualCalendarEntry.date),
                extract('month', ManualCalendarEntry.date),
                ManualCalendarEntry.category
            ).order_by(
                extract('year', ManualCalendarEntry.date).desc(),
                extract('month', ManualCalendarEntry.date).desc()
            ).all()
            return [{'year': int(r.year), 'month': int(r.month), 'category': r.category, 'count': r.count} for r in results]
        except Exception as e:
            print(f"Error loading manual calendar months: {e}")
            return []

    def save_manual_calendar(self, calendar_type, category, year, month, classifications, created_by=None):
        try:
            import calendar as cal_mod
            from datetime import date as date_type
            first_day = date_type(year, month, 1)
            last_day = date_type(year, month, cal_mod.monthrange(year, month)[1])
            ManualCalendarEntry.query.filter(
                ManualCalendarEntry.calendar_type == calendar_type,
                ManualCalendarEntry.category == category,
                ManualCalendarEntry.date >= first_day,
                ManualCalendarEntry.date <= last_day,
            ).delete()

            for cls_name, day_numbers in classifications.items():
                for day_num in day_numbers:
                    try:
                        entry_date = date_type(year, month, day_num)
                        entry = ManualCalendarEntry(
                            date=entry_date,
                            classification=cls_name,
                            calendar_type=calendar_type,
                            category=category,
                            created_by=created_by,
                        )
                        db.session.add(entry)
                    except ValueError:
                        continue

            db.session.commit()
            return True
        except Exception as e:
            print(f"Error saving manual calendar: {e}")
            db.session.rollback()
            return False


db_manager = CalendarDatabaseManager()
