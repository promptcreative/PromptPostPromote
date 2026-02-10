"""Microtransits blueprint — Yogi Point, Part of Fortune, Transit Audit, Selected Day Analysis."""

import traceback
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, session
from helpers.utils import get_user_calendar_range
from database.manager import db_manager

microtransits_bp = Blueprint('microtransits', __name__)


def _parse_date_range(data):
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    days = data.get('days')

    if not start_date_str:
        user_info = session.get('user_info', {})
        user_email = user_info.get('email')
        start_date_obj, end_date_obj, user_days = get_user_calendar_range(user_email)
        start_date_str = start_date_obj.strftime('%Y-%m-%d')
        if not end_date_str:
            end_date_str = end_date_obj.strftime('%Y-%m-%d')
        if not days:
            days = user_days

    if not days:
        days = 7

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    except ValueError:
        return None, None, days, ('Invalid start_date format. Use YYYY-MM-DD', start_date_str)

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        except ValueError:
            return None, None, days, ('Invalid end_date format. Use YYYY-MM-DD', end_date_str)
    else:
        end_date = start_date + timedelta(days=days)

    return start_date, end_date, days, None


def _extract_date_part(date_string):
    if not date_string:
        return None
    if 'T' in date_string:
        return date_string.split('T')[0]
    if ' ' in date_string:
        return date_string.split(' ')[0]
    return date_string


def _deduplicate_transits(transits):
    def _unique_key(t):
        date_val = t.get('datetime', '') or t.get('date', '') or t.get('start_time', '')
        time_val = t.get('time', '') or (t.get('start_time', '')[:16] if t.get('start_time') else '')
        transit_type = t.get('type', '') or t.get('description', '')
        return f"{str(date_val)[:10]}|{time_val}|{transit_type}"

    seen = set()
    result = []
    for t in transits:
        key = _unique_key(t)
        if key not in seen:
            seen.add(key)
            result.append(t)
    return result


@microtransits_bp.route('/yogi-point-transits', methods=['POST'])
def get_yogi_point_transits():
    """Get Yogi Point transits for a date range."""
    try:
        data = request.get_json() or {}
        start_date, end_date, days, err = _parse_date_range(data)
        if err:
            return jsonify({'error': err[0], 'provided': err[1]}), 400

        try:
            from microtransits.yp import process_transits
        except ImportError as ie:
            return jsonify({'error': f'Yogi Point module unavailable: {ie}'}), 500

        yogi_transits = process_transits(start_date, end_date)

        return jsonify({
            'calendar_type': 'Yogi_Point_Transits',
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'days_processed': (end_date - start_date).days,
            'total_transits': len(yogi_transits),
            'transits': yogi_transits,
            'metadata': {
                'scripts_used': ['vb2.py', 'yp.py', 'wb1.py'],
                'generated_at': datetime.now().isoformat(),
                'description': 'Yogi Point transit events combining Vedic and Western calculations'
            }
        })

    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@microtransits_bp.route('/part-of-fortune-transits', methods=['POST'])
def get_part_of_fortune_transits():
    """Get Part of Fortune transits for a date range."""
    try:
        data = request.get_json() or {}
        start_date, end_date, days, err = _parse_date_range(data)
        if err:
            return jsonify({'error': err[0], 'provided': err[1]}), 400

        try:
            from microtransits.wb1 import process_transits
        except ImportError as ie:
            return jsonify({'error': f'Part of Fortune module unavailable: {ie}'}), 500

        pof_transits = process_transits(start_date, end_date)

        return jsonify({
            'calendar_type': 'Part_of_Fortune_Transits',
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'days_processed': (end_date - start_date).days,
            'total_transits': len(pof_transits),
            'transits': pof_transits,
            'metadata': {
                'scripts_used': ['wb1.py', 'wb2.py', 'wb3.py'],
                'generated_at': datetime.now().isoformat(),
                'description': 'Part of Fortune transit events from Western astrological calculations'
            }
        })

    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@microtransits_bp.route('/api/transit-audit', methods=['POST'])
