"""Application use cases for solver integration and strategy library."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.application.dtos import JobResponseDTO
from app.application.ports.solver_port import SolverAdapter
from app.application.ports.unit_of_work import UnitOfWork
from app.core.logging import get_logger
from app.domain.entities.job import Job, JobStatus
from app.domain.exceptions import EntityNotFoundError, ValidationError
from app.domain.poker.solver_types import (
    ResourceEstimate,
    SolverConfig,
    ValidationResult,
)

logger = get_logger(__name__)


class GetSolverCapabilitiesUseCase:
    """Return engine capabilities and constraints."""

    def __init__(self, adapter: SolverAdapter) -> None:
        self.adapter = adapter

    def execute(self) -> dict[str, Any]:
        meta = self.adapter.get_engine_metadata()
        return {
            "name": meta.name,
            "version": meta.version,
            "commit": meta.commit,
            "license": meta.license,
            "algorithm": meta.algorithm,
            "supported_streets": meta.supported_streets,
            "measured_convergence": meta.measured_convergence,
            "supported_features": {
                "heads_up_postflop": True,
                "vectorized_dcfr": True,
                "measured_exploitability": True,
                "exact_card_removal": True,
                "i16_quantized_storage": True,
                "multiway_solving": False,
                "preflop_solving": False,
            },
        }


class ValidateSolverConfigUseCase:
    """Validate a solver configuration."""

    def __init__(self, adapter: SolverAdapter) -> None:
        self.adapter = adapter

    def execute(self, config: SolverConfig) -> ValidationResult:
        return self.adapter.validate_configuration(config)


class EstimateSolverResourcesUseCase:
    """Estimate compute resources for a solver configuration."""

    def __init__(self, adapter: SolverAdapter) -> None:
        self.adapter = adapter

    def execute(self, config: SolverConfig) -> ResourceEstimate:
        return self.adapter.estimate_resources(config)


class CreateSolverJobUseCase:
    """Enqueue a durable background solve job."""

    def __init__(self, uow: UnitOfWork, adapter: SolverAdapter) -> None:
        self.uow = uow
        self.adapter = adapter

    async def execute(
        self,
        config: SolverConfig,
        pack_name: str | None = None,
        pack_description: str | None = None,
    ) -> dict[str, Any]:
        validation = self.adapter.validate_configuration(config)
        if not validation.valid:
            raise ValidationError(f"Invalid solver configuration: {'; '.join(validation.errors)}")

        scenario_key = config.canonical_hash()

        # Check if already solved and verified
        async with self.uow:
            existing_pack = await self.uow.strategy_packs.get_by_scenario_key(scenario_key)
            if existing_pack and existing_pack.verify_artifact_integrity():
                logger.info(f"Reusing existing solution pack {existing_pack.id} for {scenario_key}")
                return {
                    "job_id": None,
                    "status": "COMPLETED",
                    "scenario_key": scenario_key,
                    "pack": existing_pack.to_summary_dict(),
                    "reused": True,
                }

            # Create durable background job
            payload = {
                "solver_config": config.canonical_dict(),
                "pack_name": pack_name or f"Spot {config.board}",
                "pack_description": pack_description or "Equilibrium reference solve",
            }
            job = Job.create(
                job_type="solve_scenario",
                payload=payload,
                idempotency_key=f"solve-{scenario_key}",
            )
            saved_job = await self.uow.jobs.save(job)
            await self.uow.commit()

            return {
                "job_id": saved_job.id,
                "status": saved_job.status.value,
                "scenario_key": scenario_key,
                "reused": False,
            }


class GetSolverJobStatusUseCase:
    """Fetch status and result of a solver job."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, job_id: str) -> JobResponseDTO:
        async with self.uow:
            job = await self.uow.jobs.get_by_id(job_id)
            if job is None:
                raise EntityNotFoundError("Job", job_id)
            return JobResponseDTO.from_entity(job)


class CancelSolverJobUseCase:
    """Cancel a pending or running solver job."""

    def __init__(self, uow: UnitOfWork, adapter: SolverAdapter) -> None:
        self.uow = uow
        self.adapter = adapter

    async def execute(self, job_id: str) -> dict[str, Any]:
        self.adapter.cancel(job_id)
        async with self.uow:
            job = await self.uow.jobs.get_by_id(job_id)
            if job is None:
                raise EntityNotFoundError("Job", job_id)
            if job.status in (JobStatus.PENDING, JobStatus.RUNNING):
                job.mark_failed("Cancelled by user request")
                await self.uow.jobs.save(job)
                await self.uow.commit()
            return {"job_id": job_id, "status": job.status.value, "cancelled": True}


