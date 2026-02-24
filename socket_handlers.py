"""
socket_handlers.py — Socket.IO event handlers and notification push listener.

Extracted from app.py so that:
  - Circular imports between app → blueprints → app are broken.
  - app.py stays thin; all real-time logic lives here.

Imported once by app.py (`import socket_handlers`) so that the
@socketio.on(...) decorators are evaluated and the handlers registered.
"""

from flask import session, current_app
from flask_socketio import emit, join_room, leave_room
from sqlalchemy import event
from datetime import timedelta

from extensions import db, socketio
from utils import escape_html, sanitize_for_display, check_unkind_words
from services.elo import handle_game_over


# ==================== GAME EVENTS ====================

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


@socketio.on('challenge')
def on_challenge(data):
    buddy_room = f"user_{data['buddy_id']}"
    socketio.emit('game_challenge', {
        'challenger_name': session.get('full_name'),
        'challenger_id': session.get('user_id'),
        'game_id': data['game_id'],
        'game_title': data['game_title']
    }, room=buddy_room)


@socketio.on('ready')
def on_ready(data):
    from models import GameSession
    session_id = data.get('session_id')
    user_id = session.get('user_id')

    if session_id is not None:
        try:
            session_id = int(session_id)
        except (ValueError, TypeError):
            pass

    if user_id is not None:
        user_id = int(user_id)

    gs = GameSession.query.get(session_id)
    if not gs:
        return

    if gs.player1_id == user_id:
        gs.player1_ready = True
    elif gs.player2_id == user_id:
        gs.player2_ready = True

    db.session.commit()

    room = f"game_{session_id}"
    if gs.player1_ready and gs.player2_ready:
        gs.status = 'active'
        db.session.commit()
        socketio.emit('game_start', {'session_id': session_id}, room=room)
    else:
        socketio.emit('player_ready', {'user_id': user_id}, room=room)


@socketio.on('forfeit')
def on_forfeit(data):
    from models import GameSession
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
        if gs.status == 'waiting':
            gs.status = 'abandoned'
            db.session.commit()
            room = f"game_{session_id}"
            socketio.emit('opponent_forfeit', {'winner_name': session.get('full_name')}, room=room, include_self=False)
            return

        forfeiter_name = session.get('full_name')
        winner_id = gs.player2_id if user_id == gs.player1_id else gs.player1_id
        stats = handle_game_over(session_id, winner_id=winner_id)

        if stats:
            room = f"game_{session_id}"
            socketio.emit('opponent_forfeit', {'winner_name': forfeiter_name}, room=room, include_self=False)
            socketio.emit('game_over_stats', stats, room=room)


@socketio.on('move')
def on_move(data):
    from models import GameSession
    game_id = data.get('game_id')
    room = f"game_{game_id}"

    gs = GameSession.query.get(game_id)
    if gs:
        new_state = data.get('fen') or data.get('board') or data.get('game_state')
        if new_state:
            gs.game_state = str(new_state)
            db.session.commit()

    emit('move', data, room=room, include_self=False)


# ==================== CHAT EVENTS ====================

@socketio.on('game_chat')
def on_game_chat(data):
    from models import Message, User

    sender_id = session.get('user_id')
    recipient_id = data.get('recipient_id')
    content = data.get('content')
    game_id = data.get('game_id')

    if not sender_id or not recipient_id or not content:
        return

    is_flagged = check_unkind_words(content, current_app.config.get('UNKIND_WORDS', []))
    safe_content = sanitize_for_display(content)

    new_msg = Message(
        sender_id=sender_id,
        recipient_id=recipient_id,
        content=safe_content,
        is_flagged=is_flagged
    )
    db.session.add(new_msg)
    db.session.commit()

    room = f"game_{game_id}"
    emit('new_game_message', {
        'id': new_msg.id,
        'sender_id': sender_id,
        'content': safe_content,
        'is_flagged': is_flagged,
        'created_at': (new_msg.created_at + timedelta(hours=8)).strftime('%I:%M %p'),
        'is_me': False
    }, room=room)


# ==================== COMMUNITY EVENTS ====================

@socketio.on('join_community')
def on_join_community(data):
    room = f"community_{data['community_id']}"
    join_room(room)


@socketio.on('leave_community')
def on_leave_community(data):
    room = f"community_{data['community_id']}"
    leave_room(room)


@socketio.on('community_message')
def on_community_message(data):
    from models import CommunityPost, User
    from datetime import datetime

    user_id = session.get('user_id')
    if not user_id:
        return

    original_content = data.get('content', '')
    is_flagged = check_unkind_words(original_content, current_app.config.get('UNKIND_WORDS', []))

    if is_flagged:
        emit('message_flagged', {
            'message': 'Your message contains words that may be considered unkind. It has been flagged for review.',
            'original_content': escape_html(original_content)
        })

    safe_content = sanitize_for_display(original_content)
    reply_to_id = data.get('reply_to_id') or None

    new_post = CommunityPost(
        community_id=data['community_id'],
        user_id=user_id,
        content=safe_content,
        photo_url=data.get('photo_url'),
        reply_to_id=reply_to_id
    )
    db.session.add(new_post)
    db.session.commit()

    user = User.query.get(user_id)

    avatar = user.profile_picture
    if avatar and not avatar.startswith('images/'):
        avatar = f'images/{avatar}'

    # Build reply preview if this message is a reply
    reply_preview = None
    if reply_to_id:
        parent = CommunityPost.query.get(reply_to_id)
        if parent:
            reply_preview = {
                'author': escape_html(parent.user.full_name),
                'content': escape_html((parent.content or '')[:80])
            }

    room = f"community_{data['community_id']}"
    emit('new_community_post', {
        'id': new_post.id,
        'user_id': user.id,
        'username': escape_html(user.full_name),
        'avatar': avatar,
        'content': new_post.content,
        'photo_url': new_post.photo_url,
        'created_at': (new_post.created_at + timedelta(hours=8)).strftime('%I:%M %p'),
        'is_flagged': is_flagged,
        'reply_preview': reply_preview
    }, room=room)


