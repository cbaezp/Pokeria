"""Unit tests for canonical scenario serialization, hashing, and replay."""

from app.domain.poker.cards import Deck
from app.domain.poker.game_state import Action, ActionType, GameConfig, GameState
from app.domain.poker.scenario import PokerScenario


class TestScenarioModel:
    """Test suite for deterministic scenario canonicalization and replay."""

    def test_scenario_creation_and_canonical_hash_stability(self) -> None:
        """Verify identical game states produce identical SHA-256 hashes."""
        cfg = GameConfig(small_blind=5, big_blind=10, max_players=2)
        # Use fixed deck order for reproducibility
        deck1 = Deck()
        deck1.shuffle(seed=42)
        state1 = GameState.start_hand(
            config=cfg,
            players_data=[("alice", 1000), ("bob", 1000)],
            deck=deck1,
        )

        deck2 = Deck()
        deck2.shuffle(seed=42)
        state2 = GameState.start_hand(
            config=cfg,
            players_data=[("alice", 1000), ("bob", 1000)],
            deck=deck2,
        )

        scen1 = PokerScenario.from_game_state(state1)
        scen2 = PokerScenario.from_game_state(state2)

        hash1 = scen1.canonical_hash()
        hash2 = scen2.canonical_hash()

        assert len(hash1) == 64
        assert hash1 == hash2

    def test_json_roundtrip_serialization(self) -> None:
        """Verify scenario serializes to JSON and deserializes identically."""
        cfg = GameConfig(small_blind=10, big_blind=20, max_players=3)
        state = GameState.start_hand(
            config=cfg,
            players_data=[("p1", 500), ("p2", 800), ("p3", 1200)],
        )
        scenario = PokerScenario.from_game_state(state)
        json_str = scenario.to_canonical_json()

        deserialized = PokerScenario.from_canonical_json(json_str)
        assert deserialized.canonical_hash() == scenario.canonical_hash()
        assert deserialized.small_blind == scenario.small_blind
        assert deserialized.big_blind == scenario.big_blind
        assert len(deserialized.players) == len(scenario.players)

    def test_scenario_replay(self) -> None:
        """Verify replaying action history reconstructs active game state."""
        cfg = GameConfig(small_blind=5, big_blind=10, max_players=2)
        deck = Deck()
        deck.shuffle(seed=99)
        deck_cards_snapshot = list(deck.cards)

        state = GameState.start_hand(
            config=cfg,
            players_data=[("alice", 500), ("bob", 500)],
            deck=deck,
        )
        # Alice calls, Bob checks
        state = state.apply_action(Action("alice", ActionType.CALL, 5))
        state = state.apply_action(Action("bob", ActionType.CHECK))

        scenario = PokerScenario.from_game_state(state)
        # Replay should reproduce flop state
        replayed_state = scenario.replay_actions(starting_deck_cards=deck_cards_snapshot)

        assert replayed_state.street == state.street
        assert replayed_state.community_cards == state.community_cards
        assert replayed_state.players[0].stack == state.players[0].stack
        assert replayed_state.players[1].stack == state.players[1].stack
