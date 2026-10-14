"""Assessment and Spaced Repetition Domain Models.

Defines:
- Assessment tiers (Tiers 1-5) and capability gates.
- Strict session lifecycle states.
- Assessment items with immutable solver-backed provenance.
- Clean vs contaminated delayed-retention evaluation.
- Rule-based spaced repetition scheduling with versioned review-success policies.
- Injectable clock interface for deterministic time simulation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol

from app.domain.training.models import (
    ActionEVItem,
    LegalAction,
    ScenarioFamily,
)

ITEM_BANK_VERSION: str = "v1.0.0"
SCORING_VERSION: str = "v2.0_solver_ev"
REVIEW_POLICY_VERSION: str = "v2.0_combined_and"

# Standard heuristic intervals in days
HEURISTIC_INTERVAL_SEQUENCE: tuple[int, ...] = (1, 3, 7, 14, 30)

# Math-based thresholds matching target policy v2.0_combined_and
CHIP_MISTAKE_THRESHOLD: float = 0.50
POT_NORMALIZED_MISTAKE_THRESHOLD: float = 0.02
EXCELLENT_EV_LOSS_TOLERANCE: float = 0.10


class AssessmentTier(StrEnum):
    """Rigorous categorization of assessment scope and generalization claims."""

    TIER1_RETEST = "TIER1_RETEST"
    TIER2_HELD_OUT_COMBO = "TIER2_HELD_OUT_COMBO"
    TIER3_HELD_OUT_NODE = "TIER3_HELD_OUT_NODE"
    TIER4_HELD_OUT_BOARD = "TIER4_HELD_OUT_BOARD"
    TIER5_BROAD_TRANSFER = "TIER5_BROAD_TRANSFER"


class AssessmentSessionStatus(StrEnum):
    """Strict state machine for assessment sessions."""

    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    SUBMITTED = "SUBMITTED"
    GRADED = "GRADED"
    INVALIDATED = "INVALIDATED"
    ABANDONED = "ABANDONED"


class AssessmentMode(StrEnum):
    """Context and execution purpose of the assessment."""

    BLIND_ASSESSMENT = "BLIND_ASSESSMENT"
    RETENTION_REVIEW = "RETENTION_REVIEW"
    PRETEST = "PRETEST"
    POSTTEST = "POSTTEST"


class PriorExposureStatus(StrEnum):
    """Point-in-time exposure classification relative to the user's prior history."""

    NO_PRIOR_EXPOSURE = "NO_PRIOR_EXPOSURE"
    EXACT_SCENARIO_EXPOSED = "EXACT_SCENARIO_EXPOSED"
    NODE_EXPOSED = "NODE_EXPOSED"
    BOARD_EXPOSED = "BOARD_EXPOSED"


class ContaminationReason(StrEnum):
    """Reason why an assessment observation is flagged as contaminated."""

    NONE = "NONE"
    INTERVENING_EXACT_SCENARIO_TRAINING = "INTERVENING_EXACT_SCENARIO_TRAINING"
    INTERVENING_NODE_PRACTICE = "INTERVENING_NODE_PRACTICE"
    INTERVENING_BOARD_PRACTICE = "INTERVENING_BOARD_PRACTICE"
    CONCURRENT_TRAINING_RESERVATION_VIOLATION = "CONCURRENT_TRAINING_RESERVATION_VIOLATION"


class ReviewSuccessClassification(StrEnum):
    """Deterministic, EV-loss-based review outcome classification."""

    SUCCESSFUL = "SUCCESSFUL"
    PARTIALLY_SUCCESSFUL = "PARTIALLY_SUCCESSFUL"
    UNSUCCESSFUL = "UNSUCCESSFUL"
    UNGRADED = "UNGRADED"


class Clock(Protocol):
    """Injectable clock protocol for deterministic testing of elapsed intervals."""

    def now(self) -> datetime: ...


