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


def check_achievement_badges(user):
    """Check and award achievement badges based on real user activity."""
    from models import Badge, EventParticipant, StoryComment, StoryReaction, CommunityMember, Message, User as UserModel, Streak
    from flask import flash
    from extensions import db

    user_id = user.id
    streak = Streak.query.filter_by(user_id=user_id).first()

    events_attended    = EventParticipant.query.filter_by(user_id=user_id).count()
    stories_commented  = StoryComment.query.filter_by(user_id=user_id).count()
    communities_joined = CommunityMember.query.filter_by(user_id=user_id).count()
    story_reactions    = StoryReaction.query.filter_by(user_id=user_id).count()
    games_played       = streak.games_played if streak else 0
    messages_sent      = Message.query.filter_by(sender_id=user_id).count()

    seniors_messaged = db.session.query(Message.recipient_id).join(
        UserModel, Message.recipient_id == UserModel.id
    ).filter(
        Message.sender_id == user_id,
        UserModel.role == 'senior'
    ).distinct().count()

    criteria = [
        ('First Steps',        events_attended    >= 1),
        ('Story Keeper',       stories_commented  >= 5),
        ('Tech Wizard',        seniors_messaged   >= 10),
        ('Game Master',        games_played       >= 15),
        ('Community Builder',  communities_joined >= 5),
        ('Event Organizer',    events_attended    >= 3),
        ('Heritage Champion',  story_reactions    >= 5),
        ('Conversation Partner', messages_sent    >= 20),
    ]

    awarded = False
    for badge_name, qualified in criteria:
        if qualified:
            exists = Badge.query.filter_by(user_id=user_id, badge_type=badge_name).first()
            if not exists:
                db.session.add(Badge(user_id=user_id, badge_type=badge_name))
                flash(f'Congratulations! You earned the {badge_name} badge!', 'success')
                awarded = True

    if awarded:
        db.session.commit()


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
