"""
ICS Calendar Feed routes blueprint
Ports ICS feed endpoints from src/api/astrobatch_api.py
"""

from flask import Blueprint, request, make_response, jsonify
from database.models import SubscriptionToken
from database.manager import db_manager
from datetime import datetime, timedelta, date, time
import hashlib

ics_bp = Blueprint('ics_feeds', __name__)

CALENDAR_DISPLAY_NAMES = {
    'bird_batch': 'ABmicrotimes - Bird Batch',
    'personal': 'ABmicrotimes - Personal Transit',
    'pti': 'ABmicrotimes - PTI Collective',
    'combined': 'ABmicrotimes - Combined',
    'yogi_point': 'ABmicrotimes - Yogi Point',
    'vedic': 'ABmicrotimes - Vedic Collective',
    'nogo': 'ABmicrotimes - NO GO',
    'microbird': 'ABmicrotimes - MicroBird',
    'enhanced_pof': 'ABmicrotimes - Enhanced POF',
    'all_microtransits': 'ABmicrotimes - All Microtransits',
}


def _escape_ics_text(text):
    if not text:
        return ''
    text = text.replace('\\', '\\\\')
    text = text.replace(';', '\\;')
    text = text.replace(',', '\\,')
    text = text.replace('\n', '\\n')
    return text


def create_ics_response(calendar_name, events, cal_name_override=None):
    display_name = cal_name_override or CALENDAR_DISPLAY_NAMES.get(
        calendar_name, f'ABmicrotimes - {calendar_name}'
    )
    dtstamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    sequence = int(datetime.utcnow().timestamp()) % 100000

    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Astrobatch//ABmicrotimes//EN',
        'METHOD:PUBLISH',
        f'X-WR-CALNAME:{display_name}',
        f'X-WR-CALDESC:Astrobatching calendar - {display_name}',
    ]

    for ev in events:
        dt_start = ev.get('start')
        dt_end = ev.get('end')
        summary = _escape_ics_text(ev.get('title', 'Event'))
        description = _escape_ics_text(ev.get('description', ''))
        uid = ev.get('uid') or f"{ev.get('id', hashlib.md5(summary.encode()).hexdigest())}@astrobatch"
        location = _escape_ics_text(ev.get('location', ''))

        lines.append('BEGIN:VEVENT')

        if isinstance(dt_start, date) and not isinstance(dt_start, datetime):
            lines.append(f'DTSTART;VALUE=DATE:{dt_start.strftime("%Y%m%d")}')
            if dt_end and isinstance(dt_end, date) and not isinstance(dt_end, datetime):
                lines.append(f'DTEND;VALUE=DATE:{dt_end.strftime("%Y%m%d")}')
            else:
                next_day = dt_start + timedelta(days=1)
                lines.append(f'DTEND;VALUE=DATE:{next_day.strftime("%Y%m%d")}')
        elif isinstance(dt_start, datetime):
            lines.append(f'DTSTART:{dt_start.strftime("%Y%m%dT%H%M%S")}')
            if dt_end and isinstance(dt_end, datetime):
                lines.append(f'DTEND:{dt_end.strftime("%Y%m%dT%H%M%S")}')
        else:
            lines.append(f'DTSTART;VALUE=DATE:{datetime.utcnow().strftime("%Y%m%d")}')

        lines.append(f'SUMMARY:{summary}')
        if description:
            lines.append(f'DESCRIPTION:{description}')
        if location:
            lines.append(f'LOCATION:{location}')
        lines.append(f'UID:{uid}')
        lines.append(f'DTSTAMP:{dtstamp}')
        lines.append(f'SEQUENCE:{sequence}')
        lines.append('END:VEVENT')

    lines.append('END:VCALENDAR')

    ics_content = '\r\n'.join(lines)
    response = make_response(ics_content)
    response.headers['Content-Type'] = 'text/calendar; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename={calendar_name}.ics'
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-Published-TTL'] = 'PT15M'
    response.headers['ETag'] = f'"{int(datetime.utcnow().timestamp())}"'
    return response


