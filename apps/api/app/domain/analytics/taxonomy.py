"""Versioned, deterministic poker skill taxonomy for Poker Lab.

Defines the taxonomic dimensions describing poker scenarios and decisions:
- Street
- Decision Type
- Position and Relative Position (IP/OOP)
- Hand Category & Draw/Blocker Dynamics
- Board Texture
- Strategic Concepts (strictly derived from objective metadata or range definitions)

Taxonomy versioning guarantees historical grading and classification consistency.
Zero machine learning, zero speculative psychological attributes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from app.domain.poker.cards import Card
from app.domain.poker.evaluator import HandRank, evaluate_hand

TAXONOMY_VERSION: str = "v1.0.0"


class Street(StrEnum):
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"


class DecisionType(StrEnum):
    OPEN_RAISE = "open_raise"
    FACING_OPEN = "facing_open"
    FACING_3BET = "facing_3bet"
    CONTINUATION_BET = "continuation_bet"
    FACING_CBET = "facing_cbet"
    BARREL = "barrel"
    FACING_BARREL = "facing_barrel"
    VALUE_BET = "value_bet"
    BLUFF = "bluff"
    BLUFF_CATCH = "bluff_catch"
    CHECK = "check"
    CALL = "call"
    FOLD = "fold"
    RAISE = "raise"
    ALL_IN_DECISION = "all_in_decision"


class Position(StrEnum):
    UTG = "UTG"
    MP = "MP"
    HJ = "HJ"
    CO = "CO"
    BTN = "BTN"
    SB = "SB"
    BB = "BB"


class RelativePosition(StrEnum):
    IN_POSITION = "in_position"
    OUT_OF_POSITION = "out_of_position"


class HandCategory(StrEnum):
    HIGH_CARD = "high_card"
    ONE_PAIR = "one_pair"
    TWO_PAIR = "two_pair"
    THREE_OF_A_KIND = "three_of_a_kind"
    STRAIGHT = "straight"
    FLUSH = "flush"
    FULL_HOUSE = "full_house"
    FOUR_OF_A_KIND = "four_of_a_kind"
    STRAIGHT_FLUSH = "straight_flush"

    # Relevant objective draws / blockers
    NUT_FLUSH_DRAW = "nut_flush_draw"
    FLUSH_DRAW = "flush_draw"
    OPEN_ENDED_STRAIGHT_DRAW = "open_ended_straight_draw"
    GUTSHOT = "gutshot"
    OVERCARDS = "overcards"
    ACE_BLOCKER = "ace_blocker"
    KING_BLOCKER = "king_blocker"


class BoardTexture(StrEnum):
    PAIRED = "paired"
    UNPAIRED = "unpaired"
    MONOTONE = "monotone"
    TWO_TONE = "two_tone"
    RAINBOW = "rainbow"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    HIGH_CARD = "high_card"
    LOW_CARD = "low_card"
    FLUSH_COMPLETING = "flush_completing"
    STRAIGHT_COMPLETING = "straight_completing"


class StrategicConcept(StrEnum):
    RANGE_ADVANTAGE = "range_advantage"
    NUT_ADVANTAGE = "nut_advantage"
    BLOCKER_EFFECTS = "blocker_effects"
    POT_ODDS = "pot_odds"
    POLARIZED_SIZING = "polarized_sizing"
    BLUFF_CATCHING = "bluff_catching"
    THIN_VALUE = "thin_value"
    PROTECTION = "protection"
    EQUITY_REALIZATION = "equity_realization"


@dataclass(frozen=True, slots=True)
class ScenarioClassification:
    """Immutable classification tags assigned to a scenario under a specific taxonomy version."""

    taxonomy_version: str
    street: Street
    decision_types: tuple[DecisionType, ...]
    position: Position | None
    relative_position: RelativePosition | None
    hand_categories: tuple[HandCategory, ...]
    board_textures: tuple[BoardTexture, ...]
    strategic_concepts: tuple[StrategicConcept, ...]
    tags: tuple[str, ...] = field(default_factory=tuple)

    @property
    def primary_skill_tag(self) -> str:
        """Single representative tag for summary aggregations."""
        if self.strategic_concepts:
            return self.strategic_concepts[0].value
        if self.decision_types:
            return self.decision_types[0].value
        return self.street.value


def parse_cards_safely(card_str: str) -> list[Card]:
    """Parse space-separated or concatenated card tokens into Card value objects."""
    if not card_str:
        return []
    clean = card_str.strip()
    if not clean:
        return []

    # Handle space-separated tokens e.g. "Ah Kd 2c"
    if " " in clean:
        tokens = [t for t in clean.split(" ") if t]
    else:
        # Concatenated pairs e.g. "AhKd" or "AhKd2c"
        tokens = [clean[i : i + 2] for i in range(0, len(clean), 2) if len(clean[i : i + 2]) == 2]

    cards: list[Card] = []
    for t in tokens:
        try:
            cards.append(Card.from_str(t))
        except Exception:
            continue
    return cards


def classify_board_texture(board_cards: list[Card]) -> list[BoardTexture]:
    """Deterministically classify board texture dimensions from a list of board cards."""
    if not board_cards:
        return []

    textures: list[BoardTexture] = []
    ranks = [c.rank.value for c in board_cards]
    suits = [c.suit.value for c in board_cards]

    # Paired vs Unpaired
    if len(set(ranks)) < len(ranks):
        textures.append(BoardTexture.PAIRED)
    else:
        textures.append(BoardTexture.UNPAIRED)

    # Suit composition
    suit_counts = {s: suits.count(s) for s in set(suits)}
    max_suit = max(suit_counts.values()) if suit_counts else 0

    if max_suit >= 3:
        textures.append(BoardTexture.MONOTONE)
        textures.append(BoardTexture.FLUSH_COMPLETING)
    elif max_suit == 2:
        textures.append(BoardTexture.TWO_TONE)
    else:
        textures.append(BoardTexture.RAINBOW)

    # High vs Low card
    has_high = any(r >= 11 for r in ranks)  # Jack, Queen, King, Ace
    all_low = all(r <= 9 for r in ranks)
    if has_high:
        textures.append(BoardTexture.HIGH_CARD)
    elif all_low:
        textures.append(BoardTexture.LOW_CARD)

    # Connectedness
    sorted_unique_ranks = sorted(set(ranks))
    has_close_ranks = False
    for i in range(len(sorted_unique_ranks) - 1):
        if sorted_unique_ranks[i + 1] - sorted_unique_ranks[i] == 1:
            has_close_ranks = True
            break
    if has_close_ranks and len(sorted_unique_ranks) >= 2:
        textures.append(BoardTexture.CONNECTED)
    else:
        textures.append(BoardTexture.DISCONNECTED)

    # Straight-completing (if 3+ ranks span <= 4 ranks)
    if len(sorted_unique_ranks) >= 3:
        for i in range(len(sorted_unique_ranks) - 2):
            if sorted_unique_ranks[i + 2] - sorted_unique_ranks[i] <= 4:
                textures.append(BoardTexture.STRAIGHT_COMPLETING)
                break

    return textures


def classify_hero_hand(hero_cards: list[Card], board_cards: list[Card]) -> list[HandCategory]:
    """Deterministically classify hero hand strength and draw/blocker properties."""
    categories: list[HandCategory] = []
    if len(hero_cards) < 2:
        return categories

    # Blocker effects
    hero_ranks = [c.rank.value for c in hero_cards]
    if 14 in hero_ranks:  # Ace
        categories.append(HandCategory.ACE_BLOCKER)
    if 13 in hero_ranks:  # King
        categories.append(HandCategory.KING_BLOCKER)

    # Hand evaluation
    total_cards = hero_cards + board_cards
    if len(total_cards) >= 5:
        try:
            strength = evaluate_hand(total_cards[:7])
            rank_mapping = {
                HandRank.HIGH_CARD: HandCategory.HIGH_CARD,
                HandRank.ONE_PAIR: HandCategory.ONE_PAIR,
                HandRank.TWO_PAIR: HandCategory.TWO_PAIR,
                HandRank.THREE_OF_A_KIND: HandCategory.THREE_OF_A_KIND,
                HandRank.STRAIGHT: HandCategory.STRAIGHT,
                HandRank.FLUSH: HandCategory.FLUSH,
                HandRank.FULL_HOUSE: HandCategory.FULL_HOUSE,
                HandRank.FOUR_OF_A_KIND: HandCategory.FOUR_OF_A_KIND,
                HandRank.STRAIGHT_FLUSH: HandCategory.STRAIGHT_FLUSH,
            }
            if strength.hand_rank in rank_mapping:
                categories.append(rank_mapping[strength.hand_rank])
        except Exception:
            pass
    elif len(hero_cards) == 2 and not board_cards:
        # Preflop hole cards
        if hero_ranks[0] == hero_ranks[1]:
            categories.append(HandCategory.ONE_PAIR)
        else:
            categories.append(HandCategory.HIGH_CARD)

    # Flush draws (if 4 cards of same suit among hero + board)
    suits = [c.suit for c in total_cards]
    suit_counts = {s: suits.count(s) for s in set(suits)}
    for s, count in suit_counts.items():
        if count == 4:
            hero_suits = [c.suit for c in hero_cards]
            if s in hero_suits:
                # Check nut flush draw (hero holds Ace of that suit)
                if any(c.suit == s and c.rank.value == 14 for c in hero_cards):
                    categories.append(HandCategory.NUT_FLUSH_DRAW)
                else:
                    categories.append(HandCategory.FLUSH_DRAW)

    return categories


def classify_scenario(
    board: str = "",
    combo: str = "",
    hero_position: str = "BTN",
    pot: float | None = None,
    effective_stack: float | None = None,
    action_history: list[dict[str, Any]] | None = None,
    legal_actions: list[dict[str, Any]] | None = None,
    scenario_family: str = "",
    villain_position: str = "",
) -> ScenarioClassification:
    """Deterministically map scenario inputs into a versioned ScenarioClassification.

    Rule-based, verifiable, and strictly derived from objective situation properties.
    """
    board_cards = parse_cards_safely(board)
    hero_cards = parse_cards_safely(combo)

    # 1. Street
    num_board = len(board_cards)
    if num_board == 0:
        street = Street.PREFLOP
    elif num_board == 3:
        street = Street.FLOP
    elif num_board == 4:
        street = Street.TURN
    else:
        street = Street.RIVER

    # 2. Position
    pos_clean = hero_position.upper().strip()
    position = None
    for p in Position:
        if p.value == pos_clean:
            position = p
            break

    # Relative Position (IP vs OOP)
    relative_pos = None
    fam_lower = scenario_family.lower()
    if "oop" in fam_lower:
        relative_pos = RelativePosition.OUT_OF_POSITION
    elif "ip" in fam_lower:
        relative_pos = RelativePosition.IN_POSITION
    elif villain_position:
        # Standard postflop order: SB, BB, UTG, MP, HJ, CO, BTN
        postflop_order = ["SB", "BB", "UTG", "MP", "HJ", "CO", "BTN"]
        v_clean = villain_position.upper().strip()
        if pos_clean in postflop_order and v_clean in postflop_order:
            hero_idx = postflop_order.index(pos_clean)
            v_idx = postflop_order.index(v_clean)
            relative_pos = (
                RelativePosition.IN_POSITION
                if hero_idx > v_idx
                else RelativePosition.OUT_OF_POSITION
            )
    if relative_pos is None:
        if position in (Position.BTN, Position.CO, Position.HJ, Position.MP):
            relative_pos = RelativePosition.IN_POSITION
        elif position in (Position.SB, Position.BB):
            relative_pos = RelativePosition.OUT_OF_POSITION

    # 3. Decision Types
    decision_types: list[DecisionType] = []
    actions_clean = [
        (a.get("kind") or a.get("action") or "").upper() for a in (legal_actions or [])
    ]
    if "ALLIN" in actions_clean or "ALL_IN" in actions_clean:
        decision_types.append(DecisionType.ALL_IN_DECISION)
    if "CHECK" in actions_clean:
        decision_types.append(DecisionType.CHECK)
    if "CALL" in actions_clean:
        decision_types.append(DecisionType.CALL)
    if "FOLD" in actions_clean:
        decision_types.append(DecisionType.FOLD)
    if "BET" in actions_clean:
        if street == Street.FLOP and "cbet" in fam_lower:
            decision_types.append(DecisionType.CONTINUATION_BET)
        elif street in (Street.TURN, Street.RIVER) and "barrel" in fam_lower:
            decision_types.append(DecisionType.BARREL)
        elif "value" in fam_lower:
            decision_types.append(DecisionType.VALUE_BET)
        elif "bluff" in fam_lower and "catch" not in fam_lower:
            decision_types.append(DecisionType.BLUFF)
    if "RAISE" in actions_clean:
        decision_types.append(DecisionType.RAISE)

    if street == Street.PREFLOP:
        if "open" in fam_lower and "facing" not in fam_lower:
            decision_types.append(DecisionType.OPEN_RAISE)
        elif "facing_open" in fam_lower or "vs_open" in fam_lower:
            decision_types.append(DecisionType.FACING_OPEN)
        elif "facing_3bet" in fam_lower or "vs_3bet" in fam_lower:
            decision_types.append(DecisionType.FACING_3BET)

    if "bluff_catch" in fam_lower or "bluff-catch" in fam_lower:
        decision_types.append(DecisionType.BLUFF_CATCH)

    # 4. Board Texture
    board_textures = classify_board_texture(board_cards)

    # 5. Hand Categories
    hand_categories = classify_hero_hand(hero_cards, board_cards)

    # 6. Strategic Concepts (strictly rule-based from verifiable scenario definitions)
    strategic_concepts: list[StrategicConcept] = []
    if (
        "bluff_catch" in fam_lower
        or "bluff-catch" in fam_lower
        or DecisionType.BLUFF_CATCH in decision_types
    ):
        strategic_concepts.append(StrategicConcept.BLUFF_CATCHING)
    if "pot_odds" in fam_lower:
        strategic_concepts.append(StrategicConcept.POT_ODDS)
    if "polarized" in fam_lower:
        strategic_concepts.append(StrategicConcept.POLARIZED_SIZING)
    if "thin_value" in fam_lower:
        strategic_concepts.append(StrategicConcept.THIN_VALUE)
    if "range_advantage" in fam_lower:
        strategic_concepts.append(StrategicConcept.RANGE_ADVANTAGE)
    if "nut_advantage" in fam_lower:
        strategic_concepts.append(StrategicConcept.NUT_ADVANTAGE)
    if "protection" in fam_lower:
        strategic_concepts.append(StrategicConcept.PROTECTION)
    if "equity_realization" in fam_lower:
        strategic_concepts.append(StrategicConcept.EQUITY_REALIZATION)
    if HandCategory.ACE_BLOCKER in hand_categories or HandCategory.KING_BLOCKER in hand_categories:
        strategic_concepts.append(StrategicConcept.BLOCKER_EFFECTS)

    # Assemble composite string tags for fast SQL querying and UI pills
    all_tags: list[str] = [street.value]
    if position:
        all_tags.append(f"pos_{position.value.lower()}")
    if relative_pos:
        all_tags.append(relative_pos.value)
    for dt in decision_types:
        all_tags.append(dt.value)
    for sc in strategic_concepts:
        all_tags.append(sc.value)
    for bt in board_textures:
        all_tags.append(f"board_{bt.value}")
    for hc in hand_categories:
        all_tags.append(f"hand_{hc.value}")

    return ScenarioClassification(
        taxonomy_version=TAXONOMY_VERSION,
        street=street,
        decision_types=tuple(decision_types),
        position=position,
        relative_position=relative_pos,
        hand_categories=tuple(hand_categories),
        board_textures=tuple(board_textures),
        strategic_concepts=tuple(strategic_concepts),
        tags=tuple(dict.fromkeys(all_tags)),  # preserve order, unique
    )
