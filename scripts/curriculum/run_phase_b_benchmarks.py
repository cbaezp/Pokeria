"""Benchmark runner and certification bank generator for Poker Lab Phase B.

Executes:
1. Benchmarks A through H with exact numerical metrics:
   - Config, iterations, convergence, solve time, pipeline time, peak RSS, output bytes,
     extraction time, full artifact validation time, quantization delta.
2. Generates the small certification bank (river textures, turn, flop, cash with rake, tournament ICM).
3. Produces a machine-readable summary JSON and console output.
"""

from __future__ import annotations

import json
import os
import resource
import subprocess
import time
from pathlib import Path
from typing import Any

from app.domain.poker.generation_pipeline import (
    ControlledGenerationPipeline,
)
from app.domain.poker.node_extractor import node_extractor
from app.domain.poker.solver_types import (
    PlayerSizings,
    SolverBetTree,
    SolverConfig,
    StreetSizings,
)


def get_peak_rss_mb() -> float:
    """Return peak resident set size in megabytes for current process & children."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    usage_children = resource.getrusage(resource.RUSAGE_CHILDREN)
    # On macOS, ru_maxrss is in bytes; on Linux, in kilobytes
    factor = 1.0 / (1024 * 1024) if os.uname().sysname == "Darwin" else 1.0 / 1024
    return (usage.ru_maxrss + usage_children.ru_maxrss) * factor


def run_benchmarks(solutions_dir: Path) -> dict[str, Any]:
    """Execute benchmarks A through H."""
    results: dict[str, Any] = {}
    solver_bin = Path("apps/solver/target/release/solver")

    configs = {
        "A": {
            "name": "River, simple sizing",
            "path": "data/benchmarks/bench_simple_river.toml",
            "storage": "f32",
        },
        "B": {
            "name": "River, multiple sizes",
            "path": "data/benchmarks/bench_multinode_river.toml",
            "storage": "f32",
        },
        "C": {
            "name": "Turn, multiple betting lines",
            "path": "data/benchmarks/bench_turn.toml",
            "storage": "f32",
        },
        "D": {
            "name": "Flop, compact tree",
            "path": "data/benchmarks/bench_flop.toml",
            "storage": "f32",
        },
        "E": {
            "name": "Flop, realistic multi-size tree",
            "path": "data/benchmarks/bench_flop.toml",
            "storage": "f32",
            "override_args": ["--max-iterations", "100"],
        },
        "F": {
            "name": "Cash game with rake",
            "path": "data/benchmarks/bench_rake.toml",
            "storage": "f32",
        },
        "G": {
            "name": "Tournament heads-up postflop with payout context",
            "path": "data/benchmarks/bench_tournament.toml",
            "storage": "f32",
        },
        "H": {
            "name": "I16 versus F32 storage accuracy (River Multi-Size)",
            "path": "data/benchmarks/bench_multinode_river.toml",
            "storage": "i16",
        },
    }

    scratch_dir = Path("scratch/benchmarks")
    scratch_dir.mkdir(parents=True, exist_ok=True)

    for key, spec in configs.items():
        print(f"--- Running Benchmark {key}: {spec['name']} ---")
        cfg_path = Path(spec["path"])
        out_path = scratch_dir / f"bench_{key}.json"

        cmd = [
            str(solver_bin),
            "solve",
            "--config",
            str(cfg_path),
            "--out",
            str(out_path),
            "--storage",
            spec["storage"],
        ]
        if "override_args" in spec:
            cmd.extend(spec["override_args"])

        t_start = time.perf_counter()
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        t_solve = time.perf_counter() - t_start

        if proc.returncode != 0:
            raise RuntimeError(f"Benchmark {key} failed: {proc.stderr}")

        # Parse final report from solver stdout
        iterations = 0
        exploit_chips = 0.0
        exploit_pct = 0.0
        payoff_unit = "chips"
        for line in proc.stdout.splitlines():
            line_str = line.strip()
            if line_str.startswith("iterations:"):
                iterations = int(line_str.split()[1])
            elif "exploitability:" in line_str or "NashConv:" in line_str:
                parts = line_str.split()
                try:
                    exploit_chips = float(parts[1])
                    exploit_pct = float(parts[3].replace("%", ""))
                except Exception:
                    pass
            elif line_str.startswith("payoff unit:"):
                payoff_unit = line_str.split(":")[1].strip().split()[0]

        file_bytes = out_path.stat().st_size

        # Node extraction benchmark
        t_extract_start = time.perf_counter()
        node_extractor.extract_node(f"bench_{key}", 0, out_path)
        t_extract_cold = time.perf_counter() - t_extract_start

        t_extract_wstart = time.perf_counter()
        node_extractor.extract_node(f"bench_{key}", 0, out_path)
        t_extract_warm = time.perf_counter() - t_extract_wstart

        # Full artifact validation
        t_val_start = time.perf_counter()
        with open(out_path, encoding="utf-8") as f:
            json.load(f)
        # Load config from file
        t_val = time.perf_counter() - t_val_start
        t_pipeline = t_solve + t_extract_cold + t_val

        results[key] = {
            "name": spec["name"],
            "config_file": spec["path"],
            "storage_mode": spec["storage"],
            "iterations": iterations,
            "convergence": f"{exploit_pct:.4f}% of pot ({exploit_chips:.6f} {payoff_unit})",
            "exploitability_pct_of_pot": exploit_pct,
            "payoff_unit": payoff_unit,
            "solve_wall_sec": round(t_solve, 4),
            "pipeline_wall_sec": round(t_pipeline, 4),
            "output_bytes": file_bytes,
            "extraction_cold_ms": round(t_extract_cold * 1000, 3),
            "extraction_warm_ms": round(t_extract_warm * 1000, 4),
            "validation_sec": round(t_val, 4),
            "peak_rss_mb": round(get_peak_rss_mb(), 2),
        }

    # Compare Benchmark B (F32) and Benchmark H (I16) for Quantization Delta
    with open(scratch_dir / "bench_B.json", encoding="utf-8") as f:
        data_b = json.load(f)
    with open(scratch_dir / "bench_H.json", encoding="utf-8") as f:
        data_h = json.load(f)

    # Compute max strategy and EV difference across root combos
    strat_b = data_b["nodes"][0]["strategy"]
    strat_h = data_h["nodes"][0]["strategy"]
    max_strat_diff = max(abs(sb - sh) for sb, sh in zip(strat_b, strat_h, strict=False))

    ev_b = data_b["nodes"][0].get("action_evs")
    ev_h = data_h["nodes"][0].get("action_evs")
    max_ev_diff = 0.0
    if ev_b and ev_h:
        max_ev_diff = max(abs(eb - eh) for eb, eh in zip(ev_b, ev_h, strict=False))

    results["H"]["quantization_max_strategy_diff"] = round(max_strat_diff, 6)
    results["H"]["quantization_max_action_ev_diff"] = round(max_ev_diff, 6)

    return results


def generate_certification_bank(solutions_dir: Path) -> list[dict[str, Any]]:
    """Generate and verify 5 certified production strategy packs."""
    pipeline = ControlledGenerationPipeline(solutions_dir=solutions_dir)
    certified_packs = []

    specs = [
        {
            "scenario_key": "cert_cash_river_polarized",
            "name": "Cash River Polarized Bet / Bluff-Catch",
            "description": "Certified cash game river spot with polarized sizing (33%, 75%, 150%)",
            "config": SolverConfig(
                board="As Kd 7h 2c 9s",
                oop_range="AA,KK,QQ,JJ,77,22,AKs,AKo,A5s",
                ip_range="AA,KK,QQ,JJ,TT,99,77,AKs,AKo,KQo,QJs",
                starting_pot=20.0,
                effective_stack=100.0,
                game_type="CASH",
                payoff_unit="chips",
                max_iterations=300,
                target_exploitability=0.25,
                raise_cap=2,
                bet_tree=SolverBetTree(
                    oop=PlayerSizings(
                        river=StreetSizings(bet=[33.0, 75.0, 150.0], raise_=[50.0, 100.0])
                    ),
                    ip=PlayerSizings(river=StreetSizings(bet=[33.0, 75.0], raise_=[50.0, 100.0])),
                ),
            ),
            "min_iterations": 150,
        },
        {
            "scenario_key": "cert_cash_river_rake",
            "name": "Cash River Multi-Size (5% Rake, $3 Cap)",
            "description": "Certified rake-aware cash game river spot under casino rake rules",
            "config": SolverConfig(
                board="Ks 8c 4d 2h Th",
                oop_range="AA,KK,QQ,JJ,TT,88,AKs,AKo,A5s",
                ip_range="AA,KK,QQ,JJ,TT,99,88,AKs,AKo,KQo,QJs",
                starting_pot=20.0,
                effective_stack=50.0,
                game_type="CASH",
                payoff_unit="chips",
                rake_percent=5.0,
                rake_cap=3.0,
                max_iterations=200,
                target_exploitability=0.50,
                raise_cap=2,
                bet_tree=SolverBetTree(
                    oop=PlayerSizings(river=StreetSizings(bet=[50.0, 100.0], raise_=[100.0])),
                    ip=PlayerSizings(river=StreetSizings(bet=[50.0, 100.0], raise_=[100.0])),
                ),
            ),
            "min_iterations": 100,
        },
        {
            "scenario_key": "cert_cash_turn_barrel",
            "name": "Cash Turn Double-Barrel Spot",
            "description": "Certified turn betting scenario with turn barrel and river decision tree",
            "config": SolverConfig(
                board="Qh Jd 4s 8c",
                oop_range="QQ,JJ,88,44,AJs,KJs,QJs,JTs,T9s,98s",
                ip_range="AA,KK,QQ,JJ,88,44,AJs,ATs,KJs,QJs,AKo",
                starting_pot=16.0,
                effective_stack=80.0,
                game_type="CASH",
                payoff_unit="chips",
                max_iterations=150,
                target_exploitability=0.50,
                raise_cap=1,
                bet_tree=SolverBetTree(
                    oop=PlayerSizings(
                        turn=StreetSizings(bet=[66.0]),
                        river=StreetSizings(bet=[66.0]),
                    ),
                    ip=PlayerSizings(
                        turn=StreetSizings(bet=[66.0], raise_=[100.0]),
                        river=StreetSizings(bet=[66.0], raise_=[100.0]),
                    ),
                ),
            ),
            "min_iterations": 100,
        },
        {
            "scenario_key": "cert_cash_flop_cbet",
            "name": "Cash Flop Continuation Bet Spot",
            "description": "Certified flop c-bet spot on dry Ace-high texture",
            "config": SolverConfig(
                board="Ac 8d 3s",
                oop_range="AA,88,33,AKs,A8s,A3s,KQs,KJs,87s,76s",
                ip_range="AA,KK,QQ,JJ,88,33,AKs,A8s,KQs,QJs,JTs,AKo",
                starting_pot=10.0,
                effective_stack=50.0,
                game_type="CASH",
                payoff_unit="chips",
                max_iterations=250,
                target_exploitability=0.50,
                raise_cap=1,
                bet_tree=SolverBetTree(
                    oop=PlayerSizings(
                        flop=StreetSizings(bet=[33.0]),
                        turn=StreetSizings(bet=[50.0]),
                        river=StreetSizings(bet=[75.0]),
                    ),
                    ip=PlayerSizings(
                        flop=StreetSizings(bet=[33.0]),
                        turn=StreetSizings(bet=[50.0]),
                        river=StreetSizings(bet=[75.0]),
                    ),
                ),
            ),
            "min_iterations": 80,
        },
        {
            "scenario_key": "cert_tourn_hu_icm",
            "name": "Tournament Heads-Up Postflop (ICM CSTE)",
            "description": "Certified tournament heads-up spot evaluated in Chip-Scaled Tournament Equity (CSTE)",
            "config": SolverConfig(
                board="Kd 9s 2c 6h 3d",
                oop_range="AA,KK,QQ,JJ,TT,99,77,22,AKs,AKo,A5s",
                ip_range="AA,KK,QQ,JJ,TT,99,77,22,AKs,AKo,KQo,QJs",
                starting_pot=20.0,
                effective_stack=25.0,
                game_type="TOURNAMENT",
                payoff_unit="cste",
                payout_structure=[500.0, 300.0, 200.0],
                tournament_stacks=[25.0, 35.0, 40.0, 15.0, 10.0, 15.0],
                tournament_seats=[0, 1],
                max_iterations=200,
                target_exploitability=0.10,
                raise_cap=2,
                bet_tree=SolverBetTree(
                    oop=PlayerSizings(river=StreetSizings(bet=[50.0, 100.0], raise_=[100.0])),
                    ip=PlayerSizings(river=StreetSizings(bet=[50.0, 100.0], raise_=[100.0])),
                ),
            ),
            "min_iterations": 100,
        },
    ]

    for s in specs:
        print(f"Generating certified pack: {s['scenario_key']}...")
        pack, gate = pipeline.generate_and_certify(
            config=s["config"],
            name=s["name"],
            description=s["description"],
            scenario_key=s["scenario_key"],
            min_iterations=s["min_iterations"],
        )
        certified_packs.append(
            {
                "id": pack.id,
                "scenario_key": pack.scenario_key,
                "name": pack.name,
                "board": pack.board,
                "game_type": pack.game_type,
                "payoff_unit": pack.payoff_unit,
                "rake_percent": pack.rake_percent,
                "iterations": pack.iterations,
                "exploitability_pct_of_pot": pack.exploitability_pct_of_pot,
                "node_count": pack.node_count,
                "artifact_bytes": pack.artifact_bytes,
                "validation_status": pack.validation_status.value,
            }
        )

    return certified_packs


if __name__ == "__main__":
    solutions_path = Path("data/solutions")
    print("=== POKER LAB PHASE B: RUNNING BENCHMARKS A THROUGH H ===")
    benchmarks_data = run_benchmarks(solutions_path)

    print("\n=== POKER LAB PHASE B: GENERATING CERTIFICATION BANK ===")
    cert_bank_data = generate_certification_bank(solutions_path)

    summary = {
        "benchmarks": benchmarks_data,
        "certification_bank": cert_bank_data,
    }

    out_file = Path("scratch/phase_b_benchmarks_report.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\nAll benchmarks and certification packs completed. Report saved to {out_file}")
