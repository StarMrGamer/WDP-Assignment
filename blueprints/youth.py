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
    upcoming_events = Event.query.filter(Event.date >= datetime.utcnow())\
        .order_by(Event.date).all()

    return render_template('youth/events.html', events=upcoming_events)


# ==================== COMMUNITIES ====================
@youth_bp.route('/communities')
@login_required
def communities():
    """Display all communities."""
    all_communities = Community.query.all()

    return render_template('youth/communities.html', communities=all_communities)


# ==================== BADGES ====================
@youth_bp.route('/badges')
@login_required
def badges():
    """Display earned badges and achievements."""
    user = User.query.get(session['user_id'])

    # Get earned badges
    earned_badges = Badge.query.filter_by(user_id=user.id).all()

    # Get streak info
    from models import Streak
    streak = Streak.query.filter_by(user_id=user.id).first()

    return render_template('youth/badges.html',
                         user=user,
                         earned_badges=earned_badges,
                         streak=streak)


# ==================== PROFILE ====================
@youth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Display and edit youth profile."""
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        # 1. Update basic information
        user.full_name = request.form.get('full_name')
        user.email = request.form.get('email')
        user.phone = request.form.get('phone')
        user.school = request.form.get('school')
        user.bio = request.form.get('bio')
        
        # Handle age with validation
        try:
            user.age = int(request.form.get('age'))
        except (ValueError, TypeError):
            flash('Invalid age provided.', 'warning')

        # 2. Handle Profile Picture Upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename != '':
                from werkzeug.utils import secure_filename
                import os
                
                filename = secure_filename(file.filename)
                # Check extension
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                if ext in current_app.config['ALLOWED_EXTENSIONS']:
                    # Ensure upload directory exists
                    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                    
                    # Save file with unique name to prevent collisions
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S_')
                    unique_filename = f"profile_{user.id}_{timestamp}{filename}"
                    
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
                    
                    # Delete old profile picture if it's not the default
                    if user.profile_picture and user.profile_picture != 'default-avatar.png':
                        old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], user.profile_picture)
                        if os.path.exists(old_path):
                            try:
                                os.remove(old_path)
                            except OSError:
                                pass # Ignore error if old file cannot be deleted
                                
                    user.profile_picture = unique_filename

        # 3. Commit changes
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your profile.', 'danger')
            print(f"Error updating profile: {e}")
            
        return redirect(url_for('youth.profile'))

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
