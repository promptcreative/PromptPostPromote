"""
Calendar generation routes blueprint
Ports calendar endpoints from src/api/astrobatch_api.py
"""

import traceback
from datetime import datetime, date, timedelta

from flask import Blueprint, request, jsonify, session
from database.models import db, UserProfile
from database.manager import db_manager
from helpers.utils import (
    get_user_calendar_range, get_two_month_range,
    make_json_serializable, normalize_dashboard_data,
    apply_double_go_to_combined_results
)
from helpers.dashboard import generate_dashboard_core, normalize_for_ui

calendars_bp = Blueprint('calendars', __name__)


@calendars_bp.route('/generate-collective-calendar', methods=['POST'])
def generate_collective_calendar():
    """Generate collective calendar using PTI Collective Calendar"""
    try:
        data = request.get_json() or {}

        from core.magi_collective import PTICollectiveCalendar

        location_name = data.get('location')
        coordinates = data.get('coordinates')

        if not location_name and not coordinates:
            return jsonify({
                'error': 'Either location name or coordinates required',
                'example': {'location': 'Miami, FL'}
            }), 400

        user_info = session.get('user_info', {})
        user_email = user_info.get('email')
        start_date, end_date, total_days = get_user_calendar_range(user_email)

        if location_name:
            lat = data.get('latitude', 25.76)
            lon = data.get('longitude', -80.19)
            location_info = {
                'name': location_name,
                'latitude': lat,
                'longitude': lon,
                'timezone': 'America/New_York'
            }
        else:
            if coordinates and len(coordinates) == 2:
                lat, lon = coordinates
                location_info = {
                    'name': f'{lat:.4f}°N, {lon:.4f}°W',
                    'latitude': lat,
                    'longitude': lon,
                    'timezone': 'America/New_York'
                }
            else:
                return jsonify({
                    'error': 'Invalid coordinates format. Expected [lat, lon]'
                }), 400

        pti_system = PTICollectiveCalendar()
        start_dt = datetime.combine(start_date, datetime.min.time())
        analysis_results = pti_system.generate_calendar(start_dt, total_days)

        class_counts = {}
        for result in analysis_results:
            classification = result.get('classification', 'NEUTRAL')
            class_counts[classification] = class_counts.get(classification, 0) + 1

        timing_data = []
        for result in analysis_results:
            date_str = result.get('date', str(result.get('date', 'unknown')))
            classification = result.get('classification', 'NEUTRAL')

            timing_entry = {
                'date': date_str,
                'pti_level': classification,
                'magi_classification': classification,
                'score': result.get('score', 0.0),
                'description': result.get('reason', result.get('description', '')),
                'emoji': result.get('emoji', ''),
                'color': result.get('color', ''),
                'key_factors': result.get('key_factors', []),
                'classification_reason': result.get('reason', ''),
                'major_aspects_count': len(result.get('aspects', [])),
                'chiron_aspects_count': 0,
                'midpoints_count': 0,
                'details': result.get('details', {})
            }
            timing_data.append(timing_entry)

        serializable_analysis = {
            'location_info': location_info,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': total_days
            },
            'summary': {
                'total_days': len(analysis_results),
                'class_counts': class_counts
            },
            'timing_data': timing_data,
            'daily_results': {
                result.get('date', 'unknown'): result.get('classification', 'NEUTRAL')
                for result in analysis_results
            }
        }

        return jsonify({
            'calendar_type': 'PTI_Collective',
            'analysis': serializable_analysis,
            'data_processing': 'in-memory only (no files created)',
            'generated_at': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@calendars_bp.route('/generate-personal-calendar', methods=['POST'])
def generate_personal_calendar():
    """Generate personal transit calendar using EnhancedPersonalTransitCalculator"""
    try:
        data = request.get_json() or {}

        from personal_calendar.personal_transit_yp import EnhancedPersonalTransitCalculator

        required_fields = ['birth_date', 'birth_time', 'birth_latitude', 'birth_longitude']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400

        birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
        birth_time = datetime.strptime(data['birth_time'], '%H:%M').time()
        birth_latitude = float(data['birth_latitude'])
        birth_longitude = float(data['birth_longitude'])
        current_latitude = float(data.get('current_latitude', birth_latitude))
        current_longitude = float(data.get('current_longitude', birth_longitude))
        timezone = float(data.get('timezone', -5.0))

        user_info = session.get('user_info', {})
        user_email = user_info.get('email')
        start_date, end_date, total_days = get_user_calendar_range(user_email)

        calculator = EnhancedPersonalTransitCalculator()

        birth_chart = calculator.calculate_birth_chart(
            birth_date, birth_time, birth_latitude, birth_longitude, timezone
        )

        if not birth_chart:
            return jsonify({'error': 'Could not calculate birth chart'}), 500

        calendar_data = calculator.generate_personal_calendar(
            birth_chart, start_date, end_date,
            current_latitude, current_longitude, timezone
        )

        json_calendar = {}
        for date_str, day_data in calendar_data.items():
            if day_data.get('personal_score'):
                json_calendar[date_str] = {
                    'date': date_str,
                    'weekday': day_data['weekday'],
                    'quality': day_data['personal_score']['quality'],
                    'score': day_data['personal_score']['score'],
                    'factors': day_data['personal_score']['factors'],
                    'moon_house': day_data['personal_score']['moon_house'],
                    'subject_line': day_data['personal_score'].get('subject_line'),
                    'yogi_enhancement': day_data['personal_score'].get('yogi_enhancement', ''),
                    'awareness_message': day_data['personal_score'].get('awareness_message', '')
                }
            else:
                json_calendar[date_str] = {
                    'date': date_str,
                    'weekday': day_data['weekday'],
                    'quality': 'error',
                    'score': 0.0,
                    'factors': ['Error calculating day score'],
                    'moon_house': 0,
                    'subject_line': 'Personal - error',
                    'yogi_enhancement': '',
                    'awareness_message': 'Unable to calculate personal score for this day'
                }

        return jsonify({
            'calendar_type': 'Enhanced_Personal_Transit',
            'birth_chart': birth_chart,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days': json_calendar,
            'generated_at': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@calendars_bp.route('/generate-electional-calendar', methods=['POST'])
def generate_electional_calendar():
    """Stub - electional calendar not ported to rebuild"""
    return jsonify({
        'error': 'Electional calendar is not available in this version',
        'message': 'This calendar type has not been ported to the rebuild.'
    }), 501


@calendars_bp.route('/generate-combined-calendar', methods=['POST'])
def generate_combined_calendar():
    """Generate Combined Electional+Personal Calendar"""
    try:
        data = request.get_json() or {}

        required_fields = ['birth_date', 'birth_time', 'birth_latitude', 'birth_longitude']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required for combined analysis'}), 400

        birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
        birth_time = datetime.strptime(data['birth_time'], '%H:%M').time()
        birth_latitude = float(data['birth_latitude'])
        birth_longitude = float(data['birth_longitude'])

        location_name = data.get('location')
        coordinates = data.get('coordinates')

        if 'days' in data:
            days = data.get('days')
        else:
            _, _, days = get_two_month_range()

        current_lat = float(data.get('current_latitude', birth_latitude))
        current_lon = float(data.get('current_longitude', birth_longitude))

        if coordinates and len(coordinates) >= 2:
            current_lat, current_lon = coordinates[:2]

        if 'days' in data:
            start_date_val = date.today()
            end_date_val = start_date_val + timedelta(days=days - 1)
        else:
            start_date_val, end_date_val, _ = get_two_month_range()

        dashboard_data = generate_dashboard_core({
            'birth_date': data['birth_date'],
            'birth_time': data['birth_time'],
            'birth_latitude': birth_latitude,
            'birth_longitude': birth_longitude,
            'latitude': current_lat,
            'longitude': current_lon,
            'location': location_name,
            'days': days,
        })

        timing_data = []
        combined_cal = (dashboard_data or {}).get('calendars', {}).get('combined', {})
        combined_results = combined_cal.get('data', {}).get('results', []) or combined_cal.get('results', [])

        for day_result in combined_results:
            if not isinstance(day_result, dict):
                continue
            timing_data.append({
                'date': day_result.get('date', ''),
                'power_level': day_result.get('combined_quality', 'neutral'),
                'description': day_result.get('reason', ''),
                'combined_score': day_result.get('combined_score', 0),
                'is_double_go': day_result.get('is_double_go', False),
                'system_breakdown': day_result.get('system_breakdown', {}),
            })

        result = {
            'calendar_type': 'Combined_All_Calendar',
            'birth_info': {
                'date': birth_date.isoformat(),
                'time': str(birth_time),
                'location': {
                    'latitude': birth_latitude,
                    'longitude': birth_longitude
                }
            },
            'location': {
                'name': location_name,
                'latitude': current_lat,
                'longitude': current_lon
            },
            'period': {
                'start_date': start_date_val.isoformat(),
                'end_date': end_date_val.isoformat(),
                'days': days
            },
            'analysis': {
                'timing_data': timing_data,
                'generated': len(timing_data) > 0,
                'summary': {
                    'total_days': len(timing_data),
                    'power_levels': len([t for t in timing_data if t['power_level'] != 'neutral']),
                    'avg_score': sum(t.get('combined_score', 0) for t in timing_data) / max(len(timing_data), 1)
                }
            },
            'timing_data': timing_data,
        }

        return jsonify(make_json_serializable(result))

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@calendars_bp.route('/generate-dashboard-calendar', methods=['POST'])
def generate_dashboard_calendar():
    """Generate dashboard calendar data"""
    try:
        data = request.get_json(silent=True) or {}
        user_info = session.get('user_info', {})
        user_id = user_info.get('email') or None
        results = generate_dashboard_core(data, user_id=user_id)
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@calendars_bp.route('/generate-all-calendars', methods=['POST'])
def generate_all_calendars():
    """Generate all calendars for authenticated user (triggered from dashboard)"""
    try:
        if not session.get('authenticated'):
            return jsonify({'status': 'error', 'error': 'Authentication required'}), 401

        user_info = session.get('user_info', {})
        user_id = user_info.get('email')

        if not user_id:
            return jsonify({'status': 'error', 'error': 'User ID not found'}), 400

        user_profile = UserProfile.query.filter_by(email=user_id).first()
        if not user_profile or not user_profile.birth_date:
            return jsonify({'status': 'error', 'error': 'Profile not complete'}), 400

        profile_payload = {
            'birth_date': user_profile.birth_date.isoformat() if user_profile.birth_date else None,
            'birth_time': user_profile.birth_time.isoformat() if user_profile.birth_time else None,
            'birth_latitude': getattr(user_profile, 'birth_latitude', None),
            'birth_longitude': getattr(user_profile, 'birth_longitude', None),
            'latitude': getattr(user_profile, 'current_latitude', None),
            'longitude': getattr(user_profile, 'current_longitude', None),
            'location': getattr(user_profile, 'current_location_name', None),
            'force_regenerate': True
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

        if core_result and not core_result.get('error'):
            return jsonify({'status': 'success', 'message': 'Calendars generated successfully'})
        else:
            return jsonify({'status': 'error', 'error': core_result.get('error', 'Generation failed')})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': str(e)}), 500


@calendars_bp.route('/get-saved-calendar', methods=['GET'])
def get_saved_calendar():
    """Retrieve saved calendar data for authenticated user"""
    try:
        if not session.get('authenticated'):
            return jsonify({'error': 'Authentication required'}), 401

        user_info = session.get('user_info', {})
        user_id = user_info.get('email')

        if not user_id:
            return jsonify({'error': 'User ID not found'}), 400

        saved_data = db_manager.get_calendar_data(user_id)

        if saved_data:
            calendars = saved_data.get('calendars', {})
            if calendars:
                combined_cal = calendars.get('combined', {})
                combined_results = (
                    combined_cal.get('data', {}).get('results', [])
                    or combined_cal.get('results', [])
                )

                if combined_results:
                    pti_cal = calendars.get('pti_collective', {}) or calendars.get('pti', {})
                    vedic_cal = calendars.get('vedic_pti', {}) or calendars.get('goslow', {})

                    pti_data = (
                        pti_cal.get('data', {}).get('timing_data', [])
                        or pti_cal.get('results', [])
                        or pti_cal.get('timing_data', [])
                    )
                    vedic_data = (
                        vedic_cal.get('data', {}).get('results', [])
                        or vedic_cal.get('results', [])
                    )

                    pti_by_date = {
                        item.get("date"): item
                        for item in pti_data
                        if isinstance(item, dict) and item.get("date")
                    } if pti_data else {}
                    vedic_by_date = {
                        item.get("date"): item
                        for item in vedic_data
                        if isinstance(item, dict) and item.get("date")
                    } if vedic_data else {}

                    apply_double_go_to_combined_results(combined_results, pti_by_date, vedic_by_date)

            return jsonify({
                'status': 'success',
                'data': saved_data,
                'from_cache': True
            })
        else:
            return jsonify({
                'status': 'not_found',
                'message': 'No saved calendar data found. Please generate new calendars.'
            }), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@calendars_bp.route('/list-calendars', methods=['GET'])
def list_available_calendars():
    """List all available calendar types"""
    return jsonify({
        'available_calendars': [
            {
                'type': 'collective',
                'name': 'PTI Collective Calendar',
                'endpoint': '/generate-collective-calendar',
                'description': 'Planetary parallel analysis for optimal timing',
                'required_params': ['location OR coordinates', 'days']
            },
            {
                'type': 'personal',
                'name': 'Enhanced Personal Transit Calendar',
                'endpoint': '/generate-personal-calendar',
                'description': 'Personalized transit calendar with Yogi/Avayogi analysis',
                'required_params': ['birth_date', 'birth_time', 'birth_latitude', 'birth_longitude']
            },
            {
                'type': 'combined',
                'name': 'Combined Calendar',
                'endpoint': '/generate-combined-calendar',
                'description': 'Hybrid methodology combining location + personal factors',
                'required_params': [
                    'birth_date', 'birth_time', 'birth_latitude',
                    'birth_longitude', 'location OR coordinates'
                ]
            },
            {
                'type': 'dashboard',
                'name': 'Dashboard Calendar',
                'endpoint': '/generate-dashboard-calendar',
                'description': 'Complete 6-calendar dashboard generation',
                'required_params': []
            }
        ]
    })


@calendars_bp.route('/calendars/clear-and-regenerate', methods=['POST'])
def clear_and_regenerate_calendars():
    """Clear current calendar data and generate fresh calendars"""
    try:
        if not session.get('authenticated'):
            return jsonify({
                'status': 'error',
                'message': 'Authentication required to clear calendar data'
            }), 401

        user_info = session.get('user_info', {})
        user_id = user_info.get('email')

        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'Valid user ID required to clear calendar data'
            }), 400

        now = datetime.now()
        current_year = now.year
        current_month = now.month

        success_current = db_manager.clear_calendar_data(user_id, current_year, current_month)

        next_month = current_month + 1
        next_year = current_year
        if next_month > 12:
            next_month = 1
            next_year = current_year + 1

        success_next = db_manager.clear_calendar_data(user_id, next_year, next_month)

        if not (success_current and success_next):
            return jsonify({
                'status': 'error',
                'message': 'Failed to clear all calendar data'
            }), 500

        return jsonify({
            'status': 'success',
            'message': 'Calendar data cleared successfully. Ready for regeneration.',
            'user_id': user_id[:10] + '...' if len(user_id) > 10 else user_id,
            'cleared': True,
            'months_cleared': [
                f'{current_year}-{current_month:02d}',
                f'{next_year}-{next_month:02d}'
            ]
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to clear calendar data: {str(e)}'
        }), 500


@calendars_bp.route('/api/combined', methods=['POST'])
def api_combined_calendar():
    """Combined calendar endpoint for multi-calendar view. Returns all calendar systems."""
    try:
        data = request.get_json() or {}

        birth_date_str = data.get('birth_date')
        birth_time_str = data.get('birth_time')
        birth_latitude = data.get('birth_latitude')
        birth_longitude = data.get('birth_longitude')
        birth_timezone = data.get('birth_timezone', -5)
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        location_latitude = data.get('location_latitude', birth_latitude)
        location_longitude = data.get('location_longitude', birth_longitude)
        location_timezone = data.get('location_timezone', birth_timezone)
        location_name = data.get('location_name', 'Unknown')

        if not all([birth_date_str, birth_time_str, birth_latitude, birth_longitude]):
            return jsonify({
                'success': False,
                'error': 'Missing required birth data (birth_date, birth_time, birth_latitude, birth_longitude)'
            }), 400

        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()

        if 'T' in birth_time_str:
            birth_time_str = birth_time_str.split('T')[1][:5]
        elif len(birth_time_str) > 5:
            birth_time_str = birth_time_str[:5]
        birth_time = datetime.strptime(birth_time_str, '%H:%M').time()

        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            start_date = date.today()

        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            end_date = start_date + timedelta(days=30)

        days_result = {}
        current_date = start_date

        personal_data = {}
        try:
            from personal_calendar.personal_transit_yp import EnhancedPersonalTransitCalculator

            calculator = EnhancedPersonalTransitCalculator()
            birth_chart = calculator.calculate_birth_chart(
                birth_date, birth_time,
                float(birth_latitude), float(birth_longitude), float(birth_timezone)
            )
            if birth_chart:
                personal_calendar = calculator.generate_personal_calendar(
                    birth_chart, start_date, end_date,
                    float(location_latitude), float(location_longitude), float(location_timezone)
                )
                personal_data = personal_calendar
        except Exception as e:
            print(f"Personal calendar error: {e}")

        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            weekday = current_date.strftime('%A')

            day_data = personal_data.get(date_str, {})
            personal_score = day_data.get('personal_score', {})

            quality = personal_score.get('quality', 'neutral')
            if quality in ['power', 'supportive']:
                electional_quality = 'good'
            elif quality == 'avoid':
                electional_quality = 'caution'
            elif quality == 'aware':
                electional_quality = 'slow'
            else:
                electional_quality = 'neutral'

            days_result[date_str] = {
                'date': date_str,
                'weekday': weekday,
                'electional': {
                    'evaluation': {
                        'quality': electional_quality,
                        'score': personal_score.get('score', 0)
                    }
                },
                'personal': {
                    'personal_score': {
                        'quality': quality,
                        'score': personal_score.get('score', 0),
                        'moon_house': personal_score.get('moon_house', 0)
                    }
                },
                'vedic_collective': {
                    'classification': electional_quality
                },
                'magi_transit': {
                    'quality': electional_quality,
                    'classification': quality.capitalize() if quality else 'Neutral'
                }
            }

            current_date += timedelta(days=1)

        return jsonify({
            'success': True,
            'days': days_result,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'generated_at': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
