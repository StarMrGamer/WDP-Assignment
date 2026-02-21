"""Event reminder notification job — called by APScheduler every 15 minutes."""
from datetime import datetime, timedelta
from extensions import db


def send_event_reminders(app):
    with app.app_context():
        from models import Event, EventParticipant, Notification

        now = datetime.utcnow()

        window_24h_lo = now + timedelta(hours=23, minutes=45)
        window_24h_hi = now + timedelta(hours=24, minutes=15)

        window_1h_lo = now + timedelta(minutes=45)
        window_1h_hi = now + timedelta(hours=1, minutes=15)

        # 24-hour reminders
        due_24h = (
            EventParticipant.query
            .join(Event, EventParticipant.event_id == Event.id)
            .filter(
                Event.status == 'approved',
                Event.date >= window_24h_lo,
                Event.date <= window_24h_hi,
                EventParticipant.reminder_24h_sent == False,
            )
            .all()
        )
        for ep in due_24h:
            display_time = (ep.event.date + timedelta(hours=8)).strftime('%I:%M %p')
            db.session.add(Notification(
                user_id=ep.user_id,
                title=f"Event Tomorrow: {ep.event.title}",
                message=f"Reminder: '{ep.event.title}' is happening tomorrow at {display_time}.",
                type='event',
                link=f"/{ep.user.role}/events",
            ))
            ep.reminder_24h_sent = True

        # 1-hour reminders
        due_1h = (
            EventParticipant.query
            .join(Event, EventParticipant.event_id == Event.id)
            .filter(
                Event.status == 'approved',
                Event.date >= window_1h_lo,
                Event.date <= window_1h_hi,
                EventParticipant.reminder_1h_sent == False,
            )
            .all()
        )
        for ep in due_1h:
            db.session.add(Notification(
                user_id=ep.user_id,
                title=f"Starting Soon: {ep.event.title}",
                message=f"'{ep.event.title}' starts in about 1 hour. Get ready!",
                type='event',
                link=f"/{ep.user.role}/events",
            ))
            ep.reminder_1h_sent = True

        db.session.commit()