@socketio.on('edit_community_message')
def on_edit_community_message(data):
    from models import CommunityPost
    from datetime import datetime

    user_id = session.get('user_id')
    if not user_id:
        return

    post_id = data.get('post_id')
    new_content = (data.get('content') or '').strip()

    if not post_id or not new_content:
        return

    post = CommunityPost.query.get(post_id)
    if not post or post.user_id != user_id:
        return

    if check_unkind_words(new_content, current_app.config.get('UNKIND_WORDS', [])):
        emit('message_flagged', {
            'message': 'Your edited message contains inappropriate language and cannot be saved.'
        })
        return

    post.content = sanitize_for_display(new_content)
    post.edited_at = datetime.utcnow()
    db.session.commit()

    room = f"community_{post.community_id}"
    emit('community_post_edited', {
        'post_id': post.id,
        'content': post.content
    }, room=room)


# ==================== VIDEO CALL / WEBRTC SIGNALING ====================

@socketio.on('call_user')
def on_call_user(data):
    """Caller initiates a call to their buddy."""
    caller_id = session.get('user_id')
    target_id = data.get('target_id')
    if not caller_id or not target_id:
        return
    target_room = f"user_{target_id}"
    emit('incoming_call', {
        'caller_id': caller_id,
        'caller_name': session.get('full_name', 'Your buddy'),
        'video': data.get('video', True)
    }, room=target_room)


@socketio.on('call_accepted')
def on_call_accepted(data):
    """Callee accepts the call — notify caller to start WebRTC offer."""
    callee_id = session.get('user_id')
    target_id = data.get('target_id')
    if not callee_id or not target_id:
        return
    target_room = f"user_{target_id}"
    emit('call_accepted', {'callee_id': callee_id}, room=target_room)


@socketio.on('call_rejected')
def on_call_rejected(data):
    """Callee rejects the call."""
    target_id = data.get('target_id')
    if not target_id:
        return
    target_room = f"user_{target_id}"
    emit('call_rejected', {}, room=target_room)


@socketio.on('webrtc_offer')
def on_webrtc_offer(data):
    """Relay WebRTC offer from caller to callee."""
    caller_id = session.get('user_id')
    target_id = data.get('target_id')
    if not target_id:
        return
    target_room = f"user_{target_id}"
    emit('webrtc_offer', {
        'offer': data.get('offer'),
        'caller_id': caller_id
    }, room=target_room)


@socketio.on('webrtc_answer')
def on_webrtc_answer(data):
    """Relay WebRTC answer from callee to caller."""
    target_id = data.get('target_id')
    if not target_id:
        return
    target_room = f"user_{target_id}"
    emit('webrtc_answer', {
        'answer': data.get('answer')
    }, room=target_room)


@socketio.on('webrtc_candidate')
def on_webrtc_candidate(data):
    """Relay ICE candidate between peers."""
    target_id = data.get('target_id')
    if not target_id:
        return
    target_room = f"user_{target_id}"
    emit('webrtc_candidate', {
        'candidate': data.get('candidate')
    }, room=target_room)


@socketio.on('end_call')
def on_end_call(data):
    """Notify the other party that the call has ended."""
    target_id = data.get('target_id')
    if not target_id:
        return
    target_room = f"user_{target_id}"
    emit('call_ended', {}, room=target_room)


@socketio.on('screen_share_toggle')
def on_screen_share_toggle(data):
    """Notify the other party that screen sharing started/stopped."""
    target_id = data.get('target_id')
    if not target_id:
        return
    target_room = f"user_{target_id}"
    emit('screen_share_toggled', {
        'sharing': data.get('sharing', False)
    }, room=target_room)


# ==================== CONNECTION EVENTS ====================

@socketio.on('connect')
def on_connect():
    if 'user_id' in session:
        join_room(f"user_{session['user_id']}")


@socketio.on('disconnect')
def on_disconnect():
    pass


# ==================== NOTIFICATION PUSH LISTENER ====================

def push_notification(mapper, connection, target):
    """
    SQLAlchemy event listener: push a Socket.IO notification whenever
    a new Notification row is inserted.
    """
    try:
        room = f"user_{target.user_id}"
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
    except Exception as e:
        print(f"ERROR: Failed to push notification: {e}")


# Register listener at import time (deferred model import to avoid circular imports)
def _register_notification_listener():
    from models import Notification
    event.listen(Notification, 'after_insert', push_notification)

_register_notification_listener()
