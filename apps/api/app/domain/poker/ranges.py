"""Hand ranges engine for Texas Hold'em.

Models all 1,326 two-card combinations and 169 starting hand classes.
Supports canonical range notation parsing (e.g., 'AA, AKs:0.75, 77+, AJs+, KQo'),
individual combo weights, blocker filtering (card removal), conditional normalization,
and seeded reproducible combo sampling.
"""

from __future__ import annotations

import random
import re
from collections.abc import Sequence
from dataclasses import dataclass

from app.domain.exceptions import InvalidRangeError
from app.domain.poker.cards import Card, Rank, Suit


@dataclass(frozen=True, slots=True)
class HandCombo:
    """A canonical 2-card hole hand combination.

    Always sorted so c1 > c2 by rank value (or suit if same rank).
    """

    c1: Card
    c2: Card

    def __post_init__(self) -> None:
        if self.c1 == self.c2:
            raise ValueError(f"Duplicate card in HandCombo: {self.c1}")
        # Enforce canonical ordering: c1 > c2
        if (self.c1.rank.value, self.c1.suit.value) < (self.c2.rank.value, self.c2.suit.value):
            c1_card, c2_card = self.c2, self.c1
            object.__setattr__(self, "c1", c1_card)
            object.__setattr__(self, "c2", c2_card)

    def __str__(self) -> str:
        return f"{self.c1}{self.c2}"

    def __repr__(self) -> str:
        return f"HandCombo('{self.c1}{self.c2}')"

    @classmethod
    def from_str(cls, s: str) -> HandCombo:
        clean = s.strip()
        if len(clean) != 4:
            raise ValueError(
                f"HandCombo string must be exactly 4 characters (e.g. 'AsKs'), got '{s}'"
            )
        return cls(Card.from_str(clean[:2]), Card.from_str(clean[2:]))

    @property
    def is_pair(self) -> bool:
        return self.c1.rank == self.c2.rank

    @property
    def is_suited(self) -> bool:
        return self.c1.suit == self.c2.suit

    @property
    def hand_class(self) -> str:
        """169-class notation: 'AA', 'AKs', or 'AKo'."""
        if self.is_pair:
            return f"{self.c1.rank.symbol}{self.c2.rank.symbol}"
        if self.is_suited:
            return f"{self.c1.rank.symbol}{self.c2.rank.symbol}s"
        return f"{self.c1.rank.symbol}{self.c2.rank.symbol}o"

    def contains_card(self, card: Card) -> bool:
        return self.c1 == card or self.c2 == card

    def shares_cards(self, dead_cards: Sequence[Card]) -> bool:
        dead_set = set(dead_cards)
        return self.c1 in dead_set or self.c2 in dead_set


# Generate all 1,326 canonical combinations
ALL_1326_COMBOS: list[HandCombo] = []
_all_cards = [Card(rank=r, suit=s) for r in Rank for s in Suit]
for i in range(len(_all_cards)):
    for j in range(i + 1, len(_all_cards)):
        ALL_1326_COMBOS.append(HandCombo(c1=_all_cards[i], c2=_all_cards[j]))
assert len(ALL_1326_COMBOS) == 1326


def _all_combos_for_pair(rank: Rank) -> list[HandCombo]:
    suits = list(Suit)
    combos = []
    for i in range(len(suits)):
        for j in range(i + 1, len(suits)):
            combos.append(HandCombo(Card(rank, suits[i]), Card(rank, suits[j])))
    return combos


def _all_combos_suited(r1: Rank, r2: Rank) -> list[HandCombo]:
    high, low = (r1, r2) if r1 > r2 else (r2, r1)
    return [HandCombo(Card(high, s), Card(low, s)) for s in Suit]


def _all_combos_offsuit(r1: Rank, r2: Rank) -> list[HandCombo]:
    high, low = (r1, r2) if r1 > r2 else (r2, r1)
    combos = []
    for s1 in Suit:
        for s2 in Suit:
            if s1 != s2:
                combos.append(HandCombo(Card(high, s1), Card(low, s2)))
    return combos