def _create_stub_ics(calendar_name, display_name):
    today = date.today()
    events = [{
        'id': f'{calendar_name}_stub',
        'title': f'{display_name} - Coming Soon',
        'description': f'This calendar feed ({display_name}) is not yet available in the rebuild. Check back soon.',
        'start': today,
        'end': today + timedelta(days=1),
    }]
    return create_ics_response(calendar_name, events, cal_name_override=display_name)


def _verify_subscription(calendar_type):
    user_id = request.args.get('user_id')
    token = request.args.get('token')
    if not user_id:
        return None, ('user_id query parameter required', 400)
    if not token:
        return None, ('Authentication token required', 401)
    if not SubscriptionToken.verify(user_id, calendar_type, token):
        return None, ('Invalid authentication token', 403)
    return user_id, None


def _get_saved_calendar_section(user_id, section_key):
    saved_data = db_manager.get_calendar_data(user_id)
    if not saved_data:
        return None, None
    calendars = saved_data.get('calendars', {})
    cal_section = calendars.get(section_key, {})
    return saved_data, cal_section


PTI_ICONS = {
    'PTI BEST': '💜⚡',
    'PTI GO': '✅',
    'BEST': '💜⚡',
    'NORMAL': '⚪',
    'PTI SLOW': '🐢',
}

VEDIC_ICONS = {
    'GO': '✅',
    'FOCUS': '🎯',
    'BUILD': '🔨',
    'SLOW': '🐢',
    'INWARD': '🩷',
    'STOP': '⛔',
    'NEUTRAL': '⚪',
}

COMBINED_ICONS = {
    'OMNI': '⚡',
    'DOUBLE GO': '🚀',
    'DOUBLE_GO': '🚀',
    'GOOD': '💚',
    'CAUTION': '🔴',
    'SLOW': '🟡',
    'NEUTRAL': '⚪',
}

PERSONAL_QUALITY_EMOJIS = {
    'power': '💜⚡',
    'supportive': '💚✨',
    'neutral': '⚪🌑',
    'aware': '🟡⚠️',
    'awareness': '🟡⚠️',
    'caution': '🔴🚫',
    'avoid': '🔴🚫',
}


@ics_bp.route('/calendar/bird_batch.ics')
def bird_batch_calendar_feed():
    user_id, err = _verify_subscription('bird_batch')
    if err:
        return err

    try:
        saved_data, bird_cal = _get_saved_calendar_section(user_id, 'bird_batch')
        if not bird_cal:
            return 'No bird batch calendar data found. Please generate calendars first.', 404

        daily_results = bird_cal.get('daily_results', [])
        if not daily_results and isinstance(bird_cal.get('data'), dict):
            daily_results = bird_cal['data'].get('daily_results', [])

        events = []
        for day_data in daily_results:
            day_date_str = day_data.get('date')
            if not day_date_str:
                continue
            periods = day_data.get('periods', [])
            for period in periods:
                bird = period.get('main_bird', '')
                activity = period.get('sub_activity', period.get('main_activity', ''))
                tier = period.get('tier', '')
                rating = period.get('rating', '')

                bird_emojis = {'Crow': '🐦', 'Cock': '🐓', 'Peacock': '🦚', 'Vulture': '🦅', 'Owl': '🦉'}
                activity_emojis = {'Ruling': '👑', 'Eating': '🍽️', 'Walking': '🚶', 'Sleeping': '💤', 'Dying': '💀'}
                tier_emojis = {'Double Boost': '⚡⚡', 'Boost': '⚡', 'Build': '🔨'}

                activity_icon = activity_emojis.get(activity, '')
                tier_icon = tier_emojis.get(tier, '')
                title = f"{activity_icon} {activity}"
                if tier_icon and tier:
                    title = f"{tier_icon} {tier} {title}"

                description = f"🎯 BIRD BATCH PERIOD\\n"
                description += f"📊 Rating: {rating}\\n"
                description += f"🏆 Tier: {tier}\\n"
                description += f"⏱️ Duration: {period.get('duration_minutes', 0)} minutes"

                try:
                    day_date_obj = datetime.strptime(day_date_str, '%Y-%m-%d').date()
                except ValueError:
                    continue

                start_time_str = period.get('start_time', '00:00')
                end_time_str = period.get('end_time', '23:59')

                try:
                    start_dt = _parse_time_to_datetime(day_date_obj, start_time_str)
                    end_dt = _parse_time_to_datetime(day_date_obj, end_time_str)
                    if end_dt <= start_dt:
                        end_dt += timedelta(days=1)
                except ValueError:
                    start_dt = datetime.combine(day_date_obj, time(0, 0))
                    end_dt = datetime.combine(day_date_obj, time(23, 59))

                events.append({
                    'id': f"bird_{day_date_str}_{start_time_str.replace(':', '').replace(' ', '')}",
                    'title': title,
                    'description': description,
                    'start': start_dt,
                    'end': end_dt,
                })

        return create_ics_response('bird_batch', events)

    except Exception as e:
        return f"Error generating Bird Batch calendar: {str(e)}", 500


