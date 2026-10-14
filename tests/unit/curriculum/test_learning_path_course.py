"""Unit tests for the structured learning path course and progression."""

from app.domain.curriculum.lessons import lesson_catalog


class TestCourseHierarchyAndLessons:
    """Verify Chapters, Units, and gold-standard lessons."""

    def test_chapter_and_unit_inventory(self):
        chapters = lesson_catalog.get_all_chapters()
        assert len(chapters) >= 6
        assert chapters[0].id == "chap_1_table"
        assert chapters[1].id == "chap_2_ranges"

        # Check Chapter 1 units
        ch1 = lesson_catalog.get_chapter("chap_1_table")
        assert ch1 is not None
        assert len(ch1.unit_ids) == 5
        assert "unit_1_holdem_rules" in ch1.unit_ids
        assert "unit_2_hand_rankings" in ch1.unit_ids
        assert "unit_3_table_positions" in ch1.unit_ids
        assert "unit_4_blinds_betting" in ch1.unit_ids
        assert "unit_5_stack_sizes" in ch1.unit_ids

    def test_gold_standard_range_lesson_steps(self):
        """Verify Chapter 2, Unit 2 'How to Read a Poker Range' satisfies all 8 specified steps."""
        lesson = lesson_catalog.get_lesson("lesson.c2.u2.how_to_read_a_range")
        assert lesson is not None
        assert lesson.title == "How to Read a Poker Range"
        assert len(lesson.steps) == 8

        # Step 1: Explain purpose of range
        assert lesson.steps[0].step_number == 1
        assert "range" in lesson.steps[0].content_markdown.lower()

        # Step 2: Show interactive 13x13 matrix
        assert lesson.steps[1].step_number == 2
        assert lesson.steps[1].component_type == "range_matrix_explorer"

        # Step 3: Explain AKs vs AKo vs AA
        assert lesson.steps[2].step_number == 3
        assert "AKs" in lesson.steps[2].content_markdown
        assert "AKo" in lesson.steps[2].content_markdown

        # Step 4: Ask learner to identify suited and offsuit cells
        assert lesson.steps[3].step_number == 4
        assert lesson.steps[3].quiz_question is not None
        assert lesson.steps[3].quiz_question["correct_index"] == 0

        # Step 5: Teach 4 suited, 12 offsuit, and 6 pocket-pair combinations
        assert lesson.steps[4].step_number == 5
        assert lesson.steps[4].component_type == "range_combination_counter"

        # Step 6: Ask a combination-counting question
        assert lesson.steps[5].step_number == 6
        assert lesson.steps[5].quiz_question is not None
        assert (
            lesson.steps[5].quiz_question["options"][lesson.steps[5].quiz_question["correct_index"]]
            == "12 combinations"
        )

        # Step 7: Introduce position-specific example (UTG vs BTN)
        assert lesson.steps[6].step_number == 7
        assert "UTG" in lesson.steps[6].content_markdown
        assert "Button" in lesson.steps[6].content_markdown

        # Step 8: End with recap & completion summary
        assert lesson.steps[7].step_number == 8
        assert lesson.steps[7].step_type == "RECAP"

    def test_course_tree_generation(self):
        tree = lesson_catalog.get_full_course_tree()
        assert "chapters" in tree
        assert tree["total_chapters"] >= 6
        for ch in tree["chapters"]:
            assert "units" in ch
            assert len(ch["units"]) >= 1
