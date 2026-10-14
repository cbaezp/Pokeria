"""Verify Poker Lab hand evaluator against independent reference library 'treys' (MIT).

Runs 100,000 comparisons comparing relative hand strengths and tie determinations.
"""

import random
import sys
import time

from treys import Card as TreysCard
from treys import Evaluator as TreysEvaluator

from app.domain.poker.cards import Deck
from app.domain.poker.evaluator import evaluate_hand


def run_comparisons(n_comparisons: int = 100_000, seed: int = 42) -> None:
    rng = random.Random(seed)
    treys_evaluator = TreysEvaluator()

    discrepancies = 0
    start_time = time.time()

    deck_prototype = Deck.generate_standard_deck()

    print(f"Starting {n_comparisons:,} randomized hand comparisons against 'treys'...")

    for i in range(1, n_comparisons + 1):
        # Sample 9 distinct cards (5 board, 2 for hand A, 2 for hand B)
        sampled = rng.sample(deck_prototype, 9)
        board = sampled[:5]
        hand_a = sampled[5:7]
        hand_b = sampled[7:9]

        # 1. Evaluate with Poker Lab domain evaluator
        pl_strength_a = evaluate_hand(hand_a + board)
        pl_strength_b = evaluate_hand(hand_b + board)

        if pl_strength_a > pl_strength_b:
            pl_result = 1  # A wins
        elif pl_strength_a < pl_strength_b:
            pl_result = -1  # B wins
        else:
            pl_result = 0  # Tie

        # 2. Evaluate with Treys (independent reference)
        treys_board = [TreysCard.new(str(c)) for c in board]
        treys_hand_a = [TreysCard.new(str(c)) for c in hand_a]
        treys_hand_b = [TreysCard.new(str(c)) for c in hand_b]

        score_a = treys_evaluator.evaluate(treys_board, treys_hand_a)
        score_b = treys_evaluator.evaluate(treys_board, treys_hand_b)

        if score_a < score_b:
            treys_result = 1  # A wins
        elif score_a > score_b:
            treys_result = -1  # B wins
        else:
            treys_result = 0  # Tie

        if pl_result != treys_result:
            discrepancies += 1
            print(f"DISCREPANCY at iteration {i}:")
            print(f"  Board: {[str(c) for c in board]}")
            print(f"  Hand A: {[str(c) for c in hand_a]} -> PL: {pl_strength_a} | Treys: {score_a}")
            print(f"  Hand B: {[str(c) for c in hand_b]} -> PL: {pl_strength_b} | Treys: {score_b}")
            print(f"  PL outcome: {pl_result} vs Treys outcome: {treys_result}")
            if discrepancies >= 5:
                print("Aborting early due to multiple discrepancies.")
                break

        if i % 25_000 == 0:
            elapsed = time.time() - start_time
            rate = i / elapsed
            print(f"  Completed {i:,} / {n_comparisons:,} ({rate:.0f} comparisons/sec)...")

    elapsed = time.time() - start_time
    print("=" * 70)
    print(
        f"Finished {n_comparisons:,} comparisons in {elapsed:.2f}s ({n_comparisons / elapsed:.0f} comp/sec)"
    )
    print(f"Discrepancies found: {discrepancies}")
    print("=" * 70)

    if discrepancies > 0:
        sys.exit(1)


if __name__ == "__main__":
    n = 100_000
    if len(sys.argv) > 1:
        n = int(sys.argv[1])
    run_comparisons(n)
