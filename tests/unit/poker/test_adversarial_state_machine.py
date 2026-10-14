"""Adversarial state machine tests for Texas Hold'em betting rules.

Explicitly tests Cases A through H required by Adversarial Audit 2:
- CASE A: Insufficient short all-in does not reopen action to original bettor.
- CASE B: Multiple short all-ins cumulatively meeting full raise threshold REOPENS betting.
- CASE C: Player faces bet larger than stack; calling all-in does not produce negative stack.
- CASE D: All but one fold; winner receives net pot and uncalled wager is refunded.
- CASE E: All remaining players all-in before river; engine auto-completes to showdown.
- CASE F: Heads-up button is Small Blind; acts first preflop, last postflop.
- CASE G: Big Blind facing unraised preflop pot retains check or raise option.
- CASE H: Illegal action rejection leaves original game state completely unchanged.
"""

import pytest

from app.domain.exceptions import InvalidActionError
from app.domain.poker.game_state import Action, ActionType, GameConfig, GameState, Street


class TestAdversarialStateMachine:
    """Rigorous adversarial testing of the betting rules state machine."""

    def test_case_a_insufficient_all_in_does_not_reopen(self) -> None:
        """CASE A: P1 bets 100, P2 short all-in for 140 (min raise is 100).

        Action returns to P1. P1 cannot raise; P1 can only call (40 more) or fold.
        """
        config = GameConfig(small_blind=5, big_blind=10)
        players = [("P1", 1000), ("P2", 140)]
        # Flop state where P1 bets 100, P2 raises to 140 all-in
        # For simplicity, create flop state directly or play to flop
        state = GameState.start_hand(config=config, players_data=players, button_seat_index=0)
        # Preflop: P1 is BT/SB (posts 5), P2 is BB (posts 10)
        # P1 calls 10 (puts in 5 more). P2 checks.
        state = state.apply_action(Action("P1", ActionType.CALL, 5))
        state = state.apply_action(Action("P2", ActionType.CHECK))

        assert state.street == Street.FLOP
        # Postflop in Heads-up: P2 (BB) acts first, P1 (BT) acts last
        # P2 checks
        state = state.apply_action(Action("P2", ActionType.CHECK))
        # P1 bets 100 (min raise delta becomes 100)
        state = state.apply_action(Action("P1", ActionType.BET, 100))
        # P2 shoves all-in for remaining 130 (total 130 this round, an increase of 30 < 100)
        state = state.apply_action(Action("P2", ActionType.ALL_IN, 130))

        # Now action is back to P1!
        assert state.current_actor_seat == 0
        legal = state.get_legal_actions()
        legal_types = [a.action_type for a in legal]

        # P1 CANNOT RAISE because P2's all-in was an insufficient raise (30 < 100)
        assert ActionType.RAISE not in legal_types
        # P1 can only call (30 chips) or fold
        assert ActionType.CALL in legal_types
        assert ActionType.FOLD in legal_types
        call_action = [a for a in legal if a.action_type == ActionType.CALL][0]
        assert call_action.min_amount == 30

    def test_case_b_cumulative_short_all_ins_reopen_action(self) -> None:
        """CASE B: P1 bets 100 (min raise delta 100).

        P2 short all-in for 140 (+40).
        P3 short all-in for 210 (+70 from 140, total +110 from P1).
        Cumulative increase facing P1 is 110 >= 100.
        Action MUST reopen for P1 to raise!
        """
        config = GameConfig(small_blind=5, big_blind=10)
        # 3 players: P1 (deep), P2 (140 chips), P3 (210 chips)
        players = [("P1", 1000), ("P2", 140), ("P3", 210)]
        state = GameState.start_hand(config=config, players_data=players, button_seat_index=0)
        # P1 = BTN, P2 = SB (posts 5), P3 = BB (posts 10)
        # Preflop: P1 calls 10, P2 calls 10, P3 checks
        state = state.apply_action(Action("P1", ActionType.CALL, 10))
        state = state.apply_action(Action("P2", ActionType.CALL, 5))
        state = state.apply_action(Action("P3", ActionType.CHECK))

        assert state.street == Street.FLOP
        # Postflop action order: P2 (SB), P3 (BB), P1 (BTN)
        # P2 checks, P3 checks
        state = state.apply_action(Action("P2", ActionType.CHECK))
        state = state.apply_action(Action("P3", ActionType.CHECK))

        # P1 bets 100 (min raise delta = 100)
        state = state.apply_action(Action("P1", ActionType.BET, 100))

        # P2 has 130 remaining. Goes all-in for 130 (raise_delta = 30 < 100)
        state = state.apply_action(Action("P2", ActionType.ALL_IN, 130))

        # P3 has 200 remaining. Goes all-in for 200 (from 130 to 200 is +70 < 100, but from 100 to 200 is +100 >= 100!)
        state = state.apply_action(Action("P3", ActionType.ALL_IN, 200))

        # Now action is back to P1!
        assert state.current_actor_seat == 0
        legal = state.get_legal_actions()
        legal_types = [a.action_type for a in legal]

        # Betting IS REOPENED because total increase facing P1 is 200 - 100 = 100 >= 100!
        assert ActionType.RAISE in legal_types
        raise_action = [a for a in legal if a.action_type == ActionType.RAISE][0]
        # Min raise-to is current high bet (200) + min_raise_delta (100) = 300
        assert raise_action.min_amount == 300

    def test_case_c_facing_bet_larger_than_stack_no_negative_stack(self) -> None:
        """CASE C: Player faces bet larger than stack; calling puts player all-in with exactly 0 stack."""
        config = GameConfig(small_blind=5, big_blind=10)
        players = [("P1", 1000), ("P2", 50)]
        state = GameState.start_hand(config=config, players_data=players, button_seat_index=0)
        # P1 (BTN/SB) raises to 500
        state = state.apply_action(Action("P1", ActionType.RAISE, 500))

        # P2 has 40 chips left (posted BB 10). Call needed is 490 > 40.
        legal = state.get_legal_actions()
        call_act = [a for a in legal if a.action_type == ActionType.CALL][0]
        assert call_act.max_amount == 40  # Can only call remaining stack

        state = state.apply_action(Action("P2", ActionType.CALL, 40))
        p2 = state.get_player("P2")
        p1 = state.get_player("P1")
        assert state.street == Street.SHOWDOWN
        assert p2.stack >= 0
        assert p1.stack >= 0
        # Total chips strictly conserved: 1000 + 50 = 1050
        assert p1.stack + p2.stack == 1050

    def test_case_d_all_but_one_fold_awards_net_pot_and_refunds(self) -> None:
        """CASE D: P1 bets 500, P2 folds. P1 gets net pot and uncalled wager is refunded."""
        config = GameConfig(small_blind=5, big_blind=10)
        players = [("P1", 1000), ("P2", 1000)]
        state = GameState.start_hand(config=config, players_data=players, button_seat_index=0)
        # P1 raises to 500
        state = state.apply_action(Action("P1", ActionType.RAISE, 500))
        # P2 folds
        state = state.apply_action(Action("P2", ActionType.FOLD))

        assert state.street == Street.SHOWDOWN
        assert state.result is not None
        assert state.result.winners == ["P1"]

        # P1 had put in 500, P2 put in 10 (BB).
        # Uncalled amount 490 refunded to P1. P1 wins P2's 10 chips.
        # P1 ending stack = 1000 + 10 = 1010. P2 ending stack = 1000 - 10 = 990.
        # Total chips = 2000 (conserved!).
        p1 = state.get_player("P1")
        p2 = state.get_player("P2")
        assert p1.stack == 1010
        assert p2.stack == 990
        assert p1.stack + p2.stack == 2000

    def test_case_e_all_in_players_auto_complete_hand(self) -> None:
        """CASE E: Both players all-in preflop; engine deals to river and completes showdown without actions."""
        config = GameConfig(small_blind=5, big_blind=10)
        players = [("P1", 100), ("P2", 100)]
        state = GameState.start_hand(config=config, players_data=players, button_seat_index=0)
        # P1 shoves all-in for 100
        state = state.apply_action(Action("P1", ActionType.ALL_IN, 100))
        # P2 calls all-in for 100
        state = state.apply_action(Action("P2", ActionType.CALL, 90))

        # Since both players are all-in, street automatically runs out to showdown
        assert state.street == Street.SHOWDOWN
        assert len(state.community_cards) == 5
        assert state.result is not None
        assert state.current_actor_seat is None
        assert len(state.get_legal_actions()) == 0

    def test_case_f_heads_up_action_order(self) -> None:
        """CASE F: Heads-up button is SB: acts first preflop, but last postflop."""
        config = GameConfig(small_blind=5, big_blind=10)
        players = [("P1", 1000), ("P2", 1000)]
        # Button is seat 0 (P1)
        state = GameState.start_hand(config=config, players_data=players, button_seat_index=0)
        p1 = state.get_player("P1")
        p2 = state.get_player("P2")
        assert p1.position_name == "BT"
        assert p2.position_name == "BB"

        # Preflop: P1 (Button/SB) acts first
        assert state.current_actor_seat == 0
        state = state.apply_action(Action("P1", ActionType.CALL, 5))
        # Now P2 (BB) acts
        assert state.current_actor_seat == 1
        state = state.apply_action(Action("P2", ActionType.CHECK))

        # Flop: P2 (BB) acts first postflop!
        assert state.street == Street.FLOP
        assert state.current_actor_seat == 1
        state = state.apply_action(Action("P2", ActionType.CHECK))
        # Button (P1) acts last postflop!
        assert state.current_actor_seat == 0

    def test_case_g_big_blind_option_unraised_pot(self) -> None:
        """CASE G: Preflop calls around to BB; BB retains the option to check or raise."""
        config = GameConfig(small_blind=5, big_blind=10)
        players = [("P1", 1000), ("P2", 1000), ("P3", 1000)]
        # Seat 0 = BTN (P1), Seat 1 = SB (P2), Seat 2 = BB (P3)
        state = GameState.start_hand(config=config, players_data=players, button_seat_index=0)
        # Preflop first actor is UTG (which in 3-handed is BTN / P1)
        assert state.current_actor_seat == 0
        state = state.apply_action(Action("P1", ActionType.CALL, 10))
        # SB (P2) calls 10 (puts in 5 more)
        assert state.current_actor_seat == 1
        state = state.apply_action(Action("P2", ActionType.CALL, 5))

        # Action is now on BB (P3)!
        assert state.current_actor_seat == 2
        legal = state.get_legal_actions()
        legal_types = [a.action_type for a in legal]

        # BB has the option to CHECK or RAISE!
        assert ActionType.CHECK in legal_types
        assert ActionType.RAISE in legal_types
        raise_act = [a for a in legal if a.action_type == ActionType.RAISE][0]
        # Min raise is to 20 (BB 10 + min raise delta 10)
        assert raise_act.min_amount == 20

    def test_case_h_invalid_action_leaves_state_unchanged(self) -> None:
        """CASE H: Action failing validation raises error and original state is untouched."""
        config = GameConfig(small_blind=5, big_blind=10)
        players = [("P1", 1000), ("P2", 1000)]
        state = GameState.start_hand(config=config, players_data=players, button_seat_index=0)
        state_dict_before = state.to_dict()

        # Illegal action: P1 tries to check when facing 10 BB (needs 5 to call)
        with pytest.raises(InvalidActionError):
            state.apply_action(Action("P1", ActionType.CHECK))

        # Illegal action: Wrong player acts out of turn
        with pytest.raises(InvalidActionError):
            state.apply_action(Action("P2", ActionType.CALL, 0))

        # Illegal action: Negative or below min raise
        with pytest.raises(InvalidActionError):
            state.apply_action(Action("P1", ActionType.RAISE, 12))  # Min raise is 20

        assert state.to_dict() == state_dict_before
