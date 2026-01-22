"""
File: auth.py
Purpose: Authentication blueprint for login, registration, and logout
Author: Rai (Team Lead)
Date: December 2025
Feature: Authentication & User Management
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
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
    # If user is already logged in, redirect to their dashboard
    if 'user_id' in session:
        return redirect(url_for(f"{session['role']}.dashboard"))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember')

        if not username or not password:
            flash('Please enter both username and password', 'danger')
            return render_template('auth/login.html')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            # CHECK IF ACCOUNT IS DISABLED
            if not user.is_active:
                reason = user.disable_reason or "Account disabled by administrator."
                flash(f'Your account has been disabled. Reason: {reason}', 'danger')
                return render_template('auth/login.html')

            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['profile_picture'] = user.profile_picture
            session['full_name'] = user.full_name
            session.permanent = remember is not None

            user.last_active = datetime.utcnow()
            update_user_streak(user)
            db.session.commit()

            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(url_for(f'{user.role}.dashboard'))
        else:
            flash('Invalid username or password', 'danger')
            return render_template('auth/login.html')

    return render_template('auth/login.html')


# ==================== SETUP ROUTE (Updated) ====================
@auth_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    """
    Handle quick setup: Profile Picture + Interests
    """
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        user = User.query.get(session['user_id'])
        
        # 1. Handle Interests
        interests = request.form.getlist('interests')
        if user:
            user.interests = interests
            
            # 2. Handle Profile Picture Upload (MOVED HERE)
            if 'profile_picture' in request.files:
                file = request.files['profile_picture']
                if file and file.filename != '':
                    filename = secure_filename(file.filename)
                    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                    
                    if ext in current_app.config['ALLOWED_EXTENSIONS']:
                        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                        
                        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                        unique_filename = f"profile_{user.username}_{timestamp}.{ext}"
                        
                        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
                        
                        # Save with uploads/ prefix
                        user.profile_picture = f"uploads/{unique_filename}"
                        # Update session so navbar updates immediately
                        session['profile_picture'] = user.profile_picture

            db.session.commit()
            
            flash('Profile setup complete!', 'success')
            return redirect(url_for(f'{user.role}.dashboard'))

    return render_template('auth/setup.html')


# ==================== REGISTRATION ROUTE (Cleaned) ====================
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for(f"{session['role']}.dashboard"))

    role = request.args.get('role', 'senior')

    if request.method == 'POST':
        role = request.form.get('role')
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        age = request.form.get('age')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not all([full_name, email, age, username, password, confirm_password]):
            flash('Please fill in all required fields', 'danger')
            return render_template('auth/register.html', role=role)

        try:
            age = int(age)
        except ValueError:
            flash('Please enter a valid age', 'danger')
            return render_template('auth/register.html', role=role)

        if role == 'senior' and age < 60:
            flash('Seniors must be 60 years or older', 'danger')
            return render_template('auth/register.html', role=role)

        if role == 'youth' and age < 13:
            flash('Youth volunteers must be 13 years or older', 'danger')
            return render_template('auth/register.html', role=role)

        if role == 'youth' and age >= 60:
            flash('If you are 60 or older, please register as a Senior', 'warning')
            return render_template('auth/register.html', role=role)

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('auth/register.html', role=role)

        if User.query.filter_by(username=username).first():
            flash('Username already taken. Please choose another.', 'danger')
            return render_template('auth/register.html', role=role)

        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login instead.', 'warning')
            return render_template('auth/register.html', role=role)

        # Create new user (NO FILE UPLOAD HERE)
        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            age=age,
            role=role,
            profile_picture='default-avatar.png'
        )

        new_user.set_password(password)

        if role == 'senior':
            new_user.accessibility_settings = {
                'font_size': 'normal',
                'high_contrast': False,
                'color_blind_friendly': False
            }

        if role == 'youth':
            new_user.accessibility_settings = {'theme': 'light'}

        try:
            db.session.add(new_user)
            db.session.commit()

            streak = Streak(user_id=new_user.id)
            db.session.add(streak)
            db.session.commit()

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

    return render_template('auth/register.html', role=role)

# ... [Keep the logout and helper functions at the bottom unchanged] ...
@auth_bp.route('/logout')
def logout():
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye, {username}! You have been logged out.', 'info')
    return redirect(url_for('index'))

def update_user_streak(user):
    from datetime import date, timedelta
    streak = Streak.query.filter_by(user_id=user.id).first()
    if not streak:
        streak = Streak(user_id=user.id, current_streak=1, longest_streak=1, points=10)
        db.session.add(streak)
        return
    today = date.today()
    if streak.last_login == today:
        return
    yesterday = today - timedelta(days=1)
    if streak.last_login == yesterday:
        streak.current_streak += 1
        streak.points += 10 * streak.current_streak
        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak
        check_streak_badges(user, streak.current_streak)
    else:
        streak.current_streak = 1
        streak.points += 10
    streak.last_login = today

def check_streak_badges(user, streak_days):
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