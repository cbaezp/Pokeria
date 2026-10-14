"""Statistical anti-leakage and synthetic profile tests.

Constructs synthetic decision histories representing Profiles A, B, C, D, E
to verify that analytics and data quality auditing prevent measurement leakage,
repetition inflation, and false claims of skill improvement:

- Profile A: Repeated scenario memorization with speed gains (repetition inflation risk)
- Profile B: Genuine multi-family practice with verified improvement
- Profile C: Scenario mix bias (apparent improvement explained by easier spots)
- Profile D: Heavy illustrative chart volume with few solver-graded decisions
- Profile E: Low-quality / unsupported strategy observations
"""

from app.domain.analytics.data_quality import (
    DataQualityReport,
    LeakageRiskLevel,
)
from app.domain.analytics.value_objects import (
    SampleAdequacy,
    SessionComparability,
)


class TestAntiLeakageSyntheticProfiles:
    """Verifies that measurement leakage and scenario bias are detected across distinct profiles."""

    def test_profile_a_repeated_scenario_memorization_detected(self) -> None:
        """Profile A repeats one single scenario 20 times, reducing latency from 5000ms to 800ms.

        The system must flag high repetition ratio and extreme board concentration,
        and MUST NOT report this as broad poker improvement.
        """
        report = DataQualityReport.analyze(
            profile_id="profile_a",
            total_decisions=20,
            graded_decisions=20,
            missing_ev_count=0,
            distinct_scenarios_count=1,
            first_exposure_count=1,
            repeat_exposure_count=19,
            distinct_boards_count=1,
            max_board_frequency=20,
            missing_provenance_count=0,
            legacy_grading_version_count=0,
            distinct_strategy_packs_count=1,
            validated_solver_families_count=1,
            missing_latency_count=0,
            missing_confidence_count=0,
            invalid_pot_count=0,
            unknown_board_texture_count=0,
        )

        assert report.repetition_ratio == 0.95
        assert report.max_board_concentration_pct == 100.0

        # Must flag REPETITION_INDUCED_INFLATION and BOARD_SELECTION_BIAS
        warning_codes = {w.code for w in report.risk_warnings}
        assert "REPETITION_INDUCED_INFLATION" in warning_codes
        assert "BOARD_SELECTION_BIAS" in warning_codes

        # Repetition inflation must be classified at HIGH risk level
        rep_warning = next(
            w for w in report.risk_warnings if w.code == "REPETITION_INDUCED_INFLATION"
        )
        assert rep_warning.level == LeakageRiskLevel.HIGH

    def test_profile_b_genuine_multi_family_practice(self) -> None:
        """Profile B practices 30 distinct scenarios across 10 distinct boards and 4 solver families.

        Should pass data quality checks without high-severity inflation warnings.
        """
        report = DataQualityReport.analyze(
            profile_id="profile_b",
            total_decisions=30,
            graded_decisions=30,
            missing_ev_count=0,
            distinct_scenarios_count=28,
            first_exposure_count=28,
            repeat_exposure_count=2,
            distinct_boards_count=10,
            max_board_frequency=3,
            missing_provenance_count=0,
            legacy_grading_version_count=0,
            distinct_strategy_packs_count=2,
            validated_solver_families_count=4,
            missing_latency_count=0,
            missing_confidence_count=0,
            invalid_pot_count=0,
            unknown_board_texture_count=0,
        )

        assert report.repetition_ratio < 0.10
        assert report.max_board_concentration_pct == 10.0

        # No HIGH severity warnings
        high_risks = [w for w in report.risk_warnings if w.level == LeakageRiskLevel.HIGH]
        assert len(high_risks) == 0

    def test_profile_c_scenario_mix_bias_between_sessions(self) -> None:
        """Profile C practices tough river 3-bet bluff catching in Session 1, then easy preflop in Session 2.

        Session comparability check must declare them NOT directly comparable.
        """
        session_1 = {
            "session_id": "sess_1",
            "categories": ["river", "facing_barrel", "bluff_catch"],
            "graded_decisions": 15,
            "mean_ev_loss_chips": 28.5,
        }
        session_2 = {
            "session_id": "sess_2",
            "categories": ["preflop", "open_raise"],
            "graded_decisions": 20,
            "mean_ev_loss_chips": 1.2,
        }

        # Compare category overlap: Jaccard similarity is 0.0
        set1 = set(session_1["categories"])
        set2 = set(session_2["categories"])
        overlap = len(set1 & set2) / len(set1 | set2)
        assert overlap == 0.0

        comparability = SessionComparability.evaluate(
            categories_a=session_1["categories"],
            categories_b=session_2["categories"],
            mode_a="GUIDED",
            mode_b="GUIDED",
            count_a=session_1["graded_decisions"],
            count_b=session_2["graded_decisions"],
        )

        assert not comparability.is_comparable
        assert comparability.similarity_score == 0.0
        assert "Low category overlap" in comparability.reason

    def test_profile_d_heavy_illustrative_chart_volume(self) -> None:
        """Profile D has 100 illustrative chart attempts and only 2 solver-graded decisions.

        Must flag HIGH_UNGRADED_PROPORTION warning and classify solver adequacy as INSUFFICIENT_DATA.
        """
        report = DataQualityReport.analyze(
            profile_id="profile_d",
            total_decisions=102,
            graded_decisions=2,
            missing_ev_count=100,
            distinct_scenarios_count=20,
            first_exposure_count=20,
            repeat_exposure_count=82,
            distinct_boards_count=5,
            max_board_frequency=30,
            missing_provenance_count=0,
            legacy_grading_version_count=0,
            distinct_strategy_packs_count=1,
            validated_solver_families_count=1,
            missing_latency_count=0,
            missing_confidence_count=0,
            invalid_pot_count=0,
            unknown_board_texture_count=0,
        )

        assert report.missing_ev_percentage >= 98.0
        warning_codes = {w.code for w in report.risk_warnings}
        assert "HIGH_UNGRADED_PROPORTION" in warning_codes

        # Sample adequacy for solver EV metrics must be INSUFFICIENT_DATA
        adequacy = SampleAdequacy.evaluate(report.graded_decisions, 0.0)
        assert adequacy == SampleAdequacy.INSUFFICIENT_DATA

    def test_profile_e_unsupported_and_missing_provenance(self) -> None:
        """Profile E has decisions with missing strategy pack provenance and legacy grading versions.

        Must produce HIGH severity warnings for provenance and legacy grading version leakage.
        """
        report = DataQualityReport.analyze(
            profile_id="profile_e",
            total_decisions=25,
            graded_decisions=15,
            missing_ev_count=10,
            distinct_scenarios_count=10,
            first_exposure_count=10,
            repeat_exposure_count=15,
            distinct_boards_count=4,
            max_board_frequency=10,
            missing_provenance_count=12,
            legacy_grading_version_count=8,
            distinct_strategy_packs_count=0,
            validated_solver_families_count=0,
            missing_latency_count=5,
            missing_confidence_count=20,
            invalid_pot_count=2,
            unknown_board_texture_count=1,
        )

        warning_codes = {w.code for w in report.risk_warnings}
        assert "MISSING_STRATEGY_PROVENANCE" in warning_codes
        assert "LEGACY_GRADING_VERSION" in warning_codes

        prov_warning = next(
            w for w in report.risk_warnings if w.code == "MISSING_STRATEGY_PROVENANCE"
        )
        assert prov_warning.level == LeakageRiskLevel.HIGH
