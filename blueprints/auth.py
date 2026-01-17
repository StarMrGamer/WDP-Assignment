"""
File: auth.py
Purpose: Authentication blueprint for login, registration, and logout
Author: Rai (Team Lead)
Date: December 2025
Feature: Authentication & User Management (RAI's Feature Part 1)
Description: Handles:
             - Role selection
             - User login with session management
             - User registration with age validation
             - Password hashing and verification
             - Logout functionality
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, User, Streak
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Create authentication blueprint
# All routes in this file will be prefixed with /auth (set in app.py)
auth_bp = Blueprint('auth', __name__)


# ==================== LOGIN ROUTE ====================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login.

    GET: Display login form
    POST: Process login credentials

    Form fields:
        - username: User's username
        - password: User's password
        - remember: Remember me checkbox (optional)

    Returns:
        GET: Rendered login.html template
        POST: Redirect to role-specific dashboard or back to login with error
    """
    # If user is already logged in, redirect to their dashboard
    if 'user_id' in session:
        return redirect(url_for(f"{session['role']}.dashboard"))

    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember')

        # Validate input
        if not username or not password:
            flash('Please enter both username and password', 'danger')
            return render_template('auth/login.html')

        # Query database for user
        user = User.query.filter_by(username=username).first()

        # Check if user exists and password is correct
        if user and user.check_password(password):
            # Set session variables (logs user in)
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['profile_picture'] = user.profile_picture
            session['full_name'] = user.full_name

            # Set session permanence based on "remember me"
            session.permanent = remember is not None

            # Update last active timestamp
            user.last_active = datetime.utcnow()

            # Update or create streak
            update_user_streak(user)

            db.session.commit()

            # Flash success message
            flash(f'Welcome back, {user.full_name}!', 'success')

            # Redirect to role-specific dashboard based on user's actual role
            return redirect(url_for(f'{user.role}.dashboard'))

        else:
            # Invalid credentials
            flash('Invalid username or password', 'danger')
            return render_template('auth/login.html')

    # GET request - display login form
    return render_template('auth/login.html')


# ==================== SETUP ROUTE ====================
@auth_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    """
    Handle quick setup after registration.
    Allows users to select interests.
    """
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        interests = request.form.getlist('interests')
        
        user = User.query.get(session['user_id'])
        if user:
            user.interests = interests
            db.session.commit()
            
            flash('Profile setup complete!', 'success')
            return redirect(url_for(f'{user.role}.dashboard'))

    return render_template('auth/setup.html')


