"""SQLAlchemy StrategyPack ORM model."""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.poker.solver_types import RootEvs, SolverStatus
from app.domain.poker.strategy_pack import StrategyPack
from app.infrastructure.database.models.base import Base, TimestampMixin


class StrategyPackModel(Base, TimestampMixin):
    """Strategy pack metadata table model for solved poker scenarios."""

    __tablename__ = "strategy_packs"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    scenario_key: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    board: Mapped[str] = mapped_column(String(100), nullable=False)
    oop_range: Mapped[str] = mapped_column(Text, nullable=False)
    ip_range: Mapped[str] = mapped_column(Text, nullable=False)
    starting_pot: Mapped[float] = mapped_column(Float, nullable=False)
    effective_stack: Mapped[float] = mapped_column(Float, nullable=False)
    bet_tree: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    iterations: Mapped[int] = mapped_column(Integer, nullable=False)
    exploitability_chips: Mapped[float] = mapped_column(Float, nullable=False)
    exploitability_pct_of_pot: Mapped[float] = mapped_column(Float, nullable=False)
    root_ev_oop_zero_sum: Mapped[float] = mapped_column(Float, nullable=False)
    root_ev_ip_zero_sum: Mapped[float] = mapped_column(Float, nullable=False)
    root_ev_oop_pot_share: Mapped[float] = mapped_column(Float, nullable=False)
    root_ev_ip_pot_share: Mapped[float] = mapped_column(Float, nullable=False)
    artifact_path: Mapped[str] = mapped_column(String(512), nullable=False)
    artifact_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    artifact_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    node_count: Mapped[int] = mapped_column(Integer, nullable=False)
    engine_version: Mapped[str] = mapped_column(String(50), nullable=False)
    engine_commit: Mapped[str] = mapped_column(String(50), nullable=False)
    validation_status: Mapped[str] = mapped_column(String(50), default="VALIDATED", nullable=False)
    game_type: Mapped[str] = mapped_column(String(32), default="CASH", nullable=False)
    table_context: Mapped[str] = mapped_column(String(32), default="heads_up", nullable=False)
    hero_position: Mapped[str] = mapped_column(String(32), default="OOP", nullable=False)
    villain_position: Mapped[str] = mapped_column(String(32), default="IP", nullable=False)
    payoff_unit: Mapped[str] = mapped_column(String(32), default="chips", nullable=False)
    rake_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    rake_cap: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    ante: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tournament_context: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    def to_domain(self) -> StrategyPack:
        """Map ORM model to domain entity."""
        return StrategyPack(
            id=self.id,
            name=self.name,
            description=self.description,
            scenario_key=self.scenario_key,
            board=self.board,
            oop_range=self.oop_range,
            ip_range=self.ip_range,
            starting_pot=self.starting_pot,
            effective_stack=self.effective_stack,
            bet_tree=self.bet_tree,
            iterations=self.iterations,
            exploitability_chips=self.exploitability_chips,
            exploitability_pct_of_pot=self.exploitability_pct_of_pot,
            root_evs=RootEvs(
                oop_zero_sum=self.root_ev_oop_zero_sum,
                ip_zero_sum=self.root_ev_ip_zero_sum,
                oop_pot_share=self.root_ev_oop_pot_share,
                ip_pot_share=self.root_ev_ip_pot_share,
            ),
            artifact_path=self.artifact_path,
            artifact_checksum=self.artifact_checksum,
            artifact_bytes=self.artifact_bytes,
            node_count=self.node_count,
            engine_version=self.engine_version,
            engine_commit=self.engine_commit,
            validation_status=SolverStatus(self.validation_status),
            game_type=getattr(self, "game_type", "CASH"),
            table_context=getattr(self, "table_context", "heads_up"),
            hero_position=getattr(self, "hero_position", "OOP"),
            villain_position=getattr(self, "villain_position", "IP"),
            payoff_unit=getattr(self, "payoff_unit", "chips"),
            rake_percent=getattr(self, "rake_percent", 0.0),
            rake_cap=getattr(self, "rake_cap", 0.0),
            ante=getattr(self, "ante", 0.0),
            tournament_context=getattr(self, "tournament_context", None),
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, pack: StrategyPack) -> StrategyPackModel:
        """Create ORM model from domain entity."""
        return cls(
            id=pack.id,
            name=pack.name,
            description=pack.description,
            scenario_key=pack.scenario_key,
            board=pack.board,
            oop_range=pack.oop_range,
            ip_range=pack.ip_range,
            starting_pot=pack.starting_pot,
            effective_stack=pack.effective_stack,
            bet_tree=pack.bet_tree,
            iterations=pack.iterations,
            exploitability_chips=pack.exploitability_chips,
            exploitability_pct_of_pot=pack.exploitability_pct_of_pot,
            root_ev_oop_zero_sum=pack.root_evs.oop_zero_sum,
            root_ev_ip_zero_sum=pack.root_evs.ip_zero_sum,
            root_ev_oop_pot_share=pack.root_evs.oop_pot_share,
            root_ev_ip_pot_share=pack.root_evs.ip_pot_share,
            artifact_path=pack.artifact_path,
            artifact_checksum=pack.artifact_checksum,
            artifact_bytes=pack.artifact_bytes,
            node_count=pack.node_count,
            engine_version=pack.engine_version,
            engine_commit=pack.engine_commit,
            validation_status=pack.validation_status.value,
            game_type=pack.game_type,
            table_context=pack.table_context,
            hero_position=pack.hero_position,
            villain_position=pack.villain_position,
            payoff_unit=pack.payoff_unit,
            rake_percent=pack.rake_percent,
            rake_cap=pack.rake_cap,
            ante=pack.ante,
            tournament_context=pack.tournament_context,
        )
