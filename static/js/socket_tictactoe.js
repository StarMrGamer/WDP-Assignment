/**
 * Tic Tac Toe Multiplayer Socket Handler
 */

let board;
let currentPlayer;
let gameOver;
let mySymbol;
let gameActive = false;

var socket = io();

console.log("TicTacToe script starting... Session ID:", gameSessionId);

// Join the specific game room on load
socket.emit('join', { game_id: gameSessionId });

// Also join on reconnect
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
    console.log("Initial game status:", data.status);
    if (data.status === 'active') {
        startGame();
    }
});

// Update UI when buddy is ready
socket.on('player_ready', function(data) {
    if (data.user_id != currentUserId) {
        console.log("Buddy is ready!");
        document.getElementById('winner').innerText = 'Buddy is ready! Waiting for you...';
    }
});

function startGame() {
    console.log("Starting game UI...");
    gameActive = true;
    const overlay = document.getElementById('waitingOverlay');
    const boardEl = document.getElementById('board');
    const readyBtn = document.getElementById('readyBtn');

    if (overlay) overlay.classList.add('d-none');
    if (boardEl) boardEl.classList.remove('opacity-50');
    if (readyBtn) readyBtn.classList.add('d-none');
    
    setGame();
    
    // Set player symbols based on player color
    mySymbol = (playerColor === 'X') ? 'X' : 'O';
    document.getElementById('winner').innerText = "X's Turn";
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

function setGame() {
    board = [
        [' ', ' ', ' '],
        [' ', ' ', ' '],
        [' ', ' ', ' ']
    ];

    currentPlayer = 'X';
    gameOver = false;

    // Clear existing board
    document.getElementById("board").innerHTML = "";

    for (let r = 0; r < 3; r++) {
        for (let c = 0; c < 3; c++) {
            let tile = document.createElement("div");
            tile.id = r.toString() + "-" + c.toString();
            tile.classList.add("tile");
            tile.addEventListener("click", setPiece);
            document.getElementById("board").appendChild(tile);
        }
    }
}

function setPiece() {
    if (gameOver || !gameActive) {
        return;
    }

    // Check if it's player's turn
    if (currentPlayer !== mySymbol) {
        return;
    }

    let coords = this.id.split("-");
    let r = parseInt(coords[0]);
    let c = parseInt(coords[1]);

    if (board[r][c] != ' ') {
        return;
    }
    
    board[r][c] = currentPlayer;
    this.innerText = currentPlayer;
    this.classList.add(currentPlayer.toLowerCase());

    // Send move to server
    socket.emit('move', {
        game_id: gameSessionId,
        row: r,
        col: c,
        symbol: currentPlayer,
        board: boardToString()
    });

    checkWinner();
    
    if (!gameOver) {
        currentPlayer = currentPlayer == 'X' ? 'O' : 'X';
        updateStatus();
    }
}

// Receive move from server
socket.on('move', function(data) {
    board[data.row][data.col] = data.symbol;
    let tile = document.getElementById(data.row + "-" + data.col);
    tile.innerText = data.symbol;
    tile.classList.add(data.symbol.toLowerCase());
    
    currentPlayer = data.symbol == 'X' ? 'O' : 'X';
    checkWinner();
    updateStatus();
});

function checkWinner() {
    // Check rows
    for (let r = 0; r < 3; r++) {
        if (board[r][0] == board[r][1] && board[r][1] == board[r][2] && board[r][0] != ' ') {
            for (let i = 0; i < 3; i++) {
                let tile = document.getElementById(r + "-" + i);
                tile.classList.add("winner");
            }
            gameOver = true;
            document.getElementById("winner").innerText = board[r][0] + " Wins!";
            if (currentPlayer === mySymbol) {
                socket.emit('game_over', { session_id: gameSessionId, winner_color: board[r][0] });
            }
            return;
        }
    }

    // Check columns
    for (let c = 0; c < 3; c++) {
        if (board[0][c] == board[1][c] && board[1][c] == board[2][c] && board[0][c] != ' ') {
            for (let i = 0; i < 3; i++) {
                let tile = document.getElementById(i + "-" + c);
                tile.classList.add("winner");
            }
            gameOver = true;
            document.getElementById("winner").innerText = board[0][c] + " Wins!";
            if (currentPlayer === mySymbol) {
                socket.emit('game_over', { session_id: gameSessionId, winner_color: board[0][c] });
            }
            return;
        }
    }

    // Check diagonals
    if (board[0][0] == board[1][1] && board[1][1] == board[2][2] && board[0][0] != ' ') {
        for (let i = 0; i < 3; i++) {
            let tile = document.getElementById(i + "-" + i);
            tile.classList.add("winner");
        }
        gameOver = true;
        document.getElementById("winner").innerText = board[0][0] + " Wins!";
        if (currentPlayer === mySymbol) {
            socket.emit('game_over', { session_id: gameSessionId, winner_color: board[0][0] });
        }
        return;
    }

    if (board[0][2] == board[1][1] && board[1][1] == board[2][0] && board[0][2] != ' ') {
        let tile = document.getElementById("0-2");
        tile.classList.add("winner");
        tile = document.getElementById("1-1");
        tile.classList.add("winner");
        tile = document.getElementById("2-0");
        tile.classList.add("winner");
        gameOver = true;
        document.getElementById("winner").innerText = board[0][2] + " Wins!";
        if (currentPlayer === mySymbol) {
            socket.emit('game_over', { session_id: gameSessionId, winner_color: board[0][2] });
        }
        return;
    }

    // Check for tie
    let tie = true;
    for (let r = 0; r < 3; r++) {
        for (let c = 0; c < 3; c++) {
            if (board[r][c] == ' ') {
                tie = false;
                break;
            }
        }
        if (!tie) break;
    }

    if (tie) {
        gameOver = true;
        document.getElementById("winner").innerText = "It's a Tie!";
        socket.emit('game_over', { session_id: gameSessionId, is_draw: true });
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

function updateStatus() {
    if (!gameOver && gameActive) {
        if (currentPlayer === mySymbol) {
            document.getElementById("winner").innerText = "Your Turn (" + mySymbol + ")";
        } else {
            document.getElementById("winner").innerText = "Opponent's Turn (" + currentPlayer + ")";
        }
    }
}

function boardToString() {
    let result = '';
    for (let r = 0; r < 3; r++) {
        for (let c = 0; c < 3; c++) {
            result += board[r][c];
        }
    }
    return result;
}

// Initial button setup
initButtons();