@dataclass
class HandRange:
    """A weighted distribution over 2-card poker combinations."""

    # Mapping from canonical HandCombo to weight in [0.0, 1.0]
    weights: dict[HandCombo, float]

    @classmethod
    def empty(cls) -> HandRange:
        return cls(weights={})

    @classmethod
    def from_combos(cls, combos: dict[HandCombo, float]) -> HandRange:
        valid_weights = {}
        for combo, weight in combos.items():
            if not (0.0 <= weight <= 1.0):
                raise InvalidRangeError(str(combo), f"Weight {weight} must be between 0.0 and 1.0")
            if weight > 0.0:
                valid_weights[combo] = float(weight)
        return cls(weights=valid_weights)

    @classmethod
    def from_string(cls, range_str: str) -> HandRange:
        """Parse standard poker range notation.

        Examples:
            'AA, KK, QQ'
            'AKs, AQs, AJs'
            '77+' (77 through AA)
            '88-TT' (88, 99, TT)
            'AJs+' (AJs, AQs, AKs)
            'ATo+' (ATo, AJo, AQo, AKo)
            'KQo, QJo'
            'AhKh, AsKd'
            'AKs:0.5, QQ:0.25'
        """
        if not range_str or not range_str.strip():
            return cls.empty()

        combos_with_weights: dict[HandCombo, float] = {}
        tokens = [t.strip() for t in range_str.split(",") if t.strip()]

        for token in tokens:
            weight = 1.0
            expr = token

            if ":" in token:
                parts = token.split(":")
                expr = parts[0].strip()
                try:
                    weight = float(parts[1].strip())
                    if not (0.0 <= weight <= 1.0):
                        raise InvalidRangeError(token, f"Weight {weight} must be in [0.0, 1.0]")
                except ValueError as err:
                    raise InvalidRangeError(token, f"Invalid weight syntax in '{token}'") from err

            # Expand the expression into HandCombos
            expanded = _expand_range_token(expr)
            for c in expanded:
                combos_with_weights[c] = weight

        return cls(weights=combos_with_weights)

    @property
    def total_weight(self) -> float:
        """Sum of all combination weights."""
        return sum(self.weights.values())

    @property
    def combo_count(self) -> int:
        """Count of distinct active combinations with weight > 0."""
        return len([w for w in self.weights.values() if w > 0])

    @property
    def percentage(self) -> float:
        """Percentage of the total 1,326 combinations represented by this range."""
        return (self.total_weight / 1326.0) * 100.0

    def filter_blockers(self, dead_cards: Sequence[Card]) -> HandRange:
        """Return a new HandRange excluding any combinations containing dead cards."""
        dead_set = set(dead_cards)
        filtered = {
            combo: weight
            for combo, weight in self.weights.items()
            if combo.c1 not in dead_set and combo.c2 not in dead_set
        }
        return HandRange(weights=filtered)

    def normalized_distribution(self) -> dict[HandCombo, float]:
        """Return combination probabilities normalized to sum to 1.0."""
        tot = self.total_weight
        if tot <= 0:
            return {}
        return {combo: weight / tot for combo, weight in self.weights.items()}

    def sample_combo(self, rng: random.Random | None = None) -> HandCombo | None:
        """Sample a single HandCombo from the range weighted by its probability."""
        if not self.weights:
            return None
        combos = list(self.weights.keys())
        w_values = list(self.weights.values())
        if sum(w_values) <= 0:
            return None
        if rng is not None:
            return rng.choices(combos, weights=w_values, k=1)[0]
        return random.choices(combos, weights=w_values, k=1)[0]

    def to_string(self) -> str:
        """Serialize back to a concise readable range string."""
        if not self.weights:
            return ""
        # Group combos by hand class and weight
        by_class: dict[str, list[float]] = {}
        for combo, weight in self.weights.items():
            by_class.setdefault(combo.hand_class, []).append(weight)

        parts = []
        for h_class, w_list in sorted(by_class.items()):
            avg_w = sum(w_list) / len(w_list)
            if avg_w >= 0.999:
                parts.append(h_class)
            else:
                parts.append(f"{h_class}:{avg_w:.2f}")
        return ", ".join(parts)


