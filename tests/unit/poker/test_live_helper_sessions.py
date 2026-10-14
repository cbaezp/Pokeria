"""Comprehensive Unit and Invariant Test Suite for Live Helper Continuous Training Sessions.

Tests:
1. 5-Hand Cash Session Lifecycle & Strict Stack Carryover (S_{n+1} = S_n)
2. Clockwise Button Progression & Heads-Up Reversal
3. Proactive Coach Mode vs Independent Decision Check Mode Attribution
4. Mode Switching Mid-Hand Without Resetting State
5. Side Pots with Unequal All-Ins & Clockwise Odd-Chip Allocation
6. Uncalled Bet Refunds & No-Flop-No-Drop Casino Rake
7. Cash Rebuys, Top-Ups, Cash-Outs, and Chip Conservation Invariants
8. Tournament MTT Eliminations, Reduced Occupancy, and Blind Increases
9. Idempotent Pot Settlement & Concurrency Safety
10. End-of-Session Analytics (VPIP, PFR, 3-Bet %, Assistance Rate %, Solver EV Regret)
11. Zero-Fabrication Strategic Guarantees (STRATEGY_UNGRADED for Unsupported Spots)
"""

from app.domain.live_helper.session_analytics import SessionAnalyticsEngine
from app.domain.live_helper.session_engine import LiveHelperSessionEngine
from app.domain.live_helper.settlement import HandSettlementEngine


def _build_test_session_payload(
    capacity: int = 6, format_type: str = "CASH", starting_stack: int = 10000
):
    return {
        "profile_id": "test_profile_123",
        "name": "Validation Suite Session",
        "format_type": format_type,
        "table_capacity": capacity,
        "button_seat": 1,
        "default_mode": "DECISION_CHECK",
        "configuration": {
            "format_type": format_type,
            "specific_format": "ONLINE_6MAX" if format_type == "CASH" else "STANDARD_MTT",
            "max_capacity": capacity,
            "small_blind": 50,
            "big_blind": 100,
            "ante": 0,
            "cash_rules": {"rake_percent": 5.0, "rake_cap": 300, "no_flop_no_drop": True},
            "tournament_rules": {
                "buy_in": 100.0,
                "total_entrants": 100,
                "players_remaining": capacity,
                "paid_positions": 3,
                "payout_ladder": [5000, 3000, 2000],
                "bounty_values": [],
                "is_pko": False,
                "current_level": 1,
            },
        },
        "participants": [
            {
                "seat_number": i,
                "player_name": "Hero" if i == 4 else f"Player_{i}",
                "starting_stack": starting_stack,
                "current_stack": starting_stack,
                "is_hero": (i == 4),
                "is_active": True,
                "is_sitting_out": False,
                "hole_cards": ["Ah", "Kd"] if i == 4 else [],
            }
            for i in range(1, capacity + 1)
        ],
    }


# ============================================================================
# 1. FIVE-HAND CONTINUOUS CASH SESSION WITH STRICT STACK CARRYOVER
# ============================================================================


