"""Unit tests for No-Limit Texas Hold'em game state machine and betting rules."""

import pytest

from app.domain.exceptions import InvalidActionError
from app.domain.poker.game_state import (
    Action,
    ActionType,
    GameConfig,
    GameState,
    Street,
)


class TestGameStateAndBettingRules:
    """Test suite for betting state transitions, action legality, and position handling."""

    def test_heads_up_positions_and_preflop_action_order(self) -> None:
        """In Heads-Up: Button is SB (seat 0), non-button is BB (seat 1).

        Preflop: Button (SB) acts FIRST.
        Postflop: BB acts FIRST, Button acts LAST.
        """
        cfg = GameConfig(small_blind=5, big_blind=10, max_players=2)
        state = GameState.start_hand(
            config=cfg,
            players_data=[("alice", 1000), ("bob", 1000)],
            button_seat_index=0,
        )

        assert state.players[0].position_name == "BT"
        assert state.players[1].position_name == "BB"
        assert state.players[0].round_bet == 5  # Alice posted SB
        assert state.players[1].round_bet == 10  # Bob posted BB
        assert state.current_actor_seat == 0  # Alice (Button/SB) acts first preflop!

        # Alice calls 5 more (total round_bet = 10)
        state = state.apply_action(Action("alice", ActionType.CALL, 5))
        assert state.players[0].round_bet == 10
        assert state.current_actor_seat == 1  # Action moves to Bob (BB)

        # Bob checks his big blind option -> Round closes, advances to FLOP
        state = state.apply_action(Action("bob", ActionType.CHECK))
        assert state.street == Street.FLOP
        assert len(state.community_cards) == 3
        assert state.current_actor_seat == 1  # On flop, Bob (BB) acts first!

    def test_six_max_preflop_action_order(self) -> None:
        """In 6-max: Button=seat 0, SB=seat 1, BB=seat 2, UTG=seat 3.

        Preflop first actor is UTG (seat 3).
        """
        cfg = GameConfig(small_blind=10, big_blind=20, max_players=6)
        players = [
            ("p0_bt", 1000),
            ("p1_sb", 1000),
            ("p2_bb", 1000),
            ("p3_utg", 1000),
            ("p4_mp", 1000),
            ("p5_co", 1000),
        ]
        state = GameState.start_hand(config=cfg, players_data=players, button_seat_index=0)

        assert state.players[1].round_bet == 10  # SB
        assert state.players[2].round_bet == 20  # BB
        assert state.current_actor_seat == 3  # UTG acts first!
        assert state.players[3].position_name == "UTG"

    def test_legal_actions_facing_bet_vs_facing_check(self) -> None:
        """Verify check is legal when facing 0, but illegal when facing a bet."""
        cfg = GameConfig(small_blind=5, big_blind=10, max_players=2)
        state = GameState.start_hand(
            config=cfg,
            players_data=[("alice", 1000), ("bob", 1000)],
            button_seat_index=0,
        )
        legal_actions = state.get_legal_actions()
        legal_types = [la.action_type for la in legal_actions]

        # Facing BB of 10 with SB of 5: Alice CANNOT check
        assert ActionType.CHECK not in legal_types
        assert ActionType.FOLD in legal_types
        assert ActionType.CALL in legal_types
        assert ActionType.RAISE in legal_types

        # Attempting illegal CHECK raises InvalidActionError
        with pytest.raises(InvalidActionError):
            state.apply_action(Action("alice", ActionType.CHECK))

    def test_short_all_in_does_not_reopen_betting(self) -> None:
        """Verify Robert's Rules / TDA standard for short all-in raises:

        Player 1 bets 100.
        Player 2 raises to 200 (delta 100).
        Player 3 goes all-in for 240 (short raise: delta 40 < min_raise 100).
        Action returns to Player 1:
        Since Player 1 already faced 200 and the 40 chip increase is NOT a full raise,
        Player 1 cannot raise! Player 1 can only fold or call.
        """
        cfg = GameConfig(small_blind=5, big_blind=10, max_players=3)
        # Custom stacks: p1 has 1000, p2 has 1000, p3 has 240
        state = GameState.start_hand(
            config=cfg,
            players_data=[("p1", 1000), ("p2", 1000), ("p3", 240)],
            button_seat_index=0,
        )
        # Preflop: p1 is BT, p2 is SB, p3 is BB. First actor in 3-max is BT (p1)
        # p1 raises to 100
        state = state.apply_action(Action("p1", ActionType.RAISE, 100))
        # p2 raises to 200 (full raise, delta 100)
        state = state.apply_action(Action("p2", ActionType.RAISE, 200))
        # p3 goes all-in for 240 (was BB with 240 stack: 20 posted + 220 remaining = 240 total)
        state = state.apply_action(Action("p3", ActionType.ALL_IN, 240))

        # Now action is back to p1!
        # p1 was facing p2's full raise to 200 (delta 100) + p3's shove to 240.
        # p1 can call or re-raise p2's full raise!
        assert state.current_actor_seat == 0
        legal_p1 = state.get_legal_actions()
        assert ActionType.RAISE in [la.action_type for la in legal_p1]

        # p1 calls 240 (puts in 140 more)
        state = state.apply_action(Action("p1", ActionType.CALL, 140))

        # Now action is on p2 (who originally raised to 200)!
        # p2 faces 240 (an increase of only 40 < min_raise 100)
        # Action is NOT reopened for p2! p2 can only fold or call!
        assert state.current_actor_seat == 1
        legal_p2 = state.get_legal_actions()
        legal_types_p2 = [la.action_type for la in legal_p2]

        assert ActionType.RAISE not in legal_types_p2
        assert ActionType.CALL in legal_types_p2
        assert ActionType.FOLD in legal_types_p2

    def test_early_termination_when_all_opponents_fold(self) -> None:
        """When all opponents fold, remaining player wins pot immediately."""
        cfg = GameConfig(small_blind=5, big_blind=10, max_players=2)
        state = GameState.start_hand(
            config=cfg,
            players_data=[("alice", 1000), ("bob", 1000)],
            button_seat_index=0,
        )
        # Alice folds
        state = state.apply_action(Action("alice", ActionType.FOLD))

        assert state.street == Street.SHOWDOWN
        assert state.result is not None
        assert state.result.winners == ["bob"]
        # Bob started with 1000, posted 10, won Alice's 5 SB -> ended with 1005
        assert state.players[1].stack == 1005
        assert state.players[0].stack == 995
        # Chip conservation check
        assert sum(p.stack for p in state.players) == 2000

    def test_complete_hand_to_showdown_and_chip_conservation(self) -> None:
        """Play a full hand through Flop, Turn, River to Showdown and verify chips conserved."""
        cfg = GameConfig(small_blind=5, big_blind=10, max_players=2)
        state = GameState.start_hand(
            config=cfg,
            players_data=[("alice", 500), ("bob", 500)],
            button_seat_index=0,
        )
        # Preflop: Alice calls, Bob checks
        state = state.apply_action(Action("alice", ActionType.CALL, 5))
        state = state.apply_action(Action("bob", ActionType.CHECK))

        # Flop: Bob checks, Alice bets 20, Bob calls 20
        assert state.street == Street.FLOP
        state = state.apply_action(Action("bob", ActionType.CHECK))
        state = state.apply_action(Action("alice", ActionType.BET, 20))
        state = state.apply_action(Action("bob", ActionType.CALL, 20))

        # Turn: Bob checks, Alice checks
        assert state.street == Street.TURN
        state = state.apply_action(Action("bob", ActionType.CHECK))
        state = state.apply_action(Action("alice", ActionType.CHECK))

        # River: Bob checks, Alice checks -> Showdown!
        assert state.street == Street.RIVER
        state = state.apply_action(Action("bob", ActionType.CHECK))
        state = state.apply_action(Action("alice", ActionType.CHECK))

        assert state.street == Street.SHOWDOWN
        assert state.result is not None
        assert len(state.community_cards) == 5
        # Total chips must equal exactly 1000
        assert sum(p.stack for p in state.players) == 1000
