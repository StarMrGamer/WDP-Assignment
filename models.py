"""
File: models.py
Purpose: Database models for GenCon SG application using SQLAlchemy ORM
Author: Rai (Team Lead), Hong You, Tian An, Asher
Date: December 2025
Description: Defines all database tables and relationships:
             - User accounts (seniors, youth, admins)
             - Stories and reactions/comments
             - Messages and translations
             - Events and participants
             - Communities and posts
             - Buddy pairs
             - Streaks and badges
             - Chat reports
             - Check-ins
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json

# Initialize SQLAlchemy database object
# This will be initialized in app.py with db.init_app(app)
db = SQLAlchemy()


# ==================== USER MODEL ====================
class User(db.Model):
    """
    User model representing all user accounts (seniors, youth, admins).

    Attributes:
        id (int): Primary key, auto-incrementing user ID
        username (str): Unique username for login
        password_hash (str): Hashed password (never store plain text!)
        email (str): User email address
        full_name (str): User's full name
        phone (str): Contact phone number
        age (int): User's age (60+ for seniors, 13+ for youth)
        role (str): User role - 'senior', 'youth', or 'admin'
        profile_picture (str): Path to profile picture file
        interests_json (str): JSON string of user interests
        languages_json (str): JSON string of languages spoken
        accessibility_settings_json (str): JSON string of accessibility preferences
        created_at (datetime): Account creation timestamp
        last_active (datetime): Last login/activity timestamp
        is_active (bool): Whether account is active

    Relationships:
        stories: One-to-many with Story (stories created by this user)
        sent_messages: One-to-many with Message (messages sent)
        received_messages: One-to-many with Message (messages received)
        senior_pairs: One-to-many with Pair (if user is senior)
        youth_pairs: One-to-many with Pair (if user is youth)
        event_participants: One-to-many with EventParticipant
        community_members: One-to-many with CommunityMember
        streak: One-to-one with Streak
        badges: One-to-many with Badge
        checkins: One-to-many with Checkin
        story_reactions: One-to-many with StoryReaction
        story_comments: One-to-many with StoryComment
    """
    __tablename__ = 'users'

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Authentication fields
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # Personal information
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    age = db.Column(db.Integer, nullable=False)
    bio = db.Column(db.Text)  # User biography
    school = db.Column(db.String(255))  # School or organization for youth

    # Role-based access control
    role = db.Column(db.String(20), nullable=False)  # 'senior', 'youth', or 'admin'

    # Profile customization
    profile_picture = db.Column(db.String(255), default='images/default-avatar.png')

    # Disabkle Account #
    disable_reason = db.Column(db.Text)

    # JSON fields for flexible data storage
    # Using JSON allows storing arrays/objects without additional tables
    interests_json = db.Column(db.Text)  # Stores interests as JSON array
    languages_json = db.Column(db.Text)  # Stores languages as JSON array
    accessibility_settings_json = db.Column(db.Text)  # Stores settings as JSON object

    # Timestamps and status
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_active = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships (defined with back_populates for bidirectional access)
    stories = db.relationship('Story', back_populates='user', lazy='dynamic')
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id',
                                   back_populates='sender', lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys='Message.recipient_id',
                                       back_populates='recipient', lazy='dynamic')
    senior_pairs = db.relationship('Pair', foreign_keys='Pair.senior_id',
                                   back_populates='senior', lazy='dynamic')
    youth_pairs = db.relationship('Pair', foreign_keys='Pair.youth_id',
                                 back_populates='youth', lazy='dynamic')
    streak = db.relationship('Streak', back_populates='user', uselist=False)
    badges = db.relationship('Badge', back_populates='user', lazy='dynamic')
    checkins = db.relationship('Checkin', back_populates='user', lazy='dynamic')

    def set_password(self, password):
        """
        Hash and set user password using Werkzeug security.

        Args:
            password (str): Plain text password

        Security: Uses pbkdf2:sha256 algorithm for secure hashing
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Verify password against stored hash.

        Args:
            password (str): Plain text password to check

        Returns:
            bool: True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)

    @property
    def interests(self):
        """Get interests as Python list from JSON string."""
        if self.interests_json:
            return json.loads(self.interests_json)
        return []

    @interests.setter
    def interests(self, value):
        """Set interests from Python list, store as JSON string."""
        self.interests_json = json.dumps(value)

    @property
    def languages(self):
        """Get languages as Python list from JSON string."""
        if self.languages_json:
            return json.loads(self.languages_json)
        return []

    @languages.setter
    def languages(self, value):
        """Set languages from Python list, store as JSON string."""
        self.languages_json = json.dumps(value)

    @property
    def accessibility_settings(self):
        """Get accessibility settings as Python dict from JSON string."""
        if self.accessibility_settings_json:
            return json.loads(self.accessibility_settings_json)
        return {}

    @accessibility_settings.setter
    def accessibility_settings(self, value):
        """Set accessibility settings from Python dict, store as JSON string."""
        self.accessibility_settings_json = json.dumps(value)

    def __repr__(self):
        """String representation for debugging."""
        return f'<User {self.username} ({self.role})>'


