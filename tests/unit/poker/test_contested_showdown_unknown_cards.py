"""Unit and regression tests for contested showdown settlement with unknown hole cards,
muck/forfeit handling, pending settlement enforcement, decision grading labels, and event integrity.
"""

import pytest

from app.domain.live_helper.engine import LiveHelperEngine
from app.domain.live_helper.models import (
    FormatType,
    LiveHelperGameConfig,
    SpecificGameFormat,
    StrategicMatchLevel,
)
from app.domain.live_helper.session_engine import LiveHelperSessionEngine
from app.domain.live_helper.settlement import HandSettlementEngine, HandSettlementResult


def test_contested_showdown_with_unknown_cards_suspends_settlement():
    """Contested showdown with unknown hole cards must suspend settlement and prompt for card reveals."""
    seats = [
        {
            "seat_number": 1,
            "player_name": "Hero",
            "stack": 1000,
            "starting_stack": 1000,
            "is_hero": True,
            "hole_cards": ["Ah", "Kh"],
        },
        {
            "seat_number": 2,
            "player_name": "Villain",
            "stack": 1000,
            "starting_stack": 1000,
            "is_hero": False,
            "hole_cards": [],
        },
    ]
    board = ["Ks", "7d", "2c", "8h", "2s"]
    actions = [
        {"seat_number": 1, "action_type": "post_sb", "amount": 50, "street": "preflop"},
        {"seat_number": 2, "action_type": "post_bb", "amount": 100, "street": "preflop"},
        {"seat_number": 1, "action_type": "call", "amount": 100, "street": "preflop"},
        {"seat_number": 2, "action_type": "check", "amount": 0, "street": "preflop"},
        {"seat_number": 2, "action_type": "check", "amount": 0, "street": "flop"},
        {"seat_number": 1, "action_type": "check", "amount": 0, "street": "flop"},
        {"seat_number": 2, "action_type": "check", "amount": 0, "street": "turn"},
        {"seat_number": 1, "action_type": "check", "amount": 0, "street": "turn"},
        {"seat_number": 2, "action_type": "check", "amount": 0, "street": "river"},
        {"seat_number": 1, "action_type": "check", "amount": 0, "street": "river"},
    ]

    result: HandSettlementResult = HandSettlementEngine.settle_hand(
        button_seat=1,
        table_capacity=6,
        seats=seats,
        board_cards=board,
        actions=actions,
        pots_payload={"total_pot": 200, "main_pot": 200, "side_pots": []},
        is_cash=True,
    )

    assert result.is_settled is False
    assert result.requires_card_reveal is True
    assert result.missing_card_seats == [2]
    assert result.winning_seats == []
    assert result.pots_settled == []
    assert "Settlement Pending" in result.settlement_summary
    assert "Seat(s) 2" in result.settlement_summary


def test_contested_showdown_blocks_advancing_to_next_hand():
    """LiveHelperSessionEngine.advance_to_next_hand must strictly raise ValueError if settlement is pending."""
    session = {
        "id": "sess-test-1",
        "format_type": "CASH",
        "default_mode": "DECISION_CHECK",
        "table_capacity": 6,
        "configuration": {"big_blind": 100, "small_blind": 50},
        "participants": [
            {
                "seat_number": 1,
                "player_name": "Hero",
                "current_stack": 1000,
                "is_hero": True,
                "is_active": True,
                "is_sitting_out": False,
            },
            {
                "seat_number": 2,
                "player_name": "Villain",
                "current_stack": 1000,
                "is_hero": False,
                "is_active": True,
                "is_sitting_out": False,
            },
        ],
        "total_hands_completed": 0,
    }

    hand = {
        "id": "hand-test-1",
        "session_id": "sess-test-1",
        "hand_index": 1,
        "button_seat": 1,
        "small_blind": 50,
        "big_blind": 100,
        "ante": 0,
        "starting_stacks": {"1": 1000, "2": 1000},
        "ending_stacks": None,
        "hole_cards": {"1": ["Ah", "Kh"], "2": []},
        "board": ["Ks", "7d", "2c", "8h", "2s"],
        "street": "showdown",
        "actions": [
            {"seat_number": 1, "action_type": "post_sb", "amount": 50, "street": "preflop"},
            {"seat_number": 2, "action_type": "post_bb", "amount": 100, "street": "preflop"},
            {"seat_number": 1, "action_type": "call", "amount": 100, "street": "preflop"},
            {"seat_number": 2, "action_type": "check", "amount": 0, "street": "preflop"},
        ],
        "pots": {"total_pot": 200, "main_pot": 200, "side_pots": []},
        "is_settled": False,
        "settlement": None,
    }

    with pytest.raises(ValueError, match="Settlement Pending|Showdown settlement is unresolved"):
        LiveHelperSessionEngine.advance_to_next_hand(session=session, previous_hand=hand)


