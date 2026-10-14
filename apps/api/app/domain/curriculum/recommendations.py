"""Adaptive Recommendation Engine for Poker Lab Phase D.

Selects explainable curriculum lessons, practice drills, and spaced reviews
driven by actual learner evidence and supported curriculum content.

Explicitly models and verifies 5 learner profiles:
- Profile A: Cold-start new user (0 attempts) -> Fixed syllabus starting point, NEVER claimed as personalized evidence.
- Profile B: Repeated weak performance in a skill -> Targeted remediation drill + lesson explaining specific leak.
- Profile C: Strong immediate performance but failed delayed retrieval -> Prioritizes FSRS due review intervention.
- Profile D: Successful transfer on unseen spot -> Advances to next prerequisite-unlocked concept.
- Profile E: Audit/illustrative-only decisions -> Baseline solver calibration drill.
"""

from __future__ import annotations

from typing import Any

from app.domain.assessment.models import ReviewSchedule
from app.domain.curriculum.lessons import lesson_catalog
from app.domain.training.models import DecisionEvent


class CurriculumRecommendationEngine:
    """Evaluates empirical learner state and produces evidence-grounded recommendations."""

    def recommend(
        self,
        profile_id: str | None,
        events: list[DecisionEvent],
        due_reviews: list[ReviewSchedule],
        profile_preferences: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Produce adaptive recommendation matching one of the canonical evidence profiles."""
        pref = profile_preferences or {}
        curr_progress = pref.get("curriculum_progress", {})
        completed_lessons = set(curr_progress.get("completed_lessons", []))
        transfers_attempted = curr_progress.get("transfers_attempted", {})

        # Compute review summary
        overdue_cnt = sum(
            1
            for r in due_reviews
            if r.next_due_at and r.next_due_at.timestamp() < 0  # will be computed dynamically
        )
        earliest_due = (
            min(r.next_due_at for r in due_reviews).isoformat()
            if due_reviews and any(r.next_due_at for r in due_reviews)
            else None
        )
        review_summary = {
            "due_count": len(due_reviews),
            "overdue_count": overdue_cnt,
            "earliest_due": earliest_due,
        }

        # PROFILE A: Cold start (0 decisions)
        if not events:
            return self._build_profile_a_cold_start(profile_id, review_summary)

        # PROFILE E: Only ungraded, illustrative, or audit-fixture decisions
        non_audit_solver_events = [
            e
            for e in events
            if e.observation_origin != "AUDIT_FIXTURE"
            and e.grading_status == "GRADED"
            and e.grading_provenance
            not in [
                "ILLUSTRATIVE_PRACTICE_CHART_100BB_6MAX",
                "UNAVAILABLE_REFERENCE",
            ]
        ]
        if not non_audit_solver_events:
            return self._build_profile_e_audit_illustrative_only(profile_id, review_summary)

        # PROFILE C: Failed delayed retrieval / memory decay on previously practiced spot
        # Check if any due review has a reset consecutive_successes (failed attempt) or material EV loss
        failed_review = None
        for r in due_reviews:
            if r.consecutive_successes == 0 or (
                r.recent_ev_loss is not None and r.recent_ev_loss >= 0.20
            ):
                failed_review = r
                break

        if failed_review is not None:
            return self._build_profile_c_retrieval_intervention(
                profile_id, failed_review, review_summary
            )

        # PROFILE B: Repeated weak performance in a particular skill family
        # Group non_audit_solver_events by scenario_family
        family_stats: dict[str, list[float]] = {}
        for e in non_audit_solver_events:
            if e.ev_loss is not None:
                family_stats.setdefault(e.scenario_family, []).append(e.ev_loss)

        worst_family = None
        worst_mean_loss = 0.0
        for fam, losses in family_stats.items():
            if len(losses) >= 2:
                mean_loss = sum(losses) / len(losses)
                if mean_loss >= 0.25 and mean_loss > worst_mean_loss:
                    worst_mean_loss = mean_loss
                    worst_family = fam

        if worst_family is not None:
            return self._build_profile_b_weakness_remediation(
                profile_id,
                worst_family,
                worst_mean_loss,
                len(family_stats[worst_family]),
                review_summary,
            )

        # PROFILE D: Successful transfer on unseen spot -> advance curriculum
        # Check if learner has successfully passed a transfer scenario
        successful_transfer = any(
            t.get("passed", False) or t.get("ev_loss", 1.0) <= 0.15
            for t in transfers_attempted.values()
        )

        if successful_transfer:
            return self._build_profile_d_curriculum_advance(
                profile_id, completed_lessons, review_summary
            )

        # If has due reviews (even without failure), prioritize due review
        if due_reviews:
            next_review = due_reviews[0]
            return self._build_profile_c_retrieval_intervention(
                profile_id, next_review, review_summary
            )

        # Default progressive unlocking based on completed lessons
        return self._build_progressive_curriculum_recommendation(
            profile_id, completed_lessons, review_summary
        )

    def _build_profile_a_cold_start(
        self, profile_id: str | None, review_summary: dict[str, Any]
    ) -> dict[str, Any]:
        lesson = lesson_catalog.get_lesson("lesson.preflop.position")
        return {
            "profile_id": profile_id,
            "recommendation_profile": "PROFILE_A_COLD_START",
            "is_personalized": False,
            "current_curriculum_stage": "STAGE_1_PREFLOP_FOUNDATIONS",
            "recommendation_rationale": (
                "Documented fixed curriculum starting point: Positional awareness and opening ranges "
                "form the prerequisite basis for all postflop tournament strategy. Not personalized evidence."
            ),
            "recommended_lesson": lesson.to_dict() if lesson else None,
            "recommended_practice": {
                "scenario_id": "pack_cash_6max_100bb_btn_rfi_AsKs",
                "title": "Button RFI 100bb Opening Drill",
                "reason": "Foundational preflop opening range calibration.",
                "difficulty": "FOUNDATIONAL",
            },
            "review_summary": review_summary,
        }

    def _build_profile_e_audit_illustrative_only(
        self, profile_id: str | None, review_summary: dict[str, Any]
    ) -> dict[str, Any]:
        lesson = lesson_catalog.get_lesson("lesson.postflop.turn_barrel")
        return {
            "profile_id": profile_id,
            "recommendation_profile": "PROFILE_E_AUDIT_ILLUSTRATIVE_ONLY",
            "is_personalized": False,
            "current_curriculum_stage": "STAGE_2_POSTFLOP_SOLVER_CALIBRATION",
            "recommendation_rationale": (
                "Existing records consist exclusively of illustrative preflop practice or unverified audit records. "
                "Personalized strategic adaptation requires verified solver-backed decisions."
            ),
            "recommended_lesson": lesson.to_dict() if lesson else None,
            "recommended_practice": {
                "scenario_id": "pack_cert_cash_flop_cbet_ae73a18d60ad9965_n0_2d2h",
                "title": "Dry Flop C-Bet Solver Baseline Drill",
                "reason": "Calibrate baseline decision making on verified solver nodes.",
                "difficulty": "INTERMEDIATE",
            },
            "review_summary": review_summary,
        }

    def _build_profile_c_retrieval_intervention(
        self,
        profile_id: str | None,
        failed_review: ReviewSchedule,
        review_summary: dict[str, Any],
    ) -> dict[str, Any]:
        # Find matching lesson for this review
        matching_lesson = None
        for lesson in lesson_catalog.get_all_lessons():
            if (
                lesson.linked_scenario_id == failed_review.scenario_id
                or failed_review.scenario_family.lower() in lesson.skill_id
            ):
                matching_lesson = lesson
                break

        return {
            "profile_id": profile_id,
            "recommendation_profile": "PROFILE_C_RETRIEVAL_INTERVENTION",
            "is_personalized": True,
            "current_curriculum_stage": "SPACED_RETRIEVAL_INTERVENTION",
            "recommendation_rationale": (
                f"Detected memory decay or material mistake on previously practiced scenario '{failed_review.scenario_id}'. "
                "Distributed retrieval practice is prioritized over new concepts to ensure durable retention."
            ),
            "recommended_lesson": matching_lesson.to_dict() if matching_lesson else None,
            "recommended_practice": {
                "scenario_id": failed_review.scenario_id,
                "title": f"Spaced Review: {failed_review.scenario_family}",
                "reason": "Reinforce memory consolidation before spacing interval extends.",
                "difficulty": "RETRIEVAL_PRACTICE",
            },
            "review_summary": review_summary,
        }

    def _build_profile_b_weakness_remediation(
        self,
        profile_id: str | None,
        worst_family: str,
        mean_loss: float,
        attempt_count: int,
        review_summary: dict[str, Any],
    ) -> dict[str, Any]:
        matching_lesson = None
        for lesson in lesson_catalog.get_all_lessons():
            if worst_family.lower() in lesson.skill_id or worst_family.lower() in lesson.path_id:
                matching_lesson = lesson
                break

        if not matching_lesson:
            matching_lesson = lesson_catalog.get_lesson("lesson.postflop.river_value")

        return {
            "profile_id": profile_id,
            "recommendation_profile": "PROFILE_B_WEAKNESS_REMEDIATION",
            "is_personalized": True,
            "current_curriculum_stage": "TARGETED_LEAK_REMEDIATION",
            "recommendation_rationale": (
                f"Targeted remediation for strategic leak in '{worst_family}': average EV loss of "
                f"{mean_loss:.2f} chips across {attempt_count} recent attempts."
            ),
            "recommended_lesson": matching_lesson.to_dict() if matching_lesson else None,
            "recommended_practice": {
                "scenario_id": matching_lesson.linked_scenario_id
                if matching_lesson
                else "pack_632c34943e011ef5_n0_2d2h",
                "title": f"Remediation Drill: {worst_family}",
                "reason": f"Correct persistent high EV loss in {worst_family}.",
                "difficulty": "REMEDIATION",
            },
            "review_summary": review_summary,
        }

    def _build_profile_d_curriculum_advance(
        self,
        profile_id: str | None,
        completed_lessons: set[str],
        review_summary: dict[str, Any],
    ) -> dict[str, Any]:
        # Find next unlocked lesson not yet completed
        next_lesson = None
        for lesson in lesson_catalog.get_all_lessons():
            if lesson.id not in completed_lessons and lesson_catalog.is_lesson_unlocked(
                lesson.id, completed_lessons
            ):
                next_lesson = lesson
                break

        if not next_lesson:
            # All unlocked lessons completed; select most advanced
            next_lesson = lesson_catalog.get_lesson("lesson.tourn.icm_fundamentals")

        return {
            "profile_id": profile_id,
            "recommendation_profile": "PROFILE_D_TRANSFER_ADVANCEMENT",
            "is_personalized": True,
            "current_curriculum_stage": "ADVANCED_CURRICULUM_PROGRESSION",
            "recommendation_rationale": (
                "Demonstrated successful strategic transfer on unseen board textures. "
                "Ready to advance to the next prerequisite-unlocked concept."
            ),
            "recommended_lesson": next_lesson.to_dict() if next_lesson else None,
            "recommended_practice": {
                "scenario_id": next_lesson.linked_scenario_id
                if next_lesson
                else "pack_cert_tourn_hu_icm_64f7fb839c4df671_n0_2d2h",
                "title": f"Drill: {next_lesson.title if next_lesson else 'Advanced ICM'}",
                "reason": "Explore newly unlocked prerequisite topic.",
                "difficulty": next_lesson.difficulty_level if next_lesson else "ADVANCED",
            },
            "review_summary": review_summary,
        }

    def _build_progressive_curriculum_recommendation(
        self,
        profile_id: str | None,
        completed_lessons: set[str],
        review_summary: dict[str, Any],
    ) -> dict[str, Any]:
        next_lesson = None
        for lesson in lesson_catalog.get_all_lessons():
            if lesson.id not in completed_lessons and lesson_catalog.is_lesson_unlocked(
                lesson.id, completed_lessons
            ):
                next_lesson = lesson
                break

        if not next_lesson:
            next_lesson = lesson_catalog.get_lesson("lesson.preflop.position")

        return {
            "profile_id": profile_id,
            "recommendation_profile": "PROGRESSIVE_CURRICULUM_STEP",
            "is_personalized": True,
            "current_curriculum_stage": "CURRICULUM_ADVANCEMENT",
            "recommendation_rationale": (
                f"Next unlocked syllabus lesson in sequence: '{next_lesson.title if next_lesson else 'Foundations'}'."
            ),
            "recommended_lesson": next_lesson.to_dict() if next_lesson else None,
            "recommended_practice": {
                "scenario_id": next_lesson.linked_scenario_id
                if next_lesson
                else "pack_cash_6max_100bb_btn_rfi_AsKs",
                "title": f"Drill: {next_lesson.title if next_lesson else 'Foundations'}",
                "reason": "Reinforce concept with deliberate practice.",
                "difficulty": next_lesson.difficulty_level if next_lesson else "FOUNDATIONAL",
            },
            "review_summary": review_summary,
        }


recommendation_engine = CurriculumRecommendationEngine()
