"""
extensions.py — Flask extension singletons.

Instantiated here (without an app) so that any module can import them
without triggering a circular import.  Bound to the actual Flask app
later via db.init_app(app) / socketio.init_app(app) in create_app().
"""
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
socketio = SocketIO()
mail = Mail()
csrf = CSRFProtect()
