"""Deterministic scenario model for Texas Hold'em.

Provides a canonical representation for solver integration (Part 3),
decision grading, and replay.
Features:
- Stable SHA-256 canonical hashing (excludes presentation/display metadata).
- Deterministic JSON serialization and deserialization.
- Replay validation to reconstruct active GameState.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from app.domain.exceptions import PokerDomainError
from app.domain.poker.cards import Card, Deck
from app.domain.poker.game_state import Action, ActionType, GameConfig, GameState


@dataclass(frozen=True)
class ScenarioPlayer:
    """Player information stored in a canonical poker scenario."""

    player_id: str
    position: str
    stack: int
    starting_stack: int = 0
    hole_cards: tuple[str, ...] = ()
    range_notation: str = ""

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "player_id": self.player_id,
            "position": self.position,
            "stack": self.stack,
            "starting_stack": self.starting_stack,
            "hole_cards": sorted(self.hole_cards),
            "range": self.range_notation,
        }


@dataclass(frozen=True)
class PokerScenario:
    """Canonical, versioned, hashable representation of a Texas Hold'em state."""

    variant: str
    ruleset_version: str
    small_blind: int
    big_blind: int
    players: tuple[ScenarioPlayer, ...]
    board: tuple[str, ...]
    street: str
    pot: int
    current_actor: str | None
    action_history: tuple[dict[str, Any], ...]
    button_seat_index: int = 0

    @classmethod
    def from_game_state(cls, state: GameState) -> PokerScenario:
        """Construct a canonical scenario from an active GameState."""
        players_data = []
        payouts = state.result.payouts if state.result else {}
        for p in state.players:
            payout = payouts.get(p.player_id, 0)
            initial_stack = p.stack + p.total_bet - payout
            players_data.append(
                ScenarioPlayer(
                    player_id=p.player_id,
                    position=p.position_name,
                    stack=p.stack,
                    starting_stack=initial_stack,
                    hole_cards=tuple(str(c) for c in p.hole_cards),
                )
            )

        total_pot = sum(p.amount for p in state.pots) + sum(p.round_bet for p in state.players)
        curr_actor = None
        if state.current_actor_seat is not None:
            curr_actor = state.players[state.current_actor_seat].player_id

        return cls(
            variant="NLHE",
            ruleset_version="1.0",
            small_blind=state.config.small_blind,
            big_blind=state.config.big_blind,
            players=tuple(players_data),
            board=tuple(str(c) for c in state.community_cards),
            street=state.street.value,
            pot=total_pot,
            current_actor=curr_actor,
            action_history=state.action_history,
            button_seat_index=state.button_seat_index,
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        """Dictionary containing all strategically meaningful fields with deterministic sorting."""
        return {
            "variant": self.variant,
            "ruleset_version": self.ruleset_version,
            "small_blind": self.small_blind,
            "big_blind": self.big_blind,
            "button_seat_index": self.button_seat_index,
            "players": [p.to_canonical_dict() for p in self.players],
            "board": list(self.board),
            "street": self.street,
            "pot": self.pot,
            "current_actor": self.current_actor,
            "action_history": list(self.action_history),
        }

    def to_canonical_json(self) -> str:
        """Strictly formatted, key-sorted, compact JSON string."""
        return json.dumps(self.to_canonical_dict(), sort_keys=True, separators=(",", ":"))

    def canonical_hash(self) -> str:
        """Hex-encoded SHA-256 digest of the canonical scenario JSON."""
        return hashlib.sha256(self.to_canonical_json().encode("utf-8")).hexdigest()

    @classmethod
    def from_canonical_json(cls, json_str: str) -> PokerScenario:
        """Deserialize a scenario from canonical JSON."""
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as err:
            raise PokerDomainError(f"Malformed scenario JSON: {err}") from err

        players = [
            ScenarioPlayer(
                player_id=p["player_id"],
                position=p["position"],
                stack=p["stack"],
                starting_stack=p["starting_stack"] if "starting_stack" in p else p["stack"],
                hole_cards=tuple(p.get("hole_cards", [])),
                range_notation=p.get("range", ""),
            )
            for p in data["players"]
        ]

        if "pot" not in data:
            raise ValueError("Scenario definition must include explicit 'pot'")
        raw_pot = data["pot"]
        pot_val = (
            int(raw_pot)
            if isinstance(raw_pot, int)
            or (isinstance(raw_pot, float) and float(raw_pot).is_integer())
            else float(raw_pot)
        )
        return cls(
            variant=data.get("variant", "NLHE"),
            ruleset_version=data.get("ruleset_version", "1.0"),
            small_blind=data["small_blind"],
            big_blind=data["big_blind"],
            players=tuple(players),
            board=tuple(data.get("board", [])),
            street=data.get("street", "preflop"),
            pot=pot_val,
            current_actor=data.get("current_actor"),
            action_history=tuple(data.get("action_history", [])),
            button_seat_index=data.get("button_seat_index", 0),
        )

    def replay_actions(
        self,
        starting_deck_cards: Sequence[Card] | None = None,
    ) -> GameState:
        """Replay action history starting from preflop to verify state integrity and exact street runouts."""
        config = GameConfig(small_blind=self.small_blind, big_blind=self.big_blind)
        players_data = [
            (p.player_id, p.starting_stack if p.starting_stack > 0 else p.stack)
            for p in self.players
        ]

        deck_to_use: list[Card] | None = None
        if starting_deck_cards is not None:
            deck_to_use = list(starting_deck_cards)
        else:
            # Reconstruct deterministic deck from known player hole cards and board cards
            all_have_hole = all(len(p.hole_cards) == 2 for p in self.players)
            if all_have_hole:
                ordered_cards: list[Card] = []
                dead_set: set[Card] = set()
                # 1. Hole cards in seat deal order
                for p in self.players:
                    c1 = Card.from_str(p.hole_cards[0])
                    c2 = Card.from_str(p.hole_cards[1])
                    ordered_cards.extend([c1, c2])
                    dead_set.add(c1)
                    dead_set.add(c2)
                # 2. Board cards in deal order
                for b_str in self.board:
                    c = Card.from_str(b_str)
                    ordered_cards.append(c)
                    dead_set.add(c)
                # 3. Remaining cards from standard deck
                for c in Deck.generate_standard_deck():
                    if c not in dead_set:
                        ordered_cards.append(c)
                if len(ordered_cards) == 52:
                    deck_to_use = ordered_cards

        state = GameState.start_hand(
            config=config,
            players_data=players_data,
            button_seat_index=self.button_seat_index,
            custom_deck_cards=deck_to_use,
        )

        # Apply actions from history skipping blind postings which start_hand handles
        for rec in self.action_history:
            action_name = rec.get("action", "")
            if action_name in ("post_sb", "post_bb"):
                continue
            act_type = ActionType(action_name)
            act = Action(
                player_id=rec["player_id"],
                action_type=act_type,
                amount=rec.get("amount", 0),
            )
            state = state.apply_action(act)

        return state