def test_revealing_opponent_cards_settles_and_unblocks_next_hand():
    """Revealing opponent hole cards must resolve showdown, determine true winner, update stacks, and allow advance."""
    session = {
        "id": "sess-test-2",
        "format_type": "CASH",
        "default_mode": "DECISION_CHECK",
        "table_capacity": 6,
        "configuration": {
            "big_blind": 100,
            "small_blind": 50,
            "cash_rules": {"rake_percent": 0.0, "rake_cap": 0},
        },
        "participants": [
            {
                "seat_number": 1,
                "player_name": "Hero",
                "current_stack": 1000,
                "starting_stack": 1000,
                "is_hero": True,
                "is_active": True,
                "is_sitting_out": False,
            },
            {
                "seat_number": 2,
                "player_name": "Villain",
                "current_stack": 1000,
                "starting_stack": 1000,
                "is_hero": False,
                "is_active": True,
                "is_sitting_out": False,
            },
        ],
        "total_hands_completed": 0,
    }

    hand = {
        "id": "hand-test-2",
        "session_id": "sess-test-2",
        "hand_index": 1,
        "button_seat": 1,
        "small_blind": 50,
        "big_blind": 100,
        "ante": 0,
        "starting_stacks": {"1": 1000, "2": 1000},
        "ending_stacks": None,
        "hole_cards": {"1": ["Ah", "Kh"], "2": []},
        "board": ["Ks", "7d", "2c", "8h", "2s"],
        "street": "showdown",
        "actions": [
            {"seat_number": 1, "action_type": "post_sb", "amount": 50, "street": "preflop"},
            {"seat_number": 2, "action_type": "post_bb", "amount": 100, "street": "preflop"},
            {"seat_number": 1, "action_type": "call", "amount": 100, "street": "preflop"},
            {"seat_number": 2, "action_type": "check", "amount": 0, "street": "preflop"},
            {"seat_number": 2, "action_type": "check", "amount": 0, "street": "flop"},
            {"seat_number": 1, "action_type": "check", "amount": 0, "street": "flop"},
            {"seat_number": 2, "action_type": "check", "amount": 0, "street": "turn"},
            {"seat_number": 1, "action_type": "check", "amount": 0, "street": "turn"},
            {"seat_number": 2, "action_type": "check", "amount": 0, "street": "river"},
            {"seat_number": 1, "action_type": "check", "amount": 0, "street": "river"},
        ],
        "pots": {"total_pot": 200, "main_pot": 200, "side_pots": []},
        "is_settled": False,
        "settlement": None,
    }

    # Step 1: Reveal villain cards as Qd Jd (K-high pair on Ks 7d 2c 8h 2s vs Hero's Kings & Twos with Ace kicker)
    upd_session, upd_hand = LiveHelperSessionEngine.reveal_opponent_cards(
        session=session,
        hand=hand,
        seat_number=2,
        hole_cards=["Qd", "Jd"],
    )

    assert upd_hand["is_settled"] is True
    assert upd_hand["settlement"]["requires_card_reveal"] is False
    assert upd_hand["settlement"]["winning_seats"] == [1]
    # Hero wins 200 pot: investment was 100, so net is +100 -> stack becomes 1100
    assert upd_hand["ending_stacks"]["1"] == 1100
    assert upd_hand["ending_stacks"]["2"] == 900
    assert upd_session["participants"][0]["current_stack"] == 1100
    assert upd_session["participants"][1]["current_stack"] == 900

    # Step 2: Now advance_to_next_hand must succeed and carry stacks forward
    next_session, next_hand = LiveHelperSessionEngine.advance_to_next_hand(
        session=upd_session,
        previous_hand=upd_hand,
    )

    assert next_hand["hand_index"] == 2
    assert next_hand["starting_stacks"]["1"] == 1100
    assert next_hand["starting_stacks"]["2"] == 900
    # Button rotated from Seat 1 to Seat 2
    assert next_hand["button_seat"] == 2


