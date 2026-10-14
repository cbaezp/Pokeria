"""Integration tests for Learner endpoints (/api/v1/learner/*)."""

import uuid

from httpx import AsyncClient

from app.application.ports.unit_of_work import UnitOfWork


class TestLearnerApiIntegration:
    """Integration test suite for Personalized Learner endpoints."""

    async def _create_test_profile(self, client: AsyncClient) -> str:
        """Helper to create a fresh profile."""
        uname = f"player_{uuid.uuid4().hex[:6]}"
        res = await client.post(
            "/api/v1/profiles",
            json={
                "username": uname,
                "display_name": "Test Player",
                "email": f"{uname}@example.com",
            },
        )
        assert res.status_code == 201
        return res.json()["id"]

    async def test_cold_start_learner_status(self, client: AsyncClient) -> None:
        """Test status endpoint for cold-start user with no decisions."""
        profile_id = await self._create_test_profile(client)

        res = await client.get(f"/api/v1/learner/status?profile_id={profile_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["profile_id"] == profile_id
        assert data["recommendation_mode"] == "RULE_BASED_BASELINE"
        assert data["is_cold_start"] is True
        assert data["eligible_observations_count"] == 0
        assert "cold start" in data["limitations_disclaimer"].lower()

    async def test_learner_evidence_endpoint(self, client: AsyncClient) -> None:
        """Test evidence endpoint reports accurate counts and exclusions."""
        profile_id = await self._create_test_profile(client)

        res = await client.get(f"/api/v1/learner/evidence?profile_id={profile_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["profile_id"] == profile_id
        assert data["total_decisions"] == 0
        assert data["eligible_solver_decisions"] == 0
        assert "distinct_boards" in data

    async def test_learner_weaknesses_endpoint(self, client: AsyncClient) -> None:
        """Test weaknesses endpoint returns structured findings."""
        profile_id = await self._create_test_profile(client)

        res = await client.get(f"/api/v1/learner/weaknesses?profile_id={profile_id}")
        assert res.status_code == 200
        data = res.json()
        assert "profile_id" in data
        assert "weaknesses" in data
        assert isinstance(data["weaknesses"], list)

    async def test_learner_recommendations_endpoint(self, client: AsyncClient) -> None:
        """Test recommendation engine returns valid, solver-backed recommendations even on cold start."""
        profile_id = await self._create_test_profile(client)

        res = await client.get(f"/api/v1/learner/recommendations?profile_id={profile_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["mode"] == "RULE_BASED_BASELINE"
        assert len(data["recommendations"]) > 0

        # Each recommendation must have required evidence-aware metadata
        rec = data["recommendations"][0]
        assert "scenario_id" in rec
        assert "scenario_family" in rec
        assert "reason" in rec
        assert "recommendation_mode" in rec
        assert "source_pack_id" in rec
        assert rec["source_pack_id"] is not None

    async def test_train_model_insufficient_evidence_flow(self, client: AsyncClient) -> None:
        """Test requesting training queues a training job."""
        profile_id = await self._create_test_profile(client)

        res = await client.post(
            "/api/v1/learner/models/train",
            json={"profile_id": profile_id, "force_retrain": False},
        )
        assert res.status_code == 202
        data = res.json()
        assert "job_id" in data
        assert data["status"] in ("QUEUED", "COMPLETED")

    async def test_audit_exclusion_in_learner_evidence(
        self, client: AsyncClient, test_uow: UnitOfWork
    ) -> None:
        """Verify that audit/test profile decisions do not count towards training eligibility."""
        profile_id = await self._create_test_profile(client)

        # Mark profile as test profile using test_uow
        async with test_uow:
            p = await test_uow.profiles.get_by_id(profile_id)
            assert p is not None
            p.is_test_profile = True
            await test_uow.profiles.save(p)
            await test_uow.commit()

        res = await client.get(f"/api/v1/learner/status?profile_id={profile_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["is_test_profile_excluded"] is True
        assert data["eligible_observations_count"] == 0
