"""
services/elo.py — ELO rating calculation and game-over handling.

Extracted from app.py so that socket_handlers.py and any future
service layer can import these without touching the app module.
"""
from extensions import db


def calculate_elo(winner_id, p1_id, p2_id, is_draw=False):
    """
    Calculate new ELO ratings for players.
    K-factor is fixed at 32 for simplicity.
    """
    from models import User

    p1 = User.query.get(p1_id)
    p2 = User.query.get(p2_id)

    if not p1 or not p2:
        return

    k = 32

    # Expected scores
    expected_p1 = 1 / (1 + 10 ** ((p2.elo - p1.elo) / 400))
    expected_p2 = 1 / (1 + 10 ** ((p1.elo - p2.elo) / 400))

    # Actual scores
    if is_draw:
        actual_p1 = 0.5
        actual_p2 = 0.5
    else:
        actual_p1 = 1 if winner_id == p1_id else 0
        actual_p2 = 1 if winner_id == p2_id else 0

    p1_old_elo = p1.elo
    p2_old_elo = p2.elo

    # New ratings
    p1.elo = round(p1.elo + k * (actual_p1 - expected_p1))
    p2.elo = round(p2.elo + k * (actual_p2 - expected_p2))

    db.session.commit()
    return p1_old_elo, p1.elo, p2_old_elo, p2.elo


def handle_game_over(session_id, winner_id=None, winner_color=None, is_draw=False):
    from models import GameSession, GameHistory, Streak

    gs = GameSession.query.get(session_id)
    if not gs or gs.status == 'completed':
        return None

    if not winner_id and winner_color:
        if winner_color in ['w', 'red', 'X']:
            winner_id = gs.player1_id
        else:
            winner_id = gs.player2_id

    gs.status = 'completed'
    gs.winner_id = winner_id

    # Calculate Elo
    p1_old, p1_new, p2_old, p2_new = calculate_elo(
        winner_id, gs.player1_id, gs.player2_id, is_draw
    )

    # Record history
    history = GameHistory(
        game_id=gs.game_id,
        player1_id=gs.player1_id,
        player2_id=gs.player2_id,
        winner_id=winner_id,
        player1_elo_before=p1_old,
        player1_elo_after=p1_new,
        player2_elo_before=p2_old,
        player2_elo_after=p2_new,
    )
    db.session.add(history)

    # Update streaks and stats
    for pid in [gs.player1_id, gs.player2_id]:
        streak = Streak.query.filter_by(user_id=pid).first()
        if not streak:
            streak = Streak(user_id=pid)
            db.session.add(streak)

        streak.games_played += 1
        if pid == winner_id:
            streak.games_won += 1
            streak.points += 50
        elif is_draw:
            streak.points += 20
        else:
            streak.points += 5

    db.session.commit()

    return {
        'winner_id': winner_id,
        'is_draw': is_draw,
        'p1': {'id': gs.player1_id, 'old_elo': p1_old, 'new_elo': p1_new},
        'p2': {'id': gs.player2_id, 'old_elo': p2_old, 'new_elo': p2_new},
    }
