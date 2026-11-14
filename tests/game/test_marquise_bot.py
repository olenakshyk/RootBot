from pathlib import Path

import pytest

from rootbot.common.types import ClearingId, Faction, PieceCounts
from rootbot.game.actions import Score
from rootbot.game.board import load_board
from rootbot.game.marquise_bot import birdsong
from rootbot.game.state import BOT, GameState

AUTUMN = Path(__file__).resolve().parents[2] / "config" / "maps" / "autumn.yaml"
ALLIANCE, EYRIE = Faction.ALLIANCE, Faction.EYRIE
RULES = {"points_per_clearing": 2, "min_warriors": 3}  # як у config/default.yaml


@pytest.fixture(scope="module")
def board():
    return load_board(AUTUMN)


def pc(w=0, b=0, t=0, p=0):
    return PieceCounts(warriors=w, buildings=b, tokens=t, pawn=p)


def state(board, pieces):
    return GameState(board, pieces={ClearingId(c): here for c, here in pieces.items()})


# --- Світанок ---


def score(board, pieces, **rules):
    return birdsong(state(board, pieces), **(rules or RULES))


def test_birdsong_empty_board_scores_zero(board):
    assert birdsong(GameState(board), **RULES) == Score(0, "birdsong: scoring clearings none")


def test_birdsong_scores_ruled_clearing_with_three_warriors(board):
    assert score(board, {1: {BOT: pc(w=3)}}).points == 2


def test_birdsong_two_warriors_not_enough(board):
    assert score(board, {1: {BOT: pc(w=2)}}).points == 0


def test_birdsong_needs_rule_not_just_warriors(board):
    assert score(board, {1: {BOT: pc(w=3), ALLIANCE: pc(w=4)}}).points == 0


def test_birdsong_tie_is_not_rule(board):
    assert score(board, {1: {BOT: pc(w=3), ALLIANCE: pc(w=2, b=1)}}).points == 0


def test_birdsong_eyrie_wins_tie(board):
    assert score(board, {1: {BOT: pc(w=3), EYRIE: pc(w=3)}}).points == 0


def test_birdsong_enemy_tokens_do_not_break_rule(board):
    assert score(board, {1: {BOT: pc(w=3), ALLIANCE: pc(t=5)}}).points == 2


def test_birdsong_sums_clearings_in_priority_order(board):
    first, second = (c.id for c in board.by_priority()[:2])
    result = score(board, {second: {BOT: pc(w=5)}, first: {BOT: pc(w=3)}})
    assert result == Score(4, f"birdsong: scoring clearings {first}, {second}")


def test_birdsong_uses_given_rules(board):
    assert score(board, {1: {BOT: pc(w=1)}}, points_per_clearing=3, min_warriors=1).points == 3
