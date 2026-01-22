"""
File: admin.py
Purpose: Admin routes blueprint
Author: Asher
Date: December 2025
Features: Admin Dashboard, User Management, Pair Management, Event Management,
          Community Management, Report Review
Description: Handles all administrative functions including user moderation,
             pair monitoring, event creation, and chat report management
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, User, Pair, Event, Community, ChatReport, Story, Message
from datetime import datetime, timedelta
from functools import wraps

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
    # Get user statistics
    total_seniors = User.query.filter_by(role='senior', is_active=True).count()
    total_youth = User.query.filter_by(role='youth', is_active=True).count()

    # Get pair statistics
    active_pairs = Pair.query.filter_by(status='active').count()

    # Get pending reports
    pending_reports = ChatReport.query.filter_by(status='pending').count()

    # Get recent activity
    recent_stories = Story.query.order_by(Story.created_at.desc()).limit(5).all()
    recent_users = User.query.filter(User.role != 'admin')\
        .order_by(User.created_at.desc()).limit(5).all()

    # Get inactive pairs (no interaction in 7 days)
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

# --- CORRECTION: These routes must be un-indented (aligned to the left) ---

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


# ==================== EVENT MANAGEMENT ====================
@admin_bp.route('/events')
@admin_required
def events():
    """Display all events."""
    all_events = Event.query.order_by(Event.date.desc()).all()

    return render_template('admin/events.html', events=all_events, now=datetime.utcnow())


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
        event_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')

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


# ==================== COMMUNITY MANAGEMENT ====================
@admin_bp.route('/communities')
@admin_required
def communities():
    """Display all communities."""
    all_communities = Community.query.order_by(Community.created_at.desc()).all()

    return render_template('admin/communities.html', communities=all_communities)


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

    return render_template('admin/report_detail.html', report=report)


# ==================== ANALYTICS ====================
@admin_bp.route('/analytics')
@admin_required
def analytics():
    """Display platform analytics and insights."""
    # Calculate various metrics

    # User growth
    total_users = User.query.filter(User.role != 'admin').count()
    new_users_this_month = User.query.filter(
        User.role != 'admin',
        User.created_at >= datetime.utcnow() - timedelta(days=30)
    ).count()

    # User Breakdown
    total_seniors = User.query.filter_by(role='senior').count()
    total_youth = User.query.filter_by(role='youth').count()
    total_admins = User.query.filter_by(role='admin').count()

    # Active Users (last 30 days)
    active_users_30d = User.query.filter(
        User.last_active >= datetime.utcnow() - timedelta(days=30)
    ).count()

    # Inactive Users (users not active in 30 days)
    # Note: total_users calculation above excludes admins, but active_users_30d might include them if not filtered.
    # To be consistent with "User Breakdown" card which usually sums up to total users visible.
    # Let's count inactive based on role != admin to match total_users.
    inactive_users = User.query.filter(
        User.role != 'admin',
        (User.last_active < datetime.utcnow() - timedelta(days=30)) | (User.last_active == None)
    ).count()

    # Engagement metrics
    total_stories = Story.query.count()
    total_messages = Message.query.count()

    # Pair health
    total_pairs = Pair.query.count()
    active_pairs = Pair.query.filter_by(status='active').count()
    
    # Inactive pairs (no interaction in 7 days)
    inactive_threshold = datetime.utcnow() - timedelta(days=7)
    inactive_pairs_count = Pair.query.filter(
        Pair.status == 'active',
        Pair.last_interaction < inactive_threshold
    ).count()

    # Reports
    pending_reports_count = ChatReport.query.filter_by(status='pending').count()
    resolved_reports = ChatReport.query.filter_by(status='resolved').count()
    total_reports = ChatReport.query.count()
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


# ==================== ADMIN PROFILE ====================
@admin_bp.route('/profile')
@admin_required
def profile():
    """Admin profile page."""
    user = User.query.get(session['user_id'])
    return render_template('admin/profile.html', user=user)
