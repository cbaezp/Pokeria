"""Unit tests for TrainingSession aggregate root state transitions and scenario scheduling."""

import pytest

from app.domain.training.models import (
    SessionStatus,
    TrainingMode,
    TrainingSession,
)
from app.domain.training.scenario_generator import catalog


class TestTrainingSessionLifecycle:
    """State transition tests for TrainingSession."""

    def test_session_creation_and_initial_state(self) -> None:
        session = TrainingSession.create(
            profile_id="prof-123",
            mode=TrainingMode.GUIDED,
            target_decisions=5,
            scenarios_sequence=["sc1", "sc2", "sc3", "sc4", "sc5"],
        )
        assert session.status == SessionStatus.ACTIVE
        assert session.completed_decisions == 0
        assert session.current_scenario_id == "sc1"
        assert session.target_decisions == 5

    def test_pause_and_resume_transitions(self) -> None:
        session = TrainingSession.create(
            profile_id="prof-123",
            mode=TrainingMode.BLIND,
            target_decisions=3,
            scenarios_sequence=["sc1", "sc2", "sc3"],
        )
        session.pause()
        assert session.status == SessionStatus.PAUSED

        # Cannot pause while paused
        with pytest.raises(ValueError, match="Cannot pause session in PAUSED state"):
            session.pause()

        session.resume()
        assert session.status == SessionStatus.ACTIVE

        # Cannot resume while active
        with pytest.raises(ValueError, match="Cannot resume session in ACTIVE state"):
            session.resume()

    def test_advance_and_completion_lifecycle(self) -> None:
        session = TrainingSession.create(
            profile_id="prof-123",
            mode=TrainingMode.GUIDED,
            target_decisions=2,
            scenarios_sequence=["sc1", "sc2"],
        )
        next_sc = session.advance()
        assert session.completed_decisions == 1
        assert session.status == SessionStatus.ACTIVE
        assert next_sc == "sc2"
        assert session.current_scenario_id == "sc2"

        final_sc = session.advance()
        assert session.completed_decisions == 2
        assert session.status == SessionStatus.COMPLETED
        assert final_sc is None
        assert session.current_scenario_id is None
        assert session.completed_at is not None

    def test_seeded_scenario_sequence_reproducibility(self) -> None:
        catalog.initialize()
        seq1 = catalog.select_scenarios_sequence(count=10, seed=42)
        seq2 = catalog.select_scenarios_sequence(count=10, seed=42)
        assert seq1 == seq2
        assert len(seq1) == 10
