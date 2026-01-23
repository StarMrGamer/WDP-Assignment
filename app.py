"""
File: app.py
Purpose: Main Flask application initialization for GenCon SG
Author: Rai (Team Lead)
Date: December 2025
Description: This is the entry point for the Flask application. It:
             - Initializes Flask app with configuration
             - Sets up SQLAlchemy database
             - Registers blueprints (auth, senior, youth, admin)
             - Configures session management
             - Creates database tables on first run
             - Provides the main route (index/landing page)
"""

from flask import Flask, render_template, session, redirect, url_for, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from config import get_config
from models import db
from datetime import timedelta
import os

# Initialize Flask application
app = Flask(__name__)

# Load configuration
config_name = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(get_config(config_name))

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Initialize database with app
db.init_app(app)

# ==================== SOCKET.IO EVENTS ====================
@socketio.on('join')
def on_join(data):
    from models import GameSession
    room = f"game_{data['game_id']}"
    join_room(room)
    print(f"DEBUG: User {session.get('username')} (ID: {session.get('user_id')}) joined room {room}")
    
    # Send initial status
    gs = GameSession.query.get(data['game_id'])
    if gs:
        emit('init_game', {'status': gs.status})
        print(f"DEBUG: Sent init_game with status {gs.status} to {session.get('username')}")

@socketio.on('challenge')
def on_challenge(data):
    # Data contains game_id and buddy_id
    buddy_room = f"user_{data['buddy_id']}"
    print(f"DEBUG: {session.get('username')} challenging buddy in room {buddy_room}")
    socketio.emit('game_challenge', {
        'challenger_name': session.get('full_name'),
        'challenger_id': session.get('user_id'),
        'game_id': data['game_id'],
        'game_title': data['game_title']
    }, room=buddy_room)

@socketio.on('ready')
def on_ready(data):
    from models import GameSession, db
    session_id = data.get('session_id')
    user_id = session.get('user_id')
    print(f"DEBUG: Ready event from {user_id} for session {session_id}")
    
    gs = GameSession.query.get(session_id)
    if not gs: 
        print(f"DEBUG: Session {session_id} not found")
        return

    if gs.player1_id == user_id:
        gs.player1_ready = True
        print(f"DEBUG: Player 1 ({user_id}) is ready")
    elif gs.player2_id == user_id:
        gs.player2_ready = True
        print(f"DEBUG: Player 2 ({user_id}) is ready")
    
    db.session.commit()
    
    room = f"game_{session_id}"
    if gs.player1_ready and gs.player2_ready:
        gs.status = 'active'
        db.session.commit()
        print(f"DEBUG: BOTH READY - Starting game {session_id} in room {room}")
        socketio.emit('game_start', {'session_id': session_id}, room=room)
    else:
        print(f"DEBUG: One player ready, waiting for other. Room: {room}")
        socketio.emit('player_ready', {'user_id': user_id}, room=room)

@socketio.on('forfeit')
def on_forfeit(data):
    from models import GameSession, db
    session_id = data.get('session_id')
    gs = GameSession.query.get(session_id)
    if gs:
        gs.status = 'abandoned'
        db.session.commit()
        room = f"game_{session_id}"
        print(f"DEBUG: Game {session_id} forfeited by {session.get('username')}. Notifying room {room}")
        socketio.emit('opponent_forfeit', {'winner_name': session.get('full_name')}, room=room, include_self=False)

@socketio.on('move')
def on_move(data):
    room = f"game_{data['game_id']}"
    # Broadcast the move to the other player in the room
    emit('move', data, room=room, include_self=False)
    print(f"Move received in room {room}: {data['move']}")

@socketio.on('connect')
def on_connect():
    # Join a private room for the user to receive challenges
    if 'user_id' in session:
        join_room(f"user_{session['user_id']}")

@socketio.on('disconnect')
def on_disconnect():
    print(f"User {session.get('username')} disconnected")


