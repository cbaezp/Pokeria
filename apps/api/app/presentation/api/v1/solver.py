"""FastAPI endpoints for GTO equilibrium solver integration and strategy packs."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.solver_use_cases import (
    CancelSolverJobUseCase,
    CreateSolverJobUseCase,
    DeleteStrategyPackUseCase,
    EstimateSolverResourcesUseCase,
    GetSolverCapabilitiesUseCase,
    GetSolverJobStatusUseCase,
    GetStrategyPackUseCase,
    ListStrategyPacksUseCase,
    QueryNodeStrategyUseCase,
    QueryStrategyDecisionUseCase,
    ValidateSolverConfigUseCase,
    VerifyStrategyPackIntegrityUseCase,
)
from app.domain.exceptions import EntityNotFoundError, ValidationError
from app.domain.poker.solver_types import (
    PlayerSizings,
    SolverBetTree,
    SolverConfig,
    StreetSizings,
)
from app.infrastructure.solver.subprocess_solver import SubprocessSolverAdapter
from app.presentation.api.dependencies import get_uow

router = APIRouter(prefix="/solver", tags=["solver"])


def get_solver_adapter() -> SubprocessSolverAdapter:
    """Dependency provider for SolverAdapter."""
    return SubprocessSolverAdapter()


# Pydantic Schemas
class StreetSizingsSchema(BaseModel):
    bet: list[float] = Field(default_factory=list, description="Bet percentages of pot")
    raise_: list[float] = Field(
        default_factory=list, alias="raise", description="Raise percentages of pot"
    )
    allin: bool = Field(default=True, description="Allow all-in action")


class PlayerSizingsSchema(BaseModel):
    flop: StreetSizingsSchema = Field(default_factory=StreetSizingsSchema)
    turn: StreetSizingsSchema = Field(default_factory=StreetSizingsSchema)
    river: StreetSizingsSchema = Field(default_factory=StreetSizingsSchema)


class SolverBetTreeSchema(BaseModel):
    oop: PlayerSizingsSchema = Field(default_factory=PlayerSizingsSchema)
    ip: PlayerSizingsSchema = Field(default_factory=PlayerSizingsSchema)


class SolverConfigSchema(BaseModel):
    board: str = Field(..., json_schema_extra={"example": "Ah Kd 2c 7s 9c"})
    oop_range: str = Field(..., json_schema_extra={"example": "AA,KK,QQ,JJ,AKs,AKo"})
    ip_range: str = Field(..., json_schema_extra={"example": "AA,KK,QQ,JJ,AKs,AKo"})
    starting_pot: float = Field(..., gt=0.0, json_schema_extra={"example": 20.0})
    effective_stack: float = Field(..., gt=0.0, json_schema_extra={"example": 50.0})
    bet_tree: SolverBetTreeSchema = Field(default_factory=SolverBetTreeSchema)
    max_iterations: int = Field(default=500, ge=1, le=50000)
    target_exploitability: float = Field(default=0.5, gt=0.0)
    report_every: int = Field(default=50, ge=1)
    allin_threshold: float = Field(default=67.0, ge=0.0)
    raise_cap: int = Field(default=3, ge=1)
    threads: int | None = Field(default=None)


class CreateSolverJobRequest(BaseModel):
    config: SolverConfigSchema
    pack_name: str | None = None
    pack_description: str | None = None


def schema_to_domain(s: SolverConfigSchema) -> SolverConfig:
    """Map Pydantic schema to typed domain object."""
    oop_sizings = PlayerSizings(
        flop=StreetSizings(
            bet=s.bet_tree.oop.flop.bet,
            raise_=s.bet_tree.oop.flop.raise_,
            allin=s.bet_tree.oop.flop.allin,
        ),
        turn=StreetSizings(
            bet=s.bet_tree.oop.turn.bet,
            raise_=s.bet_tree.oop.turn.raise_,
            allin=s.bet_tree.oop.turn.allin,
        ),
        river=StreetSizings(
            bet=s.bet_tree.oop.river.bet,
            raise_=s.bet_tree.oop.river.raise_,
            allin=s.bet_tree.oop.river.allin,
        ),
    )
    ip_sizings = PlayerSizings(
        flop=StreetSizings(
            bet=s.bet_tree.ip.flop.bet,
            raise_=s.bet_tree.ip.flop.raise_,
            allin=s.bet_tree.ip.flop.allin,
        ),
        turn=StreetSizings(
            bet=s.bet_tree.ip.turn.bet,
            raise_=s.bet_tree.ip.turn.raise_,
            allin=s.bet_tree.ip.turn.allin,
        ),
        river=StreetSizings(
            bet=s.bet_tree.ip.river.bet,
            raise_=s.bet_tree.ip.river.raise_,
            allin=s.bet_tree.ip.river.allin,
        ),
    )
    return SolverConfig(
        board=s.board,
        oop_range=s.oop_range,
        ip_range=s.ip_range,
        starting_pot=s.starting_pot,
        effective_stack=s.effective_stack,
        bet_tree=SolverBetTree(oop=oop_sizings, ip=ip_sizings),
        max_iterations=s.max_iterations,
        target_exploitability=s.target_exploitability,
        report_every=s.report_every,
        allin_threshold=s.allin_threshold,
        raise_cap=s.raise_cap,
        threads=s.threads,
    )


@router.get("/capabilities", summary="Get solver engine capabilities")
def get_capabilities(
    adapter: Annotated[SubprocessSolverAdapter, Depends(get_solver_adapter)],
) -> dict[str, Any]:
    """Return solver algorithm, version, and supported game features."""
    return GetSolverCapabilitiesUseCase(adapter).execute()


@router.post("/validate", summary="Validate solver scenario configuration")
def validate_config(
    body: SolverConfigSchema,
    adapter: Annotated[SubprocessSolverAdapter, Depends(get_solver_adapter)],
) -> dict[str, Any]:
    """Validate scenario syntax, board cards, ranges, and sizing constraints."""
    config = schema_to_domain(body)
    res = ValidateSolverConfigUseCase(adapter).execute(config)
    return {
        "valid": res.valid,
        "errors": res.errors,
        "warnings": res.warnings,
        "scenario_key": config.canonical_hash(),
    }


@router.post("/estimate", summary="Estimate required computational resources")
def estimate_resources(
    body: SolverConfigSchema,
    adapter: Annotated[SubprocessSolverAdapter, Depends(get_solver_adapter)],
) -> dict[str, Any]:
    """Estimate memory consumption, game tree size, and solve duration."""
    config = schema_to_domain(body)
    res = EstimateSolverResourcesUseCase(adapter).execute(config)
    return {
        "estimated_nodes": res.estimated_nodes,
        "estimated_memory_mb": res.estimated_memory_mb,
        "estimated_seconds": res.estimated_seconds,
        "feasible": res.feasible,
        "warnings": res.warnings,
    }


@router.post("/jobs", status_code=status.HTTP_202_ACCEPTED, summary="Enqueue solver background job")
async def create_solver_job(
    body: CreateSolverJobRequest,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    adapter: Annotated[SubprocessSolverAdapter, Depends(get_solver_adapter)],
) -> dict[str, Any]:
    """Enqueue a durable background equilibrium solve job."""
    config = schema_to_domain(body.config)
    try:
        return await CreateSolverJobUseCase(uow, adapter).execute(
            config,
            pack_name=body.pack_name,
            pack_description=body.pack_description,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/jobs/{job_id}", summary="Get status of a solver job")
async def get_solver_job(
    job_id: str,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> dict[str, Any]:
    """Poll solver background job progress and result."""
    try:
        dto = await GetSolverJobStatusUseCase(uow).execute(job_id)
        return dto.model_dump()
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/jobs/{job_id}/cancel", summary="Cancel a solver job")
async def cancel_solver_job(
    job_id: str,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    adapter: Annotated[SubprocessSolverAdapter, Depends(get_solver_adapter)],
) -> dict[str, Any]:
    """Cancel a pending or currently running solver job."""
    try:
        return await CancelSolverJobUseCase(uow, adapter).execute(job_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/packs", summary="List reference strategy packs")
async def list_strategy_packs(
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    uow: Annotated[UnitOfWork, Depends(get_uow)] = None,  # type: ignore
) -> dict[str, Any]:
    """List persisted solution packs with pagination."""
    return await ListStrategyPacksUseCase(uow).execute(limit=limit, offset=offset)


@router.get("/packs/{pack_id}", summary="Inspect a reference strategy pack")
async def get_strategy_pack(
    pack_id: str,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> dict[str, Any]:
    """Inspect full metadata and tree node summary of a solution pack."""
    try:
        return await GetStrategyPackUseCase(uow).execute(pack_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/packs/{pack_id}", summary="Delete a strategy pack")
async def delete_strategy_pack(
    pack_id: str,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> dict[str, Any]:
    """Delete a solution pack record and its on-disk artifact."""
    try:
        return await DeleteStrategyPackUseCase(uow).execute(pack_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/packs/{pack_id}/verify", summary="Verify integrity of a strategy pack")
async def verify_strategy_pack(
    pack_id: str,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> dict[str, Any]:
    """Verify artifact SHA-256 checksum and disk integrity."""
    try:
        return await VerifyStrategyPackIntegrityUseCase(uow).execute(pack_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/packs/{pack_id}/decision", summary="Query decision strategy for a hand combo")
async def query_decision(
    pack_id: str,
    node_id: Annotated[int, Query(ge=0)],
    combo: Annotated[str, Query(description="Hole card combination, e.g. AhKh")],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    adapter: Annotated[SubprocessSolverAdapter, Depends(get_solver_adapter)],
) -> dict[str, Any]:
    """Query exact equilibrium action frequencies for a combo at a decision node."""
    try:
        return await QueryStrategyDecisionUseCase(uow, adapter).execute(
            pack_id=pack_id, node_id=node_id, combo=combo
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/packs/{pack_id}/node/{node_id}", summary="Query complete strategy matrix for a node")
async def query_node_strategy(
    pack_id: str,
    node_id: int,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    adapter: Annotated[SubprocessSolverAdapter, Depends(get_solver_adapter)],
) -> dict[str, Any]:
    """Query strategy distributions for all combos at a decision node."""
    try:
        return await QueryNodeStrategyUseCase(uow, adapter).execute(
            pack_id=pack_id, node_id=node_id
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