# ==================== REGISTRATION ROUTE ====================
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle user registration.

    GET: Display registration form
    POST: Process registration data and create new user

    Form fields:
        - full_name: User's full name
        - email: Email address
        - phone: Phone number
        - age: User's age (validated based on role)
        - username: Desired username
        - password: Password
        - confirm_password: Password confirmation

    Validation:
        - Seniors must be 60+ years old
        - Youth must be 13+ years old
        - Username must be unique
        - Email must be unique
        - Password must match confirmation

    Returns:
        GET: Rendered register.html template
        POST: Redirect to login on success, or back to register with errors
    """
    # If user is already logged in, redirect to dashboard
    if 'user_id' in session:
        return redirect(url_for(f"{session['role']}.dashboard"))

    # Get role from query parameter
    role = request.args.get('role', 'senior')

    if request.method == 'POST':
        # Get form data
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        age = request.form.get('age')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validate all fields are filled
        if not all([full_name, email, age, username, password, confirm_password]):
            flash('Please fill in all required fields', 'danger')
            return render_template('auth/register.html', role=role)

        # Convert age to integer
        try:
            age = int(age)
        except ValueError:
            flash('Please enter a valid age', 'danger')
            return render_template('auth/register.html', role=role)

        # Validate age based on role
        if role == 'senior' and age < 60:
            flash('Seniors must be 60 years or older', 'danger')
            return render_template('auth/register.html', role=role)

        if role == 'youth' and age < 13:
            flash('Youth volunteers must be 13 years or older', 'danger')
            return render_template('auth/register.html', role=role)

        if role == 'youth' and age >= 60:
            flash('If you are 60 or older, please register as a Senior', 'warning')
            return render_template('auth/register.html', role=role)

        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('auth/register.html', role=role)

        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already taken. Please choose another.', 'danger')
            return render_template('auth/register.html', role=role)

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login instead.', 'warning')
            return render_template('auth/register.html', role=role)

        # Create new user
        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            age=age,
            role=role
        )

        # Set hashed password
        new_user.set_password(password)

        # Set default accessibility settings for seniors
        if role == 'senior':
            new_user.accessibility_settings = {
                'font_size': 'normal',
                'high_contrast': False,
                'color_blind_friendly': False
            }

        # Set default theme for youth
        if role == 'youth':
            new_user.accessibility_settings = {
                'theme': 'light'
            }

        try:
            # Add user to database
            db.session.add(new_user)
            db.session.commit()

            # Create initial streak record
            streak = Streak(user_id=new_user.id)
            db.session.add(streak)
            db.session.commit()

            # Auto-login the user
            session['user_id'] = new_user.id
            session['username'] = new_user.username
            session['role'] = new_user.role
            session['profile_picture'] = new_user.profile_picture
            session['full_name'] = new_user.full_name
            session.permanent = True

            flash(f'Account created successfully! Please complete your profile setup.', 'success')
            return redirect(url_for('auth.setup'))

        except Exception as e:
            db.session.rollback()
            print(f"Registration error: {e}")
            flash('An error occurred during registration. Please try again.', 'danger')
            return render_template('auth/register.html', role=role)

    # GET request - display registration form
    return render_template('auth/register.html', role=role)


# ==================== LOGOUT ROUTE ====================
@auth_bp.route('/logout')
def logout():
    """
    Handle user logout.

    Clears session data and redirects to landing page.

    Returns:
        Redirect to index page
    """
    # Get username for goodbye message
    username = session.get('username', 'User')

    # Clear all session data
    session.clear()

    # Flash goodbye message
    flash(f'Goodbye, {username}! You have been logged out.', 'info')

    # Redirect to landing page
    return redirect(url_for('index'))


# ==================== HELPER FUNCTIONS ====================
def update_user_streak(user):
    """
    Update user's daily streak on login.

    Checks if user logged in today. If not, updates streak:
    - If last login was yesterday, increment streak
    - If last login was 2+ days ago, reset streak to 1
    - Awards badges for milestone streaks

    Args:
        user (User): User object to update streak for
    """
    from datetime import date, timedelta

    # Get or create streak record
    streak = Streak.query.filter_by(user_id=user.id).first()
    if not streak:
        streak = Streak(user_id=user.id, current_streak=1, longest_streak=1, points=10)
        db.session.add(streak)
        return

    today = date.today()

    # Check if already logged in today
    if streak.last_login == today:
        return  # Streak already updated today

    yesterday = today - timedelta(days=1)

    if streak.last_login == yesterday:
        # Consecutive day - increment streak
        streak.current_streak += 1
        streak.points += 10 * streak.current_streak

        # Update longest streak if needed
        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak

        # Check for milestone badges
        check_streak_badges(user, streak.current_streak)

    else:
        # Streak broken - reset to 1
        streak.current_streak = 1
        streak.points += 10

    streak.last_login = today


def check_streak_badges(user, streak_days):
    """
    Award badges for streak milestones.

    Args:
        user (User): User to award badge to
        streak_days (int): Current streak count
    """
    from models import Badge
    from flask import current_app

    # Get streak milestones from config
    milestones = current_app.config.get('STREAK_MILESTONES', {
        7: 'Week Warrior',
        30: 'Month Master',
        100: 'Century Champion',
        365: 'Year Legend'
    })

    # Check if user reached a milestone
    if streak_days in milestones:
        badge_name = milestones[streak_days]

        # Check if badge already exists
        existing_badge = Badge.query.filter_by(
            user_id=user.id,
            badge_type=badge_name
        ).first()

        if not existing_badge:
            # Award new badge
            new_badge = Badge(user_id=user.id, badge_type=badge_name)
            db.session.add(new_badge)
            flash(f'🎉 Congratulations! You earned the {badge_name} badge!', 'success')
