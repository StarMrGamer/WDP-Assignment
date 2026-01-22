
var board = null
var game = new Chess()
var $status = $('#status')
var $pgn = $('#pgn')

// Initializing socket
var socket = io();

let gameActive = false; // Will be set to true when game_start received

console.log("Chess script starting... Session ID:", gameSessionId);

// Join the specific game room
socket.emit('join', { game_id: gameSessionId });

function initButtons() {
    const readyBtn = document.getElementById('readyBtn');
    const forfeitBtn = document.getElementById('forfeitBtn');

    if (readyBtn) {
        readyBtn.onclick = function() {
            console.log("Ready button clicked");
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Waiting...';
            socket.emit('ready', { session_id: gameSessionId });
        };
    }

    if (forfeitBtn) {
        forfeitBtn.onclick = function() {
            if (confirm('Are you sure you want to forfeit? This will end the game.')) {
                socket.emit('forfeit', { session_id: gameSessionId });
                window.location.href = (window.location.pathname.includes('senior')) ? '/senior/games' : '/youth/games';
            }
        };
    }
}

// Listen for initial state
socket.on('init_game', function(data) {
    console.log("Initial game status:", data.status);
    if (data.status === 'active') {
        startGame();
    }
});

// Update UI when buddy is ready
socket.on('player_ready', function(data) {
    if (data.user_id != currentUserId) {
        console.log("Buddy is ready!");
        $status.html('Buddy is ready! Waiting for you...');
    }
});

function startGame() {
    console.log("Starting game UI...");
    gameActive = true;
    const overlay = document.getElementById('waitingOverlay');
    const boardEl = document.getElementById('myBoard');
    const readyBtn = document.getElementById('readyBtn');

    if (overlay) overlay.classList.add('d-none');
    if (boardEl) boardEl.classList.remove('opacity-50');
    if (readyBtn) readyBtn.classList.add('d-none');
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
    window.location.href = (window.location.pathname.includes('senior')) ? '/senior/games' : '/youth/games';
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
        fen: game.fen()
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

    $status.html(status)
    $pgn.html(game.pgn())
}

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
