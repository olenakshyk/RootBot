# Логіка гри Механічної Маркізи: Світанок, День (бій / рух / набір), Вечір.
# Див. docs/game-rules.md.
from __future__ import annotations

from rootbot.common.types import ClearingId, Faction, OrderCard, Suit
from rootbot.game.actions import Battle, BattleResult, Score
from rootbot.game.board import Board
from rootbot.game.state import BOT, GameState

DIE_FACES = range(4)  # 12-гранний кубик бою має значення 0..3


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


def battles(state: GameState, card: OrderCard) -> list[Battle]:
    """День, крок 1: бій на кожній галявині масті карти, де є воїни бота й ворожі фігурки.

    Захисника обирає `GameState.defender`. Бої на різних галявинах не впливають один на одний,
    тому видаються всі разом, у порядку пріоритету галявин.
    """
    result = []
    for clearing in order_clearings(state.board, card):
        defender = state.defender(clearing)
        if state.counts(clearing, BOT).warriors > 0 and defender is not None:
            result.append(Battle(clearing, defender))
    return result


def resolve_battle(
    state: GameState,
    battle: Battle,
    rolls: tuple[int, int],
    *,
    vagabond_swords: int | None = None,
) -> BattleResult:
    """Наслідки бою бота за кидком двох кубиків. Бот завжди атакує.

    - Атакувальник отримує більше значення, захисник менше. Альянс як захисник
      навпаки отримує більше.
    - Влучань від кубика не більше, ніж воїнів сторони на галявині. У Бродяги замість воїнів
      рахуються непошкоджені мечі `vagabond_swords`: їх обов'язково передати, якщо захищається він.
    - Захисник без воїнів (Бродяга без мечів) беззахисний і отримує +1 влучання.
    - Бот знімає спершу воїнів, а Keep лише тоді, коли воїнів на галявині вже немає.
    - Влучань по захиснику не більше, ніж у нього фігурок на галявині (зайві пропадають).
      Бродягу не обрізаємо: влучання по ньому йдуть у предмети, яких камера не бачить.
    """
    if len(rolls) != 2 or any(r not in DIE_FACES for r in rolls):
        raise ValueError(f"rolls must be two values in 0..{DIE_FACES[-1]}, got {rolls}")
    enemy = state.counts(battle.clearing, battle.defender)
    if battle.defender is Faction.VAGABOND:
        if vagabond_swords is None or vagabond_swords < 0:
            raise ValueError("vagabond_swords must be given and non-negative for a Vagabond battle")
        defender_max = vagabond_swords
    else:
        defender_max = enemy.warriors

    high, low = max(rolls), min(rolls)
    bot_roll, defender_roll = (low, high) if battle.defender is Faction.ALLIANCE else (high, low)
    bot_warriors = state.counts(battle.clearing, BOT).warriors

    defender_hits = min(bot_roll, bot_warriors) + (1 if defender_max == 0 else 0)
    if battle.defender is not Faction.VAGABOND:
        defender_hits = min(defender_hits, enemy.warriors + enemy.buildings + enemy.tokens)
    bot_hits = min(defender_roll, defender_max)
    return BattleResult(
        bot_warriors_lost=min(bot_hits, bot_warriors),
        keep_lost=bot_hits > bot_warriors and state.keep_clearing == battle.clearing,
        defender_hits=defender_hits,
    )


def order_clearings(board: Board, card: OrderCard) -> list[ClearingId]:
    """Галявини масті карти наказу в порядку пріоритету. Птах діє як будь-яка масть: усі."""
    return [c.id for c in board.by_priority() if card.suit in (Suit.BIRD, c.suit)]