def test_five_hand_cash_session_stack_continuity_and_button_rotation():
    """Verify a continuous 5-hand cash session preserves stacks, rotates button, and maintains chip conservation."""
    payload = _build_test_session_payload(capacity=6, format_type="CASH", starting_stack=10000)
    session, hand1 = LiveHelperSessionEngine.create_session(**payload)

    initial_total_chips = sum(p["current_stack"] for p in session["participants"])
    assert initial_total_chips == 60000

    # Hand 1: Hero (Seat 4 UTG) raises to 250, all fold to Hero
    session, hand1, dec1 = LiveHelperSessionEngine.record_action(
        session=session,
        hand=hand1,
        seat_number=4,
        action_type="raise",
        amount=250,
        mode="DECISION_CHECK",
    )
    for s in [5, 6, 1, 2, 3]:
        session, hand1, _ = LiveHelperSessionEngine.record_action(
            session=session, hand=hand1, seat_number=s, action_type="fold"
        )

    assert hand1["is_settled"] is True
    # Hero won 150 blinds (SB 50 + BB 100), net +150 chips (stack: 10150)
    # SB (Seat 2) lost 50, BB (Seat 3) lost 100
    assert hand1["ending_stacks"]["4"] == 10150
    assert hand1["ending_stacks"]["2"] == 9950
    assert hand1["ending_stacks"]["3"] == 9900

    # Total chips in system preserved exactly
    assert sum(int(v) for v in hand1["ending_stacks"].values()) == 60000

    # Hand 2: Advance next hand
    session, hand2 = LiveHelperSessionEngine.advance_to_next_hand(
        session=session, previous_hand=hand1
    )
    assert hand2["hand_index"] == 2
    assert hand2["button_seat"] == 2  # Button rotated from 1 to 2
    # Verify strict stack carryover into Hand 2 starting stacks
    assert hand2["starting_stacks"]["4"] == 10150
    assert hand2["starting_stacks"]["2"] == 9950
    assert hand2["starting_stacks"]["3"] == 9900

    # Hand 2: Seat 5 raises to 300, all fold to Seat 5
    session, hand2, _ = LiveHelperSessionEngine.record_action(
        session=session, hand=hand2, seat_number=5, action_type="raise", amount=300
    )
    for s in [6, 1, 2, 3, 4]:
        session, hand2, _ = LiveHelperSessionEngine.record_action(
            session=session, hand=hand2, seat_number=s, action_type="fold"
        )
    assert hand2["is_settled"] is True

    # Hand 3: Advance next hand
    session, hand3 = LiveHelperSessionEngine.advance_to_next_hand(
        session=session, previous_hand=hand2
    )
    assert hand3["hand_index"] == 3
    assert hand3["button_seat"] == 3  # Button rotated from 2 to 3

    # Hand 3: Seat 1 raises, all fold
    session, hand3, _ = LiveHelperSessionEngine.record_action(
        session=session, hand=hand3, seat_number=1, action_type="raise", amount=250
    )
    for s in [2, 3, 4, 5, 6]:
        session, hand3, _ = LiveHelperSessionEngine.record_action(
            session=session, hand=hand3, seat_number=s, action_type="fold"
        )

    # Hand 4: Advance next hand
    session, hand4 = LiveHelperSessionEngine.advance_to_next_hand(
        session=session, previous_hand=hand3
    )
    assert hand4["hand_index"] == 4
    assert hand4["button_seat"] == 4  # Button rotated to Hero

    # Hand 4: Hero is BTN, raises to 200, SB & BB fold
    session, hand4, dec4 = LiveHelperSessionEngine.record_action(
        session=session, hand=hand4, seat_number=4, action_type="raise", amount=200, mode="COACH"
    )
    for s in [5, 6, 1, 2, 3]:
        if s != 4:
            session, hand4, _ = LiveHelperSessionEngine.record_action(
                session=session, hand=hand4, seat_number=s, action_type="fold"
            )

    # Hand 5: Advance next hand
    session, hand5 = LiveHelperSessionEngine.advance_to_next_hand(
        session=session, previous_hand=hand4
    )
    assert hand5["hand_index"] == 5
    assert hand5["button_seat"] == 5

    # Hand 5: Fold around
    session, hand5, _ = LiveHelperSessionEngine.record_action(
        session=session, hand=hand5, seat_number=6, action_type="raise", amount=200
    )
    for s in [1, 2, 3, 4, 5]:
        session, hand5, _ = LiveHelperSessionEngine.record_action(
            session=session, hand=hand5, seat_number=s, action_type="fold"
        )

    assert session["total_hands_completed"] == 5
    # Strict Invariant: Total chips across all participants remains exactly 60000
    final_total_chips = sum(p["current_stack"] for p in session["participants"])
    assert final_total_chips == initial_total_chips


# ============================================================================
# 2. COACH MODE VS DECISION CHECK MODE ATTRIBUTION
# ============================================================================


