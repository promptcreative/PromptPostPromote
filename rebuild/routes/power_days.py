"""Power Days routes — classified power days, filtered microtransits."""

import traceback
from datetime import datetime, date, timedelta

from flask import Blueprint, jsonify, request, session
from database.manager import db_manager
from database.models import db, UserProfile
from helpers.dashboard import generate_dashboard_core
from helpers.utils import get_two_month_range, get_effective_user_id

power_days_bp = Blueprint('power_days', __name__)


def _extract_date_part(date_string):
    if not date_string:
        return None
    if 'T' in date_string:
        return date_string.split('T')[0]
    if ' ' in date_string:
        return date_string.split(' ')[0]
    return date_string


def _extract_power_days(saved_data):
    calendars = (saved_data or {}).get('calendars', {})
    combined_cal = calendars.get('combined', {})
    combined_results = (
        combined_cal.get('data', {}).get('results', [])
        or combined_cal.get('results', [])
    )

    omni_days = []
    double_go_days = []
    good_days = []
    background_days = []

    for day in combined_results:
        if not isinstance(day, dict):
            continue

        breakdown = day.get('system_breakdown', {})
        details = day.get('details', {})
        if not breakdown:
            breakdown = details.get('system_breakdown', {})

        pti_info = breakdown.get('pti_collective', {}) or breakdown.get('pti', {}) or {}
        vedic_info = breakdown.get('vedic_pti', {}) or breakdown.get('vedic', {}) or {}
        personal_info = breakdown.get('personal', {}) or {}
        pti_quality = pti_info.get('quality', '')
        vedic_quality = vedic_info.get('quality', '')
        personal_quality = personal_info.get('quality', '')

        entry = {
            'date': day.get('date', ''),
            'reason': day.get('reason', ''),
            'pti_label': pti_quality,
            'vedic_label': vedic_quality,
            'personal_label': personal_quality,
        }

        classification = day.get('classification', '')
        is_bg = day.get('is_background', False)
        if not is_bg:
            cls_key = day.get('classification_key', '') or details.get('classification_key', '')
            if cls_key in ('omni', 'double_go', 'good'):
                is_bg = True

        if classification == 'OMNI':
            omni_days.append(entry)
            background_days.append(entry['date'])
        elif classification == 'DOUBLE GO':
            double_go_days.append(entry)
            background_days.append(entry['date'])
        elif classification == 'GOOD':
            good_days.append(entry)
            background_days.append(entry['date'])
        elif is_bg and entry['date'] not in background_days:
            background_days.append(entry['date'])

    return {
        'omni_days': omni_days,
        'double_go_days': double_go_days,
        'good_days': good_days,
        'background_days': background_days,
        'total_background': len(background_days),
        'total_days': len(combined_results),
    }


def _get_background_days_and_period(saved_data):
    power = _extract_power_days(saved_data)
    bg_dates = set(power['background_days'])

    period = (saved_data or {}).get('period', {})
    try:
        days = int(period.get('days', 60))
    except (ValueError, TypeError):
        days = 60

    return bg_dates, days


@power_days_bp.route('/api/power-days', methods=['GET'])
def get_power_days():
    try:
        if not session.get('authenticated'):
            return jsonify({'error': 'Authentication required'}), 401

        user_id = get_effective_user_id()
        if not user_id:
            return jsonify({'error': 'User ID not found'}), 400

        saved_data = db_manager.get_calendar_data(user_id)
        if not saved_data:
            return jsonify({'error': 'No saved calendar data found. Generate calendars first.'}), 404

        result = _extract_power_days(saved_data)
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@power_days_bp.route('/api/power-days/generate', methods=['POST'])
def generate_power_days():
    try:
        if not session.get('authenticated'):
            return jsonify({'error': 'Authentication required'}), 401

        user_info = session.get('user_info', {})
        user_id = get_effective_user_id()
        if not user_id:
            return jsonify({'error': 'User ID not found'}), 400

        role = user_info.get('role', 'user')
        if role == 'client':
            return jsonify({'error': 'Calendar generation is managed by your agency admin.'}), 403

        user_profile = UserProfile.query.filter_by(email=user_info.get('email')).first()
        if not user_profile or not user_profile.birth_date:
            return jsonify({'error': 'Profile not complete'}), 400

        profile_payload = {
            'birth_date': user_profile.birth_date.isoformat() if user_profile.birth_date else None,
            'birth_time': user_profile.birth_time.isoformat() if user_profile.birth_time else None,
            'birth_latitude': getattr(user_profile, 'birth_latitude', None),
            'birth_longitude': getattr(user_profile, 'birth_longitude', None),
            'latitude': getattr(user_profile, 'current_latitude', None),
            'longitude': getattr(user_profile, 'current_longitude', None),
            'location': getattr(user_profile, 'current_location_name', None),
            'force_regenerate': True,
        }

        try:
            profile_days = int(getattr(user_profile, 'calendar_range_days', 0) or 0)
        except Exception:
            profile_days = 0
        if profile_days >= 30:
            profile_payload['days'] = profile_days
        else:
            _, _, auto_days = get_two_month_range()
            profile_payload['days'] = auto_days

        core_result = generate_dashboard_core(profile_payload, user_id=user_id)

        if not core_result or core_result.get('error'):
            return jsonify({'error': core_result.get('error', 'Generation failed')}), 500

        saved_data = db_manager.get_calendar_data(user_id)
        if not saved_data:
            saved_data = core_result

        result = _extract_power_days(saved_data)
        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@power_days_bp.route('/api/power-days/bird-batch', methods=['GET'])