def _parse_time_to_datetime(day_date, time_str):
    formats = ['%I:%M %p', '%I:%M:%S %p', '%H:%M:%S', '%H:%M']
    for fmt in formats:
        try:
            t = datetime.strptime(time_str, fmt).time()
            return datetime.combine(day_date, t)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse time: {time_str}")


@ics_bp.route('/calendar/personal.ics')
def personal_calendar_feed():
    user_id, err = _verify_subscription('personal')
    if err:
        return err

    try:
        saved_data, personal_cal = _get_saved_calendar_section(user_id, 'personal')
        if not personal_cal:
            return 'No personal calendar data found. Please generate calendars first.', 404

        daily_results = personal_cal.get('daily_results', [])
        nakshatra_transits = personal_cal.get('nakshatra_transits', [])

        score_by_date = {}
        for dr in daily_results:
            date_str = dr.get('date')
            day_score = dr.get('day_score', {})
            if date_str and day_score:
                score_by_date[date_str] = {
                    'quality': day_score.get('quality', 'neutral'),
                    'score': day_score.get('score', 0),
                    'moon_house': dr.get('moon_house', 0),
                    'factors': day_score.get('factors', []),
                    'awareness_message': day_score.get('awareness_message', ''),
                    'yogi_enhancement': day_score.get('yogi_enhancement', ''),
                }

        events = []
        if nakshatra_transits:
            for idx, transit in enumerate(nakshatra_transits):
                nakshatra_name = transit.get('nakshatra_name', 'Unknown')
                ruler = transit.get('ruler', 'Unknown')

                entry_local_str = transit.get('entry_local') or transit.get('entry_time')
                exit_local_str = transit.get('exit_local') or transit.get('exit_time')

                try:
                    entry_local = datetime.fromisoformat(str(entry_local_str)) if entry_local_str else None
                    exit_local = datetime.fromisoformat(str(exit_local_str)) if exit_local_str else None
                except (ValueError, TypeError):
                    continue

                if not entry_local or not exit_local:
                    continue

                transit_date_str = entry_local.strftime('%Y-%m-%d')
                score_data = score_by_date.get(transit_date_str)
                if not score_data:
                    exit_date_str = exit_local.strftime('%Y-%m-%d')
                    score_data = score_by_date.get(exit_date_str)

                if score_data:
                    quality = score_data.get('quality', 'Neutral')
                    score = score_data.get('score', 0)
                    quality_emoji = PERSONAL_QUALITY_EMOJIS.get(quality.lower(), '⚪')
                    title = f"{nakshatra_name} ({ruler}) - {score:.1f} - {quality.title()} {quality_emoji}"
                    description = f"🌙 NAKSHATRA: {nakshatra_name}\\n"
                    description += f"👑 Ruler: {ruler}\\n"
                    description += f"📈 Personal Score: {score:.1f}\\n"
                    description += f"💫 Quality: {quality.title()}"
                    awareness_msg = score_data.get('awareness_message', '')
                    if awareness_msg:
                        description += f"\\n🎯 {awareness_msg}"
                else:
                    title = f"{nakshatra_name} ({ruler}) - ⚪ Neutral"
                    description = f"🌙 NAKSHATRA: {nakshatra_name}\\n👑 Ruler: {ruler}"

                entry_utc_str = transit.get('entry_time')
                exit_utc_str = transit.get('exit_time')
                try:
                    entry_utc = datetime.fromisoformat(str(entry_utc_str)) if entry_utc_str else entry_local
                    exit_utc = datetime.fromisoformat(str(exit_utc_str)) if exit_utc_str else exit_local
                except (ValueError, TypeError):
                    entry_utc = entry_local
                    exit_utc = exit_local

                events.append({
                    'id': f"personal_transit_{idx}",
                    'title': title,
                    'description': description,
                    'start': entry_utc.replace(tzinfo=None) if hasattr(entry_utc, 'replace') else entry_utc,
                    'end': exit_utc.replace(tzinfo=None) if hasattr(exit_utc, 'replace') else exit_utc,
                })
        else:
            for date_str, score_data in sorted(score_by_date.items()):
                quality = score_data.get('quality', 'neutral')
                score = score_data.get('score', 0)
                quality_emoji = PERSONAL_QUALITY_EMOJIS.get(quality.lower(), '⚪')
                try:
                    day_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    continue
                title = f"{quality_emoji} Personal: {quality.title()} ({score:.1f})"
                description = f"📈 Personal Score: {score:.1f}\\n💫 Quality: {quality.title()}"
                events.append({
                    'id': f"personal_{date_str}",
                    'title': title,
                    'description': description,
                    'start': day_date,
                    'end': day_date + timedelta(days=1),
                })

        return create_ics_response('personal', events, cal_name_override='Personal Transit')

    except Exception as e:
        return f"Error generating Personal calendar: {str(e)}", 500


