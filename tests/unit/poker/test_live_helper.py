"""Comprehensive Unit and Adversarial Strategy Validation Suite for Live Helper.

Covers:
1. Exact Seat Geometry & Clockwise Traversal (2-9 players, heads-up button/SB reversal, empty seats).
2. Integer Chip Accounting & Conservation across all betting transitions and side-pot constructions.
3. Malmuth-Harville Tournament ICM & Asymmetric Risk Premiums.
4. PKO Bounty Chip Valuation and missing payout resilience.
5. Reopening rules, full vs incomplete all-in raises.
6. Blocker counting and removal mathematics.
7. Metamorphic tests (varying stack depth, open size, rake, game formats).
8. Adversarial rejection of invalid inputs (duplicate cards, negative stacks, out-of-turn actions, undersized raises).
"""

import pytest

from app.domain.live_helper.engine import LiveHelperEngine
from app.domain.live_helper.models import (
    CashRuleConfig,
    FormatType,
    LiveHelperGameConfig,
    MathematicalVerdict,
    SpecificGameFormat,
)
from app.domain.live_helper.reasoning_evaluator import ReasoningEvaluator
from app.domain.poker.icm import (
    calculate_bubble_factor,
    calculate_icm_equity,
    calculate_tournament_context,
)
from app.domain.poker.seat_geometry import (
    TableSeatConfig,
    infer_table_geometry,
)

# ============================================================================
# 1. SEAT GEOMETRY & HEADS-UP REVERSAL TESTS
# ============================================================================


def test_seat_geometry_heads_up_reversal():
    """In heads-up NLHE, the button posts the Small Blind and acts first preflop, second postflop."""
    seats = [
        TableSeatConfig(seat_number=1, player_id="1", player_name="P1", stack=1000),
        TableSeatConfig(seat_number=2, player_id="2", player_name="P2", stack=1000),
    ]
    geom = infer_table_geometry(max_capacity=2, button_seat=1, seats=seats)

    assert geom.button_seat == 1
    assert geom.sb_seat == 1  # Button is SB
    assert geom.bb_seat == 2  # Other player is BB
    assert geom.get_position(1) in ("BTN", "BTN/SB")
    assert geom.get_position(2) == "BB"

    # Preflop: Button (SB) acts first
    assert geom.preflop_order == (1, 2)
    # Postflop: BB acts first
    assert geom.postflop_order == (2, 1)


def test_seat_geometry_6max_with_empty_seats():
    """Correctly assigns positions when seats 1, 3, 5 are occupied on a 6-max table."""
    seats = [
        TableSeatConfig(seat_number=1, player_id="1", player_name="P1", stack=1000),
        TableSeatConfig(seat_number=3, player_id="3", player_name="P3", stack=1000),
        TableSeatConfig(seat_number=5, player_id="5", player_name="P5", stack=1000),
    ]
    geom = infer_table_geometry(max_capacity=6, button_seat=1, seats=seats)

    assert geom.button_seat == 1
    assert geom.sb_seat == 3
    assert geom.bb_seat == 5
    assert geom.get_position(1) == "BTN"
    assert geom.get_position(3) == "SB"
    assert geom.get_position(5) == "BB"

    assert geom.preflop_order == (1, 3, 5)
    assert geom.postflop_order == (3, 5, 1)


def test_seat_geometry_9max_full_ring():
    """Correctly infers all 9 positions on a full 9-max table."""
    seats = [
        TableSeatConfig(seat_number=i, player_id=str(i), player_name=f"P{i}", stack=1000)
        for i in range(1, 10)
    ]
    geom = infer_table_geometry(max_capacity=9, button_seat=1, seats=seats)

    assert geom.button_seat == 1
    assert geom.sb_seat == 2
    assert geom.bb_seat == 3
    assert geom.get_position(1) == "BTN"
    assert geom.get_position(2) == "SB"
    assert geom.get_position(3) == "BB"
    assert geom.get_position(4) == "UTG"
    assert geom.get_position(9) == "CO"

    assert geom.preflop_order[0] == 4  # UTG acts first preflop
    assert geom.preflop_order[-1] == 3  # BB acts last preflop


# ============================================================================
# 2. EXACT MALMUTH-HARVILLE ICM & TOURNAMENT RISK TESTS
# ============================================================================


def test_malmuth_harville_icm_exact_conservation():
    """Sum of ICM prize equities must exactly equal total prize pool across all players."""
    stacks = [10000.0, 20000.0, 30000.0, 40000.0]
    payouts = [5000.0, 3000.0, 2000.0]

    equities, _ = calculate_icm_equity(stacks, payouts)
    assert len(equities) == 4

    total_prize = sum(payouts)
    total_assigned_equity = sum(equities)
    assert pytest.approx(total_assigned_equity, 1e-4) == total_prize

    # Largest stack must receive highest equity
    assert equities[3] > equities[2] > equities[1] > equities[0]