# ==================== BLUEPRINT REGISTRATION ====================
# Blueprints organize routes into modules (auth, senior, youth, admin)
# Each blueprint handles routes for its specific user role

from blueprints.auth import auth_bp
from blueprints.senior import senior_bp
from blueprints.youth import youth_bp
from blueprints.admin import admin_bp

# Register blueprints with URL prefixes
# auth_bp: Handles /login, /register, /logout
app.register_blueprint(auth_bp, url_prefix='/auth')

# senior_bp: Handles /senior/dashboard, /senior/stories, etc.
app.register_blueprint(senior_bp, url_prefix='/senior')

# youth_bp: Handles /youth/dashboard, /youth/story_feed, etc.
app.register_blueprint(youth_bp, url_prefix='/youth')

# admin_bp: Handles /admin/dashboard, /admin/users, etc.
app.register_blueprint(admin_bp, url_prefix='/admin')


# ==================== DATABASE INITIALIZATION ====================
# Create tables in app context (runs once at startup)
with app.app_context():
    """
    Create all database tables at application startup.

    This runs once when the app initializes.
    It creates all tables defined in models.py if they don't exist.

    Note: In production, database migrations should be handled by Flask-Migrate
    """
    db.create_all()
    print("Database tables created successfully")


# ==================== CONTEXT PROCESSORS ====================
@app.context_processor
def inject_user():
    """
    Make session data available to all templates.

    Context processors inject variables into template context automatically.
    This allows templates to access session.user_id, session.role, etc.

    Returns:
        dict: Dictionary with session object
    """
    return dict(session=session)


# ==================== MAIN ROUTES ====================
@app.route('/')
def index():
    """
    Landing page route - displays role selection cards.
    Redirects logged-in users to their respective dashboards.
    """
    if 'user_id' in session:
        role = session.get('role')
        if role == 'senior':
            return redirect(url_for('senior.dashboard'))
        elif role == 'youth':
            return redirect(url_for('youth.dashboard'))
        elif role == 'admin':
            return redirect(url_for('admin.dashboard'))

    return render_template('index.html')


# ==================== SECURITY HEADERS ====================
@app.after_request
def add_security_headers(response):
    """
    Add security headers to response.
    Specifically enables unsafe-eval for third-party libraries that require it.
    """
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' blob: https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
        "img-src 'self' data: blob: https:; "
        "connect-src 'self' ws: wss: https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "worker-src 'self' blob:;"
    )
    response.headers['Content-Security-Policy'] = csp
    return response


# ==================== ERROR HANDLERS ====================
@app.errorhandler(404)
def not_found_error(error):
    """
    Handle 404 Not Found errors.

    Args:
        error: Error object from Flask

    Returns:
        Rendered 404.html template with 404 status code
    """
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """
    Handle 500 Internal Server errors.

    Args:
        error: Error object from Flask

    Returns:
        Rendered 500.html template with 500 status code

    Note: Rolls back database session in case of database errors
    """
    db.session.rollback()
    return render_template('errors/500.html'), 500


@app.errorhandler(403)
def forbidden_error(error):
    """
    Handle 403 Forbidden errors (unauthorized access).

    Args:
        error: Error object from Flask

    Returns:
        Rendered 403.html template with 403 status code
    """
    return render_template('errors/403.html'), 403


# ==================== TEMPLATE FILTERS ====================
@app.template_filter('timeago')
def timeago_filter(date):
    """
    Convert datetime to relative time string (e.g., "2 hours ago").

    This is a Jinja2 template filter that can be used in templates like:
    {{ story.created_at|timeago }}

    Args:
        date (datetime): DateTime object to convert

    Returns:
        str: Human-readable relative time string
    """
    from datetime import datetime
    now = datetime.utcnow()
    diff = now - date

    seconds = diff.total_seconds()
    if seconds < 60:
        return 'Just now'
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f'{minutes} minute{"s" if minutes != 1 else ""} ago'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours} hour{"s" if hours != 1 else ""} ago'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{days} day{"s" if days != 1 else ""} ago'
    else:
        return (date + timedelta(hours=8)).strftime('%B %d, %Y')