def _expand_range_token(token: str) -> list[HandCombo]:
    """Expand a single range token into concrete HandCombos."""
    t = token.strip()

    # Exact specific card combo, e.g. "AhKh" or "AsKd"
    if len(t) == 4 and t[0].upper() in "23456789TJQKA" and t[2].upper() in "23456789TJQKA":
        try:
            c1 = Card.from_str(t[:2])
            c2 = Card.from_str(t[2:])
            return [HandCombo(c1, c2)]
        except Exception:
            pass

    # Pocket pairs: AA, 77+, 88-TT
    pair_dash_match = re.match(r"^([2-9TJQKA])\1-([2-9TJQKA])\2$", t, re.IGNORECASE)
    if pair_dash_match:
        r1 = Rank.from_symbol(pair_dash_match.group(1))
        r2 = Rank.from_symbol(pair_dash_match.group(2))
        low, high = (r1, r2) if r1 < r2 else (r2, r1)
        combos = []
        for r_val in range(low.value, high.value + 1):
            combos.extend(_all_combos_for_pair(Rank(r_val)))
        return combos

    pair_plus_match = re.match(r"^([2-9TJQKA])\1\+$", t, re.IGNORECASE)
    if pair_plus_match:
        r = Rank.from_symbol(pair_plus_match.group(1))
        combos = []
        for r_val in range(r.value, Rank.ACE.value + 1):
            combos.extend(_all_combos_for_pair(Rank(r_val)))
        return combos

    single_pair_match = re.match(r"^([2-9TJQKA])\1$", t, re.IGNORECASE)
    if single_pair_match:
        r = Rank.from_symbol(single_pair_match.group(1))
        return _all_combos_for_pair(r)

    # Suited plus, e.g. "AJs+", "K9s+"
    suited_plus_match = re.match(r"^([2-9TJQKA])([2-9TJQKA])s\+$", t, re.IGNORECASE)
    if suited_plus_match:
        r_high = Rank.from_symbol(suited_plus_match.group(1))
        r_low = Rank.from_symbol(suited_plus_match.group(2))
        if r_high <= r_low:
            raise InvalidRangeError(t, f"High rank must exceed low rank in {t}")
        combos = []
        for kicker in range(r_low.value, r_high.value):
            combos.extend(_all_combos_suited(r_high, Rank(kicker)))
        return combos

    # Suited single, e.g. "AKs"
    suited_single_match = re.match(r"^([2-9TJQKA])([2-9TJQKA])s$", t, re.IGNORECASE)
    if suited_single_match:
        r1 = Rank.from_symbol(suited_single_match.group(1))
        r2 = Rank.from_symbol(suited_single_match.group(2))
        if r1 == r2:
            raise InvalidRangeError(t, f"Cannot have suited pocket pairs: {t}")
        return _all_combos_suited(r1, r2)

    # Offsuit plus, e.g. "ATo+", "Q9o+"
    offsuit_plus_match = re.match(r"^([2-9TJQKA])([2-9TJQKA])o\+$", t, re.IGNORECASE)
    if offsuit_plus_match:
        r_high = Rank.from_symbol(offsuit_plus_match.group(1))
        r_low = Rank.from_symbol(offsuit_plus_match.group(2))
        if r_high <= r_low:
            raise InvalidRangeError(t, f"High rank must exceed low rank in {t}")
        combos = []
        for kicker in range(r_low.value, r_high.value):
            combos.extend(_all_combos_offsuit(r_high, Rank(kicker)))
        return combos

    # Offsuit single, e.g. "AKo"
    offsuit_single_match = re.match(r"^([2-9TJQKA])([2-9TJQKA])o$", t, re.IGNORECASE)
    if offsuit_single_match:
        r1 = Rank.from_symbol(offsuit_single_match.group(1))
        r2 = Rank.from_symbol(offsuit_single_match.group(2))
        if r1 == r2:
            raise InvalidRangeError(t, f"Cannot have offsuit pocket pairs: {t}")
        return _all_combos_offsuit(r1, r2)

    # Unsuited generic: "AK" expands to suited + offsuit
    unspecified_match = re.match(r"^([2-9TJQKA])([2-9TJQKA])$", t, re.IGNORECASE)
    if unspecified_match:
        r1 = Rank.from_symbol(unspecified_match.group(1))
        r2 = Rank.from_symbol(unspecified_match.group(2))
        if r1 == r2:
            return _all_combos_for_pair(r1)
        return _all_combos_suited(r1, r2) + _all_combos_offsuit(r1, r2)

    raise InvalidRangeError(t, f"Unrecognized range syntax '{t}'")
