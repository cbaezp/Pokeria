"""Integration tests for Curriculum Course Hierarchy, Onboarding, and Step Progression API."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestCurriculumCourseApi:
    """Test suite for curriculum course tree, onboarding, and step progress."""

    async def test_get_course_hierarchy(self, client: AsyncClient) -> None:
        res = await client.get("/api/v1/curriculum/course")
        assert res.status_code == 200
        data = res.json()
        assert "chapters" in data
        assert data["total_chapters"] >= 6
        ch1 = data["chapters"][0]
        assert ch1["id"] == "chap_1_table"
        assert len(ch1["units"]) == 5

        # Check Chapter 2 Unit 2 has gold-standard range lesson
        ch2 = data["chapters"][1]
        assert ch2["id"] == "chap_2_ranges"
        u2 = next(u for u in ch2["units"] if u["id"] == "unit_2_2_matrix_13x13")
        assert any(lesson["id"] == "lesson.c2.u2.how_to_read_a_range" for lesson in u2["lessons"])

    async def test_onboarding_and_step_progress_journey(self, client: AsyncClient) -> None:
        # 1. Create a learner profile
        p_res = await client.post(
            "/api/v1/profiles",
            json={
                "username": "beginner_sam",
                "display_name": "Beginner Sam",
                "email": "sam@pokerlab.test",
            },
        )
        assert p_res.status_code == 201
        profile = p_res.json()
        pid = profile["id"]

        # 2. Complete Onboarding as NEW_TO_POKER
        onb_res = await client.post(
            "/api/v1/curriculum/onboarding",
            json={"profile_id": pid, "onboarding_level": "NEW_TO_POKER"},
        )
        assert onb_res.status_code == 200
        onb_data = onb_res.json()
        assert onb_data["onboarding_level"] == "NEW_TO_POKER"
        assert onb_data["current_path_node"] == "lesson.c1.u1.how_holdem_works"

        # 3. Advance through steps of the first lesson
        step_res = await client.post(
            "/api/v1/curriculum/lessons/lesson.c1.u1.how_holdem_works/step-progress",
            json={
                "profile_id": pid,
                "step_number": 1,
                "total_steps": 5,
                "is_completed": False,
            },
        )
        assert step_res.status_code == 200
        step_data = step_res.json()
        assert step_data["step_progress"]["step_number"] == 1
        assert not step_data["step_progress"]["is_completed"]

        # 4. Complete the lesson
        complete_res = await client.post(
            "/api/v1/curriculum/lessons/lesson.c1.u1.how_holdem_works/step-progress",
            json={
                "profile_id": pid,
                "step_number": 5,
                "total_steps": 5,
                "is_completed": True,
            },
        )
        assert complete_res.status_code == 200
        comp_data = complete_res.json()
        assert "lesson.c1.u1.how_holdem_works" in comp_data["completed_lessons"]
        # Next path node should be unlocked
        assert comp_data["current_path_node"] != "lesson.c1.u1.how_holdem_works"

        # 5. Query learner progress
        prog_res = await client.get(f"/api/v1/curriculum/progress/{pid}")
        assert prog_res.status_code == 200
        prog = prog_res.json()
        assert prog["profile_id"] == pid
        assert prog["onboarding_level"] == "NEW_TO_POKER"
        assert "lesson.c1.u1.how_holdem_works" in prog["completed_lessons"]
        assert prog["total_xp"] >= 25
        assert len(prog["chapter_progress"]) >= 6
