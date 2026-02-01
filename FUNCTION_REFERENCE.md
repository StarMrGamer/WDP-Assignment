# Function Reference Guide

> **How to use:** Open the file listed, then press `Ctrl+F` and search for the keyword in the **Search Keyword** column.

---

## Python Backend

### app.py

| Search Keyword | Description |
|---|---|
| `def calculate_elo` | Calculates new ELO ratings for two players after a game |
| `def handle_game_over` | Finalizes a game session: updates ELO, records history, awards streak points |
| `def on_game_over` | Socket.IO handler for 'game_over' event |
| `def on_join` | Socket.IO handler for 'join' event; joins a game room |
| `def on_challenge` | Socket.IO handler for 'challenge' event; forwards challenge to buddy |
| `def on_ready` | Socket.IO handler for 'ready' event; starts game when both ready |
| `def on_forfeit` | Socket.IO handler for 'forfeit' event; ends game, awards win |
| `def on_move` | Socket.IO handler for 'move' event; broadcasts move to opponent |
| `def on_game_chat` | Socket.IO handler for 'game_chat'; filters and broadcasts messages |
| `def on_join_community` | Socket.IO handler to join a community chat room |
| `def on_leave_community` | Socket.IO handler to leave a community chat room |
| `def on_community_message` | Socket.IO handler for community messages |
| `def on_connect` | Socket.IO handler for client connect |
| `def on_disconnect` | Socket.IO handler for client disconnect |
| `def push_notification` | SQLAlchemy after_insert listener for pushing notifications via Socket.IO |
| `def patch_db` | Safely executes ALTER TABLE or other SQL patches |
| `def inject_user` | Context processor injecting session data and streak into templates |
| `def index` | Landing page route; redirects logged-in users to dashboard |
| `def add_security_headers` | After-request hook adding Content-Security-Policy headers |
| `def not_found_error` | Error handler for 404 |
| `def internal_error` | Error handler for 500 |
| `def forbidden_error` | Error handler for 403 |
| `def timeago_filter` | Jinja2 filter converting datetime to relative time string |
| `def format_date_filter` | Jinja2 filter formatting datetime with SGT offset |
| `def date_filter` | Jinja2 filter for formatting datetime to date string |
| `def fix_pfp_filter` | Jinja2 filter ensuring profile picture paths have correct prefix |
| `def get_notifications` | API endpoint returning unread notifications as JSON |
| `def dismiss_notification` | API endpoint to mark a notification as read |
| `def mark_all_notifications_read` | API endpoint to mark all notifications as read |
| `def favicon` | Serves the favicon |
| `def get_streak` | API endpoint returning current user's streak and points |

### config.py

| Search Keyword | Description |
|---|---|
| `class Config` | Base configuration class with all app settings |
| `class DevelopmentConfig` | Development config with DEBUG=True |
| `class TestingConfig` | Testing config using in-memory SQLite |
| `class ProductionConfig` | Production config with DEBUG=False |
| `def get_config` | Returns config class based on environment name |

### models.py

| Search Keyword | Description |
|---|---|
| `class User` | User model for all accounts (senior, youth, admin) |
| `def set_password` | Hashes and stores a password |
| `def check_password` | Verifies a password against the stored hash |
| `def interests` | Property getter/setter for user interests (JSON) |
| `def languages` | Property getter/setter for user languages (JSON) |
| `def accessibility_settings` | Property getter/setter for accessibility settings (JSON) |
| `class Story` | Model for senior life stories |
| `class StoryReaction` | Model for story reactions (heart, smile, clap, hug) |
| `class StoryComment` | Model for text comments on stories |
| `class Message` | Model for chat messages between buddies |
| `class Pair` | Model for senior-youth buddy pairs |
| `class Event` | Model for events/activities |
| `class EventParticipant` | Junction model for event registrations |
| `class Community` | Model for interest-based communities |
| `class CommunityMember` | Junction model for community memberships |
| `class CommunityPost` | Model for posts within communities |
| `class Streak` | Model for user engagement streaks and game stats |
| `class Badge` | Model for achievement badges |
| `class ChatReport` | Model for reported chat messages/posts |
| `class Checkin` | Model for weekly senior mood check-ins |
| `class Notification` | Model for user notifications |
| `class RegistrationCode` | Model for registration codes |
| `class Game` | Model for game definitions in the arcade |
| `class GameSession` | Model for active game sessions between two users |
| `class GameHistory` | Model for completed game records with ELO |
| `class TicTacToeSession` | Model for Tic-Tac-Toe specific sessions |

### forms.py

