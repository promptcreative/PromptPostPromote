"""
Downloads blueprint - ICS file downloads and subscription URL management
"""

from flask import Blueprint, request, jsonify, session, make_response
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from database.models import db, UserProfile
from database.manager import db_manager
from helpers.utils import get_user_calendar_range, calculate_is_double_go

downloads_bp = Blueprint('downloads', __name__)


def create_ics_event(summary, dtstart, dtend, description=""):
    lines = [
        "BEGIN:VEVENT",
        f"DTSTART:{dtstart.strftime('%Y%m%dT%H%M%SZ')}",
        f"DTEND:{dtend.strftime('%Y%m%dT%H%M%SZ')}",
        f"SUMMARY:{summary}",
        f"DESCRIPTION:{description}",
        "END:VEVENT"
    ]
    return "\n".join(lines)


def _parse_time_string(date_str, time_str):
    if 'AM' in time_str.upper() or 'PM' in time_str.upper():
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %I:%M %p")
    return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")


def _apply_double_go_recalculation(calendars, combined_results):
    from helpers.utils import apply_double_go_to_combined_results

    pti_cal = calendars.get('pti_collective', {}) or calendars.get('pti', {})
    vedic_cal = calendars.get('vedic_pti', {}) or calendars.get('goslow', {})

    pti_data = (pti_cal.get('data', {}).get('timing_data', [])
                or pti_cal.get('results', [])
                or pti_cal.get('timing_data', []))
    vedic_data = (vedic_cal.get('data', {}).get('results', [])
                  or vedic_cal.get('results', []))

    pti_by_date = {
        item.get("date"): item
        for item in (pti_data or [])
        if isinstance(item, dict) and item.get("date")
    }
    vedic_by_date = {
        item.get("date"): item
        for item in (vedic_data or [])
        if isinstance(item, dict) and item.get("date")
    }

    apply_double_go_to_combined_results(combined_results, pti_by_date, vedic_by_date)


