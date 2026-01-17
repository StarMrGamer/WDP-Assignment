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
from models import db, User, Story, Message, Event, Community, Pair
from datetime import datetime
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
        'created_at': msg.created_at.strftime('%I:%M %p'), # Format: 02:30 PM
        'is_flagged': msg.is_flagged,
        'translated_content': msg.translated_content if msg.original_language != 'en' else None
    } for msg in messages]

    return {'messages': messages_data}


# ==================== EVENTS ====================
@senior_bp.route('/events')
@login_required
def events():
    """Display all available events."""
    upcoming_events = Event.query.filter(Event.date >= datetime.utcnow())\
        .order_by(Event.date).all()

    return render_template('senior/events.html', events=upcoming_events)


# ==================== COMMUNITIES ====================
@senior_bp.route('/communities')
@login_required
def communities():
    """Display all communities."""
    all_communities = Community.query.all()

    return render_template('senior/communities.html', communities=all_communities)


# ==================== GAMES ====================
@senior_bp.route('/games')
@login_required
def games():
    """Display game selection lobby."""
    # Get paired youth buddy for online status
    pair = Pair.query.filter_by(senior_id=session['user_id'], status='active').first()
    buddy = User.query.get(pair.youth_id) if pair else None

    return render_template('senior/games.html', buddy=buddy)


# ==================== PROFILE ====================
@senior_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    Display and edit senior profile.
    Handles both viewing the profile and processing updates.
    """
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        # 1. Update basic information
        user.full_name = request.form.get('full_name')
        user.email = request.form.get('email')
        user.phone = request.form.get('phone')
        
        # Handle age with validation
        try:
            user.age = int(request.form.get('age'))
        except (ValueError, TypeError):
            flash('Invalid age provided.', 'warning')

        # 2. Handle Interests (Textarea -> List conversion)
        # We split the comma-separated string into a list for JSON storage
        interests_text = request.form.get('interests')
        if interests_text:
            # Split by comma and strip whitespace
            user.interests = [i.strip() for i in interests_text.split(',') if i.strip()]
        
        # 3. Handle Languages (Checkboxes -> List)
        # getlist returns all selected values from checkboxes with same name
        languages = request.form.getlist('languages')
        user.languages = languages

        # 4. Handle Profile Picture Upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename != '':
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