@ics_bp.route('/calendar/pti.ics')
def pti_calendar_feed():
    user_id, err = _verify_subscription('pti')
    if err:
        return err

    try:
        saved_data, pti_cal = _get_saved_calendar_section(user_id, 'pti_collective')
        if not pti_cal:
            saved_data, pti_cal = _get_saved_calendar_section(user_id, 'pti')
        if not pti_cal:
            return 'No PTI calendar data found. Please generate calendars first.', 404

        timing_data = (
            pti_cal.get('data', {}).get('timing_data', [])
            or pti_cal.get('results', [])
            or pti_cal.get('timing_data', [])
        )

        events = []
        for day_data in timing_data:
            day_date_str = day_data.get('date')
            if not day_date_str:
                continue
            try:
                if isinstance(day_date_str, str):
                    day_date = datetime.strptime(day_date_str, '%Y-%m-%d').date()
                else:
                    day_date = day_date_str
            except (ValueError, TypeError):
                continue

            classification = day_data.get('classification') or day_data.get('magi_classification', 'Normal')
            score = day_data.get('score', 0)
            reason = day_data.get('reason') or day_data.get('classification_reason', '')

            icon = PTI_ICONS.get(classification.upper(), '📊')
            title = f"{icon} PTI: {classification}"

            description = f"📈 PROFESSIONAL TIMING INDEX\\n"
            description += f"📅 {day_date.strftime('%A, %B %d, %Y')}\\n"
            description += f"🏷️ Classification: {classification}\\n"
            description += f"📊 Score: {score:.2f}\\n"
            if reason:
                description += f"📜 Reason: {reason}"

            events.append({
                'id': f"pti_{day_date.strftime('%Y%m%d')}",
                'title': title,
                'description': description,
                'start': day_date,
                'end': day_date + timedelta(days=1),
            })

        return create_ics_response('pti', events, cal_name_override='PTI Collective')

    except Exception as e:
        return f"Error generating PTI calendar: {str(e)}", 500


