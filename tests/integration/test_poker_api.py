"""Integration tests for Poker Lab API endpoints (/api/v1/poker)."""

import pytest
from httpx import AsyncClient


class TestPokerApiEndpoints:
    """Integration test suite for poker HTTP endpoints."""

    async def test_parse_cards_endpoint(self, client: AsyncClient) -> None:
        """Verify POST /api/v1/poker/cards/parse returns parsed cards."""
        res = await client.post("/api/v1/poker/cards/parse", json={"cards": ["As", "Kh", "10d"]})
        assert res.status_code == 200
        data = res.json()
        assert data["count"] == 3
        notations = [c["notation"] for c in data["cards"]]
        assert notations == ["As", "Kh", "Td"]

    async def test_parse_duplicate_cards_returns_422(self, client: AsyncClient) -> None:
        """Duplicate cards in payload must be rejected with HTTP 422."""
        res = await client.post("/api/v1/poker/cards/parse", json={"cards": ["As", "Kh", "As"]})
        assert res.status_code == 422
        data = res.json()
        assert "detail" in data
        assert data["detail"]["code"] == "DUPLICATE_CARD"

    async def test_evaluate_hand_endpoint(self, client: AsyncClient) -> None:
        """Verify POST /api/v1/poker/hand/evaluate accurately evaluates a hand."""
        res = await client.post(
            "/api/v1/poker/hand/evaluate",
            json={"cards": ["As", "Ks", "Qs", "Js", "Ts"]},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["category"] == "Straight Flush"
        assert data["description"] == "Royal Flush"

    async def test_parse_range_endpoint(self, client: AsyncClient) -> None:
        """Verify POST /api/v1/poker/range/parse returns combo counts and percentages."""
        res = await client.post(
            "/api/v1/poker/range/parse",
            json={"range": "AA, AKs, 77+"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["combo_count"] > 0
        assert data["percentage"] > 0.0

    async def test_pot_odds_endpoint(self, client: AsyncClient) -> None:
        """Verify POST /api/v1/poker/math/pot-odds returns correct math."""
        res = await client.post(
            "/api/v1/poker/math/pot-odds",
            json={"call_amount": 50, "pot_before_call": 100, "bet_amount": 50},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["call_amount"] == 50
        assert data["pot_odds_fraction"] == 0.25
        assert data["required_equity_pct"] == 25.0
        assert data["alpha_bluff_break_even_pct"] == 33.33
        assert data["minimum_defense_frequency_pct"] == 66.67

    async def test_equity_endpoint(self, client: AsyncClient) -> None:
        """Verify POST /api/v1/poker/equity executes Monte Carlo simulation."""
        res = await client.post(
            "/api/v1/poker/equity",
            json={
                "players": [
                    {"name": "Alice", "range": "AhKh"},
                    {"name": "Bob", "range": "QcQd"},
                ],
                "board": [],
                "samples": 1000,
                "seed": 42,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data["results"]) == 2
        p1 = data["results"][0]
        p2 = data["results"][1]
        assert p1["equity"] + p2["equity"] == pytest.approx(100.0, abs=0.1)

    async def test_start_game_endpoint(self, client: AsyncClient) -> None:
        """Verify POST /api/v1/poker/game/start initializes hand and returns scenario."""
        res = await client.post(
            "/api/v1/poker/game/start",
            json={
                "small_blind": 5,
                "big_blind": 10,
                "players": [
                    {"player_id": "alice", "starting_stack": 1000},
                    {"player_id": "bob", "starting_stack": 1000},
                ],
                "button_seat": 0,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert "game_state" in data
        assert "scenario" in data
        assert data["game_state"]["street"] == "preflop"
        assert len(data["scenario"]["canonical_hash"]) == 64