def test_muck_forfeit_at_showdown_awards_pot_uncontested():
    """If an opponent mucks at showdown, pot is awarded uncontested to remaining contender."""
    seats = [
        {
            "seat_number": 1,
            "player_name": "Hero",
            "stack": 1000,
            "starting_stack": 1000,
            "is_hero": True,
            "hole_cards": ["Ah", "Kh"],
        },
        {
            "seat_number": 2,
            "player_name": "Villain",
            "stack": 1000,
            "starting_stack": 1000,
            "is_hero": False,
            "hole_cards": ["MUCK"],
        },
    ]
    board = ["Ks", "7d", "2c", "8h", "2s"]
    actions = [
        {"seat_number": 1, "action_type": "post_sb", "amount": 50, "street": "preflop"},
        {"seat_number": 2, "action_type": "post_bb", "amount": 100, "street": "preflop"},
        {"seat_number": 1, "action_type": "call", "amount": 100, "street": "preflop"},
        {"seat_number": 2, "action_type": "check", "amount": 0, "street": "preflop"},
    ]

    result: HandSettlementResult = HandSettlementEngine.settle_hand(
        button_seat=1,
        table_capacity=6,
        seats=seats,
        board_cards=board,
        actions=actions,
        pots_payload={"total_pot": 200, "main_pot": 200, "side_pots": []},
        is_cash=False,
    )

    assert result.is_settled is True
    assert result.requires_card_reveal is False
    assert result.winning_seats == [1]
    assert result.ending_stacks[1] == 1100
    assert result.ending_stacks[2] == 900
    assert "Seat 1" in result.settlement_summary
    assert "mucked" in result.settlement_summary.lower()


def test_uncontested_fold_win_settles_immediately_without_card_reveals():
    """Uncontested pot won by fold preflop or postflop settles cleanly without card reveals."""
    seats = [
        {
            "seat_number": 1,
            "player_name": "Hero",
            "stack": 1000,
            "starting_stack": 1000,
            "is_hero": True,
            "hole_cards": ["Ah", "Kh"],
        },
        {
            "seat_number": 2,
            "player_name": "Villain",
            "stack": 1000,
            "starting_stack": 1000,
            "is_hero": False,
            "hole_cards": [],
        },
    ]
    actions = [
        {"seat_number": 1, "action_type": "post_sb", "amount": 50, "street": "preflop"},
        {"seat_number": 2, "action_type": "post_bb", "amount": 100, "street": "preflop"},
        {"seat_number": 1, "action_type": "raise", "amount": 250, "street": "preflop"},
        {"seat_number": 2, "action_type": "fold", "amount": 0, "street": "preflop"},
    ]

    result: HandSettlementResult = HandSettlementEngine.settle_hand(
        button_seat=1,
        table_capacity=6,
        seats=seats,
        board_cards=[],
        actions=actions,
        pots_payload={"total_pot": 350, "main_pot": 350, "side_pots": []},
        is_cash=False,
    )

    assert result.is_settled is True
    assert result.requires_card_reveal is False
    assert result.winning_seats == [1]
    assert result.uncalled_returns == {1: 150}  # 250 uncalled by 100 BB -> 150 refund
    assert result.ending_stacks[1] == 1100
    assert result.ending_stacks[2] == 900


