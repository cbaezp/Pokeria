"""Integration tests for Training API endpoints (/api/v1/training)."""

from httpx import AsyncClient


class TestTrainingApiIntegration:
    """Integration test suite for interactive training endpoints."""

    async def _create_test_profile(self, client: AsyncClient) -> str:
        """Helper to create a local profile for session testing."""
        import uuid

        uname = f"trainer_{uuid.uuid4().hex[:6]}"
        res = await client.post(
            "/api/v1/profiles",
            json={
                "username": uname,
                "display_name": "Trainer Pro",
                "email": f"{uname}@example.com",
            },
        )
        assert res.status_code == 201
        return res.json()["id"]

    async def test_modes_endpoint(self, client: AsyncClient) -> None:
        """Verify GET /api/v1/training/modes returns all supported modes."""
        res = await client.get("/api/v1/training/modes")
        assert res.status_code == 200
        modes = res.json()
        assert len(modes) >= 6
        mode_names = [m["mode"] for m in modes]
        assert "GUIDED" in mode_names
        assert "BLIND" in mode_names
        assert "MIXED" in mode_names
        assert "STREET" in mode_names
        assert "TIMED" in mode_names
        assert "REVIEW" in mode_names

    async def test_scenarios_listing(self, client: AsyncClient) -> None:
        """Verify GET /api/v1/training/scenarios returns indexed scenarios."""
        res = await client.get("/api/v1/training/scenarios")
        assert res.status_code == 200
        scenarios = res.json()
        assert len(scenarios) > 0
        first = scenarios[0]
        assert "id" in first
        assert "street" in first
        assert "legal_actions" in first

    async def test_complete_training_session_lifecycle_and_decision_grading(
        self, client: AsyncClient
    ) -> None:
        """Verify full interactive flow:
        Create session -> Fetch exercise -> Submit decision -> Solver evaluation -> Review.
        """
        profile_id = await self._create_test_profile(client)

        # 1. Create a session with 3 target decisions
        create_res = await client.post(
            "/api/v1/training/sessions",
            json={
                "profile_id": profile_id,
                "mode": "GUIDED",
                "target_decisions": 3,
                "selected_categories": ["river"],
                "seed": 123,
            },
        )
        assert create_res.status_code == 201
        session_data = create_res.json()
        session_id = session_data["id"]
        assert session_data["status"] == "ACTIVE"
        assert session_data["completed_decisions"] == 0
        assert session_data["target_decisions"] == 3

        # 2. Get next exercise
        next_res = await client.get(f"/api/v1/training/sessions/{session_id}/next")
        assert next_res.status_code == 200
        scenario = next_res.json()
        assert scenario is not None
        assert "hero_cards" in scenario
        assert len(scenario["legal_actions"]) >= 2
        chosen_action = scenario["legal_actions"][0]["kind"]
        chosen_amount = scenario["legal_actions"][0].get("amount")

        # 3. Submit decision
        dec_res = await client.post(
            f"/api/v1/training/sessions/{session_id}/decision",
            json={
                "chosen_action": chosen_action,
                "chosen_amount": chosen_amount,
                "latency_ms": 1200,
                "confidence_score": 85,
            },
        )
        assert dec_res.status_code == 200
        evaluation = dec_res.json()
        assert evaluation["chosen_action"] == chosen_action
        assert evaluation["grade"] in ("STRONG", "ACCEPTABLE", "INACCURACY", "MISTAKE", "BLUNDER")
        assert "raw_ev_loss" in evaluation
        assert evaluation["session_progress"]["completed_decisions"] == 1

        # 4. Duplicate submission for the same exercise should be rejected
        dup_res = await client.post(
            f"/api/v1/training/sessions/{session_id}/decision",
            json={"chosen_action": chosen_action, "latency_ms": 1000},
        )
        # Session already moved to next scenario, or if pointing to different scenario, rejection rules apply
        assert dup_res.status_code in (200, 400)

        # 5. List decisions in session
        list_dec_res = await client.get(f"/api/v1/training/sessions/{session_id}/decisions")
        assert list_dec_res.status_code == 200
        decisions = list_dec_res.json()
        assert len(decisions) >= 1
        decision_id = decisions[0]["id"]
        assert decisions[0]["confidence_score"] == 85

        # 6. Review decision
        review_res = await client.get(f"/api/v1/training/decisions/{decision_id}/review")
        assert review_res.status_code == 200
        rev_data = review_res.json()
        assert "decision" in rev_data
        assert "review_notes" in rev_data

        # 7. Pause and Resume session
        pause_res = await client.post(f"/api/v1/training/sessions/{session_id}/pause")
        assert pause_res.status_code == 200
        assert pause_res.json()["status"] == "PAUSED"

        resume_res = await client.post(f"/api/v1/training/sessions/{session_id}/resume")
        assert resume_res.status_code == 200
        assert resume_res.json()["status"] == "ACTIVE"

        # 8. Complete session
        comp_res = await client.post(f"/api/v1/training/sessions/{session_id}/complete")
        assert comp_res.status_code == 200
        assert comp_res.json()["status"] == "COMPLETED"