# ==================== STORY MODEL ====================
class Story(db.Model):
    """
    Story model for senior life stories.

    Attributes:
        id (int): Primary key
        user_id (int): Foreign key to User who created the story
        title (str): Story title
        content (text): Full story content
        category (str): Category - 'Childhood', 'Work Life', 'Family', 'Hobbies', 'Other'
        photo_url (str): Path to uploaded photo (optional)
        audio_url (str): Path to voice recording (optional)
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last edit timestamp

    Relationships:
        user: Many-to-one with User
        reactions: One-to-many with StoryReaction
        comments: One-to-many with StoryComment
    """
    __tablename__ = 'stories'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # 5 categories
    photo_url = db.Column(db.String(255))  # Optional photo
    audio_url = db.Column(db.String(255))  # Optional voice recording

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='stories')
    reactions = db.relationship('StoryReaction', back_populates='story',
                               lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('StoryComment', back_populates='story',
                              lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Story {self.id}: {self.title[:30]}>'


# ==================== STORY REACTION MODEL ====================
class StoryReaction(db.Model):
    """
    Story reaction model (Heart, Smile, Clap, Hug).

    Attributes:
        id (int): Primary key
        story_id (int): Foreign key to Story
        user_id (int): Foreign key to User who reacted
        reaction_type (str): Type of reaction - 'heart', 'smile', 'clap', 'hug'
        created_at (datetime): Reaction timestamp

    Relationships:
        story: Many-to-one with Story
        user: Many-to-one with User
    """
    __tablename__ = 'story_reactions'

    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    reaction_type = db.Column(db.String(20), nullable=False)  # heart, smile, clap, hug
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    story = db.relationship('Story', back_populates='reactions')
    user = db.relationship('User')

    # Unique constraint: one user can only react once per story with same type
    __table_args__ = (db.UniqueConstraint('story_id', 'user_id', 'reaction_type',
                                         name='unique_story_user_reaction'),)

    def __repr__(self):
        return f'<Reaction {self.reaction_type} on Story {self.story_id}>'


# ==================== STORY COMMENT MODEL ====================
class StoryComment(db.Model):
    """
    Comments on stories.

    Attributes:
        id (int): Primary key
        story_id (int): Foreign key to Story
        user_id (int): Foreign key to User who commented
        content (text): Comment text
        created_at (datetime): Comment timestamp

    Relationships:
        story: Many-to-one with Story
        user: Many-to-one with User
    """
    __tablename__ = 'story_comments'

    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    story = db.relationship('Story', back_populates='comments')
    user = db.relationship('User')

    def __repr__(self):
        return f'<Comment {self.id} on Story {self.story_id}>'


# ==================== MESSAGE MODEL ====================
class Message(db.Model):
    """
    Chat messages between buddies (Lingo Bridge).

    Attributes:
        id (int): Primary key
        sender_id (int): Foreign key to User who sent message
        recipient_id (int): Foreign key to User who receives message
        content (text): Message content (original text)
        original_language (str): Language code of original message
        translated_content (text): Translated message text (optional)
        is_voice (bool): Whether message is voice message
        voice_url (str): Path to voice recording file (optional)
        is_flagged (bool): Whether message contains inappropriate content
        created_at (datetime): Message timestamp

    Relationships:
        sender: Many-to-one with User
        recipient: Many-to-one with User
        reports: One-to-many with ChatReport
    """
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    content = db.Column(db.Text, nullable=False)
    original_language = db.Column(db.String(10), default='en')
    translated_content = db.Column(db.Text)  # Translated version

    is_voice = db.Column(db.Boolean, default=False)
    voice_url = db.Column(db.String(255))

    is_flagged = db.Column(db.Boolean, default=False)  # Flagged by safety system
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], back_populates='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], back_populates='received_messages')
    reports = db.relationship('ChatReport', back_populates='message', lazy='dynamic')

    def __repr__(self):
        return f'<Message {self.id} from User {self.sender_id} to {self.recipient_id}>'


# ==================== PAIR MODEL ====================
class Pair(db.Model):
    """
    Buddy pairs between seniors and youth volunteers.
    Feature owner: Tian An

    Attributes:
        id (int): Primary key
        senior_id (int): Foreign key to senior User
        youth_id (int): Foreign key to youth User
        program (str): Program name/type
        status (str): Pair status - 'active', 'inactive', 'paused'
        paired_date (datetime): When pair was created
        last_interaction (datetime): Last message/activity timestamp

    Relationships:
        senior: Many-to-one with User (senior)
        youth: Many-to-one with User (youth)
    """
    __tablename__ = 'pairs'

    id = db.Column(db.Integer, primary_key=True)
    senior_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    youth_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    program = db.Column(db.String(100))  # Program/initiative name
    status = db.Column(db.String(20), default='active')  # active, inactive, paused
    paired_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_interaction = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    senior = db.relationship('User', foreign_keys=[senior_id], back_populates='senior_pairs')
    youth = db.relationship('User', foreign_keys=[youth_id], back_populates='youth_pairs')

    # Unique constraint: one senior can only be paired with one youth at a time
    __table_args__ = (db.UniqueConstraint('senior_id', 'youth_id', name='unique_senior_youth_pair'),)

    def __repr__(self):
        return f'<Pair {self.id}: Senior {self.senior_id} - Youth {self.youth_id}>'


# ==================== EVENT MODEL ====================
class Event(db.Model):
    """
    Events and activities.
    Feature owner: Asher

    Attributes:
        id (int): Primary key
        title (str): Event title
        description (text): Event description
        event_type (str): Type - 'online' or 'in-person'
        location (str): Location (physical address or online link)
        date (datetime): Event date and time
        capacity (int): Maximum participants
        created_by (int): Foreign key to admin User who created event
        created_at (datetime): Creation timestamp

    Relationships:
        creator: Many-to-one with User
        participants: One-to-many with EventParticipant
    """
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_type = db.Column(db.String(20), nullable=False)  # 'online' or 'in-person'
    location = db.Column(db.String(255))
    date = db.Column(db.DateTime, nullable=False, index=True)
    capacity = db.Column(db.Integer)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    creator = db.relationship('User')
    participants = db.relationship('EventParticipant', back_populates='event',
                                   lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Event {self.id}: {self.title}>'


# ==================== EVENT PARTICIPANT MODEL ====================
class EventParticipant(db.Model):
    """
    Event registrations (junction table).

    Attributes:
        id (int): Primary key
        event_id (int): Foreign key to Event
        user_id (int): Foreign key to User
        registered_at (datetime): Registration timestamp

    Relationships:
        event: Many-to-one with Event
        user: Many-to-one with User
    """
    __tablename__ = 'event_participants'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    event = db.relationship('Event', back_populates='participants')
    user = db.relationship('User')

    # Unique constraint: one user can only register once per event
    __table_args__ = (db.UniqueConstraint('event_id', 'user_id', name='unique_event_user'),)

    def __repr__(self):
        return f'<EventParticipant User {self.user_id} in Event {self.event_id}>'


# ==================== COMMUNITY MODEL ====================
class Community(db.Model):
    """
    Interest-based communities.
    Feature owner: Hong You

    Attributes:
        id (int): Primary key
        name (str): Community name
        type (str): Community type - 'Story', 'Hobby', 'Learning'
        description (text): Community description
        rules (text): Community rules
        member_count (int): Number of members
        created_by (int): Foreign key to User who created community
        created_at (datetime): Creation timestamp

    Relationships:
        creator: Many-to-one with User
        members: One-to-many with CommunityMember
        posts: One-to-many with CommunityPost
    """
    __tablename__ = 'communities'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    type = db.Column(db.String(20), nullable=False)  # Story, Hobby, Learning
    description = db.Column(db.Text)
    rules = db.Column(db.Text)
    
    # Visual customization
    icon = db.Column(db.String(50), default='fas fa-users')
    banner_class = db.Column(db.String(50), default='default')
    tags = db.Column(db.String(255))  # Comma separated tags
    photo_url = db.Column(db.String(255))
    
    member_count = db.Column(db.Integer, default=0)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    creator = db.relationship('User')
    members = db.relationship('CommunityMember', back_populates='community',
                             lazy='dynamic', cascade='all, delete-orphan')
    posts = db.relationship('CommunityPost', back_populates='community',
                           lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Community {self.id}: {self.name}>'


# ==================== COMMUNITY MEMBER MODEL ====================
class CommunityMember(db.Model):
    """
    Community memberships (junction table).

    Attributes:
        id (int): Primary key
        community_id (int): Foreign key to Community
        user_id (int): Foreign key to User
        joined_at (datetime): Join timestamp

    Relationships:
        community: Many-to-one with Community
        user: Many-to-one with User
    """
    __tablename__ = 'community_members'

    id = db.Column(db.Integer, primary_key=True)
    community_id = db.Column(db.Integer, db.ForeignKey('communities.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_viewed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    community = db.relationship('Community', back_populates='members')
    user = db.relationship('User')

    # Unique constraint: one user can only join a community once
    __table_args__ = (db.UniqueConstraint('community_id', 'user_id', name='unique_community_user'),)

    def __repr__(self):
        return f'<CommunityMember User {self.user_id} in Community {self.community_id}>'


# ==================== COMMUNITY POST MODEL ====================
class CommunityPost(db.Model):
    """
    Posts within communities.

    Attributes:
        id (int): Primary key
        community_id (int): Foreign key to Community
        user_id (int): Foreign key to User who posted
        content (text): Post content
        created_at (datetime): Post timestamp

    Relationships:
        community: Many-to-one with Community
        user: Many-to-one with User
    """
    __tablename__ = 'community_posts'

    id = db.Column(db.Integer, primary_key=True)
    community_id = db.Column(db.Integer, db.ForeignKey('communities.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=True)
    photo_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    community = db.relationship('Community', back_populates='posts')
    user = db.relationship('User')

    def __repr__(self):
        return f'<CommunityPost {self.id} in Community {self.community_id}>'


# ==================== STREAK MODEL ====================
class Streak(db.Model):
    """
    User engagement streaks.
    Feature owner: Tian An

    Attributes:
        id (int): Primary key
        user_id (int): Foreign key to User (one-to-one relationship)
        current_streak (int): Current consecutive days
        longest_streak (int): Record longest streak
        points (int): Total points accumulated
        games_played (int): Total games completed
        games_won (int): Total games won
        last_login (date): Last login date for streak tracking

    Relationships:
        user: One-to-one with User
    """
    __tablename__ = 'streaks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)

    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    points = db.Column(db.Integer, default=0)
    games_played = db.Column(db.Integer, default=0)
    games_won = db.Column(db.Integer, default=0)
    last_login = db.Column(db.Date, default=datetime.utcnow().date)

    # Relationships
    user = db.relationship('User', back_populates='streak')

    def __repr__(self):
        return f'<Streak User {self.user_id}: {self.current_streak} days>'


# ==================== BADGE MODEL ====================
class Badge(db.Model):
    """
    Achievement badges earned by users.
    Feature owner: Tian An

    Attributes:
        id (int): Primary key
        user_id (int): Foreign key to User
        badge_type (str): Badge type/name
        earned_at (datetime): When badge was earned

    Relationships:
        user: Many-to-one with User
    """
    __tablename__ = 'badges'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    badge_type = db.Column(db.String(50), nullable=False)  # e.g., 'Week Warrior', 'Month Master'
    earned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = db.relationship('User', back_populates='badges')

    def __repr__(self):
        return f'<Badge {self.badge_type} for User {self.user_id}>'


# ==================== CHAT REPORT MODEL ====================
class ChatReport(db.Model):
    """
    Reported chat messages for moderation.
    Feature owner: Rai (Smart Chat Safety)

    Attributes:
        id (int): Primary key
        message_id (int): Foreign key to reported Message
        reported_by (int): Foreign key to User who reported
        reported_user_id (int): Foreign key to User who sent the message
        reason (str): Report reason
        description (text): Additional details (optional)
        status (str): Report status - 'pending', 'under_review', 'resolved', 'dismissed'
        admin_notes (text): Admin notes on the report
        created_at (datetime): Report timestamp

    Relationships:
        message: Many-to-one with Message
        reporter: Many-to-one with User
        reported_user: Many-to-one with User
    """
    __tablename__ = 'chat_reports'

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=False, index=True)
    reported_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    reported_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    reason = db.Column(db.String(100), nullable=False)  # Harassment, Inappropriate, Spam, etc.
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, under_review, resolved, dismissed
    admin_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    message = db.relationship('Message', back_populates='reports')
    reporter = db.relationship('User', foreign_keys=[reported_by])
    reported_user = db.relationship('User', foreign_keys=[reported_user_id])

    def __repr__(self):
        return f'<ChatReport {self.id}: {self.status}>'


# ==================== CHECKIN MODEL ====================
class Checkin(db.Model):
    """
    Weekly mood check-ins for seniors.
    Feature owner: Rai

    Attributes:
        id (int): Primary key
        user_id (int): Foreign key to senior User
        mood (str): Mood selection - 'Great', 'Good', 'Okay', 'Not Good'
        notes (text): Optional written response
        created_at (datetime): Check-in timestamp

    Relationships:
        user: Many-to-one with User
    """
    __tablename__ = 'checkins'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    mood = db.Column(db.String(20), nullable=False)  # Great, Good, Okay, Not Good
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = db.relationship('User', back_populates='checkins')

    def __repr__(self):
        return f'<Checkin {self.id}: User {self.user_id} - {self.mood}>'


# ==================== NOTIFICATION MODEL ====================
class Notification(db.Model):
    """
    User notifications for events, games, etc.
    """
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20)) # 'event', 'game', 'message'
    link = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    user = db.relationship('User', backref=db.backref('notifications_list', lazy='dynamic'))

    def __repr__(self):
        return f'<Notification {self.id}: {self.title}>'


# ==================== GAME MODELS ====================
class Game(db.Model):
    """
    Game definitions for the Games Arcade.
    """
    __tablename__ = 'games'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))  # e.g., 'fas fa-chess'
    
    # Badge info (e.g., "Traditional", "Strategy")
    badge_label = db.Column(db.String(50))
    badge_class = db.Column(db.String(50))  # css class
    badge_icon = db.Column(db.String(50))
    
    # Meta info
    players_text = db.Column(db.String(50))  # "2 Players"
    duration_text = db.Column(db.String(50)) # "20-40 min"
    
    # Type info
    type_label = db.Column(db.String(50))    # "Strategy", "Logic"
    type_icon = db.Column(db.String(50))
    
    # Visuals
    bg_gradient = db.Column(db.String(255))  # CSS gradient string

    sessions = db.relationship('GameSession', back_populates='game', lazy='dynamic')

    def __repr__(self):
        return f'<Game {self.title}>'


class GameSession(db.Model):
    """
    Active game sessions between users.
    """
    __tablename__ = 'game_sessions'

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    player1_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    player2_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    current_turn_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(20), default='waiting')  # active, completed, abandoned, waiting
    
    player1_ready = db.Column(db.Boolean, default=False)
    player2_ready = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    game = db.relationship('Game', back_populates='sessions')
    player1 = db.relationship('User', foreign_keys=[player1_id])
    player2 = db.relationship('User', foreign_keys=[player2_id])

    def __repr__(self):
        return f'<GameSession {self.id}: {self.status}>'