class ListStrategyPacksUseCase:
    """List reference strategy packs."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, limit: int = 50, offset: int = 0) -> dict[str, Any]:
        async with self.uow:
            packs = await self.uow.strategy_packs.list_packs(limit=limit, offset=offset)
            total = await self.uow.strategy_packs.count_packs()
            return {
                "items": [p.to_summary_dict() for p in packs],
                "total": total,
                "limit": limit,
                "offset": offset,
            }


class GetStrategyPackUseCase:
    """Inspect metadata and tree details of a strategy pack."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, pack_id: str) -> dict[str, Any]:
        async with self.uow:
            pack = await self.uow.strategy_packs.get_by_id(pack_id)
            if pack is None:
                raise EntityNotFoundError("StrategyPack", pack_id)

            summary = pack.to_summary_dict()
            # Check artifact existence and tree structure
            artifact_file = Path(pack.artifact_path)
            if artifact_file.is_file():
                try:
                    data = json.loads(artifact_file.read_text(encoding="utf-8"))
                    summary["nodes_summary"] = [
                        {
                            "node": n.get("node"),
                            "player": n.get("player"),
                            "actions": n.get("actions", []),
                            "combo_count": n.get("combo_count"),
                        }
                        for n in data.get("nodes", [])
                    ]
                    summary["root_combos"] = data.get("root_combos", [[], []])
                except Exception as exc:
                    logger.warning(f"Could not read artifact for pack {pack_id}: {exc}")
            return summary


class QueryStrategyDecisionUseCase:
    """Query equilibrium strategy for a specific hole card combination and decision node."""

    def __init__(self, uow: UnitOfWork, adapter: SolverAdapter) -> None:
        self.uow = uow
        self.adapter = adapter

    async def execute(
        self,
        pack_id: str,
        node_id: int,
        combo: str,
    ) -> dict[str, Any]:
        async with self.uow:
            pack = await self.uow.strategy_packs.get_by_id(pack_id)
            if pack is None:
                raise EntityNotFoundError("StrategyPack", pack_id)

        artifact_file = Path(pack.artifact_path)
        if not artifact_file.is_file():
            raise EntityNotFoundError("SolutionArtifact", pack.artifact_path)

        data = json.loads(artifact_file.read_text(encoding="utf-8"))
        hand_strategy = self.adapter.extract_strategy(data, node_id=node_id, combo=combo)

        return {
            "pack_id": pack_id,
            "node_id": node_id,
            "combo": hand_strategy.combo,
            "combo_index": hand_strategy.combo_index,
            "actions": [{"kind": a.kind, "amount": a.amount} for a in hand_strategy.actions],
            "frequencies": hand_strategy.frequencies,
            "action_evs": hand_strategy.action_evs,
            "expected_value": hand_strategy.expected_value,
        }


class QueryNodeStrategyUseCase:
    """Query complete strategy matrix for all combos at a decision node."""

    def __init__(self, uow: UnitOfWork, adapter: SolverAdapter) -> None:
        self.uow = uow
        self.adapter = adapter

    async def execute(self, pack_id: str, node_id: int) -> dict[str, Any]:
        async with self.uow:
            pack = await self.uow.strategy_packs.get_by_id(pack_id)
            if pack is None:
                raise EntityNotFoundError("StrategyPack", pack_id)

        artifact_file = Path(pack.artifact_path)
        if not artifact_file.is_file():
            raise EntityNotFoundError("SolutionArtifact", pack.artifact_path)

        data = json.loads(artifact_file.read_text(encoding="utf-8"))
        node_strat = self.adapter.extract_node_strategy(data, node_id=node_id)

        return {
            "pack_id": pack_id,
            "node_id": node_strat.node_id,
            "player": node_strat.player,
            "actions": [{"kind": a.kind, "amount": a.amount} for a in node_strat.actions],
            "combo_count": node_strat.combo_count,
            "combos": node_strat.combos,
            "strategy_by_combo": node_strat.strategy_by_combo,
        }


class VerifyStrategyPackIntegrityUseCase:
    """Verify artifact integrity and checksum for a strategy pack."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, pack_id: str) -> dict[str, Any]:
        async with self.uow:
            pack = await self.uow.strategy_packs.get_by_id(pack_id)
            if pack is None:
                raise EntityNotFoundError("StrategyPack", pack_id)

            intact = pack.verify_artifact_integrity()
            return {
                "pack_id": pack_id,
                "intact": intact,
                "artifact_path": pack.artifact_path,
                "expected_checksum": pack.artifact_checksum,
                "expected_bytes": pack.artifact_bytes,
            }


class DeleteStrategyPackUseCase:
    """Delete a strategy pack record and artifact."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, pack_id: str) -> dict[str, Any]:
        async with self.uow:
            pack = await self.uow.strategy_packs.get_by_id(pack_id)
            if pack is None:
                raise EntityNotFoundError("StrategyPack", pack_id)

            artifact_path = Path(pack.artifact_path)
            if artifact_path.is_file():
                try:
                    artifact_path.unlink()
                except Exception as exc:
                    logger.warning(f"Could not remove artifact {artifact_path}: {exc}")

            deleted = await self.uow.strategy_packs.delete(pack_id)
            await self.uow.commit()
            return {"pack_id": pack_id, "deleted": deleted}
