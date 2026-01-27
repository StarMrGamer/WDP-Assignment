/* global io, gameSessionId, userRole, currentUserId, playerColor, Chess, Chessboard, $ */

var board = null
var game = new Chess()
var $status = $('#status')
var $pgn = $('#pgn')

// Initializing socket
var socket = io();

let gameActive = false; // Will be set to true when game_start received

console.log("Chess script starting... Session ID:", gameSessionId);

// Join the specific game room on load
socket.emit('join', { game_id: gameSessionId });

// Also join on reconnect to ensure room membership is maintained
socket.on('connect', function() {
    console.log("Socket connected/reconnected. Joining room...");
    socket.emit('join', { game_id: gameSessionId });
});

function initButtons() {
    const readyBtn = document.getElementById('readyBtn');
    const forfeitBtn = document.getElementById('forfeitBtn');

    if (readyBtn) {
        readyBtn.onclick = function() {
            console.log("Ready button clicked");
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Waiting...';
            
            // Update my badge locally
            const myBadge = document.getElementById('myBadge');
            if (myBadge) {
                myBadge.innerText = 'Ready';
                myBadge.classList.remove('bg-secondary');
                myBadge.classList.add('bg-success');
            }
            
            socket.emit('ready', { session_id: gameSessionId });
        };
    }

    if (forfeitBtn) {
        forfeitBtn.onclick = function() {
            if (confirm('Are you sure you want to forfeit? This will end the game.')) {
                socket.emit('forfeit', { session_id: gameSessionId });
                window.location.href = (userRole === 'senior') ? '/senior/games' : '/youth/games';
            }
        };
    }
}

// Listen for initial state
socket.on('init_game', function(data) {
    console.log("Initial game status:", data.status, "State:", data.game_state);
    
    // Update readiness badges if game is still waiting
    if (data.status === 'waiting') {
        const isP1 = data.p1_id == currentUserId;
        const myReady = isP1 ? data.p1_ready : data.p2_ready;
        const opponentReady = isP1 ? data.p2_ready : data.p1_ready;
        
        const myBadge = document.getElementById('myBadge');
        if (myBadge && myReady) {
            myBadge.innerText = 'Ready';
            myBadge.classList.remove('bg-secondary');
            myBadge.classList.add('bg-success');
        }
        
        const opponentBadge = document.getElementById('opponentBadge');
        if (opponentBadge && opponentReady) {
            opponentBadge.innerText = 'Ready';
            opponentBadge.classList.remove('bg-secondary');
            opponentBadge.classList.add('bg-success');
            
            $status.html('Buddy is ready! Waiting for you...');
        }
    }

    if (data.status === 'active') {
        if (data.game_state && data.game_state !== 'null') {
            savedState = data.game_state;
        }
        startGame();
    }
});

// Update UI when buddy is ready
socket.on('player_ready', function(data) {
    if (data.user_id != currentUserId) {
        console.log("Buddy is ready!");
        $status.html('Buddy is ready! Waiting for you...');
        
        // Update opponent badge
        const opponentBadge = document.getElementById('opponentBadge');
        if (opponentBadge) {
            opponentBadge.innerText = 'Ready';
            opponentBadge.classList.remove('bg-secondary');
            opponentBadge.classList.add('bg-success');
        }
    }
});

let savedState = null;

function startGame() {
    console.log("Starting game UI...");
    gameActive = true;
    const overlay = document.getElementById('waitingOverlay');
    const boardEl = document.getElementById('myBoard');
    const readyBtn = document.getElementById('readyBtn');

    if (overlay) overlay.classList.add('d-none');
    if (boardEl) boardEl.classList.remove('opacity-50');
    if (readyBtn) readyBtn.classList.add('d-none');
    
    // Apply saved state if it exists
    if (savedState) {
        game.load(savedState);
        board.position(savedState);
        savedState = null;
    }
    
    updateStatus();
}

// Socket Listeners for Game State
socket.on('game_start', function(data) {
    console.log("game_start event received!");
    startGame();
});

socket.on('opponent_forfeit', function(data) {
    gameActive = false;
    alert(data.winner_name + ' has left the game. You win by forfeit!');
    window.location.href = (userRole === 'senior') ? '/senior/games' : '/youth/games';
});

