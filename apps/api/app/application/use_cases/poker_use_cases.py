"""Application use cases for Texas Hold'em poker operations.

Pure application orchestrator coordinating poker domain entities, math, ranges,
and state machine without external infrastructure dependencies.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app.domain.exceptions import ValidationError
from app.domain.poker.cards import Card, validate_unique_cards
from app.domain.poker.equity import EquityEngine
from app.domain.poker.evaluator import evaluate_hand
from app.domain.poker.game_state import Action, ActionType, GameConfig, GameState
from app.domain.poker.math import (
    bluff_break_even_percentage,
    minimum_defense_frequency,
    pot_relative_bet_size,
)
from app.domain.poker.ranges import HandRange
from app.domain.poker.scenario import PokerScenario


class PokerUseCases:
    """Use cases providing clean API interfaces to poker domain functionality."""

    @staticmethod
    def parse_cards(card_strings: Sequence[str]) -> list[dict[str, Any]]:
        """Validate and parse a list of card strings."""
        cards = [Card.from_str(s) for s in card_strings]
        validate_unique_cards(cards)
        return [c.to_dict() for c in cards]

    @staticmethod
    def evaluate_hand_from_strings(card_strings: Sequence[str]) -> dict[str, Any]:
        """Evaluate a 5-7 card poker hand."""
        if not (5 <= len(card_strings) <= 7):
            raise ValidationError("Hand evaluation requires between 5 and 7 cards", field="cards")
        cards = [Card.from_str(s) for s in card_strings]
        validate_unique_cards(cards)
        strength = evaluate_hand(cards)
        return strength.to_dict()

    @staticmethod
    def parse_range_notation(range_string: str) -> dict[str, Any]:
        """Parse poker range notation into summary statistics and combo distributions."""
        r = HandRange.from_string(range_string)
        return {
            "range": range_string,
            "combo_count": r.combo_count,
            "total_weight": round(r.total_weight, 2),
            "percentage": round(r.percentage, 2),
            "canonical_string": r.to_string(),
        }

    @staticmethod
    def calculate_pot_odds_summary(
        call_amount: int,
        pot_before_call: int | None = None,
        pot_before_bet: int | None = None,
        bet_amount: int = 0,
    ) -> dict[str, Any]:
        """Calculate pot odds, required equity, MDF, and alpha with unambiguous pot parameters.

        Documented Contract:
        - If pot_before_bet is provided (e.g. 100), facing_bet is bet_amount (e.g. 50):
          pot facing call is 100 + 50 = 150.
          total pot after call is 100 + 50 + 50 = 200.
          required equity = 50 / 200 = 25.0%.
        - If pot_before_call is provided without pot_before_bet and bet_amount == 0:
          pot facing call is pot_before_call directly.
        """
        if pot_before_bet is not None:
            starting_pot = pot_before_bet
            facing_call_pot = starting_pot + bet_amount
        elif pot_before_call is not None:
            if bet_amount > 0:
                # User provided pot before opponent's bet as pot_before_call
                starting_pot = pot_before_call
                facing_call_pot = starting_pot + bet_amount
            else:
                starting_pot = pot_before_call
                facing_call_pot = pot_before_call
        else:
            raise ValueError("Either pot_before_bet or pot_before_call must be provided")

        total_after_call = facing_call_pot + call_amount
        odds = call_amount / total_after_call if total_after_call > 0 else 0.0
        req_eq = odds * 100.0

        mdf = 0.0
        alpha = 0.0
        if bet_amount > 0 and (starting_pot + bet_amount) > 0:
            alpha = bluff_break_even_percentage(bet_amount, starting_pot)
            mdf = minimum_defense_frequency(bet_amount, starting_pot)

        sizing_33 = pot_relative_bet_size(facing_call_pot, 0.33)
        sizing_50 = pot_relative_bet_size(facing_call_pot, 0.50)
        sizing_75 = pot_relative_bet_size(facing_call_pot, 0.75)
        sizing_100 = pot_relative_bet_size(facing_call_pot, 1.00)

        return {
            "call_amount": call_amount,
            "pot_before_bet": starting_pot,
            "bet_amount": bet_amount,
            "pot_before_call": facing_call_pot,
            "total_pot_after_call": total_after_call,
            "pot_odds_fraction": round(odds, 4),
            "required_equity_pct": round(req_eq, 2),
            "alpha_bluff_break_even_pct": round(alpha, 2),
            "minimum_defense_frequency_pct": round(mdf, 2),
            "pot_relative_sizes": {
                "33_pct": sizing_33,
                "50_pct": sizing_50,
                "75_pct": sizing_75,
                "100_pct": sizing_100,
            },
        }

    @staticmethod
    def calculate_equity(
        players: Sequence[tuple[str, str]],  # (player_name, range_or_hole_cards)
        board_cards: Sequence[str] = (),
        samples: int = 10_000,
        seed: int | None = 42,
    ) -> dict[str, Any]:
        """Calculate equities between hands/ranges with card removal and confidence intervals."""
        if not (2 <= len(players) <= 6):
            raise ValidationError(
                "Equity calculation requires between 2 and 6 players", field="players"
            )

        parsed_board = [Card.from_str(c) for c in board_cards]
        validate_unique_cards(parsed_board)

        # Parse player ranges
        range_players: list[tuple[str, HandRange]] = []
        for name, r_expr in players:
            r = HandRange.from_string(r_expr)
            range_players.append((name, r))

        result = EquityEngine.calculate_monte_carlo(
            players=range_players,
            board=parsed_board,
            samples=samples,
            seed=seed,
        )
        return result.to_dict()

    @staticmethod
    def start_game_state(
        small_blind: int,
        big_blind: int,
        players: Sequence[tuple[str, int]],
        button_seat: int = 0,
        custom_deck_cards: Sequence[str] | None = None,
    ) -> GameState:
        """Initialize a new Texas Hold'em game state."""
        cfg = GameConfig(small_blind=small_blind, big_blind=big_blind, max_players=len(players))
        deck_cards = [Card.from_str(s) for s in custom_deck_cards] if custom_deck_cards else None
        return GameState.start_hand(
            config=cfg,
            players_data=list(players),
            button_seat_index=button_seat,
            custom_deck_cards=deck_cards,
        )

    @staticmethod
    def apply_action(
        state: GameState,
        player_id: str,
        action_type_str: str,
        amount: int = 0,
    ) -> GameState:
        """Apply an action to an active GameState."""
        try:
            act_type = ActionType(action_type_str.lower())
        except ValueError as err:
            raise ValidationError(
                f"Invalid action type '{action_type_str}'", field="action_type"
            ) from err

        act = Action(player_id=player_id, action_type=act_type, amount=amount)
        return state.apply_action(act)

    @staticmethod
    def canonicalize_scenario(state: GameState) -> dict[str, Any]:
        """Create a canonical scenario representation and return canonical hash and json."""
        scen = PokerScenario.from_game_state(state)
        return {
            "canonical_hash": scen.canonical_hash(),
            "scenario": scen.to_canonical_dict(),
            "canonical_json": scen.to_canonical_json(),
        }
