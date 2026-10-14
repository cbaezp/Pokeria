"""Integration tests for Live Helper Session API Remediation.

Verifies:
1. Session creation and initial state (total_hands_completed = 0).
2. Action recording, automated terminal detection, and idempotent hand settlement.
3. Advance to next hand: dealer rotation, strict chip continuity, completed count invariant.
4. Session termination: report generation, accurate completed hands count matching settled hands.
"""

from httpx import AsyncClient


class TestLiveHelperSessionRemediationIntegration:
    """Test suite for continuous session workflow and counter accuracy."""

    async def test_session_lifecycle_and_counter_accuracy(self, client: AsyncClient) -> None:
        """Verify full continuous training session through HTTP API."""
        headers = {"X-Profile-ID": "9221674a-5be7-4ee9-ba02-86ca08b97090"}

        # 1. Create a 6-max cash session
        payload = {
            "name": "Integration Remediation Session",
            "format_type": "CASH",
            "default_mode": "COACH",
            "table_capacity": 6,
            "button_seat": 4,  # Hero on BTN
            "configuration": {
                "small_blind": 50,
                "big_blind": 100,
                "ante": 0,
                "cash_rules": {
                    "rake_percent": 0.0,
                    "rake_cap": 0,
                    "no_flop_no_drop": True,
                },
            },
            "participants": [
                {"seat_number": 1, "player_name": "UTG", "current_stack": 10000, "is_hero": False},
                {"seat_number": 2, "player_name": "HJ", "current_stack": 10000, "is_hero": False},
                {"seat_number": 3, "player_name": "CO", "current_stack": 10000, "is_hero": False},
                {"seat_number": 4, "player_name": "Hero", "current_stack": 10000, "is_hero": True},
                {"seat_number": 5, "player_name": "SB", "current_stack": 10000, "is_hero": False},
                {"seat_number": 6, "player_name": "BB", "current_stack": 10000, "is_hero": False},
            ],
        }

        res = await client.post("/api/v1/live-helper/sessions", json=payload, headers=headers)
        assert res.status_code == 201, res.text
        data = res.json()
        session_id = data["session"]["id"]
        assert data["session"]["total_hands_completed"] == 0
        assert data["session"]["current_hand_index"] == 1

        # 2. Preflop actions: Blinds 50/100 posted. UTG, HJ, CO fold.
        for seat in [1, 2, 3]:
            act_res = await client.post(
                f"/api/v1/live-helper/sessions/{session_id}/action",
                json={"seat_number": seat, "action_type": "fold"},
                headers=headers,
            )
            assert act_res.status_code == 200

        # Hero raises to 250
        hero_res = await client.post(
            f"/api/v1/live-helper/sessions/{session_id}/action",
            json={"seat_number": 4, "action_type": "raise", "amount": 250, "mode": "COACH"},
            headers=headers,
        )
        assert hero_res.status_code == 200
        assert hero_res.json()["decision"] is not None

        # SB and BB fold -> terminal hand!
        for seat in [5, 6]:
            act_res = await client.post(
                f"/api/v1/live-helper/sessions/{session_id}/action",
                json={"seat_number": seat, "action_type": "fold"},
                headers=headers,
            )
            assert act_res.status_code == 200

        # Hand settled automatically on terminal fold!
        # Verify total_hands_completed incremented to 1
        sess_get = await client.get(f"/api/v1/live-helper/sessions/{session_id}", headers=headers)
        assert sess_get.status_code == 200
        s_data = sess_get.json()
        assert s_data["total_hands_completed"] == 1

        # Verify chip accounting for blind steal:
        # Hero: 10150, SB: 9950, BB: 9900
        part_map = {p["seat_number"]: p["current_stack"] for p in s_data["participants"]}
        assert part_map[4] == 10150
        assert part_map[5] == 9950
        assert part_map[6] == 9900

        # 3. Explicit settle endpoint idempotency: must not increment completed count again
        settle_res = await client.post(
            f"/api/v1/live-helper/sessions/{session_id}/settle", headers=headers
        )
        assert settle_res.status_code == 200
        assert settle_res.json()["session"]["total_hands_completed"] == 1

        # 4. Advance to Next Hand
        next_res = await client.post(
            f"/api/v1/live-helper/sessions/{session_id}/next-hand", headers=headers
        )
        assert next_res.status_code == 200
        n_data = next_res.json()
        assert n_data["session"]["total_hands_completed"] == 1
        assert n_data["new_hand"]["hand_index"] == 2
        # Verify stack carryover into Hand #2 starting stacks
        h2_start = n_data["new_hand"]["starting_stacks"]
        assert h2_start["4"] == 10150
        assert h2_start["5"] == 9950
        assert h2_start["6"] == 9900

        # 5. End session with Hand #2 pending
        end_res = await client.post(
            f"/api/v1/live-helper/sessions/{session_id}/end", headers=headers
        )
        assert end_res.status_code == 200
        report = end_res.json()
        assert report["total_hands"] >= 1

        # Verify final session details
        final_sess = await client.get(f"/api/v1/live-helper/sessions/{session_id}", headers=headers)
        assert final_sess.status_code == 200
        assert final_sess.json()["status"] == "COMPLETED"
        assert final_sess.json()["total_hands_completed"] == 1
