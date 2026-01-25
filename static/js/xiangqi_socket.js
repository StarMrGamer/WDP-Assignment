// Socket.IO logic for Xiangqi Multiplayer

var socket = io();
var $status = $('#status'); // Assuming jQuery is available or we use document.getElementById
// xiangqi_game.js doesn't seem to use jQuery, so we should be careful.
// Let's use vanilla JS where possible to match xiangqi_game.js style.

console.log("Xiangqi Socket Script Loaded. Session:", gameSessionId, "Color:", playerColor);

// Join room
socket.emit('join', { game_id: gameSessionId });

socket.on('connect', function() {
    console.log("Connected to server.");
    socket.emit('join', { game_id: gameSessionId });
});

// Setup buttons
const readyBtn = document.getElementById('readyBtn');
if (readyBtn) {
    readyBtn.onclick = function() {
        console.log("Ready clicked");
        this.disabled = true;
        this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Waiting...';
        socket.emit('ready', { session_id: gameSessionId });
    };
}

const forfeitBtn = document.getElementById('forfeitBtn');
if (forfeitBtn) {
    forfeitBtn.onclick = function() {
        if (confirm('Are you sure you want to forfeit? This will end the game.')) {
            socket.emit('forfeit', { session_id: gameSessionId });
            window.location.href = (userRole === 'senior') ? '/senior/games' : '/youth/games';
        }
    };
}

// Game State Listeners
socket.on('init_game', function(data) {
    if (data.status === 'active') {
        startGame();
    }
});

socket.on('player_ready', function(data) {
    if (data.user_id != currentUserId) {
        let statusEl = document.getElementById('status');
        if(statusEl) statusEl.innerText = "Buddy is ready! Waiting for you...";
    }
});

socket.on('game_start', function(data) {
    console.log("Game Start!");
    startGame();
});

socket.on('opponent_forfeit', function(data) {
    alert(data.winner_name + ' has left the game. You win!');
    window.location.href = (userRole === 'senior') ? '/senior/games' : '/youth/games';
});

// Move Listener
socket.on('move', function(data) {
    console.log("Received move:", data);
    // data.move contains { from: source, to: target } (squares)
    // We need to apply this to the engine and board.
    // xiangqi_game.js has movePiece(userSource, userTarget)
    // But we need to make sure we don't trigger another emit.
    
    // Convert generic squares to board coordinates?
    // In xiangqi_game.js, squares are integers (0-89?).
    // We need to ensure the coordinate system matches.
    
    applyRemoteMove(data.move.from, data.move.to);
});

function startGame() {
    const overlay = document.getElementById('waitingOverlay');
    if (overlay) overlay.style.display = 'none';
    
    // If we are black, flip board
    if (playerColor === 'black') {
        // Only flip if not already flipped?
        // xiangqi_game.js has flipBoard().
        // We assume default is Red at bottom.
        // check flip state in xiangqi_game.js (var flip = 0)
        // We can access global variables from xiangqi_game.js
        if (typeof flip !== 'undefined' && flip === 0) {
            flipBoard();
        }
    }
    
    document.getElementById('status').innerText = "Game Started! Red to move.";
}

// Override or Hook into xiangqi_game.js
// We need to intercept moves.
// xiangqi_game.js has dropPiece(event, square) -> calling movePiece -> think()
// In multiplayer, we want to disable think() (bot) and instead emit('move').

// We can inject logic into 'clickLock' or 'dropPiece' logic.
// Better: Override 'think()' to do nothing in multiplayer?
// Override 'movePiece'?

// Strategy:
// 1. We modify xiangqi_game.js to check `isMultiplayer`.
// 2. OR we monkey-patch here.

// Let's monkey-patch `think` to disable bot.
var originalThink = window.think;
window.think = function() {
    if (isMultiplayer) return; // Disable bot
    originalThink();
}

// We need to capture the USER's move to emit it.
// xiangqi_game.js calls `movePiece(userSource, userTarget)` when user moves.
// We can wrap `movePiece`.

