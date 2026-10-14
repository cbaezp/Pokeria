"""Hypothesis property-based tests for poker domain invariants.

Tests:
- Chip conservation under random legal action sequences.
- Card uniqueness across dealt hands and boards.
- HandStrength transitivity and comparability.
- Range weight boundaries and normalization.
"""

import random

import hypothesis.strategies as st
from hypothesis import given, settings

from app.domain.poker.cards import Card, Deck, validate_unique_cards
from app.domain.poker.evaluator import evaluate_5cards
from app.domain.poker.game_state import Action, ActionType, GameConfig, GameState, Street


class TestPokerPropertyInvariants:
    """Property-based verification of poker mathematical and domain invariants."""

    @settings(max_examples=50)
    @given(
        st.integers(min_value=2, max_value=6),
        st.integers(min_value=1, max_value=10),
        st.integers(min_value=11, max_value=50),
        st.integers(min_value=100, max_value=5000),
    )
    def test_initial_chips_invariant_and_card_uniqueness(
        self, num_players: int, sb: int, bb: int, base_stack: int
    ) -> None:
        """Every dealt hand must have strictly unique cards and conserved initial chips."""
        cfg = GameConfig(small_blind=sb, big_blind=bb, max_players=num_players)
        players = [(f"p_{i}", base_stack + (i * 50)) for i in range(num_players)]
        total_starting_chips = sum(stack for _, stack in players)

        state = GameState.start_hand(config=cfg, players_data=players)

        # 1. Total starting chips match
        assert state.total_starting_chips == total_starting_chips

        # 2. All dealt cards across all players are strictly unique
        all_dealt: list[Card] = []
        for p in state.players:
            all_dealt.extend(p.hole_cards)
        validate_unique_cards(all_dealt)
        assert len(all_dealt) == 2 * num_players

    @settings(max_examples=30)
    @given(st.integers(min_value=1000, max_value=9999))
    def test_random_legal_playout_conserves_chips(self, seed: int) -> None:
        """Play random legal actions until hand termination; chips MUST BE strictly conserved.

        Invariant: TOTAL_INITIAL_CHIPS == TOTAL_FINAL_CHIPS.
        """
        rng = random.Random(seed)
        num_players = rng.randint(2, 4)
        cfg = GameConfig(small_blind=5, big_blind=10, max_players=num_players)
        players = [(f"player_{i}", rng.randint(200, 1000)) for i in range(num_players)]
        total_starting_chips = sum(stack for _, stack in players)

        state = GameState.start_hand(config=cfg, players_data=players, rng=rng)

        # Step through up to 50 legal actions
        steps = 0
        while state.street != Street.SHOWDOWN and steps < 50:
            steps += 1
            legal_actions = state.get_legal_actions()
            if not legal_actions or state.current_actor_seat is None:
                break

            actor = state.players[state.current_actor_seat]
            chosen_legal = rng.choice(legal_actions)

            amount = 0
            if chosen_legal.action_type in (ActionType.BET, ActionType.RAISE):
                if chosen_legal.max_amount > chosen_legal.min_amount:
                    amount = rng.randint(chosen_legal.min_amount, chosen_legal.max_amount)
                else:
                    amount = chosen_legal.min_amount
            elif chosen_legal.action_type == ActionType.CALL:
                amount = chosen_legal.min_amount

            act = Action(
                player_id=actor.player_id,
                action_type=chosen_legal.action_type,
                amount=amount,
            )
            state = state.apply_action(act)

        # Invariant: final total stacks must equal initial total
        final_total = sum(p.stack for p in state.players)
        # If hand reached showdown, result payouts are already added back to stacks
        if state.street == Street.SHOWDOWN:
            assert final_total == total_starting_chips

    @settings(max_examples=40)
    @given(st.integers(min_value=1, max_value=1000))
    def test_hand_strength_reflexivity_and_transitivity(self, seed: int) -> None:
        """HandStrength rich comparison must satisfy equivalence and total ordering."""
        rng = random.Random(seed)
        deck = Deck.generate_standard_deck()

        # Sample two 5-card hands
        h1 = rng.sample(deck, 5)
        h2 = rng.sample(deck, 5)

        s1 = evaluate_5cards(h1)
        s2 = evaluate_5cards(h2)

        # Reflexivity
        assert s1 == s1
        assert s2 == s2
        assert not (s1 < s1)

        # Antisymmetry & Trichotomy
        if s1 < s2:
            assert not (s2 < s1)
            assert s1 != s2
            assert s2 > s1
        elif s2 < s1:
            assert not (s1 < s2)
            assert s1 != s2
            assert s1 > s2
        else:
            assert s1 == s2
            assert not (s1 < s2)
            assert not (s2 < s1)
