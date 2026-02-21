# GenCon SG

A **Flask-based intergenerational platform** connecting seniors and youths in Singapore through stories, events, communities, real-time chat, and multiplayer board games.

---

## Features

### 👴 Senior Portal
- **Stories** – Share and browse life stories with photo/video uploads
- **Messages** – 1-on-1 real-time chat with youth partners (with translation support)
- **Events** – Browse, RSVP, and view upcoming community events
- **Communities** – Join interest groups and participate in group chats
- **Games** – Play Chess, Xiangqi, and Tic-Tac-Toe with matched youth
- **Daily Check-in** – Earn points and maintain login streaks
- **Profile** – Manage profile picture, bio, and accessibility settings (font size)

### 🧑 Youth Portal
- **Story Feed** – React to and comment on senior stories
- **Messages** – Chat with paired seniors; automatic multi-language translation
- **Events** – Browse and RSVP to events
- **Communities** – Join groups and chat
- **Games** – Challenge paired seniors to multiplayer board games
- **Badges** – Earn achievement badges for engagement milestones
- **Profile** – Manage profile and choose app themes

### 🔧 Admin Portal
- **Dashboard** – Platform-wide analytics and activity overview
- **User Management** – View, activate/deactivate all user accounts
- **Pair Management** – Create and manage senior–youth pairings
- **Event Management** – Create, edit, approve/reject events
- **Community Management** – Create and moderate communities
- **Chat Moderation** – Review AI-analysed chat reports
- **Analytics** – Engagement trends, ELO game rankings, inactive user alerts

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web Framework | Flask 3.0 + Werkzeug |
| Database | SQLite via Flask-SQLAlchemy 3.1 |
| Forms & Validation | Flask-WTF / WTForms |
| Real-time | Flask-SocketIO 5.3 + eventlet |
| Translation | deep-translator (EN / ZH / MS / TA) |
| PDF Export | fpdf2 |
| AI Moderation | DeepSeek API (via `requests`) |
| Testing | pytest |

---

## Project Structure

```
WDP-Assignment/
├── app.py                  # Application factory (create_app)
├── config.py               # Dev / Testing / Production config classes
├── extensions.py           # Shared Flask extensions (db, socketio)
├── models.py               # 16 SQLAlchemy database models
├── forms.py                # WTForms form definitions
├── socket_handlers.py      # Socket.IO event handlers (real-time chat/games)
├── ai_utils.py             # DeepSeek AI integration for chat moderation
├── utils.py                # Shared helpers (text filtering, file uploads)
├── seed_db.py              # Database seeding script
├── blueprints/
│   ├── auth.py             # /auth — Login, Register, Logout
│   ├── main.py             # / — Landing page, support, public API
│   ├── senior.py           # /senior — All senior-facing routes
│   ├── youth.py            # /youth — All youth-facing routes
│   ├── admin.py            # /admin — All admin-facing routes
│   └── decorators.py       # Role-based access decorators
├── templates/              # Jinja2 HTML templates (68 files)
├── static/                 # CSS, JS, images
│   ├── css/
│   └── js/
├── requirements.txt
└── database.db             # SQLite database (auto-created on first run)
```

---

## Getting Started

### Prerequisites
- **Python 3.10+**
- `pip` package manager

### 1. Clone the Repository

```bash
git clone <repository-url>
cd WDP-Assignment
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables

```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Windows (PowerShell)
$env:SECRET_KEY = "<your-generated-key>"

# macOS / Linux
export SECRET_KEY="<your-generated-key>"
```

> **Note:** In development mode, a fallback insecure key is used automatically with a warning if `SECRET_KEY` is not set. Always set it for production.

### 5. (Optional) Seed the Database

```bash
python seed_db.py
```

### 6. Run the Application

```bash
python app.py
```

The server will start at **http://localhost:5001**.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes (Production) | Flask secret key for session signing and CSRF |
| `FLASK_ENV` | No | `development` (default), `testing`, or `production` |
| `DATABASE_URL` | No | Override SQLite with a custom DB URI (e.g., PostgreSQL) |
| `ALLOWED_ORIGINS` | No | Comma-separated CORS origins for Socket.IO (default: `*`) |

---

## Running Tests

```bash
pytest
```

Test files:
- `test_basic.py` — Smoke tests for core routes
- `test_characterization.py` — Characterization tests for all blueprints
- `conftest.py` — Shared pytest fixtures (in-memory SQLite DB)

---

## User Roles

| Role | Registration | Default Landing |
|---|---|---|
| **Senior** | Requires an invite code from Admin | `/senior/dashboard` |
| **Youth** | Requires an invite code from Admin | `/youth/dashboard` |
| **Admin** | Pre-seeded via `seed_db.py` | `/admin/dashboard` |

---

## Configuration Environments

| Environment | Debug | Database | Use case |
|---|---|---|---|
| `development` | Off | `database.db` | Local development |
| `testing` | Off | In-memory SQLite | Automated tests |
| `production` | Off | `DATABASE_URL` env var | Deployment |

---

## Key Database Models

`User`, `SeniorProfile`, `YouthProfile`, `Message`, `Story`, `StoryReaction`, `Comment`, `Event`, `EventRSVP`, `Community`, `CommunityMember`, `CommunityPost`, `GameSession`, `GameHistory`, `ChatReport`, `SupportTicket`

---

## Accessibility & Localisation

- **Font sizes** for seniors: Normal (18px), Large (20px), XL (24px)
- **Themes** for youth: Light, Dark, Blue, Purple
- **In-chat translation**: English, Chinese (Simplified), Malay, Tamil — powered by `deep-translator`

---

## License

This project is developed as a Web Development Project (WDP) assignment. All rights reserved.
