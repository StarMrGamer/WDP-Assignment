"""
File: auth.py
Purpose: Authentication blueprint for login, registration, and logout
Author: to be assigned
Date: December 2025
Feature: Authentication & User Management
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, jsonify
from models import db, User, Streak, RegistrationCode, Notification
from utils import check_unkind_words, sanitize_for_display
from forms import LoginForm, RegistrationForm, GoogleCompleteForm, ForgotPasswordForm, ResetPasswordForm
from werkzeug.utils import secure_filename
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
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

    form = LoginForm()
    if form.validate_on_submit():
        # Get form data
        username = form.username.data
        password = form.password.data
        remember = form.remember.data

        # Query database for user by username or email
        if '@' in username:
            user = User.query.filter_by(email=username).first()
        else:
            user = User.query.filter_by(username=username).first()

        # Check if user exists and password is correct
        if user and user.check_password(password):
            # Check if account is pending approval
            if not user.is_approved:
                flash('Your account is pending admin approval. You will be notified once approved.', 'warning')
                return render_template('auth/login.html', form=form)

            # === NEW: CHECK IF ACCOUNT IS DISABLED ===
            if not user.is_active:
                reason = user.disable_reason or "Account disabled by administrator."
                flash(f'Your account has been disabled. Reason: {reason}', 'danger')
                return render_template('auth/login.html', form=form)

            # SECURITY: Regenerate session to prevent session fixation attacks
            session.clear()

            # Set session variables
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['profile_picture'] = user.profile_picture
            session['full_name'] = user.full_name

            # Set session permanence based on "remember me"
            session.permanent = remember

            # Update last active timestamp
            user.last_active = datetime.utcnow()

            # Update or create streak
            update_user_streak(user)

            db.session.commit()

            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(url_for(f'{user.role}.dashboard'))

        else:
            flash('Invalid username or password', 'danger')
            return render_template('auth/login.html', form=form)

    return render_template('auth/login.html', form=form)


# ==================== SETUP ROUTE ====================
@auth_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    """
    Handle quick setup after registration.
    """
    if 'user_id' not in session:
        return redirect(url_for('main.index'))

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

    form = RegistrationForm()
    role = request.args.get('role', 'senior')

    # Profanity check runs on every POST, before WTForms validation
    if request.method == 'POST':
        unkind_words = current_app.config.get('UNKIND_WORDS', [])
        raw_full_name = request.form.get('full_name', '')
        raw_username = request.form.get('username', '')
        if check_unkind_words(raw_full_name, unkind_words) or check_unkind_words(raw_username, unkind_words):
            flash('Your name or username contains inappropriate language. Please choose different values.', 'danger')
            return render_template('auth/register.html', role=role, form=form)

    if form.validate_on_submit():
        # Get data from form
        role = form.role.data
        full_name = form.full_name.data
        email = form.email.data
        phone = form.phone.data
        age = form.age.data
        username = form.username.data
        password = form.password.data
        registration_code = form.registration_code.data

        # Create new user
        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            age=age,
            role=role,
            profile_picture='images/default-avatar.png' # Default value
        )

        # Handle Profile Picture Upload
        if form.profile_picture.data:
            file = form.profile_picture.data
            if file:
                from flask import current_app
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
                    new_user.profile_picture = f"images/uploads/{unique_filename}"

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

        # If registering via Google, link google_id and auto-approve
        google_pending = session.get('google_pending')
        google_id_from_form = request.form.get('google_id', '')
        if google_pending and google_id_from_form == google_pending.get('google_id'):
            new_user.google_id = google_id_from_form
            new_user.is_approved = True
        else:
            # New accounts require admin approval before they can log in
            new_user.is_approved = False

        try:
            # Mark registration code as used
            # Validation happens in form, so code exists and is unused
            code_record = RegistrationCode.query.filter_by(code=registration_code).first()

            # Add user to database
            db.session.add(new_user)
            db.session.commit() # Commit first to get ID

            # Create initial streak record
            streak = Streak(user_id=new_user.id)
            db.session.add(streak)

            # Update code record
            code_record.is_used = True
            code_record.used_by = new_user

            # Notify all admins of the new registration
            admins = User.query.filter_by(role='admin').all()
            for admin in admins:
                notif = Notification(
                    user_id=admin.id,
                    title='New Account Pending Approval',
                    message=f"{new_user.full_name} (@{new_user.username}) has registered as a {role} and is awaiting approval.",
                    type='info',
                    link='/admin/pending-accounts'
                )
                db.session.add(notif)

            db.session.commit()

            # If Google registration, clear pending and auto-login
            if new_user.google_id and new_user.is_approved:
                session.pop('google_pending', None)
                flash(f'Welcome, {new_user.full_name}! Your account has been created.', 'success')
                return _login_user(new_user)

            flash(f'Account created! An admin will review and approve your account shortly. You\'ll be able to log in once approved.', 'success')
            return redirect(url_for('main.index'))

        except Exception as e:
            db.session.rollback()
            print(f"Registration error: {e}")
            flash('An error occurred during registration. Please try again.', 'danger')
            return render_template('auth/register.html', role=role, form=form)
            
    # Flash form errors if any
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'danger')

    # GET request - display registration form
    return render_template('auth/register.html', role=role, form=form)


# ==================== FORGOT / RESET PASSWORD ====================

def _get_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data.strip()
        user = User.query.filter_by(email=email).first()
        if user:
            s = _get_serializer()
            token = s.dumps(email, salt='password-reset')
            reset_url = url_for('auth.reset_password', token=token, _external=True)

            from extensions import mail
            from flask_mail import Message
            msg = Message(
                subject='GenCon SG — Reset Your Password',
                recipients=[email],
                html=render_template('auth/reset_email.html',
                                     user=user, reset_url=reset_url)
            )
            try:
                mail.send(msg)
            except Exception as e:
                print(f"Email send error: {e}")

        # Always show same message to prevent email enumeration
        flash('If an account with that email exists, a password reset link has been sent.', 'info')
        return redirect(url_for('auth.forgot_password'))

    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    s = _get_serializer()
    try:
        email = s.loads(token, salt='password-reset', max_age=3600)  # 1 hour
    except SignatureExpired:
        flash('This reset link has expired. Please request a new one.', 'warning')
        return redirect(url_for('auth.forgot_password'))
    except BadSignature:
        flash('Invalid reset link.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Account not found.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset. You can now sign in.', 'success')
        return redirect(url_for('main.index'))

    return render_template('auth/reset_password.html', form=form, token=token)


# ==================== GOOGLE SIGN-IN ROUTES ====================
@auth_bp.route('/google-login', methods=['POST'])
def google_login():
    """
    Handle Google Sign-In callback.
    Receives a Google JWT credential, verifies it, and either logs in
    an existing user or redirects to complete registration.
    """
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests

    credential = request.form.get('credential')
    if not credential:
        flash('Google sign-in failed. No credential received.', 'danger')
        return redirect(url_for('main.index'))

    client_id = current_app.config.get('GOOGLE_CLIENT_ID')
    if not client_id:
        flash('Google sign-in is not configured.', 'danger')
        return redirect(url_for('main.index'))

    try:
        idinfo = id_token.verify_oauth2_token(
            credential, google_requests.Request(), client_id
        )
    except Exception:
        flash('Google sign-in failed. Invalid token.', 'danger')
        return redirect(url_for('main.index'))

    google_id = idinfo.get('sub')
    email = idinfo.get('email')
    full_name = idinfo.get('name', '')

    if not email:
        flash('Google sign-in failed. No email provided.', 'danger')
        return redirect(url_for('main.index'))

    # Case 1: User with this google_id already exists → login
    user = User.query.filter_by(google_id=google_id).first()
    if user:
        return _login_user(user)

    # Case 2: User with this email exists but no google_id → link & login
    user = User.query.filter_by(email=email).first()
    if user:
        user.google_id = google_id
        db.session.commit()
        return _login_user(user)

    # Case 3: New user → store Google info in session, redirect to register with pre-filled email
    session['google_pending'] = {
        'google_id': google_id,
        'email': email,
        'full_name': full_name
    }
    flash('No account found. Please create one — your email and name have been filled in.', 'info')
    return redirect(url_for('main.index', panel='register'))


@auth_bp.route('/google-complete', methods=['GET', 'POST'])
def google_complete():
    """
    Complete registration for a new Google Sign-In user.
    Requires invite code, username, password, age, and phone.
    """
    google_info = session.get('google_pending')
    if not google_info:
        flash('Please sign in with Google first.', 'warning')
        return redirect(url_for('main.index'))

    form = GoogleCompleteForm()

    if request.method == 'POST':
        # Profanity check on username
        unkind_words = current_app.config.get('UNKIND_WORDS', [])
        raw_username = request.form.get('username', '')
        if check_unkind_words(raw_username, unkind_words):
            flash('Your username contains inappropriate language. Please choose a different one.', 'danger')
            return render_template('auth/google_complete.html', form=form, google_info=google_info)

    if form.validate_on_submit():
        age = form.age.data
        role = 'senior' if age >= 60 else 'youth'

        new_user = User(
            username=form.username.data,
            email=google_info['email'],
            full_name=google_info['full_name'],
            phone=form.phone.data,
            age=age,
            role=role,
            google_id=google_info['google_id'],
            profile_picture='images/default-avatar.png',
            is_approved=True
        )
        new_user.set_password(form.password.data)

        if role == 'senior':
            new_user.accessibility_settings = {
                'font_size': 'normal',
                'high_contrast': False,
                'color_blind_friendly': False
            }
        else:
            new_user.accessibility_settings = {
                'theme': 'light'
            }

        try:
            # Mark registration code as used
            code_record = RegistrationCode.query.filter_by(code=form.registration_code.data).first()

            db.session.add(new_user)
            db.session.commit()

            # Create initial streak record
            streak = Streak(user_id=new_user.id)
            db.session.add(streak)

            code_record.is_used = True
            code_record.used_by = new_user

            db.session.commit()

            # Clear pending Google info
            session.pop('google_pending', None)

            flash(f'Welcome, {new_user.full_name}! Your account has been created.', 'success')
            return _login_user(new_user)

        except Exception as e:
            db.session.rollback()
            print(f"Google registration error: {e}")
            flash('An error occurred during registration. Please try again.', 'danger')
            return render_template('auth/google_complete.html', form=form, google_info=google_info)

    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'danger')

    return render_template('auth/google_complete.html', form=form, google_info=google_info)


def _login_user(user):
    """Helper to log in a user and redirect to their dashboard."""
    if not user.is_approved:
        flash('Your account is pending admin approval.', 'warning')
        return redirect(url_for('main.index'))

    if not user.is_active:
        reason = user.disable_reason or "Account disabled by administrator."
        flash(f'Your account has been disabled. Reason: {reason}', 'danger')
        return redirect(url_for('main.index'))

    # Clear google_pending if present
    google_pending = session.get('google_pending')
    session.clear()

    session['user_id'] = user.id
    session['username'] = user.username
    session['role'] = user.role
    session['profile_picture'] = user.profile_picture
    session['full_name'] = user.full_name
    session.permanent = True

    user.last_active = datetime.utcnow()
    update_user_streak(user)
    db.session.commit()

    flash(f'Welcome back, {user.full_name}!', 'success')
    return redirect(url_for(f'{user.role}.dashboard'))


# ==================== LOGOUT ROUTE ====================
@auth_bp.route('/logout')
def logout():
    """
    Handle user logout.
    """
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye, {username}! You have been logged out.', 'info')
    return redirect(url_for('main.index'))


# ==================== API ROUTES ====================
@auth_bp.route('/change_password', methods=['POST'])
def change_password():
    """
    API endpoint to change user password.
    """
    if 'user_id' not in session:
        return {'success': False, 'message': 'Please login to change password'}, 401
        
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return {'success': False, 'message': 'Missing required fields'}, 400
        
    user = User.query.get(session['user_id'])
    
    if not user.check_password(current_password):
        return {'success': False, 'message': 'Incorrect current password'}, 400
        
    user.set_password(new_password)
    db.session.commit()
    
    return {'success': True, 'message': 'Password updated successfully'}


# ==================== HELPER FUNCTIONS ====================
# Moved to services/streak.py
from services.streak import update_user_streak, check_streak_badges