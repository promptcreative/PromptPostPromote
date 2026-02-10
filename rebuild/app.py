#!/usr/bin/env python3
"""
Astrobatching - Vedic Astrology Timing Platform
Clean rebuild with organized blueprints
"""

import os
from datetime import datetime, date, time
from flask import Flask
from flask.json.provider import DefaultJSONProvider
from database.models import db, init_database


class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, (datetime, date, time)):
            return obj.isoformat()
        return super().default(obj)


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    app.json = CustomJSONProvider(app)
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.jinja_env.auto_reload = True

    init_database(app)

    from routes.auth import auth_bp
    from routes.pages import pages_bp
    from routes.calendars import calendars_bp
    from routes.ics_feeds import ics_bp
    from routes.microtransits import microtransits_bp
    from routes.downloads import downloads_bp
    from routes.api import api_bp
    from routes.clients import clients_bp
    from routes.power_days import power_days_bp
    from routes.publer import publer_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(calendars_bp)
    app.register_blueprint(ics_bp)
    app.register_blueprint(microtransits_bp)
    app.register_blueprint(downloads_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(power_days_bp)
    app.register_blueprint(publer_bp)

    @app.after_request
    def add_no_cache_headers(response):
        if 'text/html' in response.content_type:
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response

    @app.errorhandler(404)
    def not_found(e):
        return {"error": "Not found"}, 404

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
