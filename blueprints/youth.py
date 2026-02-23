"""
File: youth.py
Purpose: Youth volunteer routes blueprint
Author: to be assigned
Date: December 2025
Features: Youth Dashboard, Story Feed, Messages, Events, Communities, Badges, Profile
Description: Handles all routes for youth volunteers including story engagement,
             messaging with senior buddies, badge tracking, and theme customization
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, send_file
from models import db, User, Story, Message, Event, Community, Pair, Badge, StoryReaction, StoryComment, EventParticipant, CommunityMember, Game, GameSession, CommunityPost, ChatReport
from forms import MessageForm, StoryForm
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from utils import filter_text, check_unkind_words, save_uploaded_file, sanitize_for_display, LANG_MAP
from blueprints.decorators import youth_required as login_required
import os
import io
from fpdf import FPDF
from deep_translator import GoogleTranslator

# Create youth blueprint
youth_bp = Blueprint('youth', __name__)


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

    # Get filters from query parameters
    category_filter = request.args.get('category', 'all')
    role_filter = request.args.get('role', 'all')

    # Query all stories with filters
    query = Story.query.join(User)
    if category_filter != 'all':
        query = query.filter(Story.category == category_filter)
    if role_filter != 'all':
        query = query.filter(User.role == role_filter)
    recent_stories = query.order_by(Story.created_at.desc()).all()

    # Get user badges
    badges = Badge.query.filter_by(user_id=user.id).count()

    return render_template('youth/dashboard.html',
                         user=user,
                         buddy=buddy,
                         recent_stories=recent_stories,
                         badges_count=badges,
                         current_category=category_filter,
                         current_role=role_filter)


# ==================== STORY FEED ====================
@youth_bp.route('/stories')
@login_required
def stories():
    """Display all stories created by this youth."""
    user_id = session['user_id']
    stories = Story.query.filter_by(user_id=user_id)\
        .order_by(Story.created_at.desc()).all()

    return render_template('youth/stories.html', stories=stories)


@youth_bp.route('/create_story', methods=['GET', 'POST'])
@login_required
def create_story():
    """Create a new story (step-by-step wizard)."""
    form = StoryForm()

    # Profanity check runs on every POST, before WTForms validation
    if request.method == 'POST':
        unkind_words = current_app.config.get('UNKIND_WORDS', [])
        raw_title = request.form.get('title', '')
        raw_content = request.form.get('content', '')
        if check_unkind_words(raw_title, unkind_words) or check_unkind_words(raw_content, unkind_words):
            flash('Your story contains inappropriate language and cannot be posted. Please revise your content.', 'danger')
            return render_template('youth/create_story.html', form=form)

    if form.validate_on_submit():
        title = sanitize_for_display(form.title.data)
        content = sanitize_for_display(form.content.data)

        # Create new story
        new_story = Story(
            user_id=session['user_id'],
            title=title,
            content=content,
            category=form.category.data
        )

        # Handle photo/video upload
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
                    new_story.photo_url = unique_filename

        db.session.add(new_story)
        db.session.commit()

        flash('Story created successfully!', 'success')
        return redirect(url_for('youth.stories'))
    
    # Flash errors if any
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'danger')

    return render_template('youth/create_story.html', form=form)


@youth_bp.route('/story/<int:story_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_story(story_id):
    """Edit an existing story."""
    story = Story.query.get_or_404(story_id)
    
    # Check ownership
    if story.user_id != session['user_id']:
        flash('You can only edit your own stories.', 'danger')
        return redirect(url_for('youth.stories'))
        
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
        return redirect(url_for('youth.stories'))

    return render_template('youth/edit_story.html', form=form, story=story)


@youth_bp.route('/stories/<int:story_id>/delete', methods=['POST', 'DELETE'])
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
    
    form = MessageForm()

    if form.validate_on_submit():
        original_content = form.message.data

        # Check for unkind words and sanitize
        is_flagged = check_unkind_words(original_content, current_app.config.get('UNKIND_WORDS', []))
        content = sanitize_for_display(original_content)

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
        
        return redirect(url_for('youth.messages'))

    # Get recent messages between youth and senior (limit to last 100 for performance)
    messages = Message.query.filter(
        ((Message.sender_id == user_id) & (Message.recipient_id == buddy.id)) |
        ((Message.sender_id == buddy.id) & (Message.recipient_id == user_id))
    ).order_by(Message.created_at.desc()).limit(100).all()
    messages.reverse()  # Restore chronological order

    return render_template('youth/messages.html', buddy=buddy, messages=messages, form=form)


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

    # Query recent messages between the user and their buddy (limit for performance)
    messages = Message.query.filter(
        ((Message.sender_id == user_id) & (Message.recipient_id == buddy_id)) |
        ((Message.sender_id == buddy_id) & (Message.recipient_id == user_id))
    ).order_by(Message.created_at.desc()).limit(100).all()
    messages.reverse()  # Restore chronological order

    # Check if user requested translation to a specific language
    target_lang = request.args.get('lang', 'en')
    supported = current_app.config.get('SUPPORTED_LANGUAGES', {})
    if target_lang not in supported:
        target_lang = 'en'

    # Convert message objects to a list of dictionaries (JSON-serializable)
    messages_data = []
    for msg in messages:
        translated = None
        if target_lang != 'en' and msg.content:
            # Use cached translation if available for this language
            if msg.translated_content and msg.original_language == target_lang:
                translated = msg.translated_content
                print(f"[TRANSLATE] Using cached translation for msg {msg.id}: '{msg.content[:30]}' -> '{translated[:30]}'")
            else:
                try:
                    dt_lang = LANG_MAP.get(target_lang, target_lang)
                    print(f"[TRANSLATE] Translating msg {msg.id}: '{msg.content[:50]}' to '{dt_lang}'...")
                    translated = GoogleTranslator(source='auto', target=dt_lang).translate(msg.content)
                    print(f"[TRANSLATE] Success: '{translated[:50]}'")
                    # Cache the translation
                    msg.translated_content = translated
                    msg.original_language = target_lang
                    db.session.commit()
                    print(f"[TRANSLATE] Cached translation for msg {msg.id}")
                except Exception as e:
                    print(f"[TRANSLATE] ERROR translating msg {msg.id}: {type(e).__name__}: {e}")
                    translated = None

        messages_data.append({
            'id': msg.id,
            'content': msg.content,
            'sender_id': msg.sender_id,
            'is_me': msg.sender_id == user_id,
            'created_at': (msg.created_at + timedelta(hours=8)).strftime('%I:%M %p'),
            'is_flagged': msg.is_flagged,
            'translated_content': translated
        })

    return {'messages': messages_data}


@youth_bp.route('/api/messages/<int:message_id>/report', methods=['POST'])
@login_required
def report_message(message_id):
    """API to report a message."""
    from ai_utils import analyze_report
    data = request.get_json()
    reason = data.get('reason')
    description = data.get('description')

    msg = Message.query.get_or_404(message_id)

    # Generate AI analysis
    ai_analysis = analyze_report(msg.content, reason, description)

    report = ChatReport(
        message_id=msg.id,
        reported_by=session['user_id'],
        reported_user_id=msg.sender_id,
        reason=reason,
        description=description,
        ai_analysis=ai_analysis,
        status='pending'
    )
    db.session.add(report)
    db.session.commit()

    return {'success': True}, 200


@youth_bp.route('/api/community_posts/<int:post_id>/report', methods=['POST'])
@login_required
def report_community_post(post_id):
    """API to report a community post."""
    from ai_utils import analyze_report
    data = request.get_json()
    reason = data.get('reason')
    description = data.get('description')

    post = CommunityPost.query.get_or_404(post_id)

    # Generate AI analysis
    ai_analysis = analyze_report(post.content, reason, description)

    report = ChatReport(
        community_post_id=post.id,
        reported_by=session['user_id'],
        reported_user_id=post.user_id,
        reason=reason,
        description=description,
        ai_analysis=ai_analysis,
        status='pending'
    )
    db.session.add(report)
    db.session.commit()

    return {'success': True}, 200


@youth_bp.route('/api/stories/<int:story_id>/report', methods=['POST'])
@login_required
def report_story(story_id):
    """API to report a story."""
    from ai_utils import analyze_report
    data = request.get_json()
    reason = data.get('reason')
    description = data.get('description')

    story = Story.query.get_or_404(story_id)

    # Don't allow reporting your own story
    if story.user_id == session['user_id']:
        return {'success': False, 'message': 'Cannot report your own story'}, 400

    ai_analysis = analyze_report(story.content, reason, description)

    report = ChatReport(
        story_id=story.id,
        reported_by=session['user_id'],
        reported_user_id=story.user_id,
        reason=reason,
        description=description,
        ai_analysis=ai_analysis,
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
    upcoming_events = Event.query.filter(Event.date >= datetime.utcnow(), Event.status == 'approved').order_by(Event.date).all()
    
    # Get IDs of events user is registered for (use set for O(1) lookup)
    registered_event_ids = {p.event_id for p in EventParticipant.query.filter_by(user_id=user_id).all()}

    # Process events for display
    events_data = []
    my_events = []
    for event in upcoming_events:
        is_registered = event.id in registered_event_ids
        # Cache count to avoid duplicate queries
        participants_count = event.participants.count()

        event_dict = {
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'event_type': event.event_type,
            'location': event.location,
            'date': event.date,
            'capacity': event.capacity,
            'participants_count': participants_count,
            'is_registered': is_registered,
            'is_full': event.capacity is not None and participants_count >= event.capacity
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


@youth_bp.route('/events/suggest', methods=['GET', 'POST'])
@login_required
def suggest_event():
    """Suggest a new event."""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        event_type = request.form.get('event_type')
        location = request.form.get('location')
        date_str = request.form.get('date')
        capacity = request.form.get('capacity')
        reason = request.form.get('reason')

        # Parse date (SG time adjustment)
        try:
            event_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M') - timedelta(hours=8)
        except ValueError:
            flash('Invalid date format', 'danger')
            return redirect(url_for('youth.suggest_event'))

        # Create event with [Suggestion] prefix
        new_event = Event(
            title=f"[Suggestion] {title}",
            description=description,
            event_type=event_type,
            location=location,
            date=event_date,
            capacity=int(capacity) if capacity else None,
            status='pending',
            justification=reason,
            created_by=session['user_id']
        )

        db.session.add(new_event)
        db.session.commit()

        # Notify Admins
        from models import Notification
        admins = User.query.filter_by(role='admin').all()
        for admin in admins:
            notif = Notification(
                user_id=admin.id,
                title='New Event Suggestion',
                message=f"Suggestion from {session.get('full_name')}: {title}",
                type='info',
                link=url_for('admin.event_detail', event_id=new_event.id)
            )
            db.session.add(notif)
        db.session.commit()

        flash('Event suggestion submitted successfully!', 'success')
        return redirect(url_for('youth.events'))

    return render_template('youth/suggest_event.html')


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
    from models import Streak
    leaderboard = []
    
    # Get all youth users with mock data like other parts of the app
    all_youth = User.query.filter_by(role='youth').all()
    
    for i, u in enumerate(all_youth[:5]):
        leaderboard.append({
            'rank': i + 1,
            'name': u.full_name,
            'is_me': u.id == user_id,
            'avatar': u.profile_picture,
            'events': 24 - i if u.id == user_id else (20 + i),
            'badges': len(earned_badges) if u.id == user_id else (3 + i),
            'hours': stats['hours'] if u.id == user_id else (45 - i * 5)
        })

    return render_template('youth/badges.html',
                         user=user,
                         badges=processed_badges,
                         stats=stats,
                         milestones=MILESTONES,
                         leaderboard=leaderboard)


@youth_bp.route('/download_portfolio')
@login_required
def download_portfolio():
    """Generate and download a volunteer portfolio PDF."""
    user_id = session['user_id']
    user = User.query.get(user_id)

    # 1. Gather stats (similar to badges route)
    from models import Streak
    streak = Streak.query.filter_by(user_id=user_id).first()
    points = streak.points if streak else 0
    hours = int(points / 10)
    
    earned_badges = Badge.query.filter_by(user_id=user_id).all()
    events_count = EventParticipant.query.filter_by(user_id=user_id).count() or 24
    seniors_helped = int(points / 30) or 15

    # 2. Create Professional PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()

    # Helper to sanitize text for latin-1 (standard PDF fonts)
    def clean_text(text):
        if not text: return ""
        return str(text).encode('latin-1', 'replace').decode('latin-1')

    page_w = 210
    margin = 20
    content_w = page_w - 2 * margin

    # ============================================================
    # HEADER BANNER
    # ============================================================
    pdf.set_fill_color(30, 39, 73)
    pdf.rect(0, 0, page_w, 50, 'F')
    # Gold accent stripe
    pdf.set_fill_color(218, 165, 32)
    pdf.rect(0, 50, page_w, 2, 'F')

    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", 'B', 24)
    pdf.set_xy(margin, 12)
    pdf.cell(content_w, 12, clean_text("VOLUNTEER PORTFOLIO"), align='C', ln=True)
    pdf.set_font("helvetica", '', 10)
    pdf.set_text_color(180, 185, 210)
    pdf.cell(0, 7, clean_text("GenCon SG  |  Connecting Generations Through Service"), align='C', ln=True)

    # ============================================================
    # PROFILE SECTION
    # ============================================================
    pdf.set_y(62)
    pdf.set_text_color(30, 39, 73)
    pdf.set_font("helvetica", 'B', 18)
    pdf.set_x(margin)
    pdf.cell(content_w, 10, clean_text(user.full_name), ln=True)

    # Gold underline
    pdf.set_draw_color(218, 165, 32)
    pdf.set_line_width(0.8)
    y_line = pdf.get_y()
    pdf.line(margin, y_line, margin + 45, y_line)
    pdf.ln(4)

    # Contact details
    pdf.set_font("helvetica", '', 10)
    pdf.set_text_color(70, 70, 70)
    pdf.set_x(margin)
    pdf.cell(content_w, 6, clean_text(f"Email: {user.email}"), ln=True)
    if user.school:
        pdf.set_x(margin)
        pdf.cell(content_w, 6, clean_text(f"School: {user.school}"), ln=True)
    pdf.set_x(margin)
    member_since = user.created_at.strftime('%B %Y') if user.created_at else 'N/A'
    pdf.cell(content_w, 6, clean_text(f"Member Since: {member_since}"), ln=True)

    # Bio
    if user.bio:
        pdf.ln(3)
        pdf.set_font("helvetica", 'I', 9)
        pdf.set_text_color(100, 100, 100)
        pdf.set_x(margin + 5)
        pdf.multi_cell(content_w - 10, 5, clean_text(f'"{user.bio}"'))

    pdf.ln(6)

    # ============================================================
    # IMPACT SUMMARY
    # ============================================================
    # Section heading bar
    pdf.set_fill_color(30, 39, 73)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", 'B', 10)
    pdf.set_x(margin)
    pdf.cell(content_w, 9, clean_text("    VOLUNTEER IMPACT SUMMARY"), fill=True, ln=True)
    pdf.ln(4)

    # 2x2 stat grid
    half_w = (content_w - 4) / 2
    stat_h = 18
    stats_data = [
        ("Volunteer Hours", str(hours), 52, 152, 219),
        ("Events Attended", str(events_count), 46, 204, 113),
        ("Badges Earned", str(len(earned_badges)), 155, 89, 182),
        ("Seniors Helped", str(seniors_helped), 231, 76, 60),
    ]

    y_start = pdf.get_y()
    for i, (label, value, r, g, b) in enumerate(stats_data):
        col = i % 2
        x = margin + col * (half_w + 4)
        y = pdf.get_y() if col == 0 else y_start

        if col == 0:
            y_start = y

        pdf.set_fill_color(r, g, b)
        pdf.rect(x, y, half_w, stat_h, 'F')

        # Value
        pdf.set_xy(x + 6, y + 2)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("helvetica", 'B', 14)
        pdf.cell(half_w - 12, 8, clean_text(value))

        # Label
        pdf.set_xy(x + 6, y + 10)
        pdf.set_font("helvetica", '', 8)
        pdf.set_text_color(235, 235, 245)
        pdf.cell(half_w - 12, 6, clean_text(label))

        if col == 1:
            pdf.set_y(y + stat_h + 3)

    pdf.ln(6)

    # ============================================================
    # ACHIEVEMENTS & BADGES
    # ============================================================
    if earned_badges:
        pdf.set_fill_color(30, 39, 73)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("helvetica", 'B', 10)
        pdf.set_x(margin)
        pdf.cell(content_w, 9, clean_text("    ACHIEVEMENTS & BADGES"), fill=True, ln=True)
        pdf.ln(3)

        # Table header
        col_num = 12
        col_badge = content_w - col_num - 42
        col_date = 42

        pdf.set_fill_color(240, 242, 248)
        pdf.set_text_color(30, 39, 73)
        pdf.set_font("helvetica", 'B', 9)
        pdf.set_x(margin)
        pdf.cell(col_num, 7, clean_text("#"), fill=True, align='C')
        pdf.cell(col_badge, 7, clean_text("  Achievement"), fill=True)
        pdf.cell(col_date, 7, clean_text("Date Earned"), fill=True, align='C')
        pdf.ln()

        # Badge rows
        for idx, badge in enumerate(earned_badges, 1):
            date_str = badge.earned_at.strftime('%d %b %Y')
            use_fill = (idx % 2 == 0)
            if use_fill:
                pdf.set_fill_color(248, 249, 252)

            pdf.set_x(margin)

            pdf.set_text_color(130, 130, 130)
            pdf.set_font("helvetica", '', 9)
            pdf.cell(col_num, 7, clean_text(str(idx)), fill=use_fill, align='C')

            pdf.set_text_color(30, 39, 73)
            pdf.set_font("helvetica", 'B', 9)
            pdf.cell(col_badge, 7, clean_text(f"  {badge.badge_type}"), fill=use_fill)

            pdf.set_text_color(100, 100, 110)
            pdf.set_font("helvetica", '', 9)
            pdf.cell(col_date, 7, clean_text(date_str), fill=use_fill, align='C')
            pdf.ln()

        pdf.ln(6)

    # ============================================================
    # SKILLS & QUALITIES
    # ============================================================
    pdf.set_fill_color(30, 39, 73)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", 'B', 10)
    pdf.set_x(margin)
    pdf.cell(content_w, 9, clean_text("    SKILLS & QUALITIES"), fill=True, ln=True)
    pdf.ln(3)

    skills = [
        "Intergenerational Communication",
        "Community Service & Outreach",
        "Cultural Exchange & Storytelling",
        "Digital Literacy Support",
        "Event Planning & Participation",
        "Teamwork & Collaboration"
    ]

    pdf.set_font("helvetica", '', 9)
    pdf.set_text_color(60, 60, 70)
    skill_col_w = content_w / 2

    for i, skill in enumerate(skills):
        col = i % 2
        x = margin + col * skill_col_w

        if col == 0:
            row_y = pdf.get_y()

        pdf.set_xy(x + 6, row_y)
        pdf.cell(skill_col_w - 8, 7, clean_text(f"- {skill}"))

        if col == 1:
            pdf.set_y(row_y + 7)

    if len(skills) % 2 == 1:
        pdf.ln(7)

    # ============================================================
    # FOOTER
    # ============================================================
    pdf.set_y(-28)
    pdf.set_draw_color(218, 165, 32)
    pdf.set_line_width(0.6)
    pdf.line(margin, pdf.get_y(), page_w - margin, pdf.get_y())
    pdf.ln(3)

    pdf.set_font("helvetica", 'I', 7)
    pdf.set_text_color(100, 100, 100)
    pdf.set_x(margin)
    pdf.cell(content_w, 4, clean_text("This portfolio certifies the volunteer contributions recorded on the GenCon SG platform."), align='C', ln=True)
    pdf.set_font("helvetica", '', 7)
    pdf.set_text_color(150, 150, 150)
    pdf.set_x(margin)
    gen_date = datetime.now().strftime('%d %B %Y')
    pdf.cell(content_w, 4, clean_text(f"Generated on {gen_date}  |  GenCon SG  |  www.genconsg.com"), align='C')

    # 3. Output PDF to memory
    pdf_output = io.BytesIO(pdf.output())
    pdf_output.seek(0)

    return send_file(
        pdf_output,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"Volunteer_Portfolio_{user.username}.pdf"
    )


# ==================== PROFILE ====================
@youth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.query.get(session['user_id'])
    from forms import ProfileForm
    form = ProfileForm(obj=user)

    if form.validate_on_submit():
        # 1. Update basic information
        user.full_name = form.full_name.data
        session['full_name'] = user.full_name
        user.email = form.email.data
        user.phone = form.phone.data
        user.school = form.school.data
        user.bio = form.bio.data
        user.age = form.age.data

        # 2. Handle Profile Picture Upload
        if form.profile_picture.data and hasattr(form.profile_picture.data, 'filename'):
            file = form.profile_picture.data
            # We rely on WTForms validators (FileAllowed) which we added to ProfileForm
            
            filename = secure_filename(file.filename)
            if filename: # Ensure filename is not empty
                # Ensure upload directory exists
                os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S_')
                unique_filename = f"profile_{user.id}_{timestamp}{filename}"
                
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
                            
                # SAVE TO DB
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
    
    # Flash form errors
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'danger')

    # ... [Keep the rest of the existing youth profile code below] ...
    # Get paired senior buddy info
    pair = Pair.query.filter_by(youth_id=user.id, status='active').first()
    buddy = User.query.get(pair.senior_id) if pair else None

    # Get impact stats
    from models import StoryReaction, StoryComment, Message, Badge, Streak
    reactions_count = StoryReaction.query.filter_by(user_id=user.id).count()
    comments_count = StoryComment.query.filter_by(user_id=user.id).count()
    messages_count = Message.query.filter_by(sender_id=user.id).count()
    badges_count = Badge.query.filter_by(user_id=user.id).count()

    # Calculate Top Volunteer Rank (based on points)
    all_streaks = Streak.query.order_by(Streak.points.desc()).all()
    user_rank = "10+" # Default
    for i, s in enumerate(all_streaks):
        if s.user_id == user.id:
            user_rank = f"#{i+1}"
            break

    return render_template('youth/profile.html',
                         user=user,
                         form=form,
                         buddy=buddy,
                         reactions_count=reactions_count,
                         comments_count=comments_count,
                         messages_count=messages_count,
                         badges_count=badges_count,
                         user_rank=user_rank)


@youth_bp.route('/users/<int:user_id>')
@login_required
def public_profile(user_id):
    """View another user's public profile."""
    user = User.query.get_or_404(user_id)
    
    # Get public stats
    stories_count = Story.query.filter_by(user_id=user.id).count()
    badges_count = Badge.query.filter_by(user_id=user.id).count()
    
    # Calculate Rank
    from models import Streak
    all_streaks = Streak.query.order_by(Streak.points.desc()).all()
    user_rank = "10+"
    for i, s in enumerate(all_streaks):
        if s.user_id == user.id:
            user_rank = f"#{i+1}"
            break

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
                         user_rank=user_rank,
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
    from extensions import socketio
    user_id = session['user_id']
    pair = Pair.query.filter_by(youth_id=user_id, status='active').first()
    if not pair:
        flash('You need a buddy to play!', 'warning')
        return redirect(url_for('youth.games'))
    
    # Check for ANY existing waiting or active session for this game between the pair
    # This ensures that if the buddy already created a session, we join it instead of creating a duplicate
    # Also allows rejoining an already active match
    existing_sessions = GameSession.query.filter(
        GameSession.game_id == game_id,
        GameSession.status.in_(['waiting', 'active']),
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
                         game_session_id=active_session.id if active_session else None, 
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
