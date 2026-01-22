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
from models import db, User, Story, Message, Event, Community, Pair, Badge, StoryReaction, StoryComment
from datetime import datetime
from functools import wraps

# Create youth blueprint
youth_bp = Blueprint('youth', __name__)


# ==================== HELPER FUNCTIONS ====================
def check_badges(user):
    """
    Check and award badges based on user stats.
    """
    from models import Badge
    
    # 1. First Steps: 1st Event
    events_count = user.event_participants.count()
    if events_count >= 1:
        award_badge(user, 'First Steps')
        
    # 2. Community Builder: 5 Communities
    communities_count = user.community_members.count()
    if communities_count >= 5:
        award_badge(user, 'Community Builder')
        
    # 3. Conversation Partner: 20 Messages
    messages_count = user.sent_messages.count()
    if messages_count >= 20:
        award_badge(user, 'Conversation Partner')

def award_badge(user, badge_name):
    from models import Badge
    if not Badge.query.filter_by(user_id=user.id, badge_type=badge_name).first():
        new_badge = Badge(user_id=user.id, badge_type=badge_name)
        db.session.add(new_badge)
        flash(f'🎉 Congratulations! You earned the {badge_name} badge!', 'success')


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
            
            # MOCK TRANSLATION LOGIC
            translated_text = None
            if content and len(content) > 0 and not content.isascii():
                 # Mock: If non-ascii characters (simulating foreign lang), add translation
                 translated_text = f"{content} [Translated to English]"
            elif content and "Bonjour" in content:
                 translated_text = "Hello [Translated]"
                 
            new_message = Message(
                sender_id=user_id,
                recipient_id=buddy.id,
                content=content,
                is_flagged=is_flagged,
                translated_content=translated_text
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
        'created_at': msg.created_at.strftime('%I:%M %p'), # Format: 02:30 PM
        'is_flagged': msg.is_flagged,
        'translated_content': msg.translated_content if msg.original_language != 'en' else None
    } for msg in messages]

    return {'messages': messages_data}


# ==================== EVENTS ====================
@youth_bp.route('/events')
@login_required
def events():
    """Display all available events."""
    user = User.query.get(session['user_id'])
    
    upcoming_events = Event.query.filter(Event.date >= datetime.utcnow())\
        .order_by(Event.date).all()
        
    # Get IDs of events the user has registered for
    registered_event_ids = {p.event_id for p in user.event_participants}

    return render_template('youth/events.html', 
                         events=upcoming_events, 
                         user=user,
                         registered_event_ids=registered_event_ids,
                         now=datetime.utcnow())


@youth_bp.route('/events/<int:event_id>/register', methods=['POST'])
@login_required
def register_event(event_id):
    """Register for an event."""
    from models import EventParticipant
    
    # Check if already registered
    existing = EventParticipant.query.filter_by(
        event_id=event_id, 
        user_id=session['user_id']
    ).first()
    
    if existing:
        flash('You are already registered for this event.', 'info')
    else:
        new_participant = EventParticipant(
            event_id=event_id,
            user_id=session['user_id']
        )
        db.session.add(new_participant)
        db.session.commit()
        
        event = Event.query.get(event_id)
        
        # Check for badges
        user = User.query.get(session['user_id'])
        check_badges(user)
        db.session.commit() # Commit again for badge
        
        flash(f'Successfully registered for {event.title}!', 'success')
        
    return redirect(url_for('youth.events'))


# ==================== COMMUNITIES ====================
@youth_bp.route('/communities')
@login_required
def communities():
    """Display all communities."""
    user = User.query.get(session['user_id'])
    all_communities = Community.query.all()
    
    # Get IDs of communities the user has already joined
    joined_community_ids = {member.community_id for member in user.community_members}

    return render_template('youth/communities.html', 
                         communities=all_communities, 
                         user=user,
                         joined_community_ids=joined_community_ids)