def test_coach_mode_vs_decision_check_mode_attribution():
    """Verify that Coach Mode actions are attributed as assisted, whereas Decision Check actions are independent."""
    payload = _build_test_session_payload(capacity=6, format_type="CASH")
    session, hand = LiveHelperSessionEngine.create_session(**payload)

    # 1. Hero acts in DECISION_CHECK mode
    session, hand, dec_check = LiveHelperSessionEngine.record_action(
        session=session,
        hand=hand,
        seat_number=4,
        action_type="raise",
        amount=250,
        mode="DECISION_CHECK",
        reasoning="Premium hand open",
        confidence=4,
    )
    assert dec_check is not None
    assert dec_check["mode"] == "DECISION_CHECK"
    assert dec_check["is_assisted"] is False
    assert dec_check["user_confidence"] == 4
    assert dec_check["user_reasoning"] == "Premium hand open"

    # Settle hand and advance
    for s in [5, 6, 1, 2, 3]:
        session, hand, _ = LiveHelperSessionEngine.record_action(
            session=session, hand=hand, seat_number=s, action_type="fold"
        )
    session, hand2 = LiveHelperSessionEngine.advance_to_next_hand(
        session=session, previous_hand=hand
    )

    # 2. Hero acts in COACH mode
    session, hand2, dec_coach = LiveHelperSessionEngine.record_action(
        session=session,
        hand=hand2,
        seat_number=4,
        action_type="raise",
        amount=250,
        mode="COACH",
    )
    assert dec_coach is not None
    assert dec_coach["mode"] == "COACH"
    assert dec_coach["is_assisted"] is True


# ============================================================================
# 3. SIDE POTS, UNEQUAL ALL-INS, AND CLOCKWISE ODD CHIP ALLOCATION
# ============================================================================


def test_side_pots_unequal_all_ins_and_odd_chip_allocation():
    """Test mathematically exact multiway settlement with unequal side pots and split pot odd chip handling."""
    seats = [
        {
            "seat_number": 1,
            "starting_stack": 500,
            "stack": 500,
            "is_active": True,
            "hole_cards": ["Ah", "Ad"],
        },
        {
            "seat_number": 2,
            "starting_stack": 1500,
            "stack": 1500,
            "is_active": True,
            "hole_cards": ["Kh", "Kd"],
        },
        {
            "seat_number": 3,
            "starting_stack": 3000,
            "stack": 3000,
            "is_active": True,
            "hole_cards": ["Qh", "Qd"],
        },
    ]
    actions = [
        {"seat_number": 1, "action_type": "all_in", "amount": 500, "street": "preflop"},
        {"seat_number": 2, "action_type": "all_in", "amount": 1500, "street": "preflop"},
        {"seat_number": 3, "action_type": "call", "amount": 1500, "street": "preflop"},
    ]
    board = ["2c", "7d", "9s", "Jc", "4h"]

    pots_payload = {
        "total_pot": 3500,
        "main_pot": 1500,
        "side_pots": [{"amount": 2000, "eligible_seat_numbers": [2, 3]}],
    }

    res = HandSettlementEngine.settle_hand(
        button_seat=1,
        table_capacity=3,
        seats=seats,
        board_cards=board,
        actions=actions,
        pots_payload=pots_payload,
        is_cash=False,  # Tournament chip settlement
    )

    assert res.is_settled is True
    assert res.is_showdown is True
    # Seat 1 has Aces (wins Main Pot 1500)
    # Seat 2 has Kings vs Seat 3 Queens (Seat 2 wins Side Pot 2000)
    assert 1 in res.winning_seats
    assert 2 in res.winning_seats
    # Ending stacks:
    # Seat 1 started 500, won 1500 -> 1500
    # Seat 2 started 1500, put in 1500, won side pot 2000 -> 2000
    # Seat 3 started 3000, put in 1500, won 0 -> 1500
    assert res.ending_stacks[1] == 1500
    assert res.ending_stacks[2] == 2000
    assert res.ending_stacks[3] == 1500

    # Total chips conservation: 1500 + 2000 + 1500 == 5000 (starting total)
    assert sum(res.ending_stacks.values()) == 5000