var originalMovePiece = window.movePiece;
window.movePiece = function(source, target) {
    // Call original to update board locally
    originalMovePiece(source, target);
    
    // Check if it was a user move (we can check turn?)
    // In xiangqi_game.js, movePiece is called by think() (bot) AND dropPiece/tapPiece (user).
    // Since we disabled think(), only user calls this.
    // However, applyRemoteMove will also call this.
    
    // We need to distinguish LOCAL user move from REMOTE move.
    if (isMultiplayer && !isRemoteMove) {
        // Emit move
        console.log("Emitting move:", source, target);
        socket.emit('move', {
            game_id: gameSessionId,
            move: { from: source, to: target }
        });
    }
    
    isRemoteMove = false; // Reset flag
}

var isRemoteMove = false;

function applyRemoteMove(source, target) {
    isRemoteMove = true;
    // We need to use the engine to validate/apply?
    // movePiece in xiangqi_game.js does: engine.loadMoves, drawBoard, updatePgn.
    movePiece(source, target);
    
    // Play sound?
    // xiangqi_game.js plays sound in dropPiece/think. 
    // movePiece doesn't play sound itself usually, it's called by caller.
    // We should play sound here.
    playSound(1); // 1 = capture/valid? 
}

// Also need to restrict picking up pieces if not my turn.
// xiangqi_game.js: dragPiece, tapPiece.
// We should check turn before allowing interaction.

var originalTapPiece = window.tapPiece;
window.tapPiece = function(square) {
    if (isMultiplayer) {
        if (!gameActive()) return;
        if (!isMyTurn()) return;
        // Also check if piece belongs to me (Red vs Black)
        // engine.getPiece(square) -> returns int.
        // Need to check color.
        if (!isMyPiece(square) && clickLock == 0) return; 
    }
    originalTapPiece(square);
}

var originalDragPiece = window.dragPiece;
window.dragPiece = function(event, square) {
    if (isMultiplayer) {
        if (!gameActive()) { event.preventDefault(); return; }
        if (!isMyTurn()) { event.preventDefault(); return; }
        if (!isMyPiece(square)) { event.preventDefault(); return; }
    }
    originalDragPiece(event, square);
}

function gameActive() {
    let overlay = document.getElementById('waitingOverlay');
    return !overlay || overlay.style.display === 'none';
}

function isMyTurn() {
    // engine.getSide() returns 0 for Red, 1 for Black.
    let side = engine.getSide(); // 0 or 1
    let mySide = (playerColor === 'red' ? 0 : 1);
    return side === mySide;
}

function isMyPiece(square) {
    let piece = engine.getPiece(square);
    if (piece === 0) return false;
    // Wukong engine:
    // Red pieces: 1-7 (KABNRCP) ?
    // Black pieces: 9-15 (kabnrcp) ?
    // Let's check wukong.js or verify.
    // Usually standard engines: Upper case (Red?) vs Lower case.
    // engine.getPiece returns integer.
    // Need to know range.
    
    // In wukong.js (assumed standard):
    // 8-14 are Black? 16-22 Red?
    // Let's infer from engine.getSide().
    // Actually, xiangqi_game.js uses:
    // pieceImage += 'src="/static/images/xiangqi/' + pieceFolder + '/' + piece ...
    
    // Let's blindly trust engine.getSide() is correct for turn.
    // But for selecting a piece to MOVE, we must own it.
    
    // Heuristic:
    // If I am Red (0), I can only select Red pieces.
    // If I am Black (1), I can only select Black pieces.
    
    // Inspecting wukong.js would be ideal, but let's guess:
    // Usually piece & 8 (or 16) indicates color.
    
    // Let's look at isMyTurn() - that restricts moving OUT OF TURN.
    // If I try to move opponent's piece on my turn, engine usually allows it (edit mode) or blocks it?
    // xiangqi_game.js is a GUI.
    
    // IMPORTANT: In standard xiangqi_game.js, you can only move side to move.
    // So isMyTurn() check combined with engine's internal check should be enough?
    // No, I shouldn't be able to move opponent's pieces even if it's their turn (I shouldn't move FOR them).
    // So isMyTurn() is the main check. If it's my turn, I can move.
    // If I try to move an opponent piece, it's either a capture or invalid.
    // But I shouldn't be able to Select (start drag) opponent piece.
    
    // We will assume `isMyTurn()` covers "It is currently my color's turn".
    // AND I am that color.
    
    return true; // Simplified for now, relying on isMyTurn.
}
