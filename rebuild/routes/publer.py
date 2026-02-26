"""Publer integration routes — push Micro Bird results as draft posts."""

import os
import traceback
from datetime import datetime, timedelta, date, time

from flask import Blueprint, request, jsonify, session
from database.manager import db_manager

publer_bp = Blueprint('publer', __name__)


def _get_publer_api():
    import sys
    parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from publer_service import PublerAPI
    return PublerAPI()


def _extract_date_part(date_string):
    if not date_string:
        return None
    if 'T' in date_string:
        return date_string.split('T')[0]
    if ' ' in date_string:
        return date_string.split(' ')[0]
    return date_string


def _get_background_dates(saved_data):
    calendars = (saved_data or {}).get('calendars', {})
    combined_cal = calendars.get('combined', {})
    combined_results = (
        combined_cal.get('data', {}).get('results', [])
        or combined_cal.get('results', [])
    )
    bg_dates = set()
    for day in combined_results:
        if not isinstance(day, dict):
            continue
        classification = day.get('classification', '')
        is_bg = day.get('is_background', False)
        if classification in ('OMNI', 'DOUBLE GO', 'GOOD') or is_bg:
            bg_dates.add(day.get('date', ''))
    return bg_dates


def _parse_time_to_datetime(day_date, time_str):
    formats = ['%I:%M %p', '%I:%M:%S %p', '%H:%M:%S', '%H:%M']
    for fmt in formats:
        try:
            t = datetime.strptime(time_str, fmt).time()
            return datetime.combine(day_date, t)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse time: {time_str}")


def _compute_micro_bird_events(saved_data):
    bg_dates = _get_background_dates(saved_data)
    if not bg_dates:
        return []

    calendars = (saved_data or {}).get('calendars', {})

    bird_cal = calendars.get('bird_batch', {})
    daily_results = bird_cal.get('daily_results', [])
    if not daily_results and isinstance(bird_cal.get('data'), dict):
        daily_results = bird_cal['data'].get('daily_results', [])

    bird_windows = []
    for day_data in daily_results:
        day_date_str = day_data.get('date', '')
        if day_date_str not in bg_dates:
            continue
        try:
            day_date_obj = datetime.strptime(day_date_str, '%Y-%m-%d').date()
        except ValueError:
            continue
        for period in day_data.get('periods', []):
            start_str = period.get('start_time', '')
            end_str = period.get('end_time', '')
            try:
                start_dt = _parse_time_to_datetime(day_date_obj, start_str)
                end_dt = _parse_time_to_datetime(day_date_obj, end_str)
                if end_dt <= start_dt:
                    end_dt += timedelta(days=1)
            except (ValueError, TypeError):
                continue
            bird_windows.append({
                'date': day_date_str,
                'start': start_dt,
                'end': end_dt,
                'tier': period.get('tier', ''),
                'activity': period.get('sub_activity', period.get('main_activity', '')),
            })

    yp_cal = calendars.get('yogi_point', {})
    yp_transits = yp_cal.get('transits', []) or yp_cal.get('results', [])

    pof_transits = []
    pof_cal = calendars.get('part_of_fortune', calendars.get('enhanced_pof', {}))
    if pof_cal:
        pof_transits = pof_cal.get('transits', []) or pof_cal.get('results', [])

    all_transits = []
    for t in yp_transits:
        t['_source'] = 'Yogi Point'
        all_transits.append(t)
    for t in pof_transits:
        t['_source'] = 'Part of Fortune'
        all_transits.append(t)

    micro_bird_events = []
    for transit in all_transits:
        t_start_raw = transit.get('start_time') or transit.get('start')
        t_end_raw = transit.get('end_time') or transit.get('end')
        if not t_start_raw or not t_end_raw:
            continue
        try:
            t_start = datetime.fromisoformat(str(t_start_raw).replace('Z', '+00:00')).replace(tzinfo=None)
            t_end = datetime.fromisoformat(str(t_end_raw).replace('Z', '+00:00')).replace(tzinfo=None)
        except (ValueError, TypeError):
            continue

        t_date = t_start.strftime('%Y-%m-%d')
        if t_date not in bg_dates:
            continue

        for bw in bird_windows:
            if bw['date'] != t_date:
                continue
            if t_start < bw['end'] and t_end > bw['start']:
                overlap_start = max(t_start, bw['start'])
                overlap_end = min(t_end, bw['end'])
                duration_min = int((overlap_end - overlap_start).total_seconds() / 60)
                if duration_min < 1:
                    continue

                source = transit.get('_source', 'Microtransit')
                planet = transit.get('planet', transit.get('type', ''))
                tier = bw['tier']

                micro_bird_events.append({
                    'date': t_date,
                    'start': overlap_start.isoformat(),
                    'end': overlap_end.isoformat(),
                    'duration_minutes': duration_min,
                    'transit_source': source,
                    'planet': planet,
                    'bird_tier': tier,
                    'bird_activity': bw['activity'],
                    'title': f"MicroBird: {source} x {tier}",
                    'description': f"{source} ({planet}) overlaps {tier} bird period ({bw['activity']}). Duration: {duration_min} min.",
                })

    micro_bird_events.sort(key=lambda x: x['start'])
    return micro_bird_events


