from flask import Blueprint, render_template, redirect, request, session
from datetime import datetime, timezone
from urllib.parse import quote

from database.models import db, UserProfile
from database.manager import db_manager
from helpers.utils import get_two_month_range, normalize_dashboard_data
from helpers.dashboard import generate_dashboard_core, normalize_for_ui, get_user_defaults
from routes.auth import check_auth_status

pages_bp = Blueprint("pages", __name__)


@pages_bp.route('/', methods=['GET'])
def landing_page():
    try:
        auth_status = check_auth_status()
        if auth_status.get('status') == 'authenticated':
            return redirect('/account-dashboard')
    except Exception:
        pass
    return render_template('landing_page.html')


@pages_bp.route('/account-dashboard', methods=['GET'])
def account_dashboard():
    user_info = session.get('user_info', {})
    is_admin = user_info.get('is_admin', False)
    return render_template('account_dashboard.html', is_admin=is_admin)


@pages_bp.route('/calendar-feeds', methods=['GET'])
def calendar_feeds_page():
    personal_calendar_url = None
    pti_calendar_url = None
    vedic_calendar_url = None
    is_authenticated = False

    try:
        user_info = session.get('user_info', {})
        user_email = user_info.get('email')
        is_authenticated = session.get('authenticated', False)

        if user_email:
            user_profile = UserProfile.query.filter_by(email=user_email).first()
            if user_profile and user_profile.birth_date and user_profile.birth_time:
                birth_date = user_profile.birth_date.isoformat()
                birth_time = user_profile.birth_time.strftime('%H:%M')
                birth_lat = user_profile.birth_latitude or 0
                birth_lon = user_profile.birth_longitude or 0
                tz_offset = user_profile.birth_timezone or -5
                user_id_encoded = quote(user_email, safe='')

                personal_token = db_manager.get_subscription_token(user_email, 'personal')
                personal_calendar_url = (
                    f"/calendar/personal.ics?user_id={user_id_encoded}"
                    f"&token={personal_token}&birth_date={birth_date}"
                    f"&birth_time={birth_time}&birth_lat={birth_lat}"
                    f"&birth_lon={birth_lon}&timezone={tz_offset}"
                )

                pti_token = db_manager.get_subscription_token(user_email, 'pti')
                pti_calendar_url = (
                    f"/calendar/pti.ics?user_id={user_id_encoded}"
                    f"&token={pti_token}"
                )

                vedic_token = db_manager.get_subscription_token(user_email, 'vedic')
                vedic_calendar_url = (
                    f"/calendar/vedic.ics?user_id={user_id_encoded}"
                    f"&token={vedic_token}"
                )
    except Exception:
        pass

    return render_template('calendar_feeds.html',
                           personal_calendar_url=personal_calendar_url,
                           pti_calendar_url=pti_calendar_url,
                           vedic_calendar_url=vedic_calendar_url,
                           is_authenticated=is_authenticated)


@pages_bp.route('/my-calendars', methods=['GET'])
def my_calendars():
    user_id = "user_default"
    user_info = session.get('user_info', {})
    if user_info.get('email'):
        user_id = user_info.get('email')

    user_profile = UserProfile.query.filter_by(email=user_id).first()
    if not user_profile or not user_profile.birth_date:
        return redirect('/profile-setup')

    profile_payload = {
        'birth_date': user_profile.birth_date.isoformat() if user_profile.birth_date else None,
        'birth_time': user_profile.birth_time.isoformat() if user_profile.birth_time else None,
        'birth_latitude': user_profile.birth_latitude,
        'birth_longitude': user_profile.birth_longitude,
        'latitude': user_profile.current_latitude,
        'longitude': user_profile.current_longitude,
        'location': user_profile.current_location_name,
    }

    try:
        profile_days = int(user_profile.calendar_range_days or 0)
    except Exception:
        profile_days = 0
    if profile_days >= 30:
        profile_payload['days'] = profile_days
    else:
        _, _, auto_days = get_two_month_range()
        profile_payload['days'] = auto_days

    if request.args.get("force") in {"1", "true", "True"} or request.args.get("regenerate") in {"1", "true", "True"}:
        profile_payload["force_regenerate"] = True

    try:
        saved_data = db_manager.get_calendar_data(user_id)
        if saved_data and not profile_payload.get("force_regenerate"):
            exp_str = saved_data.get('expires_at')
            if exp_str:
                if exp_str.endswith('Z'):
                    exp_str = exp_str[:-1] + '+00:00'
                try:
                    exp_dt = datetime.fromisoformat(exp_str)
                except Exception:
                    exp_dt = None
                if exp_dt is not None:
                    if exp_dt.tzinfo is None:
                        exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                    now = datetime.now(timezone.utc)
                    if exp_dt <= now:
                        profile_payload["force_regenerate"] = True
    except Exception:
        pass

    results = generate_dashboard_core(profile_payload, user_id=user_id)

    base_url = request.url_root.rstrip('/')
    subscription_urls = db_manager.get_user_subscriptions(user_id, base_url)
    dashboard_data = normalize_dashboard_data(results)
    dashboard_data = normalize_for_ui(dashboard_data)
    dashboard_data['subscription_urls'] = subscription_urls
    dashboard_data['show_subscriptions'] = True
    dashboard_data['calendar_range_days'] = user_profile.calendar_range_days or 60

    dashboard_data['background_days'] = []
    dashboard_data['precision_timing'] = None
    try:
        saved_data = db_manager.get_calendar_data(user_id)
        if saved_data:
            bg_days = saved_data.get('background_days', [])
            if bg_days:
                dashboard_data['background_days'] = bg_days
            precision_timing = saved_data.get('precision_timing')
            if precision_timing:
                dashboard_data['precision_timing'] = precision_timing
    except Exception:
        pass

    birth_data = {
        'birth_date': user_profile.birth_date.isoformat() if user_profile.birth_date else None,
        'birth_time': user_profile.birth_time.isoformat() if user_profile.birth_time else None,
        'birth_latitude': user_profile.birth_latitude,
        'birth_longitude': user_profile.birth_longitude,
        'birth_location': user_profile.birth_location_name,
        'current_location': user_profile.current_location_name,
    }

    return render_template('calendar_view.html',
                           dashboard_data=dashboard_data,
                           birth_data=birth_data)


@pages_bp.route('/clients', methods=['GET'])
def clients_page():
    if not session.get('authenticated'):
        return redirect('/login')
    user_info = session.get('user_info', {})
    if not user_info.get('is_admin'):
        return redirect('/account-dashboard')
    return render_template('clients.html')


@pages_bp.route('/clients/<int:client_id>/results', methods=['GET'])
def client_results_page(client_id):
    if not session.get('authenticated'):
        return redirect('/login')
    user_info = session.get('user_info', {})
    if not user_info.get('is_admin'):
        return redirect('/account-dashboard')
    return render_template('client_results.html', client_id=client_id)


@pages_bp.route('/calendar-form', methods=['GET'])
def calendar_form():
    return render_template('calendar_form.html')


@pages_bp.route('/calendar-view', methods=['GET'])
def calendar_view():
    session_id = request.args.get('session_id')
    if not session_id:
        return redirect('/account-dashboard')

    return redirect('/account-dashboard')


@pages_bp.route('/interactive-calendar', methods=['GET'])
def interactive_calendar():
    return render_template('interactive_calendar.html')


@pages_bp.route('/power-days', methods=['GET'])
def power_days_page():
    return render_template('power_days.html')


@pages_bp.route('/multi-calendar', methods=['GET'])
def multi_calendar():
    return render_template('multi_calendar_view.html')
