"""
File: youth.py
Purpose: Youth volunteer routes blueprint
Author: Rai (Team Lead)
Date: December 2025
Features: Youth Dashboard, Story Feed, Messages, Events, Communities, Badges, Profile
Description: Handles all routes for youth volunteers including story engagement,
             messaging with senior buddies, badge tracking, and theme customization
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, User, Story, Message, Event, Community, Pair, Badge
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
@youth_bp.route('/messages')
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

    # Get messages between youth and senior
    messages = Message.query.filter(
        ((Message.sender_id == user_id) & (Message.recipient_id == buddy.id)) |
        ((Message.sender_id == buddy.id) & (Message.recipient_id == user_id))
    ).order_by(Message.created_at).all()

    return render_template('youth/messages.html', buddy=buddy, messages=messages)


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
@youth_bp.route('/profile')
@login_required
def profile():
    """Display and edit youth profile."""
    user = User.query.get(session['user_id'])

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