| Search Keyword | Description |
|---|---|
| `class LoginForm` | Form for user login |
| `class RegistrationForm` | Form for user registration with validation |
| `def validate_username` | Checks username uniqueness |
| `def validate_email` | Checks email uniqueness |
| `def validate_registration_code` | Checks registration code is valid and unused |
| `def validate_age` | Enforces age rules based on role |
| `def validate_phone` | Validates Singapore phone number format |
| `class ProfileForm` | Form for profile editing |
| `class StoryForm` | Form for creating/editing stories |
| `class MessageForm` | Form for sending chat messages |

### utils.py

| Search Keyword | Description |
|---|---|
| `def filter_text` | Replaces profanity/unkind words with asterisks |

### seed_db.py

| Search Keyword | Description |
|---|---|
| `def seed_data` | Drops and recreates all tables, seeds sample data |

### fix_database.py

| Search Keyword | Description |
|---|---|
| `def fix_database` | Adds missing photo_url column to community_posts table |

---

## Blueprints

### blueprints/auth.py

| Search Keyword | Description |
|---|---|
| `def login` | Route handler for user login with credential validation |
| `def setup` | Route handler for post-registration interest selection |
| `def register` | Route handler for new user registration |
| `def logout` | Clears session and redirects to index |
| `def change_password` | API endpoint to change the user's password |
| `def update_user_streak` | Updates daily login streak (increment or reset) |
| `def check_streak_badges` | Awards badge when user reaches a streak milestone |

### blueprints/admin.py

| Search Keyword | Description |
|---|---|
| `def admin_required` | Decorator ensuring user is logged in as admin |
| `def dashboard` | Admin dashboard with user counts and recent activity |
| `def users` | Displays all non-admin users with filtering |
| `def user_detail` | Shows detailed info for a specific user |
| `def toggle_user_status` | Enables or disables a user account |
| `def delete_user` | Permanently deletes a user account |
| `def pairs` | Displays all buddy pairs with health status |
| `def create_pair` | Creates a new senior-youth buddy pair |
| `def delete_pair` | Deletes a buddy pair |
| `def send_pair_reminder` | Sends reminder to an inactive pair |
| `def events` | Displays all events ordered by date |
| `def event_detail` | Shows event details and participants |
| `def edit_event` | Edits an existing event |
| `def create_event` | Creates a new event |
| `def delete_event` | Deletes an event |
| `def communities` | Displays all communities |
| `def create_community` | Creates a new community with optional photo |
| `def delete_community` | Deletes a community and cleans up photo |
| `def manage_community` | Management view for a community |
| `def update_community` | Updates community details |
| `def delete_community_post` | Deletes a post from a community chat |
| `def remove_community_member` | Removes a user from a community |
| `def add_community_member` | Adds a user to a community |
| `def reports` | Displays chat reports with status filtering |
| `def report_detail` | Views and manages an individual report |
| `def analytics` | Displays platform analytics |
| `def codes` | Manages registration codes |
| `def profile` | Displays admin profile page |

### blueprints/senior.py

| Search Keyword | Description |
|---|---|
| `def login_required` | Decorator ensuring user is logged in as senior |
| `def dashboard` | Senior dashboard with stats, buddy info, stories, events |
| `def story_feed` | All stories with category and role filtering |
| `def story_detail` | Full story view with reactions and comments |
| `def stories` | Lists stories created by the logged-in senior |
| `def create_story` | Creates a new story with optional photo |
| `def edit_story` | Edits an existing story (ownership-checked) |
| `def delete_story` | Deletes a story and its photo |
| `def messages` | Messaging interface with paired youth buddy |
| `def get_messages_json` | API returning conversation messages as JSON |
| `def report_message` | Creates a ChatReport for a message |
| `def report_community_post` | Creates a ChatReport for a community post |
| `def events` | Displays upcoming events with registration status |
| `def register_event` | Toggles event registration for the user |
| `def communities` | Lists all communities with join status and unread counts |
| `def view_community` | Views community chat |
| `def upload_community_photo` | Handles photo upload for community chat |
| `def join_community` | Toggles community membership |
| `def games` | Game lobby with buddy info, stats, ELO, history |
| `def challenge_buddy` | Creates/joins game session and sends challenge notification |
| `def chess_game` | Renders International Chess game page |
| `def xiangqi_game` | Renders Chinese Chess game page |
| `def tictactoe_game` | Renders Tic-Tac-Toe game page |
| `def profile` | Senior profile view/edit |
| `def public_profile` | Views another user's public profile |
| `def checkin` | Weekly mood check-in form |
| `def save_accessibility_settings` | API to save accessibility preferences |

