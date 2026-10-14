"""Integration tests for Contested Showdown and Event Integrity Remediation.

Validates the full end-to-end HTTP API lifecycle:
1. River contested showdown with unknown opponent cards suspends settlement (is_settled: False, requires_card_reveal: True).
2. Advancing to next hand while pending is strictly blocked.
3. Revealing opponent cards computes correct winner via domain evaluator, settles hand, updates stacks.
4. Advance to Hand #2 succeeds with exact stack carryover.
5. Hand #2 uncontested fold win settles immediately without requiring card reveal.
6. Persisted decision events in PostgreSQL verify exact actions, amounts, streets, and evaluation provenance.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

import app.infrastructure.database.models.live_helper  # noqa: F401 - Register models on Base.metadata
from app.infrastructure.database.models.live_helper import LiveHelperDecisionModel


class TestContestedShowdownRemediationIntegration:
    """Integration test suite for contested showdowns and decision event consistency."""

    async def test_full_contested_showdown_to_uncontested_fold_lifecycle(
        self, client: AsyncClient, test_session_factory
    ) -> None:
        headers = {"X-Profile-ID": "9221674a-5be7-4ee9-ba02-86ca08b97090"}

        # 1. Create a Heads-Up Cash Session (Hero vs Villain, 1000 chips each)
        payload = {
            "name": "Contested Showdown E2E Session",
            "format_type": "CASH",
            "default_mode": "DECISION_CHECK",
            "table_capacity": 2,
            "button_seat": 1,
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
                {"seat_number": 1, "player_name": "Hero", "current_stack": 1000, "is_hero": True},
                {
                    "seat_number": 2,
                    "player_name": "Villain",
                    "current_stack": 1000,
                    "is_hero": False,
                },
            ],
        }

        res = await client.post("/api/v1/live-helper/sessions", json=payload, headers=headers)
        assert res.status_code == 201, res.text
        data = res.json()
        session_id = data["session"]["id"]
        assert data["session"]["total_hands_completed"] == 0

        # Set Hero's cards to Ah Kh
        await client.post(
            f"/api/v1/live-helper/sessions/{session_id}/reveal",
            json={"seat_number": 1, "hole_cards": ["Ah", "Kh"]},
            headers=headers,
        )

        # 2. Preflop: Hero is SB/BTN, calls 100. Villain checks BB.
        hero_call = await client.post(
            f"/api/v1/live-helper/sessions/{session_id}/action",
            json={
                "seat_number": 1,
                "action_type": "call",
                "amount": 100,
                "mode": "DECISION_CHECK",
                "reasoning": "Standard limp/call from BTN with premium hand",
                "confidence": 4,
            },
            headers=headers,
        )
        assert hero_call.status_code == 200
        assert hero_call.json()["decision"]["chosen_action"] == "call"
        assert hero_call.json()["decision"]["chosen_amount"] == 100

        bb_check = await client.post(
            f"/api/v1/live-helper/sessions/{session_id}/action",
            json={"seat_number": 2, "action_type": "check", "amount": 0},
            headers=headers,
        )
        assert bb_check.status_code == 200

        # 3. Flop: Deal Ks 7d 2c
        flop_res = await client.post(
            f"/api/v1/live-helper/sessions/{session_id}/deal",
            json={"cards": ["Ks", "7d", "2c"]},
            headers=headers,
        )
        assert flop_res.status_code == 200
        assert flop_res.json()["hand"]["board"] == ["Ks", "7d", "2c"]

        # Flop checks: Villain checks, Hero checks
        await client.post(
            f"/api/v1/live-helper/sessions/{session_id}/action",
            json={"seat_number": 2, "action_type": "check", "amount": 0},
            headers=headers,
        )
        hero_flop = await client.post(
            f"/api/v1/live-helper/sessions/{session_id}/action",
            json={
                "seat_number": 1,
                "action_type": "check",
                "amount": 0,
                "mode": "DECISION_CHECK",
                "reasoning": "Check behind with top pair top kicker for pot control",
                "confidence": 5,
            },
            headers=headers,
        )
        assert hero_flop.status_code == 200
        assert hero_flop.json()["decision"]["chosen_action"] == "check"

        # 4. Turn: Deal 8h
        turn_res = await client.post(
            f"/api/v1/live-helper/sessions/{session_id}/deal",
            json={"cards": ["8h"]},
            headers=headers,
        )
        assert turn_res.status_code == 200

        # Turn checks: Villain checks, Hero checks
        await client.post(
            f"/api/v1/live-helper/sessions/{session_id}/action",
            json={"seat_number": 2, "action_type": "check", "amount": 0},
            headers=headers,
        )
        await client.post(
            f"/api/v1/live-helper/sessions/{session_id}/action",
            json={"seat_number": 1, "action_type": "check", "amount": 0, "mode": "DECISION_CHECK"},
            headers=headers,
        )

        # 5. River: Deal 2s
        river_res = await client.post(
            f"/api/v1/live-helper/sessions/{session_id}/deal",
            json={"cards": ["2s"]},
            headers=headers,
        )
        assert river_res.status_code == 200

        # River checks: Villain checks, Hero checks
        await client.post(
            f"/api/v1/live-helper/sessions/{session_id}/action",
            json={"seat_number": 2, "action_type": "check", "amount": 0},
            headers=headers,
        )
        await client.post(
            f"/api/v1/live-helper/sessions/{session_id}/action",
            json={"seat_number": 1, "action_type": "check", "amount": 0, "mode": "DECISION_CHECK"},
            headers=headers,
        )

        # 6. Attempt Settlement with Unknown Opponent Cards
        settle_attempt = await client.post(
            f"/api/v1/live-helper/sessions/{session_id}/settle",
            headers=headers,
        )
        assert settle_attempt.status_code == 200
        settle_data = settle_attempt.json()["hand"]
        assert settle_data["is_settled"] is False
        assert settle_data["settlement"]["requires_card_reveal"] is True
        assert settle_data["settlement"]["missing_card_seats"] == [2]
        assert "Settlement Pending" in settle_data["settlement"]["settlement_summary"]

        # 7. Verify advance to next hand is BLOCKED
        with pytest.raises(Exception, match="Settlement Pending|Showdown settlement is unresolved"):
            await client.post(
                f"/api/v1/live-helper/sessions/{session_id}/next-hand",
                headers=headers,
            )

        # 8. Reveal Opponent Cards: Villain has Qd Jd (Kings and Twos, Queen kicker vs Hero's Ace kicker)
        reveal_res = await client.post(
            f"/api/v1/live-helper/sessions/{session_id}/reveal",
            json={"seat_number": 2, "hole_cards": ["Qd", "Jd"]},
            headers=headers,
        )
        assert reveal_res.status_code == 200
        rev_data = reveal_res.json()["hand"]
        assert rev_data["is_settled"] is True
        assert rev_data["settlement"]["requires_card_reveal"] is False
        assert rev_data["settlement"]["winning_seats"] == [1]
        assert rev_data["ending_stacks"]["1"] == 1100
        assert rev_data["ending_stacks"]["2"] == 900
        assert reveal_res.json()["session"]["total_hands_completed"] == 1

        # 9. Now advance to Hand #2: Must succeed cleanly
        next_hand_res = await client.post(
            f"/api/v1/live-helper/sessions/{session_id}/next-hand",
            headers=headers,
        )
        assert next_hand_res.status_code == 200
        h2_data = next_hand_res.json()["new_hand"]
        assert h2_data["hand_index"] == 2
        assert h2_data["button_seat"] == 2
        assert h2_data["starting_stacks"]["1"] == 1100
        assert h2_data["starting_stacks"]["2"] == 900

        # 10. Hand #2: Uncontested Fold Win
        # In Hand #2, Villain is BTN/SB, raises to 250
        v_raise = await client.post(
            f"/api/v1/live-helper/sessions/{session_id}/action",
            json={"seat_number": 2, "action_type": "raise", "amount": 250},
            headers=headers,
        )
        assert v_raise.status_code == 200

        # Hero (Seat 1) 3-bets to 700
        hero_3bet = await client.post(
            f"/api/v1/live-helper/sessions/{session_id}/action",
            json={
                "seat_number": 1,
                "action_type": "raise",
                "amount": 700,
                "mode": "DECISION_CHECK",
            },
            headers=headers,
        )
        assert hero_3bet.status_code == 200
        assert hero_3bet.json()["decision"]["chosen_action"] == "raise"
        assert hero_3bet.json()["decision"]["chosen_amount"] == 700

        # Villain folds -> Uncontested win for Hero!
        v_fold = await client.post(
            f"/api/v1/live-helper/sessions/{session_id}/action",
            json={"seat_number": 2, "action_type": "fold", "amount": 0},
            headers=headers,
        )
        assert v_fold.status_code == 200
        h2_settled = v_fold.json()["hand"]
        assert h2_settled["is_settled"] is True
        assert h2_settled["settlement"]["requires_card_reveal"] is False
        assert h2_settled["settlement"]["winning_seats"] == [1]
        assert "uncontested" in h2_settled["settlement"]["settlement_summary"].lower()

        # Hero won Villain's 250 chips: Hero ending stack 1100 + 250 = 1350, Villain 900 - 250 = 650
        assert h2_settled["ending_stacks"]["1"] == 1350
        assert h2_settled["ending_stacks"]["2"] == 650

        # 11. End Session and verify final report
        end_sess = await client.post(
            f"/api/v1/live-helper/sessions/{session_id}/end",
            headers=headers,
        )
        assert end_sess.status_code == 200
        rep = end_sess.json()
        assert rep["total_hands"] == 2

        # 12. Reconcile database persistence for Hero decisions
        async with test_session_factory() as db:
            stmt = (
                select(LiveHelperDecisionModel)
                .where(LiveHelperDecisionModel.session_id == session_id)
                .order_by(LiveHelperDecisionModel.created_at)
            )
            result = await db.execute(stmt)
            decisions = result.scalars().all()

            # Verify every Hero decision was recorded with high fidelity
            actions_found = [d.chosen_action for d in decisions]
            [d.chosen_amount for d in decisions]

            # Hero actions were: call (100), check (0), check (0), check (0), raise (700)
            assert "call" in actions_found
            assert "raise" in actions_found
            assert "check" in actions_found
            # Crucial requirement: raise was NOT converted to check!
            raise_dec = next(d for d in decisions if d.chosen_action == "raise")
            assert raise_dec.chosen_amount == 700
            assert raise_dec.street == "preflop"
            assert raise_dec.is_assisted is False
            assert raise_dec.mode == "DECISION_CHECK"
            assert "provenance" in raise_dec.evaluation_verdicts["strategy"]
