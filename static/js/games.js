/**
 * File: games.js
 * Purpose: Game logic for Senior Game Lobby
 * Author: Rai (Team Lead)
 * Date: January 2026
 * Description: Handles game selection, launching game modals, and simple game implementations (Tic-Tac-Toe)
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Games module loaded');

    // DOM Elements
    const playButtons = document.querySelectorAll('.btn-play');
    const learnButtons = document.querySelectorAll('.btn-learn');
    const continueButton = document.querySelector('.btn-continue');
    
    // Initialize Modal (if not already present in HTML, we'll create it dynamically)
    let gameModal = document.getElementById('gameModal');
    if (!gameModal) {
        createGameModal();
        gameModal = document.getElementById('gameModal');
    }
    const modalInstance = new bootstrap.Modal(gameModal);

    // Event Listeners
    playButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const gameCard = this.closest('.game-card');
            const gameName = gameCard.querySelector('h3').textContent.trim();
            launchGame(gameName);
        });
    });

    learnButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const gameName = this.closest('.game-card').querySelector('h3').textContent.trim();
            showRules(gameName);
        });
    });

    if (continueButton) {
        continueButton.addEventListener('click', function() {
            launchGame('Congkak'); // Default to Congkak for demo
        });
    }

    /**
     * Create the generic game modal container
     */
    function createGameModal() {
        const modalHtml = `
            <div class="modal fade" id="gameModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-lg modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header bg-primary text-white">
                            <h5 class="modal-title" id="gameModalLabel">Game Title</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body p-4 text-center" id="gameModalBody">
                            <!-- Game Content Goes Here -->
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-primary" id="modalActionBtn" style="display:none;">Action</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    /**
     * Launch a specific game
     * @param {string} gameName 
     */
    function launchGame(gameName) {
        const modalTitle = document.getElementById('gameModalLabel');
        const modalBody = document.getElementById('gameModalBody');
        const actionBtn = document.getElementById('modalActionBtn');

        modalTitle.textContent = gameName;
        actionBtn.style.display = 'none';

        if (gameName === 'Tic-Tac-Toe') {
            initTicTacToe(modalBody);
        } else if (gameName === 'Memory Match') {
            initMemoryMatch(modalBody);
        } else {
            // Default placeholder for other games
            modalBody.innerHTML = `
                <div class="py-5">
                    <i class="fas fa-gamepad fa-4x text-muted mb-3"></i>
                    <h3>${gameName}</h3>
                    <p class="lead">This game is currently being developed.</p>
                    <p class="text-muted">Check back soon for the full version!</p>
                </div>
            `;
        }

        modalInstance.show();
    }

    /**
     * Show rules for a game
     * @param {string} gameName 
     */
    function showRules(gameName) {
        const modalTitle = document.getElementById('gameModalLabel');
        const modalBody = document.getElementById('gameModalBody');
        const actionBtn = document.getElementById('modalActionBtn');

        modalTitle.textContent = `How to Play: ${gameName}`;
        actionBtn.style.display = 'none';
        
        let rules = '';
        switch(gameName) {
            case 'Tic-Tac-Toe':
                rules = `
                    <ul class="text-start fs-5">
                        <li class="mb-2">The game is played on a grid that's 3 squares by 3 squares.</li>
                        <li class="mb-2">You are <strong>X</strong>, your friend (or computer) is <strong>O</strong>.</li>
                        <li class="mb-2">The first player to get 3 of her marks in a row (up, down, across, or diagonally) is the winner.</li>
                        <li class="mb-2">When all 9 squares are full, the game is over. If no player has 3 marks in a row, the game ends in a tie.</li>
                    </ul>
                `;
                break;
            case 'Memory Match':
                rules = `
                    <ul class="text-start fs-5">
                        <li class="mb-2">Turn over any two cards.</li>
                        <li class="mb-2">If the two cards match, keep them.</li>
                        <li class="mb-2">If they don't match, turn them back over.</li>
                        <li class="mb-2">Remember what was on each card and where it was.</li>
                        <li class="mb-2">The game is over when all the cards have been matched.</li>
                    </ul>
                `;
                break;
            default:
                rules = `<p class="fs-5">Standard rules for ${gameName} apply. Try to score points and have fun!</p>`;
        }

        modalBody.innerHTML = `
            <div class="p-3">
                <i class="fas fa-book-open fa-3x text-info mb-3"></i>
                ${rules}
            </div>
        `;
        modalInstance.show();
    }

    // ==================== TIC-TAC-TOE IMPLEMENTATION ====================
    let tttBoard = ['', '', '', '', '', '', '', '', ''];
    let tttCurrentPlayer = 'X';
    let tttGameActive = true;

    function initTicTacToe(container) {
        tttBoard = ['', '', '', '', '', '', '', '', ''];
        tttCurrentPlayer = 'X';
        tttGameActive = true;

        const boardHtml = `
            <style>
                .ttt-grid {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 10px;
                    max-width: 300px;
                    margin: 0 auto;
                }
                .ttt-cell {
                    background: #f8f9fa;
                    height: 100px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 3rem;
                    font-weight: bold;
                    cursor: pointer;
                    border: 2px solid #dee2e6;
                    border-radius: 10px;
                    transition: all 0.2s;
                }
                .ttt-cell:hover {
                    background: #e9ecef;
                }
                .ttt-cell.x { color: #e67e22; }
                .ttt-cell.o { color: #2ecc71; }
            </style>
            <div class="mb-3">
                <h4 id="tttStatus">Player X's Turn</h4>
            </div>
            <div class="ttt-grid" id="tttGrid">
                ${Array(9).fill('').map((_, i) => `<div class="ttt-cell" data-index="${i}"></div>`).join('')}
            </div>
            <div class="mt-4">
                <button class="btn btn-outline-primary" id="tttReset">Restart Game</button>
            </div>
        `;
        container.innerHTML = boardHtml;

        // Add event listeners
        document.querySelectorAll('.ttt-cell').forEach(cell => {
            cell.addEventListener('click', handleCellClick);
        });
        document.getElementById('tttReset').addEventListener('click', () => initTicTacToe(container));
    }

    function handleCellClick(e) {
        const clickedCell = e.target;
        const clickedCellIndex = parseInt(clickedCell.getAttribute('data-index'));

        if (tttBoard[clickedCellIndex] !== '' || !tttGameActive) {
            return;
        }

        handleCellPlayed(clickedCell, clickedCellIndex);
        handleResultValidation();
    }

    function handleCellPlayed(clickedCell, clickedCellIndex) {
        tttBoard[clickedCellIndex] = tttCurrentPlayer;
        clickedCell.textContent = tttCurrentPlayer;
        clickedCell.classList.add(tttCurrentPlayer.toLowerCase());
    }

    function handleResultValidation() {
        const winningConditions = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            [0, 3, 6], [1, 4, 7], [2, 5, 8],
            [0, 4, 8], [2, 4, 6]
        ];

        let roundWon = false;
        for (let i = 0; i < 8; i++) {
            const winCondition = winningConditions[i];
            let a = tttBoard[winCondition[0]];
            let b = tttBoard[winCondition[1]];
            let c = tttBoard[winCondition[2]];

            if (a === '' || b === '' || c === '') {
                continue;
            }
            if (a === b && b === c) {
                roundWon = true;
                break;
            }
        }

        const statusDisplay = document.getElementById('tttStatus');

        if (roundWon) {
            statusDisplay.textContent = `Player ${tttCurrentPlayer} Wins! 🎉`;
            statusDisplay.classList.add('text-success');
            tttGameActive = false;
            return;
        }

        let roundDraw = !tttBoard.includes("");
        if (roundDraw) {
            statusDisplay.textContent = 'Game Draw! 🤝';
            statusDisplay.classList.add('text-warning');
            tttGameActive = false;
            return;
        }

        tttCurrentPlayer = tttCurrentPlayer === "X" ? "O" : "X";
        statusDisplay.textContent = `Player ${tttCurrentPlayer}'s Turn`;
    }

    // ==================== MEMORY MATCH IMPLEMENTATION ====================
    let mmCards = [];
    let mmHasFlippedCard = false;
    let mmLockBoard = false;
    let mmFirstCard, mmSecondCard;
    let mmMatchesFound = 0;

    function initMemoryMatch(container) {
        mmMatchesFound = 0;
        mmHasFlippedCard = false;
        mmLockBoard = false;
        mmFirstCard = null;
        mmSecondCard = null;

        const icons = ['fa-cat', 'fa-dog', 'fa-fish', 'fa-dove', 'fa-dragon', 'fa-horse'];
        // Create pairs and shuffle
        mmCards = [...icons, ...icons].sort(() => 0.5 - Math.random());

        const boardHtml = `
            <style>
                .mm-grid {
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 10px;
                    max-width: 400px;
                    margin: 0 auto;
                    perspective: 1000px;
                }
                .mm-card {
                    height: 80px;
                    position: relative;
                    transform-style: preserve-3d;
                    transform: scale(1);
                    transition: transform 0.5s;
                    cursor: pointer;
                }
                .mm-card:active {
                    transform: scale(0.97);
                    transition: transform 0.2s;
                }
                .mm-card.flip {
                    transform: rotateY(180deg);
                }
                .mm-front, .mm-back {
                    width: 100%;
                    height: 100%;
                    padding: 20px;
                    position: absolute;
                    border-radius: 5px;
                    background: #9B59B6;
                    backface-visibility: hidden;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }
                .mm-front {
                    transform: rotateY(180deg);
                    background: white;
                    border: 2px solid #9B59B6;
                }
                .mm-icon {
                    font-size: 2rem;
                    color: #9B59B6;
                }
                .mm-back {
                    color: white;
                }
            </style>
            <div class="mb-3">
                <h4 id="mmStatus">Find the matching pairs!</h4>
            </div>
            <div class="mm-grid">
                ${mmCards.map((icon, i) => `
                    <div class="mm-card" data-framework="${icon}">
                        <div class="mm-front">
                            <i class="fas ${icon} mm-icon"></i>
                        </div>
                        <div class="mm-back">
                            <i class="fas fa-question fa-2x"></i>
                        </div>
                    </div>
                `).join('')}
            </div>
             <div class="mt-4">
                <button class="btn btn-outline-primary" id="mmReset">Restart Game</button>
            </div>
        `;
        container.innerHTML = boardHtml;

        document.querySelectorAll('.mm-card').forEach(card => card.addEventListener('click', flipCard));
        document.getElementById('mmReset').addEventListener('click', () => initMemoryMatch(container));
    }

    function flipCard() {
        if (mmLockBoard) return;
        if (this === mmFirstCard) return;

        this.classList.add('flip');

        if (!mmHasFlippedCard) {
            mmHasFlippedCard = true;
            mmFirstCard = this;
            return;
        }

        mmSecondCard = this;
        checkForMatch();
    }

    function checkForMatch() {
        let isMatch = mmFirstCard.dataset.framework === mmSecondCard.dataset.framework;

        isMatch ? disableCards() : unflipCards();
    }

    function disableCards() {
        mmFirstCard.removeEventListener('click', flipCard);
        mmSecondCard.removeEventListener('click', flipCard);

        mmMatchesFound++;
        if (mmMatchesFound === mmCards.length / 2) {
            document.getElementById('mmStatus').textContent = 'You found them all! 🎉';
            document.getElementById('mmStatus').classList.add('text-success');
        }

        resetBoard();
    }

    function unflipCards() {
        mmLockBoard = true;

        setTimeout(() => {
            mmFirstCard.classList.remove('flip');
            mmSecondCard.classList.remove('flip');

            resetBoard();
        }, 1000);
    }

    function resetBoard() {
        [mmHasFlippedCard, mmLockBoard] = [false, false];
        [mmFirstCard, mmSecondCard] = [null, null];
    }

});
