from flask import Blueprint, request, session, jsonify
from database.manager import db_manager
from datetime import date
import calendar as cal_mod

manual_cal_bp = Blueprint('manual_calendar', __name__)

MAGI_CLASSIFICATIONS = ['Best', 'Good', 'Slow', 'Worst']
VEDIC_CLASSIFICATIONS = ['GO', 'MILD GO', 'BUILD', 'STOP', 'MEGA RED']


def _require_admin():
    user_info = session.get('user_info', {})
    if not user_info.get('is_admin'):
        return False
    return True


@manual_cal_bp.route('/api/manual-calendar', methods=['POST'])
def save_manual_calendar():
    if not _require_admin():
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    calendar_type = data.get('calendar_type', '').strip().lower()
    category = data.get('category', 'COLLECTIVE').strip().upper()
    year = data.get('year')
    month = data.get('month')

    if calendar_type not in ('magi', 'vedic'):
        return jsonify({'error': 'calendar_type must be "magi" or "vedic"'}), 400
    if not year or not month:
        return jsonify({'error': 'year and month required'}), 400

    try:
        year = int(year)
        month = int(month)
        if month < 1 or month > 12:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid year or month'}), 400

    valid_cls = MAGI_CLASSIFICATIONS if calendar_type == 'magi' else VEDIC_CLASSIFICATIONS
    classifications = {}
    seen_days = set()
    tiers = data.get('tiers', {})
    for tier_name, day_str in tiers.items():
        if tier_name not in valid_cls:
            continue
        if isinstance(day_str, str):
            day_numbers = _parse_day_numbers(day_str, year, month)
        elif isinstance(day_str, list):
            day_numbers = [int(d) for d in day_str if _valid_day(d, year, month)]
        else:
            continue
        day_numbers = [d for d in day_numbers if d not in seen_days]
        seen_days.update(day_numbers)
        if day_numbers:
            classifications[tier_name] = day_numbers

    admin_email = session.get('user_info', {}).get('email', '')
    success = db_manager.save_manual_calendar(
        calendar_type=calendar_type,
        category=category,
        year=year,
        month=month,
        classifications=classifications,
        created_by=admin_email,
    )

    if success:
        total = sum(len(v) for v in classifications.values())
        return jsonify({'success': True, 'entries_saved': total})
    return jsonify({'error': 'Failed to save'}), 500


@manual_cal_bp.route('/api/manual-calendar', methods=['GET'])
def get_manual_calendar():
    if not _require_admin():
        return jsonify({'error': 'Admin access required'}), 403

    calendar_type = request.args.get('calendar_type', 'magi').strip().lower()
    category = request.args.get('category', 'COLLECTIVE').strip().upper()
    year = request.args.get('year')
    month = request.args.get('month')

    if not year or not month:
        return jsonify({'error': 'year and month required'}), 400

    try:
        year = int(year)
        month = int(month)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid year or month'}), 400

    first_day = date(year, month, 1)
    last_day = date(year, month, cal_mod.monthrange(year, month)[1])

    entries = db_manager.get_manual_calendar(calendar_type, category, first_day, last_day)

    tiers = {}
    for e in entries:
        cls = e['classification']
        day_num = int(e['date'].split('-')[2])
        if cls not in tiers:
            tiers[cls] = []
        tiers[cls].append(day_num)

    return jsonify({
        'calendar_type': calendar_type,
        'category': category,
        'year': year,
        'month': month,
        'tiers': tiers,
        'entries': entries,
    })


@manual_cal_bp.route('/api/manual-calendar/months', methods=['GET'])
def get_manual_calendar_months():
    if not _require_admin():
        return jsonify({'error': 'Admin access required'}), 403

    calendar_type = request.args.get('calendar_type', 'magi').strip().lower()
    months = db_manager.get_manual_calendar_months(calendar_type)
    return jsonify({'months': months})


def _parse_day_numbers(day_str, year, month):
    nums = []
    max_day = cal_mod.monthrange(year, month)[1]
    for part in day_str.replace(';', ',').split(','):
        part = part.strip()
        if not part:
            continue
        try:
            d = int(part)
            if 1 <= d <= max_day:
                nums.append(d)
        except ValueError:
            continue
    return nums


def _valid_day(d, year, month):
    try:
        max_day = cal_mod.monthrange(year, month)[1]
        return 1 <= int(d) <= max_day
    except (ValueError, TypeError):
        return False