@downloads_bp.route('/download-power-days')
def download_power_days():
    """Generate and download an ICS file with Power Days:
    Double GO days, Personal Power Days, and top-tier Bird Batch periods.
    """
    try:
        if not session.get('authenticated'):
            return jsonify({'error': 'Authentication required. Please log in first.'}), 401

        user_info = session.get('user_info', {})
        user_id = user_info.get('email')
        if not user_id:
            return jsonify({'error': 'User ID not found'}), 400

        saved_data = db_manager.get_calendar_data(user_id)
        if not saved_data:
            return jsonify({'error': 'No calendar data found. Please generate calendars first.'}), 404

        calendars = saved_data.get('calendars', {})
        events = []
        ny_tz = ZoneInfo("America/New_York")

        combined_cal = calendars.get('combined', {})
        combined_results = (combined_cal.get('data', {}).get('results', [])
                           or combined_cal.get('results', []))

        if combined_results:
            _apply_double_go_recalculation(calendars, combined_results)

        combined_results = (combined_cal.get('data', {}).get('results', [])
                           or combined_cal.get('results', []))

        double_go_dates = set()
        for day in combined_results:
            if day.get('is_double_go'):
                date_str = day.get('date')
                double_go_dates.add(date_str)
                events.append({
                    'type': 'double_go',
                    'date': date_str,
                    'title': 'DOUBLE GO Day',
                    'description': (f"PTI + Vedic systems aligned\\n"
                                    f"Classification: {day.get('classification', 'GOOD')}\\n"
                                    f"{day.get('reason', '')}"),
                    'all_day': True
                })

        personal_cal = calendars.get('personal', {})
        personal_data = (personal_cal.get('data', {}).get('daily_results', [])
                        or personal_cal.get('daily_results', []))

        for day in personal_data:
            date_str = day.get('date')
            day_score = day.get('day_score', {})
            quality = day_score.get('quality') if isinstance(day_score, dict) else None

            if quality == 'power' and date_str not in double_go_dates:
                score = day_score.get('score', 0) if isinstance(day_score, dict) else 0
                moon_house = day.get('moon_house', '')
                events.append({
                    'type': 'power_day',
                    'date': date_str,
                    'title': 'Personal Power Day',
                    'description': f"Quality: Power (Score: {score})\\nMoon House: {moon_house}",
                    'all_day': True
                })

        bird_batch_cal = calendars.get('bird_batch', {})
        bird_data = (bird_batch_cal.get('data', {}).get('filtered_periods', [])
                    or bird_batch_cal.get('filtered_periods', []))

        for period in bird_data:
            tier = period.get('tier', '')
            if tier in ['Double Boost', 'Boost']:
                date_str = period.get('date')
                start_time = period.get('start_time', '00:00')
                end_time = period.get('end_time', '23:59')
                bird = period.get('main_bird', '')
                activity = period.get('sub_activity', period.get('main_activity', ''))

                events.append({
                    'type': 'bird_batch',
                    'date': date_str,
                    'start_time': start_time,
                    'end_time': end_time,
                    'title': f"{tier}: {bird} {activity}",
                    'description': f"Bird: {bird}\\nActivity: {activity}\\nTier: {tier}",
                    'all_day': False
                })

        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Astrobatching//Power Days Calendar//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Astrobatching Power Days",
            "X-WR-TIMEZONE:America/New_York"
        ]

        for i, event in enumerate(events):
            uid = f"powerday-{event['date']}-{i}@astrobatching.com"

            if event.get('all_day'):
                dtstart = event['date'].replace('-', '')
                dt_end_date = datetime.strptime(event['date'], '%Y-%m-%d') + timedelta(days=1)
                dtend = dt_end_date.strftime('%Y%m%d')

                ics_lines.extend([
                    "BEGIN:VEVENT",
                    f"UID:{uid}",
                    f"DTSTART;VALUE=DATE:{dtstart}",
                    f"DTEND;VALUE=DATE:{dtend}",
                    f"SUMMARY:{event['title']}",
                    f"DESCRIPTION:{event['description']}",
                    "END:VEVENT"
                ])
            else:
                try:
                    start_dt = _parse_time_string(event['date'], event.get('start_time', '00:00'))
                    end_dt = _parse_time_string(event['date'], event.get('end_time', '23:59'))

                    start_utc = start_dt.replace(tzinfo=ny_tz).astimezone(ZoneInfo("UTC"))
                    end_utc = end_dt.replace(tzinfo=ny_tz).astimezone(ZoneInfo("UTC"))

                    ics_lines.extend([
                        "BEGIN:VEVENT",
                        f"UID:{uid}",
                        f"DTSTART:{start_utc.strftime('%Y%m%dT%H%M%SZ')}",
                        f"DTEND:{end_utc.strftime('%Y%m%dT%H%M%SZ')}",
                        f"SUMMARY:{event['title']}",
                        f"DESCRIPTION:{event['description']}",
                        "END:VEVENT"
                    ])
                except Exception:
                    continue

        ics_lines.append("END:VCALENDAR")
        ics_content = "\r\n".join(ics_lines)

        response = make_response(ics_content)
        response.headers['Content-Type'] = 'text/calendar; charset=utf-8'
        response.headers['Content-Disposition'] = 'attachment; filename="astrobatching-power-days.ics"'
        return response

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@downloads_bp.route('/download-birdbatch')
def download_birdbatch():
    """Generate and download an ICS file with BirdBatch favorable periods."""
    try:
        if not session.get('authenticated'):
            return jsonify({'error': 'Authentication required. Please log in first.'}), 401

        user_info = session.get('user_info', {})
        user_id = user_info.get('email')
        if not user_id:
            return jsonify({'error': 'User ID not found'}), 400

        user_profile = UserProfile.query.filter_by(email=user_id).first()
        if not user_profile or not user_profile.birth_date:
            return jsonify({'error': 'Profile not found. Please complete your profile first.'}), 404

        saved_data = db_manager.get_calendar_data(user_id)
        if not saved_data:
            return jsonify({'error': 'No calendar data found. Please generate calendars first.'}), 404

        calendars = saved_data.get('calendars', {})
        bird_batch_cal = calendars.get('bird_batch', {})
        bird_data = (bird_batch_cal.get('data', {}).get('filtered_periods', [])
                    or bird_batch_cal.get('filtered_periods', []))

        if not bird_data:
            return jsonify({'error': 'No bird batch periods found. Please generate calendars first.'}), 404

        ny_tz = ZoneInfo("America/New_York")
        events = []

        for period in bird_data:
            date_str = period.get('date')
            start_time = period.get('start_time', '00:00')
            end_time = period.get('end_time', '23:59')
            bird = period.get('main_bird', '')
            activity = period.get('sub_activity', period.get('main_activity', ''))
            tier = period.get('tier', 'Standard')

            events.append({
                'date': date_str,
                'start_time': start_time,
                'end_time': end_time,
                'title': f"{bird} - {activity}",
                'description': (f"Bird: {bird}\\nActivity: {activity}\\n"
                                f"Tier: {tier}\\nTime: {start_time} - {end_time}")
            })

        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Astrobatching//BirdBatch Calendar//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Astrobatching BirdBatch",
            "X-WR-TIMEZONE:America/New_York"
        ]

        for i, event in enumerate(events):
            uid = f"birdbatch-{event['date']}-{i}@astrobatching.com"

            try:
                start_dt = _parse_time_string(event['date'], event.get('start_time', '00:00'))
                end_dt = _parse_time_string(event['date'], event.get('end_time', '23:59'))

                start_utc = start_dt.replace(tzinfo=ny_tz).astimezone(ZoneInfo("UTC"))
                end_utc = end_dt.replace(tzinfo=ny_tz).astimezone(ZoneInfo("UTC"))

                ics_lines.extend([
                    "BEGIN:VEVENT",
                    f"UID:{uid}",
                    f"DTSTART:{start_utc.strftime('%Y%m%dT%H%M%SZ')}",
                    f"DTEND:{end_utc.strftime('%Y%m%dT%H%M%SZ')}",
                    f"SUMMARY:{event['title']}",
                    f"DESCRIPTION:{event['description']}",
                    "END:VEVENT"
                ])
            except Exception:
                continue

        ics_lines.append("END:VCALENDAR")
        ics_content = "\r\n".join(ics_lines)

        response = make_response(ics_content)
        response.headers['Content-Type'] = 'text/calendar; charset=utf-8'
        response.headers['Content-Disposition'] = 'attachment; filename="astrobatching-birdbatch.ics"'
        return response

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@downloads_bp.route('/get-subscription-urls', methods=['GET'])
def get_subscription_urls():
    """Get subscription URLs for all calendar types for authenticated user."""
    try:
        if not session.get('authenticated'):
            return jsonify({'error': 'Authentication required'}), 401

        user_info = session.get('user_info', {})
        user_id = user_info.get('email')
        if not user_id:
            return jsonify({'error': 'User ID not found'}), 400

        base_url = request.url_root.rstrip('/')
        subscription_urls = db_manager.get_user_subscriptions(user_id, base_url)

        calendar_names = {
            'astrobatching': 'Astrobatching',
            'part_of_fortune': 'Part of Fortune',
            'yogi_point': 'Yogi Point',
            'personal': 'Personal',
            'pti': 'PTI/Magi',
            'goslow': 'Go/Slow/Build',
            'electional': 'Electional',
            'combined': 'Combined',
            'bird_batch': 'Bird Batch'
        }

        formatted_urls = []
        for cal_type, url in subscription_urls.items():
            formatted_urls.append({
                'type': cal_type,
                'name': calendar_names.get(cal_type, cal_type),
                'url': url
            })

        return jsonify({
            'status': 'success',
            'subscription_urls': formatted_urls,
            'instructions': ('Copy these URLs and add them to your calendar app '
                             '(Google Calendar, Apple Calendar, Outlook, etc.) '
                             'to subscribe to auto-updating calendars.')
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
