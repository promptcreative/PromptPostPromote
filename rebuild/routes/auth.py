import os
from flask import Blueprint, request, jsonify, session, render_template, redirect
from database.models import db, UserProfile
from database.manager import db_manager
from datetime import datetime

auth_bp = Blueprint("auth", __name__)


def check_auth_status():
    authenticated = session.get('authenticated', False)
    user_info = session.get('user_info', {})
    auth_timestamp = session.get('auth_timestamp')

    if authenticated:
        return {
            "status": "authenticated",
            "user_info": user_info,
            "authenticated_at": auth_timestamp,
            "session_active": True
        }
    else:
        return {
            "status": "not_authenticated",
            "user_info": None,
            "authenticated_at": None,
            "session_active": False
        }


@auth_bp.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')


@auth_bp.route('/login', methods=['POST'])
def login_email():
    try:
        if request.is_json:
            data = request.get_json()
            email = data.get('email', '').strip().lower()
        else:
            email = request.form.get('email', '').strip().lower()

        if not email or '@' not in email or '.' not in email:
            if request.is_json:
                return jsonify({"status": "error", "message": "Please enter a valid email address"}), 400
            return redirect('/login?error=invalid_email')

        session['authenticated'] = True

        up = UserProfile.query.filter_by(email=email).first()
        admin_email = os.environ.get('ADMIN_EMAIL', '').strip().lower()
        is_admin = (up and up.is_admin) or (email == admin_email)

        if is_admin and up and not up.is_admin:
            up.is_admin = True
            db.session.commit()

        from database.models import Client
        client_record = Client.query.filter_by(email=email).first()

        if is_admin:
            role = 'admin'
        elif client_record:
            role = 'client'
        else:
            role = 'user'

        session['user_info'] = {
            'email': email,
            'name': client_record.name if client_record else email.split('@')[0],
            'display_name': client_record.name if client_record else email.split('@')[0].title(),
            'picture': None,
            'auth_method': 'email',
            'is_admin': is_admin,
            'role': role,
            'client_id': client_record.id if client_record else None,
        }
        session['auth_timestamp'] = datetime.now().isoformat()

        if role == 'client':
            redirect_url = '/client-dashboard'
        elif is_admin:
            redirect_url = '/account-dashboard'
        elif not up or not up.birth_date or not up.birth_time:
            redirect_url = '/profile-setup'
        else:
            redirect_url = '/account-dashboard'

        if request.is_json:
            return jsonify({
                "status": "success",
                "message": "Logged in successfully",
                "redirect": redirect_url
            })

        return redirect(redirect_url)

    except Exception as e:
        if request.is_json:
            return jsonify({"status": "error", "message": str(e)}), 500
        return redirect('/login?error=server_error')


@auth_bp.route('/auth/status')
def auth_status():
    try:
        return jsonify(check_auth_status())
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@auth_bp.route('/auth/user-info')
def get_user_info():
    try:
        if not session.get('authenticated', False):
            return jsonify({
                "status": "error",
                "message": "Not authenticated"
            }), 401

        user_info = session.get('user_info', {})
        return jsonify({"status": "success", "user_info": user_info})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@auth_bp.route('/auth/logout', methods=['GET', 'POST'])
