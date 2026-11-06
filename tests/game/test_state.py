from pathlib import Path

import pytest

from rootbot.common.types import ClearingId, Faction, PieceCounts
from rootbot.game.board import load_board
from rootbot.game.state import BOT, GameState, GameStateError

AUTUMN = Path(__file__).resolve().parents[2] / "config" / "maps" / "autumn.yaml"
EYRIE, ALLIANCE, VAGABOND = Faction.EYRIE, Faction.ALLIANCE, Faction.VAGABOND
C = ClearingId(5)  # будь-яка галявина, для тестів не важливо яка


@pytest.fixture(scope="module")
def board():
    return load_board(AUTUMN)


def pc(w=0, b=0, t=0, p=0):
    return PieceCounts(warriors=w, buildings=b, tokens=t, pawn=p)


def state(board, here=None, scores=None):
    """Стан з фігурками `here` на галявині C."""
    return GameState(board, pieces={C: here or {}}, scores=scores or {})


# --- панування ---


def test_empty_clearing_nobody_rules(board):
    assert state(board).ruler(C) is None


def test_clearing_without_entry_nobody_rules(board):
    assert GameState(board).ruler(ClearingId(1)) is None


def test_majority_rules(board):
    s = state(board, {BOT: pc(w=3), ALLIANCE: pc(w=2)})
    assert s.ruler(C) == BOT
    assert s.rules(C)
    assert not s.rules(C, ALLIANCE)


def test_buildings_count_for_rule(board):
    assert state(board, {BOT: pc(w=2), ALLIANCE: pc(w=1, b=2)}).ruler(C) == ALLIANCE


def test_tie_nobody_rules(board):
    s = state(board, {BOT: pc(w=2), ALLIANCE: pc(w=1, b=1)})
    assert s.ruler(C) is None
    assert not s.rules(C)


def test_tokens_do_not_count_for_rule(board):
    assert state(board, {BOT: pc(w=1), ALLIANCE: pc(t=3)}).ruler(C) == BOT


def test_vagabond_never_rules(board):
    s = state(board, {VAGABOND: pc(p=1)})
    assert s.ruler(C) is None


def test_rule_compares_each_faction_separately(board):
    # 2 проти 1 і 1: бот панує, хоча ворогів разом стільки ж
    assert state(board, {BOT: pc(w=2), EYRIE: pc(w=1), ALLIANCE: pc(b=1)}).ruler(C) == BOT


def test_eyrie_rule_ties(board):
    assert state(board, {BOT: pc(w=2), EYRIE: pc(w=1, b=1)}).ruler(C) == EYRIE


def test_eyrie_rule_three_way_tie(board):
    s = state(board, {BOT: pc(w=1), EYRIE: pc(b=1), ALLIANCE: pc(w=1)})
    assert s.ruler(C) == EYRIE


def test_eyrie_loses_without_tie(board):
    assert state(board, {BOT: pc(w=3), EYRIE: pc(w=2)}).ruler(C) == BOT


def test_eyrie_with_only_tokens_does_not_rule(board):
    assert state(board, {EYRIE: pc(t=1)}).ruler(C) is None


# --- ворожі фігурки ---


def test_enemy_pieces_counts_everything_but_bot(board):
    s = state(board, {BOT: pc(w=4), EYRIE: pc(w=1, b=1), ALLIANCE: pc(t=2), VAGABOND: pc(p=1)})
    assert s.enemy_pieces(C) == 5


def test_enemy_pieces_empty(board):
    assert state(board, {BOT: pc(w=3)}).enemy_pieces(C) == 0


def test_enemies_skip_zero_counts(board):
    s = state(board, {BOT: pc(w=1), EYRIE: pc(), VAGABOND: pc(p=1)})
    assert s.enemies(C) == [VAGABOND]


def test_counts_default_to_zero(board):
    assert state(board).counts(C, EYRIE) == pc()


# --- вибір захисника ---


def test_no_enemies_no_defender(board):
    assert state(board, {BOT: pc(w=3)}).defender(C) is None


def test_single_enemy(board):
    assert state(board, {BOT: pc(w=1), VAGABOND: pc(p=1)}).defender(C) == VAGABOND


def test_defender_most_pieces(board):
    # жетони теж фігурки: у Альянсу 3, у Династії 2
    s = state(board, {BOT: pc(w=1), EYRIE: pc(w=2), ALLIANCE: pc(w=1, t=2)})
    assert s.defender(C) == ALLIANCE


def test_defender_tie_most_points(board):
    s = state(board, {EYRIE: pc(w=2), ALLIANCE: pc(w=2)}, scores={EYRIE: 7, ALLIANCE: 12})
    assert s.defender(C) == ALLIANCE


def test_defender_tie_missing_score_is_zero(board):
    s = state(board, {EYRIE: pc(w=2), ALLIANCE: pc(w=2)}, scores={ALLIANCE: 1})
    assert s.defender(C) == ALLIANCE


def test_defender_full_tie_setup_order(board):
    here = {EYRIE: pc(w=2), ALLIANCE: pc(w=2)}
    scores = {EYRIE: 5, ALLIANCE: 5}
    assert state(board, here, scores).defender(C) == EYRIE
    assert state(board, {ALLIANCE: pc(w=2), VAGABOND: pc(p=2)}, scores).defender(C) == ALLIANCE


def test_defender_ignores_bot_score(board):
    s = state(board, {BOT: pc(w=5), EYRIE: pc(w=1)}, scores={BOT: 29})
    assert s.defender(C) == EYRIE


# --- некоректний стан ---


def test_unknown_clearing_query(board):
    with pytest.raises(GameStateError, match="unknown clearing 13"):
        state(board).ruler(ClearingId(13))


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"pieces": {ClearingId(13): {}}}, "pieces: unknown clearing 13"),
        (
            {"pieces": {C: {Faction.LIZARDS: PieceCounts(warriors=1)}}},
            "unsupported faction lizards",
        ),
        ({"pieces": {C: {EYRIE: PieceCounts(warriors=-1)}}}, r"negative eyrie \['warriors'\]"),
        ({"keep_clearing": ClearingId(0)}, "keep_clearing: unknown clearing 0"),
        ({"scores": {Faction.RIVERFOLK: 3}}, "scores: unsupported faction riverfolk"),
        ({"scores": {EYRIE: -1}}, "negative score for eyrie"),
    ],
)
def test_invalid_state(board, kwargs, message):
    with pytest.raises(GameStateError, match=message):
        GameState(board, **kwargs)


def test_reports_all_errors(board):
    with pytest.raises(GameStateError) as exc:
        GameState(board, scores={EYRIE: -1}, keep_clearing=ClearingId(0))
    assert "negative score" in str(exc.value)
    assert "keep_clearing" in str(exc.value)