def test_educational_reference_never_returns_optimal_or_perfect():
    """Educational heuristic references must return qualified labels, never OPTIMAL or PERFECT."""
    config = LiveHelperGameConfig(
        format_type=FormatType.CASH,
        specific_format=SpecificGameFormat.ONLINE_6MAX,
        max_capacity=6,
        small_blind=50,
        big_blind=100,
    )
    table_state = {
        "street": "preflop",
        "action_history": [
            {"seat_number": 1, "action_type": "post_sb", "amount": 50},
            {"seat_number": 2, "action_type": "post_bb", "amount": 100},
        ],
        "legal_actions": [{"kind": "RAISE", "min_amount": 200, "max_amount": 1000}],
        "total_pot": 150,
        "effective_stack": 1000,
        "seats": [],
        "geometry": None,
    }

    # Evaluate BTN raise with AA on 100bb 6-max benchmark
    eval_resp = LiveHelperEngine._match_strategy_reference(
        config=config,
        street="preflop",
        hero_pos="BTN",
        hero_cards=("Ah", "As"),
        chosen_action="raise",
        table_state=table_state,
    )

    assert eval_resp.match_classification == StrategicMatchLevel.EDUCATIONAL_HEURISTIC
    # Must NOT be OPTIMAL or PERFECT
    assert eval_resp.qualitative_grade != "OPTIMAL"
    assert eval_resp.qualitative_grade != "PERFECT"
    assert eval_resp.qualitative_grade in ["REFERENCE_PREFERRED", "REFERENCE_ALIGNED"]


def test_decision_event_integrity_raise_is_never_check():
    """Verify that Hero raise is persisted as raise with exact amounts and provenance."""
    session = {
        "id": "sess-test-3",
        "format_type": "CASH",
        "default_mode": "DECISION_CHECK",
        "table_capacity": 6,
        "configuration": {"big_blind": 100, "small_blind": 50},
        "participants": [
            {
                "seat_number": 1,
                "player_name": "Hero",
                "current_stack": 1000,
                "is_hero": True,
                "is_active": True,
                "is_sitting_out": False,
            },
            {
                "seat_number": 2,
                "player_name": "Villain",
                "current_stack": 1000,
                "is_hero": False,
                "is_active": True,
                "is_sitting_out": False,
            },
        ],
        "total_hands_completed": 0,
    }

    hand = {
        "id": "hand-test-3",
        "session_id": "sess-test-3",
        "hand_index": 1,
        "button_seat": 1,
        "small_blind": 50,
        "big_blind": 100,
        "ante": 0,
        "starting_stacks": {"1": 1000, "2": 1000},
        "ending_stacks": None,
        "hole_cards": {"1": ["Ah", "Kh"], "2": []},
        "board": [],
        "street": "preflop",
        "actions": [
            {"seat_number": 1, "action_type": "post_sb", "amount": 50, "street": "preflop"},
            {"seat_number": 2, "action_type": "post_bb", "amount": 100, "street": "preflop"},
        ],
        "pots": {"total_pot": 150, "main_pot": 150, "side_pots": []},
        "is_settled": False,
        "settlement": None,
        "decisions": [],
    }

    # Hero acts: raise to 250
    upd_sess, upd_hand, decision = LiveHelperSessionEngine.record_action(
        session=session,
        hand=hand,
        seat_number=1,
        action_type="raise",
        amount=250,
        mode="DECISION_CHECK",
        reasoning="Strong BTN open with AKs",
        confidence=5,
    )

    assert decision is not None
    assert decision["chosen_action"] == "raise"
    assert decision["chosen_amount"] == 250
    assert decision["street"] == "preflop"
    assert decision["mode"] == "DECISION_CHECK"
    assert decision["is_assisted"] is False
    assert decision["user_confidence"] == 5
    assert decision["user_reasoning"] == "Strong BTN open with AKs"
    assert "provenance" in decision["evaluation_verdicts"]["strategy"]
    assert decision["chosen_action"] != "check"
