"""
blueprints/decorators.py — Role-based access-control decorators.

Extracted from the individual blueprint files so the logic lives in one place.
Each blueprint imports the decorator it needs:

    from blueprints.decorators import senior_required as login_required
    from blueprints.decorators import youth_required   as login_required
    from blueprints.decorators import admin_required
"""

from functools import wraps
from flask import session, flash, redirect, url_for


def senior_required(f):
    """Allow only authenticated senior users."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('auth.login', role='senior'))
        if session.get('role') != 'senior':
            flash('Access denied. Senior account required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def youth_required(f):
    """Allow only authenticated youth users."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('auth.login', role='youth'))
        if session.get('role') != 'youth':
            flash('Access denied. Youth account required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Allow only authenticated admin users."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('auth.login', role='admin'))
        if session.get('role') != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function
