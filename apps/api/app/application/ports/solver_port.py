"""SolverAdapter interface port.

Decouples application orchestration from the underlying equilibrium solving engine.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from app.domain.poker.solver_types import (
    ConvergenceMetrics,
    EngineMetadata,
    HandStrategy,
    NodeStrategy,
    ResourceEstimate,
    SolverConfig,
    SolverProgress,
    SolverResult,
    ValidationResult,
)


class SolverAdapter(Protocol):
    """Protocol for poker equilibrium solvers."""

    def validate_configuration(self, config: SolverConfig) -> ValidationResult:
        """Validate scenario configuration for syntax, card removal, and tree bounds."""
        ...

    def estimate_resources(self, config: SolverConfig) -> ResourceEstimate:
        """Estimate tree size, memory usage, and runtime."""
        ...

    def create_game_tree(self, config: SolverConfig) -> int:
        """Construct the solver's betting tree and return total node count."""
        ...

    async def solve(
        self,
        config: SolverConfig,
        job_id: str | None = None,
        cancel_event: asyncio.Event | None = None,
        on_progress: Callable[[SolverProgress], Awaitable[None]] | None = None,
    ) -> SolverResult:
        """Execute equilibrium solving to convergence or resource limit."""
        ...

    def cancel(self, job_id: str) -> bool:
        """Signal cancellation to a currently running solve job."""
        ...

    def extract_strategy(
        self, solution_data: dict[str, Any], node_id: int, combo: str
    ) -> HandStrategy:
        """Extract action frequencies for a specific hand combo at a decision node."""
        ...

    def extract_node_strategy(self, solution_data: dict[str, Any], node_id: int) -> NodeStrategy:
        """Extract strategy matrix for all combos at a decision node."""
        ...

    def extract_action_evs(
        self, solution_data: dict[str, Any], node_id: int, combo: str
    ) -> list[float] | None:
        """Extract counterfactual action EVs for a specific combo if available."""
        ...

    def extract_convergence_metrics(self, solution_data: dict[str, Any]) -> ConvergenceMetrics:
        """Extract verified exploitability and EV convergence measurements."""
        ...

    def serialize_solution(self, solution_data: dict[str, Any]) -> bytes:
        """Serialize solution to canonical storage format."""
        ...

    def deserialize_solution(self, data: bytes) -> dict[str, Any]:
        """Deserialize solution from storage format."""
        ...

    def get_engine_metadata(self) -> EngineMetadata:
        """Return engine metadata including version, commit, and algorithm details."""
        ...
