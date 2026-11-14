# Логіка гри Механічної Маркізи: Світанок, День (бій / рух / набір), Вечір.
# Див. docs/game-rules.md.
from __future__ import annotations

from rootbot.game.actions import Score
from rootbot.game.state import BOT, GameState


def birdsong(state: GameState, *, points_per_clearing: int, min_warriors: int) -> Score:
    """Світанок: `points_per_clearing` ПО за кожну галявину, якою бот панує і де в нього не менше
    `min_warriors` воїнів. Числа беруться з `game.birdsong` у config/default.yaml.

    Завжди повертає один `Score` (можливо, з 0 ПО); у `reason` галявини в порядку пріоритету.
    """
    scoring = [
        c.id
        for c in state.board.by_priority()
        if state.ruling_faction(c.id) == BOT and state.counts(c.id, BOT).warriors >= min_warriors
    ]
    clearings = ", ".join(str(c) for c in scoring) or "none"
    return Score(points_per_clearing * len(scoring), f"birdsong: scoring clearings {clearings}")
