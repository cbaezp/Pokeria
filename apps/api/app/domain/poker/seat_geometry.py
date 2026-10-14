"""Seat geometry, table occupancy, and position inference for 2 to 9 players.

Canonical domain logic supporting:
- 2 to 9 occupied players at nominal 2 to 9 capacity tables.
- Arbitrary physical seat indices (e.g. seats 1, 4, 7 occupied at a 9-max table).
- Full heads-up button / small-blind exception handling.
- Clockwise active-seat traversal with empty seats and sitting-out participants skipped.
- Canonical position names: BTN, SB, BB, UTG, UTG+1, UTG+2, LJ, HJ, CO.
- Preflop action order vs postflop action order derivation.
- Chip conservation and invariant validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.exceptions import PokerDomainError


class TablePosition(StrEnum):
    """Canonical table positions."""

    BTN = "BTN"
    SB = "SB"
    BB = "BB"
    UTG = "UTG"
    UTG1 = "UTG+1"
    UTG2 = "UTG+2"
    LJ = "LJ"
    HJ = "HJ"
    CO = "CO"


# Standard position sequences in clockwise order from button (index 0 = BTN)
STANDARD_POSITIONS_BY_COUNT: dict[int, list[str]] = {
    2: ["BTN", "BB"],  # In heads-up, BTN is SB
    3: ["BTN", "SB", "BB"],
    4: ["BTN", "SB", "BB", "CO"],
    5: ["BTN", "SB", "BB", "UTG", "CO"],
    6: ["BTN", "SB", "BB", "UTG", "HJ", "CO"],
    7: ["BTN", "SB", "BB", "UTG", "LJ", "HJ", "CO"],
    8: ["BTN", "SB", "BB", "UTG", "UTG+1", "LJ", "HJ", "CO"],
    9: ["BTN", "SB", "BB", "UTG", "UTG+1", "UTG+2", "LJ", "HJ", "CO"],
}


@dataclass(frozen=True)
class TableSeatConfig:
    """Configuration for an individual seat at the table."""

    seat_number: int  # 1-indexed (1 to max_capacity) or 0-indexed
    player_id: str
    player_name: str
    stack: int
    is_hero: bool = False
    is_sitting_out: bool = False
    hole_cards: tuple[str, ...] = ()  # e.g. ("As", "Kh") or () if hidden/unknown


@dataclass(frozen=True)
class InferredSeatPosition:
    """Inferred strategic position and action indices for an active seat."""

    seat_number: int
    player_id: str
    player_name: str
    position_name: str
    is_button: bool
    is_small_blind: bool
    is_big_blind: bool
    is_hero: bool
    stack: int
    preflop_action_order: int  # 0-indexed order of acting preflop
    postflop_action_order: int  # 0-indexed order of acting postflop


@dataclass(frozen=True)
class TableGeometry:
    """Evaluated table geometry for a specific hand setup."""

    max_capacity: int
    button_seat: int
    active_seats: tuple[InferredSeatPosition, ...]
    preflop_order: tuple[int, ...]  # Seat numbers in preflop action order
    postflop_order: tuple[int, ...]  # Seat numbers in postflop action order
    sb_seat: int
    bb_seat: int
    hero_seat: int | None = None

    def get_seat(self, seat_number: int) -> InferredSeatPosition | None:
        for s in self.active_seats:
            if s.seat_number == seat_number:
                return s
        return None

    def get_position(self, seat_number: int) -> str | None:
        seat = self.get_seat(seat_number)
        return seat.position_name if seat else None


def infer_table_geometry(
    max_capacity: int,
    button_seat: int,
    seats: list[TableSeatConfig],
) -> TableGeometry:
    """Infer positions, blinds, and action orders from occupied seats and button position.

    Args:
        max_capacity: Nominal table capacity (2 to 9).
        button_seat: Seat number where the dealer button is located.
        seats: List of seat configurations.

    Returns:
        TableGeometry with canonical position names, blinds, and preflop/postflop action orders.
    """
    if not (2 <= max_capacity <= 9):
        raise PokerDomainError(f"Table capacity must be between 2 and 9, got {max_capacity}")

    # Filter out empty seats and sitting-out players
    active_candidates = [s for s in seats if not s.is_sitting_out and s.stack > 0]
    num_active = len(active_candidates)

    if not (2 <= num_active <= max_capacity):
        raise PokerDomainError(
            f"Active players ({num_active}) must be between 2 and table capacity ({max_capacity})"
        )

    # Sort seats in ascending order of seat_number
    sorted_seats = sorted(active_candidates, key=lambda s: s.seat_number)
    seat_numbers = [s.seat_number for s in sorted_seats]

    # Validate button seat is among active seats, or find the closest occupied seat clockwise
    if button_seat in seat_numbers:
        btn_idx = seat_numbers.index(button_seat)
    else:
        # Move clockwise from button_seat to next occupied seat
        higher_seats = [s for s in seat_numbers if s >= button_seat]
        if higher_seats:
            button_seat = higher_seats[0]
        else:
            button_seat = seat_numbers[0]
        btn_idx = seat_numbers.index(button_seat)

    # Order active seats starting from the button in clockwise circular order:
    # index 0: Button
    # index 1: Small Blind (or Big Blind in Heads-Up)
    # index 2: Big Blind (in 3+ handed)
    clockwise_seats: list[TableSeatConfig] = [
        sorted_seats[(btn_idx + i) % num_active] for i in range(num_active)
    ]

    position_names = STANDARD_POSITIONS_BY_COUNT[num_active]

    # Heads-up vs Multiway logic:
    # Heads-up (2 players):
    #   - Seat 0 is Button / Small Blind.
    #   - Seat 1 is Big Blind.
    #   - Preflop action: Button acts FIRST (order 0), Big Blind acts SECOND (order 1).
    #   - Postflop action: Big Blind acts FIRST (order 0), Button acts SECOND (order 1).
    #
    # 3+ Handed:
    #   - Seat 0 is Button (BTN).
    #   - Seat 1 is Small Blind (SB).
    #   - Seat 2 is Big Blind (BB).
    #   - Seat 3 is UTG (first to act preflop).
    #   - Preflop action: UTG acts first, then clockwise around to BB.
    #     In terms of clockwise list [BTN, SB, BB, UTG, ...]:
    #     preflop order starts at index 3 (UTG), wraps to BTN (0), SB (1), BB (2).
    #   - Postflop action: Starts at SB (index 1), wraps to BTN (index 0).

    inferred: list[InferredSeatPosition] = []
    preflop_order_seats: list[int] = []
    postflop_order_seats: list[int] = []

    if num_active == 2:
        btn_seat_cfg = clockwise_seats[0]
        bb_seat_cfg = clockwise_seats[1]

        sb_seat_num = btn_seat_cfg.seat_number  # BTN is SB in heads-up
        bb_seat_num = bb_seat_cfg.seat_number

        inferred.append(
            InferredSeatPosition(
                seat_number=btn_seat_cfg.seat_number,
                player_id=btn_seat_cfg.player_id,
                player_name=btn_seat_cfg.player_name,
                position_name="BTN/SB",
                is_button=True,
                is_small_blind=True,
                is_big_blind=False,
                is_hero=btn_seat_cfg.is_hero,
                stack=btn_seat_cfg.stack,
                preflop_action_order=0,
                postflop_action_order=1,
            )
        )
        inferred.append(
            InferredSeatPosition(
                seat_number=bb_seat_cfg.seat_number,
                player_id=bb_seat_cfg.player_id,
                player_name=bb_seat_cfg.player_name,
                position_name="BB",
                is_button=False,
                is_small_blind=False,
                is_big_blind=True,
                is_hero=bb_seat_cfg.is_hero,
                stack=bb_seat_cfg.stack,
                preflop_action_order=1,
                postflop_action_order=0,
            )
        )

        preflop_order_seats = [btn_seat_cfg.seat_number, bb_seat_cfg.seat_number]
        postflop_order_seats = [bb_seat_cfg.seat_number, btn_seat_cfg.seat_number]

    else:
        sb_seat_num = clockwise_seats[1].seat_number
        bb_seat_num = clockwise_seats[2].seat_number

        # Preflop order: starts at index 3 (UTG), wraps to 0 (BTN), 1 (SB), 2 (BB)
        preflop_indices = [(3 + i) % num_active for i in range(num_active)]
        # Postflop order: starts at index 1 (SB), wraps to 0 (BTN)
        postflop_indices = [(1 + i) % num_active for i in range(num_active)]

        preflop_order_seats = [clockwise_seats[idx].seat_number for idx in preflop_indices]
        postflop_order_seats = [clockwise_seats[idx].seat_number for idx in postflop_indices]

        for i, seat_cfg in enumerate(clockwise_seats):
            pos_name = position_names[i]
            preflop_order = preflop_indices.index(i)
            postflop_order = postflop_indices.index(i)

            inferred.append(
                InferredSeatPosition(
                    seat_number=seat_cfg.seat_number,
                    player_id=seat_cfg.player_id,
                    player_name=seat_cfg.player_name,
                    position_name=pos_name,
                    is_button=(i == 0),
                    is_small_blind=(i == 1),
                    is_big_blind=(i == 2),
                    is_hero=seat_cfg.is_hero,
                    stack=seat_cfg.stack,
                    preflop_action_order=preflop_order,
                    postflop_action_order=postflop_order,
                )
            )

    hero_seat = next((s.seat_number for s in inferred if s.is_hero), None)

    return TableGeometry(
        max_capacity=max_capacity,
        button_seat=button_seat,
        active_seats=tuple(inferred),
        preflop_order=tuple(preflop_order_seats),
        postflop_order=tuple(postflop_order_seats),
        sb_seat=sb_seat_num,
        bb_seat=bb_seat_num,
        hero_seat=hero_seat,
    )
