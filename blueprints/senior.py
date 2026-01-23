"""
File: senior.py
Purpose: Senior user routes blueprint
Author: Rai (Team Lead)
Date: December 2025
Features: Senior Dashboard, Story Sharing, Messages, Events, Communities, Games, Profile
Description: Handles all routes for senior users including story creation,
             messaging with youth buddies, event registration, and accessibility features
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from models import db, User, Story, Message, Event, Community, Pair, EventParticipant, CommunityMember, Game, GameSession, CommunityPost, Badge, ChatReport
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.utils import secure_filename
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
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category')

        # Validate
        if not all([title, content, category]):
            flash('Please fill in all required fields', 'danger')
            return render_template('senior/create_story.html')

        # Create new story
        new_story = Story(
            user_id=session['user_id'],
            title=title,
            content=content,
            category=category
        )

        # Handle photo upload
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '':
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

    return render_template('senior/create_story.html')


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

    if request.method == 'POST':
        # Retrieve message content from form
        content = request.form.get('message')
        if content:
            # Check for unkind words using the application configuration
            # This is a basic safety feature to flag potentially harmful content
            is_flagged = False
            unkind_words = current_app.config.get('UNKIND_WORDS', [])
            for word in unkind_words:
                if word.lower() in content.lower():
                    is_flagged = True
                    break
            
            # Create new message object
            # Status defaults to sent/unread (logic handled by frontend display)
            new_message = Message(
                sender_id=user_id,
                recipient_id=buddy.id,
                content=content,
                is_flagged=is_flagged
            )
            
            # Add to database session
            db.session.add(new_message)
            
            # Update pair last interaction timestamp
            # This helps track active vs inactive pairs for admin reporting
            pair.last_interaction = datetime.utcnow()
            
            # Commit changes to database
            db.session.commit()
            
            # Notify user if their message was flagged
            if is_flagged:
                flash('Your message was sent but flagged for review due to potentially unkind language.', 'warning')
            
            # Redirect to the same page to show the new message
            # This follows the Post-Redirect-Get pattern
            return redirect(url_for('senior.messages'))

    # Get messages between senior and youth
    messages = Message.query.filter(
        ((Message.sender_id == user_id) & (Message.recipient_id == buddy.id)) |
        ((Message.sender_id == buddy.id) & (Message.recipient_id == user_id))
    ).order_by(Message.created_at).all()

    return render_template('senior/messages.html', buddy=buddy, messages=messages)


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
    
    # Stats
    stats = {
        'played': streak_info.games_played if streak_info else 0,
        'won': streak_info.games_won if streak_info else 0,
        'points': streak_info.points if streak_info else 0,
        'streak': streak_info.current_streak if streak_info else 0
    }

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

    return render_template('senior/games.html', buddy=buddy, games=games_data, stats=stats, active_session=active_session)


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
    
    # Close any existing active sessions for this game/pair
    existing = GameSession.query.filter_by(player1_id=user_id, player2_id=pair.youth_id, status='waiting').first()
    if existing:
        db.session.delete(existing)

    game = Game.query.get(game_id)
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
        link=url_for('youth.chess_game', session_id=new_session.id)
    )
    db.session.add(notif)
    db.session.commit()
    
    return redirect(url_for('senior.chess_game', session_id=new_session.id))


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
    return render_template('senior/chess.html', color=color, game_session_id=active_session.id, active_session=active_session)


# ==================== PROFILE ====================
@senior_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        # 1. Update basic information
        user.full_name = request.form.get('full_name')
        session['full_name'] = user.full_name
        user.email = request.form.get('email')
        user.phone = request.form.get('phone')
        
        try:
            user.age = int(request.form.get('age'))
        except (ValueError, TypeError):
            flash('Invalid age provided.', 'warning')

        # 2. Handle Interests
        interests_text = request.form.get('interests')
        if interests_text:
            user.interests = [i.strip() for i in interests_text.split(',') if i.strip()]
        
        # 3. Handle Languages
        languages = request.form.getlist('languages')
        user.languages = languages

        # 4. Handle Profile Picture Upload (FIXED)
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                if ext in current_app.config['ALLOWED_EXTENSIONS']:
                    # Ensure upload directory exists
                    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                    
                    # Create unique filename
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S_')
                    unique_filename = f"profile_{user.id}_{timestamp}{filename}"
                    
                    # Save the physical file to static/images/uploads/
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
                    
                    # DELETE OLD PICTURE (Updated logic)
                    if user.profile_picture and 'default-avatar' not in user.profile_picture:
                        # We use basename to get just the filename, ignoring any 'uploads/' prefix
                        old_filename = os.path.basename(user.profile_picture)
                        old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], old_filename)
                        if os.path.exists(old_path):
                            try:
                                os.remove(old_path)
                            except OSError:
                                pass 
                                
                    # SAVE TO DB WITH 'uploads/' PREFIX
                    # This tells the template to look inside the uploads folder
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

    # Get paired youth buddy info for display
    pair = Pair.query.filter_by(senior_id=user.id, status='active').first()
    buddy = User.query.get(pair.youth_id) if pair else None

    return render_template('senior/profile.html', user=user, buddy=buddy)


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
