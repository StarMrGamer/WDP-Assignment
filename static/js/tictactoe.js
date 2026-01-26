/**
 * Tic Tac Toe Game
 * Based on https://github.com/ImKennyYip/tictactoe
 */

let board;
let currentPlayer;
let gameOver;

window.onload = function() {
    setGame();
}

function setGame() {
    board = [
        [' ', ' ', ' '],
        [' ', ' ', ' '],
        [' ', ' ', ' ']
    ];

    currentPlayer = 'X';
    gameOver = false;

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
    if (gameOver) {
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

    // Add class for styling
    this.classList.add(currentPlayer.toLowerCase());

    checkWinner();
    
    if (!gameOver) {
        currentPlayer = currentPlayer == 'X' ? 'O' : 'X';
        updateStatus();
    }
}

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
    }
}

function updateStatus() {
    if (!gameOver) {
        document.getElementById("winner").innerText = currentPlayer + "'s Turn";
    }
}

function resetGame() {
    // Clear the board
    document.getElementById("board").innerHTML = "";
    document.getElementById("winner").innerText = "";
    setGame();
    updateStatus();
}

// Initialize status
updateStatus();