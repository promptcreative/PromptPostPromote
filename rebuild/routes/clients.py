from flask import Blueprint, request, jsonify, session
from datetime import datetime
from database.models import db, Client, CalendarData
from database.manager import db_manager
from helpers.dashboard import generate_dashboard_core
from helpers.utils import make_json_serializable, normalize_dashboard_data

clients_bp = Blueprint('clients', __name__)


def _get_owner_email():
    user_info = session.get('user_info', {})
    return user_info.get('email')


@clients_bp.route('/api/clients', methods=['GET'])
def list_clients():
    if not session.get('authenticated'):
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    try:
        owner_email = _get_owner_email()
        clients = Client.query.filter_by(owner_email=owner_email).all()
        return jsonify([c.to_dict() for c in clients])
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@clients_bp.route('/api/clients', methods=['POST'])
def create_client():
    if not session.get('authenticated'):
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    try:
        owner_email = _get_owner_email()
        data = request.get_json(force=True, silent=True) or {}

        name = data.get('name')
        if not name:
            return jsonify({"status": "error", "message": "Name is required"}), 400

        birth_date = None
        birth_date_str = data.get('birth_date')
        if birth_date_str:
            try:
                birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
            except Exception:
                pass

        birth_time = None
        birth_time_str = data.get('birth_time')
        if birth_time_str:
            for fmt in ("%H:%M", "%H:%M:%S"):
                try:
                    birth_time = datetime.strptime(birth_time_str, fmt).time()
                    break
                except Exception:
                    pass

        def _to_float(v):
            try:
                if v is None or v == "":
                    return None
                return float(v)
            except Exception:
                return None

        client = Client(
            owner_email=owner_email,
            name=name,
            email=data.get('email'),
            birth_date=birth_date,
            birth_time=birth_time,
            birth_latitude=_to_float(data.get('birth_latitude')),
            birth_longitude=_to_float(data.get('birth_longitude')),
            birth_timezone=_to_float(data.get('birth_timezone')) if data.get('birth_timezone') is not None else -5.0,
            birth_location_name=data.get('birth_location_name'),
            current_latitude=_to_float(data.get('current_latitude')),
            current_longitude=_to_float(data.get('current_longitude')),
            current_location_name=data.get('current_location_name'),
        )

        db.session.add(client)
        db.session.commit()

        return jsonify(client.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@clients_bp.route('/api/clients/<int:client_id>', methods=['GET'])
def get_client(client_id):
    if not session.get('authenticated'):
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    try:
        owner_email = _get_owner_email()
        client = Client.query.get(client_id)

        if not client:
            return jsonify({"status": "error", "message": "Client not found"}), 404

        if client.owner_email != owner_email:
            return jsonify({"status": "error", "message": "Forbidden"}), 403

        return jsonify(client.to_dict())

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@clients_bp.route('/api/clients/<int:client_id>', methods=['PUT'])
def update_client(client_id):
    if not session.get('authenticated'):
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    try:
        owner_email = _get_owner_email()
        client = Client.query.get(client_id)

        if not client:
            return jsonify({"status": "error", "message": "Client not found"}), 404

        if client.owner_email != owner_email:
            return jsonify({"status": "error", "message": "Forbidden"}), 403

        data = request.get_json(force=True, silent=True) or {}

        def _to_float(v):
            try:
                if v is None or v == "":
                    return None
                return float(v)
            except Exception:
                return None

        if 'name' in data:
            client.name = data['name']
        if 'email' in data:
            client.email = data['email']
        if 'birth_location_name' in data:
            client.birth_location_name = data['birth_location_name']
        if 'current_location_name' in data:
            client.current_location_name = data['current_location_name']
        if 'birth_latitude' in data:
            client.birth_latitude = _to_float(data['birth_latitude'])
        if 'birth_longitude' in data:
            client.birth_longitude = _to_float(data['birth_longitude'])
        if 'birth_timezone' in data:
            client.birth_timezone = _to_float(data['birth_timezone'])
        if 'current_latitude' in data:
            client.current_latitude = _to_float(data['current_latitude'])
        if 'current_longitude' in data:
            client.current_longitude = _to_float(data['current_longitude'])
        if 'calendar_range_days' in data:
            try:
                client.calendar_range_days = int(data['calendar_range_days'])
            except (ValueError, TypeError):
                pass

        if 'birth_date' in data:
            birth_date_str = data['birth_date']
            if birth_date_str:
                try:
                    client.birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
                except Exception:
                    pass
            else:
                client.birth_date = None

        if 'birth_time' in data:
            birth_time_str = data['birth_time']
            if birth_time_str:
                for fmt in ("%H:%M", "%H:%M:%S"):
                    try:
                        client.birth_time = datetime.strptime(birth_time_str, fmt).time()
                        break
                    except Exception:
                        pass
            else:
                client.birth_time = None

        db.session.commit()

        return jsonify(client.to_dict())

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@clients_bp.route('/api/clients/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    if not session.get('authenticated'):
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    try:
        owner_email = _get_owner_email()
        client = Client.query.get(client_id)

        if not client:
            return jsonify({"status": "error", "message": "Client not found"}), 404

        if client.owner_email != owner_email:
            return jsonify({"status": "error", "message": "Forbidden"}), 403

        CalendarData.query.filter_by(user_email=f"client_{client_id}").delete()
        db.session.delete(client)
        db.session.commit()

        return jsonify({"status": "success", "message": "Client deleted"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@clients_bp.route('/api/clients/<int:client_id>/generate', methods=['POST'])
def generate_client_calendar(client_id):
    if not session.get('authenticated'):
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    try:
        owner_email = _get_owner_email()
        client = Client.query.get(client_id)

        if not client:
            return jsonify({"status": "error", "message": "Client not found"}), 404

        if client.owner_email != owner_email:
            return jsonify({"status": "error", "message": "Forbidden"}), 403

        if not client.birth_date or not client.birth_time:
            return jsonify({"status": "error", "message": "Client needs birth date and time before generating"}), 400

        client.calendar_status = 'generating'
        db.session.commit()

        client_user_id = f"client_{client_id}"

        profile_payload = {
            'birth_date': client.birth_date.isoformat(),
            'birth_time': client.birth_time.isoformat(),
            'birth_latitude': client.birth_latitude or 0,
            'birth_longitude': client.birth_longitude or 0,
            'latitude': client.current_latitude or client.birth_latitude or 0,
            'longitude': client.current_longitude or client.birth_longitude or 0,
            'location': client.current_location_name or client.birth_location_name or '',
            'timezone_offset': client.birth_timezone or -5.0,
            'days': client.calendar_range_days or 60,
            'force_regenerate': True,
        }

        results = generate_dashboard_core(profile_payload, user_id=client_user_id)

        client.calendar_status = 'ready'
        client.last_generated_at = datetime.utcnow()
        db.session.commit()

        summary = {}
        calendars = (results or {}).get('calendars', {})
        for cal_name, cal_data in calendars.items():
            if isinstance(cal_data, dict):
                if cal_data.get('error'):
                    summary[cal_name] = {'status': 'error', 'error': str(cal_data['error'])}
                elif cal_data.get('generated') or cal_data.get('results') or cal_data.get('daily_results'):
                    summary[cal_name] = {'status': 'ready'}
                else:
                    summary[cal_name] = {'status': 'partial'}

        return jsonify({
            "status": "success",
            "client_id": client_id,
            "calendar_summary": summary,
            "generated_at": client.last_generated_at.isoformat(),
        })

    except Exception as e:
        try:
            client = Client.query.get(client_id)
            if client:
                client.calendar_status = 'error'
                db.session.commit()
        except Exception:
            db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@clients_bp.route('/api/clients/<int:client_id>/calendar', methods=['GET'])
def get_client_calendar(client_id):
    if not session.get('authenticated'):
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    try:
        owner_email = _get_owner_email()
        client = Client.query.get(client_id)

        if not client:
            return jsonify({"status": "error", "message": "Client not found"}), 404

        if client.owner_email != owner_email:
            return jsonify({"status": "error", "message": "Forbidden"}), 403

        client_user_id = f"client_{client_id}"
        saved_data = db_manager.get_calendar_data(client_user_id)

        if not saved_data:
            return jsonify({"status": "error", "message": "No calendar data. Generate first."}), 404

        calendars = saved_data.get('calendars', {})

        combined = calendars.get('combined', {})
        combined_results = combined.get('results', [])

        background_days = []
        golden_windows = []
        for day in combined_results:
            classification = day.get('classification', '').upper()
            day_date = day.get('date', '')
            if classification in ('OMNI', 'DOUBLE GO', 'DOUBLE_GO'):
                golden_windows.append({
                    'date': day_date,
                    'classification': classification,
                    'label': day.get('label', classification),
                    'description': day.get('description', ''),
                    'pti_label': day.get('pti_label', ''),
                    'vedic_label': day.get('vedic_label', ''),
                    'personal_label': day.get('personal_label', ''),
                })
            if classification in ('OMNI', 'DOUBLE GO', 'DOUBLE_GO', 'GOOD'):
                background_days.append(day_date)

        bird_batch = calendars.get('bird_batch', {})
        bird_periods = []
        if isinstance(bird_batch, dict) and not bird_batch.get('error'):
            for day_data in (bird_batch.get('daily_results') or bird_batch.get('results') or []):
                day_date = day_data.get('date', '')
                if day_date in background_days:
                    periods = day_data.get('top_periods', day_data.get('periods', []))
                    for p in periods[:3]:
                        bird_periods.append({
                            'date': day_date,
                            'start': p.get('start_time', p.get('start', '')),
                            'end': p.get('end_time', p.get('end', '')),
                            'tier': p.get('tier', p.get('combination', '')),
                            'bird': p.get('bird', ''),
                            'activity': p.get('activity', ''),
                        })

        return jsonify({
            "status": "success",
            "client": client.to_dict(),
            "golden_windows": golden_windows,
            "background_days": background_days,
            "bird_periods": bird_periods,
            "combined_results": combined_results,
            "generated_at": saved_data.get('period', {}).get('generated_at'),
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