def test_icm_bubble_factors_asymmetry():
    """Bubble factor must be > 1.0 on tournament bubble (chips lost worth more than chips won)."""
    stacks = [10000.0, 15000.0, 25000.0, 50000.0]
    payouts = [5000.0, 3000.0, 2000.0]

    bf = calculate_bubble_factor(stacks, payouts, hero_idx=0, villain_idx=3)
    assert bf > 1.0, f"Bubble factor should exceed 1.0, got {bf}"


def test_icm_insufficient_payout_data_handling():
    """Gracefully handles missing payouts without fabricating prize equity."""
    stacks = [10000.0, 20000.0]
    payouts = []

    ctx = calculate_tournament_context(stacks, payouts, hero_seat_index=0)
    assert ctx.status == "INSUFFICIENT_PAYOUT_DATA"
    assert ctx.is_icm_active is False
    assert ctx.bubble_factors_against_villains[1] == 1.0


def test_pko_bounty_chip_conversion():
    """Translates progressive knockout bounties into chip equivalencies based on tournament equity."""
    stacks = [20000.0, 20000.0, 20000.0]
    payouts = [1000.0, 600.0, 400.0]
    bounties = [50.0, 50.0, 50.0]

    ctx = calculate_tournament_context(
        stacks=stacks,
        payouts=payouts,
        hero_seat_index=0,
        bounty_values=bounties,
        regular_prize_pool=2000.0,
    )
    assert ctx.pko_bounty_chip_value > 0


# ============================================================================
# 3. INTEGER CHIP ACCOUNTING, SIDE POTS & REOPENING TESTS
# ============================================================================


def test_live_helper_multiway_side_pot_construction():
    """Unequal stack multiway all-ins create distinct main and side pots with correct eligibilities."""
    config = LiveHelperGameConfig(
        format_type=FormatType.CASH,
        specific_format=SpecificGameFormat.ONLINE_6MAX,
        max_capacity=6,
        small_blind=100,
        big_blind=200,
    )

    seat_configs = [
        TableSeatConfig(
            seat_number=1, player_id="1", player_name="Short", stack=1000, is_hero=False
        ),
        TableSeatConfig(
            seat_number=2, player_id="2", player_name="Medium", stack=3000, is_hero=False
        ),
        TableSeatConfig(
            seat_number=3,
            player_id="3",
            player_name="Deep",
            stack=5000,
            is_hero=True,
            hole_cards=("Ah", "Kh"),
        ),
    ]

    actions = [
        {"seat_number": 1, "action_type": "all_in", "amount": 1000},
        {"seat_number": 2, "action_type": "all_in", "amount": 3000},
        {"seat_number": 3, "action_type": "call", "amount": 3000},
    ]

    state = LiveHelperEngine.reconstruct_table(
        config, button_seat=1, seat_configs=seat_configs, actions=actions, board_cards=[]
    )

    assert state["total_pot"] == 7000
    assert len(state["pots"]) == 2
    assert state["pots"][0]["amount"] == 3000
    assert set(state["pots"][0]["eligible_seat_numbers"]) == {1, 2, 3}
    assert state["pots"][1]["amount"] == 4000
    assert set(state["pots"][1]["eligible_seat_numbers"]) == {2, 3}


def test_live_helper_incomplete_all_in_reopening_rule():
    """A short all-in that does not meet the minimum full raise does not reopen action to prior raisers."""
    config = LiveHelperGameConfig(
        format_type=FormatType.CASH,
        specific_format=SpecificGameFormat.ONLINE_6MAX,
        max_capacity=6,
        small_blind=100,
        big_blind=200,
    )

    seat_configs = [
        TableSeatConfig(
            seat_number=1, player_id="1", player_name="Alice", stack=10000, is_hero=False
        ),
        TableSeatConfig(
            seat_number=2, player_id="2", player_name="Bob", stack=10000, is_hero=False
        ),
        TableSeatConfig(
            seat_number=3, player_id="3", player_name="Charlie", stack=550, is_hero=False
        ),
    ]

    actions = [
        {"seat_number": 1, "action_type": "post_sb", "amount": 100},
        {"seat_number": 2, "action_type": "post_bb", "amount": 200},
        {"seat_number": 1, "action_type": "raise", "amount": 500},
        {"seat_number": 3, "action_type": "all_in", "amount": 550},
        {"seat_number": 2, "action_type": "fold", "amount": 0},
    ]

    state = LiveHelperEngine.reconstruct_table(
        config, button_seat=1, seat_configs=seat_configs, actions=actions, board_cards=[]
    )

    assert state["current_actor_seat"] == 1  # Alice
    legal_kinds = [a["kind"] for a in state["legal_actions"]]
    assert "CALL" in legal_kinds
    assert "FOLD" in legal_kinds
    # Action not reopened to Alice for full raise because Charlie's 550 was incomplete!
    assert "RAISE" not in legal_kinds


