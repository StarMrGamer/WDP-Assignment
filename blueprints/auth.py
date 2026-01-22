"""
File: auth.py
Purpose: Authentication blueprint for login, registration, and logout
Author: Rai (Team Lead)
Date: December 2025
Feature: Authentication & User Management
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, User, Streak
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__)


# ==================== LOGIN ROUTE ====================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login.
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
            # === NEW: CHECK IF ACCOUNT IS DISABLED ===
            if not user.is_active:
                reason = user.disable_reason or "Account disabled by administrator."
                flash(f'Your account has been disabled. Reason: {reason}', 'danger')
                return render_template('auth/login.html')
            # Set session variables
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

            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(url_for(f'{user.role}.dashboard'))

        else:
            flash('Invalid username or password', 'danger')
            return render_template('auth/login.html')

    return render_template('auth/login.html')


# ==================== SETUP ROUTE ====================
@auth_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    """
    Handle quick setup after registration.
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
    if 'user_id' in session:
        return redirect(url_for(f"{session['role']}.dashboard"))

    role = request.args.get('role', 'senior')

    if request.method == 'POST':
        # Get role from form
        role = request.form.get('role')

        # ... [Keep existing form data extraction] ...
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

        # Validate age based on the CORRECTLY detected role
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
            role=role,
            profile_picture='default-avatar.png' # Default value
        )

        # === NEW CODE: Handle Profile Picture Upload ===
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                
                if ext in current_app.config['ALLOWED_EXTENSIONS']:
                    # Ensure upload directory exists
                    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                    
                    # Create unique filename: profile_username_timestamp.ext
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    unique_filename = f"profile_{username}_{timestamp}.{ext}"
                    
                    # Save file
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
                    
                    # Update user object (Store with 'uploads/' prefix)
                    new_user.profile_picture = f"uploads/{unique_filename}"
        # ===============================================

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
    """
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye, {username}! You have been logged out.', 'info')
    return redirect(url_for('index'))


# ==================== DELETE ACCOUNT ROUTE ====================
@auth_bp.route('/delete_account', methods=['POST'])
def delete_account():
    """
    Allow users to delete their own account.
    """
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('index'))

    try:
        # Delete user (Cascading delete should handle related records if configured,
        # otherwise we might need to manually clean up. Assuming DB cascade is set or
        # SQLAlchemy cascade options are correct. If not, minimal cleanup here.)
        
        # Manually delete user-specific relations if they don't cascade automatically
        # to ensure clean removal.
        # (For this assignment, we rely on standard SQLAlchemy cascade behavior or just delete the user)
        db.session.delete(user)
        db.session.commit()

        session.clear()
        flash('Your account has been successfully deleted. We are sorry to see you go.', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting account: {e}")
        flash('An error occurred while deleting your account.', 'danger')
        return redirect(url_for(f"{session.get('role', 'senior')}.profile"))


# ==================== HELPER FUNCTIONS ====================
def update_user_streak(user):
    """
    Update user's daily streak on login.
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
        return

    yesterday = today - timedelta(days=1)

    if streak.last_login == yesterday:
        # Consecutive day - increment streak
        streak.current_streak += 1
        streak.points += 10 * streak.current_streak

        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak

        check_streak_badges(user, streak.current_streak)

    else:
        # Streak broken - reset to 1
        streak.current_streak = 1
        streak.points += 10

    streak.last_login = today


def check_streak_badges(user, streak_days):
    """
    Award badges for streak milestones.
    """
    from models import Badge
    from flask import current_app

    milestones = current_app.config.get('STREAK_MILESTONES', {
        7: 'Week Warrior',
        30: 'Month Master',
        100: 'Century Champion',
        365: 'Year Legend'
    })

    if streak_days in milestones:
        badge_name = milestones[streak_days]
        
        existing_badge = Badge.query.filter_by(
            user_id=user.id,
            badge_type=badge_name
        ).first()

        if not existing_badge:
            new_badge = Badge(user_id=user.id, badge_type=badge_name)
            db.session.add(new_badge)
            flash(f'🎉 Congratulations! You earned the {badge_name} badge!', 'success')