"""
blueprints/main.py — Main (public) routes, context processor, template filters,
security headers, and error handlers.

Extracted from app.py so that app.py stays thin and focused on app creation.
"""

from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from datetime import datetime, timedelta
from extensions import db
from forms import LoginForm, RegistrationForm

main_bp = Blueprint('main', __name__)


# ==================== CONTEXT PROCESSOR ====================

@main_bp.app_context_processor
def inject_user():
    """Make session + streak data available to all templates."""
    user_streak = 0
    if 'user_id' in session:
        from models import Streak
        streak = Streak.query.filter_by(user_id=session['user_id']).first()
        if streak:
            user_streak = streak.current_streak
    return dict(session=session, user_streak=user_streak)


# ==================== TEMPLATE FILTERS ====================

@main_bp.app_template_filter('timeago')
def timeago_filter(date):
    """Convert datetime to relative time string (e.g., '2 hours ago')."""
    now = datetime.utcnow()
    diff = now - date
    seconds = diff.total_seconds()

    if seconds < 60:
        return 'Just now'
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f'{minutes} minute{"s" if minutes != 1 else ""} ago'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours} hour{"s" if hours != 1 else ""} ago'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{days} day{"s" if days != 1 else ""} ago'
    else:
        return (date + timedelta(hours=8)).strftime('%B %d, %Y')


@main_bp.app_template_filter('format_date')
def format_date_filter(date, format='%B %d, %Y'):
    """Format datetime object to string."""
    if date:
        return (date + timedelta(hours=8)).strftime(format)
    return ''


@main_bp.app_template_filter('date')
def date_filter(value, format='%B %d, %Y'):
    """Custom date filter; accepts a datetime object or the string 'now'."""
    if value == "now":
        value = datetime.utcnow() + timedelta(hours=8)
    elif value:
        value = value + timedelta(hours=8)
    if value:
        return value.strftime(format)
    return ''


@main_bp.app_template_filter('fix_pfp')
def fix_pfp_filter(path):
    """Ensure profile picture path has correct prefix."""
    if not path:
        return 'images/default-avatar.png'
    if path.startswith('images/') or path.startswith('http'):
        return path
    return f'images/{path}'


# ==================== SECURITY HEADERS ====================

@main_bp.after_app_request
def add_security_headers(response):
    """Add Content-Security-Policy to every response (skip /profolio)."""
    if request.path.startswith('/profolio'):
        return response

    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' blob: https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://accounts.google.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com https://accounts.google.com; "
        "font-src 'self' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://fonts.gstatic.com; "
        "img-src 'self' data: blob: https:; "
        "connect-src 'self' ws: wss: https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://accounts.google.com; "
        "frame-src https://accounts.google.com; "
        "worker-src 'self' blob:;"
    )
    response.headers['Content-Security-Policy'] = csp
    return response


# ==================== ERROR HANDLERS ====================

@main_bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@main_bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500


@main_bp.app_errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403


# ==================== MAIN ROUTES ====================

@main_bp.route('/')
def index():
    """Landing page — redirect logged-in users to their dashboard."""
    if 'user_id' in session:
        role = session.get('role')
        if role == 'senior':
            return redirect(url_for('senior.dashboard'))
        elif role == 'youth':
            return redirect(url_for('youth.dashboard'))
        elif role == 'admin':
            return redirect(url_for('admin.dashboard'))
    google_pending = session.get('google_pending')
    return render_template('index.html',
                           login_form=LoginForm(),
                           register_form=RegistrationForm(),
                           google_pending=google_pending)


@main_bp.route('/support', methods=['GET', 'POST'])
def support():
    """Public support ticket submission page."""
    from forms import SupportTicketForm
    from models import SupportTicket

    form = SupportTicketForm()

    if form.validate_on_submit():
        ticket = SupportTicket(
            ticket_type=form.ticket_type.data,
            subject=form.subject.data,
            description=form.description.data
        )

        if 'user_id' in session:
            ticket.user_id = session['user_id']
        else:
            if not form.guest_email.data:
                flash('Email is required for guest submissions.', 'danger')
                return render_template('support.html', form=form)
            ticket.guest_email = form.guest_email.data

        db.session.add(ticket)
        db.session.commit()
        flash(
            f'Your support ticket #{ticket.id} has been submitted successfully! We will get back to you soon.',
            'success'
        )
        return redirect(url_for('main.support'))

    return render_template('support.html', form=form)


@main_bp.route('/about')
def about():
    return render_template('about.html')


@main_bp.route('/privacy')
def privacy():
    return render_template('privacy.html')


@main_bp.route('/terms')
def terms():
    return render_template('terms.html')


@main_bp.route('/favicon.ico')
def favicon():
    from flask import current_app
    return current_app.send_static_file('images/default-avatar.png')


# ==================== NOTIFICATION API ====================

@main_bp.route('/api/notifications')
def get_notifications():
    if 'user_id' not in session:
        return {'count': 0, 'notifications': []}

    from models import Notification
    user_id = session['user_id']
    notifs = Notification.query.filter_by(user_id=user_id, is_read=False)\
        .order_by(Notification.created_at.desc()).all()

    return {
        'count': len(notifs),
        'notifications': [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.type,
            'link': n.link,
            'timeAgo': timeago_filter(n.created_at)
        } for n in notifs]
    }


@main_bp.route('/api/notifications/<int:notification_id>/dismiss', methods=['POST'])
def dismiss_notification(notification_id):
    if 'user_id' not in session:
        return {'success': False}, 403

    from models import Notification
    notif = Notification.query.get_or_404(notification_id)

    if notif.user_id != session['user_id']:
        return {'success': False}, 403

    notif.is_read = True
    db.session.commit()
    return {'success': True}


@main_bp.route('/api/notifications/mark-read', methods=['POST'])
def mark_all_notifications_read():
    if 'user_id' not in session:
        return {'success': False}, 403

    from models import Notification
    user_id = session['user_id']
    Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()
    return {'success': True}


# ==================== STREAK API ====================

@main_bp.route('/api/streak')
def get_streak():
    """Get user's current streak status."""
    if 'user_id' not in session:
        return {'currentStreak': 0}

    from models import Streak
    user_id = session['user_id']
    streak = Streak.query.filter_by(user_id=user_id).first()

    if not streak:
        return {'currentStreak': 0}

    return {
        'currentStreak': streak.current_streak,
        'points': streak.points,
        'newBadge': None,
        'dailyReward': False
    }
