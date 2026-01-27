"""
File: admin.py
Purpose: Admin routes blueprint
Author: to be assigned
Date: December 2025
Features: Admin Dashboard, User Management, Pair Management, Event Management,
          Community Management, Report Review
Description: Handles all administrative functions including user moderation,
             pair monitoring, event creation, and chat report management
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from models import db, User, Pair, Event, Community, ChatReport, Story, Message, CommunityPost, CommunityMember, RegistrationCode, EventParticipant
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.utils import secure_filename
import os

# Create admin blueprint
admin_bp = Blueprint('admin', __name__)


# ==================== AUTHENTICATION DECORATOR ====================
def admin_required(f):
    """
    Decorator to require admin login for routes.
    Ensures user is logged in and is an admin.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('auth.login', role='admin'))
        if session.get('role') != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# ==================== DASHBOARD ====================
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """
    Admin dashboard with key metrics and alerts.
    Shows user counts, active pairs, pending reports, and system health.
    """
    # Get user statistics (Active Seniors and Youth)
    total_seniors = User.query.filter_by(role='senior', is_active=True).count()
    total_youth = User.query.filter_by(role='youth', is_active=True).count()

    # Get pair statistics (Active connections)
    active_pairs = Pair.query.filter_by(status='active').count()

    # Get pending reports requiring attention
    pending_reports = ChatReport.query.filter_by(status='pending').count()

    # Get recent activity for the feed
    recent_stories = Story.query.order_by(Story.created_at.desc()).limit(5).all()
    recent_users = User.query.filter(User.role != 'admin')\
        .order_by(User.created_at.desc()).limit(5).all()

    # Get inactive pairs (no interaction in 7 days) to show warnings
    inactive_threshold = datetime.utcnow() - timedelta(days=7)
    inactive_pairs = Pair.query.filter(
        Pair.status == 'active',
        Pair.last_interaction < inactive_threshold
    ).count()

    return render_template('admin/dashboard.html',
                         total_seniors=total_seniors,
                         total_youth=total_youth,
                         active_pairs=active_pairs,
                         pending_reports=pending_reports,
                         inactive_pairs=inactive_pairs,
                         recent_stories=recent_stories,
                         recent_users=recent_users)


# ==================== USER MANAGEMENT ====================
@admin_bp.route('/users')
@admin_required
def users():
    """Display all users with filtering options."""
    # Get filter parameters
    role_filter = request.args.get('role', 'all')
    status_filter = request.args.get('status', 'all')

    # Build query
    query = User.query.filter(User.role != 'admin')

    if role_filter != 'all':
        query = query.filter_by(role=role_filter)

    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)

    users = query.order_by(User.created_at.desc()).all()

    return render_template('admin/users.html',
                         users=users,
                         role_filter=role_filter,
                         status_filter=status_filter)


@admin_bp.route('/users/<int:user_id>')
@admin_required
def user_detail(user_id):
    """View detailed user information."""
    user = User.query.get_or_404(user_id)

    # Get user statistics
    if user.role == 'senior':
        stories_count = Story.query.filter_by(user_id=user.id).count()
        pair = Pair.query.filter_by(senior_id=user.id, status='active').first()
    else:
        stories_count = 0
        pair = Pair.query.filter_by(youth_id=user.id, status='active').first()

    messages_sent = Message.query.filter_by(sender_id=user.id).count()

    return render_template('admin/user_detail.html',
                         user=user,
                         stories_count=stories_count,
                         messages_sent=messages_sent,
                         pair=pair)


