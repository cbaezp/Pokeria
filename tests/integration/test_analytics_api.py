"""Integration tests for Learning Analytics endpoints (/api/v1/analytics)."""

import uuid

from httpx import AsyncClient


class TestAnalyticsApiIntegration:
    """Integration test suite for Learning Analytics endpoints."""

    async def _create_test_profile(self, client: AsyncClient) -> str:
        """Helper to create a fresh profile."""
        uname = f"analyst_{uuid.uuid4().hex[:6]}"
        res = await client.post(
            "/api/v1/profiles",
            json={
                "username": uname,
                "display_name": "Analyst Pro",
                "email": f"{uname}@example.com",
            },
        )
        assert res.status_code == 201
        return res.json()["id"]

    async def _populate_session_with_decisions(self, client: AsyncClient, profile_id: str) -> str:
        """Helper to create a session and submit decisions to populate real decision events."""
        # 1. Create a session
        create_res = await client.post(
            "/api/v1/training/sessions",
            json={
                "profile_id": profile_id,
                "mode": "GUIDED",
                "target_decisions": 2,
                "selected_categories": ["river"],
                "seed": 42,
            },
        )
        assert create_res.status_code == 201
        session_id = create_res.json()["id"]

        # 2. Get exercise and submit decision
        ex_res = await client.get(f"/api/v1/training/sessions/{session_id}/next")
        assert ex_res.status_code == 200
        scenario = ex_res.json()

        # Submit first legal action
        first_action = scenario["legal_actions"][0]["kind"]
        sub_res = await client.post(
            f"/api/v1/training/sessions/{session_id}/decision",
            json={
                "scenario_id": scenario["id"],
                "chosen_action": first_action,
                "latency_ms": 1250,
                "confidence_score": 4,
            },
        )
        assert sub_res.status_code == 200

        # Complete the session
        comp_res = await client.post(f"/api/v1/training/sessions/{session_id}/complete")
        assert comp_res.status_code == 200
        return session_id

    async def test_empty_profile_analytics(self, client: AsyncClient) -> None:
        """An empty profile with no decisions should return valid zero/null structures without 500 errors."""
        profile_id = await self._create_test_profile(client)

        # Overview
        res = await client.get(f"/api/v1/analytics/overview?profile_id={profile_id}")
        assert res.status_code == 200
        overview = res.json()
        assert overview["total_decisions"] == 0
        assert overview["graded_decisions"] == 0
        assert overview["mean_ev_loss_chips"] is None
        assert overview["sample_adequacy"] == "insufficient_data"

        # Streets
        res = await client.get(f"/api/v1/analytics/streets?profile_id={profile_id}")
        assert res.status_code == 200
        streets = res.json()
        assert len(streets) == 4
        for s in streets:
            assert s["total_decisions"] == 0
            assert s["mean_ev_loss_chips"] is None

        # Positions
        res = await client.get(f"/api/v1/analytics/positions?profile_id={profile_id}")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

        # Skills
        res = await client.get(
            f"/api/v1/analytics/skills?profile_id={profile_id}&dimension=strategic_concept"
        )
        assert res.status_code == 200
        assert isinstance(res.json(), list)

        # Exposure
        res = await client.get(f"/api/v1/analytics/exposure?profile_id={profile_id}")
        assert res.status_code == 200
        exposure = res.json()
        assert exposure["total_decisions"] == 0
        assert exposure["repetition_ratio"] == 0.0

        # Data quality
        res = await client.get(f"/api/v1/analytics/data-quality?profile_id={profile_id}")
        assert res.status_code == 200
        dq = res.json()
        assert dq["total_decisions"] == 0
        assert dq["profile_id"] == profile_id

    async def test_populated_profile_analytics(self, client: AsyncClient) -> None:
        """Verify analytics endpoints with populated decision events."""
        profile_id = await self._create_test_profile(client)
        session_id = await self._populate_session_with_decisions(client, profile_id)

        # 1. Overview
        res = await client.get(f"/api/v1/analytics/overview?profile_id={profile_id}")
        assert res.status_code == 200
        overview = res.json()
        assert overview["total_decisions"] >= 1
        assert overview["completed_sessions"] == 1
        assert overview["median_latency_ms"] is not None

        # 2. Trends
        res = await client.get(f"/api/v1/analytics/trends?profile_id={profile_id}&interval=day")
        assert res.status_code == 200
        trends = res.json()
        assert len(trends) >= 1
        assert trends[0]["total_decisions"] >= 1

        # 3. Streets breakdown
        res = await client.get(f"/api/v1/analytics/streets?profile_id={profile_id}")
        assert res.status_code == 200
        streets = res.json()
        river_stat = next((s for s in streets if s["key"] == "river"), None)
        assert river_stat is not None
        assert river_stat["total_decisions"] >= 1

        # 4. Mistakes Explorer
        res = await client.get(
            f"/api/v1/analytics/mistakes?profile_id={profile_id}&page=1&page_size=10"
        )
        assert res.status_code == 200
        mistakes = res.json()
        assert "items" in mistakes
        assert "total" in mistakes
        assert mistakes["page"] == 1

        # 5. Session Comparison
        res = await client.get(
            f"/api/v1/analytics/sessions/compare?profile_id={profile_id}&session_ids={session_id}"
        )
        assert res.status_code == 200
        comp = res.json()
        assert "sessions" in comp
        assert len(comp["sessions"]) == 1
        assert "comparability" in comp

        # 6. Data Quality Report
        res = await client.get(f"/api/v1/analytics/data-quality?profile_id={profile_id}")
        assert res.status_code == 200
        dq = res.json()
        assert dq["total_decisions"] >= 1
        assert dq["first_exposure_count"] >= 1
