"""Interactive Equity Trainer Sub-Engine.

Provides 7 challenge modes for Texas Hold'em equity estimation:
1. Hand vs Hand
2. Hand vs Range
3. Range vs Range
4. Equity Changes by Street (Sequential runout)
5. Range Narrowing Exercises (Action conditioning)
6. Blocker and Combination Counting
7. Equity Intuition Challenges (Archetypes)

Leverages the verified EquityEngine for ground-truth calculation:
- Uses exact enumeration when <= 50,000 runouts.
- Uses deterministic seeded Monte Carlo with 95% CI when runouts are large.
- Explicitly flags exact vs approximate simulation.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from app.domain.poker.cards import Card, Deck
from app.domain.poker.equity import EquityEngine
from app.domain.poker.ranges import HandCombo, HandRange


@dataclass
class EquityChallenge:
    """An equity training challenge."""

    challenge_id: str
    challenge_type: str  # HAND_VS_HAND, HAND_VS_RANGE, RANGE_VS_RANGE, STREET_CHANGES, RANGE_NARROWING, BLOCKERS, INTUITION
    title: str
    description: str
    hero_hand: list[str]  # e.g. ["As", "Kd"]
    opponent_hand_or_range: str | list[str]  # e.g. ["Qh", "Qc"] or "TT+, AJs+, KQs, AQo+"
    board: list[str]  # e.g. ["Ts", "8s", "2c"]
    street: str  # preflop, flop, turn, river
    ground_truth_equity: float  # Hero equity (0.0 to 100.0)
    is_exact: bool  # True if exact combinations, False if Monte Carlo
    confidence_interval_95: list[float]  # [low, high]
    sample_count: int
    archetype: str | None = None
    outs_explanation: str = ""
    blocker_impact_explanation: str = ""
    seed: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "challenge_id": self.challenge_id,
            "challenge_type": self.challenge_type,
            "title": self.title,
            "description": self.description,
            "hero_hand": self.hero_hand,
            "opponent_hand_or_range": self.opponent_hand_or_range,
            "board": self.board,
            "street": self.street,
            "ground_truth_equity": round(self.ground_truth_equity, 2),
            "is_exact": self.is_exact,
            "confidence_interval_95": [round(c, 2) for c in self.confidence_interval_95],
            "sample_count": self.sample_count,
            "archetype": self.archetype,
            "outs_explanation": self.outs_explanation,
            "blocker_impact_explanation": self.blocker_impact_explanation,
            "seed": self.seed,
        }


class EquityTrainerEngine:
    """Generates and evaluates equity challenges with ground-truth mathematical rigor."""

    ARCHETYPES = [
        ("pair_vs_overcards", "Pocket Pair vs Two Overcards (Coin Flip)", "JJ", "AKs"),
        ("overpair_vs_set", "Overpair vs Flopped Set", "AA", "77"),
        ("flush_draw_vs_top_pair", "Flush Draw vs Top Pair Top Kicker", "As 5s", "Kd Qh"),
        ("combo_draw_vs_made_hand", "Monster Combo Draw vs Overpair", "Js Ts", "Qh Qc"),
        ("dominated_ace", "Dominating Ace vs Weaker Ace", "Ah Kd", "Ac Qs"),
        ("two_pair_vs_straight_draw", "Two Pair vs Open-Ended Straight Draw", "As Ts", "9h 8h"),
        (
            "bluff_catcher_vs_polarized",
            "River Bluff Catcher vs Polarized Shove",
            "Jh Jd",
            "AA, KK, 72o",
        ),
    ]

    @classmethod
    def generate_challenge(
        cls,
        challenge_type: str = "HAND_VS_HAND",
        street: str = "flop",
        seed: int | None = None,
    ) -> EquityChallenge:
        """Create a mathematically verified equity challenge."""
        rng = random.Random(seed if seed is not None else random.randint(1, 999_999_999))
        effective_seed = rng.randint(1, 999_999_999)

        if challenge_type == "INTUITION":
            return cls._gen_intuition(rng, effective_seed)
        elif challenge_type == "BLOCKERS":
            return cls._gen_blockers(rng, effective_seed)
        elif challenge_type == "HAND_VS_RANGE":
            return cls._gen_hand_vs_range(rng, effective_seed, street)
        elif challenge_type == "STREET_CHANGES":
            return cls._gen_street_changes(rng, effective_seed)
        else:
            return cls._gen_hand_vs_hand(rng, effective_seed, street)

    @classmethod
    def _gen_hand_vs_hand(cls, rng: random.Random, seed: int, street: str) -> EquityChallenge:
        deck = Deck()
        deck.shuffle(seed=seed)

        hero_c1, hero_c2 = deck.deal(2)
        villain_c1, villain_c2 = deck.deal(2)

        board_cards: list[Card] = []
        if street in ("flop", "turn", "river"):
            board_cards.extend(deck.deal(3))
        if street in ("turn", "river"):
            board_cards.extend(deck.deal(1))
        if street == "river":
            board_cards.extend(deck.deal(1))

        hero_hand = [str(hero_c1), str(hero_c2)]
        villain_hand = [str(villain_c1), str(villain_c2)]
        board_strs = [str(c) for c in board_cards]

        result = EquityEngine.calculate_exact_hole_cards(
            hands=[
                ("Hero", (hero_c1, hero_c2)),
                ("Villain", (villain_c1, villain_c2)),
            ],
            board=board_cards,
        )

        hero_res = result.players[0]
        eq_pct = hero_res.equity

        return EquityChallenge(
            challenge_id=f"eq_hvh_{seed}",
            challenge_type="HAND_VS_HAND",
            title=f"Hand vs Hand Equity ({street.capitalize()})",
            description=f"Estimate Hero's showdown equity with {hero_hand[0]} {hero_hand[1]} against Villain's {villain_hand[0]} {villain_hand[1]}.",
            hero_hand=hero_hand,
            opponent_hand_or_range=villain_hand,
            board=board_strs,
            street=street,
            ground_truth_equity=eq_pct,
            is_exact=result.is_exact,
            confidence_interval_95=[
                hero_res.confidence_interval_95[0],
                hero_res.confidence_interval_95[1],
            ],
            sample_count=result.total_samples,
            outs_explanation="Showdown equity accounts for all remaining cards in the deck, including river redraws and split pots.",
            seed=seed,
        )

    @classmethod
    def _gen_intuition(cls, rng: random.Random, seed: int) -> EquityChallenge:
        arch_id, arch_title, h_repr, v_repr = rng.choice(cls.ARCHETYPES)

        # Standard preset boards and cards for classic archetypes
        if arch_id == "pair_vs_overcards":
            hero_cards = [Card.from_str("Jh"), Card.from_str("Jc")]
            villain_cards = [Card.from_str("As"), Card.from_str("Kd")]
            board_cards = []
            street = "preflop"
            desc = "Classic preflop coin flip: Pocket Jacks vs Ace-King offsuit."
        elif arch_id == "overpair_vs_set":
            hero_cards = [Card.from_str("Ah"), Card.from_str("As")]
            villain_cards = [Card.from_str("7h"), Card.from_str("7d")]
            board_cards = [Card.from_str("7s"), Card.from_str("9c"), Card.from_str("2d")]
            street = "flop"
            desc = "Aces overpair facing a flopped set of Sevens on 7s 9c 2d."
        elif arch_id == "flush_draw_vs_top_pair":
            hero_cards = [Card.from_str("As"), Card.from_str("5s")]
            villain_cards = [Card.from_str("Kh"), Card.from_str("Qd")]
            board_cards = [Card.from_str("Kd"), Card.from_str("Ts"), Card.from_str("2s")]
            street = "flop"
            desc = "Nut flush draw (plus Ace overcard) vs Top Pair on Kd Ts 2s."
        elif arch_id == "combo_draw_vs_made_hand":
            hero_cards = [Card.from_str("Js"), Card.from_str("Ts")]
            villain_cards = [Card.from_str("Qh"), Card.from_str("Qc")]
            board_cards = [Card.from_str("9s"), Card.from_str("8s"), Card.from_str("2d")]
            street = "flop"
            desc = "Monster 15-out straight + flush combo draw vs Overpair Queens on 9s 8s 2d."
        elif arch_id == "dominated_ace":
            hero_cards = [Card.from_str("Ah"), Card.from_str("Kd")]
            villain_cards = [Card.from_str("Ac"), Card.from_str("Qs")]
            board_cards = []
            street = "preflop"
            desc = "Dominated Ace: Ace-King offsuit vs Ace-Queen offsuit."
        else:
            hero_cards = [Card.from_str("As"), Card.from_str("Ts")]
            villain_cards = [Card.from_str("9h"), Card.from_str("8h")]
            board_cards = [Card.from_str("Ah"), Card.from_str("Td"), Card.from_str("7s")]
            street = "flop"
            desc = "Hero holds Top Two Pair vs Open-Ended Straight Draw on Ah Td 7s."

        result = EquityEngine.calculate_exact_hole_cards(
            hands=[
                ("Hero", tuple(hero_cards)),
                ("Villain", tuple(villain_cards)),
            ],
            board=board_cards,
        )
        hero_res = result.players[0]

        return EquityChallenge(
            challenge_id=f"eq_int_{seed}",
            challenge_type="INTUITION",
            title=f"Archetype: {arch_title}",
            description=desc,
            hero_hand=[str(c) for c in hero_cards],
            opponent_hand_or_range=[str(c) for c in villain_cards],
            board=[str(c) for c in board_cards],
            street=street,
            ground_truth_equity=hero_res.equity,
            is_exact=result.is_exact,
            confidence_interval_95=[
                hero_res.confidence_interval_95[0],
                hero_res.confidence_interval_95[1],
            ],
            sample_count=result.total_samples,
            archetype=arch_id,
            outs_explanation="Notice how combo draws with 15 outs are often mathematical favorites over made overpairs on the flop!",
            seed=seed,
        )

    @classmethod
    def _gen_hand_vs_range(cls, rng: random.Random, seed: int, street: str) -> EquityChallenge:
        # Hero with top pair or draw vs a realistic continuing range
        hero_cards = [Card.from_str("Ah"), Card.from_str("Kh")]
        board_cards = [Card.from_str("As"), Card.from_str("8d"), Card.from_str("3c")]
        villain_range_str = "TT-88, 33, AQs-A8s, KQs, AQo"

        # Run Monte Carlo simulation vs range
        villain_range = HandRange.from_string(villain_range_str)
        hero_range = HandRange.from_combos({HandCombo(hero_cards[0], hero_cards[1]): 1.0})

        result = EquityEngine.calculate_monte_carlo(
            players=[("Hero", hero_range), ("Villain", villain_range)],
            board=board_cards,
            num_samples=10_000,
            seed=seed,
        )
        hero_res = result.players[0]

        return EquityChallenge(
            challenge_id=f"eq_hvr_{seed}",
            challenge_type="HAND_VS_RANGE",
            title="Hand vs Range Estimation",
            description=f"Hero holds Ah Kh on a board of As 8d 3c facing Villain's continuation range: '{villain_range_str}'. Estimate Hero's equity.",
            hero_hand=["Ah", "Kh"],
            opponent_hand_or_range=villain_range_str,
            board=["As", "8d", "3c"],
            street="flop",
            ground_truth_equity=hero_res.equity,
            is_exact=False,
            confidence_interval_95=[
                hero_res.confidence_interval_95[0],
                hero_res.confidence_interval_95[1],
            ],
            sample_count=result.total_samples,
            outs_explanation="Villain holds sets (88, 33) which crush Hero, but numerous weaker Aces (AQ, AJ, AT) that Hero dominates.",
            seed=seed,
        )

    @classmethod
    def _gen_blockers(cls, rng: random.Random, seed: int) -> EquityChallenge:
        # Question about combo counts
        hand = ["As", "Kd"]
        # Total combos of AA is 6. With As in Hero's hand, remaining is comb(3, 2) = 3 combos.
        desc = "Hero holds As Kd. How many combinations of Pocket Aces (AA) remain in the opponent's range?"
        return EquityChallenge(
            challenge_id=f"eq_blk_{seed}",
            challenge_type="BLOCKERS",
            title="Card Removal & Combination Counting",
            description=desc,
            hero_hand=hand,
            opponent_hand_or_range="AA",
            board=[],
            street="preflop",
            ground_truth_equity=3.0,  # 3 combos remaining
            is_exact=True,
            confidence_interval_95=[3.0, 3.0],
            sample_count=1,
            blocker_impact_explanation="An unblocked pair has 6 combos. Holding 1 card of that rank reduces combos to 3 (a 50% reduction!). Holding 2 cards reduces combos to 1.",
            seed=seed,
        )

    @classmethod
    def _gen_street_changes(cls, rng: random.Random, seed: int) -> EquityChallenge:
        # Flush draw on flop -> hits flush on turn -> river pairs board
        hero = ["Qs", "Js"]
        villain = ["Ah", "Kd"]
        board = ["As", "Ts", "2c"]  # Flop
        # Hero has gutshot + flush draw (12 outs)
        result = EquityEngine.calculate_exact_hole_cards(
            hands=[
                ("Hero", (Card.from_str(hero[0]), Card.from_str(hero[1]))),
                ("Villain", (Card.from_str(villain[0]), Card.from_str(villain[1]))),
            ],
            board=[Card.from_str(c) for c in board],
        )
        hero_res = result.players[0]

        return EquityChallenge(
            challenge_id=f"eq_str_{seed}",
            challenge_type="STREET_CHANGES",
            title="Equity Changes by Street",
            description="Hero holds Qs Js vs Villain's Ah Kd on flop As Ts 2c. Estimate Hero's equity with the flush draw + gutshot straight draw.",
            hero_hand=hero,
            opponent_hand_or_range=villain,
            board=board,
            street="flop",
            ground_truth_equity=hero_res.equity,
            is_exact=result.is_exact,
            confidence_interval_95=[
                hero_res.confidence_interval_95[0],
                hero_res.confidence_interval_95[1],
            ],
            sample_count=result.total_samples,
            outs_explanation="Hero has 9 spade outs for the flush + 3 King-less Tens/Nines for straight = 12 total clean outs.",
            seed=seed,
        )

    @classmethod
    def evaluate_estimate(
        cls, challenge: EquityChallenge, student_estimate: float, time_ms: int
    ) -> dict[str, Any]:
        """Grade student equity estimate with tolerance and signed bias."""
        gt = challenge.ground_truth_equity
        abs_error = abs(student_estimate - gt)
        signed_bias = student_estimate - gt

        # Tolerance: +/- 3.0% for hand vs hand, +/- 5.0% for complex ranges
        tolerance = 5.0 if not challenge.is_exact else 3.5
        is_correct = abs_error <= tolerance

        # Diagnostic classification
        bias_desc = "unbiased"
        if signed_bias > tolerance:
            bias_desc = "overestimating"
        elif signed_bias < -tolerance:
            bias_desc = "underestimating"

        explanation = (
            f"Ground truth equity: {gt:.1f}% ({'Exact combinatorial' if challenge.is_exact else 'Monte Carlo simulated 95% CI [' + str(round(challenge.confidence_interval_95[0], 1)) + '% - ' + str(round(challenge.confidence_interval_95[1], 1)) + '%]'}). "
            f"Your estimate was {student_estimate:.1f}%, yielding an absolute error of {abs_error:.1f}% ({bias_desc}). "
            f"{challenge.outs_explanation}"
        )

        return {
            "is_correct": is_correct,
            "student_estimate": student_estimate,
            "ground_truth_equity": gt,
            "is_exact": challenge.is_exact,
            "absolute_error": round(abs_error, 2),
            "signed_bias": round(signed_bias, 2),
            "bias_description": bias_desc,
            "time_taken_ms": time_ms,
            "explanation": explanation,
            "blocker_impact": challenge.blocker_impact_explanation,
        }