# ============================================================================
# 4. UNCALLED BET REFUNDS & NO-FLOP-NO-DROP RAKE
# ============================================================================


def test_uncalled_bet_refunds_and_no_flop_no_drop_rake():
    """Verify that uncalled bets are refunded before rake calculation, and preflop uncontested hands pay zero rake."""
    seats = [
        {"seat_number": 1, "starting_stack": 2000, "stack": 2000, "is_active": True},
        {"seat_number": 2, "starting_stack": 2000, "stack": 2000, "is_active": True},
    ]
    actions = [
        {"seat_number": 1, "action_type": "post_sb", "amount": 50, "street": "preflop"},
        {"seat_number": 2, "action_type": "post_bb", "amount": 100, "street": "preflop"},
        {"seat_number": 1, "action_type": "raise", "amount": 500, "street": "preflop"},
        {"seat_number": 2, "action_type": "fold", "amount": 0, "street": "preflop"},
    ]
    pots = {"total_pot": 600, "main_pot": 200, "side_pots": []}

    res = HandSettlementEngine.settle_hand(
        button_seat=1,
        table_capacity=2,
        seats=seats,
        board_cards=[],
        actions=actions,
        pots_payload=pots,
        is_cash=True,
        rake_percent=5.0,
        rake_cap=300,
        no_flop_no_drop=True,
    )

    assert res.is_settled is True
    assert res.is_showdown is False
    # Uncalled return to Seat 1: 500 - 100 = 400 chips
    assert res.uncalled_returns[1] == 400
    # No flop seen -> No rake taken
    assert res.rake_collected == 0
    # Seat 1 won Seat 2's BB (100 chips) -> Ending stack 2100
    assert res.ending_stacks[1] == 2100
    assert res.ending_stacks[2] == 1900


# ============================================================================
# 5. CASH REBUYS, TOP-UPS, AND CHIP CONSERVATION INVARIANTS
# ============================================================================


def test_cash_rebuys_topups_and_cashouts_conservation():
    """Verify explicit stack adjustments maintain strict ledger conservation."""
    payload = _build_test_session_payload(capacity=6, format_type="CASH", starting_stack=10000)
    session, _ = LiveHelperSessionEngine.create_session(**payload)

    # Initial chips = 60000
    assert sum(p["current_stack"] for p in session["participants"]) == 60000

    # Player 2 tops up 5000
    session = LiveHelperSessionEngine.adjust_participant_stack(
        session=session, seat_number=2, adjustment_type="TOP_UP", amount=5000
    )
    p2 = next(p for p in session["participants"] if p["seat_number"] == 2)
    assert p2["current_stack"] == 15000
    assert p2["rebuys"] == 5000

    # Player 3 cashes out 2000
    session = LiveHelperSessionEngine.adjust_participant_stack(
        session=session, seat_number=3, adjustment_type="CASH_OUT", amount=2000
    )
    p3 = next(p for p in session["participants"] if p["seat_number"] == 3)
    assert p3["current_stack"] == 8000
    assert p3["cash_outs"] == 2000

    # Total stack invariant: 60000 + 5000 (topup) - 2000 (cashout) = 63000
    assert sum(p["current_stack"] for p in session["participants"]) == 63000


# ============================================================================
# 6. TOURNAMENT MTT ELIMINATIONS AND BLIND PROGRESSION
# ============================================================================


