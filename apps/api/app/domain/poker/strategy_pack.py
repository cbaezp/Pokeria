"""Strategy Pack domain entity for persistent reference solutions.

Versioned, content-addressed solution packages with verifiable SHA-256 integrity.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.domain.poker.solver_types import RootEvs, SolverStatus


@dataclass
class StrategyPack:
    """A persistent, versioned solution pack containing a solved poker scenario."""

    id: str  # content-addressed hash or unique slug
    name: str
    description: str
    scenario_key: str
    board: str
    oop_range: str
    ip_range: str
    starting_pot: float
    effective_stack: float
    bet_tree: dict[str, Any]
    iterations: int
    exploitability_chips: float
    exploitability_pct_of_pot: float
    root_evs: RootEvs
    artifact_path: str
    artifact_checksum: str
    artifact_bytes: int
    node_count: int
    engine_version: str
    engine_commit: str
    validation_status: SolverStatus
    game_type: str = "CASH"  # "CASH" or "TOURNAMENT"
    table_context: str = "heads_up"
    hero_position: str = "OOP"
    villain_position: str = "IP"
    payoff_unit: str = "chips"  # "chips" or "cste"
    rake_percent: float = 0.0
    rake_cap: float = 0.0
    ante: float = 0.0
    tournament_context: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def verify_artifact_integrity(self, base_dir: Path | str | None = None) -> bool:
        """Verify the disk artifact exists, matches size, and has identical SHA-256 hash."""
        path = Path(self.artifact_path)
        if not path.is_absolute() and base_dir is not None:
            path = Path(base_dir) / path

        if not path.exists() or not path.is_file():
            return False

        hasher = hashlib.sha256()
        total_bytes = 0
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
                total_bytes += len(chunk)

        computed_digest = hasher.hexdigest()
        return computed_digest == self.artifact_checksum and total_bytes == self.artifact_bytes

    def to_summary_dict(self) -> dict[str, Any]:
        """Serialize metadata for listing and inspection."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "scenario_key": self.scenario_key,
            "board": self.board,
            "oop_range": self.oop_range,
            "ip_range": self.ip_range,
            "starting_pot": self.starting_pot,
            "effective_stack": self.effective_stack,
            "iterations": self.iterations,
            "exploitability_chips": self.exploitability_chips,
            "exploitability_pct_of_pot": self.exploitability_pct_of_pot,
            "root_evs": {
                "oop_zero_sum": self.root_evs.oop_zero_sum,
                "ip_zero_sum": self.root_evs.ip_zero_sum,
                "oop_pot_share": self.root_evs.oop_pot_share,
                "ip_pot_share": self.root_evs.ip_pot_share,
            },
            "node_count": self.node_count,
            "engine_version": self.engine_version,
            "engine_commit": self.engine_commit,
            "validation_status": self.validation_status.value,
            "game_type": self.game_type,
            "table_context": self.table_context,
            "hero_position": self.hero_position,
            "villain_position": self.villain_position,
            "payoff_unit": self.payoff_unit,
            "rake_percent": self.rake_percent,
            "rake_cap": self.rake_cap,
            "ante": self.ante,
            "tournament_context": self.tournament_context,
            "artifact_path": self.artifact_path,
            "artifact_checksum": self.artifact_checksum,
            "artifact_bytes": self.artifact_bytes,
            "created_at": self.created_at.isoformat(),
        }
