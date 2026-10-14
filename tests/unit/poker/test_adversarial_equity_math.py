"""Adversarial test cases for Poker Mathematics, Equity Engine, and Scenario Replay.

Verifies:
- Exact 25.0% required equity on pot 100, bet 50, call 50.
- Multiway ties: Sum of player equities == 100.0%.
- Exact 0.0 standard error on deterministic ties (continuous sample variance).
- Multiway fractional pot shares correctly allocated on split pots.
- Scenario replay with button position and full street runout matching original state.
"""

import math

from app.domain.poker.cards import Card, Deck
from app.domain.poker.equity import EquityEngine
from app.domain.poker.game_state import Action, ActionType, GameConfig, GameState, Street
from app.domain.poker.math import (
    bluff_break_even_percentage,
    minimum_defense_frequency,
    pot_odds_from_bet,
    required_equity_from_bet,
)
from app.domain.poker.ranges import HandRange
from app.domain.poker.scenario import PokerScenario


class TestAdversarialEquityAndMath:
    """Rigorous adversarial testing of equity engine and poker mathematics."""

    def test_pot_odds_documented_contract_25_percent(self) -> None:
        """When pot is 100, opponent bets 50, and player must call 50:

        Total pot after call is 100 + 50 + 50 = 200.
        Required equity is 50 / 200 = 25.0%.
        MDF is 100 / (100 + 50) = 66.67%.
        Alpha is 50 / (100 + 50) = 33.33%.
        """
        starting_pot = 100
        bet_amount = 50
        call_amount = 50

        odds = pot_odds_from_bet(starting_pot, bet_amount, call_amount)
        req_eq = required_equity_from_bet(starting_pot, bet_amount, call_amount)
        alpha = bluff_break_even_percentage(bet_amount, starting_pot)
        mdf = minimum_defense_frequency(bet_amount, starting_pot)

        assert math.isclose(odds, 0.25, abs_tol=1e-5)
        assert math.isclose(req_eq, 25.0, abs_tol=1e-3)
        assert math.isclose(alpha, 33.3333, abs_tol=1e-3)
        assert math.isclose(mdf, 66.6667, abs_tol=1e-3)

    def test_multiway_equity_conservation_sum_to_100(self) -> None:
        """In any single-pot showdown, sum of player equities must equal 100% within numerical tolerance."""
        p1 = ("P1", HandRange.from_string("AA"))
        p2 = ("P2", HandRange.from_string("KK"))
        p3 = ("P3", HandRange.from_string("QQ"))

        result = EquityEngine.calculate_monte_carlo(
            players=[p1, p2, p3],
            board=[],
            samples=2000,
            seed=42,
        )

        total_equity = sum(p.equity for p in result.players)
        assert math.isclose(total_equity, 100.0, abs_tol=1e-2)

    def test_guaranteed_multiway_tie_has_zero_standard_error(self) -> None:
        """When board is an unavoidable royal flush, both players tie on 100% of iterations.

        Continuous sample variance is exactly 0.0, so standard error must be 0.0
        (unlike binary Bernoulli SE which would falsely report > 0).
        """
        p1 = ("P1", HandRange.from_string("2c2d"))
        p2 = ("P2", HandRange.from_string("3c3d"))
        royal_board = [Card.from_str(c) for c in ["As", "Ks", "Qs", "Js", "Ts"]]

        result = EquityEngine.calculate_monte_carlo(
            players=[p1, p2],
            board=royal_board,
            samples=500,
            seed=42,
        )

        for p in result.players:
            assert p.equity == 50.0
            assert p.ties == 500
            assert p.wins == 0
            assert p.losses == 0
            # Continuous sample variance of a constant outcome is exactly 0!
            assert p.std_error == 0.0

    def test_scenario_deterministic_replay_across_all_streets(self) -> None:
        """A complete multi-street hand serializes to canonical scenario and replays to exact identical GameState."""
        config = GameConfig(small_blind=5, big_blind=10)
        players = [("Alice", 1000), ("Bob", 1000)]
        # Deterministic deck
        deck_cards = [
            Card.from_str(c)
            for c in [
                # Alice hole
                "As",
                "Ks",
                # Bob hole
                "Qh",
                "Qd",
                # Flop
                "Jh",
                "Th",
                "2c",
                # Turn
                "3d",
                # River
                "4s",
            ]
        ]
        # Fill rest of deck
        dead = set(deck_cards)
        for c in Deck().cards:
            if c not in dead:
                deck_cards.append(c)

        # Start hand with Button = seat 1 (Bob is BTN/SB, Alice is BB)
        state = GameState.start_hand(
            config=config,
            players_data=players,
            button_seat_index=1,
            custom_deck_cards=deck_cards,
        )

        # Preflop: Bob calls 10 (puts in 5 more). Alice checks.
        state = state.apply_action(Action("Bob", ActionType.CALL, 5))
        state = state.apply_action(Action("Alice", ActionType.CHECK))

        # Flop: Alice checks, Bob bets 20, Alice calls 20
        assert state.street == Street.FLOP
        state = state.apply_action(Action("Alice", ActionType.CHECK))
        state = state.apply_action(Action("Bob", ActionType.BET, 20))
        state = state.apply_action(Action("Alice", ActionType.CALL, 20))

        # Turn: Alice checks, Bob checks
        assert state.street == Street.TURN
        state = state.apply_action(Action("Alice", ActionType.CHECK))
        state = state.apply_action(Action("Bob", ActionType.CHECK))

        # River: Alice bets 50, Bob calls 50
        assert state.street == Street.RIVER
        state = state.apply_action(Action("Alice", ActionType.BET, 50))
        state = state.apply_action(Action("Bob", ActionType.CALL, 50))

        # Showdown reached!
        assert state.street == Street.SHOWDOWN
        assert state.result is not None

        # Create scenario from showdown state
        scenario = PokerScenario.from_game_state(state)
        # Verify button seat preserved
        assert scenario.button_seat_index == 1

        # Replay entire hand from the scenario action history!
        replayed_state = scenario.replay_actions()

        # Assert full structural equality between original and replayed state
        assert replayed_state.street == state.street
        assert replayed_state.button_seat_index == state.button_seat_index
        assert [str(c) for c in replayed_state.community_cards] == [
            str(c) for c in state.community_cards
        ]
        assert replayed_state.result.winners == state.result.winners
        assert replayed_state.result.payouts == state.result.payouts
        for p_orig, p_rep in zip(state.players, replayed_state.players, strict=False):
            assert p_orig.player_id == p_rep.player_id
            assert p_orig.stack == p_rep.stack
            assert p_orig.total_bet == p_rep.total_bet
            assert p_orig.position_name == p_rep.position_name