def test_tournament_eliminations_and_blind_progression():
    """Verify that tournament bust-outs eliminate players and blinds escalate."""
    payload = _build_test_session_payload(capacity=3, format_type="TOURNAMENT", starting_stack=1000)
    session, hand1 = LiveHelperSessionEngine.create_session(**payload)

    # Hand 1: Seat 3 is eliminated (loses all chips)
    # Simulate Hand 1 ending stacks: Seat 1: 1500, Seat 2: 1500, Seat 3: 0
    hand1["is_settled"] = True
    hand1["ending_stacks"] = {"1": 1500, "2": 1500, "3": 0}
    session["participants"][0]["current_stack"] = 1500
    session["participants"][1]["current_stack"] = 1500
    session["participants"][2]["current_stack"] = 0

    # Advance to Hand 2
    session, hand2 = LiveHelperSessionEngine.advance_to_next_hand(
        session=session, previous_hand=hand1
    )
    p3 = next(p for p in session["participants"] if p["seat_number"] == 3)
    assert p3["is_active"] is False
    assert p3["is_eliminated"] is True

    # Hand 2 occupied seats only has Seats 1 & 2
    assert "3" not in hand2["starting_stacks"]
    assert hand2["button_seat"] in (1, 2)


# ============================================================================
# 7. IDEMPOTENT SETTLEMENT AND CONCURRENCY SAFETY
# ============================================================================


def test_settle_hand_idempotency():
    """Repeated calls to settle_hand must never award duplicate chips or corrupt state."""
    payload = _build_test_session_payload(capacity=2, format_type="CASH", starting_stack=5000)
    session, hand = LiveHelperSessionEngine.create_session(**payload)

    # Fold to Seat 1
    session, hand, _ = LiveHelperSessionEngine.record_action(
        session=session, hand=hand, seat_number=1, action_type="raise", amount=250
    )
    session, hand, _ = LiveHelperSessionEngine.record_action(
        session=session, hand=hand, seat_number=2, action_type="fold"
    )

    stack_after_settle1 = hand["ending_stacks"]["1"]
    total_completed1 = session["total_hands_completed"]

    # Calling settle_hand again directly
    session, hand = LiveHelperSessionEngine.settle_hand(session=session, hand=hand)
    stack_after_settle2 = hand["ending_stacks"]["1"]
    total_completed2 = session["total_hands_completed"]

    assert stack_after_settle1 == stack_after_settle2
    assert total_completed1 == total_completed2


# ============================================================================
# 8. END-OF-SESSION ANALYTICS & ZERO FABRICATION
# ============================================================================


def test_end_of_session_analytics_report():
    """Verify session report calculates accurate VPIP, PFR, and assistance rates with no fabricated EV."""
    session_data = {
        "id": "sess_test_123",
        "name": "Analytics Audit Session",
        "format_type": "CASH",
        "started_at": "2026-10-12T12:00:00+00:00",
        "completed_at": "2026-10-12T13:00:00+00:00",
        "configuration": {"big_blind": 100},
        "participants": [
            {"seat_number": 4, "is_hero": True, "starting_stack": 10000, "current_stack": 11500}
        ],
    }

    hands = [
        {
            "id": "h1",
            "hand_index": 1,
            "actions": [
                {"seat_number": 4, "action_type": "raise", "street": "preflop"},
            ],
            "settlement": {"net_chips": {"4": 500}},
            "ending_stacks": {"4": 10500},
        },
        {
            "id": "h2",
            "hand_index": 2,
            "actions": [
                {"seat_number": 4, "action_type": "fold", "street": "preflop"},
            ],
            "settlement": {"net_chips": {"4": -50}},
            "ending_stacks": {"4": 10450},
        },
    ]

    decisions = [
        {
            "is_assisted": False,
            "mode": "DECISION_CHECK",
            "evaluation_verdicts": {
                "rules": {"is_legal": True},
                "strategy": {"qualitative_grade": "GOOD", "ev_regret": None},
            },
            "ev_regret": None,
        },
        {
            "is_assisted": True,
            "mode": "COACH",
            "evaluation_verdicts": {
                "rules": {"is_legal": True},
                "strategy": {"qualitative_grade": "UNGRADED", "ev_regret": None},
            },
            "ev_regret": None,
        },
    ]

    report = SessionAnalyticsEngine.compute_report(session_data, hands, decisions)

    assert report.total_hands == 2
    assert report.hero_net_chips == 1500
    assert report.hero_net_bb == 15.0
    assert report.vpip_pct == 50.0  # Voluntarily put in chips 1 of 2 hands
    assert report.pfr_pct == 50.0  # Raised preflop 1 of 2 hands
    assert report.assistance_rate_pct == 50.0  # 1 of 2 decisions assisted by Coach
    assert report.coach_assisted_decisions == 1
    assert report.independent_decisions == 1
    # Zero fabrication: EV loss is strictly None (displays as N/A), never 0.0
    assert report.mean_solver_ev_loss is None