@admin_bp.route('/users/<int:user_id>/toggle_status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    """Enable or disable a user account."""
    user = User.query.get_or_404(user_id)
    
    # Toggle status
    user.is_active = not user.is_active
    
    if not user.is_active:
        # If disabling, save the reason
        reason = request.form.get('reason', 'No reason provided')
        user.disable_reason = reason
        flash(f'User {user.username} has been disabled.', 'warning')
    else:
        # If enabling, clear the reason
        user.disable_reason = None
        flash(f'User {user.username} has been reactivated.', 'success')
        
    db.session.commit()
    return redirect(url_for('admin.user_detail', user_id=user.id))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Permanently delete a user account."""
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting yourself
    if user.id == session['user_id']:
        flash('You cannot delete your own admin account.', 'danger')
        return redirect(url_for('admin.user_detail', user_id=user.id))
        
    try:
        # 1. Delete or unlink dependencies (Optional but recommended)
        # SQLAlchemy 'cascade' usually handles this if configured, 
        # but manual cleanup is safer for complex relationships.
        
        # 2. Delete the user
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        flash(f'User {username} has been permanently deleted.', 'success')
        return redirect(url_for('admin.users'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Delete error: {e}")
        flash('Error deleting user. Ensure all related records are cleared.', 'danger')
        return redirect(url_for('admin.user_detail', user_id=user.id))

# ==================== PAIR MANAGEMENT ====================
@admin_bp.route('/pairs')
@admin_required
def pairs():
    """Display all buddy pairs with health monitoring."""
    # Get all active pairs
    all_pairs = Pair.query.order_by(Pair.paired_date.desc()).all()

    # Calculate interaction health for each pair
    inactive_threshold = datetime.utcnow() - timedelta(days=7)
    warning_threshold = datetime.utcnow() - timedelta(days=3)

    pairs_data = []
    for pair in all_pairs:
        # Get message count between pair
        message_count = Message.query.filter(
            ((Message.sender_id == pair.senior_id) & (Message.recipient_id == pair.youth_id)) |
            ((Message.sender_id == pair.youth_id) & (Message.recipient_id == pair.senior_id))
        ).count()

        # Determine health status
        if pair.last_interaction < inactive_threshold:
            health = 'critical'
        elif pair.last_interaction < warning_threshold:
            health = 'warning'
        else:
            health = 'good'

        pairs_data.append({
            'pair': pair,
            'message_count': message_count,
            'health': health
        })

    return render_template('admin/pairs.html', pairs_data=pairs_data)


@admin_bp.route('/pairs/create', methods=['GET', 'POST'])
@admin_required
def create_pair():
    """Create a new buddy pair."""
    if request.method == 'POST':
        senior_id = request.form.get('senior_id')
        youth_id = request.form.get('youth_id')
        program = request.form.get('program')

        # Validate
        if not all([senior_id, youth_id]):
            flash('Please select both a senior and youth volunteer', 'danger')
            return redirect(url_for('admin.create_pair'))

        # Create pair
        new_pair = Pair(
            senior_id=senior_id,
            youth_id=youth_id,
            program=program
        )

        db.session.add(new_pair)
        db.session.commit()

        flash('Buddy pair created successfully!', 'success')
        return redirect(url_for('admin.pairs'))

    # Get unpaired seniors and youth
    unpaired_seniors = User.query.filter(
        User.role == 'senior',
        ~User.id.in_(db.session.query(Pair.senior_id).filter_by(status='active'))
    ).all()

    unpaired_youth = User.query.filter(
        User.role == 'youth',
        ~User.id.in_(db.session.query(Pair.youth_id).filter_by(status='active'))
    ).all()

    return render_template('admin/create_pair.html',
                         unpaired_seniors=unpaired_seniors,
                         unpaired_youth=unpaired_youth)


@admin_bp.route('/pairs/<int:pair_id>/delete', methods=['POST'])
@admin_required
def delete_pair(pair_id):
    """Permanently delete a buddy pair."""
    pair = Pair.query.get_or_404(pair_id)
    try:
        db.session.delete(pair)
        db.session.commit()
        flash('Buddy pair has been removed.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error removing pair.', 'danger')
    return redirect(url_for('admin.pairs'))


@admin_bp.route('/pairs/<int:pair_id>/remind', methods=['POST'])
@admin_required
def send_pair_reminder(pair_id):
    """Send a reminder to a pair (Mock interaction update)."""
    pair = Pair.query.get_or_404(pair_id)
    # In a real app, this would send an email or push notification.
    # For this project, we'll update the interaction time to show it was "handled".
    pair.last_interaction = datetime.utcnow()
    db.session.commit()
    flash(f'Reminder sent to {pair.senior.full_name} and {pair.youth.full_name}.', 'info')
    return redirect(url_for('admin.pairs'))


# ==================== EVENT MANAGEMENT ====================
@admin_bp.route('/events')
@admin_required
def events():
    """Display all events."""
    all_events = Event.query.order_by(Event.date.desc()).all()

    return render_template('admin/events.html', events=all_events, now=datetime.utcnow())


@admin_bp.route('/events/<int:event_id>')
@admin_required
def event_detail(event_id):
    """View event details and participants."""
    event = Event.query.get_or_404(event_id)
    
    # Fetch participants by joining User and EventParticipant tables
    participants = User.query.join(EventParticipant).filter(
        EventParticipant.event_id == event.id
    ).all()
    
    return render_template('admin/event_detail.html', 
                         event=event, 
                         participants=participants,
                         now=datetime.utcnow())


@admin_bp.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_event(event_id):
    """Edit an existing event."""
    event = Event.query.get_or_404(event_id)
    
    if request.method == 'POST':
        event.title = request.form.get('title')
        event.description = request.form.get('description')
        event.event_type = request.form.get('event_type')
        event.location = request.form.get('location')
        
        date_str = request.form.get('date')
        if date_str:
            # Parse date (assuming input is SG time, convert to UTC)
            event.date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M') - timedelta(hours=8)
        
        capacity = request.form.get('capacity')
        event.capacity = int(capacity) if capacity and capacity.strip() else None
        
        db.session.commit()
        flash('Event updated successfully!', 'success')
        return redirect(url_for('admin.event_detail', event_id=event.id))
    
    # Prepare date for datetime-local input (SG time)
    current_date_str = (event.date + timedelta(hours=8)).strftime('%Y-%m-%dT%H:%M')
    return render_template('admin/edit_event.html', event=event, current_date_str=current_date_str)


@admin_bp.route('/events/create', methods=['GET', 'POST'])
@admin_required
def create_event():
    """Create a new event."""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        event_type = request.form.get('event_type')
        location = request.form.get('location')
        date_str = request.form.get('date')
        capacity = request.form.get('capacity')

        # Parse date
        event_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M') - timedelta(hours=8)

        # Create event
        new_event = Event(
            title=title,
            description=description,
            event_type=event_type,
            location=location,
            date=event_date,
            capacity=int(capacity) if capacity else None,
            created_by=session['user_id']
        )

        db.session.add(new_event)
        db.session.commit()

        flash('Event created successfully!', 'success')
        return redirect(url_for('admin.events'))

    return render_template('admin/create_event.html')


@admin_bp.route('/events/<int:event_id>/delete', methods=['POST'])
@admin_required
def delete_event(event_id):
    """Delete an event."""
    event = Event.query.get_or_404(event_id)
    try:
        db.session.delete(event)
        db.session.commit()
        flash('Event deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting event. It may have active participants.', 'danger')
    return redirect(url_for('admin.events'))


# ==================== COMMUNITY MANAGEMENT ====================
@admin_bp.route('/communities')
@admin_required
def communities():
    """Display all communities."""
    all_communities = Community.query.order_by(Community.created_at.desc()).all()

    return render_template('admin/communities.html', communities=all_communities)


@admin_bp.route('/communities/create', methods=['GET', 'POST'])
@admin_required
def create_community():
    """Create a new community."""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        comm_type = request.form.get('type')
        icon = request.form.get('icon')
        banner_class = request.form.get('banner_class')
        tags = request.form.get('tags')

        if Community.query.filter_by(name=name).first():
            flash('Community with this name already exists', 'danger')
            return redirect(url_for('admin.create_community'))

        # Handle photo upload
        photo_url = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                if ext in current_app.config['ALLOWED_EXTENSIONS']:
                    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                    
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S_')
                    unique_filename = f"comm_new_{timestamp}{filename}"
                    
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
                    photo_url = f"images/uploads/{unique_filename}"

        new_community = Community(
            name=name,
            description=description,
            type=comm_type,
            icon=icon,
            banner_class=banner_class,
            tags=tags,
            photo_url=photo_url,
            created_by=session['user_id']
        )

        db.session.add(new_community)
        db.session.commit()

        flash('Community created successfully!', 'success')
        return redirect(url_for('admin.communities'))

    return render_template('admin/create_community.html')


@admin_bp.route('/communities/<int:community_id>/delete', methods=['POST'])
@admin_required
def delete_community(community_id):
    """Delete a community."""
    community = Community.query.get_or_404(community_id)
    
    try:
        # Clean up photo if exists
        if community.photo_url:
            try:
                old_filename = os.path.basename(community.photo_url)
                old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], old_filename)
                if os.path.exists(old_path):
                    os.remove(old_path)
            except Exception:
                pass

        db.session.delete(community)
        db.session.commit()
        flash('Community deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting community. It may have active members or posts.', 'danger')
        
    return redirect(url_for('admin.communities'))


@admin_bp.route('/communities/<int:community_id>/manage')
@admin_required
def manage_community(community_id):
    """Manage community: monitor chat and members."""
    community = Community.query.get_or_404(community_id)
    
    # Get chat history
    posts = CommunityPost.query.filter_by(community_id=community_id)\
        .order_by(CommunityPost.created_at.desc()).all()
        
    # Get members
    members = community.members.all()
    member_user_ids = [m.user_id for m in members]
    
    # Get non-members for the "Add Member" dropdown
    if member_user_ids:
        non_members = User.query.filter(User.role != 'admin', ~User.id.in_(member_user_ids)).all()
    else:
        non_members = User.query.filter(User.role != 'admin').all()
        
    return render_template('admin/manage_community.html', 
                           community=community, 
                           posts=posts, 
                           members=members,
                           non_members=non_members)


@admin_bp.route('/communities/<int:community_id>/update', methods=['POST'])
@admin_required
def update_community(community_id):
    """Update community details."""
    community = Community.query.get_or_404(community_id)
    
    # Update text fields
    community.name = request.form.get('name')
    community.description = request.form.get('description')
    community.type = request.form.get('type')
    community.banner_class = request.form.get('banner_class')
    community.icon = request.form.get('icon')
    community.tags = request.form.get('tags')
    
    # Handle photo upload
    if 'photo' in request.files:
        file = request.files['photo']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            if ext in current_app.config['ALLOWED_EXTENSIONS']:
                os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                # Clean up old photo if exists
                if community.photo_url:
                    try:
                        old_filename = os.path.basename(community.photo_url)
                        old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], old_filename)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    except Exception:
                        pass

                timestamp = datetime.now().strftime('%Y%m%d%H%M%S_')
                unique_filename = f"comm_{community.id}_{timestamp}{filename}"
                
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
                community.photo_url = f"images/uploads/{unique_filename}"

    try:
        db.session.commit()
        flash('Community updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating community. Name might already be taken.', 'danger')
        
    return redirect(url_for('admin.manage_community', community_id=community_id))


@admin_bp.route('/communities/posts/<int:post_id>/delete', methods=['POST'])
@admin_required
def delete_community_post(post_id):
    """Delete a message from the community chat."""
    post = CommunityPost.query.get_or_404(post_id)
    community_id = post.community_id
    
    db.session.delete(post)
    db.session.commit()
    
    flash('Message deleted successfully.', 'success')
    return redirect(url_for('admin.manage_community', community_id=community_id))


@admin_bp.route('/communities/<int:community_id>/members/<int:user_id>/remove', methods=['POST'])
@admin_required
def remove_community_member(community_id, user_id):
    """Remove a user from the community."""
    member = CommunityMember.query.filter_by(community_id=community_id, user_id=user_id).first_or_404()
    
    db.session.delete(member)
    community = Community.query.get(community_id)
    community.member_count = max(0, community.member_count - 1)
    db.session.commit()
    
    flash('Member removed from community.', 'success')
    return redirect(url_for('admin.manage_community', community_id=community_id))


@admin_bp.route('/communities/<int:community_id>/members/add', methods=['POST'])
@admin_required
def add_community_member(community_id):
    """Add a user to the community."""
    user_id = request.form.get('user_id')
    if user_id:
        # Logic reuses the join_community logic but forced by admin
        # We can just create the record directly
        if not CommunityMember.query.filter_by(community_id=community_id, user_id=user_id).first():
            new_member = CommunityMember(community_id=community_id, user_id=user_id)
            db.session.add(new_member)
            
            community = Community.query.get(community_id)
            community.member_count += 1
            db.session.commit()
            flash('User added to community.', 'success')
        else:
            flash('User is already a member.', 'warning')
            
    return redirect(url_for('admin.manage_community', community_id=community_id))


# ==================== REPORT MANAGEMENT ====================
@admin_bp.route('/reports')
@admin_required
def reports():
    """Display all chat reports for review."""
    # Get filter parameter
    status_filter = request.args.get('status', 'pending')

    # Query reports
    query = ChatReport.query

    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    all_reports = query.order_by(ChatReport.created_at.desc()).all()

    return render_template('admin/reports.html',
                         reports=all_reports,
                         status_filter=status_filter)


@admin_bp.route('/reports/<int:report_id>', methods=['GET', 'POST'])
@admin_required
def report_detail(report_id):
    """View and manage individual report."""
    report = ChatReport.query.get_or_404(report_id)

    if request.method == 'POST':
        action = request.form.get('action')
        admin_notes = request.form.get('admin_notes')

        if action == 'resolve':
            report.status = 'resolved'
            flash('Report marked as resolved', 'success')
        elif action == 'dismiss':
            report.status = 'dismissed'
            flash('Report dismissed', 'info')
        elif action == 'under_review':
            report.status = 'under_review'
            flash('Report marked as under review', 'info')

        report.admin_notes = admin_notes
        db.session.commit()

        return redirect(url_for('admin.reports'))

    # Get conversation history (last 20 messages between the two users)
    sender_id = report.message.sender_id
    recipient_id = report.message.recipient_id
    
    conversation_history = Message.query.filter(
        ((Message.sender_id == sender_id) & (Message.recipient_id == recipient_id)) |
        ((Message.sender_id == recipient_id) & (Message.recipient_id == sender_id))
    ).order_by(Message.created_at.desc()).limit(20).all()
    
    # Reverse to show chronological order
    conversation_history.reverse()

    return render_template('admin/report_detail.html', report=report, history=conversation_history)


# ==================== ANALYTICS ====================
@admin_bp.route('/analytics')
@admin_required
def analytics():
    """
    Display platform analytics and insights.
    Aggregates data across users, stories, messages, and pairs to provide
    a comprehensive view of platform usage and health.
    """
    # Calculate various metrics

    # User growth: Total non-admin users and new signups in last 30 days
    total_users = User.query.filter(User.role != 'admin').count()
    new_users_this_month = User.query.filter(
        User.role != 'admin',
        User.created_at >= datetime.utcnow() - timedelta(days=30)
    ).count()

    # User Breakdown by Role
    total_seniors = User.query.filter_by(role='senior').count()
    total_youth = User.query.filter_by(role='youth').count()
    total_admins = User.query.filter_by(role='admin').count()

    # Active Users (users with activity in last 30 days)
    active_users_30d = User.query.filter(
        User.last_active >= datetime.utcnow() - timedelta(days=30)
    ).count()

    # Inactive Users (users not active in 30 days or never active)
    # Note: total_users calculation above excludes admins, but active_users_30d might include them if not filtered.
    # To be consistent with "User Breakdown" card which usually sums up to total users visible.
    # Let's count inactive based on role != admin to match total_users.
    inactive_users = User.query.filter(
        User.role != 'admin',
        (User.last_active < datetime.utcnow() - timedelta(days=30)) | (User.last_active == None)
    ).count()

    # Engagement metrics (Total content created)
    total_stories = Story.query.count()
    total_messages = Message.query.count()

    # Pair health metrics
    total_pairs = Pair.query.count()
    active_pairs = Pair.query.filter_by(status='active').count()
    
    # Inactive pairs (active status but no interaction in 7 days)
    inactive_threshold = datetime.utcnow() - timedelta(days=7)
    inactive_pairs_count = Pair.query.filter(
        Pair.status == 'active',
        Pair.last_interaction < inactive_threshold
    ).count()

    # Reports and Moderation stats
    pending_reports_count = ChatReport.query.filter_by(status='pending').count()
    resolved_reports = ChatReport.query.filter_by(status='resolved').count()
    total_reports = ChatReport.query.count()
    # Calculate resolution rate percentage
    resolution_rate = int((resolved_reports / total_reports * 100)) if total_reports > 0 else 100

    return render_template('admin/analytics.html',
                         total_users=total_users,
                         new_users_this_month=new_users_this_month,
                         total_stories=total_stories,
                         total_messages=total_messages,
                         total_pairs=total_pairs,
                         active_pairs=active_pairs,
                         total_seniors=total_seniors,
                         total_youth=total_youth,
                         total_admins=total_admins,
                         active_users_30d=active_users_30d,
                         inactive_users=inactive_users,
                         inactive_pairs_count=inactive_pairs_count,
                         pending_reports_count=pending_reports_count,
                         resolution_rate=resolution_rate)


# ==================== REGISTRATION CODES ====================
@admin_bp.route('/codes', methods=['GET', 'POST'])
@admin_required
def codes():
    """Manage registration codes."""
    if request.method == 'POST':
        import random
        import string
        
        # Generate random 8-character code
        chars = string.ascii_uppercase + string.digits
        code = ''.join(random.choices(chars, k=8))
        
        # Ensure uniqueness
        while RegistrationCode.query.filter_by(code=code).first():
            code = ''.join(random.choices(chars, k=8))
            
        new_code = RegistrationCode(code=code)
        db.session.add(new_code)
        db.session.commit()
        
        flash(f'New code generated: {code}', 'success')
        return redirect(url_for('admin.codes'))
        
    # Get all codes
    all_codes = RegistrationCode.query.order_by(RegistrationCode.created_at.desc()).all()
    
    return render_template('admin/codes.html', codes=all_codes)


# ==================== ADMIN PROFILE ====================
@admin_bp.route('/profile')
@admin_required
def profile():
    """Admin profile page."""
    user = User.query.get(session['user_id'])
    return render_template('admin/profile.html', user=user)