### blueprints/youth.py

| Search Keyword | Description |
|---|---|
| `def login_required` | Decorator ensuring user is logged in as youth |
| `def dashboard` | Youth dashboard with buddy info, stories, badge count |
| `def stories` | Lists stories created by the logged-in youth |
| `def create_story` | Creates a new story with optional photo |
| `def edit_story` | Edits an existing story (ownership-checked) |
| `def delete_story` | Deletes a story and its photo |
| `def story_feed` | All stories with category and role filtering |
| `def story_detail` | Full story view with reactions and comments |
| `def messages` | Messaging interface with paired senior buddy |
| `def get_messages_json` | API returning conversation messages as JSON |
| `def report_message` | Creates a ChatReport for a message |
| `def report_community_post` | Creates a ChatReport for a community post |
| `def events` | Displays upcoming events with registration status |
| `def register_event` | Toggles event registration for the user |
| `def communities` | Lists all communities with join status and unread counts |
| `def view_community` | Views community chat |
| `def upload_community_photo` | Handles photo upload for community chat |
| `def join_community` | Toggles community membership |
| `def badges` | Displays earned badges, milestones, leaderboard, progress |
| `def profile` | Youth profile view/edit |
| `def public_profile` | Views another user's public profile |
| `def api_react_story` | API to toggle/update a reaction on a story |
| `def api_comment_story` | API to add a comment to a story |
| `def games` | Game lobby with buddy info, stats, ELO, history |
| `def challenge_buddy` | Creates/joins game session and sends challenge notification |
| `def chess_game` | Renders International Chess game page |
| `def xiangqi_game` | Renders Chinese Chess game page |
| `def tictactoe_game` | Renders Tic-Tac-Toe game page |

---

## JavaScript (static/js/)

### main.js

| Search Keyword | Description |
|---|---|
| `function setFontSize` | Sets and persists the body font size preference |
| `function toggleHighContrast` | Toggles high contrast mode on/off |
| `function setTheme` | Applies a color theme and persists preference |
| `function loadAccessibilityPreferences` | Restores saved font/contrast/theme from localStorage |
| `function loadNotifications` | Fetches notifications from API and renders dropdown |
| `function dismissNotification` | Dismisses a notification by ID via POST |
| `function loadStreak` | Fetches user's login streak data |
| `function showBadgeModal` | Displays modal for a newly earned badge |
| `function showDailyRewardModal` | Displays modal for daily streak reward |
| `function showToast` | Shows a temporary toast notification |
| `function validateEmail` | Validates an email string |
| `function validatePassword` | Checks password strength |
| `function updatePasswordStrength` | Visually reflects password strength in DOM |
| `function validateAge` | Validates age based on user role |
| `function showConfirmModal` | Displays a confirmation dialog with callback |
| `async function postData` | Generic async POST request helper |
| `async function getData` | Generic async GET request helper |
| `function previewImage` | Previews selected image before upload |
| `function formatTimeAgo` | Formats date as relative time string |
| `function formatCountdown` | Formats future date as countdown text |
| `window.initNotificationSocket` | Sets up Socket.IO listener for push notifications |
| `function fixNavbarProfile` | Fixes navbar profile picture sizing |
| `window.openReportModal` | Opens report modal for a message ID |
| `window.submitReport` | Submits a report to the server |

### animated-nav.js

| Search Keyword | Description |
|---|---|
| `function updateBorderPosition` | Sets sliding border position under a nav item |
| `function setActiveFromCurrentPage` | Highlights nav item matching current URL |

### chat.js

| Search Keyword | Description |
|---|---|
| `function fetchMessages` | Fetches messages from API and triggers re-render |
| `function renderMessages` | Builds and injects HTML for chat messages |
| `function scrollToBottom` | Scrolls chat container to latest message |

### socket_chess.js

| Search Keyword | Description |
|---|---|
| `function initButtons` | Wires up Ready and Forfeit button handlers |
| `function startGame` | Activates chess game UI, hides waiting overlay |
| `function onDragStart` | Validates whether a piece drag is allowed |
| `function onDrop` | Handles piece drop, validates move, emits to server |
| `function onSnapEnd` | Syncs board display after animation |
| `function updateStatus` | Updates game status text, PGN, detects game over |

### socket_tictactoe.js