@ics_bp.route('/calendar/vedic.ics')
def vedic_calendar_feed():
    user_id, err = _verify_subscription('vedic')
    if err:
        return err

    try:
        saved_data, vedic_cal = _get_saved_calendar_section(user_id, 'vedic_pti')
        if not vedic_cal:
            saved_data, vedic_cal = _get_saved_calendar_section(user_id, 'goslow')
        if not vedic_cal:
            saved_data, vedic_cal = _get_saved_calendar_section(user_id, 'vedic')
        if not vedic_cal:
            return 'No Vedic calendar data found. Please generate calendars first.', 404

        results = (
            vedic_cal.get('data', {}).get('results', [])
            or vedic_cal.get('results', [])
            or vedic_cal.get('timing_data', [])
        )

        events = []
        for day_data in results:
            day_date_str = day_data.get('date')
            if not day_date_str:
                continue
            try:
                if isinstance(day_date_str, str):
                    day_date = datetime.strptime(day_date_str, '%Y-%m-%d').date()
                else:
                    day_date = day_date_str
            except (ValueError, TypeError):
                continue

            classification = day_data.get('classification', 'NEUTRAL')
            rule_reason = day_data.get('rule_reason', '')
            tithi_name = day_data.get('tithi_name', '')
            nakshatra = day_data.get('nakshatra', '')

            icon = VEDIC_ICONS.get(classification.upper(), '⚪')
            title = f"{icon} Vedic: {classification}"

            description = f"🕉️ VEDIC COLLECTIVE CALENDAR\\n"
            description += f"📅 {day_date.strftime('%A, %B %d, %Y')}\\n"
            description += f"🏷️ Classification: {classification}"
            if rule_reason:
                description += f"\\n📜 {rule_reason}"
            if tithi_name:
                description += f"\\n🌙 Tithi: {tithi_name}"
            if nakshatra:
                description += f"\\n⭐ Nakshatra: {nakshatra}"

            events.append({
                'id': f"vedic_{day_date.strftime('%Y%m%d')}",
                'title': title,
                'description': description,
                'start': day_date,
                'end': day_date + timedelta(days=1),
            })

        return create_ics_response('vedic', events, cal_name_override='Vedic Collective')

    except Exception as e:
        return f"Error generating Vedic calendar: {str(e)}", 500


@ics_bp.route('/calendar/combined.ics')
def combined_calendar_feed():
    user_id, err = _verify_subscription('combined')
    if err:
        return err

    try:
        saved_data, combined_cal = _get_saved_calendar_section(user_id, 'combined')
        if not combined_cal:
            return 'No combined calendar data found. Please generate calendars first.', 404

        combined_results = (
            combined_cal.get('data', {}).get('results', [])
            or combined_cal.get('results', [])
        )

        events = []
        for day_result in combined_results:
            if not isinstance(day_result, dict):
                continue
            day_date_str = day_result.get('date')
            if not day_date_str:
                continue
            try:
                if isinstance(day_date_str, str):
                    day_date = datetime.strptime(day_date_str, '%Y-%m-%d').date()
                else:
                    day_date = day_date_str
            except (ValueError, TypeError):
                continue

            classification = day_result.get('combined_quality', day_result.get('classification', 'NEUTRAL'))
            reason = day_result.get('reason', '')
            is_double_go = day_result.get('is_double_go', False)

            system_breakdown = day_result.get('system_breakdown', {})
            pti_quality = system_breakdown.get('pti_collective', {}).get('quality', '')
            vedic_quality = system_breakdown.get('vedic_pti', {}).get('quality', '')
            personal_quality = system_breakdown.get('personal', {}).get('quality', '')

            icon = COMBINED_ICONS.get(classification.upper(), '⚪')
            if is_double_go:
                icon = '🚀'
                title = f"{icon} DOUBLE GO"
            else:
                title = f"{icon} Combined: {classification}"

            description = f"🔄 COMBINED CALENDAR\\n"
            description += f"📅 {day_date.strftime('%A, %B %d, %Y')}\\n"
            description += f"🏷️ Classification: {classification}"
            if reason:
                description += f"\\n📜 {reason}"
            if pti_quality:
                description += f"\\n📈 PTI: {pti_quality}"
            if vedic_quality:
                description += f"\\n🕉️ Vedic: {vedic_quality}"
            if personal_quality:
                description += f"\\n🌙 Personal: {personal_quality}"

            events.append({
                'id': f"combined_{day_date.strftime('%Y%m%d')}",
                'title': title,
                'description': description,
                'start': day_date,
                'end': day_date + timedelta(days=1),
            })

        return create_ics_response('combined', events, cal_name_override='Combined Calendar')

    except Exception as e:
        return f"Error generating Combined calendar: {str(e)}", 500