def transit_audit():
    """Transit Audit Tool — run all microtransit scripts and categorise results."""
    try:
        data = request.get_json() or {}

        start_date_str = data.get('start_date')
        days = data.get('days', 7)
        birth_date = data.get('birth_date', '1973-03-09')
        birth_time = data.get('birth_time', '16:56')
        birth_location = data.get('birth_location', {'latitude': 29.2108, 'longitude': -81.0228})
        current_location = data.get('current_location', {'latitude': 37.8018, 'longitude': -80.4456})

        if not start_date_str:
            start_date = datetime.now().date()
        else:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()

        end_date = start_date + timedelta(days=days)
        total_days = days

        audit_report = {
            'audit_date': datetime.now().isoformat(),
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': total_days
            },
            'raw_transits': {},
            'categorization': {
                'astrobatching': [],
                'yogi_point': [],
                'part_of_fortune': []
            },
            'issues': {
                'missing': [],
                'duplicates': [],
                'miscategorized': []
            },
            'statistics': {}
        }

        script_modules = {
            'vb1.py': ('microtransits.vb1', 'calculate_vb1_transits'),
            'vb2.py': ('microtransits.vb2', 'calculate_vb2_transits'),
            'wb1.py': ('microtransits.wb1', 'calculate_wb1_transits'),
            'wb2.py': ('microtransits.wb2', 'calculate_wb2_transits'),
            'wb3.py': ('microtransits.wb3', 'calculate_wb3_transits'),
            'yp.py':  ('microtransits.yp',  'process_transits'),
        }

        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.min.time())
        days_span = (end_dt - start_dt).days + 1

        for script_name, (mod_path, func_name) in script_modules.items():
            print(f"\n--- AUDITING {script_name} ---")
            try:
                import importlib
                mod = importlib.import_module(mod_path)
                calc_fn = getattr(mod, func_name)

                if script_name == 'yp.py':
                    script_transits = calc_fn(start_dt, end_dt)
                elif script_name == 'vb1.py':
                    script_transits = calc_fn(
                        birth_date, birth_location['latitude'], birth_location['longitude'],
                        current_location['latitude'], current_location['longitude'],
                        start_dt, end_dt)
                elif script_name == 'wb2.py':
                    script_transits = calc_fn(
                        birth_date, birth_location['latitude'], birth_location['longitude'],
                        current_location['latitude'], current_location['longitude'],
                        start_dt, end_dt)
                else:
                    script_transits = calc_fn(
                        birth_date, birth_time,
                        birth_location['latitude'], birth_location['longitude'],
                        start_date.isoformat(), days_span)

                audit_report['raw_transits'][script_name] = []
                for transit in script_transits:
                    transit_info = {
                        'script': script_name,
                        'type': transit.get('type', 'Unknown'),
                        'transit_code': transit.get('transit_code', ''),
                        'datetime': transit.get('datetime', ''),
                        'timestamp': str(transit.get('timestamp', ''))
                    }
                    audit_report['raw_transits'][script_name].append(transit_info)

                print(f"  Found {len(script_transits)} transits")

            except Exception as e:
                print(f"  ERROR running {script_name}: {e}")
                audit_report['issues']['missing'].append(f"Failed to run {script_name}: {str(e)}")

        for script_transits in audit_report['raw_transits'].values():
            for transit in script_transits:
                ttype = transit.get('type', '')
                tcode = transit.get('transit_code', '')
                if 'Yogi' in ttype or 'YOGI' in tcode:
                    audit_report['categorization']['yogi_point'].append(transit)
                if 'POF' in tcode or 'Fortune' in ttype:
                    audit_report['categorization']['part_of_fortune'].append(transit)

        total_raw = sum(len(t) for t in audit_report['raw_transits'].values())
        audit_report['statistics'] = {
            'total_raw_transits': total_raw,
            'total_yogi': len(audit_report['categorization']['yogi_point']),
            'total_pof': len(audit_report['categorization']['part_of_fortune']),
            'scripts_run': len(audit_report['raw_transits']),
            'issues_found': (
                len(audit_report['issues']['missing']) +
                len(audit_report['issues']['duplicates']) +
                len(audit_report['issues']['miscategorized'])
            )
        }

        return jsonify(audit_report)

    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@microtransits_bp.route('/generate-selected-day-analysis', methods=['POST'])
