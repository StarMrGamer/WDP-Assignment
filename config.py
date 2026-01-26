"""
File: config.py
Purpose: Configuration settings for GenCon SG Flask application
Author: to be assigned
Date: December 2025
Description: Contains all configuration settings including:
             - Database connection (SQLite)
             - Secret key for session management
             - File upload settings
             - Application environment settings
"""

import os
from datetime import timedelta

# Base directory of the application
# __file__ is the path to this config.py file
# os.path.abspath gets the absolute path
# os.path.dirname gets the directory containing the file
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """
    Base configuration class containing all app settings.

    This class defines configuration variables used throughout the Flask application.
    All settings are defined as class attributes that can be accessed via app.config.
    """

    # ==================== SECRET KEY ====================
    # Secret key for session management and CSRF protection
    # In production, this should be set via environment variable
    # For development, we use a default key
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'gencon-sg-super-secret-key-2025'

    # ==================== DATABASE CONFIGURATION ====================
    # SQLite database URI
    # Database file will be created in the application's base directory
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'database.db')

    # Disable Flask-SQLAlchemy event system to save resources
    # This system tracks modifications and emits signals, which we don't need
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Enable query echo for debugging (shows SQL queries in console)
    # Set to False in production for better performance
    SQLALCHEMY_ECHO = True

    # ==================== SESSION CONFIGURATION ====================
    # Session lifetime - user will be logged out after this period of inactivity
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

    # Session cookie settings for security
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Prevents JavaScript access to session cookie
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection

    # ==================== FILE UPLOAD CONFIGURATION ====================
    # Maximum file size for uploads (5MB)
    # Used for profile pictures, story photos, etc.
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB in bytes

    # Allowed file extensions for image uploads
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # Upload folder for user-uploaded files
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'images', 'uploads')

    # ==================== PAGINATION SETTINGS ====================
    # Number of items to display per page for story feeds, user lists, etc.
    STORIES_PER_PAGE = 10
    USERS_PER_PAGE = 20
    EVENTS_PER_PAGE = 12
    COMMUNITIES_PER_PAGE = 9

    # ==================== APPLICATION SETTINGS ====================
    # Application name displayed in page titles and emails
    APP_NAME = 'GenCon SG'

    # Application version
    APP_VERSION = '1.0.0'

    # Admin email for system notifications
    ADMIN_EMAIL = 'admin@genconsg.com'

    # Enable debug mode (shows detailed error pages)
    # MUST be False in production!
    DEBUG = True

    # Enable testing mode
    TESTING = False

    # ==================== ENGAGEMENT SETTINGS ====================
    # Points awarded for different actions
    POINTS_DAILY_LOGIN = 10
    POINTS_STORY_SHARE = 50
    POINTS_STORY_REACTION = 5
    POINTS_COMMENT = 10
    POINTS_MESSAGE_SENT = 2

    # Streak milestone days for badge awards
    STREAK_MILESTONES = {
        7: 'Week Warrior',
        30: 'Month Master',
        100: 'Century Champion',
        365: 'Year Legend'
    }

    # ==================== CHAT SAFETY SETTINGS ====================
    # List of inappropriate words for chat moderation
    # This is a basic list - can be expanded based on requirements
    UNKIND_WORDS = [
        'hate', 'stupid', 'idiot', 'fool', 'dumb', 'shut up',
        'ugly', 'loser', 'worthless', 'useless', 'trash'
    ]

    # ==================== NOTIFICATION SETTINGS ====================
    # Number of days before an event to send notifications
    EVENT_NOTIFICATION_DAYS = 7

    # Number of days of inactivity before considering a user inactive
    INACTIVE_USER_DAYS = 10

    # Number of days of no interaction to alert admin about a pair
    INACTIVE_PAIR_DAYS = 7

    # ==================== TRANSLATION SETTINGS ====================
    # Supported languages for Lingo Bridge translation feature
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'zh': 'Chinese',
        'ms': 'Malay',
        'ta': 'Tamil'
    }

    # Default language
    DEFAULT_LANGUAGE = 'en'

    # ==================== RATE LIMITING SETTINGS ====================
    # Maximum number of stories a senior can create per day
    MAX_STORIES_PER_DAY = 5

    # Maximum number of messages a user can send per hour
    MAX_MESSAGES_PER_HOUR = 100

    # Maximum number of login attempts before temporary lockout
    MAX_LOGIN_ATTEMPTS = 5

    # ==================== ACCESSIBILITY SETTINGS ====================
    # Font size options for seniors (in pixels)
    FONT_SIZES = {
        'normal': 18,
        'large': 20,
        'xlarge': 24
    }

    # Theme options for youth users
    YOUTH_THEMES = ['light', 'dark', 'blue', 'purple']


class DevelopmentConfig(Config):
    """
    Development environment configuration.
    Inherits from base Config class and overrides specific settings.
    """
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """
    Testing environment configuration.
    Used for running automated tests.
    """
    DEBUG = False
    TESTING = True
    # Use in-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """
    Production environment configuration.
    Used when deploying the application.
    """
    DEBUG = False
    TESTING = False
    # In production, secret key MUST be set via environment variable
    SECRET_KEY = os.environ.get('SECRET_KEY')
    # Enable secure session cookies in production
    SESSION_COOKIE_SECURE = True
    # Disable SQL query echo in production
    SQLALCHEMY_ECHO = False


# Configuration dictionary to select config based on environment
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(config_name='default'):
    """
    Get configuration object based on environment name.

    Args:
        config_name (str): Name of configuration ('development', 'testing', 'production')

    Returns:
        Config: Configuration class object
    """
    return config.get(config_name, config['default'])
