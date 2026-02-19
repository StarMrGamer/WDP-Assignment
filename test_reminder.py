"""Tests for services/reminders.py — event reminder notification job."""
from datetime import datetime, timedelta
import pytest
from extensions import db
from models import Event, EventParticipant, Notification
from services.reminders import send_event_reminders


# ── helpers ────────────────────────────────────────────────────────────────

def _make_event(admin_id, hours_from_now, status='approved', title='Test Event'):
    event = Event(
        title=title,
        event_type='online',
        date=datetime.utcnow() + timedelta(hours=hours_from_now),
        status=status,
        created_by=admin_id,
    )
    db.session.add(event)
    db.session.flush()
    return event


def _make_participant(event_id, user_id, sent_24h=False, sent_1h=False):
    ep = EventParticipant(
        event_id=event_id,
        user_id=user_id,
        reminder_24h_sent=sent_24h,
        reminder_1h_sent=sent_1h,
    )
    db.session.add(ep)
    db.session.commit()
    return ep


# ── 24-hour reminder ────────────────────────────────────────────────────────

class Test24hReminder:
    def test_sends_notification(self, app, admin_user, youth_user):
        event = _make_event(admin_user.id, hours_from_now=24)
        _make_participant(event.id, youth_user.id)

        send_event_reminders(app)

        notifs = Notification.query.filter_by(user_id=youth_user.id).all()
        assert len(notifs) == 1
        assert 'Tomorrow' in notifs[0].title
        assert event.title in notifs[0].message

    def test_marks_flag(self, app, admin_user, youth_user):
        event = _make_event(admin_user.id, hours_from_now=24)
        _make_participant(event.id, youth_user.id)

        send_event_reminders(app)

        ep = EventParticipant.query.first()
        assert ep.reminder_24h_sent is True

    def test_no_duplicate_if_already_sent(self, app, admin_user, youth_user):
        event = _make_event(admin_user.id, hours_from_now=24)
        _make_participant(event.id, youth_user.id, sent_24h=True)

        send_event_reminders(app)

        assert Notification.query.filter_by(user_id=youth_user.id).count() == 0


# ── 1-hour reminder ─────────────────────────────────────────────────────────

class Test1hReminder:
    def test_sends_notification(self, app, admin_user, senior_user):
        event = _make_event(admin_user.id, hours_from_now=1)
        _make_participant(event.id, senior_user.id)

        send_event_reminders(app)

        notifs = Notification.query.filter_by(user_id=senior_user.id).all()
        assert len(notifs) == 1
        assert 'Soon' in notifs[0].title

    def test_marks_flag(self, app, admin_user, senior_user):
        event = _make_event(admin_user.id, hours_from_now=1)
        _make_participant(event.id, senior_user.id)

        send_event_reminders(app)

        ep = EventParticipant.query.first()
        assert ep.reminder_1h_sent is True

    def test_no_duplicate_if_already_sent(self, app, admin_user, senior_user):
        event = _make_event(admin_user.id, hours_from_now=1)
        _make_participant(event.id, senior_user.id, sent_1h=True)

        send_event_reminders(app)

        assert Notification.query.filter_by(user_id=senior_user.id).count() == 0


# ── events that should be skipped ───────────────────────────────────────────

class TestSkippedEvents:
    def test_pending_event_skipped(self, app, admin_user, youth_user):
        event = _make_event(admin_user.id, hours_from_now=24, status='pending')
        _make_participant(event.id, youth_user.id)

        send_event_reminders(app)

        assert Notification.query.filter_by(user_id=youth_user.id).count() == 0

    def test_event_too_far_away_skipped(self, app, admin_user, youth_user):
        event = _make_event(admin_user.id, hours_from_now=48)  # outside both windows
        _make_participant(event.id, youth_user.id)

        send_event_reminders(app)

        assert Notification.query.filter_by(user_id=youth_user.id).count() == 0

    def test_past_event_skipped(self, app, admin_user, youth_user):
        event = _make_event(admin_user.id, hours_from_now=-1)  # in the past
        _make_participant(event.id, youth_user.id)

        send_event_reminders(app)

        assert Notification.query.filter_by(user_id=youth_user.id).count() == 0
