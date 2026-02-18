"""
conftest.py - Pytest configuration and shared fixtures for GenCon SG tests.

CRITICAL: FLASK_ENV must be set BEFORE importing app, because the module-level
`app = create_app()` in app.py runs at import time.  Setting it here (before
any app import) ensures TestingConfig is used, which points to
sqlite:///:memory: and sets TESTING=True (so create_app skips db.create_all).
"""
import os
os.environ.setdefault("FLASK_ENV", "testing")

import pytest
from app import create_app
from extensions import db as _db
from models import User, Streak


def _make_user(username, email, full_name, age, role, password="TestPass1"):
    """Helper: create a user + streak record and commit."""
    user = User(
        username=username,
        email=email,
        full_name=full_name,
        age=age,
        role=role,
    )
    user.set_password(password)
    _db.session.add(user)
    _db.session.flush()          # populate user.id without a full commit
    streak = Streak(user_id=user.id)
    _db.session.add(streak)
    _db.session.commit()
    return user


@pytest.fixture()
def app():
    """
    Provide a Flask app configured for testing.
    Each test gets a fresh in-memory SQLite database via create_app('testing').
    """
    flask_app = create_app('testing')
    ctx = flask_app.app_context()
    ctx.push()
    _db.create_all()

    yield flask_app

    _db.session.remove()
    _db.drop_all()
    ctx.pop()


@pytest.fixture()
def client(app):
    """Return a Flask test client."""
    return app.test_client()


@pytest.fixture()
def senior_user(app):
    """Create and return a senior test user."""
    return _make_user(
        "sen_test", "senior@test.com", "Senior Tester", 70, "senior"
    )


@pytest.fixture()
def youth_user(app):
    """Create and return a youth test user."""
    return _make_user(
        "yth_test", "youth@test.com", "Youth Tester", 20, "youth"
    )


@pytest.fixture()
def admin_user(app):
    """Create and return an admin test user."""
    return _make_user(
        "adm_test", "admin@test.com", "Admin Tester", 35, "admin"
    )