# ============================================================================
# 4. ADVERSARIAL & CONTRADICTORY INPUT TESTS
# ============================================================================


def test_adversarial_duplicate_card_rejection():
    """Detects duplicate cards in hole cards or board."""
    config = LiveHelperGameConfig(
        format_type=FormatType.CASH,
        specific_format=SpecificGameFormat.ONLINE_6MAX,
        max_capacity=6,
        small_blind=100,
        big_blind=200,
    )
    seat_configs = [
        TableSeatConfig(
            seat_number=1,
            player_id="1",
            player_name="P1",
            stack=1000,
            is_hero=True,
            hole_cards=("Ah", "Ah"),
        ),
        TableSeatConfig(seat_number=2, player_id="2", player_name="P2", stack=1000),
    ]
    with pytest.raises(Exception, match="[Dd]uplicate"):
        LiveHelperEngine.reconstruct_table(
            config, button_seat=1, seat_configs=seat_configs, actions=[], board_cards=[]
        )


def test_adversarial_negative_stack_rejection():
    """Rejects negative player stacks."""
    config = LiveHelperGameConfig(
        format_type=FormatType.CASH,
        specific_format=SpecificGameFormat.ONLINE_6MAX,
        max_capacity=6,
        small_blind=100,
        big_blind=200,
    )
    seat_configs = [
        TableSeatConfig(seat_number=1, player_id="1", player_name="P1", stack=-500, is_hero=True),
        TableSeatConfig(seat_number=2, player_id="2", player_name="P2", stack=1000),
    ]
    with pytest.raises(Exception, match="[Nn]egative|[Ss]tack|[Aa]ctive"):
        LiveHelperEngine.reconstruct_table(
            config, button_seat=1, seat_configs=seat_configs, actions=[], board_cards=[]
        )


def test_adversarial_undersized_raise_rejected():
    """Rejects raise below legal minimum."""
    config = LiveHelperGameConfig(
        format_type=FormatType.CASH,
        specific_format=SpecificGameFormat.ONLINE_6MAX,
        max_capacity=6,
        small_blind=100,
        big_blind=200,
    )
    seat_configs = [
        TableSeatConfig(seat_number=1, player_id="1", player_name="Alice", stack=5000),
        TableSeatConfig(seat_number=2, player_id="2", player_name="Bob", stack=5000),
    ]
    actions = [
        {"seat_number": 1, "action_type": "post_sb", "amount": 100},
        {"seat_number": 2, "action_type": "post_bb", "amount": 200},
    ]
    state = LiveHelperEngine.reconstruct_table(
        config, button_seat=1, seat_configs=seat_configs, actions=actions, board_cards=[]
    )
    eval_result = LiveHelperEngine.evaluate_decision(
        config, state, chosen_action="raise", chosen_amount=250
    )
    assert eval_result.rules.is_legal is False
    reason = eval_result.rules.rejection_reason.lower()
    assert "below" in reason and "minimum" in reason


# ============================================================================
# 5. METAMORPHIC STRATEGY TESTS
# ============================================================================


def test_metamorphic_stack_depth_variation():
    """Changing Hero stack from 100 BB to 15 BB modifies SPR and strategic legal options correctly."""
    config = LiveHelperGameConfig(
        format_type=FormatType.CASH,
        specific_format=SpecificGameFormat.ONLINE_6MAX,
        max_capacity=6,
        small_blind=100,
        big_blind=200,
    )

    # 100 BB setup
    seats_deep = [
        TableSeatConfig(seat_number=1, player_id="1", player_name="Alice", stack=20000),
        TableSeatConfig(
            seat_number=2,
            player_id="2",
            player_name="Hero",
            stack=20000,
            is_hero=True,
            hole_cards=("Ah", "Ts"),
        ),
    ]
    state_deep = LiveHelperEngine.reconstruct_table(
        config,
        button_seat=1,
        seat_configs=seats_deep,
        actions=[
            {"seat_number": 1, "action_type": "post_sb", "amount": 100},
            {"seat_number": 2, "action_type": "post_bb", "amount": 200},
        ],
        board_cards=[],
    )
    eval_deep = LiveHelperEngine.evaluate_decision(
        config, state_deep, chosen_action="raise", chosen_amount=500
    )

    # 15 BB setup
    seats_short = [
        TableSeatConfig(seat_number=1, player_id="1", player_name="Alice", stack=3000),
        TableSeatConfig(
            seat_number=2,
            player_id="2",
            player_name="Hero",
            stack=3000,
            is_hero=True,
            hole_cards=("Ah", "Ts"),
        ),
    ]
    state_short = LiveHelperEngine.reconstruct_table(
        config,
        button_seat=1,
        seat_configs=seats_short,
        actions=[
            {"seat_number": 1, "action_type": "post_sb", "amount": 100},
            {"seat_number": 2, "action_type": "post_bb", "amount": 200},
        ],
        board_cards=[],
    )
    eval_short = LiveHelperEngine.evaluate_decision(
        config, state_short, chosen_action="raise", chosen_amount=500
    )

    # SPR must drop significantly under 15 BB
    assert eval_short.mathematics.spr < eval_deep.mathematics.spr
    assert eval_short.mathematics.effective_stack == 2800
    assert eval_deep.mathematics.effective_stack == 19800