function onDragStart (source, piece, position, orientation) {
    // do not pick up pieces if the game is over or not started
    if (game.game_over()) return false
    if (!gameActive) return false;

    // Only allow moving pieces of the player's color
    if ((playerColor === 'white' && piece.search(/^b/) !== -1) ||
        (playerColor === 'black' && piece.search(/^w/) !== -1)) {
        return false;
    }

    // only pick up pieces for the side to move
    if ((game.turn() === 'w' && piece.search(/^b/) !== -1) || 
        (game.turn() === 'b' && piece.search(/^w/) !== -1)) {
        return false
    }
}

function onDrop (source, target) {
    let theMove = {
        from: source,
        to: target,
        promotion: 'q' // always promote to a queen for simplicity
    };
    
    // see if the move is legal
    var move = game.move(theMove);

    // illegal move
    if (move === null) return 'snapback'

    // PUSH MOVE TO SERVER
    socket.emit('move', {
        game_id: gameSessionId,
        move: theMove,
        game_state: game.fen() // Explicitly use game_state key for app.py
    });

    updateStatus()
}

// RECEIVE MOVE FROM SERVER
socket.on('move', function(data) {
    game.move(data.move);
    board.position(game.fen());
    updateStatus();
});

// update the board position after the piece snap
// for castling, en passant, pawn promotion
function onSnapEnd () {
    board.position(game.fen())
}

function updateStatus () {
    var status = ''

    if (!gameActive) {
        status = 'Waiting for both players to be ready...';
        $status.html(status);
        return;
    }

    var moveColor = 'White'
    if (game.turn() === 'b') {
        moveColor = 'Black'
    }

    // checkmate?
    if (game.in_checkmate()) {
        status = 'Game over, ' + moveColor + ' is in checkmate.'
    }

    // draw?
    else if (game.in_draw()) {
        status = 'Game over, drawn position'
    }

    // game still on
    else {
        status = moveColor + ' to move'

        // check?
        if (game.in_check()) {
            status += ', ' + moveColor + ' is in check'
        }
    }

    // Toggle theme based on turn
    if (game.turn() === 'w') {
        $('body').addClass('theme-white-move').removeClass('theme-black-move');
    } else {
        $('body').addClass('theme-black-move').removeClass('theme-white-move');
    }

    $status.html(status)
    $pgn.html(game.pgn())
    $pgn.scrollTop($pgn[0].scrollHeight);

    // Handle game over detection
    if (game.game_over()) {
        let winnerId = null;
        let isDraw = false;

        if (game.in_checkmate()) {
            // If it's black's turn to move and it's checkmate, white won
            if (game.turn() === 'b') {
                // White won. Find which player ID is white.
                winnerId = (playerColor === 'white') ? currentUserId : null; 
                // Wait, we need the other player ID if we are black.
                // It's better to let the server know who we think won, 
                // but the server should ideally know who is who.
                // In GameSession, player1 is always challenger (usually white in this setup).
                // Let's pass 'w' or 'b' as winner to the server or let server figure it out.
                socket.emit('game_over', {
                    session_id: gameSessionId,
                    winner_color: 'w'
                });
            } else {
                socket.emit('game_over', {
                    session_id: gameSessionId,
                    winner_color: 'b'
                });
            }
        } else if (game.in_draw()) {
            socket.emit('game_over', {
                session_id: gameSessionId,
                is_draw: true
            });
        }
    }
}

// Stats listener
socket.on('game_over_stats', function(data) {
    gameActive = false;
    let message = "Game Over! ";
    if (data.is_draw) {
        message += "It's a draw.";
    } else {
        const iWon = data.winner_id == currentUserId;
        message += iWon ? "You won!" : "You lost.";
    }
    
    // Show Elo changes
    const myStats = data.p1.id == currentUserId ? data.p1 : data.p2;
    message += `\nYour Elo: ${myStats.old_elo} -> ${myStats.new_elo} (${myStats.new_elo - myStats.old_elo >= 0 ? '+' : ''}${myStats.new_elo - myStats.old_elo})`;
    
    alert(message);
    window.location.href = (userRole === 'senior') ? '/senior/games' : '/youth/games';
});

var config = {
    draggable: true,
    position: 'start',
    onDragStart: onDragStart,
    onDrop: onDrop,
    onSnapEnd: onSnapEnd,
    pieceTheme: '/static/images/chesspieces/wikipedia/{piece}.png'
}
board = Chessboard('myBoard', config)

// Set board orientation
if (playerColor === 'black') {
    board.orientation('black');
}

// Initial button setup
initButtons();
updateStatus()
