"""API endpoints for Training Game Configurations."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.domain.training.game_configuration import (
    ALL_CONFIGURATIONS,
    CONFIG_ONLINE_CASH_6MAX_100BB,
    list_configurations,
)

router = APIRouter(prefix="/training/configurations", tags=["configurations"])


class ConfigurationSummaryResponse(BaseModel):
    """Configuration serialization response model."""

    id: str
    name: str
    short_label: str
    game_type: str
    table_size: str
    environment: str
    effective_stack_bb: float
    small_blind_bb: float
    big_blind_bb: float
    ante_structure: str
    ante_bb: float
    rake_percent: float
    rake_cap_bb: float
    open_size_bb: float
    positions: list[str]
    description: str
    is_default: bool
    supported_skills: list[dict[str, Any]]
    tournament_stage: str | None = None


@router.get("", response_model=list[ConfigurationSummaryResponse])
async def get_all_configurations() -> list[dict[str, Any]]:
    """List all supported training game configurations."""
    configs = list_configurations()
    return [c.to_dict() for c in configs]


@router.get("/default", response_model=ConfigurationSummaryResponse)
async def get_default_configuration() -> dict[str, Any]:
    """Retrieve the platform default game configuration."""
    return CONFIG_ONLINE_CASH_6MAX_100BB.to_dict()


@router.get("/{config_id}", response_model=ConfigurationSummaryResponse)
async def get_single_configuration(config_id: str) -> dict[str, Any]:
    """Retrieve details for a specific game configuration."""
    if config_id not in ALL_CONFIGURATIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration '{config_id}' not found",
        )
    return ALL_CONFIGURATIONS[config_id].to_dict()
