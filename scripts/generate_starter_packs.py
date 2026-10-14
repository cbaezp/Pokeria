"""Script to generate genuinely solved reference strategy packs for Poker Lab.

Runs real Discounted CFR solves, measures exploitability, and persists solution artifacts with SHA-256 integrity.
"""

import asyncio
import json
import time
from pathlib import Path

from app.domain.poker.solver_types import (
    PlayerSizings,
    SolverBetTree,
    SolverConfig,
    StreetSizings,
)
from app.domain.poker.strategy_pack import StrategyPack
from app.infrastructure.database.session import get_session_factory
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.solver.subprocess_solver import SubprocessSolverAdapter


async def main() -> None:
    adapter = SubprocessSolverAdapter(
        bin_path="apps/api/bin/solver",
        solutions_dir="data/solutions",
    )
    session_factory = get_session_factory()

    starter_configs = [
        {
            "name": "River Value-Betting & Bluffing (Dry Ace-High)",
            "description": "Standard river decision on Ah Kd 2c 7s 9c. Polarized betting and bluff-catching ranges.",
            "config": SolverConfig(
                board="Ah Kd 2c 7s 9c",
                oop_range="AA,KK,QQ,JJ,TT,99,77,22,AKs,AKo,A5s",
                ip_range="AA,KK,QQ,JJ,TT,99,77,22,AKs,AKo,KQo,QJs",
                starting_pot=20.0,
                effective_stack=50.0,
                bet_tree=SolverBetTree(
                    oop=PlayerSizings(river=StreetSizings(bet=[50.0, 100.0], allin=True)),
                    ip=PlayerSizings(river=StreetSizings(bet=[50.0], raise_=[100.0], allin=True)),
                ),
                max_iterations=300,
                target_exploitability=0.5,
                report_every=50,
            ),
        },
        {
            "name": "River Bluff-Catching (Monotone Flush Runout)",
            "description": "River spot on Qs Js 2s 8d 4h with made flushes, two pairs, and missed draw bluffs.",
            "config": SolverConfig(
                board="Qs Js 2s 8d 4h",
                oop_range="AsKs,KsQs,QsJs,JJ,TT,99,88,44,AdQd,AhQh,AcQc,KdQd,JdTd",
                ip_range="AsTs,KsTs,QsTs,JsTs,8s7s,7s6s,6s5s,5s4s,AsKd,AsQd,AsJd,KdJd,QdJd,AhKh",
                starting_pot=30.0,
                effective_stack=70.0,
                bet_tree=SolverBetTree(
                    oop=PlayerSizings(river=StreetSizings(bet=[], allin=False)),
                    ip=PlayerSizings(river=StreetSizings(bet=[66.0], allin=True)),
                ),
                max_iterations=300,
                target_exploitability=0.5,
                report_every=50,
            ),
        },
        {
            "name": "River Polarized Jam (Paired Board)",
            "description": "Polarized river shove spot on Kd 8c 8s 3h 2c with trips and missed bluffs.",
            "config": SolverConfig(
                board="Kd 8c 8s 3h 2c",
                oop_range="88,22,33,KQs,KJs,KTs,QJs,JTs,T9s,98s,87s,76s",
                ip_range="AA,KK,QQ,JJ,TT,99,AKs,AKo,A8s,K8s,Q8s",
                starting_pot=40.0,
                effective_stack=60.0,
                bet_tree=SolverBetTree(
                    oop=PlayerSizings(river=StreetSizings(bet=[75.0], allin=True)),
                    ip=PlayerSizings(river=StreetSizings(bet=[75.0], raise_=[100.0], allin=True)),
                ),
                max_iterations=300,
                target_exploitability=0.5,
                report_every=50,
            ),
        },
        {
            "name": "Turn Barrel (Single-Raised Pot)",
            "description": "Turn continuation betting on Js 8c 4d 2h with top pair, overpairs, and straight draws.",
            "config": SolverConfig(
                board="Js 8c 4d 2h",
                oop_range="QQ,JJ,88,44,AJs,KJs,QJs,JTs,T9s,98s,87s,76s,65s,AJo,KJo",
                ip_range="AA,KK,QQ,JJ,88,44,AJs,ATs,A8s,KJs,KTs,QJs,JTs,T9s,98s,AKo,AQo",
                starting_pot=12.0,
                effective_stack=94.0,
                bet_tree=SolverBetTree(
                    oop=PlayerSizings(
                        turn=StreetSizings(bet=[66.0], allin=False),
                        river=StreetSizings(bet=[75.0], allin=True),
                    ),
                    ip=PlayerSizings(
                        turn=StreetSizings(bet=[66.0], raise_=[60.0], allin=False),
                        river=StreetSizings(bet=[75.0], raise_=[60.0], allin=True),
                    ),
                ),
                max_iterations=400,
                target_exploitability=0.5,
                report_every=50,
            ),
        },
        {
            "name": "Turn Check/Call (Wet Draw-Heavy Board)",
            "description": "Turn check/call decision on Th 9h 6c 2d facing bet with draw vs made straights and sets.",
            "config": SolverConfig(
                board="Th 9h 6c 2d",
                oop_range="TT,99,66,22,JTs,T9s,98s,87s,76s,AhKh,KhQh,QhJh,JhTh,8h7h,7h6h",
                ip_range="AA,KK,QQ,JJ,TT,99,66,ATs,KTs,QTs,JTs,T9s,98s,87s,76s,AhJh,KhJh",
                starting_pot=15.0,
                effective_stack=92.5,
                bet_tree=SolverBetTree(
                    oop=PlayerSizings(
                        turn=StreetSizings(bet=[75.0], allin=False),
                        river=StreetSizings(bet=[75.0], allin=True),
                    ),
                    ip=PlayerSizings(
                        turn=StreetSizings(bet=[75.0], allin=False),
                        river=StreetSizings(bet=[75.0], allin=True),
                    ),
                ),
                max_iterations=400,
                target_exploitability=0.5,
                report_every=50,
            ),
        },
        {
            "name": "Flop Continuation-Bet (Dry King-High)",
            "description": "Compact flop solve on Ks 7d 2c with 33% c-bet sizing, multi-street runout validation.",
            "config": SolverConfig(
                board="Ks 7d 2c",
                oop_range="AA,KK,77,22,AKs,KQs,KJs,KTs,76s,65s,54s,AKo,KQo",
                ip_range="AA,KK,QQ,JJ,TT,77,22,AKs,A7s,A2s,KQs,KJs,KTs,QJs,JTs,T9s,98s,87s,76s,AKo",
                starting_pot=6.0,
                effective_stack=40.0,
                bet_tree=SolverBetTree(
                    oop=PlayerSizings(
                        flop=StreetSizings(bet=[33.0], allin=False),
                        turn=StreetSizings(bet=[66.0], allin=False),
                        river=StreetSizings(bet=[75.0], allin=True),
                    ),
                    ip=PlayerSizings(
                        flop=StreetSizings(bet=[33.0], allin=False),
                        turn=StreetSizings(bet=[66.0], allin=False),
                        river=StreetSizings(bet=[75.0], allin=True),
                    ),
                ),
                max_iterations=300,
                target_exploitability=0.5,
                report_every=50,
            ),
        },
    ]

    print(f"Generating {len(starter_configs)} reference strategy packs...")
    manifest = []

    for idx, item in enumerate(starter_configs, 1):
        name = item["name"]
        desc = item["description"]
        config: SolverConfig = item["config"]
        key = config.canonical_hash()

        print(f"\n[{idx}/{len(starter_configs)}] Solving '{name}' (board: {config.board})...")
        t0 = time.perf_counter()
        result = await adapter.solve(config)
        elapsed = time.perf_counter() - t0

        print(
            f"   Finished in {elapsed:.2f}s | Iterations: {result.iterations} | "
            f"Exploitability: {result.exploitability_chips:.6f} chips ({result.exploitability_pct_of_pot:.4f}% of pot) | "
            f"Status: {result.status.value}"
        )
        print(
            f"   Artifact: {result.solution_artifact_path} ({result.solution_bytes} bytes, SHA256: {result.solution_checksum[:12]}...)"
        )

        pack = StrategyPack(
            id=key[:16],
            name=name,
            description=desc,
            scenario_key=key,
            board=config.board,
            oop_range=config.oop_range,
            ip_range=config.ip_range,
            starting_pot=config.starting_pot,
            effective_stack=config.effective_stack,
            bet_tree=config.bet_tree.to_dict(),
            iterations=result.iterations,
            exploitability_chips=result.exploitability_chips,
            exploitability_pct_of_pot=result.exploitability_pct_of_pot,
            root_evs=result.root_evs,
            artifact_path=result.solution_artifact_path,
            artifact_checksum=result.solution_checksum,
            artifact_bytes=result.solution_bytes,
            node_count=result.node_count,
            engine_version=result.engine_metadata.version,
            engine_commit=result.engine_metadata.commit,
            validation_status=result.status,
        )

        manifest.append(pack.to_summary_dict())

        # Also persist to database if available
        try:
            async with SqlAlchemyUnitOfWork(session_factory) as uow:
                await uow.strategy_packs.save(pack)
                await uow.commit()
            print("   Saved to database.")
        except Exception as exc:
            print(f"   Database note (table might not exist before migration): {exc}")

    manifest_path = Path("data/solutions/manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nManifest written to {manifest_path} with {len(manifest)} starter packs.")


if __name__ == "__main__":
    asyncio.run(main())
