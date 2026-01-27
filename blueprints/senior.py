"""
File: senior.py
Purpose: Senior user routes blueprint
Author: to be assigned
Date: December 2025
Features: Senior Dashboard, Story Sharing, Messages, Events, Communities, Games, Profile
Description: Handles all routes for senior users including story creation,
             messaging with youth buddies, event registration, and accessibility features
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from models import db, User, Story, Message, Event, Community, Pair, EventParticipant, CommunityMember, Game, GameSession, CommunityPost, ChatReport
from forms import StoryForm, MessageForm
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.utils import secure_filename
from utils import filter_text
import os

# Create senior blueprint
senior_bp = Blueprint('senior', __name__)


# ==================== AUTHENTICATION DECORATOR ====================
def login_required(f):
    """
    Decorator to require login for routes.
    Ensures user is logged in and is a senior.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('auth.login', role='senior'))
        if session.get('role') != 'senior':
            flash('Access denied. Senior account required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# ==================== DASHBOARD ====================
@senior_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Senior dashboard - main page after login.
    Shows stats, recent activity, and quick actions.
    """
    user = User.query.get(session['user_id'])

    # Get user statistics
    stories_count = Story.query.filter_by(user_id=user.id).count()

    # Get buddy information (paired youth)
    pair = Pair.query.filter_by(senior_id=user.id, status='active').first()
    buddy = User.query.get(pair.youth_id) if pair else None

    # Get recent stories
    recent_stories = Story.query.filter_by(user_id=user.id)\
        .order_by(Story.created_at.desc()).limit(5).all()

    # Get upcoming events
    upcoming_events = Event.query.filter(Event.date >= datetime.utcnow())\
        .order_by(Event.date).limit(3).all()

    return render_template('senior/dashboard.html',
                         user=user,
                         stories_count=stories_count,
                         buddy=buddy,
                         recent_stories=recent_stories,
                         upcoming_events=upcoming_events)


# ==================== STORIES ====================
@senior_bp.route('/story_feed')
@login_required
def story_feed():
    """Instagram-style story feed with all stories."""
    # Get filters from query parameters
    category_filter = request.args.get('category', 'all')
    role_filter = request.args.get('role', 'all')

    # Query stories with user join for role filtering
    query = Story.query.join(User)

    if category_filter != 'all':
        query = query.filter(Story.category == category_filter)
    
    if role_filter != 'all':
        query = query.filter(User.role == role_filter)

    stories = query.order_by(Story.created_at.desc()).all()

    return render_template('senior/story_feed.html',
                         stories=stories,
                         current_category=category_filter,
                         current_role=role_filter)


@senior_bp.route('/story/<int:story_id>')
@login_required
def story_detail(story_id):
    """Full story view with reactions and comments."""
    story = Story.query.get_or_404(story_id)

    return render_template('senior/story_detail.html', story=story)


@senior_bp.route('/stories')
@login_required
def stories():
    """Display all stories created by this senior."""
    user_id = session['user_id']
    stories = Story.query.filter_by(user_id=user_id)\
        .order_by(Story.created_at.desc()).all()

    return render_template('senior/stories.html', stories=stories)


@senior_bp.route('/create_story', methods=['GET', 'POST'])
@login_required
def create_story():
    """Create a new story (step-by-step wizard)."""
    form = StoryForm()
    
    if form.validate_on_submit():
        # Create new story
        new_story = Story(
            user_id=session['user_id'],
            title=form.title.data,
            content=form.content.data,
            category=form.category.data
        )

        # Handle photo upload
        if form.photo.data:
            file = form.photo.data
            if file:
                filename = secure_filename(file.filename)
                # Check extension
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                if ext in current_app.config['ALLOWED_EXTENSIONS']:
                    # Ensure upload directory exists
                    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                    
                    # Save file with unique name
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S_')
                    unique_filename = timestamp + filename
                    
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
                    new_story.photo_url = unique_filename

        db.session.add(new_story)
        db.session.commit()

        flash('Story created successfully!', 'success')
        return redirect(url_for('senior.stories'))
    
    # Flash errors if any
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'danger')

    return render_template('senior/create_story.html', form=form)


@senior_bp.route('/story/<int:story_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_story(story_id):
    """Edit an existing story."""
    story = Story.query.get_or_404(story_id)
    
    # Check ownership
    if story.user_id != session['user_id']:
        flash('You can only edit your own stories.', 'danger')
        return redirect(url_for('senior.stories'))
        
    form = StoryForm(obj=story)
    
    if form.validate_on_submit():
        story.title = form.title.data
        story.content = form.content.data
        story.category = form.category.data
        
        # Handle photo upload
        if form.photo.data:
            file = form.photo.data
            if file:
                filename = secure_filename(file.filename)
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                if ext in current_app.config['ALLOWED_EXTENSIONS']:
                    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S_')
                    unique_filename = timestamp + filename
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
                    
                    # Delete old photo if exists
                    if story.photo_url:
                        old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], story.photo_url)
                        if os.path.exists(old_path):
                            try:
                                os.remove(old_path)
                            except OSError:
                                pass
                                
                    story.photo_url = unique_filename
        
        db.session.commit()
        flash('Story updated successfully!', 'success')
        return redirect(url_for('senior.stories'))

    return render_template('senior/edit_story.html', form=form, story=story)


@senior_bp.route('/stories/<int:story_id>/delete', methods=['DELETE'])
@login_required
def delete_story(story_id):
    """Delete a story."""
    story = Story.query.get_or_404(story_id)
    
    if story.user_id != session['user_id']:
        return {'success': False, 'message': 'Unauthorized'}, 403
        
    try:
        # Delete photo file if exists
        if story.photo_url:
            path = os.path.join(current_app.config['UPLOAD_FOLDER'], story.photo_url)
            if os.path.exists(path):
                os.remove(path)
                
        db.session.delete(story)
        db.session.commit()
        return {'success': True}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': str(e)}, 500


# ==================== MESSAGES ====================
@senior_bp.route('/messages', methods=['GET', 'POST'])
@login_required
def messages():
    """Display messaging interface with youth buddy."""
    user_id = session['user_id']

    # Get paired youth buddy
    pair = Pair.query.filter_by(senior_id=user_id, status='active').first()
    if not pair:
        flash('You are not currently paired with a youth volunteer', 'info')
        return render_template('senior/messages.html', buddy=None, messages=[])

    buddy = User.query.get(pair.youth_id)
    
    form = MessageForm()

    if form.validate_on_submit():
        original_content = form.message.data
        
        # Check for unkind words (Flagging based on original)
        is_flagged = False
        unkind_words = current_app.config.get('UNKIND_WORDS', [])
        for word in unkind_words:
            if word.lower() in original_content.lower():
                is_flagged = True
                break
        
        # Filter content
        content = filter_text(original_content)
        
        # Create new message object
        new_message = Message(
            sender_id=user_id,
            recipient_id=buddy.id,
            content=content,
            is_flagged=is_flagged
        )
        
        db.session.add(new_message)
        
        # Update pair last interaction timestamp
        pair.last_interaction = datetime.utcnow()
        
        db.session.commit()
        
        if is_flagged:
            flash('Your message was sent but flagged for review due to potentially unkind language.', 'warning')
        
        return redirect(url_for('senior.messages'))

    # Get messages between senior and youth
    messages = Message.query.filter(
        ((Message.sender_id == user_id) & (Message.recipient_id == buddy.id)) |
        ((Message.sender_id == buddy.id) & (Message.recipient_id == user_id))
    ).order_by(Message.created_at).all()

    return render_template('senior/messages.html', buddy=buddy, messages=messages, form=form)


@senior_bp.route('/api/messages')
@login_required
def get_messages_json():
    """
    API endpoint to fetch messages in JSON format.
    Used by the frontend polling script (chat.js) to update the chat window
    without reloading the entire page.
    """
    user_id = session['user_id']
    
    # Check if user has a buddy
    pair = Pair.query.filter_by(senior_id=user_id, status='active').first()
    if not pair:
        return {'messages': []}

    buddy_id = pair.youth_id

    # Query all messages between the user and their buddy
    # Ordered by creation time to show conversation history
    messages = Message.query.filter(
        ((Message.sender_id == user_id) & (Message.recipient_id == buddy_id)) |
        ((Message.sender_id == buddy_id) & (Message.recipient_id == user_id))
    ).order_by(Message.created_at).all()

    # Convert message objects to a list of dictionaries (JSON-serializable)
    messages_data = [{
        'id': msg.id,
        'content': msg.content,
        'sender_id': msg.sender_id,
        'is_me': msg.sender_id == user_id,
        'created_at': (msg.created_at + timedelta(hours=8)).strftime('%I:%M %p'), # Format: 02:30 PM
        'is_flagged': msg.is_flagged,
        'translated_content': msg.translated_content if msg.original_language != 'en' else None
    } for msg in messages]

    return {'messages': messages_data}


@senior_bp.route('/api/messages/<int:message_id>/report', methods=['POST'])
@login_required
def report_message(message_id):
    """API to report a message."""
    data = request.get_json()
    reason = data.get('reason')
    description = data.get('description')
    
    msg = Message.query.get_or_404(message_id)
    
    report = ChatReport(
        message_id=msg.id,
        reported_by=session['user_id'],
        reported_user_id=msg.sender_id,
        reason=reason,
        description=description,
        status='pending'
    )
    db.session.add(report)
    db.session.commit()
    
    return {'success': True}, 200


@senior_bp.route('/api/community_posts/<int:post_id>/report', methods=['POST'])
@login_required
def report_community_post(post_id):
    """API to report a community post."""
    data = request.get_json()
    reason = data.get('reason')
    description = data.get('description')
    
    post = CommunityPost.query.get_or_404(post_id)
    
    report = ChatReport(
        community_post_id=post.id,
        reported_by=session['user_id'],
        reported_user_id=post.user_id,
        reason=reason,
        description=description,
        status='pending'
    )
    db.session.add(report)
    db.session.commit()
    
    return {'success': True}, 200


# ==================== EVENTS ====================
@senior_bp.route('/events')
@login_required
def events():
    """Display all available events."""
    user_id = session['user_id']
    
    # Get all upcoming events
    upcoming_events = Event.query.filter(Event.date >= datetime.utcnow()).order_by(Event.date).all()
    
    # Get IDs of events user is registered for
    registered_event_ids = [p.event_id for p in EventParticipant.query.filter_by(user_id=user_id).all()]
    
    # Process events for display
    events_data = []
    for event in upcoming_events:
        is_registered = event.id in registered_event_ids
        
        event_dict = {
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'event_type': event.event_type,
            'location': event.location,
            'date': event.date,
            'capacity': event.capacity,
            'participants_count': event.participants.count(),
            'is_registered': is_registered,
            'is_full': event.capacity is not None and event.participants.count() >= event.capacity
        }
        events_data.append(event_dict)

    return render_template('senior/events.html', events=events_data)


@senior_bp.route('/events/<int:event_id>/register', methods=['POST'])
@login_required
def register_event(event_id):
    """Toggle event registration for the user."""
    
    event = Event.query.get_or_404(event_id)
    user_id = session['user_id']
    
    registration = EventParticipant.query.filter_by(
        event_id=event_id,
        user_id=user_id
    ).first()
    
    status = ''
    
    if registration:
        # Unregister
        db.session.delete(registration)
        status = 'unregistered'
    else:
        # Check capacity
        if event.capacity is not None and event.participants.count() >= event.capacity:
            return {'success': False, 'message': 'Event is full'}, 400
        
        # Register
        new_registration = EventParticipant(event_id=event_id, user_id=user_id)
        db.session.add(new_registration)
        status = 'registered'
        
    db.session.commit()
    
    return {
        'success': True,
        'status': status,
        'participant_count': event.participants.count()
    }


# ==================== COMMUNITIES ====================
@senior_bp.route('/communities')
@login_required
def communities():
    """Display all communities with search and unread counts."""
    search_query = request.args.get('q', '')
    user_id = session['user_id']
    
    query = Community.query
    if search_query:
        query = query.filter(Community.name.ilike(f'%{search_query}%') | 
                             Community.description.ilike(f'%{search_query}%'))
    
    all_communities = query.all()
    
    my_communities = []
    other_communities = []
    
    for comm in all_communities:
        member = CommunityMember.query.filter_by(community_id=comm.id, user_id=user_id).first()
        comm.is_joined = member is not None
        comm.post_count = comm.posts.count()
        
        if comm.is_joined:
            # Calculate unread posts
            last_viewed = member.last_viewed_at or member.joined_at
            unread = CommunityPost.query.filter(
                CommunityPost.community_id == comm.id,
                CommunityPost.created_at > last_viewed
            ).count()
            comm.unread_count = unread
            my_communities.append(comm)
        else:
            other_communities.append(comm)

    return render_template('senior/communities.html', 
                         my_communities=my_communities, 
                         other_communities=other_communities,
                         search_query=search_query)


@senior_bp.route('/communities/<int:community_id>')
@login_required
def view_community(community_id):
    """View community chat and details."""
    community = Community.query.get_or_404(community_id)
    user_id = session['user_id']
    
    # Check membership
    member = CommunityMember.query.filter_by(
        community_id=community_id, 
        user_id=user_id
    ).first()
    
    if not member:
        flash('You must join this community to view the chat.', 'warning')
        return redirect(url_for('senior.communities'))
        
    # Update last_viewed_at
    member.last_viewed_at = datetime.utcnow()
    db.session.commit()
        
    # Get recent posts for the chat history
    posts = CommunityPost.query.filter_by(community_id=community_id)\
        .order_by(CommunityPost.created_at.asc()).all()
        
    members = community.members.all()
    return render_template('senior/community_chat.html', community=community, posts=posts, user_id=user_id, members=members)


@senior_bp.route('/communities/<int:community_id>/upload_photo', methods=['POST'])
@login_required
def upload_community_photo(community_id):
    """Handle photo upload for community chat."""
    if 'photo' not in request.files:
        return {'error': 'No file part'}, 400
    
    file = request.files['photo']
    if file.filename == '':
        return {'error': 'No selected file'}, 400
        
    if file and file.filename:
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S_')
        unique_filename = f"chat_{community_id}_{timestamp}{filename}"
        
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
        
        return {'url': f"images/uploads/{unique_filename}"}
    
    return {'error': 'Upload failed'}, 500


@senior_bp.route('/communities/<int:community_id>/join', methods=['POST'])
@login_required
def join_community(community_id):
    """Toggle community membership."""
    
    community = Community.query.get_or_404(community_id)
    user_id = session['user_id']
    
    # Check existing membership
    membership = CommunityMember.query.filter_by(
        community_id=community_id,
        user_id=user_id
    ).first()
    
    status = 'joined'
    
    if membership:
        # Leave community
        db.session.delete(membership)
        community.member_count = max(0, community.member_count - 1)
        status = 'left'
    else:
        # Join community
        new_member = CommunityMember(
            community_id=community_id,
            user_id=user_id
        )
        db.session.add(new_member)
        community.member_count += 1
        status = 'joined'
        
    db.session.commit()
    
    return {
        'success': True,
        'status': status,
        'member_count': community.member_count
    }


# ==================== GAMES ====================
@senior_bp.route('/games')
@login_required
def games():
    """Display game selection lobby."""
    user_id = session['user_id']
    
    # Get paired youth buddy for online status
    pair = Pair.query.filter_by(senior_id=user_id, status='active').first()
    buddy = User.query.get(pair.youth_id) if pair else None

    # Get active game session
    active_session = GameSession.query.filter(
        ((GameSession.player1_id == user_id) | (GameSession.player2_id == user_id)),
        GameSession.status == 'active'
    ).first()

    # Get streak info
    from models import Streak
    streak_info = Streak.query.filter_by(user_id=user_id).first()
    
    user = User.query.get(user_id)

    # Stats
    stats = {
        'played': streak_info.games_played if streak_info else 0,
        'won': streak_info.games_won if streak_info else 0,
        'points': streak_info.points if streak_info else 0,
        'streak': streak_info.current_streak if streak_info else 0,
        'elo': user.elo
    }

    # Get recent game history
    from models import GameHistory
    game_history = GameHistory.query.filter(
        (GameHistory.player1_id == user_id) | (GameHistory.player2_id == user_id)
    ).order_by(GameHistory.completed_at.desc()).limit(5).all()

    # Fetch games from DB
    db_games = Game.query.all()
    games_data = []
    for g in db_games:
        games_data.append({
            'id': g.id,
            'name': g.title,
            'image_class': 'game-image',
            'image_style': g.bg_gradient,
            'icon': g.icon,
            'badge': g.badge_label,
            'badge_class': g.badge_class,
            'badge_icon': g.badge_icon,
            'description': g.description,
            'players': g.players_text,
            'time': g.duration_text,
            'type': g.type_label,
            'type_icon': g.type_icon
        })

    return render_template('senior/games.html', 
                         user=user, 
                         buddy=buddy, 
                         games=games_data, 
                         stats=stats, 
                         active_session=active_session,
                         game_history=game_history)


@senior_bp.route('/games/challenge/<int:game_id>')
@login_required
def challenge_buddy(game_id):
    """Create a new game session and challenge buddy."""
    from app import socketio
    user_id = session['user_id']
    pair = Pair.query.filter_by(senior_id=user_id, status='active').first()
    if not pair:
        flash('You need a buddy to play!', 'warning')
        return redirect(url_for('senior.games'))
    
    # Check for ANY existing waiting or active session for this game between the pair
    # This ensures that if the buddy already created a session, we join it instead of creating a duplicate
    # Also allows rejoining an already active match
    existing_sessions = GameSession.query.filter(
        GameSession.game_id == game_id,
        GameSession.status.in_(['waiting', 'active']),
        ((GameSession.player1_id == user_id) & (GameSession.player2_id == pair.youth_id)) |
        ((GameSession.player1_id == pair.youth_id) & (GameSession.player2_id == user_id))
    ).order_by(GameSession.created_at.desc()).all()

    # Fetch game details first to determine type
    game = Game.query.get_or_404(game_id)

    # Determine target URL based on game type
    target_url = 'senior.chess_game'
    buddy_url = 'youth.chess_game'
    
    if 'Xiangqi' in game.title:
        target_url = 'senior.xiangqi_game'
        buddy_url = 'youth.xiangqi_game'
    elif 'Tic Tac Toe' in game.title or 'Tic-Tac-Toe' in game.title:
        target_url = 'senior.tictactoe_game'
        buddy_url = 'youth.tictactoe_game'

    if existing_sessions:
        # Use the most recent one
        session_to_use = existing_sessions[0]
        
        # Clean up any duplicates to keep DB clean
        for gs in existing_sessions[1:]:
            db.session.delete(gs)
        db.session.commit()
        
        # Check if the game is already active or waiting
        if session_to_use.status == 'active':
            flash('Resuming active match.', 'info')
        else:
            flash('Entering existing game lobby.', 'info')
            
        return redirect(url_for(target_url, session_id=session_to_use.id))

    # No existing session found, create a new one
    new_session = GameSession(
        game_id=game_id,
        player1_id=user_id,
        player2_id=pair.youth_id,
        status='waiting',
        current_turn_id=user_id # Challenger starts
    )
    db.session.add(new_session)
    db.session.commit()
    
    # EMIT CHALLENGE TO BUDDY
    socketio.emit('game_challenge', {
        'challenger_name': session.get('full_name'),
        'game_title': game.title,
        'session_id': new_session.id
    }, room=f"user_{pair.youth_id}")

    # CREATE NOTIFICATION RECORD
    from models import Notification
        
    notif = Notification(
        user_id=pair.youth_id,
        title='Game Challenge!',
        message=f"{session.get('full_name')} has challenged you to a game of {game.title}!",
        type='game',
        link=url_for(buddy_url, session_id=new_session.id)
    )
    db.session.add(notif)
    db.session.commit()
    
    return redirect(url_for(target_url, session_id=new_session.id))


@senior_bp.route('/game/chess')
@login_required
def chess_game():
    """Render the chess game page."""
    user_id = session['user_id']
    session_id = request.args.get('session_id')
    
    if session_id:
        active_session = GameSession.query.get_or_404(session_id)
    else:
        active_session = GameSession.query.filter(
            ((GameSession.player1_id == user_id) | (GameSession.player2_id == user_id)),
            GameSession.status.in_(['active', 'waiting'])
        ).order_by(GameSession.created_at.desc()).first()
    
    if not active_session:
        flash('No active game session found. Please challenge your buddy!', 'warning')
        return redirect(url_for('senior.games'))
        
    color = 'white' if active_session.player1_id == user_id else 'black'
    
    player1 = User.query.get(active_session.player1_id)
    player2 = User.query.get(active_session.player2_id)
    
    return render_template('senior/chess.html', 
                         color=color, 
                         game_session_id=active_session.id, 
                         active_session=active_session,
                         player1=player1,
                         player2=player2)


@senior_bp.route('/game/xiangqi')
@login_required
def xiangqi_game():
    """Render the Chinese chess (Xiangqi) game page."""
    user_id = session['user_id']
    session_id = request.args.get('session_id')
    
    active_session = None
    if session_id:
        active_session = GameSession.query.get_or_404(session_id)
        # Validate user participation
        if active_session.player1_id != user_id and active_session.player2_id != user_id:
            flash('You are not part of this game.', 'danger')
            return redirect(url_for('senior.games'))
            
    # Default to Red (Player 1) if session exists, else Red (Bot mode default)
    color = 'red'
    player1 = None
    player2 = None
    if active_session:
        color = 'red' if active_session.player1_id == user_id else 'black'
        player1 = User.query.get(active_session.player1_id)
        player2 = User.query.get(active_session.player2_id)

    return render_template('senior/xiangqi.html', 
                         active_session=active_session, 
                         game_session_id=active_session.id if active_session else None, 
                         color=color,
                         player1=player1,
                         player2=player2)

@senior_bp.route('/game/tictactoe')
@login_required
def tictactoe_game():
    """Render the Tic Tac Toe game page."""
    user_id = session['user_id']
    session_id = request.args.get('session_id')
    
    active_session = None
    if session_id:
        active_session = GameSession.query.get_or_404(session_id)
        # Validate user participation
        if active_session.player1_id != user_id and active_session.player2_id != user_id:
            flash('You are not part of this game.', 'danger')
            return redirect(url_for('senior.games'))
            
    # Default to X (Player 1) if session exists, else X (single player default)
    color = 'X'
    player1 = None
    player2 = None
    if active_session:
        color = 'X' if active_session.player1_id == user_id else 'O'
        player1 = User.query.get(active_session.player1_id)
        player2 = User.query.get(active_session.player2_id)

    return render_template('senior/tictactoe.html', 
                         active_session=active_session, 
                         game_session_id=session_id, 
                         color=color,
                         player1=player1,
                         player2=player2)


# ==================== PROFILE ====================
@senior_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.query.get(session['user_id'])
    from forms import ProfileForm
    form = ProfileForm(obj=user)

    if form.validate_on_submit():
        # 1. Update basic information from Form
        user.full_name = form.full_name.data
        session['full_name'] = user.full_name
        user.email = form.email.data
        user.phone = form.phone.data
        user.age = form.age.data

        # 2. Handle Interests (Manual from request.form)
        interests_text = request.form.get('interests')
        if interests_text:
            user.interests = [i.strip() for i in interests_text.split(',') if i.strip()]
        
        # 3. Handle Languages (Manual from request.form)
        languages = request.form.getlist('languages')
        user.languages = languages

        # 4. Handle Profile Picture Upload (Form Validated)
        if form.profile_picture.data and hasattr(form.profile_picture.data, 'filename'):
            file = form.profile_picture.data
            # WTForms FileAllowed validator handles the check
            
            filename = secure_filename(file.filename)
            if filename: # Ensure filename is not empty
                # Ensure upload directory exists
                os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                # Create unique filename
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S_')
                unique_filename = f"profile_{user.id}_{timestamp}{filename}"
                
                # Save the physical file to static/images/uploads/
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
                
                # DELETE OLD PICTURE
                if user.profile_picture and 'default-avatar' not in user.profile_picture:
                    old_filename = os.path.basename(user.profile_picture)
                    old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], old_filename)
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except OSError:
                            pass 
                            
                # SAVE TO DB WITH 'uploads/' PREFIX
                user.profile_picture = f"images/uploads/{unique_filename}"
                session['profile_picture'] = user.profile_picture

        # 5. Commit changes
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your profile.', 'danger')
            print(f"Error updating profile: {e}")
            
        return redirect(url_for('senior.profile'))
    
    # Flash errors if form validation fails
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'danger')

    # Get paired youth buddy info for display
    pair = Pair.query.filter_by(senior_id=user.id, status='active').first()
    buddy = User.query.get(pair.youth_id) if pair else None

    return render_template('senior/profile.html', user=user, form=form, buddy=buddy)


@senior_bp.route('/users/<int:user_id>')
@login_required
def public_profile(user_id):
    """View another user's public profile."""
    user = User.query.get_or_404(user_id)
    
    # Get public stats
    stories_count = Story.query.filter_by(user_id=user.id).count()
    
    # Get badges if youth
    badges = []
    if user.role == 'youth':
        earned_badges = Badge.query.filter_by(user_id=user.id).all()
        BADGE_ICONS = {
            'First Steps': '🌟', 'Story Keeper': '📖', 'Tech Wizard': '💻',
            'Game Master': '🎮', 'Community Builder': '🏘️', 'Event Organizer': '📅',
            'Heritage Champion': '🏛️', 'Conversation Partner': '💬',
            'Week Warrior': '🔥', 'Month Master': '🏆', 'Century Champion': '💯', 'Year Legend': '👑'
        }
        badges = [{'title': b.badge_type, 'icon': BADGE_ICONS.get(b.badge_type, '🏅')} for b in earned_badges]
    
    # Get recent stories
    recent_stories = Story.query.filter_by(user_id=user.id).order_by(Story.created_at.desc()).limit(5).all()
    
    return render_template('senior/public_profile.html', 
                         profile_user=user, 
                         stories_count=stories_count,
                         badges=badges,
                         recent_stories=recent_stories)

# ==================== CHECKIN ====================
@senior_bp.route('/checkin', methods=['GET', 'POST'])
@login_required
def checkin():
    """Weekly mood check-in for seniors."""
    if request.method == 'POST':
        from models import Checkin

        mood = request.form.get('mood')
        notes = request.form.get('notes')

        new_checkin = Checkin(
            user_id=session['user_id'],
            mood=mood,
            notes=notes
        )

        db.session.add(new_checkin)
        db.session.commit()

        flash('Check-in submitted successfully!', 'success')
        return redirect(url_for('senior.dashboard'))

    return render_template('senior/checkin.html')


# ==================== ACCESSIBILITY SETTINGS ====================
@senior_bp.route('/accessibility-settings', methods=['POST'])
@login_required
def save_accessibility_settings():
    """
    API to save accessibility preferences.
    """
    data = request.get_json()
    user = User.query.get(session['user_id'])
    
    settings = {
        'font_size': data.get('font_size', 'normal'),
        'high_contrast': data.get('high_contrast', False),
        'color_blind_friendly': data.get('color_blind_friendly', False)
    }
    
    user.accessibility_settings = settings
    db.session.commit()
    
    return {'success': True}
