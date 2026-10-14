"""Benchmark runner for Poker Lab Part 3 GTO Solver pipeline."""

import asyncio
import os
import platform
import time

import psutil

from app.domain.poker.solver_types import (
    PlayerSizings,
    SolverBetTree,
    SolverConfig,
    StreetSizings,
)
from app.infrastructure.solver.subprocess_solver import SubprocessSolverAdapter


def get_system_specs() -> dict[str, str]:
    mem = psutil.virtual_memory()
    return {
        "os": f"{platform.system()} {platform.release()}",
        "arch": platform.machine(),
        "cpu_count": str(os.cpu_count()),
        "total_ram_gb": f"{mem.total / (1024**3):.2f} GB",
        "available_ram_gb": f"{mem.available / (1024**3):.2f} GB",
    }


async def run_benchmarks() -> dict:
    adapter = SubprocessSolverAdapter()
    meta = adapter.get_engine_metadata()
    specs = get_system_specs()

    print("=" * 60)
    print("POKER LAB PART 3 — SOLVER PERFORMANCE BENCHMARKS")
    print(f"System: {specs['arch']} | {specs['cpu_count']} CPUs | {specs['total_ram_gb']} RAM")
    print(f"Engine: {meta.name} @ {meta.commit[:8]} ({meta.license})")
    print("=" * 60)

    results = {
        "system": specs,
        "engine": {"name": meta.name, "commit": meta.commit, "license": meta.license},
        "benchmarks": {},
    }

    # 1. River Benchmark
    print("\n[1/6] Running River Solve Benchmark...")
    river_config = SolverConfig(
        board="Ah Kd 2c 7s 9c",
        oop_range="AA,KK,QQ,JJ,TT,99,77,22,AKs,AKo,A5s",
        ip_range="AA,KK,QQ,JJ,TT,99,77,22,AKs,AKo,KQo,QJs",
        starting_pot=20.0,
        effective_stack=50.0,
        bet_tree=SolverBetTree(
            oop=PlayerSizings(river=StreetSizings(bet=[50.0, 100.0], allin=True)),
            ip=PlayerSizings(river=StreetSizings(bet=[50.0], raise_=[100.0], allin=True)),
        ),
        max_iterations=100,
        target_exploitability=0.1,
    )
    t0 = time.perf_counter()
    proc = psutil.Process()
    mem_before = proc.memory_info().rss
    river_res = await adapter.solve(river_config)
    river_time = time.perf_counter() - t0
    mem_after = proc.memory_info().rss

    results["benchmarks"]["river"] = {
        "type": "River solve",
        "iterations": river_res.iterations,
        "elapsed_seconds": round(river_time, 4),
        "exploitability_chips": round(river_res.exploitability_chips, 6),
        "exploitability_pct_pot": round(river_res.exploitability_pct_of_pot, 4),
        "node_count": river_res.node_count,
        "memory_delta_mb": round((mem_after - mem_before) / (1024**2), 2),
    }
    print(
        f"  Done in {river_time:.4f}s | {results['benchmarks']['river']['exploitability_pct_pot']}% pot exploitability ({river_res.iterations} iters)"
    )

    # 2. Turn Benchmark
    print("\n[2/6] Running Turn Solve Benchmark...")
    turn_config = SolverConfig(
        board="Js 8c 4d 2h",
        oop_range="QQ,JJ,88,44,AJs,KJs,QJs,JTs,T9s,98s",
        ip_range="AA,KK,QQ,JJ,88,AKs,AKo,AQs,AQo,KQs",
        starting_pot=30.0,
        effective_stack=70.0,
        bet_tree=SolverBetTree(
            oop=PlayerSizings(
                turn=StreetSizings(bet=[50.0], allin=False),
                river=StreetSizings(bet=[50.0], allin=True),
            ),
            ip=PlayerSizings(
                turn=StreetSizings(bet=[50.0], raise_=[100.0], allin=True),
                river=StreetSizings(bet=[50.0], raise_=[100.0], allin=True),
            ),
        ),
        max_iterations=100,
        target_exploitability=0.2,
    )
    t0 = time.perf_counter()
    turn_res = await adapter.solve(turn_config)
    turn_time = time.perf_counter() - t0

    results["benchmarks"]["turn"] = {
        "type": "Turn-to-river solve",
        "iterations": turn_res.iterations,
        "elapsed_seconds": round(turn_time, 4),
        "exploitability_chips": round(turn_res.exploitability_chips, 6),
        "exploitability_pct_pot": round(turn_res.exploitability_pct_of_pot, 4),
        "node_count": turn_res.node_count,
    }
    print(
        f"  Done in {turn_time:.4f}s | {results['benchmarks']['turn']['exploitability_pct_pot']}% pot exploitability ({turn_res.iterations} iters)"
    )

    # 3. Feasible Flop Benchmark
    print("\n[3/6] Running Feasible Flop Solve Benchmark...")
    flop_config = SolverConfig(
        board="Ks 7d 2c",
        oop_range="TT,99,88,77,22,KQs,KJs,KTs,QJs,JTs",
        ip_range="AA,KK,QQ,JJ,AKs,AKo,AQs,AQo",
        starting_pot=20.0,
        effective_stack=40.0,
        bet_tree=SolverBetTree(
            oop=PlayerSizings(
                flop=StreetSizings(bet=[33.0], allin=False),
                turn=StreetSizings(bet=[50.0], allin=False),
                river=StreetSizings(bet=[50.0], allin=True),
            ),
            ip=PlayerSizings(
                flop=StreetSizings(bet=[33.0], allin=False),
                turn=StreetSizings(bet=[50.0], allin=False),
                river=StreetSizings(bet=[50.0], allin=True),
            ),
        ),
        max_iterations=50,
        target_exploitability=0.5,
    )
    t0 = time.perf_counter()
    flop_res = await adapter.solve(flop_config)
    flop_time = time.perf_counter() - t0

    results["benchmarks"]["flop"] = {
        "type": "Flop-to-river solve",
        "iterations": flop_res.iterations,
        "elapsed_seconds": round(flop_time, 4),
        "exploitability_chips": round(flop_res.exploitability_chips, 6),
        "exploitability_pct_pot": round(flop_res.exploitability_pct_of_pot, 4),
        "node_count": flop_res.node_count,
    }
    print(
        f"  Done in {flop_time:.4f}s | {results['benchmarks']['flop']['exploitability_pct_pot']}% pot exploitability ({flop_res.iterations} iters)"
    )

    # 4. Serialization & Load Time Benchmark
    print("\n[4/6] Running Serialization & Deserialization Benchmark...")
    t0 = time.perf_counter()
    raw_bytes = adapter.serialize_solution(river_res.raw_solution)
    ser_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    adapter.deserialize_solution(raw_bytes)
    deser_time = time.perf_counter() - t0

    results["benchmarks"]["serialization"] = {
        "size_bytes": len(raw_bytes),
        "serialize_ms": round(ser_time * 1000, 3),
        "deserialize_ms": round(deser_time * 1000, 3),
    }
    print(
        f"  Serialized {len(raw_bytes)} bytes in {ser_time * 1000:.3f}ms | Deserialized in {deser_time * 1000:.3f}ms"
    )

    # 5. Strategy Query Latency Benchmark
    print("\n[5/6] Running Strategy Query Latency Benchmark...")
    times = []
    nodes = river_res.raw_solution.get("nodes", [])
    root_node_id = nodes[0].get("node", 0) if nodes else 0
    player0_combos = river_res.raw_solution.get("root_combos", [[], []])[0]
    sample_combo = player0_combos[0].get("cards", "AhKd") if player0_combos else "AhKd"

    for _ in range(500):
        t0 = time.perf_counter()
        _ = adapter.extract_strategy(river_res.raw_solution, root_node_id, sample_combo)
        times.append(time.perf_counter() - t0)

    avg_query_us = (sum(times) / len(times)) * 1_000_000
    results["benchmarks"]["strategy_query"] = {
        "samples": 500,
        "avg_query_microseconds": round(avg_query_us, 2),
    }
    print(f"  Avg lookup latency over 500 queries: {avg_query_us:.2f} µs")

    # 6. Concurrent Solve Benchmark
    print("\n[6/6] Running Concurrent Solves Benchmark (2 parallel solves)...")
    t0 = time.perf_counter()
    res1, res2 = await asyncio.gather(
        adapter.solve(river_config),
        adapter.solve(river_config),
    )
    concurrent_time = time.perf_counter() - t0
    results["benchmarks"]["concurrency"] = {
        "parallel_solves": 2,
        "total_elapsed_seconds": round(concurrent_time, 4),
        "throughput_solves_per_sec": round(2 / concurrent_time, 2),
    }
    print(
        f"  2 parallel solves finished in {concurrent_time:.4f}s ({2 / concurrent_time:.2f} solves/s)"
    )

    print("\n" + "=" * 60)
    print("ALL BENCHMARKS COMPLETED SUCCESSFULLY")
    print("=" * 60)
    return results


if __name__ == "__main__":
    asyncio.run(run_benchmarks())
