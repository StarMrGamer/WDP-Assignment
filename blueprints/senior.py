"""
File: senior.py
Purpose: Senior user routes blueprint
Author: Rai (Team Lead)
Date: December 2025
Features: Senior Dashboard, Story Sharing, Messages, Events, Communities, Games, Profile
Description: Handles all routes for senior users including story creation,
             messaging with youth buddies, event registration, and accessibility features
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, User, Story, Message, Event, Community, Pair
from datetime import datetime
from functools import wraps

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

        # Handle photo upload (if any)
        # TODO: Implement file upload in Phase B

        db.session.add(new_story)
        db.session.commit()

        flash('Story created successfully!', 'success')
        return redirect(url_for('senior.stories'))

    return render_template('senior/create_story.html')


# ==================== MESSAGES ====================
@senior_bp.route('/messages')
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

    # Get messages between senior and youth
    messages = Message.query.filter(
        ((Message.sender_id == user_id) & (Message.recipient_id == buddy.id)) |
        ((Message.sender_id == buddy.id) & (Message.recipient_id == user_id))
    ).order_by(Message.created_at).all()

    return render_template('senior/messages.html', buddy=buddy, messages=messages)


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
@senior_bp.route('/profile')
@login_required
def profile():
    """Display and edit senior profile."""
    user = User.query.get(session['user_id'])

    # Get paired youth buddy info
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
