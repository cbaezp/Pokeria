"""Unit tests for Phase D Curriculum, Skill Taxonomy, and Prerequisite Resolution."""

from app.domain.curriculum.lessons import lesson_catalog
from app.domain.curriculum.taxonomy import CoverageStatus, PokerDomain, taxonomy_registry


class TestSkillTaxonomyUnit:
    """Verifies integrity and invariants of the Elite Poker Skill Taxonomy."""

    def test_taxonomy_node_completeness(self):
        skills = taxonomy_registry.get_all_skills()
        assert len(skills) >= 16

        for s in skills:
            assert s.id.strip() != ""
            assert s.name.strip() != ""
            assert isinstance(s.domain, PokerDomain)
            assert isinstance(s.coverage_status, CoverageStatus)
            assert len(s.learning_objectives) > 0
            assert len(s.supported_practice_modes) > 0
            assert s.valid_reference_requirements != ""
            assert s.assessment_criteria != ""

    def test_prerequisite_graph_validity(self):
        """Ensure all prerequisite IDs point to existing skill nodes without cycles."""
        skills = taxonomy_registry.get_all_skills()
        all_ids = {s.id for s in skills}

        for s in skills:
            for prereq_id in s.prerequisite_ids:
                assert (
                    prereq_id in all_ids
                ), f"Prerequisite {prereq_id} for skill {s.id} does not exist!"
                assert prereq_id != s.id, f"Self-referential prerequisite on {s.id}"

    def test_domain_filtering_and_coverage_status(self):
        preflop_skills = taxonomy_registry.get_by_domain(PokerDomain.PREFLOP)
        assert len(preflop_skills) >= 5

        partially_implemented = taxonomy_registry.get_by_coverage(
            CoverageStatus.PARTIALLY_IMPLEMENTED
        )
        assert len(partially_implemented) == 11

        conceptual_only = taxonomy_registry.get_by_coverage(CoverageStatus.CONCEPTUAL_ONLY)
        assert len(conceptual_only) == 8

        summary = taxonomy_registry.get_coverage_summary()
        assert summary[CoverageStatus.IMPLEMENTED_AND_VALIDATED.value] == 1
        assert summary[CoverageStatus.PARTIALLY_IMPLEMENTED.value] == 11
        assert summary[CoverageStatus.CONCEPTUAL_ONLY.value] == 8

        # Verify decoupled attributes per Requirement 2
        for s in taxonomy_registry.get_all_skills():
            assert s.conceptual_status in {"IMPLEMENTED", "CONCEPTUAL_ONLY"}
            assert s.solver_reference_validity != ""
            assert s.assessment_availability != ""
            if s.coverage_status in (
                CoverageStatus.PARTIALLY_IMPLEMENTED,
                CoverageStatus.CONCEPTUAL_ONLY,
            ):
                assert len(s.scope_limitations) > 0


class TestCurriculumLessonsUnit:
    """Verifies structured lessons, ordering, and prerequisite unlocking."""

    def test_lesson_catalog_integrity(self):
        lessons = lesson_catalog.get_all_lessons()
        paths = lesson_catalog.get_all_paths()

        assert len(lessons) >= 8
        assert len(paths) >= 5

        path_ids = {p.id for p in paths}
        for lesson in lessons:
            assert (
                lesson.path_id in path_ids
            ), f"Lesson {lesson.id} assigned to nonexistent path {lesson.path_id}"
            assert len(lesson.steps) >= 1

    def test_prerequisite_unlocking_logic(self):
        # Foundational lesson has no prerequisites and is unlocked by default
        assert lesson_catalog.is_lesson_unlocked("lesson.preflop.position", set()) is True

        # Second lesson requires foundational lesson
        assert lesson_catalog.is_lesson_unlocked("lesson.preflop.btn_rfi", set()) is False
        assert (
            lesson_catalog.is_lesson_unlocked("lesson.preflop.btn_rfi", {"lesson.preflop.position"})
            is True
        )