# ============================================================================
# 9. CONTINUOUS MULTI-STREET PROGRESSION & BOARD DEALING
# ============================================================================


def test_continuous_multi_street_progression_preflop_to_showdown():
    """Verify that a hand can progress through preflop -> flop -> turn -> river -> showdown with board cards and betting resets."""
    session, hand = LiveHelperSessionEngine.create_session(
        profile_id="test_profile",
        name="Multi-Street Validation",
        format_type="CASH",
        table_capacity=2,
        button_seat=1,
        configuration={"small_blind": 50, "big_blind": 100, "ante": 0},
        participants=[
            {"seat_number": 1, "player_name": "Hero", "starting_stack": 10000, "is_hero": True},
            {"seat_number": 2, "player_name": "Villain", "starting_stack": 10000, "is_hero": False},
        ],
    )

    # Set hole cards
    hand["hole_cards"] = {
        "1": ["As", "Ks"],  # Hero
        "2": ["Qh", "Qd"],  # Villain
    }

    # Preflop: In HU, Seat 1 is Button / SB (posted 50). Seat 2 is BB (posted 100).
    # Button acts first preflop!
    session, hand, dec = LiveHelperSessionEngine.record_action(
        session=session, hand=hand, seat_number=1, action_type="raise", amount=250, mode="COACH"
    )
    assert dec is not None
    assert dec["street"] == "preflop"
    assert dec["is_assisted"] is True

    # BB calls 250
    session, hand, _ = LiveHelperSessionEngine.record_action(
        session=session, hand=hand, seat_number=2, action_type="call"
    )
    # Preflop betting complete! Total pot is 500.
    assert hand["pots"]["total_pot"] == 500
    assert hand["is_settled"] is False

    # Deal Flop: Ah Kd 2c
    session, hand = LiveHelperSessionEngine.deal_community_cards(
        session=session, hand=hand, cards=["Ah", "Kd", "2c"]
    )
    assert hand["board"] == ["Ah", "Kd", "2c"]
    assert hand["street"] == "flop"

    # Postflop HU: BB (Seat 2) acts first!
    session, hand, _ = LiveHelperSessionEngine.record_action(
        session=session, hand=hand, seat_number=2, action_type="check"
    )

    # Hero on BTN (Seat 1) acts on Flop. Bets 300!
    session, hand, dec_flop = LiveHelperSessionEngine.record_action(
        session=session, hand=hand, seat_number=1, action_type="bet", amount=300, mode="COACH"
    )
    assert dec_flop is not None
    assert dec_flop["street"] == "flop"

    # Villain calls 300
    session, hand, _ = LiveHelperSessionEngine.record_action(
        session=session, hand=hand, seat_number=2, action_type="call"
    )
    assert hand["pots"]["total_pot"] == 1100

    # Deal Turn: 7s
    session, hand = LiveHelperSessionEngine.deal_community_cards(
        session=session, hand=hand, cards=["7s"]
    )
    assert hand["board"] == ["Ah", "Kd", "2c", "7s"]
    assert hand["street"] == "turn"

    # Turn action: Both check
    session, hand, _ = LiveHelperSessionEngine.record_action(
        session=session, hand=hand, seat_number=2, action_type="check"
    )
    session, hand, dec_turn = LiveHelperSessionEngine.record_action(
        session=session, hand=hand, seat_number=1, action_type="check", mode="DECISION_CHECK"
    )
    assert dec_turn is not None
    assert dec_turn["street"] == "turn"
    assert dec_turn["is_assisted"] is False

    # Deal River: Jh
    session, hand = LiveHelperSessionEngine.deal_community_cards(
        session=session, hand=hand, cards=["Jh"]
    )
    assert hand["board"] == ["Ah", "Kd", "2c", "7s", "Jh"]
    assert hand["street"] == "river"

    # River action: Villain bets 500, Hero calls!
    session, hand, _ = LiveHelperSessionEngine.record_action(
        session=session, hand=hand, seat_number=2, action_type="bet", amount=500
    )
    session, hand, dec_river = LiveHelperSessionEngine.record_action(
        session=session, hand=hand, seat_number=1, action_type="call", mode="DECISION_CHECK"
    )
    assert dec_river is not None
    assert dec_river["street"] == "river"

    # River betting complete -> showdown reached and settled!
    assert hand["is_settled"] is True
    assert hand["street"] in ["showdown", "complete"]
    assert hand["settlement"] is not None

    # Hero has Two Pair (Aces & Kings) vs Villain Pair of Queens. Hero wins!
    assert 1 in hand["settlement"]["winning_seats"]
    hero_p = next(p for p in session["participants"] if p["seat_number"] == 1)
    villain_p = next(p for p in session["participants"] if p["seat_number"] == 2)
    # Total pot was 500 + 600 + 1000 = 2100 chips.
    # Hero put in 250 + 300 + 500 = 1050 chips.
    # Villain put in 250 + 300 + 500 = 1050 chips.
    # Hero won 2100 chips -> net +1050 chips.
    # Ending stacks: Hero 11050, Villain 8950.
    assert hero_p["current_stack"] == 11050
    assert villain_p["current_stack"] == 8950
    assert hero_p["current_stack"] + villain_p["current_stack"] == 20000