| Search Keyword | Description |
|---|---|
| `function initButtons` | Wires up Ready and Forfeit button handlers |
| `function startGame` | Activates tic-tac-toe UI and initializes board |
| `function setGame` | Creates the 3x3 board grid with click listeners |
| `function setPiece` | Handles tile click: places symbol, checks winner |
| `function checkWinner` | Checks rows/columns/diagonals for winner or tie |
| `function updateStatus` | Updates turn indicator text |
| `function boardToString` | Serializes 3x3 board to 9-character string |

### standalone_chess.js

| Search Keyword | Description |
|---|---|
| `var onDragStart` | Prevents picking up pieces when game over or wrong turn |
| `var onDrop` | Handles piece drop and updates status |
| `var onSnapEnd` | Syncs board position after animation |
| `function updateStatus` | Updates status text and PGN for standalone chess |

### tictactoe.js

| Search Keyword | Description |
|---|---|
| `function setGame` | Creates 3x3 board DOM elements with click handlers |
| `function setPiece` | Places symbol on tile and checks for winner |
| `function checkWinner` | Checks all rows/columns/diagonals for win or tie |
| `function updateStatus` | Updates turn indicator text |
| `function resetGame` | Clears board and reinitializes game |

### xiangqi_game.js

| Search Keyword | Description |
|---|---|
| `function flipBoard` | Toggles board orientation (red/black perspective) |
| `function drawBoard` | Renders full Xiangqi board as HTML table |
| `function highlightMoves` | Shows legal move indicators on valid squares |
| `function setBot` | Configures AI bot (name, depth, opening book) |
| `function setBoardTheme` | Changes board background image |
| `function setPieceTheme` | Changes piece image style |
| `function playSound` | Plays move or capture sound effect |
| `function dragPiece` | Handles drag start, highlights legal moves |
| `function dragOver` | Handles drag over event |
| `function dropPiece` | Handles piece drop, validates move, triggers bot |
| `function tapPiece` | Handles click-to-move (two-click selection) |
| `function getBookMove` | Looks up position in opening book |
| `function isGameOver` | Checks for repetition, checkmate, or draw |
| `function think` | Runs engine AI: book move then search |
| `function movePiece` | Applies a move, redraws board, checks game over |
| `function undo` | Takes back the last move |
| `function validateMove` | Validates a move against engine's legal moves |
| `function getGamePgn` | Builds PGN string from move stack |
| `function updatePgn` | Updates PGN textarea with current notation |
| `function downloadPgn` | Downloads game as a PGN file |
| `function newGame` | Resets state and starts fresh game |

### xiangqi_socket.js

| Search Keyword | Description |
|---|---|
| `function startGame` | Activates multiplayer Xiangqi UI, loads saved state |
| `window.isGameOver` | Wraps isGameOver to emit game_over socket event |
| `window.think` | Disables AI thinking in multiplayer mode |
| `window.movePiece` | Wraps movePiece to emit moves via socket |
| `function applyRemoteMove` | Applies opponent's move received via socket |
| `window.tapPiece` | Wraps tapPiece with turn/ownership checks |
| `window.dragPiece` | Wraps dragPiece with turn/ownership checks |
| `function isGameUIActive` | Checks if game UI is active |
| `function isMyTurn` | Returns true if it's the player's turn |
| `function isMyPiece` | Checks if a piece belongs to the current player |

### wukong.js (Xiangqi Engine)

| Search Keyword | Description |
|---|---|
| `var Engine = function` | Constructor for the Wukong Xiangqi engine |
| `this.resetBoard` | Resets board and game state to initial values |
| `this.setBoard` | Parses FEN string and sets up position |
| `this.printBoard` | Prints board state to console |
| `this.moveFromString` | Converts move string to encoded move integer |
| `this.loadMoves` | Loads and applies a sequence of move strings |
| `this.getMoves` | Returns array of all moves played |
| `this.isSquareAttacked` | Checks if a square is attacked by a color |
| `this.generateMoves` | Generates all pseudo-legal moves |
| `this.generateLegalMoves` | Filters to only legal moves |
| `this.makeMove` | Applies a move to the board |
| `this.takeBack` | Undoes the last move |
| `this.evaluate` | Returns static evaluation score |
| `this.searchPosition` | Iterative deepening search, returns best move |
| `var encodeMove` | Encodes source/target/pieces into move integer |
| `var pushMove` | Validates and pushes a move into move list |
| `var quiescence` | Quiescence search for tactical sequences |
| `var negamax` | Main alpha-beta search with pruning |
| `var isRepetition` | Detects position repetition |

### isdevtoolopen.js

| Search Keyword | Description |
|---|---|
| `function emitEvent` | Dispatches custom 'devtoolschange' event |
| `function main` | Checks window dimensions to detect DevTools |
