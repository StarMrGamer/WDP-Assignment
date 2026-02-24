"""
File: app.py
Purpose: Application factory for GenCon SG
Author: to be assigned
Date: December 2025
Description: Exposes create_app() and a module-level app instance for
             gunicorn / python app.py invocations.
"""

import os

# Disable eventlet's green DNS to fix timeouts/ignore_errors on Windows
os.environ['EVENTLET_NO_GREENDNS'] = 'yes'

try:
    from dotenv import load_dotenv
    _here = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(_here, '.env'), override=True)
    print(f"[Startup] MAIL_PASSWORD set: {bool(os.environ.get('MAIL_PASSWORD'))}")
except ImportError:
    pass


import eventlet
eventlet.monkey_patch()

from flask import Flask, Blueprint
from config import get_config
from extensions import db, socketio, csrf
from sqlalchemy import text
import os


def _patch_db(app, sql_command, success_msg=""):
    """Run a DDL patch silently; ignore errors (column already exists, etc.)."""
    try:
        with db.engine.connect() as conn:
            conn.execute(text(sql_command))
            conn.commit()
            if success_msg:
                print(f"Database patched: {success_msg}")
    except Exception:
        pass


def create_app(config_name=None):
    """
    Application factory.

    Args:
        config_name: 'development' | 'testing' | 'production'
                     Defaults to FLASK_ENV env var, then 'development'.
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)

    # Load configuration
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    if hasattr(config_class, 'init_app'):
        config_class.init_app(app)

    # ── Extensions ────────────────────────────────────────────
    csrf.init_app(app)

    ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '*')
    if ALLOWED_ORIGINS != '*':
        ALLOWED_ORIGINS = ALLOWED_ORIGINS.split(',')
    socketio.init_app(app, cors_allowed_origins=ALLOWED_ORIGINS, async_mode='eventlet')
    db.init_app(app)

    from extensions import mail
    mail.init_app(app)
    print(f"[Mail] SMTP server: {app.config.get('MAIL_SERVER')}:{app.config.get('MAIL_PORT')} | user: {app.config.get('MAIL_USERNAME')} | password set: {bool(app.config.get('MAIL_PASSWORD'))}")


    # ── Socket.IO handlers & notification listener ────────────
    import socket_handlers  # noqa: F401 — registers @socketio.on decorators (once)

    # ── Blueprints ────────────────────────────────────────────
    from blueprints.main import main_bp
    from blueprints.auth import auth_bp
    from blueprints.senior import senior_bp
    from blueprints.youth import youth_bp
    from blueprints.admin import admin_bp

    app.register_blueprint(main_bp)                          # /, /support, /api/*, …
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(senior_bp, url_prefix='/senior')
    app.register_blueprint(youth_bp, url_prefix='/youth')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Portfolio static files served as a Blueprint
    profolio_bp = Blueprint(
        'profolio', __name__,
        static_folder='profolio',
        static_url_path='/'
    )

    @profolio_bp.route('/')
    def profolio_index():
        return profolio_bp.send_static_file('index.html')

    app.register_blueprint(profolio_bp, url_prefix='/profolio')

    # ── Database initialisation (skip in tests — fixture handles it) ───
    if not app.testing:
        with app.app_context():
            db.create_all()

            _patch_db(app, "ALTER TABLE community_posts ADD COLUMN photo_url VARCHAR(255)",
                      "Added photo_url to community_posts")
            _patch_db(app, "ALTER TABLE communities ADD COLUMN photo_url VARCHAR(255)",
                      "Added photo_url to communities")
            _patch_db(app, "ALTER TABLE community_members ADD COLUMN last_viewed_at DATETIME",
                      "Added last_viewed_at to community_members")
            _patch_db(app, "ALTER TABLE events ADD COLUMN status VARCHAR(20) DEFAULT 'approved'",
                      "Added status to events")
            _patch_db(app, "ALTER TABLE events ADD COLUMN justification TEXT",
                      "Added justification to events")
            _patch_db(app,
                "ALTER TABLE event_participants ADD COLUMN reminder_24h_sent BOOLEAN NOT NULL DEFAULT 0",
                "Added reminder_24h_sent to event_participants")
            _patch_db(app,
                "ALTER TABLE event_participants ADD COLUMN reminder_1h_sent BOOLEAN NOT NULL DEFAULT 0",
                "Added reminder_1h_sent to event_participants")

            try:
                with db.engine.connect() as conn:
                    conn.execute(text("SELECT count(*) FROM chat_reports"))
            except Exception:
                print("Creating chat_reports table...")
                db.create_all()

            _patch_db(app, "ALTER TABLE chat_reports ADD COLUMN status VARCHAR(20) DEFAULT 'pending'",
                      "Added status to chat_reports")
            _patch_db(app, "ALTER TABLE chat_reports ADD COLUMN admin_notes TEXT",
                      "Added admin_notes to chat_reports")
            _patch_db(app, "ALTER TABLE users ADD COLUMN elo INTEGER DEFAULT 1200",
                      "Added elo to users")
            _patch_db(app, "ALTER TABLE game_sessions ADD COLUMN winner_id INTEGER REFERENCES users(id)",
                      "Added winner_id to game_sessions")
            _patch_db(app, "ALTER TABLE game_sessions ADD COLUMN game_state TEXT",
                      "Added game_state to game_sessions")

            try:
                with db.engine.connect() as conn:
                    conn.execute(text("SELECT count(*) FROM game_history"))
            except Exception:
                print("Creating game_history table...")
                db.create_all()

            _patch_db(app, "ALTER TABLE chat_reports ADD COLUMN ai_analysis TEXT",
                      "Added ai_analysis to chat_reports")

            try:
                with db.engine.connect() as conn:
                    conn.execute(text("SELECT count(*) FROM support_tickets"))
            except Exception:
                print("Creating support_tickets table...")
                db.create_all()

            print("Database tables created successfully")

        import atexit
        from apscheduler.schedulers.background import BackgroundScheduler
        from services.reminders import send_event_reminders

        scheduler = BackgroundScheduler(daemon=True)
        scheduler.add_job(
            func=send_event_reminders,
            args=[app],
            trigger='interval',
            minutes=15,
            id='event_reminders',
            misfire_grace_time=300,
            max_instances=1,
        )
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown(wait=False))
        print("Event reminder scheduler started (every 15 minutes)")

    return app


# ── Module-level app instance (gunicorn / python app.py) ──────────────────
app = create_app()


# ==================== MAIN EXECUTION ====================
if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    config_name = os.environ.get('FLASK_ENV', 'development')
    port = int(os.environ.get('PORT', 5001))
    print("=" * 60)
    print("Starting GenCon SG Application")
    print("=" * 60)
    print(f"Environment: {config_name}")
    print(f"Debug Mode: {app.config['DEBUG']}")
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print("=" * 60)
    print(f"Server running at http://0.0.0.0:{port}")
    print("Press CTRL+C to quit")
    print("=" * 60)

    socketio.run(app, host='0.0.0.0', port=port, debug=True)