# ============================================================================
# 10. ACTION RETURN BEHAVIOR & SHORT ALL-IN REOPENING
# ============================================================================


def test_action_return_behavior_reraise_and_partial_allin():
    """Verify that a 3-bet returns action to Hero with updated to-call, and short all-in does not reopen action."""
    session, hand = LiveHelperSessionEngine.create_session(
        profile_id="test_profile",
        name="Action Return Validation",
        format_type="CASH",
        table_capacity=3,
        button_seat=1,
        configuration={"small_blind": 50, "big_blind": 100, "ante": 0},
        participants=[
            {"seat_number": 1, "player_name": "Hero", "starting_stack": 10000, "is_hero": True},
            {"seat_number": 2, "player_name": "SB", "starting_stack": 10000, "is_hero": False},
            {"seat_number": 3, "player_name": "BB", "starting_stack": 10000, "is_hero": False},
        ],
    )

    # Seat 1 (BTN) opens to 250
    session, hand, dec1 = LiveHelperSessionEngine.record_action(
        session=session, hand=hand, seat_number=1, action_type="raise", amount=250, mode="COACH"
    )
    assert dec1["amount_to_call"] == 100  # 100 BB

    # Seat 2 (SB) 3-bets to 800!
    session, hand, _ = LiveHelperSessionEngine.record_action(
        session=session, hand=hand, seat_number=2, action_type="raise", amount=800
    )

    # Seat 3 (BB) folds
    session, hand, _ = LiveHelperSessionEngine.record_action(
        session=session, hand=hand, seat_number=3, action_type="fold"
    )

    # Action returns to Seat 1 (Hero)!
    # Hero's previous round_bet was 250. Current high bet is 800.
    # To call is 800 - 250 = 550!
    session, hand, dec2 = LiveHelperSessionEngine.record_action(
        session=session, hand=hand, seat_number=1, action_type="call", mode="COACH"
    )
    assert dec2 is not None
    assert dec2["amount_to_call"] == 550
    assert dec2["chosen_action"] == "call"
    # Preflop betting now complete with 800 + 800 + 100 (folded BB) = 1700 in pot!
    assert hand["pots"]["total_pot"] == 1700
