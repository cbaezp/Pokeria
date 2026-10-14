"""No-Limit Texas Hold'em betting state machine, action rules, and transitions.

Pure domain module enforcing:
- 2 to 6 active players (Heads-up and 6-max position rules).
- Action order: preflop vs postflop, heads-up button/blind exceptions.
- Legal action generation with min-bet, min-raise delta, and max No-Limit shove.
- All-in short raises and action reopening rules (Robert's Rules / TDA standard).
- Uncalled bet returns and multi-tiered side pot resolution.
- Chip conservation invariant: TOTAL_INITIAL_CHIPS == TOTAL_FINAL_CHIPS.
- Immutable state transitions returning a new GameState or explicit domain errors.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from app.domain.exceptions import InvalidActionError, PokerDomainError
from app.domain.poker.cards import Card, Deck
from app.domain.poker.evaluator import HandStrength, evaluate_hand
from app.domain.poker.pot import PlayerPotContribution, Pot, PotAward, PotEngine


class Street(StrEnum):
    """The betting rounds of Texas Hold'em."""

    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"


class ActionType(StrEnum):
    """Legal poker action types."""

    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALL_IN = "all_in"


@dataclass(frozen=True, slots=True)
class Action:
    """An action attempted or committed by a player."""

    player_id: str
    action_type: ActionType
    amount: int = 0  # Total chips put in for the round, or raise-to amount


@dataclass(frozen=True, slots=True)
class LegalAction:
    """A permitted action with exact boundaries."""

    action_type: ActionType
    min_amount: int = 0
    max_amount: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_type": self.action_type.value,
            "min_amount": self.min_amount,
            "max_amount": self.max_amount,
        }


@dataclass(frozen=True, slots=True)
class GameConfig:
    """Table configuration for a Texas Hold'em game."""

    small_blind: int
    big_blind: int
    max_players: int = 6

    def __post_init__(self) -> None:
        if self.small_blind <= 0:
            raise PokerDomainError("Small blind must be positive")
        if self.big_blind <= self.small_blind:
            raise PokerDomainError("Big blind must be greater than small blind")
        if not (2 <= self.max_players <= 9):
            raise PokerDomainError("Supported table size is 2 to 9 players")


@dataclass(frozen=True)
class PlayerState:
    """State of an individual player at the table."""

    player_id: str
    seat_index: int
    stack: int
    hole_cards: tuple[Card, ...] = ()
    round_bet: int = 0
    total_bet: int = 0
    is_folded: bool = False
    is_all_in: bool = False
    has_acted_this_round: bool = False
    position_name: str = ""

    def copy_with(self, **kwargs: Any) -> PlayerState:
        fields = {
            "player_id": self.player_id,
            "seat_index": self.seat_index,
            "stack": self.stack,
            "hole_cards": self.hole_cards,
            "round_bet": self.round_bet,
            "total_bet": self.total_bet,
            "is_folded": self.is_folded,
            "is_all_in": self.is_all_in,
            "has_acted_this_round": self.has_acted_this_round,
            "position_name": self.position_name,
        }
        fields.update(kwargs)
        return PlayerState(**fields)

    def to_dict(self, show_cards: bool = True) -> dict[str, Any]:
        return {
            "player_id": self.player_id,
            "seat_index": self.seat_index,
            "position": self.position_name,
            "stack": self.stack,
            "round_bet": self.round_bet,
            "total_bet": self.total_bet,
            "is_folded": self.is_folded,
            "is_all_in": self.is_all_in,
            "has_acted": self.has_acted_this_round,
            "hole_cards": [str(c) for c in self.hole_cards] if show_cards else [],
        }


def assign_position_names(player_count: int) -> list[str]:
    """Return position names in clockwise order starting from the button (index 0 = BT)."""
    if player_count == 2:
        return ["BT", "BB"]  # Heads-up: Button is SB, other player is BB
    if player_count == 3:
        return ["BT", "SB", "BB"]
    if player_count == 4:
        return ["BT", "SB", "BB", "CO"]
    if player_count == 5:
        return ["BT", "SB", "BB", "UTG", "CO"]
    if player_count == 6:
        return ["BT", "SB", "BB", "UTG", "MP", "CO"]
    if player_count == 7:
        return ["BT", "SB", "BB", "UTG", "LJ", "HJ", "CO"]
    if player_count == 8:
        return ["BT", "SB", "BB", "UTG", "UTG+1", "LJ", "HJ", "CO"]
    if player_count == 9:
        return ["BT", "SB", "BB", "UTG", "UTG+1", "UTG+2", "LJ", "HJ", "CO"]
    raise PokerDomainError(f"Unsupported player count for positions: {player_count}")


