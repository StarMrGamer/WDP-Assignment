"""
File: app.py
Purpose: Main Flask application initialization for GenCon SG
Author: Rai (Team Lead)
Date: December 2025
Description: This is the entry point for the Flask application. It:
             - Initializes Flask app with configuration
             - Sets up SQLAlchemy database
             - Registers blueprints (auth, senior, youth, admin)
             - Configures session management
             - Creates database tables on first run
             - Provides the main route (index/landing page)
"""

from flask import Flask, render_template, session, redirect, url_for
from config import get_config
from models import db
import os

# Initialize Flask application
# __name__ tells Flask where to look for templates and static files
app = Flask(__name__)

# Load configuration from config.py
# Uses 'development' config by default, can be changed via FLASK_ENV environment variable
config_name = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(get_config(config_name))

# Initialize database with app
# This connects SQLAlchemy to our Flask app
db.init_app(app)


# ==================== BLUEPRINT REGISTRATION ====================
# Blueprints organize routes into modules (auth, senior, youth, admin)
# Each blueprint handles routes for its specific user role

from blueprints.auth import auth_bp
from blueprints.senior import senior_bp
from blueprints.youth import youth_bp
from blueprints.admin import admin_bp

# Register blueprints with URL prefixes
# auth_bp: Handles /login, /register, /logout
app.register_blueprint(auth_bp, url_prefix='/auth')

# senior_bp: Handles /senior/dashboard, /senior/stories, etc.
app.register_blueprint(senior_bp, url_prefix='/senior')

# youth_bp: Handles /youth/dashboard, /youth/story_feed, etc.
app.register_blueprint(youth_bp, url_prefix='/youth')

# admin_bp: Handles /admin/dashboard, /admin/users, etc.
app.register_blueprint(admin_bp, url_prefix='/admin')


# ==================== DATABASE INITIALIZATION ====================
# Create tables in app context (runs once at startup)
with app.app_context():
    """
    Create all database tables at application startup.

    This runs once when the app initializes.
    It creates all tables defined in models.py if they don't exist.

    Note: In production, database migrations should be handled by Flask-Migrate
    """
    db.create_all()
    print("Database tables created successfully")


# ==================== CONTEXT PROCESSORS ====================
@app.context_processor
def inject_user():
    """
    Make session data available to all templates.

    Context processors inject variables into template context automatically.
    This allows templates to access session.user_id, session.role, etc.

    Returns:
        dict: Dictionary with session object
    """
    return dict(session=session)


# ==================== MAIN ROUTES ====================
@app.route('/')
def index():
    """
    Landing page route - displays role selection cards.
    Redirects logged-in users to their respective dashboards.
    """
    if 'user_id' in session:
        role = session.get('role')
        if role == 'senior':
            return redirect(url_for('senior.dashboard'))
        elif role == 'youth':
            return redirect(url_for('youth.dashboard'))
        elif role == 'admin':
            return redirect(url_for('admin.dashboard'))

    return render_template('index.html')


# ==================== ERROR HANDLERS ====================
@app.errorhandler(404)
def not_found_error(error):
    """
    Handle 404 Not Found errors.

    Args:
        error: Error object from Flask

    Returns:
        Rendered 404.html template with 404 status code
    """
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """
    Handle 500 Internal Server errors.

    Args:
        error: Error object from Flask

    Returns:
        Rendered 500.html template with 500 status code

    Note: Rolls back database session in case of database errors
    """
    db.session.rollback()
    return render_template('errors/500.html'), 500


@app.errorhandler(403)
def forbidden_error(error):
    """
    Handle 403 Forbidden errors (unauthorized access).

    Args:
        error: Error object from Flask

    Returns:
        Rendered 403.html template with 403 status code
    """
    return render_template('errors/403.html'), 403


# ==================== TEMPLATE FILTERS ====================
@app.template_filter('timeago')
def timeago_filter(date):
    """
    Convert datetime to relative time string (e.g., "2 hours ago").

    This is a Jinja2 template filter that can be used in templates like:
    {{ story.created_at|timeago }}

    Args:
        date (datetime): DateTime object to convert

    Returns:
        str: Human-readable relative time string
    """
    from datetime import datetime
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
        return date.strftime('%B %d, %Y')


@app.template_filter('format_date')
def format_date_filter(date, format='%B %d, %Y'):
    """
    Format datetime object to string.

    Args:
        date (datetime): DateTime object to format
        format (str): strftime format string

    Returns:
        str: Formatted date string
    """
    if date:
        return date.strftime(format)
    return ''


@app.template_filter('date')
def date_filter(value, format='%B %d, %Y'):
    """
    Custom date filter for Jinja2 templates.

    This filter formats datetime objects or the string 'now' into formatted date strings.
    Usage in templates: {{ "now"|date("%A, %B %d, %Y") }}

    Args:
        value: Either a datetime object or the string 'now'
        format (str): strftime format string (default: '%B %d, %Y')

    Common format codes:
        %A - Full weekday name (Monday, Tuesday, etc.)
        %B - Full month name (January, February, etc.)
        %d - Day of month (01-31)
        %Y - Year with century (2025)
        %I - Hour 12-hour format (01-12)
        %M - Minute (00-59)
        %p - AM/PM

    Returns:
        str: Formatted date string
    """
    from datetime import datetime

    # If value is the string "now", use current datetime
    if value == "now":
        value = datetime.now()

    # Format the datetime object
    if value:
        return value.strftime(format)
    return ''


# ==================== MAIN EXECUTION ====================
if __name__ == '__main__':
    """
    Run the Flask development server.

    The app runs on http://localhost:5000 by default.
    Debug mode is enabled based on config settings.

    Command line: python app.py
    """
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    print("="* 60)
    print("Starting GenCon SG Application")
    print("="* 60)
    print(f"Environment: {config_name}")
    print(f"Debug Mode: {app.config['DEBUG']}")
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print("="* 60)
    print("Server running at http://localhost:5000")
    print("Press CTRL+C to quit")
    print("="* 60)

    # Run the development server
    app.run(
        host='0.0.0.0',  # Makes server accessible externally
        port=5000,
        debug=app.config['DEBUG']
    )