@ics_bp.route('/calendar/yogi_point.ics')
def yogi_point_calendar_feed():
    user_id, err = _verify_subscription('yogi_point')
    if err:
        return err

    try:
        saved_data, yp_cal = _get_saved_calendar_section(user_id, 'yogi_point')
        if not yp_cal:
            return 'No Yogi Point calendar data found. Please generate calendars first.', 404

        transits = yp_cal.get('transits', []) or yp_cal.get('results', [])

        events = []
        for idx, transit in enumerate(transits):
            transit_type = transit.get('type', 'Yogi Transit')
            planet = transit.get('planet', '')

            title = f"🧘 {transit_type}"
            if planet:
                title = f"🧘 Yogi Point-{planet}"

            description = f"🔮 YOGI POINT TRANSIT\\n📡 Type: {transit_type}"
            if planet:
                description += f"\\n🪐 Planet: {planet}"
            orb = transit.get('orb')
            if orb:
                description += f"\\n🎯 Orb: {orb:.2f}°"

            start_time_raw = transit.get('start_time') or transit.get('start')
            end_time_raw = transit.get('end_time') or transit.get('end')

            try:
                if start_time_raw and end_time_raw:
                    start_dt = datetime.fromisoformat(str(start_time_raw)) if isinstance(start_time_raw, str) else start_time_raw
                    end_dt = datetime.fromisoformat(str(end_time_raw)) if isinstance(end_time_raw, str) else end_time_raw
                else:
                    continue
            except (ValueError, TypeError):
                continue

            if hasattr(start_dt, 'replace'):
                start_dt = start_dt.replace(tzinfo=None)
            if hasattr(end_dt, 'replace'):
                end_dt = end_dt.replace(tzinfo=None)

            events.append({
                'id': f"yogi_{idx}",
                'title': title,
                'description': description,
                'start': start_dt,
                'end': end_dt,
            })

        return create_ics_response('yogi_point', events, cal_name_override='Yogi Point')

    except Exception as e:
        return f"Error generating Yogi Point calendar: {str(e)}", 500


@ics_bp.route('/calendar/nogo.ics')
def nogo_calendar_feed():
    user_id, err = _verify_subscription('nogo')
    if err:
        return err

    try:
        saved_data, nogo_cal = _get_saved_calendar_section(user_id, 'nogo')
        if not nogo_cal:
            return 'No NO GO calendar data found. Please generate calendars first.', 404

        periods = nogo_cal.get('periods', []) or nogo_cal.get('results', [])

        events = []
        for idx, period in enumerate(periods):
            weekday = period.get('weekday', '')
            title = f"🚫 NO GO - {weekday}"

            description = f"⛔ RAHU KALAM - NO GO PERIOD\\n"
            description += f"📅 {weekday}"
            start_str = period.get('start_time_str', '')
            end_str = period.get('end_time_str', '')
            if start_str and end_str:
                description += f"\\n⏰ {start_str} - {end_str}"
            duration = period.get('duration_minutes')
            if duration:
                description += f"\\n⏱️ Duration: {duration} minutes"

            start_time_raw = period.get('start_time') or period.get('start')
            end_time_raw = period.get('end_time') or period.get('end')

            try:
                if start_time_raw and end_time_raw:
                    start_dt = datetime.fromisoformat(str(start_time_raw)) if isinstance(start_time_raw, str) else start_time_raw
                    end_dt = datetime.fromisoformat(str(end_time_raw)) if isinstance(end_time_raw, str) else end_time_raw
                else:
                    continue
            except (ValueError, TypeError):
                continue

            if hasattr(start_dt, 'replace'):
                start_dt = start_dt.replace(tzinfo=None)
            if hasattr(end_dt, 'replace'):
                end_dt = end_dt.replace(tzinfo=None)

            events.append({
                'id': f"nogo_{idx}_{period.get('date', '')}",
                'title': title,
                'description': description,
                'start': start_dt,
                'end': end_dt,
            })

        return create_ics_response('nogo', events, cal_name_override='NO GO')

    except Exception as e:
        return f"Error generating NO GO calendar: {str(e)}", 500


