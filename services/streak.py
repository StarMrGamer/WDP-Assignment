"""
services/streak.py — Streak tracking and badge award logic.

Extracted from blueprints/auth.py so it can be reused by other parts of
the application without importing the auth blueprint.
"""
from extensions import db


def update_user_streak(user):
    """Update user's daily streak on login."""
    from datetime import date, timedelta
    from models import Streak

    streak = Streak.query.filter_by(user_id=user.id).first()
    if not streak:
        streak = Streak(user_id=user.id, current_streak=1, longest_streak=1, points=10)
        db.session.add(streak)
        return

    today = date.today()

    # Already logged in today — nothing to do
    if streak.last_login == today:
        return

    yesterday = today - timedelta(days=1)

    if streak.last_login == yesterday:
        # Consecutive day — increment streak
        streak.current_streak += 1
        streak.points += 10 * streak.current_streak

        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak

        check_streak_badges(user, streak.current_streak)
    else:
        # Streak broken — reset to 1
        streak.current_streak = 1
        streak.points += 10

    streak.last_login = today


def check_streak_badges(user, streak_days):
    """Award badges for streak milestones."""
    from models import Badge
    from flask import current_app, flash

    milestones = current_app.config.get('STREAK_MILESTONES', {
        7: 'Week Warrior',
        30: 'Month Master',
        100: 'Century Champion',
        365: 'Year Legend',
    })

    if streak_days in milestones:
        badge_name = milestones[streak_days]

        existing_badge = Badge.query.filter_by(
            user_id=user.id,
            badge_type=badge_name,
        ).first()

        if not existing_badge:
            new_badge = Badge(user_id=user.id, badge_type=badge_name)
            db.session.add(new_badge)
            flash(f'🎉 Congratulations! You earned the {badge_name} badge!', 'success')
