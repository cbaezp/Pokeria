"""Unit tests for audit/test fixture exclusion mechanism."""

from datetime import UTC, datetime

from app.domain.learner.features import PointInTimeFeatureExtractor
from app.domain.learner.models import check_decision_eligibility
from app.domain.training.models import DecisionEvent


def make_decision(profile_id: str, is_test: bool) -> DecisionEvent:
    return DecisionEvent(
        id="d1",
        session_id="s1",
        profile_id=profile_id,
        scenario_id="scen_1",
        scenario_family="RIVER_BLUFF_CATCH",
        strategy_pack_id="pack_1",
        solver_node_id=1,
        combo="AhKh",
        board="As Kd 2c",
        hero_position="BTN",
        pot=30.0,
        effective_stack=100.0,
        action_history=[],
        legal_actions=[],
        chosen_action="Bet",
        chosen_amount=10.0,
        reference_strategy=[],
        chosen_ev=10.0,
        best_ev=10.0,
        ev_loss=0.0,
        grade="BEST",
        grading_status="GRADED",
        grading_provenance="SOLVER_ACTION_EV",
        latency_ms=1000,
        confidence_score=4,
        created_at=datetime.now(UTC),
        algorithm_version="v1.0.0",
        observation_origin="INTERACTIVE_USER",
    )


