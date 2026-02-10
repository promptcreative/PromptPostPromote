from flask import Blueprint, request, jsonify, session
from datetime import datetime
import traceback
from typing import Dict, Any, Optional

from helpers.utils import get_user_calendar_range, make_json_serializable
from filters.bird_batch_filter import BirdBatchFilter
from filters.astro_batch_detector import AstroBatchDetector

api_bp = Blueprint('api_bp', __name__)


class AstrobatchAPI:
    def __init__(self):
        self.bird_filter = BirdBatchFilter()
        self.astro_detector = AstroBatchDetector()
        self.default_days = 7
        self.default_max_periods = 6
        self.valid_combinations = [
            'ruling/ruling', 'ruling/eating', 'eating/ruling'
        ]

    def process_full_batch(self, date: str, days: Optional[int] = None,
                           max_periods: Optional[int] = None,
                           combination_filter: Optional[str] = None,
                           time_filter: Optional[str] = None,
                           include_transits: bool = True) -> Dict[str, Any]:
        try:
            days = days or self.default_days
            max_periods = max_periods or self.default_max_periods

            bird_result = self.bird_filter.process_batch(
                start_date=date, days=days, max_periods_per_day=max_periods)

            result = {
                'api_version': '3.0',
                'processing_steps': ['bird_filter'],
                'step1_bird_filter': bird_result,
                'metadata': {
                    'start_date': date,
                    'days_processed': days,
                    'max_periods': max_periods,
                    'combination_filter': combination_filter,
                    'time_filter': time_filter,
                    'include_transits': include_transits,
                    'generated_at': datetime.now().isoformat()
                }
            }

            if include_transits and bird_result.get('daily_results'):
                try:
                    astro_result = self.astro_detector.process_batch(bird_result)
                    result['step2_astro_detector'] = astro_result
                    result['processing_steps'].append('astro_detector')
                    result['metadata']['automation_moments'] = astro_result[
                        'metadata']['automation_moments_found']
                    result['metadata']['total_transit_events'] = astro_result[
                        'metadata']['total_transit_events']
                except Exception as e:
                    result['step2_error'] = f"Astro detection failed: {str(e)}"

            result['summary'] = self._generate_summary(result)
            result['processing_steps'].append('summary')
            return result

        except Exception as e:
            return {
                'error': str(e),
                'traceback': traceback.format_exc(),
                'api_version': '3.0',
                'generated_at': datetime.now().isoformat()
            }

    def _generate_summary(self, result: Dict[str, Any]) -> Dict[str, Any]:
        try:
            bird_stats = result['step1_bird_filter'].get('statistics', {})
            astro_data = result.get('step2_astro_detector', {})

            summary = {
                'total_favorable_periods': bird_stats.get('total_periods', 0),
                'tier_distribution': bird_stats.get('tier_counts', {}),
                'processing_success': True,
                'steps_completed': len(result.get('processing_steps', []))
            }

            if astro_data:
                astro_stats = astro_data.get('statistics', {})
                summary.update({
                    'automation_moments': astro_stats.get('total_automation_moments', 0),
                    'enhanced_moments': astro_stats.get('enhanced_moments', 0),
                    'chronological_order': astro_stats.get('chronological_order', True)
                })

                if astro_data.get('automation_moments'):
                    next_moment = astro_data['automation_moments'][0]
                    summary['next_automation_moment'] = {
                        'date': next_moment.get('date'),
                        'time': next_moment.get('time'),
                        'bird_combination': next_moment.get('bird_combination'),
                        'enhanced': next_moment.get('enhanced', False),
                        'micro_transits_count': len(next_moment.get('micro_transits', []))
                    }

            return summary

        except Exception as e:
            return {
                'error': f"Summary generation failed: {str(e)}",
                'processing_success': False
            }


api = AstrobatchAPI()


@api_bp.route('/api', methods=['GET'])
def api_health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'Astrobatch API',
        'version': '3.0',
        'port': 5000,
        'endpoints': [
            '/health', '/bird-periods', '/astro-transits',
            '/automation-moments', '/batch'
        ],
        'timestamp': datetime.now().isoformat()
    })


