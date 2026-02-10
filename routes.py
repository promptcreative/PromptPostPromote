import os
from flask import render_template, request, jsonify, session, redirect, url_for
from functools import wraps
from app import app, db
from models import Calendar, CalendarEvent, Settings
from utils import parse_ics_content
from publer_service import PublerAPI
import requests

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "123")


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session.permanent = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/api/calendars', methods=['GET'])
@login_required
def get_calendars():
    calendars = Calendar.query.all()
    return jsonify([c.to_dict() for c in calendars])


@app.route('/api/calendars/fetch', methods=['POST'])
@login_required
def fetch_calendar():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    ics_url = data.get('ics_url')
    calendar_type = data.get('calendar_type', 'default')
    calendar_name = data.get('calendar_name', calendar_type)

    if not ics_url:
        return jsonify({'error': 'ics_url is required'}), 400

    try:
        resp = requests.get(ics_url, timeout=30)
        resp.raise_for_status()
        ics_content = resp.text
    except Exception as e:
        return jsonify({'error': f'Failed to fetch calendar: {str(e)}'}), 500

    try:
        events = parse_ics_content(ics_content)

        existing = Calendar.query.filter_by(calendar_type=calendar_type).first()
        if existing:
            CalendarEvent.query.filter_by(calendar_id=existing.id).delete()
            calendar = existing
            calendar.calendar_name = calendar_name
            calendar.ics_url = ics_url
        else:
            calendar = Calendar(calendar_type=calendar_type, calendar_name=calendar_name, ics_url=ics_url)
            db.session.add(calendar)
            db.session.flush()

        for ev in events:
            event = CalendarEvent(
                calendar_id=calendar.id,
                summary=ev['summary'],
                start_time=ev['start_time'],
                end_time=ev['end_time'],
                midpoint_time=ev['midpoint_time'],
                event_type=ev.get('event_type', 'default')
            )
            db.session.add(event)

        db.session.commit()
        return jsonify({'success': True, 'calendar': calendar.to_dict(), 'event_count': len(events)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/calendars/import', methods=['POST'])
@login_required
def import_calendar():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    calendar_type = request.form.get('calendar_type', 'default')
    calendar_name = request.form.get('calendar_name', file.filename or 'Calendar')

    try:
        content = file.read().decode('utf-8')
        events = parse_ics_content(content)

        existing = Calendar.query.filter_by(calendar_type=calendar_type).first()
        if existing:
            CalendarEvent.query.filter_by(calendar_id=existing.id).delete()
            calendar = existing
            calendar.calendar_name = calendar_name
        else:
            calendar = Calendar(calendar_type=calendar_type, calendar_name=calendar_name)
            db.session.add(calendar)
            db.session.flush()

        for ev in events:
            event = CalendarEvent(
                calendar_id=calendar.id,
                summary=ev['summary'],
                start_time=ev['start_time'],
                end_time=ev['end_time'],
                midpoint_time=ev['midpoint_time'],
                event_type=ev.get('event_type', 'default')
            )
            db.session.add(event)

        db.session.commit()
        return jsonify({'success': True, 'calendar': calendar.to_dict(), 'event_count': len(events)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/calendars/<int:calendar_id>', methods=['DELETE'])
@login_required
def delete_calendar(calendar_id):
    calendar = Calendar.query.get(calendar_id)
    if not calendar:
        return jsonify({'error': 'Not found'}), 404
    CalendarEvent.query.filter_by(calendar_id=calendar_id).delete()
    db.session.delete(calendar)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/events', methods=['GET'])
@login_required
def get_events():
    cal_type = request.args.get('calendar_type')
    if cal_type:
        calendar = Calendar.query.filter_by(calendar_type=cal_type).first()
        if not calendar:
            return jsonify([])
        events = CalendarEvent.query.filter_by(calendar_id=calendar.id).order_by(CalendarEvent.midpoint_time).all()
    else:
        events = CalendarEvent.query.order_by(CalendarEvent.midpoint_time).all()
    return jsonify([e.to_dict() for e in events])


@app.route('/api/events/<int:event_id>/copy', methods=['POST'])
@login_required
def update_event_copy(event_id):
    event = CalendarEvent.query.get(event_id)
    if not event:
        return jsonify({'error': 'Not found'}), 404
    data = request.get_json()
    event.social_copy = data.get('social_copy', '')
    if event.social_copy:
        event.publer_status = 'ready'
    db.session.commit()
    return jsonify(event.to_dict())


@app.route('/api/publer/test', methods=['GET'])
@login_required
def test_publer():
    try:
        publer = PublerAPI()
        result = publer.test_connection()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/publer/push', methods=['POST'])
@login_required
def push_to_publer():
    data = request.get_json()
    event_ids = data.get('event_ids', [])

    if not event_ids:
        return jsonify({'error': 'No events selected'}), 400

    try:
        publer = PublerAPI()
    except Exception as e:
        return jsonify({'error': f'Publer not configured: {str(e)}'}), 500

    results = []
    for eid in event_ids:
        event = CalendarEvent.query.get(eid)
        if not event or not event.social_copy:
            results.append({'event_id': eid, 'success': False, 'error': 'No content'})
            continue

        scheduled_time = event.midpoint_time.strftime('%Y-%m-%dT%H:%M:%S')
        result = publer.create_draft(text=event.social_copy, scheduled_time=scheduled_time)

        if result.get('success'):
            event.publer_status = 'pushed'
            event.publer_post_id = str(result.get('draft', {}).get('id', ''))
            db.session.commit()

        results.append({'event_id': eid, **result})

    return jsonify({'results': results})


@app.route('/api/settings', methods=['GET'])
@login_required
def get_settings():
    settings = Settings.query.first()
    if not settings:
        settings = Settings()
        db.session.add(settings)
        db.session.commit()
    return jsonify(settings.to_dict())


@app.route('/api/settings', methods=['POST'])
@login_required
def update_settings():
    data = request.get_json()
    settings = Settings.query.first()
    if not settings:
        settings = Settings()
        db.session.add(settings)

    for key in ['company_name', 'branded_hashtag', 'shop_url', 'publer_workspace_id']:
        if key in data:
            setattr(settings, key, data[key])

    db.session.commit()
    return jsonify(settings.to_dict())
