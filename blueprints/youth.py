"""
File: youth.py
Purpose: Youth volunteer routes blueprint
Author: Rai (Team Lead)
Date: December 2025
Features: Youth Dashboard, Story Feed, Messages, Events, Communities, Badges, Profile
Description: Handles all routes for youth volunteers including story engagement,
             messaging with senior buddies, badge tracking, and theme customization
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from models import db, User, Story, Message, Event, Community, Pair, Badge, StoryReaction, StoryComment, EventParticipant, CommunityMember, Game, GameSession, CommunityPost, ChatReport
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.utils import secure_filename
import os

# Create youth blueprint
youth_bp = Blueprint('youth', __name__)


# ==================== AUTHENTICATION DECORATOR ====================
def login_required(f):
    """
    Decorator to require login for routes.
    Ensures user is logged in and is a youth volunteer.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('auth.login', role='youth'))
        if session.get('role') != 'youth':
            flash('Access denied. Youth account required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# ==================== DASHBOARD ====================
@youth_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Youth dashboard - main page after login.
    Shows recent stories, stats, and quick actions.
    """
    user = User.query.get(session['user_id'])

    # Get paired senior buddy
    pair = Pair.query.filter_by(youth_id=user.id, status='active').first()
    buddy = User.query.get(pair.senior_id) if pair else None

    # Get recent stories from all seniors
    recent_stories = Story.query.order_by(Story.created_at.desc()).limit(10).all()

    # Get user badges
    badges = Badge.query.filter_by(user_id=user.id).count()

    return render_template('youth/dashboard.html',
                         user=user,
                         buddy=buddy,
                         recent_stories=recent_stories,
                         badges_count=badges)


# ==================== STORY FEED ====================
@youth_bp.route('/story_feed')
@login_required
def story_feed():
    """Instagram-style story feed with all senior stories."""
    # Get filter from query parameter
    category_filter = request.args.get('category', 'all')

    # Query stories
    query = Story.query

    if category_filter != 'all':
        query = query.filter_by(category=category_filter)

    stories = query.order_by(Story.created_at.desc()).all()

    return render_template('youth/story_feed.html',
                         stories=stories,
                         current_filter=category_filter)


@youth_bp.route('/story/<int:story_id>')
@login_required
def story_detail(story_id):
    """Full story view with reactions and comments."""
    story = Story.query.get_or_404(story_id)

    return render_template('youth/story_detail.html', story=story)


# ==================== MESSAGES ====================
@youth_bp.route('/messages', methods=['GET', 'POST'])
@login_required
def messages():
    """Display messaging interface with senior buddy."""
    user_id = session['user_id']

    # Get paired senior buddy
    pair = Pair.query.filter_by(youth_id=user_id, status='active').first()
    if not pair:
        flash('You are not currently paired with a senior', 'info')
        return render_template('youth/messages.html', buddy=None, messages=[])

    buddy = User.query.get(pair.senior_id)

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
            return redirect(url_for('youth.messages'))

    # Get messages between youth and senior
    messages = Message.query.filter(
        ((Message.sender_id == user_id) & (Message.recipient_id == buddy.id)) |
        ((Message.sender_id == buddy.id) & (Message.recipient_id == user_id))
    ).order_by(Message.created_at).all()

    return render_template('youth/messages.html', buddy=buddy, messages=messages)


@youth_bp.route('/api/messages')
@login_required
def get_messages_json():
    """
    API endpoint to fetch messages in JSON format.
    Used by the frontend polling script (chat.js) to update the chat window
    without reloading the entire page.
    """
    user_id = session['user_id']
    
    # Check if user has a buddy
    pair = Pair.query.filter_by(youth_id=user_id, status='active').first()
    if not pair:
        return {'messages': []}

    buddy_id = pair.senior_id

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


@youth_bp.route('/api/messages/<int:message_id>/report', methods=['POST'])
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
@youth_bp.route('/events')
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
    my_events = []
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
        if is_registered:
            my_events.append(event_dict)

    return render_template('youth/events.html', events=events_data, my_events=my_events)


@youth_bp.route('/events/<int:event_id>/register', methods=['POST'])
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
@youth_bp.route('/communities')
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
        
        # Determine stats label/icon based on type
        if comm.type == 'Story':
            comm.stat_label = 'stories'
            comm.stat_icon = 'fas fa-book'
        elif comm.type == 'Learning':
            comm.stat_label = 'sessions'
            comm.stat_icon = 'fas fa-laptop'
        elif comm.type == 'Hobby':
            comm.stat_label = 'activities'
            comm.stat_icon = 'fas fa-star'
        else:
            comm.stat_label = 'posts'
            comm.stat_icon = 'fas fa-comment'
            
        comm.stat_count = comm.posts.count()
        
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

    return render_template('youth/communities.html', 
                         my_communities=my_communities, 
                         other_communities=other_communities,
                         search_query=search_query)


@youth_bp.route('/communities/<int:community_id>')
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
        return redirect(url_for('youth.communities'))
        
    # Update last_viewed_at
    member.last_viewed_at = datetime.utcnow()
    db.session.commit()
        
    # Get recent posts for the chat history
    posts = CommunityPost.query.filter_by(community_id=community_id)\
        .order_by(CommunityPost.created_at.asc()).all()
        
    members = community.members.all()
    return render_template('youth/community_chat.html', community=community, posts=posts, user_id=user_id, members=members)


@youth_bp.route('/communities/<int:community_id>/upload_photo', methods=['POST'])
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


@youth_bp.route('/communities/<int:community_id>/join', methods=['POST'])
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


# ==================== BADGES ====================
@youth_bp.route('/badges')
@login_required
def badges():
    """Display earned badges and achievements."""
    user_id = session['user_id']
    user = User.query.get(user_id)

    # Get earned badges
    earned_badges = Badge.query.filter_by(user_id=user_id).all()
    earned_types = [b.badge_type for b in earned_badges]

    # Define all possible badges
    MASTER_BADGES = [
        {'title': 'First Steps', 'desc': 'Complete your first volunteer session', 'icon': '🌟', 'target': 1, 'current': 1 if 'First Steps' in earned_types else 0},
        {'title': 'Story Keeper', 'desc': 'Document 5 senior life stories', 'icon': '📖', 'target': 5, 'current': 5 if 'Story Keeper' in earned_types else 2},
        {'title': 'Tech Wizard', 'desc': 'Help 10 seniors with technology', 'icon': '💻', 'target': 10, 'current': 10 if 'Tech Wizard' in earned_types else 4},
        {'title': 'Game Master', 'desc': 'Facilitate 15 game sessions', 'icon': '🎮', 'target': 15, 'current': 9 if 'Game Master' not in earned_types else 15},
        {'title': 'Community Builder', 'desc': 'Join 5 volunteer communities', 'icon': '🏘️', 'target': 5, 'current': 3 if 'Community Builder' not in earned_types else 5},
        {'title': 'Event Organizer', 'desc': 'Organize 3 volunteer events', 'icon': '📅', 'target': 3, 'current': 0 if 'Event Organizer' not in earned_types else 3},
        {'title': 'Heritage Champion', 'desc': 'Participate in 5 heritage activities', 'icon': '🏛️', 'target': 5, 'current': 5 if 'Heritage Champion' in earned_types else 1},
        {'title': 'Conversation Partner', 'desc': 'Have 20 meaningful conversations', 'icon': '💬', 'target': 20, 'current': 15 if 'Conversation Partner' not in earned_types else 20}
    ]

    # Process badges for template
    processed_badges = []
    for mb in MASTER_BADGES:
        mb['is_earned'] = mb['current'] >= mb['target']
        mb['progress_pct'] = min(100, int((mb['current'] / mb['target']) * 100))
        processed_badges.append(mb)

    # Get streak and points
    from models import Streak
    streak = Streak.query.filter_by(user_id=user_id).first()
    points = streak.points if streak else 0
    
    # Calculate stats
    stats = {
        'hours': int(points / 10), # Derived from points
        'badges_count': len(earned_badges),
        'events_attended': EventParticipant.query.filter_by(user_id=user_id).count() or 24, # Mock if 0
        'seniors_helped': int(points / 30) or 15 # Derived
    }

    # Milestones (fixed definitions, dynamic status)
    MILESTONES = [
        {'title': 'Bronze Volunteer', 'hours': 10, 'desc': "You've taken your first steps in volunteering! Keep up the great work."},
        {'title': 'Silver Volunteer', 'hours': 25, 'desc': "You're making a real difference in the community. Seniors appreciate your dedication!"},
        {'title': 'Gold Volunteer', 'hours': 50, 'desc': "Outstanding commitment! You're on track to reach this milestone soon."},
        {'title': 'Platinum Volunteer', 'hours': 100, 'desc': "Elite volunteer status. Your impact on the community is incredible!"},
        {'title': 'Diamond Volunteer', 'hours': 200, 'desc': "The highest honor. You're a true champion for intergenerational connections!"}
    ]
    for m in MILESTONES:
        m['is_locked'] = stats['hours'] < m['hours']

    # Leaderboard (Top 5 youth by points)
    leaderboard_users = User.query.filter_by(role='youth').join(Streak).order_by(Streak.points.desc()).limit(5).all()
    leaderboard = []
    for i, u in enumerate(leaderboard_users):
        u_streak = Streak.query.filter_by(user_id=u.id).first()
        leaderboard.append({
            'rank': i + 1,
            'name': u.full_name,
            'is_me': u.id == user_id,
            'avatar': u.profile_picture,
            'events': EventParticipant.query.filter_by(user_id=u.id).count() or (20 + i), # Mock
            'badges': Badge.query.filter_by(user_id=u.id).count(),
            'hours': int((u_streak.points if u_streak else 0) / 10)
        })

    return render_template('youth/badges.html',
                         user=user,
                         badges=processed_badges,
                         stats=stats,
                         milestones=MILESTONES,
                         leaderboard=leaderboard)


# ==================== PROFILE ====================
@youth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        # 1. Update basic information
        user.full_name = request.form.get('full_name')
        session['full_name'] = user.full_name
        user.email = request.form.get('email')
        user.phone = request.form.get('phone')
        user.school = request.form.get('school')
        user.bio = request.form.get('bio')
        
        try:
            user.age = int(request.form.get('age'))
        except (ValueError, TypeError):
            flash('Invalid age provided.', 'warning')

        # 2. Handle Profile Picture Upload (FIXED)
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename != '':
                from werkzeug.utils import secure_filename
                import os
                
                filename = secure_filename(file.filename)
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                if ext in current_app.config['ALLOWED_EXTENSIONS']:
                    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                    
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S_')
                    unique_filename = f"profile_{user.id}_{timestamp}{filename}"
                    
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
                    
                    # DELETE OLD PICTURE (Updated logic)
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

        # 3. Commit changes
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your profile.', 'danger')
            print(f"Error updating profile: {e}")
            
        return redirect(url_for('youth.profile'))

    # ... [Keep the rest of the existing youth profile code below] ...
    # Get paired senior buddy info
    pair = Pair.query.filter_by(youth_id=user.id, status='active').first()
    buddy = User.query.get(pair.senior_id) if pair else None

    # Get impact stats
    from models import StoryReaction, StoryComment, Message
    reactions_count = StoryReaction.query.filter_by(user_id=user.id).count()
    comments_count = StoryComment.query.filter_by(user_id=user.id).count()
    messages_count = Message.query.filter_by(sender_id=user.id).count()

    return render_template('youth/profile.html',
                         user=user,
                         buddy=buddy,
                         reactions_count=reactions_count,
                         comments_count=comments_count,
                         messages_count=messages_count)


@youth_bp.route('/users/<int:user_id>')
@login_required
def public_profile(user_id):
    """View another user's public profile."""
    user = User.query.get_or_404(user_id)
    
    # Get public stats
    stories_count = Story.query.filter_by(user_id=user.id).count()
    badges_count = Badge.query.filter_by(user_id=user.id).count()
    
    # Get badges
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
    
    return render_template('youth/public_profile.html', 
                         profile_user=user, 
                         stories_count=stories_count,
                         badges_count=badges_count,
                         badges=badges,
                         recent_stories=recent_stories)


# ==================== STORY INTERACTIONS API ====================
@youth_bp.route('/api/stories/<int:story_id>/react', methods=['POST'])
@login_required
def api_react_story(story_id):
    """
    API endpoint to handle story reactions.
    Toggles reaction if same type exists, or updates/creates new one.
    """
    data = request.get_json()
    reaction_type = data.get('reaction_type')
    user_id = session['user_id']
    
    if not reaction_type:
        return {'success': False, 'message': 'Missing reaction type'}, 400
        
    # Check for existing reaction
    existing_reaction = StoryReaction.query.filter_by(
        story_id=story_id,
        user_id=user_id
    ).first()
    
    if existing_reaction:
        if existing_reaction.reaction_type == reaction_type:
            # Toggle off (remove reaction)
            db.session.delete(existing_reaction)
            action = 'removed'
        else:
            # Change reaction type
            existing_reaction.reaction_type = reaction_type
            action = 'updated'
    else:
        # Create new reaction
        new_reaction = StoryReaction(
            story_id=story_id,
            user_id=user_id,
            reaction_type=reaction_type
        )
        db.session.add(new_reaction)
        action = 'added'
        
    db.session.commit()
    
    # Get updated count for this reaction type
    count = StoryReaction.query.filter_by(
        story_id=story_id,
        reaction_type=reaction_type
    ).count()
    
    return {
        'success': True,
        'action': action,
        'count': count
    }


@youth_bp.route('/api/stories/<int:story_id>/comment', methods=['POST'])
@login_required
def api_comment_story(story_id):
    """
    API endpoint to add a comment to a story.
    """
    data = request.get_json()
    content = data.get('content')
    user_id = session['user_id']
    
    if not content or not content.strip():
        return {'success': False, 'message': 'Comment cannot be empty'}, 400
        
    # Create new comment
    new_comment = StoryComment(
        story_id=story_id,
        user_id=user_id,
        content=content.strip()
    )
    
    db.session.add(new_comment)
    db.session.commit()
    
    return {'success': True}


# ==================== GAMES ====================
@youth_bp.route('/games')
@login_required
def games():
    """Display available games."""
    user_id = session['user_id']

    # Get paired senior buddy for online status/active games
    pair = Pair.query.filter_by(youth_id=user_id, status='active').first()
    buddy = User.query.get(pair.senior_id) if pair else None

    # Get active game session
    active_session = GameSession.query.filter(
        ((GameSession.player1_id == user_id) | (GameSession.player2_id == user_id)),
        GameSession.status == 'active'
    ).first()

    # Get streak info
    from models import Streak
    streak_info = Streak.query.filter_by(user_id=user_id).first()
    
    user = User.query.get(user_id)
    
    # Placeholder stats
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

    return render_template('youth/games.html', 
                         user=user, 
                         buddy=buddy, 
                         games=games_data, 
                         stats=stats, 
                         active_session=active_session,
                         game_history=game_history)


@youth_bp.route('/games/challenge/<int:game_id>')
@login_required
def challenge_buddy(game_id):
    """Create a new game session and challenge buddy."""
    from app import socketio
    user_id = session['user_id']
    pair = Pair.query.filter_by(youth_id=user_id, status='active').first()
    if not pair:
        flash('You need a buddy to play!', 'warning')
        return redirect(url_for('youth.games'))
    
    # Check for ANY existing waiting session for this game between the pair
    # This ensures that if the buddy already created a session, we join it instead of creating a duplicate
    existing_sessions = GameSession.query.filter(
        GameSession.game_id == game_id,
        GameSession.status == 'waiting',
        ((GameSession.player1_id == user_id) & (GameSession.player2_id == pair.senior_id)) |
        ((GameSession.player1_id == pair.senior_id) & (GameSession.player2_id == user_id))
    ).order_by(GameSession.created_at.desc()).all()

    # Fetch game details first to determine type
    game = Game.query.get_or_404(game_id)

    # Determine target URL based on game type
    target_url = 'youth.chess_game'
    senior_url = 'senior.chess_game'
    
    if 'Xiangqi' in game.title:
        target_url = 'youth.xiangqi_game'
        senior_url = 'senior.xiangqi_game'
    elif 'Tic Tac Toe' in game.title or 'Tic-Tac-Toe' in game.title:
        target_url = 'youth.tictactoe_game'
        senior_url = 'senior.tictactoe_game'

    if existing_sessions:
        # Use the most recent one
        session_to_use = existing_sessions[0]
        
        # Clean up any duplicates
        for gs in existing_sessions[1:]:
            db.session.delete(gs)
        db.session.commit()
        
        flash('Entering existing game lobby.', 'info')
        return redirect(url_for(target_url, session_id=session_to_use.id))

    # No existing session found, create a new one
    new_session = GameSession(
        game_id=game_id,
        player1_id=user_id,
        player2_id=pair.senior_id,
        status='waiting',
        current_turn_id=user_id
    )
    db.session.add(new_session)
    db.session.commit()

    # EMIT CHALLENGE
    socketio.emit('game_challenge', {
        'challenger_name': session.get('full_name'),
        'game_title': game.title,
        'session_id': new_session.id
    }, room=f"user_{pair.senior_id}")

    # CREATE NOTIFICATION RECORD
    from models import Notification
    
    notif = Notification(
        user_id=pair.senior_id,
        title='Game Challenge!',
        message=f"{session.get('full_name')} has challenged you to a game of {game.title}!",
        type='game',
        link=url_for(senior_url, session_id=new_session.id)
    )
    db.session.add(notif)
    db.session.commit()
    
    return redirect(url_for(target_url, session_id=new_session.id))


@youth_bp.route('/game/chess')
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
        return redirect(url_for('youth.games'))

    color = 'white' if active_session.player1_id == user_id else 'black'
    
    player1 = User.query.get(active_session.player1_id)
    player2 = User.query.get(active_session.player2_id)
    
    return render_template('youth/chess.html', 
                         color=color, 
                         game_session_id=active_session.id, 
                         active_session=active_session,
                         player1=player1,
                         player2=player2)


@youth_bp.route('/game/xiangqi')
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
            return redirect(url_for('youth.games'))
            
    # Default to Red (Player 1) if session exists, else Red (Bot mode default)
    color = 'red'
    player1 = None
    player2 = None
    if active_session:
        color = 'red' if active_session.player1_id == user_id else 'black'
        player1 = User.query.get(active_session.player1_id)
        player2 = User.query.get(active_session.player2_id)

    return render_template('youth/xiangqi.html', 
                         active_session=active_session, 
                         game_session_id=session_id, 
                         color=color,
                         player1=player1,
                         player2=player2)

@youth_bp.route('/game/tictactoe')
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
            return redirect(url_for('youth.games'))
            
    # Default to X (Player 1) if session exists, else X (single player default)
    color = 'X'
    player1 = None
    player2 = None
    if active_session:
        color = 'X' if active_session.player1_id == user_id else 'O'
        player1 = User.query.get(active_session.player1_id)
        player2 = User.query.get(active_session.player2_id)

    return render_template('youth/tictactoe.html', 
                         active_session=active_session, 
                         game_session_id=session_id, 
                         color=color,
                         player1=player1,
                         player2=player2)