def generate_selected_day_analysis():
    """Generate targeted microtransit analysis for user-selected days only."""
    try:
        data = request.get_json() or {}

        selected_dates = data.get('selected_dates', [])
        birth_date = data.get('birth_date')
        birth_time = data.get('birth_time')
        birth_latitude = float(data.get('birth_latitude', 25.76))
        birth_longitude = float(data.get('birth_longitude', -80.19))

        if not selected_dates:
            return jsonify({'error': 'No dates selected for analysis'}), 400
        if not birth_date or not birth_time:
            return jsonify({'error': 'Birth data required for targeted analysis'}), 400

        start_date = min(selected_dates)
        end_date = max(selected_dates)
        days_span = (datetime.strptime(end_date, '%Y-%m-%d') -
                     datetime.strptime(start_date, '%Y-%m-%d')).days + 1

        selected_day_results = {
            'analysis_type': 'Selected_Day_Targeted_Analysis',
            'selected_dates': selected_dates,
            'birth_info': {'date': birth_date, 'time': str(birth_time)},
            'calendars': {}
        }

        # Yogi Point Transits
        try:
            from microtransits.vb2 import calculate_vb2_transits, calculate_yogi_point_transits
            from microtransits.wb1 import calculate_wb1_transits

            all_yogi_transits = []

            try:
                vb2_transits = calculate_vb2_transits(
                    birth_date, birth_time, birth_latitude, birth_longitude,
                    start_date, days_span)
                all_yogi_transits.extend(vb2_transits)
            except Exception as e:
                print(f"VB2 transits error: {e}")

            try:
                yp_transits = calculate_yogi_point_transits(
                    birth_date, birth_time, birth_latitude, birth_longitude,
                    start_date, days_span)
                all_yogi_transits.extend(yp_transits)
            except Exception as e:
                print(f"YP transits error: {e}")

            try:
                wb1_transits = calculate_wb1_transits(
                    birth_date, birth_time, birth_latitude, birth_longitude,
                    start_date, days_span)
                yogi_wb1 = [
                    t for t in wb1_transits
                    if ('Yogi' in str(t.get('type', '')) or t.get('script', '') == 'wb1.py')
                ]
                all_yogi_transits.extend(yogi_wb1)
            except Exception as e:
                print(f"WB1 transits error: {e}")

            filtered_yogi = [
                t for t in all_yogi_transits
                if _extract_date_part(
                    t.get('datetime', '') or t.get('date', '') or t.get('start_time', '')
                ) in selected_dates
            ]
            filtered_yogi = _deduplicate_transits(filtered_yogi)

            selected_day_results['calendars']['yogi_point'] = {
                'calendar_type': 'Yogi_Point_Transits',
                'total_transits': len(filtered_yogi),
                'selected_dates_only': True,
                'transits': filtered_yogi
            }
        except Exception as e:
            selected_day_results['calendars']['yogi_point'] = {'error': str(e)}

        # Part of Fortune Transits
        try:
            from microtransits.wb1 import calculate_wb1_transits
            from microtransits.wb2 import calculate_wb2_transits
            from microtransits.wb3 import calculate_wb3_transits

            all_pof_transits = []

            try:
                wb1_transits = calculate_wb1_transits(
                    birth_date, birth_time, birth_latitude, birth_longitude,
                    start_date, days_span)
                pof_wb1 = [
                    t for t in wb1_transits
                    if ('POF' in str(t.get('type', '')) or
                        'Fortune' in str(t.get('type', '')) or
                        t.get('script', '') == 'wb1.py')
                ]
                all_pof_transits.extend(pof_wb1)
            except Exception as e:
                print(f"WB1 POF error: {e}")

            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = start_dt + timedelta(days=days_span)
                wb2_transits = calculate_wb2_transits(
                    birth_date, birth_latitude, birth_longitude,
                    40.7128, -74.006, start_dt, end_dt)
                pof_wb2 = [
                    t for t in wb2_transits
                    if ('POF' in str(t.get('type', '')) or
                        'Fortune' in str(t.get('type', '')) or
                        'Fortune' in str(t.get('description', '')) or
                        t.get('script', '') == 'wb2.py')
                ]
                all_pof_transits.extend(pof_wb2)
            except Exception as e:
                print(f"WB2 POF error: {e}")

            try:
                wb3_transits = calculate_wb3_transits(
                    birth_date, birth_time, birth_latitude, birth_longitude,
                    start_date, days_span)
                pof_wb3 = [
                    t for t in wb3_transits
                    if ('POF' in str(t.get('type', '')) or
                        'Fortune' in str(t.get('type', '')) or
                        'Fortune' in str(t.get('description', '')) or
                        t.get('script', '') == 'wb3.py')
                ]
                all_pof_transits.extend(pof_wb3)
            except Exception as e:
                print(f"WB3 POF error: {e}")

            filtered_pof = [
                t for t in all_pof_transits
                if _extract_date_part(
                    t.get('datetime', '') or t.get('date', '') or t.get('start_time', '')
                ) in selected_dates
            ]
            filtered_pof = _deduplicate_transits(filtered_pof)

            selected_day_results['calendars']['part_of_fortune'] = {
                'calendar_type': 'Part_of_Fortune_Transits',
                'total_transits': len(filtered_pof),
                'selected_dates_only': True,
                'transits': filtered_pof
            }
        except Exception as e:
            selected_day_results['calendars']['part_of_fortune'] = {'error': str(e)}

        if session.get('authenticated'):
            user_info = session.get('user_info', {})
            user_id = user_info.get('email')
            if user_id:
                updated = db_manager.update_background_days(user_id, selected_dates)
                selected_day_results['background_days_saved'] = bool(updated)
                saved = db_manager.save_precision_timing(user_id, selected_day_results)
                selected_day_results['precision_timing_saved'] = bool(saved)

        return jsonify(selected_day_results)

    except Exception as e:
        print(f"Error in generate_selected_day_analysis: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@microtransits_bp.route('/save-background-days', methods=['POST'])
def save_background_days():
    """Save selected background days for authenticated user."""
    try:
        if not session.get('authenticated'):
            return jsonify({'error': 'Authentication required'}), 401

        user_info = session.get('user_info', {})
        user_id = user_info.get('email')
        if not user_id:
            return jsonify({'error': 'User ID not found'}), 400

        data = request.get_json() or {}
        background_days = data.get('background_days', [])

        if not isinstance(background_days, list):
            return jsonify({'error': 'background_days must be a list'}), 400

        success = db_manager.update_background_days(user_id, background_days)

        if success:
            return jsonify({
                'status': 'success',
                'saved_count': len(background_days),
                'background_days': background_days
            })
        else:
            return jsonify({
                'status': 'warning',
                'message': 'No calendar data found to update. Generate calendars first.'
            }), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500
