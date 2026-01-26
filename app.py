"""
File: app.py
Purpose: Main Flask application initialization for GenCon SG
Author: to be assigned
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
from models import db, ChatReport
from datetime import timedelta
from sqlalchemy import text
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

# ==================== ELO CALCULATION ====================
def calculate_elo(winner_id, p1_id, p2_id, is_draw=False):
    """
    Calculate new ELO ratings for players.
    K-factor is fixed at 32 for simplicity.
    """
    from models import User, GameHistory, db
    
    p1 = User.query.get(p1_id)
    p2 = User.query.get(p2_id)
    
    if not p1 or not p2:
        return
        
    k = 32
    
    # Expected scores
    expected_p1 = 1 / (1 + 10 ** ((p2.elo - p1.elo) / 400))
    expected_p2 = 1 / (1 + 10 ** ((p1.elo - p2.elo) / 400))
    
    # Actual scores
    if is_draw:
        actual_p1 = 0.5
        actual_p2 = 0.5
    else:
        actual_p1 = 1 if winner_id == p1_id else 0
        actual_p2 = 1 if winner_id == p2_id else 0
        
    p1_old_elo = p1.elo
    p2_old_elo = p2.elo
    
    # New ratings
    p1.elo = round(p1.elo + k * (actual_p1 - expected_p1))
    p2.elo = round(p2.elo + k * (actual_p2 - expected_p2))
    
    db.session.commit()
    return p1_old_elo, p1.elo, p2_old_elo, p2.elo

def handle_game_over(session_id, winner_id=None, winner_color=None, is_draw=False):
    from models import GameSession, GameHistory, Streak, db, User
    
    gs = GameSession.query.get(session_id)
    if not gs or gs.status == 'completed':
        return None
        
    if not winner_id and winner_color:
        if winner_color in ['w', 'red', 'X']:
            winner_id = gs.player1_id
        else:
            winner_id = gs.player2_id
            
    gs.status = 'completed'
    gs.winner_id = winner_id
    
    # Calculate Elo
    p1_old, p1_new, p2_old, p2_new = calculate_elo(winner_id, gs.player1_id, gs.player2_id, is_draw)
    
    # Record history
    history = GameHistory(
        game_id=gs.game_id,
        player1_id=gs.player1_id,
        player2_id=gs.player2_id,
        winner_id=winner_id,
        player1_elo_before=p1_old,
        player1_elo_after=p1_new,
        player2_elo_before=p2_old,
        player2_elo_after=p2_new
    )
    db.session.add(history)
    
    # Update streaks and stats
    for pid in [gs.player1_id, gs.player2_id]:
        streak = Streak.query.filter_by(user_id=pid).first()
        if not streak:
            streak = Streak(user_id=pid)
            db.session.add(streak)
        
        streak.games_played += 1
        if pid == winner_id:
            streak.games_won += 1
            streak.points += 50
        elif is_draw:
            streak.points += 20
        else:
            streak.points += 5
            
    db.session.commit()
    
    return {
        'winner_id': winner_id,
        'is_draw': is_draw,
        'p1': {'id': gs.player1_id, 'old_elo': p1_old, 'new_elo': p1_new},
        'p2': {'id': gs.player2_id, 'old_elo': p2_old, 'new_elo': p2_new}
    }

# ==================== SOCKET.IO EVENTS ====================
@socketio.on('game_over')
def on_game_over(data):
    session_id = data.get('session_id')
    if session_id is not None:
        try:
            session_id = int(session_id)
        except (ValueError, TypeError):
            pass
            
    winner_id = data.get('winner_id') 
    winner_color = data.get('winner_color')
    is_draw = data.get('is_draw', False)
    
    stats = handle_game_over(session_id, winner_id, winner_color, is_draw)
    
    if stats:
        # Notify room
        room = f"game_{session_id}"
        emit('game_over_stats', stats, room=room)

@socketio.on('join')
def on_join(data):
    from models import GameSession
    game_id = data.get('game_id')
    if game_id is not None:
        try:
            game_id = int(game_id)
        except (ValueError, TypeError):
            pass
            
    room = f"game_{game_id}"
    join_room(room)
    print(f"DEBUG: User {session.get('username')} (ID: {session.get('user_id')}) joined room {room}")
    
    # Send initial status
    gs = GameSession.query.get(game_id)
    if gs:
        emit('init_game', {
            'status': gs.status, 
            'game_state': gs.game_state,
            'p1_ready': gs.player1_ready,
            'p2_ready': gs.player2_ready,
            'p1_id': gs.player1_id,
            'p2_id': gs.player2_id
        })
        print(f"DEBUG: Sent init_game with status {gs.status} and state to {session.get('username')}")

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
    
    if session_id is not None:
        try:
            session_id = int(session_id)
        except (ValueError, TypeError):
            pass
            
    if user_id is not None:
        user_id = int(user_id)
        
    print(f"DEBUG: Ready event received. Session: {session_id}, User: {user_id} (Type: {type(user_id)})")
    
    gs = GameSession.query.get(session_id)
    if not gs: 
        print(f"DEBUG: Session {session_id} not found in DB")
        return

    print(f"DEBUG: Session found. P1: {gs.player1_id} (Ready: {gs.player1_ready}), P2: {gs.player2_id} (Ready: {gs.player2_ready})")

    if gs.player1_id == user_id:
        gs.player1_ready = True
        print(f"DEBUG: Player 1 ({user_id}) is now ready")
    elif gs.player2_id == user_id:
        gs.player2_ready = True
        print(f"DEBUG: Player 2 ({user_id}) is now ready")
    else:
        print(f"DEBUG: User {user_id} is not part of this session")
    
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
    from models import GameSession, User, db
    session_id = data.get('session_id')
    if session_id is not None:
        try:
            session_id = int(session_id)
        except (ValueError, TypeError):
            pass
            
    user_id = session.get('user_id')
    if user_id is not None:
        user_id = int(user_id)
    
    gs = GameSession.query.get(session_id)
    if gs and gs.status != 'completed':
        # If the game hasn't started yet, just end it without Elo changes
        if gs.status == 'waiting':
            gs.status = 'abandoned'
            db.session.commit()
            room = f"game_{session_id}"
            socketio.emit('opponent_forfeit', {'winner_name': session.get('full_name')}, room=room, include_self=False)
            return

        # The person who triggered this event is the forfeiter
        forfeiter_name = session.get('full_name')
        
        # Determine winner (the other player)
        winner_id = gs.player2_id if user_id == gs.player1_id else gs.player1_id
        
        # End game and update Elo
        stats = handle_game_over(session_id, winner_id=winner_id)
        
        if stats:
            room = f"game_{session_id}"
            # Notify opponent that this user forfeited
            socketio.emit('opponent_forfeit', {'winner_name': forfeiter_name}, room=room, include_self=False)
            
            # Send Elo stats to everyone in the room
            socketio.emit('game_over_stats', stats, room=room)

@socketio.on('move')
def on_move(data):
    from models import GameSession, db
    game_id = data.get('game_id')
    room = f"game_{game_id}"
    
    # Save state to DB
    gs = GameSession.query.get(game_id)
    if gs:
        # Chess uses 'fen', TicTacToe uses 'board', Xiangqi uses move list?
        # Let's save whatever 'state' is provided or infer from data
        new_state = data.get('fen') or data.get('board') or data.get('game_state')
        if new_state:
            gs.game_state = str(new_state)
            db.session.commit()
            print(f"DEBUG: Saved game state for session {game_id}")

    # Broadcast the move to the other player in the room
    emit('move', data, room=room, include_self=False)
    print(f"Move received in room {room}: {data.get('move')}")

@socketio.on('game_chat')
def on_game_chat(data):
    from models import Message, User, db
    
    sender_id = session.get('user_id')
    recipient_id = data.get('recipient_id')
    content = data.get('content')
    game_id = data.get('game_id')
    
    if not sender_id or not recipient_id or not content:
        return

    # Check for unkind words
    is_flagged = False
    unkind_words = app.config.get('UNKIND_WORDS', [])
    for word in unkind_words:
        if word.lower() in content.lower():
            is_flagged = True
            break

    # Save message to database
    new_msg = Message(
        sender_id=sender_id,
        recipient_id=recipient_id,
        content=content,
        is_flagged=is_flagged
    )
    db.session.add(new_msg)
    db.session.commit()

    # Broadcast to the game room
    room = f"game_{game_id}"
    emit('new_game_message', {
        'id': new_msg.id,
        'sender_id': sender_id,
        'content': content,
        'is_flagged': is_flagged,
        'created_at': (new_msg.created_at + timedelta(hours=8)).strftime('%I:%M %p'),
        'is_me': False # Frontend will check this
    }, room=room)

@socketio.on('join_community')
def on_join_community(data):
    room = f"community_{data['community_id']}"
    join_room(room)
    print(f"DEBUG: User {session.get('username')} joined community room {room}")

@socketio.on('leave_community')
def on_leave_community(data):
    room = f"community_{data['community_id']}"
    leave_room(room)

@socketio.on('community_message')
def on_community_message(data):
    from models import CommunityPost, User, db
    from datetime import datetime
    
    user_id = session.get('user_id')
    if not user_id: return

    # Save to DB
    new_post = CommunityPost(
        community_id=data['community_id'],
        user_id=user_id,
        content=data.get('content', ''),
        photo_url=data.get('photo_url')
    )
    db.session.add(new_post)
    db.session.commit()
    
    user = User.query.get(user_id)
    
    avatar = user.profile_picture
    if avatar and not avatar.startswith('images/'):
        avatar = f'images/{avatar}'
    
    # Broadcast to room
    room = f"community_{data['community_id']}"
    emit('new_community_post', {
        'id': new_post.id,
        'user_id': user.id,
        'username': user.full_name,
        'avatar': avatar,
        'content': new_post.content,
        'photo_url': new_post.photo_url,
        'created_at': (new_post.created_at + timedelta(hours=8)).strftime('%I:%M %p'),
        'is_me': False 
    }, room=room)

@socketio.on('connect')
def on_connect():
    # Join a private room for the user to receive challenges
    if 'user_id' in session:
        join_room(f"user_{session['user_id']}")

@socketio.on('disconnect')
def on_disconnect():
    print(f"User {session.get('username')} disconnected")


# ==================== NOTIFICATION EVENT LISTENER ====================
from sqlalchemy import event
from models import Notification

def push_notification(mapper, connection, target):
    """
    SQLAlchemy event listener to push notifications via Socket.IO
    whenever a new Notification record is inserted.
    """
    try:
        # target is the Notification instance
        room = f"user_{target.user_id}"
        
        # Prepare data matching the API response format
        notif_data = {
            'id': target.id,
            'title': target.title,
            'message': target.message,
            'type': target.type,
            'link': target.link,
            'timeAgo': 'Just now',
            'created_at': target.created_at.isoformat()
        }
        
        socketio.emit('new_notification', notif_data, room=room)
        # print(f"DEBUG: Pushed notification {target.id} to {room}")
    except Exception as e:
        print(f"ERROR: Failed to push notification: {e}")

# Register the event listener
event.listen(Notification, 'after_insert', push_notification)


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

    # Auto-patch: Add missing photo_url column if it doesn't exist
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE community_posts ADD COLUMN photo_url VARCHAR(255)"))
            conn.commit()
            print("Database patched: Added photo_url to community_posts")
    except Exception:
        pass # Column likely already exists or another error occurred

    # Auto-patch: Add missing photo_url column to communities if it doesn't exist
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE communities ADD COLUMN photo_url VARCHAR(255)"))
            conn.commit()
            print("Database patched: Added photo_url to communities")
    except Exception:
        pass

    # Auto-patch: Add missing last_viewed_at column to community_members if it doesn't exist
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE community_members ADD COLUMN last_viewed_at DATETIME"))
            conn.commit()
            print("Database patched: Added last_viewed_at to community_members")
    except Exception:
        pass

    # Auto-patch: Ensure chat_reports table exists
    try:
        with db.engine.connect() as conn:
            conn.execute(text("SELECT count(*) FROM chat_reports"))
    except Exception:
        print("Creating chat_reports table...")
        db.create_all()

    # Auto-patch: Ensure chat_reports table exists (Double check)
    try:
        with db.engine.connect() as conn:
            conn.execute(text("SELECT count(*) FROM chat_reports"))
    except Exception:
        print("Creating chat_reports table...")
        db.create_all()

    # Auto-patch: Add missing status column to chat_reports if it doesn't exist
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE chat_reports ADD COLUMN status VARCHAR(20) DEFAULT 'pending'"))
            conn.commit()
            print("Database patched: Added status to chat_reports")
    except Exception:
        pass

    # Auto-patch: Add missing admin_notes column to chat_reports if it doesn't exist
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE chat_reports ADD COLUMN admin_notes TEXT"))
            conn.commit()
            print("Database patched: Added admin_notes to chat_reports")
    except Exception:
        pass

    # Auto-patch: Add elo to users
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN elo INTEGER DEFAULT 1200"))
            conn.commit()
            print("Database patched: Added elo to users")
    except Exception:
        pass

    # Auto-patch: Add winner_id and game_state to game_sessions
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE game_sessions ADD COLUMN winner_id INTEGER REFERENCES users(id)"))
            conn.execute(text("ALTER TABLE game_sessions ADD COLUMN game_state TEXT"))
            conn.commit()
            print("Database patched: Added winner_id and game_state to game_sessions")
    except Exception:
        pass

    # Auto-patch: Ensure game_history table exists
    try:
        with db.engine.connect() as conn:
            conn.execute(text("SELECT count(*) FROM game_history"))
    except Exception:
        print("Creating game_history table...")
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
    user_streak = 0
    if 'user_id' in session:
        from models import Streak
        streak = Streak.query.filter_by(user_id=session['user_id']).first()
        if streak:
            user_streak = streak.current_streak
            
    return dict(session=session, user_streak=user_streak)


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


@app.template_filter('fix_pfp')
def fix_pfp_filter(path):
    """
    Ensure profile picture path has correct prefix.
    Usage: {{ user.profile_picture|fix_pfp }}
    """
    if not path:
        return 'images/default-avatar.png'
    if path.startswith('images/'):
        return path
    if path.startswith('http'):
        return path
    return f'images/{path}'


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

@app.route('/api/notifications/mark-read', methods=['POST'])
def mark_all_notifications_read():
    if 'user_id' not in session:
        return {'success': False}, 403
    
    from models import Notification, db
    user_id = session['user_id']
    
    # Update all unread notifications for this user
    Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
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
    Run the Flask development server.

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