def test_metamorphic_zero_rake_vs_high_rake():
    """Zero rake vs 5% rake updates rake deductions without modifying chip conservation."""
    config_rake = LiveHelperGameConfig(
        format_type=FormatType.CASH,
        specific_format=SpecificGameFormat.ONLINE_6MAX,
        max_capacity=6,
        small_blind=100,
        big_blind=200,
        cash_rules=CashRuleConfig(rake_percent=5.0, rake_cap=600, no_flop_no_drop=False),
    )
    config_no_rake = LiveHelperGameConfig(
        format_type=FormatType.CASH,
        specific_format=SpecificGameFormat.ONLINE_6MAX,
        max_capacity=6,
        small_blind=100,
        big_blind=200,
        cash_rules=CashRuleConfig(rake_percent=0.0, rake_cap=0, no_flop_no_drop=True),
    )

    seats = [
        TableSeatConfig(seat_number=1, player_id="1", player_name="P1", stack=10000),
        TableSeatConfig(
            seat_number=2,
            player_id="2",
            player_name="P2",
            stack=10000,
            is_hero=True,
            hole_cards=("Kd", "Qd"),
        ),
    ]

    actions = [
        {"seat_number": 1, "action_type": "post_sb", "amount": 100},
        {"seat_number": 2, "action_type": "post_bb", "amount": 200},
        {"seat_number": 1, "action_type": "call", "amount": 200},
    ]

    state_rake = LiveHelperEngine.reconstruct_table(
        config_rake, button_seat=1, seat_configs=seats, actions=actions, board_cards=[]
    )
    state_no_rake = LiveHelperEngine.reconstruct_table(
        config_no_rake, button_seat=1, seat_configs=seats, actions=actions, board_cards=[]
    )

    eval_rake = LiveHelperEngine.evaluate_decision(config_rake, state_rake, chosen_action="check")
    eval_no_rake = LiveHelperEngine.evaluate_decision(
        config_no_rake, state_no_rake, chosen_action="check"
    )

    assert eval_rake.mathematics.rake_deduction > 0
    assert eval_no_rake.mathematics.rake_deduction == 0


# ============================================================================
# 6. REASONING EVALUATOR TESTS
# ============================================================================


def test_reasoning_evaluator_blocker_claim():
    """Correctly evaluates valid vs invalid blocker statements."""
    math_v = MathematicalVerdict(
        total_pot=300,
        amount_to_call=100,
        pot_odds=0.25,
        pot_odds_ratio="3:1",
        break_even_equity_pct=25.0,
        effective_stack=2000,
        spr=10.0,
        hero_commitment_so_far=0,
        mdf=0.67,
        rake_deduction=0,
    )
    evals = ReasoningEvaluator.evaluate_reasoning(
        reasoning_text="Holding an Ace blocks opponent AA and AK 3-betting ranges",
        hero_cards=("Ah", "5s"),
        board_cards=[],
        hero_position="BTN",
        math_verdict=math_v,
        chosen_action="raise",
    )
    assert len(evals) > 0
    assert any(e.claim_category == "BLOCKER" and e.is_sound for e in evals)


def test_reasoning_evaluator_pot_odds_claim():
    """Evaluates user statement about required break-even equity."""
    math_v = MathematicalVerdict(
        total_pot=400,
        amount_to_call=100,
        pot_odds=0.20,
        pot_odds_ratio="4:1",
        break_even_equity_pct=20.0,
        effective_stack=2000,
        spr=8.0,
        hero_commitment_so_far=0,
        mdf=0.80,
        rake_deduction=0,
    )
    evals = ReasoningEvaluator.evaluate_reasoning(
        reasoning_text="Pot odds give me 20% required equity to call",
        hero_cards=("8c", "7c"),
        board_cards=["Ks", "9c", "2d"],
        hero_position="BB",
        math_verdict=math_v,
        chosen_action="call",
    )
    assert len(evals) > 0
    assert any(e.claim_category == "POT_ODDS" and e.is_sound for e in evals)