class SystemClock:
    """Production clock returning current UTC datetime."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class FrozenClock:
    """Deterministic test clock with settable and advanceable UTC time."""

    def __init__(self, current_time: datetime | None = None) -> None:
        if current_time is None:
            self._time = datetime(2026, 10, 9, 12, 0, 0, tzinfo=UTC)
        elif current_time.tzinfo is None:
            self._time = current_time.replace(tzinfo=UTC)
        else:
            self._time = current_time

    def now(self) -> datetime:
        return self._time

    def advance(self, **kwargs: Any) -> None:
        from datetime import timedelta

        self._time += timedelta(**kwargs)

    def set_time(self, new_time: datetime) -> None:
        if new_time.tzinfo is None:
            self._time = new_time.replace(tzinfo=UTC)
        else:
            self._time = new_time


@dataclass(frozen=True)
class AssessmentItem:
    """Immutable assessment item abstraction referencing authoritative solver data."""

    id: str
    scenario_id: str
    strategy_pack_id: str
    strategy_pack_checksum: str
    solver_node_id: int
    combo: str
    board: list[str]
    hero_position: str
    villain_position: str
    pot: float
    effective_stack: float
    action_history: list[dict[str, Any]]
    legal_actions: list[LegalAction]
    reference_actions: list[ActionEVItem]
    scenario_family: ScenarioFamily
    street: str
    grading_algorithm_version: str = "v1.0.0"
    item_bank_version: str = ITEM_BANK_VERSION
    validation_status: str = "VALIDATED"
    payoff_unit: str = "chips"  # "chips" or "cste"
    supported_tiers: list[AssessmentTier] = field(default_factory=list)
    is_quarantined: bool = False
    difficulty_metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def board_str(self) -> str:
        return " ".join(self.board)

    def to_blind_dict(self) -> dict[str, Any]:
        """Strictly redacted representation for blind assessment mode.

        MUST NOT contain reference_actions, chosen EVs, solver frequencies, or hints.
        """
        return {
            "id": self.id,
            "scenario_id": self.scenario_id,
            "combo": self.combo,
            "board": self.board,
            "hero_position": self.hero_position,
            "villain_position": self.villain_position,
            "pot": self.pot,
            "effective_stack": self.effective_stack,
            "action_history": self.action_history,
            "legal_actions": [a.to_dict() for a in self.legal_actions],
            "scenario_family": self.scenario_family.value,
            "street": self.street,
            "supported_tiers": [t.value for t in self.supported_tiers],
        }


@dataclass
class AssessmentResponse:
    """Individual response to an assessment item with full provenance and delayed grading."""

    id: str
    session_id: str
    item_id: str
    item_index: int
    chosen_action: str
    chosen_amount: float | None
    latency_ms: int
    confidence_score: int | None
    submitted_at: datetime
    prior_exposure: PriorExposureStatus = PriorExposureStatus.NO_PRIOR_EXPOSURE
    is_contaminated: bool = False
    contamination_reason: ContaminationReason = ContaminationReason.NONE
    elapsed_since_exposure_seconds: float | None = None
    chosen_ev: float | None = None
    best_ev: float | None = None
    ev_loss: float | None = None
    grade: str | None = None
    is_material_mistake: bool | None = None
    review_success: ReviewSuccessClassification | None = None

    def to_dict(self, include_grades: bool = False) -> dict[str, Any]:
        base = {
            "id": self.id,
            "session_id": self.session_id,
            "item_id": self.item_id,
            "item_index": self.item_index,
            "chosen_action": self.chosen_action,
            "chosen_amount": self.chosen_amount,
            "latency_ms": self.latency_ms,
            "confidence_score": self.confidence_score,
            "submitted_at": self.submitted_at.isoformat(),
            "prior_exposure": self.prior_exposure.value,
            "is_contaminated": self.is_contaminated,
            "contamination_reason": self.contamination_reason.value,
            "elapsed_since_exposure_seconds": self.elapsed_since_exposure_seconds,
        }
        if include_grades:
            base.update(
                {
                    "chosen_ev": self.chosen_ev,
                    "best_ev": self.best_ev,
                    "ev_loss": self.ev_loss,
                    "grade": self.grade,
                    "is_material_mistake": self.is_material_mistake,
                    "review_success": self.review_success.value if self.review_success else None,
                }
            )
        return base


@dataclass
class AssessmentSession:
    """Session managing assessment lifecycle, item reservation, and delayed reveal."""

    id: str
    profile_id: str
    tier: AssessmentTier
    mode: AssessmentMode
    status: AssessmentSessionStatus
    item_bank_version: str
    scoring_version: str
    item_ids: list[str]
    current_index: int = 0
    seed: int | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    submitted_at: datetime | None = None
    graded_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    responses: list[AssessmentResponse] = field(default_factory=list)

    @property
    def total_items(self) -> int:
        return len(self.item_ids)

    @property
    def is_completed(self) -> bool:
        return self.status in (
            AssessmentSessionStatus.SUBMITTED,
            AssessmentSessionStatus.GRADED,
            AssessmentSessionStatus.INVALIDATED,
            AssessmentSessionStatus.ABANDONED,
        )

    def to_blind_dict(self, active_item: AssessmentItem | None = None) -> dict[str, Any]:
        """User-facing view during active assessment with answer-bearing values withheld."""
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "tier": self.tier.value,
            "mode": self.mode.value,
            "status": self.status.value,
            "item_bank_version": self.item_bank_version,
            "total_items": self.total_items,
            "current_index": self.current_index,
            "is_completed": self.is_completed,
            "started_at": self.started_at.isoformat(),
            "current_item": active_item.to_blind_dict() if active_item else None,
            "progress_pct": (self.current_index / self.total_items * 100.0)
            if self.total_items > 0
            else 0.0,
        }


@dataclass
class ReviewSchedule:
    """Spaced repetition scheduling record with explicit UTC timestamps and heuristic intervals."""

    id: str
    profile_id: str
    item_id: str
    scenario_id: str
    scenario_family: str
    review_count: int = 0
    consecutive_successes: int = 0
    interval_days: int = 1
    next_due_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_exposure_at: datetime | None = None
    last_graded_attempt_at: datetime | None = None
    last_feedback_at: datetime | None = None
    recent_ev_loss: float | None = None
    policy_version: str = REVIEW_POLICY_VERSION
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def is_due(self, as_of: datetime) -> bool:
        t_as_of = as_of if as_of.tzinfo is not None else as_of.replace(tzinfo=UTC)
        t_due = (
            self.next_due_at
            if self.next_due_at.tzinfo is not None
            else self.next_due_at.replace(tzinfo=UTC)
        )
        return t_as_of >= t_due

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "item_id": self.item_id,
            "scenario_id": self.scenario_id,
            "scenario_family": self.scenario_family,
            "review_count": self.review_count,
            "consecutive_successes": self.consecutive_successes,
            "interval_days": self.interval_days,
            "next_due_at": self.next_due_at.isoformat(),
            "last_exposure_at": self.last_exposure_at.isoformat()
            if self.last_exposure_at
            else None,
            "last_graded_attempt_at": self.last_graded_attempt_at.isoformat()
            if self.last_graded_attempt_at
            else None,
            "recent_ev_loss": self.recent_ev_loss,
            "policy_version": self.policy_version,
        }


@dataclass
class AssessmentReservation:
    """Temporary reservation preventing candidate assessment items from leaking into training."""

    id: str
    profile_id: str
    session_id: str
    item_id: str
    reserved_at: datetime
    expires_at: datetime
    is_active: bool = True


@dataclass
class CapabilityGateResult:
    """Evaluated capability gate for an assessment tier given current curriculum coverage."""

    tier: AssessmentTier
    is_supported: bool
    available_item_count: int
    minimum_required_items: int
    distinct_boards_count: int
    distinct_nodes_count: int
    rejection_code: str | None
    reason: str
    curriculum_summary: dict[str, Any] = field(default_factory=dict)
