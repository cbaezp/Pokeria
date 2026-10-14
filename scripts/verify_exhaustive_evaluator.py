"""Exhaustive evaluation of all 2,598,960 five-card poker hands.

Verifies exact category counts against known mathematical constants.
"""

import itertools
import time

from app.domain.poker.cards import Deck
from app.domain.poker.evaluator import HandRank, evaluate_hand

THEORETICAL = {
    HandRank.STRAIGHT_FLUSH: 40,
    HandRank.FOUR_OF_A_KIND: 624,
    HandRank.FULL_HOUSE: 3744,
    HandRank.FLUSH: 5108,
    HandRank.STRAIGHT: 10200,
    HandRank.THREE_OF_A_KIND: 54912,
    HandRank.TWO_PAIR: 123552,
    HandRank.ONE_PAIR: 1098240,
    HandRank.HIGH_CARD: 1302540,
}


def run_exhaustive() -> None:
    deck = Deck.generate_standard_deck()
    counts = dict.fromkeys(HandRank, 0)

    print("Evaluating all 2,598,960 combinations of 5 cards...")
    t0 = time.time()

    for combo in itertools.combinations(deck, 5):
        strength = evaluate_hand(combo)
        counts[strength.hand_rank] += 1

    t1 = time.time()
    total = sum(counts.values())
    print(
        f"Completed {total:,} evaluations in {t1 - t0:.2f}s ({(total / (t1 - t0)):,.0f} evals/sec)\n"
    )

    discrepancies = False
    for cat in [
        HandRank.STRAIGHT_FLUSH,
        HandRank.FOUR_OF_A_KIND,
        HandRank.FULL_HOUSE,
        HandRank.FLUSH,
        HandRank.STRAIGHT,
        HandRank.THREE_OF_A_KIND,
        HandRank.TWO_PAIR,
        HandRank.ONE_PAIR,
        HandRank.HIGH_CARD,
    ]:
        actual = counts[cat]
        expected = THEORETICAL[cat]
        match = "MATCH" if actual == expected else "MISMATCH"
        print(f"{cat.name:<20}: {actual:>10,} (Expected: {expected:>10,}) [{match}]")
        if actual != expected:
            discrepancies = True

    if discrepancies:
        print("\nFAILED: Exhaustive frequency mismatch!")
        exit(1)
    else:
        print("\nPASSED: 100% exact match against theoretical combinatorics!")


if __name__ == "__main__":
    run_exhaustive()