def logout():
    try:
        session.clear()
        return jsonify({
            "status": "success",
            "message": "Logged out successfully"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@auth_bp.route('/profile/save', methods=['POST'])
def save_profile():
    try:
        raw = request.get_json(force=True, silent=True) or {}

        if not session.get('authenticated'):
            session['pending_profile'] = raw
            return jsonify({
                "status": "error",
                "message": "Not authenticated"
            }), 401

        user_email = (session.get('user_info') or {}).get('email')
        if not user_email:
            return jsonify({
                "status": "error",
                "message": "No email in session"
            }), 400

        _save_profile_to_db(user_email, raw)

        session.pop('pending_profile', None)

        return jsonify({
            "status": "success",
            "message": "Profile saved successfully"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@auth_bp.route('/api/user-profile', methods=['POST'])
def api_user_profile():
    try:
        body = request.get_json(force=True, silent=True) or {}
        cached = session.get('pending_profile') or {}
        prior = session.get('user_profile') or {}

        def _to_float_or_none(v):
            try:
                if v is None or v == "":
                    return None
                return float(v)
            except Exception:
                return None

        def _pick(*vals):
            for v in vals:
                if v is not None and v != "":
                    return v
            return None

        bl = body.get("birth_location") or {}
        cl = body.get("current_location") or {}

        birth_name = _pick(
            bl.get("name"), body.get("birth_location_name"),
            (cached.get("birth_location") or {}).get("name"),
            cached.get("birth_location_name"),
            (prior.get("birth_location") or {}).get("name"),
            prior.get("birth_location_name"),
        )
        current_name = _pick(
            cl.get("name"), body.get("current_location_name"),
            (cached.get("current_location") or {}).get("name"),
            cached.get("current_location_name"),
            (prior.get("current_location") or {}).get("name"),
            prior.get("current_location_name"),
        )

        birth_lat = _pick(
            _to_float_or_none(bl.get("latitude")),
            _to_float_or_none(body.get("birth_latitude")),
            _to_float_or_none(body.get("birth_lat")),
            _to_float_or_none((cached.get("birth_location") or {}).get("latitude")),
            _to_float_or_none(cached.get("birth_latitude")),
            _to_float_or_none((prior.get("birth_location") or {}).get("latitude")),
            _to_float_or_none(prior.get("birth_latitude")),
        )
        birth_lon = _pick(
            _to_float_or_none(bl.get("longitude")),
            _to_float_or_none(body.get("birth_longitude")),
            _to_float_or_none(body.get("birth_lon") or body.get("birth_long")),
            _to_float_or_none((cached.get("birth_location") or {}).get("longitude")),
            _to_float_or_none(cached.get("birth_longitude")),
            _to_float_or_none((prior.get("birth_location") or {}).get("longitude")),
            _to_float_or_none(prior.get("birth_longitude")),
        )

        current_lat = _pick(
            _to_float_or_none(cl.get("latitude")),
            _to_float_or_none(body.get("current_latitude")),
            _to_float_or_none(body.get("current_lat")),
            _to_float_or_none((cached.get("current_location") or {}).get("latitude")),
            _to_float_or_none(cached.get("current_latitude")),
            _to_float_or_none((prior.get("current_location") or {}).get("latitude")),
            _to_float_or_none(prior.get("current_latitude")),
        )
        current_lon = _pick(
            _to_float_or_none(cl.get("longitude")),
            _to_float_or_none(body.get("current_longitude")),
            _to_float_or_none(body.get("current_lon") or body.get("current_long")),
            _to_float_or_none((cached.get("current_location") or {}).get("longitude")),
            _to_float_or_none(cached.get("current_longitude")),
            _to_float_or_none((prior.get("current_location") or {}).get("longitude")),
            _to_float_or_none(prior.get("current_longitude")),
        )

        birth_date_str = _pick(body.get("birth_date"), cached.get("birth_date"), prior.get("birth_date"))
        birth_time_str = _pick(body.get("birth_time"), cached.get("birth_time"), prior.get("birth_time"))
        timezone = _pick(body.get("timezone"), cached.get("timezone"), prior.get("timezone"), "America/New_York")

        birth_date = None
        if birth_date_str:
            try:
                birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
            except Exception:
                pass

        birth_time = None
        if birth_time_str:
            for fmt in ("%H:%M", "%H:%M:%S"):
                try:
                    birth_time = datetime.strptime(birth_time_str, fmt).time()
                    break
                except Exception:
                    pass

        user_email = body.get('email') or (session.get('user_info') or {}).get('email')
        if not user_email:
            return jsonify({
                "status": "error",
                "message": "Please provide your email address"
            }), 400

        if 'user_info' not in session:
            session['user_info'] = {}
        session['user_info']['email'] = user_email
        session['authenticated'] = True

        up = UserProfile.query.filter_by(email=user_email).first()
        if not up:
            up = UserProfile(email=user_email)
            db.session.add(up)

        up.birth_date = birth_date
        up.birth_time = birth_time
        up.birth_location_name = birth_name
        up.birth_latitude = birth_lat
        up.birth_longitude = birth_lon
        up.current_location_name = current_name
        up.current_latitude = current_lat
        up.current_longitude = current_lon

        calendar_range_days = body.get("calendar_range_days")
        if calendar_range_days:
            try:
                up.calendar_range_days = int(calendar_range_days)
            except (ValueError, TypeError):
                pass

        db.session.commit()

        session['user_profile'] = {
            "birth_date": birth_date_str,
            "birth_time": birth_time_str,
            "timezone": timezone,
            "birth_location": {
                "name": birth_name,
                "latitude": birth_lat,
                "longitude": birth_lon,
            },
            "current_location": {
                "name": current_name,
                "latitude": current_lat,
                "longitude": current_lon,
            },
        }
        session.pop("pending_profile", None)

        return jsonify({"status": "success", "message": "Profile saved"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@auth_bp.route('/profile/get', methods=['GET'])
def get_profile():
    try:
        user_info = session.get('user_info', {})
        user_email = user_info.get('email')

        if not user_email:
            return jsonify({'status': 'success', 'profile': None})

        user_profile = UserProfile.query.filter_by(email=user_email).first()

        if user_profile:
            profile_data = {
                'birth_date': user_profile.birth_date.isoformat() if user_profile.birth_date else None,
                'birth_time': user_profile.birth_time.isoformat() if user_profile.birth_time else None,
                'birth_location': {
                    'name': user_profile.birth_location_name,
                    'latitude': user_profile.birth_latitude,
                    'longitude': user_profile.birth_longitude
                } if user_profile.birth_location_name else None,
                'current_location': {
                    'name': user_profile.current_location_name,
                    'latitude': user_profile.current_latitude,
                    'longitude': user_profile.current_longitude
                } if user_profile.current_location_name else None,
                'calendar_range_days': user_profile.calendar_range_days,
                'timezone': user_profile.birth_timezone
            }
            return jsonify({'status': 'success', 'profile': profile_data})
        else:
            return jsonify({'status': 'success', 'profile': None})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@auth_bp.route('/profile')
def profile():
    return redirect('/profile-setup')


@auth_bp.route('/profile-setup')
def profile_setup():
    user_info = session.get('user_info', {})
    if user_info.get('role') == 'client':
        return redirect('/client-dashboard')
    return render_template('profile_setup.html')


@auth_bp.route('/clear-profile', methods=['POST'])
def clear_profile():
    try:
        session.pop('user_profile', None)
        session.pop('pending_profile', None)
        session.pop('birth_date', None)
        session.pop('birth_time', None)
        session.pop('birth_latitude', None)
        session.pop('birth_longitude', None)
        session.pop('latitude', None)
        session.pop('longitude', None)
        session.pop('location', None)

        return jsonify({
            "status": "success",
            "message": "Profile cleared successfully"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


def _save_profile_to_db(user_email, data):
    def _to_float_or_none(v):
        try:
            if v is None or v == "":
                return None
            return float(v)
        except Exception:
            return None

    bl = data.get("birth_location") or {}
    cl = data.get("current_location") or {}

    birth_date = None
    birth_date_str = data.get("birth_date")
    if birth_date_str:
        try:
            birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
        except Exception:
            pass

    birth_time = None
    birth_time_str = data.get("birth_time")
    if birth_time_str:
        for fmt in ("%H:%M", "%H:%M:%S"):
            try:
                birth_time = datetime.strptime(birth_time_str, fmt).time()
                break
            except Exception:
                pass

    up = UserProfile.query.filter_by(email=user_email).first()
    if not up:
        up = UserProfile(email=user_email)
        db.session.add(up)

    up.birth_date = birth_date
    up.birth_time = birth_time
    up.birth_location_name = bl.get("name") or data.get("birth_location_name")
    up.birth_latitude = _to_float_or_none(bl.get("latitude") or data.get("birth_latitude"))
    up.birth_longitude = _to_float_or_none(bl.get("longitude") or data.get("birth_longitude"))
    up.current_location_name = cl.get("name") or data.get("current_location_name")
    up.current_latitude = _to_float_or_none(cl.get("latitude") or data.get("current_latitude"))
    up.current_longitude = _to_float_or_none(cl.get("longitude") or data.get("current_longitude"))

    calendar_range_days = data.get("calendar_range_days")
    if calendar_range_days:
        try:
            up.calendar_range_days = int(calendar_range_days)
        except (ValueError, TypeError):
            pass

    db.session.commit()

    session['user_profile'] = {
        "birth_date": birth_date_str,
        "birth_time": birth_time_str,
        "timezone": data.get("timezone", "America/New_York"),
        "birth_location": {
            "name": up.birth_location_name,
            "latitude": up.birth_latitude,
            "longitude": up.birth_longitude,
        },
        "current_location": {
            "name": up.current_location_name,
            "latitude": up.current_latitude,
            "longitude": up.current_longitude,
        },
    }