@dataclass(frozen=True)
class HandResult:
    """The terminal outcome of a completed hand."""

    winners: list[str]
    payouts: dict[str, int]
    awards: list[PotAward]
    hand_strengths: dict[str, HandStrength]
    summary: str


@dataclass(frozen=True)
class GameState:
    """Immutable snapshot of an entire poker table and active hand."""

    config: GameConfig
    street: Street
    players: tuple[PlayerState, ...]
    button_seat_index: int
    community_cards: tuple[Card, ...] = ()
    pots: tuple[Pot, ...] = ()
    current_actor_seat: int | None = None
    min_raise_delta: int = 0
    current_round_high_bet: int = 0
    last_raiser_seat: int | None = None
    can_raise_reopened: dict[str, bool] = field(default_factory=dict)
    faced_bet_at_last_action: dict[str, int] = field(default_factory=dict)
    deck_cards: tuple[Card, ...] = ()
    action_history: tuple[dict[str, Any], ...] = ()
    result: HandResult | None = None
    total_starting_chips: int = 0

    @classmethod
    def start_hand(
        cls,
        config: GameConfig,
        players_data: list[tuple[str, int]],  # (player_id, starting_stack)
        button_seat_index: int = 0,
        deck: Deck | None = None,
        custom_deck_cards: list[Card] | None = None,
        rng: random.Random | None = None,
    ) -> GameState:
        """Initialize a new hand: post blinds, deal 2 hole cards to each player, set initial actor."""
        n = len(players_data)
        if not (2 <= n <= config.max_players):
            raise PokerDomainError(f"Table must have between 2 and {config.max_players} players")

        total_chips = sum(stack for _, stack in players_data)
        if deck is None:
            if custom_deck_cards:
                deck = Deck(cards=custom_deck_cards)
            else:
                deck = Deck()
                deck.shuffle(rng=rng)

        # Assign positions
        pos_names = assign_position_names(n)
        # Seat 0 = Button, seat 1 = SB (or BB in heads-up), etc.
        players_list: list[PlayerState] = []
        for i, (pid, stack) in enumerate(players_data):
            if stack <= 0:
                raise PokerDomainError(f"Player {pid} has non-positive stack {stack}")
            # Deal 2 hole cards
            hole = tuple(deck.deal(2))
            pos_name = pos_names[(i - button_seat_index) % n]
            players_list.append(
                PlayerState(
                    player_id=pid,
                    seat_index=i,
                    stack=stack,
                    hole_cards=hole,
                    position_name=pos_name,
                )
            )

        # Blind postings
        # Heads-up: Button (dealer) posts Small Blind, other player posts Big Blind
        # 3+ players: seat to left of Button posts SB, next posts BB
        if n == 2:
            sb_seat = button_seat_index
            bb_seat = (button_seat_index + 1) % n
            # Preflop first actor in HU is Button (SB)
            first_actor = sb_seat
        else:
            sb_seat = (button_seat_index + 1) % n
            bb_seat = (button_seat_index + 2) % n
            # Preflop first actor in 3+ players is UTG (left of BB)
            first_actor = (bb_seat + 1) % n

        # Post SB
        sb_player = players_list[sb_seat]
        sb_amt = min(sb_player.stack, config.small_blind)
        players_list[sb_seat] = sb_player.copy_with(
            stack=sb_player.stack - sb_amt,
            round_bet=sb_amt,
            total_bet=sb_amt,
            is_all_in=(sb_player.stack == sb_amt),
        )

        # Post BB
        bb_player = players_list[bb_seat]
        bb_amt = min(bb_player.stack, config.big_blind)
        players_list[bb_seat] = bb_player.copy_with(
            stack=bb_player.stack - bb_amt,
            round_bet=bb_amt,
            total_bet=bb_amt,
            is_all_in=(bb_player.stack == bb_amt),
        )

        high_bet = max(sb_amt, bb_amt)
        min_raise_delta = config.big_blind
        last_raiser = bb_seat

        history_records = [
            {
                "street": "preflop",
                "action": "post_sb",
                "player_id": sb_player.player_id,
                "amount": sb_amt,
            },
            {
                "street": "preflop",
                "action": "post_bb",
                "player_id": bb_player.player_id,
                "amount": bb_amt,
            },
        ]

        can_reopen = {p.player_id: True for p in players_list}

        state = cls(
            config=config,
            street=Street.PREFLOP,
            players=tuple(players_list),
            button_seat_index=button_seat_index,
            community_cards=(),
            pots=(),
            current_actor_seat=first_actor,
            min_raise_delta=min_raise_delta,
            current_round_high_bet=high_bet,
            last_raiser_seat=last_raiser,
            can_raise_reopened=can_reopen,
            deck_cards=tuple(deck.cards),
            action_history=tuple(history_records),
            result=None,
            total_starting_chips=total_chips,
        )

        # Advance if first actor has no actions (e.g. all-in)
        if state.players[first_actor].is_all_in:
            return state._advance_turn_or_round()
        return state

    def get_player(self, player_id: str) -> PlayerState | None:
        for p in self.players:
            if p.player_id == player_id:
                return p
        return None

    def get_legal_actions(self) -> list[LegalAction]:
        """Compute all legal actions for the current actor."""
        if self.street == Street.SHOWDOWN or self.current_actor_seat is None:
            return []

        actor = self.players[self.current_actor_seat]
        if actor.is_folded or actor.is_all_in:
            return []

        call_needed = self.current_round_high_bet - actor.round_bet
        legal: list[LegalAction] = []

        # 1. Fold is always permitted when facing a bet
        if call_needed > 0:
            legal.append(LegalAction(ActionType.FOLD))

        # 2. Check is permitted when facing 0 bet to call
        if call_needed == 0:
            legal.append(LegalAction(ActionType.CHECK))

        # 3. Call
        if call_needed > 0:
            if actor.stack <= call_needed:
                # Call puts player all-in
                legal.append(
                    LegalAction(ActionType.CALL, min_amount=actor.stack, max_amount=actor.stack)
                )
            else:
                legal.append(
                    LegalAction(ActionType.CALL, min_amount=call_needed, max_amount=call_needed)
                )

        # 4. Bet / Raise
        # Check if raising rights are permitted (Robert's Rules / TDA cumulative reopening rule):
        can_raise = True
        if actor.has_acted_this_round:
            last_faced = self.faced_bet_at_last_action.get(actor.player_id, 0)
            increase = self.current_round_high_bet - last_faced
            if increase < self.min_raise_delta:
                can_raise = False

        if self.current_round_high_bet == 0:
            # Opening bet on postflop street
            if actor.stack > 0:
                min_bet = min(actor.stack, self.config.big_blind)
                max_bet = actor.stack
                legal.append(LegalAction(ActionType.BET, min_amount=min_bet, max_amount=max_bet))
        else:
            # Raise facing a bet
            if actor.stack > call_needed and can_raise:
                min_raise_to = self.current_round_high_bet + self.min_raise_delta
                # Total amount put in this round for raise-to
                max_raise_to = actor.round_bet + actor.stack
                if max_raise_to >= min_raise_to:
                    legal.append(
                        LegalAction(
                            ActionType.RAISE, min_amount=min_raise_to, max_amount=max_raise_to
                        )
                    )
                else:
                    # Player cannot make a full raise, but can shove all-in as a short raise
                    legal.append(
                        LegalAction(
                            ActionType.ALL_IN, min_amount=max_raise_to, max_amount=max_raise_to
                        )
                    )

        # 5. ALL_IN is explicitly available if stack > 0
        if actor.stack > 0:
            all_in_total = actor.round_bet + actor.stack
            if not any(a.action_type == ActionType.ALL_IN for a in legal):
                legal.append(
                    LegalAction(ActionType.ALL_IN, min_amount=all_in_total, max_amount=all_in_total)
                )

        return legal

    def apply_action(self, action: Action) -> GameState:
        """Apply an action deterministically and return the resulting GameState."""
        if self.street == Street.SHOWDOWN:
            raise InvalidActionError(
                action.player_id, action.action_type.value, "Hand already concluded"
            )
        if self.current_actor_seat is None:
            raise InvalidActionError(action.player_id, action.action_type.value, "No active actor")

        actor = self.players[self.current_actor_seat]
        if actor.player_id != action.player_id:
            raise InvalidActionError(
                action.player_id,
                action.action_type.value,
                f"Not player's turn; current actor is {actor.player_id}",
            )

        legal_actions = self.get_legal_actions()
        legal_types = [la.action_type for la in legal_actions]

        if action.action_type not in legal_types:
            raise InvalidActionError(
                action.player_id,
                action.action_type.value,
                f"Action {action.action_type.value} is not legal. Legal: {[t.value for t in legal_types]}",
            )

        matching_legal = next(la for la in legal_actions if la.action_type == action.action_type)

        call_needed = self.current_round_high_bet - actor.round_bet
        new_players = list(self.players)
        new_history = list(self.action_history)
        new_high_bet = self.current_round_high_bet
        new_min_raise_delta = self.min_raise_delta
        new_last_raiser = self.last_raiser_seat
        new_can_reopen = dict(self.can_raise_reopened)
        new_faced_bet = dict(self.faced_bet_at_last_action)

        if action.action_type == ActionType.FOLD:
            new_players[self.current_actor_seat] = actor.copy_with(
                is_folded=True,
                has_acted_this_round=True,
            )
            new_history.append(
                {
                    "street": self.street.value,
                    "player_id": actor.player_id,
                    "action": "fold",
                    "amount": 0,
                }
            )

            # Check if only one player remains
            active_remaining = [p for p in new_players if not p.is_folded]
            if len(active_remaining) == 1:
                return self._finalize_single_winner(new_players, new_history, active_remaining[0])

        elif action.action_type == ActionType.CHECK:
            if call_needed != 0:
                raise InvalidActionError(
                    action.player_id, "check", f"Cannot check facing {call_needed} bet"
                )
            new_players[self.current_actor_seat] = actor.copy_with(has_acted_this_round=True)
            new_faced_bet[actor.player_id] = self.current_round_high_bet
            new_history.append(
                {
                    "street": self.street.value,
                    "player_id": actor.player_id,
                    "action": "check",
                    "amount": 0,
                }
            )

        elif action.action_type == ActionType.CALL:
            actual_call = min(actor.stack, call_needed)
            is_all_in = actual_call == actor.stack
            new_players[self.current_actor_seat] = actor.copy_with(
                stack=actor.stack - actual_call,
                round_bet=actor.round_bet + actual_call,
                total_bet=actor.total_bet + actual_call,
                is_all_in=is_all_in,
                has_acted_this_round=True,
            )
            new_faced_bet[actor.player_id] = self.current_round_high_bet
            new_history.append(
                {
                    "street": self.street.value,
                    "player_id": actor.player_id,
                    "action": "call",
                    "amount": actual_call,
                }
            )

        elif action.action_type == ActionType.BET:
            amt = action.amount if action.amount > 0 else matching_legal.min_amount
            if not (matching_legal.min_amount <= amt <= matching_legal.max_amount):
                raise InvalidActionError(
                    action.player_id,
                    "bet",
                    f"Bet amount {amt} outside legal bounds [{matching_legal.min_amount}, {matching_legal.max_amount}]",
                )
            is_all_in = amt == actor.stack
            new_players[self.current_actor_seat] = actor.copy_with(
                stack=actor.stack - amt,
                round_bet=amt,
                total_bet=actor.total_bet + amt,
                is_all_in=is_all_in,
                has_acted_this_round=True,
            )
            new_high_bet = amt
            new_min_raise_delta = amt
            new_last_raiser = self.current_actor_seat
            new_faced_bet[actor.player_id] = amt
            # All other active players can raise
            for p in new_players:
                new_can_reopen[p.player_id] = True
            new_history.append(
                {
                    "street": self.street.value,
                    "player_id": actor.player_id,
                    "action": "bet",
                    "amount": amt,
                }
            )

        elif action.action_type in (ActionType.RAISE, ActionType.ALL_IN):
            raise_to = action.amount if action.amount > 0 else matching_legal.min_amount
            all_in_total = actor.round_bet + actor.stack
            if action.action_type == ActionType.ALL_IN and action.amount == 0:
                raise_to = all_in_total

            if action.action_type == ActionType.RAISE:
                if not (matching_legal.min_amount <= raise_to <= matching_legal.max_amount):
                    raise InvalidActionError(
                        action.player_id,
                        "raise",
                        f"Raise-to amount {raise_to} outside legal bounds [{matching_legal.min_amount}, {matching_legal.max_amount}]",
                    )
            elif action.action_type == ActionType.ALL_IN:
                if raise_to != all_in_total:
                    raise InvalidActionError(
                        action.player_id,
                        "all_in",
                        f"All-in requires total wager of {all_in_total}, got {raise_to}",
                    )

            added_chips = raise_to - actor.round_bet
            if added_chips > actor.stack:
                raise InvalidActionError(
                    action.player_id,
                    action.action_type.value,
                    f"Raise requires {added_chips} chips, player only has {actor.stack}",
                )

            is_all_in = added_chips == actor.stack
            raise_delta = raise_to - self.current_round_high_bet
            is_full_raise = raise_delta >= self.min_raise_delta

            new_players[self.current_actor_seat] = actor.copy_with(
                stack=actor.stack - added_chips,
                round_bet=raise_to,
                total_bet=actor.total_bet + added_chips,
                is_all_in=is_all_in,
                has_acted_this_round=True,
            )
            new_faced_bet[actor.player_id] = raise_to

            # Reopening rules (Robert's Rules / TDA):
            # A full raise reopens action for everyone.
            # A short all-in raise does NOT reopen action for players who already faced the current full bet.
            if is_full_raise:
                new_min_raise_delta = raise_delta
                new_last_raiser = self.current_actor_seat
                new_high_bet = raise_to
                for p in new_players:
                    new_can_reopen[p.player_id] = True
            else:
                # Short all-in: raise-to is the new high bet if higher
                if raise_to > new_high_bet:
                    new_high_bet = raise_to
                    # Players who have ALREADY acted on the previous full bet cannot raise again
                    for p in new_players:
                        if p.has_acted_this_round and p.seat_index != self.current_actor_seat:
                            new_can_reopen[p.player_id] = False

            new_history.append(
                {
                    "street": self.street.value,
                    "player_id": actor.player_id,
                    "action": action.action_type.value,
                    "amount": raise_to,
                }
            )

        next_state = GameState(
            config=self.config,
            street=self.street,
            players=tuple(new_players),
            button_seat_index=self.button_seat_index,
            community_cards=self.community_cards,
            pots=self.pots,
            current_actor_seat=self.current_actor_seat,
            min_raise_delta=new_min_raise_delta,
            current_round_high_bet=new_high_bet,
            last_raiser_seat=new_last_raiser,
            can_raise_reopened=new_can_reopen,
            faced_bet_at_last_action=new_faced_bet,
            deck_cards=self.deck_cards,
            action_history=tuple(new_history),
            result=None,
            total_starting_chips=self.total_starting_chips,
        )

        return next_state._advance_turn_or_round()

    def _advance_turn_or_round(self) -> GameState:
        """Advance to next actor or close betting round and advance street."""
        n = len(self.players)
        active_players = [p for p in self.players if not p.is_folded]

        # 1. Early hand conclusion if only 1 player remains
        if len(active_players) == 1:
            return self._finalize_single_winner(
                list(self.players), list(self.action_history), active_players[0]
            )

        # 2. Check if betting round is complete
        # A round is complete if every non-folded, non-all-in player has acted and matched the high bet
        non_all_in_active = [p for p in active_players if not p.is_all_in]

        round_complete = True
        if len(non_all_in_active) > 1:
            for p in non_all_in_active:
                if not p.has_acted_this_round or p.round_bet < self.current_round_high_bet:
                    round_complete = False
                    break
        elif len(non_all_in_active) == 1:
            # 1 player has chips, everyone else is all-in or folded
            single = non_all_in_active[0]
            if not single.has_acted_this_round or single.round_bet < self.current_round_high_bet:
                round_complete = False

        if not round_complete:
            # Find next active player who needs to act
            curr = self.current_actor_seat if self.current_actor_seat is not None else 0
            for step in range(1, n + 1):
                nxt = (curr + step) % n
                p = self.players[nxt]
                if not p.is_folded and not p.is_all_in:
                    return self._copy_with_new_actor(nxt)

        # Betting round closed! Advance to next street or showdown
        return self._advance_street()

    def _copy_with_new_actor(self, actor_seat: int) -> GameState:
        return GameState(
            config=self.config,
            street=self.street,
            players=self.players,
            button_seat_index=self.button_seat_index,
            community_cards=self.community_cards,
            pots=self.pots,
            current_actor_seat=actor_seat,
            min_raise_delta=self.min_raise_delta,
            current_round_high_bet=self.current_round_high_bet,
            last_raiser_seat=self.last_raiser_seat,
            can_raise_reopened=self.can_raise_reopened,
            faced_bet_at_last_action=self.faced_bet_at_last_action,
            deck_cards=self.deck_cards,
            action_history=self.action_history,
            result=self.result,
            total_starting_chips=self.total_starting_chips,
        )

    def _advance_street(self) -> GameState:
        """Close current round, consolidate pots, deal board cards, and prepare next street."""
        # Reset round bets for players and consolidate into pot engine
        contribs = [
            PlayerPotContribution(
                player_id=p.player_id,
                total_contributed=p.total_bet,
                is_folded=p.is_folded,
                is_all_in=p.is_all_in,
                seat_index=p.seat_index,
            )
            for p in self.players
        ]
        pots, refunds = PotEngine.calculate_pots_and_refunds(contribs)

        # Apply refunds if any uncalled wagers were returned
        updated_players = []
        for p in self.players:
            refund = refunds.get(p.player_id, 0)
            updated_players.append(
                p.copy_with(
                    stack=p.stack + refund,
                    round_bet=0,
                    has_acted_this_round=False,
                )
            )

        active_not_all_in = [p for p in updated_players if not p.is_folded and not p.is_all_in]
        deck = Deck(cards=list(self.deck_cards))
        board = list(self.community_cards)

        next_street = self.street
        if self.street == Street.PREFLOP:
            next_street = Street.FLOP
            board.extend(deck.deal(3))
        elif self.street == Street.FLOP:
            next_street = Street.TURN
            board.extend(deck.deal(1))
        elif self.street == Street.TURN:
            next_street = Street.RIVER
            board.extend(deck.deal(1))
        elif self.street == Street.RIVER:
            # Hand reaches showdown
            return self._finalize_showdown(updated_players, pots, board, list(self.action_history))

        # If 0 or 1 player has chips remaining, deal all remaining board cards to river and showdown!
        if len(active_not_all_in) <= 1:
            while len(board) < 5:
                board.extend(deck.deal(1))
            return self._finalize_showdown(updated_players, pots, board, list(self.action_history))

        # Determine first actor on next street (first active player to left of button)
        n = len(updated_players)
        first_actor = None
        for step in range(1, n + 1):
            cand = (self.button_seat_index + step) % n
            p = updated_players[cand]
            if not p.is_folded and not p.is_all_in:
                first_actor = cand
                break

        can_reopen = {p.player_id: True for p in updated_players}

        return GameState(
            config=self.config,
            street=next_street,
            players=tuple(updated_players),
            button_seat_index=self.button_seat_index,
            community_cards=tuple(board),
            pots=tuple(pots),
            current_actor_seat=first_actor,
            min_raise_delta=self.config.big_blind,
            current_round_high_bet=0,
            last_raiser_seat=None,
            can_raise_reopened=can_reopen,
            faced_bet_at_last_action={},
            deck_cards=tuple(deck.cards),
            action_history=self.action_history,
            result=None,
            total_starting_chips=self.total_starting_chips,
        )

    def _finalize_single_winner(
        self,
        players: list[PlayerState],
        history: list[dict[str, Any]],
        winner: PlayerState,
    ) -> GameState:
        """Finalize hand when all opponents fold."""
        contribs = [
            PlayerPotContribution(
                player_id=p.player_id,
                total_contributed=p.total_bet,
                is_folded=p.is_folded,
                is_all_in=p.is_all_in,
                seat_index=p.seat_index,
            )
            for p in players
        ]
        pots, refunds = PotEngine.calculate_pots_and_refunds(contribs)

        total_pot_won = sum(pot.amount for pot in pots)
        final_players: list[PlayerState] = []
        payouts: dict[str, int] = {p.player_id: 0 for p in players}

        for p in players:
            refund = refunds.get(p.player_id, 0)
            win_chip = total_pot_won if p.player_id == winner.player_id else 0
            final_stack = p.stack + refund + win_chip
            payouts[p.player_id] = win_chip + refund
            final_players.append(p.copy_with(stack=final_stack, round_bet=0))

        award = PotAward(
            player_id=winner.player_id,
            amount=total_pot_won,
            pot_index=0,
            description=f"Won uncontested pot of {total_pot_won} chips (opponents folded)",
        )

        result = HandResult(
            winners=[winner.player_id],
            payouts=payouts,
            awards=[award],
            hand_strengths={},
            summary=f"Player {winner.player_id} won {total_pot_won} chips uncontested.",
        )

        # Invariant check
        final_total = sum(p.stack for p in final_players)
        assert (
            final_total == self.total_starting_chips
        ), f"Chip conservation error: started with {self.total_starting_chips}, ended with {final_total}"

        return GameState(
            config=self.config,
            street=Street.SHOWDOWN,
            players=tuple(final_players),
            button_seat_index=self.button_seat_index,
            community_cards=self.community_cards,
            pots=tuple(pots),
            current_actor_seat=None,
            min_raise_delta=0,
            current_round_high_bet=0,
            last_raiser_seat=None,
            can_raise_reopened={},
            faced_bet_at_last_action={},
            deck_cards=self.deck_cards,
            action_history=tuple(history),
            result=result,
            total_starting_chips=self.total_starting_chips,
        )

    def _finalize_showdown(
        self,
        players: list[PlayerState],
        pots: list[Pot],
        board: list[Card],
        history: list[dict[str, Any]],
    ) -> GameState:
        """Evaluate hands, settle all pots, and award chips at showdown."""
        n = len(players)
        # Order clockwise starting left of button: (button + 1) % n, ..., button
        seat_order = [players[(self.button_seat_index + 1 + i) % n].player_id for i in range(n)]

        player_cards = {p.player_id: p.hole_cards for p in players if not p.is_folded}
        awards = PotEngine.settle_showdown(
            pots=pots,
            player_cards=player_cards,
            board_cards=board,
            seat_order=seat_order,
        )

        payouts: dict[str, int] = {p.player_id: 0 for p in players}
        for award in awards:
            payouts[award.player_id] += award.amount

        final_players: list[PlayerState] = []
        for p in players:
            won = payouts.get(p.player_id, 0)
            final_players.append(p.copy_with(stack=p.stack + won, round_bet=0))

        # Evaluate final hand strengths for active players
        hand_strengths = {
            pid: evaluate_hand(list(hole) + board) for pid, hole in player_cards.items()
        }

        winners = sorted({a.player_id for a in awards})
        summary_parts = [f"{a.player_id} won {a.amount} chips (pot #{a.pot_index})" for a in awards]

        result = HandResult(
            winners=winners,
            payouts=payouts,
            awards=awards,
            hand_strengths=hand_strengths,
            summary="; ".join(summary_parts) if summary_parts else "Hand concluded.",
        )

        final_total = sum(p.stack for p in final_players)
        assert (
            final_total == self.total_starting_chips
        ), f"Chip conservation error: started with {self.total_starting_chips}, ended with {final_total}"

        return GameState(
            config=self.config,
            street=Street.SHOWDOWN,
            players=tuple(final_players),
            button_seat_index=self.button_seat_index,
            community_cards=tuple(board),
            pots=tuple(pots),
            current_actor_seat=None,
            min_raise_delta=0,
            current_round_high_bet=0,
            last_raiser_seat=None,
            can_raise_reopened={},
            faced_bet_at_last_action={},
            deck_cards=self.deck_cards,
            action_history=tuple(history),
            result=result,
            total_starting_chips=self.total_starting_chips,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize complete game state to dictionary."""
        return {
            "street": self.street.value,
            "button_seat_index": self.button_seat_index,
            "community_cards": [str(c) for c in self.community_cards],
            "pots": [p.to_dict() for p in self.pots],
            "current_actor_seat": self.current_actor_seat,
            "current_high_bet": self.current_round_high_bet,
            "min_raise_delta": self.min_raise_delta,
            "players": [p.to_dict() for p in self.players],
            "legal_actions": [la.to_dict() for la in self.get_legal_actions()],
            "history_count": len(self.action_history),
            "is_terminal": self.street == Street.SHOWDOWN,
            "result": {
                "winners": self.result.winners,
                "payouts": self.result.payouts,
                "summary": self.result.summary,
            }
            if self.result
            else None,
        }