@app.template_filter('format_date')
def format_date_filter(date, format='%B %d, %Y'):
    """
    Format datetime object to string.

    Args:
        date (datetime): DateTime object to format
        format (str): strftime format string

    Returns:
        str: Formatted date string
    """
    if date:
        return (date + timedelta(hours=8)).strftime(format)
    return ''


@app.template_filter('date')
def date_filter(value, format='%B %d, %Y'):
    """
    Custom date filter for Jinja2 templates.

    This filter formats datetime objects or the string 'now' into formatted date strings.
    Usage in templates: {{ "now"|date("%A, %B %d, %Y") }}

    Args:
        value: Either a datetime object or the string 'now'
        format (str): strftime format string (default: '%B %d, %Y')

    Common format codes:
        %A - Full weekday name (Monday, Tuesday, etc.)
        %B - Full month name (January, February, etc.)
        %d - Day of month (01-31)
        %Y - Year with century (2025)
        %I - Hour 12-hour format (01-12)
        %M - Minute (00-59)
        %p - AM/PM

    Returns:
        str: Formatted date string
    """
    from datetime import datetime

    # If value is the string "now", use current datetime
    if value == "now":
        value = datetime.utcnow() + timedelta(hours=8)
    elif value:
        # Assume it's a UTC datetime object from DB
        value = value + timedelta(hours=8)

    # Format the datetime object
    if value:
        return value.strftime(format)
    return ''


# ==================== NOTIFICATION API ====================
@app.route('/api/notifications')
def get_notifications():
    if 'user_id' not in session:
        return {'count': 0, 'notifications': []}
    
    from models import Notification
    user_id = session['user_id']
    
    # Get unread notifications
    notifs = Notification.query.filter_by(user_id=user_id, is_read=False)\
        .order_by(Notification.created_at.desc()).all()
    
    return {
        'count': len(notifs),
        'notifications': [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.type,
            'link': n.link,
            'timeAgo': timeago_filter(n.created_at)
        } for n in notifs]
    }

@app.route('/api/notifications/<int:notification_id>/dismiss', methods=['POST'])
def dismiss_notification(notification_id):
    if 'user_id' not in session:
        return {'success': False}, 403
    
    from models import Notification, db
    notif = Notification.query.get_or_404(notification_id)
    
    if notif.user_id != session['user_id']:
        return {'success': False}, 403
    
    notif.is_read = True
    db.session.commit()
    return {'success': True}


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('images/default-avatar.png')


# ==================== STREAK API ====================
@app.route('/api/streak')
def get_streak():
    """
    Get user's current streak status.
    Returns JSON with current streak count and any new rewards.
    """
    if 'user_id' not in session:
        return {'currentStreak': 0}
    
    from models import Streak
    user_id = session['user_id']
    
    streak = Streak.query.filter_by(user_id=user_id).first()
    
    if not streak:
        return {'currentStreak': 0}
        
    return {
        'currentStreak': streak.current_streak,
        'points': streak.points,
        # Future: Add logic for new badges/daily rewards
        'newBadge': None,
        'dailyReward': False
    }


# ==================== MAIN EXECUTION ====================
if __name__ == '__main__':
    """
    Run the Flask development server.pyqpython -m pip install

    The app runs on http://localhost:5000 by default.
    Debug mode is enabled based on config settings.

    Command line: python app.py
    """
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    print("="* 60)
    print("Starting GenCon SG Application")
    print("="* 60)
    print(f"Environment: {config_name}")
    print(f"Debug Mode: {app.config['DEBUG']}")
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print("="* 60)
    print("Server running at http://localhost:5000")
    print("Press CTRL+C to quit")
    print("="* 60)

    # Run the development server
    socketio.run(
        app,
        host='0.0.0.0',
        port=5001,
        debug=app.config['DEBUG']
    )