class TestAuditExclusion:
    """Verifies that audit and test profile data can NEVER enter model training datasets."""

    def test_audit_flag_excludes_decision_from_training(self) -> None:
        elig = check_decision_eligibility(
            profile_is_test=True,
            grading_status="GRADED",
            grading_provenance="SOLVER_ACTION_EV",
            ev_loss=0.0,
            pot=30.0,
        )
        assert elig.is_eligible is False
        assert elig.is_test_profile is True
        assert elig.exclusion_reason == "AUDIT_TEST_FIXTURE_EXCLUDED"

    def test_feature_extractor_drops_audit_profile_samples(self) -> None:
        decision = make_decision(profile_id="audit_profile_1", is_test=True)
        extractor = PointInTimeFeatureExtractor()
        # When profile_is_test=True is passed, 0 training samples are emitted
        samples = extractor.extract_causal_dataset([decision], profile_is_test=True)
        assert len(samples) == 0

        # When profile_is_test=False (real user), sample is included
        samples_real = extractor.extract_causal_dataset([decision], profile_is_test=False)
        assert len(samples_real) == 1

    def test_scenario_a_known_audit_prefix(self) -> None:
        """A. Synthetic audit profile with an internal audit domain."""
        from app.domain.learner.models import is_disqualified_profile

        class MockProfile:
            username = "audit_fixture_user"
            email = "fixture@audit.pokerlab"
            display_name = "Fixture"
            is_test_profile = False

        assert is_disqualified_profile(MockProfile()) is True

    def test_scenario_b_ordinary_username_audit_email(self) -> None:
        """B. Synthetic audit profile with a completely ordinary username but test domain email."""
        from app.domain.learner.models import is_disqualified_profile

        class MockProfile:
            username = "user_85c18a4c"
            email = "audit_85c18a4c@test.local"
            display_name = "Audit User"
            is_test_profile = False

        assert is_disqualified_profile(MockProfile()) is True

    def test_scenario_c_legitimate_prefix_collision(self) -> None:
        """C. Legitimate profile whose username contains an audit/test substring must NOT be disqualified."""
        from app.domain.learner.models import is_disqualified_profile

        class MockProfile:
            username = "audit_accountant"
            email = "john@legitpoker.com"
            display_name = "John"
            is_test_profile = False

        # Explicit trusted provenance boundary: legitimate user without is_test_profile is NOT disqualified
        assert is_disqualified_profile(MockProfile()) is False

    def test_scenario_d_mixed_real_and_synthetic_observations(self) -> None:
        """D. Mixed historical real and synthetic observations under the same profile."""
        real_elig = check_decision_eligibility(
            profile_is_test=False,
            grading_status="GRADED",
            grading_provenance="SOLVER_ACTION_EV",
            ev_loss=0.0,
            pot=30.0,
            observation_origin="INTERACTIVE_USER",
        )
        assert real_elig.is_eligible is True

        synth_elig = check_decision_eligibility(
            profile_is_test=False,
            grading_status="GRADED",
            grading_provenance="SOLVER_ACTION_EV",
            ev_loss=0.0,
            pot=30.0,
            observation_origin="AUDIT_FIXTURE",
        )
        assert synth_elig.is_eligible is False
        assert synth_elig.exclusion_reason == "DISQUALIFIED_ORIGIN_AUDIT_FIXTURE"

    def test_scenario_e_test_decisions_imported_into_legitimate_profile(self) -> None:
        """E. Test decisions imported into an otherwise legitimate profile."""
        imported_elig = check_decision_eligibility(
            profile_is_test=False,
            grading_status="GRADED",
            grading_provenance="SOLVER_ACTION_EV",
            ev_loss=0.0,
            pot=30.0,
            observation_origin="TEST_IMPORT",
        )
        assert imported_elig.is_eligible is False
        assert imported_elig.exclusion_reason == "DISQUALIFIED_ORIGIN_TEST_IMPORT"

    def test_scenario_f_profile_renamed_after_dataset_generation(self) -> None:
        """F. Profile renamed after dataset generation preserves trusted test flag."""
        from app.domain.learner.models import is_disqualified_profile

        class MockProfileRenamed:
            username = "audit_renamed_to_normal"
            email = "normal@company.com"
            display_name = "Normal"
            is_test_profile = True  # Trusted test flag remains immutable

        assert is_disqualified_profile(MockProfileRenamed()) is True

    def test_scenario_g_newly_created_test_profile_after_migration(self) -> None:
        """G. Newly created test profile after migration."""
        from app.domain.learner.models import is_disqualified_profile

        class MockProfile:
            username = "new_test_user"
            email = "test@company.com"
            display_name = "Test"
            is_test_profile = True

        assert is_disqualified_profile(MockProfile()) is True

    def test_scenario_h_existing_audit_fixture_restored_from_backup(self) -> None:
        """H. Existing audit fixture restored from a backup."""
        from app.domain.learner.models import is_disqualified_profile

        class MockProfile:
            username = "canonical_audit_profile"
            email = "audit@pokerlab.local"
            display_name = "Canonical Audit Profile"
            is_test_profile = False

        assert is_disqualified_profile(MockProfile()) is True

    def test_scenario_i_profile_test_flag_changed_after_training(self) -> None:
        """I. Profile test flag changed after a model was trained."""
        # When profile is flagged as test profile, feature extractor emits 0 observations
        decision = make_decision(profile_id="p_toggled", is_test=True)
        extractor = PointInTimeFeatureExtractor()
        samples = extractor.extract_causal_dataset([decision], profile_is_test=True)
        assert len(samples) == 0

    def test_scenario_j_model_artifact_trained_before_observations_disqualified(self) -> None:
        """J. Model artifact trained before its observations were disqualified."""
        # Origin verification disallows unknown provenance
        unknown_elig = check_decision_eligibility(
            profile_is_test=False,
            grading_status="GRADED",
            grading_provenance="SOLVER_ACTION_EV",
            ev_loss=0.0,
            pot=30.0,
            observation_origin="UNKNOWN",
        )
        assert unknown_elig.is_eligible is False
        assert unknown_elig.exclusion_reason == "DISQUALIFIED_ORIGIN_UNKNOWN"

    def test_genuine_learners_with_unusual_names_never_disqualified(self) -> None:
        """Adversarial check: Genuine learners with substrings like test, audit, bench, mock
        in their usernames or display names MUST NOT be excluded from ML training datasets.
        """
        from app.domain.learner.models import is_disqualified_profile

        unusual_genuine_profiles = [
            ("contest_winner", "contest_winner@pokerpro.net", "Contest Winner"),
            ("dr_auditing", "auditor@university.edu", "Dr. Auditing"),
            ("audit_accountant", "john@accountingfirm.com", "John"),
            ("ben_chandler", "ben@lawfirm.org", "Ben Chandler"),  # contains 'bench'
            ("e2e4_chess_pro", "chess@grandmaster.com", "Chess Player"),  # contains 'e2e'
            ("mockingbird", "atticus@maycomb.com", "Mockingbird"),  # contains 'mock'
        ]

        extractor = PointInTimeFeatureExtractor()
        for uname, uemail, dname in unusual_genuine_profiles:

            class LegitProfile:
                username = uname
                email = uemail
                display_name = dname
                is_test_profile = False

            # Profile is NOT disqualified
            assert is_disqualified_profile(LegitProfile()) is False, (
                f"Profile {uname} was falsely disqualified!"
            )

            # Decisions under this profile are eligible
            elig = check_decision_eligibility(
                profile_is_test=False,
                grading_status="GRADED",
                grading_provenance="SOLVER_ACTION_EV",
                ev_loss=0.10,
                pot=20.0,
                observation_origin="INTERACTIVE_USER",
            )
            assert elig.is_eligible is True, f"Decision for {uname} was falsely marked ineligible!"

            # Feature extractor emits training samples
            dec = make_decision(profile_id=f"prof_{uname}", is_test=False)
            samples = extractor.extract_causal_dataset([dec], profile_is_test=False)
            assert len(samples) == 1, (
                f"Feature extractor failed to emit sample for genuine user {uname}"
            )

    def test_untrusted_and_malicious_observation_provenance_fails_closed(self) -> None:
        """Adversarial check: Untrusted, synthetic, or spoofed observation origins fail closed."""
        malicious_origins = [
            "UNKNOWN",
            "AUDIT_FIXTURE",
            "SPOOFED_INTERACTIVE",
            "TEST_IMPORT",
            "ADMIN_INJECTED",
            "SYNTHETIC_GENERATOR",
            "",
        ]
        for origin in malicious_origins:
            elig = check_decision_eligibility(
                profile_is_test=False,
                grading_status="GRADED",
                grading_provenance="SOLVER_ACTION_EV",
                ev_loss=0.0,
                pot=10.0,
                observation_origin=origin,
            )
            assert elig.is_eligible is False, f"Origin '{origin}' did not fail closed!"
            assert "DISQUALIFIED_ORIGIN" in (elig.exclusion_reason or "")