def get_bird_batch_power_days():
    """Bird Batch periods filtered to background days only."""
    try:
        if not session.get('authenticated'):
            return jsonify({'error': 'Authentication required'}), 401

        user_id = get_effective_user_id()
        if not user_id:
            return jsonify({'error': 'User ID not found'}), 400

        saved_data = db_manager.get_calendar_data(user_id)
        if not saved_data:
            return jsonify({'error': 'No saved calendar data found. Generate calendars first.'}), 404

        bg_dates, days = _get_background_days_and_period(saved_data)

        if not bg_dates:
            return jsonify({'daily_results': [], 'background_days': [], 'total_background_days': 0})

        calendars = (saved_data or {}).get('calendars', {})
        bird_cal = calendars.get('bird_batch', {})
        daily_results = bird_cal.get('daily_results', [])
        if not daily_results and isinstance(bird_cal.get('data'), dict):
            daily_results = bird_cal['data'].get('daily_results', [])

        filtered_days = []
        total_periods = 0
        tier_counts = {'Double Boost': 0, 'Boost': 0, 'Build': 0}

        for day_data in daily_results:
            day_date = day_data.get('date', '')
            if day_date not in bg_dates:
                continue

            periods = day_data.get('periods', [])
            filtered_days.append(day_data)
            total_periods += len(periods)
            for p in periods:
                tier = p.get('tier', '')
                if tier in tier_counts:
                    tier_counts[tier] += 1

        return jsonify({
            'calendar_type': 'Bird_Batch_Power_Days',
            'daily_results': filtered_days,
            'total_background_days': len(filtered_days),
            'total_periods': total_periods,
            'tier_counts': tier_counts,
            'background_days': sorted(bg_dates),
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@power_days_bp.route('/api/power-days/yogi-point', methods=['GET'])
def get_yogi_point_power_days():
    try:
        if not session.get('authenticated'):
            return jsonify({'error': 'Authentication required'}), 401

        user_id = get_effective_user_id()
        if not user_id:
            return jsonify({'error': 'User ID not found'}), 400

        saved_data = db_manager.get_calendar_data(user_id)
        if not saved_data:
            return jsonify({'error': 'No saved calendar data found. Generate calendars first.'}), 404

        bg_dates, days = _get_background_days_and_period(saved_data)

        if not bg_dates:
            return jsonify({'transits': [], 'background_days': [], 'total_filtered': 0})

        start_date = datetime.combine(date.today(), datetime.min.time())
        end_date = datetime.combine(date.today() + timedelta(days=days), datetime.min.time())

        try:
            from microtransits.yp import process_transits
        except ImportError as ie:
            return jsonify({'error': f'Yogi Point module unavailable: {ie}'}), 500

        all_transits = process_transits(start_date, end_date)

        filtered = []
        for t in all_transits:
            t_date = _extract_date_part(
                str(t.get('start', '')) or str(t.get('datetime', '')) or str(t.get('date', ''))
            )
            if t_date and t_date in bg_dates:
                filtered.append(t)

        return jsonify({
            'calendar_type': 'Yogi_Point_Power_Days',
            'transits': filtered,
            'total_filtered': len(filtered),
            'total_unfiltered': len(all_transits),
            'background_days': sorted(bg_dates),
            'period': {
                'start_date': date.today().isoformat(),
                'end_date': (date.today() + timedelta(days=days)).isoformat(),
            },
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@power_days_bp.route('/api/power-days/part-of-fortune', methods=['GET'])
def get_part_of_fortune_power_days():
    try:
        if not session.get('authenticated'):
            return jsonify({'error': 'Authentication required'}), 401

        user_id = get_effective_user_id()
        if not user_id:
            return jsonify({'error': 'User ID not found'}), 400

        saved_data = db_manager.get_calendar_data(user_id)
        if not saved_data:
            return jsonify({'error': 'No saved calendar data found. Generate calendars first.'}), 404

        bg_dates, days = _get_background_days_and_period(saved_data)

        if not bg_dates:
            return jsonify({'transits': [], 'background_days': [], 'total_filtered': 0})

        start_date = datetime.combine(date.today(), datetime.min.time())
        end_date = datetime.combine(date.today() + timedelta(days=days), datetime.min.time())

        try:
            import microtransits.wb1 as wb1_module
        except ImportError as ie:
            return jsonify({'error': f'Part of Fortune module unavailable: {ie}'}), 500

        user_profile = UserProfile.query.filter_by(email=user_id).first()
        if not user_profile or not user_profile.birth_date:
            return jsonify({'error': 'Profile with birth data required for Part of Fortune'}), 400

        birth_dt = datetime.combine(user_profile.birth_date, datetime.min.time())
        if user_profile.birth_time:
            birth_dt = datetime.combine(user_profile.birth_date, user_profile.birth_time)

        wb1_module.BIRTH_DATE = birth_dt
        if user_profile.current_latitude and user_profile.current_longitude:
            wb1_module.TRANSIT_LOCATION = (
                float(user_profile.current_latitude),
                float(user_profile.current_longitude)
            )

        all_transits = wb1_module.process_transits(start_date, end_date)

        filtered = []
        for t in all_transits:
            t_date = _extract_date_part(
                str(t.get('start', '')) or str(t.get('datetime', '')) or str(t.get('date', ''))
            )
            if t_date and t_date in bg_dates:
                filtered.append(t)

        return jsonify({
            'calendar_type': 'Part_of_Fortune_Power_Days',
            'transits': filtered,
            'total_filtered': len(filtered),
            'total_unfiltered': len(all_transits),
            'background_days': sorted(bg_dates),
            'period': {
                'start_date': date.today().isoformat(),
                'end_date': (date.today() + timedelta(days=days)).isoformat(),
            },
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@power_days_bp.route('/api/calendar-feeds', methods=['GET'])
def get_calendar_feeds():
    try:
        if not session.get('authenticated'):
            return jsonify({'error': 'Authentication required'}), 401

        user_id = get_effective_user_id()
        if not user_id:
            return jsonify({'error': 'User ID not found'}), 400

        base_url = request.host_url.rstrip('/')
        feeds = db_manager.get_user_subscriptions(user_id, base_url)
        return jsonify({'feeds': feeds})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@power_days_bp.route('/api/pti-calendar', methods=['GET'])
def get_pti_calendar():
    try:
        if not session.get('authenticated'):
            return jsonify({'error': 'Not authenticated'}), 401
        user_id = get_effective_user_id()
        if not user_id:
            return jsonify({'error': 'User ID not found'}), 400

        saved = db_manager.get_calendar_data(user_id)
        if not saved:
            return jsonify({'error': 'No calendar data found. Please generate calendars first.'}), 404

        calendars = saved.get('calendars', {})
        pti = calendars.get('pti_collective', calendars.get('pti', {}))
        pti_data = pti.get('data', pti) if isinstance(pti, dict) else {}
        results = pti_data.get('results', [])

        if not results:
            return jsonify({'error': 'No PTI data found. Please regenerate calendars.'}), 404

        classification_order = ['PTI Best', 'PTI Go', 'Normal', 'PTI Slow', 'PTI Worst']
        counts = {}
        days_by_class = {}
        formatted_days = []

        for r in results:
            cls = r.get('classification', 'Normal')
            counts[cls] = counts.get(cls, 0) + 1
            if cls not in days_by_class:
                days_by_class[cls] = []

            day_entry = {
                'date': r.get('date'),
                'classification': cls,
                'score': r.get('score'),
                'reason': r.get('reason', ''),
                'details': r.get('details', {}),
            }
            days_by_class[cls].append(day_entry)
            formatted_days.append(day_entry)

        formatted_days.sort(key=lambda d: d.get('date', ''))

        summary = []
        for cls in classification_order:
            summary.append({'classification': cls, 'count': counts.get(cls, 0)})

        return jsonify({
            'days': formatted_days,
            'total_days': len(formatted_days),
            'summary': summary,
            'period': pti_data.get('period', {}),
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
