"""Integration test tracing preflop cash and tournament decisions through the full training session lifecycle."""

import pytest
from httpx import AsyncClient


class TestPreflopTrainingIntegration:
    """End-to-end integration trace for cash-game and tournament preflop training."""

    async def _create_test_profile(self, client: AsyncClient) -> str:
        import uuid

        uname = f"preflop_hero_{uuid.uuid4().hex[:6]}"
        res = await client.post(
            "/api/v1/profiles",
            json={
                "username": uname,
                "display_name": "Preflop Specialist",
                "email": f"{uname}@example.com",
            },
        )
        assert res.status_code == 201
        return res.json()["id"]

    @pytest.mark.asyncio
    async def test_cash_preflop_decision_trace(self, client: AsyncClient) -> None:
        """Trace a Cash 6-Max BTN RFI scenario end-to-end:
        Scenario -> Session -> Decision Submission -> Grading -> Persistence.
        """
        profile_id = await self._create_test_profile(client)

        # 1. Create a session targeting preflop
        create_res = await client.post(
            "/api/v1/training/sessions",
            json={
                "profile_id": profile_id,
                "mode": "GUIDED",
                "target_decisions": 5,
                "selected_categories": ["preflop"],
                "initial_scenario_id": "pack_cash_6max_100bb_btn_rfi_AsKs",
            },
        )
        assert create_res.status_code == 201
        session_data = create_res.json()
        session_id = session_data["id"]
        assert session_data["completed_decisions"] == 0

        # 2. Get current active exercise
        next_res = await client.get(f"/api/v1/training/sessions/{session_id}/next")
        assert next_res.status_code == 200
        scenario = next_res.json()
        assert scenario["street"] == "preflop"
        legal_actions = scenario["legal_actions"]
        assert len(legal_actions) >= 2
        raise_action = next(
            (a for a in legal_actions if a["kind"].lower() == "raise"), legal_actions[0]
        )

        # 3. Submit decision: Raise
        submit_res = await client.post(
            f"/api/v1/training/sessions/{session_id}/decision",
            json={
                "chosen_action": raise_action["kind"],
                "chosen_amount": raise_action.get("amount", 2.5),
                "latency_ms": 1200,
            },
        )
        assert submit_res.status_code == 200
        evaluation = submit_res.json()
        assert evaluation["chosen_action"] == raise_action["kind"]
        assert evaluation["grade"] in ("STRONG", "ACCEPTABLE", "INACCURACY", "MISTAKE", "BLUNDER")
        assert evaluation["session_progress"]["completed_decisions"] == 1

        # 4. Verify decision persisted in DB
        list_dec = await client.get(f"/api/v1/training/sessions/{session_id}/decisions")
        assert list_dec.status_code == 200
        assert len(list_dec.json()) == 1

    @pytest.mark.asyncio
    async def test_tournament_preflop_decision_trace(self, client: AsyncClient) -> None:
        """Trace a Tournament 12bb SB Shove scenario end-to-end:
        Specific scenario -> Session -> All-In Decision -> Solver Action EV Grading -> Persistence.
        """
        profile_id = await self._create_test_profile(client)

        target_scen_id = "pack_tourn_8max_12bb_sb_shove_bba_chipev_AsKs"

        create_res = await client.post(
            "/api/v1/training/sessions",
            json={
                "profile_id": profile_id,
                "mode": "GUIDED",
                "target_decisions": 3,
                "initial_scenario_id": target_scen_id,
            },
        )
        assert create_res.status_code == 201
        session_id = create_res.json()["id"]

        # Fetch exercise
        next_res = await client.get(f"/api/v1/training/sessions/{session_id}/next")
        assert next_res.status_code == 200
        scenario = next_res.json()
        assert scenario["id"] == target_scen_id

        # Submit All-In with AKs
        submit_res = await client.post(
            f"/api/v1/training/sessions/{session_id}/decision",
            json={
                "chosen_action": "All-In",
                "chosen_amount": 12.0,
                "latency_ms": 950,
            },
        )
        assert submit_res.status_code == 200
        evaluation = submit_res.json()
        assert evaluation["grade"] == "STRONG"
        assert evaluation["best_action"] == "All-In"
        assert evaluation["chosen_action_ev"] is not None
        assert evaluation["raw_ev_loss"] == 0.0
        assert evaluation["session_progress"]["completed_decisions"] == 1

        # Verify persisted
        list_dec = await client.get(f"/api/v1/training/sessions/{session_id}/decisions")
        assert len(list_dec.json()) == 1

    @pytest.mark.asyncio
    async def test_tournament_bubble_quarantined_trace(self, client: AsyncClient) -> None:
        """Trace a Tournament 15bb Bubble Shove scenario under CSTE_POLICY_PENDING:
        Verify raw action EV preserved while categorical grade is suspended.
        """
        profile_id = await self._create_test_profile(client)

        target_scen_id = "pack_tourn_8max_15bb_bubble_sb_shove_icm_AsKs"

        create_res = await client.post(
            "/api/v1/training/sessions",
            json={
                "profile_id": profile_id,
                "mode": "GUIDED",
                "target_decisions": 3,
                "initial_scenario_id": target_scen_id,
            },
        )
        assert create_res.status_code == 201
        session_id = create_res.json()["id"]

        next_res = await client.get(f"/api/v1/training/sessions/{session_id}/next")
        assert next_res.status_code == 200

        submit_res = await client.post(
            f"/api/v1/training/sessions/{session_id}/decision",
            json={
                "chosen_action": "All-In",
                "chosen_amount": 15.0,
                "latency_ms": 1100,
            },
        )
        assert submit_res.status_code == 200
        evaluation = submit_res.json()
        assert evaluation["grading_provenance"] == "CSTE_POLICY_PENDING"
        assert evaluation["grade"] == "UNGRADED"
        assert evaluation["raw_ev_loss"] is not None
        assert evaluation["session_progress"]["completed_decisions"] == 1

    @pytest.mark.asyncio
    async def test_complete_cash_learning_journey(self, client: AsyncClient) -> None:
        """Full Cash Preflop User Journey:
        1. Profile Creation
        2. Inspect Preflop Packs
        3. Start Cash Preflop Drill Session
        4. Make Raise Decision
        5. Receive Verified Heuristic Feedback
        6. Record History & Progress
        7. Inspect Assessment Capabilities & Due Retention Reviews
        """
        # 1. Profile Creation
        profile_id = await self._create_test_profile(client)

        # 2. Inspect Preflop Packs
        pack_res = await client.get("/api/v1/preflop/packs")
        assert pack_res.status_code == 200
        packs = pack_res.json()["packs"]
        btn_pack = next((p for p in packs if p["pack_id"] == "cash_6max_100bb_btn_rfi"), None)
        assert btn_pack is not None
        assert btn_pack["source_type"] == "INSTRUCTIONAL_HEURISTIC"

        # 3. Start Cash Drill Session
        session_res = await client.post(
            "/api/v1/training/sessions",
            json={
                "profile_id": profile_id,
                "mode": "GUIDED",
                "target_decisions": 1,
                "initial_scenario_id": "pack_cash_6max_100bb_btn_rfi_AsKs",
            },
        )
        assert session_res.status_code == 201
        session_id = session_res.json()["id"]

        # 4. Fetch exercise
        ex_res = await client.get(f"/api/v1/training/sessions/{session_id}/next")
        assert ex_res.status_code == 200
        ex = ex_res.json()
        assert ex["hero_position"] == "BTN"
        assert ex["effective_stack"] == 100.0

        # 5. Submit Raise Decision
        dec_res = await client.post(
            f"/api/v1/training/sessions/{session_id}/decision",
            json={"chosen_action": "Raise", "chosen_amount": 2.5, "latency_ms": 850},
        )
        assert dec_res.status_code == 200
        evaluation = dec_res.json()
        assert evaluation["grade"] == "STRONG"
        assert evaluation["grading_provenance"] == "INSTRUCTIONAL_HEURISTIC"

        # 6. Verify Progress & History
        history_res = await client.get(f"/api/v1/training/sessions/{session_id}/decisions")
        assert history_res.status_code == 200
        assert len(history_res.json()) == 1

        # 7. Check Assessment Capabilities via Item Bank
        from app.domain.assessment.item_bank import AssessmentItemBank
        from app.domain.assessment.models import AssessmentTier

        bank = AssessmentItemBank()
        bank.initialize()
        gate = bank.evaluate_capability_gate(
            tier=AssessmentTier.TIER1_RETEST,
            exposed_scenarios={"pack_cash_6max_100bb_btn_rfi_AsKs"},
            exposed_combos={"AsKs"},
            exposed_nodes={0},
            exposed_boards={""},
        )
        assert gate is not None

    @pytest.mark.asyncio
    async def test_complete_tournament_learning_journey(self, client: AsyncClient) -> None:
        """Full Tournament Preflop User Journey (ICM Quarantined):
        1. Profile Creation
        2. Inspect Tournament Preflop Packs
        3. Start Tournament Bubble Drill Session
        4. Submit Decision
        5. Receive Raw CSTE Feedback with Suspended Categorical Severity
        6. Verify Quarantined Items Withheld from High-Stakes Assessment Tiers
        """
        profile_id = await self._create_test_profile(client)

        # 2. Inspect Tournament Packs
        pack_res = await client.get("/api/v1/preflop/packs")
        packs = pack_res.json()["packs"]
        bubble_pack = next(
            (p for p in packs if p["pack_id"] == "tourn_8max_15bb_bubble_sb_shove_icm"), None
        )
        assert bubble_pack is not None
        assert bubble_pack["game_context"] == "TOURNAMENT"

        # 3. Start Session
        sess_res = await client.post(
            "/api/v1/training/sessions",
            json={
                "profile_id": profile_id,
                "mode": "GUIDED",
                "target_decisions": 1,
                "initial_scenario_id": "pack_tourn_8max_15bb_bubble_sb_shove_icm_AsKs",
            },
        )
        assert sess_res.status_code == 201
        session_id = sess_res.json()["id"]

        # 4. Submit Decision
        dec_res = await client.post(
            f"/api/v1/training/sessions/{session_id}/decision",
            json={"chosen_action": "All-In", "chosen_amount": 15.0, "latency_ms": 950},
        )
        assert dec_res.status_code == 200
        eval_data = dec_res.json()
        assert eval_data["grade"] == "UNGRADED"
        assert eval_data["raw_ev_loss"] is not None
        assert "Tournament Action Regret Policy V2" in eval_data["solution_quality_note"]

        # 6. Verify Capability Gate withholds quarantined tournament items
        from app.domain.assessment.item_bank import AssessmentItemBank

        bank = AssessmentItemBank()
        bank.initialize()
        tourn_items = [i for i in bank.list_all_items() if i.payoff_unit == "cste"]
        assert len(tourn_items) == 4
        for item in tourn_items:
            assert item.is_quarantined is True
            assert item.supported_tiers == []