@publer_bp.route('/api/publer/test', methods=['GET'])
def test_publer():
    try:
        api = _get_publer_api()
        result = api.test_connection()
        return jsonify(result)
    except ValueError as ve:
        return jsonify({'error': str(ve), 'hint': 'Set PUBLER_API_KEY environment variable'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@publer_bp.route('/api/publer/accounts', methods=['GET'])
def publer_accounts():
    try:
        api = _get_publer_api()
        result = api.get_accounts()
        return jsonify(result)
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@publer_bp.route('/api/publer/push-microbird', methods=['POST'])
def push_microbird_to_publer():
    try:
        if not session.get('authenticated'):
            return jsonify({'error': 'Authentication required'}), 401

        from helpers.utils import get_effective_user_id
        user_id = get_effective_user_id()
        if not user_id:
            return jsonify({'error': 'User ID not found'}), 400

        saved_data = db_manager.get_calendar_data(user_id)
        if not saved_data:
            return jsonify({'error': 'No saved calendar data. Generate calendars first.'}), 404

        micro_bird_events = _compute_micro_bird_events(saved_data)
        if not micro_bird_events:
            return jsonify({'error': 'No Micro Bird events found. Ensure bird batch and microtransit data exists.'}), 404

        data = request.get_json() or {}
        account_ids = data.get('account_ids')
        hashtag = data.get('hashtag', '#astrobatching')
        prefix = data.get('prefix', '')

        try:
            api = _get_publer_api()
        except ValueError as ve:
            return jsonify({'error': str(ve), 'hint': 'Set PUBLER_API_KEY environment variable'}), 400

        results = []
        for event in micro_bird_events:
            text_parts = []
            if prefix:
                text_parts.append(prefix)
            text_parts.append(f"🎯 {event['title']}")
            text_parts.append(f"📅 {event['date']}")
            text_parts.append(f"⏰ {event['start'][:16].replace('T', ' ')} - {event['end'][:16].split('T')[1]}")
            text_parts.append(f"⏱️ {event['duration_minutes']} min window")
            text_parts.append(f"🪐 {event['planet']}")
            text_parts.append(f"🐦 {event['bird_tier']} ({event['bird_activity']})")
            if hashtag:
                text_parts.append(hashtag)
            text = '\n'.join(text_parts)

            scheduled_time = event['start']

            draft_result = api.create_draft(
                text=text,
                account_ids=account_ids,
                scheduled_time=scheduled_time,
            )
            results.append({
                'event': event['title'],
                'date': event['date'],
                'scheduled': scheduled_time,
                'publer_result': draft_result,
            })

        success_count = sum(1 for r in results if r['publer_result'].get('success'))
        return jsonify({
            'total_events': len(micro_bird_events),
            'pushed': success_count,
            'failed': len(results) - success_count,
            'results': results,
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@publer_bp.route('/api/publer/push', methods=['POST'])
def push_events_to_publer():
    try:
        if not session.get('authenticated'):
            return jsonify({'error': 'Authentication required'}), 401

        data = request.get_json() or {}
        events = data.get('events', [])
        account_ids = data.get('account_ids')

        if not events:
            return jsonify({'error': 'No events provided'}), 400

        try:
            api = _get_publer_api()
        except ValueError as ve:
            return jsonify({'error': str(ve)}), 400

        results = []
        for event in events:
            text = event.get('text', event.get('title', ''))
            scheduled_time = event.get('scheduled_time', event.get('start'))
            draft_result = api.create_draft(
                text=text,
                account_ids=account_ids,
                scheduled_time=scheduled_time,
            )
            results.append({
                'event': text[:50],
                'publer_result': draft_result,
            })

        success_count = sum(1 for r in results if r['publer_result'].get('success'))
        return jsonify({
            'total': len(events),
            'pushed': success_count,
            'failed': len(results) - success_count,
            'results': results,
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