@youth_bp.route('/communities/<int:community_id>/join', methods=['POST'])
@login_required
def join_community(community_id):
    """Join a community."""
    from models import CommunityMember
    
    # Check if already joined
    existing = CommunityMember.query.filter_by(
        community_id=community_id, 
        user_id=session['user_id']
    ).first()
    
    if existing:
        flash('You are already a member of this community.', 'info')
    else:
        new_member = CommunityMember(
            community_id=community_id,
            user_id=session['user_id']
        )
        
        # Update member count
        community = Community.query.get_or_404(community_id)
        community.member_count += 1
        
        db.session.add(new_member)
        db.session.commit()
        
        # Check for badges
        user = User.query.get(session['user_id'])
        check_badges(user)
        db.session.commit() # Commit again for badge
        
        flash(f'Successfully joined {community.name}!', 'success')
        
    return redirect(url_for('youth.communities'))


@youth_bp.route('/communities/<int:community_id>/leave', methods=['POST'])
@login_required
def leave_community(community_id):
    """Leave a community."""
    from models import CommunityMember
    
    member = CommunityMember.query.filter_by(
        community_id=community_id, 
        user_id=session['user_id']
    ).first()
    
    if member:
        # Update member count
        community = Community.query.get_or_404(community_id)
        community.member_count = max(0, community.member_count - 1)
        
        db.session.delete(member)
        db.session.commit()
        flash(f'You have left {community.name}.', 'info')
    else:
        flash('You are not a member of this community.', 'warning')
        
    return redirect(url_for('youth.communities'))


# ==================== BADGES ====================
@youth_bp.route('/badges')
@login_required
def badges():
    """Display earned badges and achievements."""
    user = User.query.get(session['user_id'])

    # Get earned badges
    earned_badges_list = Badge.query.filter_by(user_id=user.id).all()
    earned_badge_types = {b.badge_type for b in earned_badges_list}

    # Get streak info
    from models import Streak
    streak = Streak.query.filter_by(user_id=user.id).first()

    # Calculate stats
    events_count = user.event_participants.count()
    total_hours = events_count * 2 # Assumption: 2 hours per event
    seniors_helped = events_count + (1 if user.youth_pairs.count() > 0 else 0)

    # Define all available badges
    all_badges = [
        {'type': 'First Steps', 'icon': '🌟', 'desc': 'Complete your first volunteer session', 'threshold': 1},
        {'type': 'Story Keeper', 'icon': '📖', 'desc': 'Document 5 senior life stories', 'threshold': 5},
        {'type': 'Tech Wizard', 'icon': '💻', 'desc': 'Help 10 seniors with technology', 'threshold': 10},
        {'type': 'Game Master', 'icon': '🎮', 'desc': 'Facilitate 15 game sessions', 'threshold': 15},
        {'type': 'Community Builder', 'icon': '🏘️', 'desc': 'Join 5 volunteer communities', 'threshold': 5},
        {'type': 'Event Organizer', 'icon': '📅', 'desc': 'Organize 3 volunteer events', 'threshold': 3},
        {'type': 'Heritage Champion', 'icon': '🏛️', 'desc': 'Participate in 5 heritage activities', 'threshold': 5},
        {'type': 'Conversation Partner', 'icon': '💬', 'desc': 'Have 20 meaningful conversations', 'threshold': 20}
    ]

    return render_template('youth/badges.html',
                         user=user,
                         earned_badge_types=earned_badge_types,
                         streak=streak,
                         stats={
                             'hours': total_hours,
                             'badges': len(earned_badges_list),
                             'events': events_count,
                             'seniors': seniors_helped
                         },
                         all_badges=all_badges)


# ==================== PROFILE ====================
@youth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        # 1. Update basic information
        user.full_name = request.form.get('full_name')
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
                    user.profile_picture = f"uploads/{unique_filename}"

        # 3. Commit changes
        try:
            db.session.commit()
            # Update session with new profile picture to reflect changes immediately in navbar
            session['profile_picture'] = user.profile_picture
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
                         messages_count=messages_count,
                         now=datetime.utcnow())


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
