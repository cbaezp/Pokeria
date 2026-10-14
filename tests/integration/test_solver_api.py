"""Integration tests for GTO solver API endpoints (/api/v1/solver)."""

import pytest
from httpx import AsyncClient

from app.main import sync_starter_packs_to_db


class TestSolverApiEndpoints:
    """Integration test suite for solver endpoints."""

    async def test_capabilities_endpoint(self, client: AsyncClient) -> None:
        """Verify GET /api/v1/solver/capabilities returns engine metadata."""
        res = await client.get("/api/v1/solver/capabilities")
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "postflop"
        assert data["license"] == "MIT"
        assert data["measured_convergence"] is True
        assert data["supported_features"]["vectorized_dcfr"] is True

    async def test_validate_config_endpoint_valid(self, client: AsyncClient) -> None:
        """Verify POST /api/v1/solver/validate returns valid for legal configuration."""
        payload = {
            "board": "Ah Kd 2c 7s 9c",
            "oop_range": "AA,KK,QQ,JJ,AKs",
            "ip_range": "AA,KK,QQ,JJ,AKs",
            "starting_pot": 20.0,
            "effective_stack": 50.0,
            "max_iterations": 100,
            "target_exploitability": 0.5,
        }
        res = await client.post("/api/v1/solver/validate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["valid"] is True
        assert len(data["errors"]) == 0
        assert len(data["scenario_key"]) == 64

    async def test_validate_config_endpoint_invalid(self, client: AsyncClient) -> None:
        """Verify POST /api/v1/solver/validate returns errors for invalid configuration."""
        payload = {
            "board": "Ah Ah 2c 7s 9c",  # duplicate card
            "oop_range": "AA",
            "ip_range": "KK",
            "starting_pot": 20.0,
            "effective_stack": 50.0,
        }
        res = await client.post("/api/v1/solver/validate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0

    async def test_estimate_resources_endpoint(self, client: AsyncClient) -> None:
        """Verify POST /api/v1/solver/estimate returns resource bounds."""
        payload = {
            "board": "Ah Kd 2c 7s 9c",
            "oop_range": "AA,KK,QQ",
            "ip_range": "AA,KK,QQ",
            "starting_pot": 20.0,
            "effective_stack": 50.0,
        }
        res = await client.post("/api/v1/solver/estimate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["estimated_nodes"] > 0
        assert data["estimated_memory_mb"] > 0
        assert data["feasible"] is True

    async def test_list_and_inspect_strategy_packs(
        self, client: AsyncClient, test_session_factory
    ) -> None:
        """Verify listing and inspecting reference strategy packs."""
        await sync_starter_packs_to_db(test_session_factory)
        res = await client.get("/api/v1/solver/packs")
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert data["total"] >= 1

        first_pack = data["items"][0]
        pack_id = first_pack["id"]

        # Inspect specific pack
        inspect_res = await client.get(f"/api/v1/solver/packs/{pack_id}")
        assert inspect_res.status_code == 200
        pack_data = inspect_res.json()
        assert pack_data["id"] == pack_id
        assert pack_data["board"] == first_pack["board"]
        assert "nodes_summary" in pack_data
        assert len(pack_data["nodes_summary"]) > 0

        # Query decision for root node
        first_combo = pack_data["root_combos"][0][0]["cards"]
        decision_res = await client.get(
            f"/api/v1/solver/packs/{pack_id}/decision",
            params={"node_id": 0, "combo": first_combo},
        )
        assert decision_res.status_code == 200
        decision_data = decision_res.json()
        assert decision_data["combo"] == first_combo
        assert len(decision_data["frequencies"]) == len(decision_data["actions"])
        assert pytest.approx(sum(decision_data["frequencies"]), abs=0.01) == 1.0

        # Verify pack integrity
        verify_res = await client.post(f"/api/v1/solver/packs/{pack_id}/verify")
        assert verify_res.status_code == 200
        assert verify_res.json()["intact"] is True

    async def test_create_solver_job_deduplication(self, client: AsyncClient) -> None:
        """Verify enqueuing a solve job for an already solved scenario reuses the pack."""
        # Query existing pack to get its exact config
        packs_res = await client.get("/api/v1/solver/packs")
        packs_data = packs_res.json()
        if packs_data["total"] > 0:
            existing = packs_data["items"][0]
            req_payload = {
                "config": {
                    "board": existing["board"],
                    "oop_range": existing["oop_range"],
                    "ip_range": existing["ip_range"],
                    "starting_pot": existing["starting_pot"],
                    "effective_stack": existing["effective_stack"],
                    "max_iterations": existing["iterations"],
                    "target_exploitability": 0.5,
                }
            }
            job_res = await client.post("/api/v1/solver/jobs", json=req_payload)
            assert job_res.status_code == 202
            data = job_res.json()
            assert data["reused"] is True
            assert data["status"] == "COMPLETED"
            assert data["pack"]["id"] == existing["id"]
