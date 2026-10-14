"""Performance benchmarks for Poker Lab Part 2 domain engine.

Measures:
1. Five-card hand evaluation.
2. Seven-card hand evaluation.
3. Range parsing.
4. Weighted range filtering.
5. Exact equity for small scenarios (turn runouts).
6. Monte Carlo equity (5,000 samples).
7. Game-state transitions.
"""

from __future__ import annotations

import platform
import random
import time

from app.domain.poker.cards import Card, Deck
from app.domain.poker.equity import EquityEngine
from app.domain.poker.evaluator import evaluate_5cards, evaluate_hand
from app.domain.poker.game_state import Action, ActionType, GameConfig, GameState
from app.domain.poker.ranges import HandRange


def run_benchmarks() -> dict[str, dict[str, float]]:
    print("=" * 70)
    print("POKER LAB PART 2 - PERFORMANCE BENCHMARK SUITE")
    print(f"Platform: {platform.platform()} ({platform.machine()})")
    print(f"Python: {platform.python_version()}")
    print("=" * 70)

    deck = Deck.generate_standard_deck()
    rng = random.Random(42)

    results: dict[str, dict[str, float]] = {}

    # 1. Five-card Hand Evaluation
    n_5 = 20_000
    hands_5 = [rng.sample(deck, 5) for _ in range(n_5)]
    t0 = time.perf_counter()
    for h in hands_5:
        evaluate_5cards(h)
    elapsed_5 = time.perf_counter() - t0
    ops_5 = n_5 / elapsed_5
    lat_5_us = (elapsed_5 / n_5) * 1_000_000
    print(f"1. Five-card Eval:    {ops_5:10.0f} ops/sec ({lat_5_us:6.2f} µs/op)")
    results["five_card_eval"] = {"ops_per_sec": ops_5, "latency_us": lat_5_us}

    # 2. Seven-card Hand Evaluation
    n_7 = 5_000
    hands_7 = [rng.sample(deck, 7) for _ in range(n_7)]
    t0 = time.perf_counter()
    for h in hands_7:
        evaluate_hand(h)
    elapsed_7 = time.perf_counter() - t0
    ops_7 = n_7 / elapsed_7
    lat_7_us = (elapsed_7 / n_7) * 1_000_000
    print(f"2. Seven-card Eval:   {ops_7:10.0f} ops/sec ({lat_7_us:6.2f} µs/op)")
    results["seven_card_eval"] = {"ops_per_sec": ops_7, "latency_us": lat_7_us}

    # 3. Range Parsing
    n_rp = 1_000
    range_expr = "AA, KK, QQ, JJ, TT, 99, 88, 77+, AKs, AQs, AJs, KQs, AKo, AQo:0.75"
    t0 = time.perf_counter()
    for _ in range(n_rp):
        HandRange.from_string(range_expr)
    elapsed_rp = time.perf_counter() - t0
    ops_rp = n_rp / elapsed_rp
    lat_rp_us = (elapsed_rp / n_rp) * 1_000_000
    print(f"3. Range Parsing:     {ops_rp:10.0f} ops/sec ({lat_rp_us:6.2f} µs/op)")
    results["range_parsing"] = {"ops_per_sec": ops_rp, "latency_us": lat_rp_us}

    # 4. Weighted Range Blocker Filtering
    n_rf = 10_000
    r_base = HandRange.from_string("AA, KK, QQ, JJ, AKs, AQs, AKo")
    dead_samples = [rng.sample(deck, 4) for _ in range(n_rf)]
    t0 = time.perf_counter()
    for dead in dead_samples:
        r_base.filter_blockers(dead)
    elapsed_rf = time.perf_counter() - t0
    ops_rf = n_rf / elapsed_rf
    lat_rf_us = (elapsed_rf / n_rf) * 1_000_000
    print(f"4. Blocker Filtering: {ops_rf:10.0f} ops/sec ({lat_rf_us:6.2f} µs/op)")
    results["blocker_filtering"] = {"ops_per_sec": ops_rf, "latency_us": lat_rf_us}

    # 5. Exact Equity (Turn Runouts - 44 boards)
    n_ee = 50
    turn_board = [Card.from_str(s) for s in "Jh Th 2c 3d".split()]
    hands_ee = [
        ("p1", [Card.from_str("Ah"), Card.from_str("Kh")]),
        ("p2", [Card.from_str("Jc"), Card.from_str("Jd")]),
    ]
    t0 = time.perf_counter()
    for _ in range(n_ee):
        EquityEngine.calculate_exact_hole_cards(hands_ee, turn_board)
    elapsed_ee = time.perf_counter() - t0
    ops_ee = n_ee / elapsed_ee
    lat_ee_ms = (elapsed_ee / n_ee) * 1_000
    print(f"5. Exact Turn Equity: {ops_ee:10.1f} ops/sec ({lat_ee_ms:6.2f} ms/op, 44 runouts/op)")
    results["exact_equity"] = {"ops_per_sec": ops_ee, "latency_ms": lat_ee_ms}

    # 6. Monte Carlo Equity (5,000 samples)
    n_mc = 5
    mc_players = [
        ("p1", HandRange.from_string("AhKh")),
        ("p2", HandRange.from_string("QcQd")),
    ]
    t0 = time.perf_counter()
    for _ in range(n_mc):
        EquityEngine.calculate_monte_carlo(mc_players, board=(), samples=5_000, seed=42)
    elapsed_mc = time.perf_counter() - t0
    ops_mc = n_mc / elapsed_mc
    lat_mc_ms = (elapsed_mc / n_mc) * 1_000
    print(f"6. MC Equity (5k):    {ops_mc:10.2f} ops/sec ({lat_mc_ms:6.2f} ms/op)")
    results["monte_carlo_equity"] = {"ops_per_sec": ops_mc, "latency_ms": lat_mc_ms}

    # 7. Game State Transitions
    n_gst = 1_000
    cfg = GameConfig(small_blind=5, big_blind=10, max_players=2)
    t0 = time.perf_counter()
    for _ in range(n_gst):
        st = GameState.start_hand(config=cfg, players_data=[("alice", 500), ("bob", 500)], rng=rng)
        st = st.apply_action(Action("alice", ActionType.CALL, 5))
        st = st.apply_action(Action("bob", ActionType.CHECK))
        st = st.apply_action(Action("bob", ActionType.CHECK))
        st = st.apply_action(Action("alice", ActionType.CHECK))
    elapsed_gst = time.perf_counter() - t0
    ops_gst = (n_gst * 4) / elapsed_gst  # 4 actions per hand
    lat_gst_us = (elapsed_gst / (n_gst * 4)) * 1_000_000
    print(f"7. State Transitions: {ops_gst:10.0f} ops/sec ({lat_gst_us:6.2f} µs/action)")
    results["state_transitions"] = {"ops_per_sec": ops_gst, "latency_us": lat_gst_us}

    print("=" * 70)
    return results


if __name__ == "__main__":
    run_benchmarks()
