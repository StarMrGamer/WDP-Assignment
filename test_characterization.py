"""
test_characterization.py — Characterization tests for GenCon SG.

These tests lock in the CURRENT observable behaviour of every route so that
the upcoming Application-Factory refactor cannot silently break anything.

Rules:
  - DO NOT change these tests during the refactor.
  - If a test goes red after a code change, the refactor introduced a
    regression and must be fixed before continuing.
  - Tests assert on STATUS CODES and coarse content only — they do NOT
    assert on exact HTML markup, which would make them too brittle.
"""
import pytest
from models import User, Notification, Streak
from app import db


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

PASSWORD = "TestPass1"


def _login(client, username, password=PASSWORD, follow=False):
    return client.post(
        "/auth/login",
        data={"username": username, "password": password},
        follow_redirects=follow,
    )


def _login_as(client, user, follow=False):
    return _login(client, user.username, follow=follow)


# ─────────────────────────────────────────────
# Public / Anonymous routes
# ─────────────────────────────────────────────

class TestPublicRoutes:
    def test_index_anonymous_returns_200(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_index_contains_brand(self, client):
        r = client.get("/")
        assert b"GenCon" in r.data

    def test_about_returns_200(self, client):
        assert client.get("/about").status_code == 200

    def test_privacy_returns_200(self, client):
        assert client.get("/privacy").status_code == 200

    def test_terms_returns_200(self, client):
        assert client.get("/terms").status_code == 200

    def test_support_get_returns_200(self, client):
        assert client.get("/support").status_code == 200

    def test_404_handler(self, client):
        r = client.get("/this/route/does/not/exist")
        assert r.status_code == 404


# ─────────────────────────────────────────────
# Index redirect when logged in
# ─────────────────────────────────────────────

class TestIndexRedirects:
    def test_index_senior_redirects_to_senior_dashboard(self, client, senior_user):
        _login_as(client, senior_user)
        r = client.get("/")
        assert r.status_code == 302
        assert "/senior/dashboard" in r.headers["Location"]

    def test_index_youth_redirects_to_youth_dashboard(self, client, youth_user):
        _login_as(client, youth_user)
        r = client.get("/")
        assert r.status_code == 302
        assert "/youth/dashboard" in r.headers["Location"]

    def test_index_admin_redirects_to_admin_dashboard(self, client, admin_user):
        _login_as(client, admin_user)
        r = client.get("/")
        assert r.status_code == 302
        assert "/admin/dashboard" in r.headers["Location"]


# ─────────────────────────────────────────────
# Auth blueprint
# ─────────────────────────────────────────────

class TestAuthRoutes:
    def test_login_page_returns_200(self, client):
        assert client.get("/auth/login").status_code == 200

    def test_register_page_returns_200(self, client):
        assert client.get("/auth/register").status_code == 200

    def test_login_valid_senior_redirects_to_dashboard(self, client, senior_user):
        r = _login_as(client, senior_user)
        assert r.status_code == 302
        assert "/senior/dashboard" in r.headers["Location"]

    def test_login_valid_youth_redirects_to_dashboard(self, client, youth_user):
        r = _login_as(client, youth_user)
        assert r.status_code == 302
        assert "/youth/dashboard" in r.headers["Location"]

    def test_login_valid_admin_redirects_to_dashboard(self, client, admin_user):
        r = _login_as(client, admin_user)
        assert r.status_code == 302
        assert "/admin/dashboard" in r.headers["Location"]

    def test_login_invalid_password_stays_on_login(self, client, senior_user):
        r = _login(client, senior_user.username, password="wrongpassword", follow=True)
        assert r.status_code == 200
        assert b"Invalid username or password" in r.data

    def test_login_nonexistent_user_stays_on_login(self, client):
        r = _login(client, "ghost_user", follow=True)
        assert r.status_code == 200
        assert b"Invalid username or password" in r.data

    def test_logout_redirects_to_index(self, client, senior_user):
        _login_as(client, senior_user)
        r = client.get("/auth/logout")
        assert r.status_code == 302
        assert "/" in r.headers["Location"]

    def test_logout_shows_goodbye_message(self, client, senior_user):
        _login_as(client, senior_user)
        r = client.get("/auth/logout", follow_redirects=True)
        assert b"logged out" in r.data

    def test_setup_requires_login_redirects(self, client):
        r = client.get("/auth/setup")
        assert r.status_code == 302
        assert "/auth/login" in r.headers["Location"]

    def test_setup_accessible_when_logged_in(self, client, senior_user):
        _login_as(client, senior_user)
        r = client.get("/auth/setup")
        assert r.status_code == 200

    def test_logged_in_user_visiting_login_redirects(self, client, senior_user):
        _login_as(client, senior_user)
        r = client.get("/auth/login")
        assert r.status_code == 302

    def test_logged_in_user_visiting_register_redirects(self, client, senior_user):
        _login_as(client, senior_user)
        r = client.get("/auth/register")
        assert r.status_code == 302


# ─────────────────────────────────────────────
# Access control — unauthenticated
# ─────────────────────────────────────────────

class TestUnauthenticatedAccess:
    @pytest.mark.parametrize("url", [
        "/senior/dashboard",
        "/senior/stories",
        "/senior/events",
        "/senior/communities",
        "/senior/games",
        "/senior/profile",
        "/senior/checkin",
        "/senior/chatbot",
    ])
    def test_senior_routes_redirect_when_anonymous(self, client, url):
        r = client.get(url)
        assert r.status_code == 302
        assert "/auth/login" in r.headers["Location"]

    @pytest.mark.parametrize("url", [
        "/youth/dashboard",
        "/youth/stories",
        "/youth/events",
        "/youth/communities",
        "/youth/games",
        "/youth/profile",
        "/youth/badges",
    ])
    def test_youth_routes_redirect_when_anonymous(self, client, url):
        r = client.get(url)
        assert r.status_code == 302
        assert "/auth/login" in r.headers["Location"]

    @pytest.mark.parametrize("url", [
        "/admin/dashboard",
        "/admin/users",
        "/admin/pairs",
        "/admin/events",
        "/admin/reports",
        "/admin/analytics",
        "/admin/codes",
        "/admin/communities",
    ])
    def test_admin_routes_redirect_when_anonymous(self, client, url):
        r = client.get(url)
        assert r.status_code == 302
        assert "/auth/login" in r.headers["Location"]


# ─────────────────────────────────────────────
# Access control — wrong role
# ─────────────────────────────────────────────

class TestRoleEnforcement:
    def test_youth_cannot_access_senior_dashboard(self, client, youth_user):
        _login_as(client, youth_user)
        r = client.get("/senior/dashboard", follow_redirects=True)
        assert b"Access denied" in r.data

    def test_senior_cannot_access_youth_dashboard(self, client, senior_user):
        _login_as(client, senior_user)
        r = client.get("/youth/dashboard", follow_redirects=True)
        assert b"Access denied" in r.data

    def test_senior_cannot_access_admin_dashboard(self, client, senior_user):
        _login_as(client, senior_user)
        r = client.get("/admin/dashboard", follow_redirects=True)
        assert b"Access denied" in r.data

    def test_youth_cannot_access_admin_dashboard(self, client, youth_user):
        _login_as(client, youth_user)
        r = client.get("/admin/dashboard", follow_redirects=True)
        assert b"Access denied" in r.data


# ─────────────────────────────────────────────
# Senior blueprint — authenticated access
# ─────────────────────────────────────────────

class TestSeniorRoutes:
    @pytest.fixture(autouse=True)
    def login_senior(self, client, senior_user):
        _login_as(client, senior_user)

    def test_dashboard_returns_200(self, client):
        assert client.get("/senior/dashboard").status_code == 200

    def test_dashboard_contains_dashboard(self, client):
        r = client.get("/senior/dashboard")
        assert b"Dashboard" in r.data

    def test_stories_returns_200(self, client):
        assert client.get("/senior/stories").status_code == 200

    def test_create_story_get_returns_200(self, client):
        assert client.get("/senior/create_story").status_code == 200

    def test_events_returns_200(self, client):
        assert client.get("/senior/events").status_code == 200

    def test_communities_returns_200(self, client):
        assert client.get("/senior/communities").status_code == 200

    def test_games_returns_200(self, client):
        assert client.get("/senior/games").status_code == 200

    def test_profile_returns_200(self, client):
        assert client.get("/senior/profile").status_code == 200

    def test_checkin_get_returns_200(self, client):
        assert client.get("/senior/checkin").status_code == 200

    def test_chatbot_returns_200(self, client):
        assert client.get("/senior/chatbot").status_code == 200

    def test_suggest_event_get_returns_200(self, client):
        assert client.get("/senior/events/suggest").status_code == 200

    def test_messages_returns_200_no_buddy(self, client):
        # Senior with no pair: renders page with no buddy
        assert client.get("/senior/messages").status_code == 200

    def test_story_404_for_nonexistent(self, client):
        assert client.get("/senior/story/99999").status_code == 404


# ─────────────────────────────────────────────
# Youth blueprint — authenticated access
# ─────────────────────────────────────────────

class TestYouthRoutes:
    @pytest.fixture(autouse=True)
    def login_youth(self, client, youth_user):
        _login_as(client, youth_user)

    def test_dashboard_returns_200(self, client):
        assert client.get("/youth/dashboard").status_code == 200

    def test_stories_returns_200(self, client):
        assert client.get("/youth/stories").status_code == 200

    def test_create_story_get_returns_200(self, client):
        assert client.get("/youth/create_story").status_code == 200

    def test_events_returns_200(self, client):
        assert client.get("/youth/events").status_code == 200

    def test_communities_returns_200(self, client):
        assert client.get("/youth/communities").status_code == 200

    def test_games_returns_200(self, client):
        assert client.get("/youth/games").status_code == 200

    def test_profile_returns_200(self, client):
        assert client.get("/youth/profile").status_code == 200

    def test_badges_returns_200(self, client):
        assert client.get("/youth/badges").status_code == 200

    def test_suggest_event_get_returns_200(self, client):
        assert client.get("/youth/events/suggest").status_code == 200

    def test_messages_returns_200_no_buddy(self, client):
        assert client.get("/youth/messages").status_code == 200

    def test_story_404_for_nonexistent(self, client):
        assert client.get("/youth/story/99999").status_code == 404


# ─────────────────────────────────────────────
# Admin blueprint — authenticated access
# ─────────────────────────────────────────────

class TestAdminRoutes:
    @pytest.fixture(autouse=True)
    def login_admin(self, client, admin_user):
        _login_as(client, admin_user)

    def test_dashboard_returns_200(self, client):
        assert client.get("/admin/dashboard").status_code == 200

    def test_users_returns_200(self, client):
        assert client.get("/admin/users").status_code == 200

    def test_pairs_returns_200(self, client):
        assert client.get("/admin/pairs").status_code == 200

    def test_events_returns_200(self, client):
        assert client.get("/admin/events").status_code == 200

    def test_create_event_get_returns_200(self, client):
        assert client.get("/admin/events/create").status_code == 200

    def test_create_pair_get_returns_200(self, client):
        assert client.get("/admin/pairs/create").status_code == 200

    def test_reports_returns_200(self, client):
        assert client.get("/admin/reports").status_code == 200

    def test_analytics_returns_200(self, client):
        assert client.get("/admin/analytics").status_code == 200

    def test_codes_returns_200(self, client):
        assert client.get("/admin/codes").status_code == 200

    def test_communities_returns_200(self, client):
        assert client.get("/admin/communities").status_code == 200

    def test_create_community_get_returns_200(self, client):
        assert client.get("/admin/communities/create").status_code == 200

    def test_support_tickets_returns_200(self, client):
        assert client.get("/admin/support-tickets").status_code == 200

    def test_profile_returns_200(self, client):
        assert client.get("/admin/profile").status_code == 200

    def test_user_detail_404_for_nonexistent(self, client):
        assert client.get("/admin/users/99999").status_code == 404

    def test_export_analytics_returns_csv(self, client):
        r = client.get("/admin/analytics/export")
        assert r.status_code == 200
        assert b"text/csv" in r.content_type.encode()


# ─────────────────────────────────────────────
# API routes — anonymous
# ─────────────────────────────────────────────

class TestApiAnonymous:
    def test_notifications_returns_empty_json(self, client):
        r = client.get("/api/notifications")
        assert r.status_code == 200
        data = r.get_json()
        assert data["count"] == 0
        assert data["notifications"] == []

    def test_streak_returns_zero(self, client):
        r = client.get("/api/streak")
        assert r.status_code == 200
        assert r.get_json()["currentStreak"] == 0

    def test_dismiss_notification_anonymous_returns_403(self, client):
        r = client.post("/api/notifications/1/dismiss")
        assert r.status_code == 403

    def test_mark_all_read_anonymous_returns_403(self, client):
        r = client.post("/api/notifications/mark-read")
        assert r.status_code == 403


# ─────────────────────────────────────────────
# API routes — authenticated
# ─────────────────────────────────────────────

class TestApiAuthenticated:
    def test_notifications_authenticated_returns_json(self, client, senior_user):
        _login_as(client, senior_user)
        r = client.get("/api/notifications")
        assert r.status_code == 200
        data = r.get_json()
        assert "count" in data
        assert "notifications" in data

    def test_streak_authenticated_returns_streak(self, client, senior_user):
        _login_as(client, senior_user)
        r = client.get("/api/streak")
        assert r.status_code == 200
        data = r.get_json()
        assert "currentStreak" in data

    def test_mark_all_read_authenticated_returns_success(self, client, senior_user):
        _login_as(client, senior_user)
        r = client.post("/api/notifications/mark-read")
        assert r.status_code == 200
        assert r.get_json()["success"] is True

    def test_dismiss_notification_not_owned_returns_403(self, client, senior_user, youth_user, app):
        # Create a notification belonging to youth, try to dismiss as senior
        with app.app_context():
            from models import Notification
            notif = Notification(
                user_id=youth_user.id,
                title="Test",
                message="Test notification",
                type="info",
            )
            db.session.add(notif)
            db.session.commit()
            notif_id = notif.id

        _login_as(client, senior_user)
        r = client.post(f"/api/notifications/{notif_id}/dismiss")
        assert r.status_code == 403


# ─────────────────────────────────────────────
# Support ticket submission
# ─────────────────────────────────────────────

class TestSupportTicket:
    def test_guest_submission_without_email_shows_error(self, client):
        r = client.post("/support", data={
            "ticket_type": "General Inquiry",
            "subject": "Test subject here",
            "description": "A long enough description for testing.",
            "guest_email": "",
        }, follow_redirects=True)
        assert r.status_code == 200
        assert b"Email is required" in r.data

    def test_authenticated_submission_redirects(self, client, senior_user):
        _login_as(client, senior_user)
        r = client.post("/support", data={
            "ticket_type": "General Inquiry",
            "subject": "Test subject here",
            "description": "A long enough description for testing.",
        }, follow_redirects=False)
        # Should redirect back to /support after successful submission
        assert r.status_code == 302


# ─────────────────────────────────────────────
# Error handlers
# ─────────────────────────────────────────────

class TestErrorHandlers:
    def test_404_returns_404_status(self, client):
        r = client.get("/nonexistent-page-xyz")
        assert r.status_code == 404

    def test_404_renders_error_template(self, client):
        r = client.get("/nonexistent-page-xyz")
        # Should not be an empty response
        assert len(r.data) > 0


# ─────────────────────────────────────────────
# Security headers
# ─────────────────────────────────────────────

class TestSecurityHeaders:
    def test_csp_header_present_on_main_pages(self, client):
        r = client.get("/")
        assert "Content-Security-Policy" in r.headers

    def test_csp_header_absent_on_portfolio(self, client):
        # Portfolio route skips CSP — verify route exists (may 404 for index.html
        # in test since file isn't present, but header behaviour is what matters)
        r = client.get("/profolio/")
        # Either 200 (file served) or 404 (file missing in test env) — either
        # way, CSP should NOT be set for this path
        assert "Content-Security-Policy" not in r.headers
