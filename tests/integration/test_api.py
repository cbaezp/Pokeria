"""Integration tests for FastAPI endpoints."""

from httpx import AsyncClient


class TestHealthAndReadinessEndpoints:
    """Test suite for health and readiness probes."""

    async def test_health_check_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "pokerlab-api"
        assert "timestamp" in data
        assert "X-Request-ID" in response.headers

    async def test_correlation_id_propagation(self, client: AsyncClient) -> None:
        custom_id = "test-corr-id-999"
        response = await client.get("/api/v1/health", headers={"X-Request-ID": custom_id})
        assert response.status_code == 200
        assert response.headers["X-Request-ID"] == custom_id


class TestProfileEndpoints:
    """Test suite for Profile API endpoints."""

    async def test_create_and_retrieve_profile(self, client: AsyncClient) -> None:
        payload = {
            "username": "chip_leader",
            "display_name": "Chip Leader",
            "email": "chipleader@pokerlab.test",
            "preferences": {"theme": "dark", "deck_color": "four_color"},
        }
        create_res = await client.post("/api/v1/profiles", json=payload)
        assert create_res.status_code == 201
        created = create_res.json()
        assert created["id"] is not None
        assert created["username"] == "chip_leader"
        assert created["display_name"] == "Chip Leader"
        assert created["preferences"]["theme"] == "dark"

        # Retrieve profile by ID
        get_res = await client.get(f"/api/v1/profiles/{created['id']}")
        assert get_res.status_code == 200
        retrieved = get_res.json()
        assert retrieved["id"] == created["id"]
        assert retrieved["email"] == "chipleader@pokerlab.test"

    async def test_create_profile_validation_error(self, client: AsyncClient) -> None:
        # Invalid payload: username contains invalid characters
        payload = {
            "username": "invalid username with spaces!",
            "display_name": "Test",
            "email": "valid@email.com",
        }
        res = await client.post("/api/v1/profiles", json=payload)
        assert res.status_code == 422
        data = res.json()
        assert "error" in data
        assert "request_id" in data["error"]

    async def test_duplicate_username_conflict(self, client: AsyncClient) -> None:
        payload1 = {
            "username": "poker_shark",
            "display_name": "Shark 1",
            "email": "shark1@pokerlab.test",
        }
        res1 = await client.post("/api/v1/profiles", json=payload1)
        assert res1.status_code == 201

        payload2 = {
            "username": "poker_shark",
            "display_name": "Shark 2",
            "email": "shark2@pokerlab.test",
        }
        res2 = await client.post("/api/v1/profiles", json=payload2)
        assert res2.status_code == 409
        data = res2.json()
        assert data["error"]["code"] == "DUPLICATE_PROFILE_USERNAME"

    async def test_get_nonexistent_profile_returns_404(self, client: AsyncClient) -> None:
        res = await client.get("/api/v1/profiles/00000000-0000-0000-0000-000000000000")
        assert res.status_code == 404
        data = res.json()
        assert data["error"]["code"] == "PROFILE_NOT_FOUND"

    async def test_list_and_update_profiles(self, client: AsyncClient) -> None:
        # Create profile
        p_res = await client.post(
            "/api/v1/profiles",
            json={"username": "grinder", "display_name": "Grinder", "email": "grind@pokerlab.io"},
        )
        pid = p_res.json()["id"]

        # List
        list_res = await client.get("/api/v1/profiles")
        assert list_res.status_code == 200
        assert len(list_res.json()) >= 1

        # Update
        patch_res = await client.patch(
            f"/api/v1/profiles/{pid}",
            json={"display_name": "High Roller", "preferences": {"sound": False}},
        )
        assert patch_res.status_code == 200
        updated = patch_res.json()
        assert updated["display_name"] == "High Roller"
        assert updated["preferences"]["sound"] is False

    async def test_unprivileged_client_cannot_assert_test_profile(
        self, client: AsyncClient
    ) -> None:
        """Unprivileged clients attempting to pass is_test_profile=True receive 403 Forbidden."""
        payload = {
            "username": "hacker_trying_test",
            "display_name": "Hacker",
            "email": "hacker@domain.com",
            "is_test_profile": True,
        }
        res = await client.post("/api/v1/profiles", json=payload)
        assert res.status_code == 403
        data = res.json()
        assert data["error"]["code"] == "PERMISSION_DENIED"

    async def test_invalid_audit_token_rejected_with_403(self, client: AsyncClient) -> None:
        """Supplying an incorrect X-Internal-Audit-Token fails closed with 403 Forbidden."""
        payload = {
            "username": "unauthorized_auditor",
            "display_name": "Unauthorized Auditor",
            "email": "auditor@domain.com",
            "is_test_profile": True,
        }
        res = await client.post(
            "/api/v1/profiles",
            json=payload,
            headers={"X-Internal-Audit-Token": "completely-invalid-secret-token"},
        )
        assert res.status_code == 403
        data = res.json()
        assert data["error"]["code"] == "PERMISSION_DENIED"

    async def test_unset_audit_token_fails_closed(self, client: AsyncClient, monkeypatch) -> None:
        """When INTERNAL_AUDIT_TOKEN is None (default), privileged assertion fails closed."""
        from app.core.config import get_settings

        settings = get_settings()
        monkeypatch.setattr(settings, "INTERNAL_AUDIT_TOKEN", None)

        payload = {
            "username": "audit_caller_when_unset",
            "display_name": "Audit Caller",
            "email": "caller@audit.internal",
            "is_test_profile": True,
        }
        res = await client.post(
            "/api/v1/profiles",
            json=payload,
            headers={"X-Internal-Audit-Token": "some-token"},
        )
        assert res.status_code == 403
        data = res.json()
        assert data["error"]["code"] == "PERMISSION_DENIED"

    async def test_privileged_audit_client_asserts_test_profile(
        self, client: AsyncClient, monkeypatch
    ) -> None:
        """Privileged audit clients with valid runtime X-Internal-Audit-Token create is_test_profile=True."""
        from app.core.config import get_settings

        secret_token = "runtime-secret-audit-key-2026-xyz"
        settings = get_settings()
        monkeypatch.setattr(settings, "INTERNAL_AUDIT_TOKEN", secret_token)

        payload = {
            "username": "trusted_audit_bot",
            "display_name": "Audit Bot",
            "email": "bot@audit.pokerlab",
            "is_test_profile": True,
        }
        res = await client.post(
            "/api/v1/profiles",
            json=payload,
            headers={"X-Internal-Audit-Token": secret_token},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["is_test_profile"] is True

    async def test_genuine_learner_with_test_substring_not_flagged(
        self, client: AsyncClient
    ) -> None:
        """Real learners with names containing substrings like test, audit, bench are not flagged as test profiles."""
        payload = {
            "username": "contest_winner_99",
            "display_name": "Contest Pro",
            "email": "winner@gmail.com",
            "is_test_profile": False,
        }
        res = await client.post("/api/v1/profiles", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["is_test_profile"] is False


class TestJobEndpoints:
    """Test suite for background job endpoints."""

    async def test_submit_and_get_job(self, client: AsyncClient) -> None:
        payload = {
            "job_type": "demonstration_task",
            "payload": {"message": "integration_test_message", "iterations": 10},
            "idempotency_key": "idem-key-100",
        }
        res = await client.post("/api/v1/jobs", json=payload)
        assert res.status_code == 201
        job = res.json()
        assert job["id"] is not None
        assert job["job_type"] == "demonstration_task"
        assert job["status"] == "PENDING"
        assert job["idempotency_key"] == "idem-key-100"

        # Duplicate submission with same idempotency key returns 200 and same job
        res_dup = await client.post("/api/v1/jobs", json=payload)
        assert res_dup.status_code == 200
        assert res_dup.json()["id"] == job["id"]

        # Get job by ID
        get_res = await client.get(f"/api/v1/jobs/{job['id']}")
        assert get_res.status_code == 200
        assert get_res.json()["id"] == job["id"]