@api_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'api_version': '3.0',
        'port': 5000,
        'timestamp': datetime.now().isoformat(),
        'available_endpoints': [
            '/batch', '/bird-periods', '/astro-transits',
            '/automation-moments', '/generate-collective-calendar',
            '/generate-personal-calendar', '/yogi-point-transits',
            '/part-of-fortune-transits', '/list-calendars', '/api/combined'
        ]
    })


@api_bp.route('/batch', methods=['POST'])
def process_batch():
    try:
        data = request.get_json() or {}

        date = data.get('date')
        if not date:
            return jsonify({
                'error': 'Date parameter is required (YYYY-MM-DD format)',
                'example': {'date': '2025-07-18'}
            }), 400

        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return jsonify({
                'error': 'Invalid date format. Use YYYY-MM-DD',
                'provided': date
            }), 400

        days = data.get('days', 7)
        max_periods = data.get('max_periods', 6)
        combination_filter = data.get('combination_filter')
        time_filter = data.get('time_filter')
        include_transits = data.get('include_transits', True)

        if combination_filter and combination_filter.lower() not in api.valid_combinations:
            return jsonify({
                'error': 'Invalid combination filter',
                'valid_options': api.valid_combinations,
                'provided': combination_filter
            }), 400

        result = api.process_full_batch(
            date=date,
            days=days,
            max_periods=max_periods,
            combination_filter=combination_filter,
            time_filter=time_filter,
            include_transits=include_transits)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@api_bp.route('/bird-periods', methods=['POST'])
def get_bird_periods():
    try:
        data = request.get_json() or {}
        date = data.get('date')
        days = data.get('days')

        if not date:
            user_info = session.get('user_info', {})
            user_email = user_info.get('email')
            start_date, end_date, user_days = get_user_calendar_range(user_email)
            date = start_date.strftime('%Y-%m-%d')
            if not days:
                days = user_days

        if not days:
            days = 7

        result = api.bird_filter.process_batch(
            start_date=date,
            days=days,
            max_periods_per_day=data.get('max_periods', 6))

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/astro-transits', methods=['POST'])
def get_astro_transits():
    try:
        data = request.get_json() or {}
        bird_periods = data.get('bird_periods')
        date = data.get('date')

        if not bird_periods:
            return jsonify({
                'error': 'bird_periods parameter is required (output from /bird-periods)'
            }), 400

        if not date:
            return jsonify({'error': 'date parameter is required'}), 400

        if isinstance(bird_periods, list):
            bird_periods_data = {
                'daily_results': bird_periods,
                'metadata': {
                    'start_date': date,
                    'days_processed': data.get('days', 7)
                }
            }
        else:
            bird_periods_data = bird_periods

        result = api.astro_detector.process_batch(bird_periods_data)
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/automation-moments', methods=['POST'])
def get_automation_moments():
    try:
        data = request.get_json() or {}
        date = data.get('date')

        if not date:
            return jsonify({'error': 'Date parameter is required'}), 400

        result = api.process_full_batch(
            date=date,
            days=data.get('days', 7),
            include_transits=True)

        astro_data = result.get('step2_astro_detector', {})
        moments = astro_data.get('automation_moments', [])

        response = {
            'automation_moments': moments,
            'total_count': len(moments),
            'enhanced_count': len([m for m in moments if m.get('enhanced', False)]),
            'metadata': result.get('metadata', {}),
            'summary': result.get('summary', {})
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/api/geocode', methods=['GET'])
def geocode():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    try:
        import requests as http_requests
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': query,
            'format': 'json',
            'limit': 5,
            'addressdetails': 1
        }
        headers = {'User-Agent': 'Panch-Pakshi-Calculator/1.0'}

        response = http_requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            results = response.json()
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'display_name': result.get('display_name', ''),
                    'name': result.get('name', ''),
                    'lat': float(result.get('lat', 0)),
                    'lon': float(result.get('lon', 0)),
                    'type': result.get('type', ''),
                    'importance': result.get('importance', 0)
                })
            return jsonify(formatted_results)
        else:
            return jsonify([])
    except Exception:
        return jsonify([])