@ics_bp.route('/calendar/microbird.ics')
def microbird_calendar_feed():
    user_id, err = _verify_subscription('microbird')
    if err:
        return err
    return _create_stub_ics('microbird', 'MicroBird Calendar')


@ics_bp.route('/calendar/enhanced_pof.ics')
def enhanced_pof_calendar_feed():
    user_id, err = _verify_subscription('enhanced_pof')
    if err:
        return err
    return _create_stub_ics('enhanced_pof', 'Enhanced POF Calendar')


@ics_bp.route('/calendar/all_microtransits.ics')
def all_microtransits_calendar_feed():
    user_id, err = _verify_subscription('all_microtransits')
    if err:
        return err
    return _create_stub_ics('all_microtransits', 'All Microtransits Calendar')


@ics_bp.route('/calendar/info')
def calendar_subscription_info():
    info = {
        "title": "Astrobatching Calendar Subscriptions",
        "description": "Subscribe to any of these ICS calendar feeds in Google Calendar",
        "available_calendars": [
            {
                "name": "Bird Batch Calendar",
                "endpoint": "/calendar/bird_batch.ics",
                "description": "Daily bird periods with tier classifications (Double Boost, Boost, Build)",
                "requires_auth": True,
            },
            {
                "name": "Personal Transit Calendar",
                "endpoint": "/calendar/personal.ics",
                "description": "Personalized nakshatra transit calendar based on birth data",
                "requires_auth": True,
            },
            {
                "name": "PTI Collective Calendar",
                "endpoint": "/calendar/pti.ics",
                "description": "Professional Timing Index - planetary aspect classifications",
                "requires_auth": True,
            },
            {
                "name": "Vedic Collective Calendar",
                "endpoint": "/calendar/vedic.ics",
                "description": "Rule-based Vedic classification: GO, FOCUS, BUILD, SLOW, INWARD, STOP",
                "requires_auth": True,
            },
            {
                "name": "Combined Calendar",
                "endpoint": "/calendar/combined.ics",
                "description": "All calendar systems combined into a single classification",
                "requires_auth": True,
            },
            {
                "name": "Yogi Point Calendar",
                "endpoint": "/calendar/yogi_point.ics",
                "description": "Yogi Point transit events",
                "requires_auth": True,
            },
            {
                "name": "NO GO Calendar",
                "endpoint": "/calendar/nogo.ics",
                "description": "Daily Rahu Kalam periods - times to avoid starting new activities",
                "requires_auth": True,
            },
            {
                "name": "MicroBird Calendar",
                "endpoint": "/calendar/microbird.ics",
                "description": "Bird-filtered microtransits (coming soon in rebuild)",
                "requires_auth": True,
                "status": "stub",
            },
            {
                "name": "Enhanced POF Calendar",
                "endpoint": "/calendar/enhanced_pof.ics",
                "description": "Part of Fortune transits (coming soon in rebuild)",
                "requires_auth": True,
                "status": "stub",
            },
            {
                "name": "All Microtransits Calendar",
                "endpoint": "/calendar/all_microtransits.ics",
                "description": "Every transit from all scripts (coming soon in rebuild)",
                "requires_auth": True,
                "status": "stub",
            },
        ],
        "how_to_subscribe": [
            "1. Go to your account dashboard to get personalized calendar URLs with tokens",
            "2. Copy the calendar URL you want to subscribe to",
            "3. Open Google Calendar",
            "4. Click the '+' next to 'Other calendars'",
            "5. Select 'From URL'",
            "6. Paste the calendar URL and click 'Add calendar'",
            "7. Google Calendar will automatically sync updates",
        ],
    }
    return jsonify(info)
