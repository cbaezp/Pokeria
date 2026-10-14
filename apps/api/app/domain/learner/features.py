"""Point-in-time causal feature extraction for personalized poker training models.

Guarantees:
1. Strict Temporal Causality: At decision timestamp T, all historical performance
   aggregates are computed ONLY from observations occurring strictly prior to T.
2. Leakage Prevention: Never incorporates chosen_action, chosen_ev, best_ev,
   ev_loss, or grade of the target decision into its input feature vector.
3. Provenance Integrity: Only solver-backed, non-test observations enter training sets.
"""

from __future__ import annotations

from typing import Any

from app.domain.learner.models import (
    PointInTimeFeatures,
    check_decision_eligibility,
    is_material_mistake,
)
from app.domain.training.models import DecisionEvent


def classify_board_texture(board: str) -> str:
    """Classifies card board texture without external dependencies."""
    if not board or not board.strip():
        return "NONE"

    cards = [c.strip() for c in board.strip().split() if len(c.strip()) >= 2]
    if not cards:
        return "NONE"

    ranks = [c[0] for c in cards]
    suits = [c[1] for c in cards]

    # Paired board
    if len(ranks) != len(set(ranks)):
        return "PAIR"

    suit_counts = {s: suits.count(s) for s in set(suits)}
    max_suit = max(suit_counts.values()) if suit_counts else 0

    if max_suit >= 3:
        return "MONOTONE"
    if max_suit == 2:
        return "TWO_TONE"
    return "RAINBOW"


class PointInTimeFeatureExtractor:
    """Extracts causal, point-in-time features from chronologically ordered decision events."""

    def __init__(self, family_vocab: list[str] | None = None) -> None:
        self.family_vocab = sorted(
            family_vocab
            or [
                "RIVER_BLUFF_CATCH",
                "FLOP_CBET",
                "TURN_BARREL",
                "RIVER_POLARIZED_BET",
                "PREFLOP_RFI",
                "SINGLE_RAISED_POT_IP",
                "3BET_POT_OOP",
                "MULTIWAY_POT",
            ]
        )

    def extract_causal_dataset(
        self,
        events: list[DecisionEvent],
        profile_is_test: bool = False,
    ) -> list[dict[str, Any]]:
        """Transforms raw decision events into causal (features, target) samples.

        Events MUST be sorted chronologically by created_at.
        """
        # Strict fail-safe: Test profiles NEVER emit training or calibration samples
        if profile_is_test:
            return []

        # Strict deterministic ordering by (created_at, id)
        sorted_events = sorted(events, key=lambda e: (e.created_at, e.id))
        samples: list[dict[str, Any]] = []

        # Running historical state strictly prior to current index
        prior_solver_events: list[DecisionEvent] = []

        for current in sorted_events:
            # Check eligibility of current decision for target evaluation
            current_origin = getattr(current, "observation_origin", "UNKNOWN")
            eligibility = check_decision_eligibility(
                profile_is_test=profile_is_test,
                grading_status=current.grading_status,
                grading_provenance=current.grading_provenance,
                ev_loss=current.ev_loss,
                pot=current.pot,
                observation_origin=current_origin,
            )

            # Build historical features using ONLY decisions strictly prior to current (created_at, id)
            history = [
                e
                for e in prior_solver_events
                if (e.created_at, e.id) < (current.created_at, current.id)
            ]

            prior_count = len(history)
            if prior_count > 0:
                prior_ev_pcts = [
                    (e.ev_loss / e.pot * 100.0)
                    for e in history
                    if e.ev_loss is not None and e.pot > 0
                ]
                prior_mean_pct = sum(prior_ev_pcts) / len(prior_ev_pcts) if prior_ev_pcts else 0.0

                prior_mistakes = sum(
                    1
                    for e in history
                    if e.ev_loss is not None
                    and is_material_mistake(
                        e.ev_loss,
                        e.pot,
                        e.grade,
                        grading_status=e.grading_status,
                        grading_provenance=e.grading_provenance,
                    )
                )
                prior_mistake_rate = prior_mistakes / prior_count

                # Prior family rate
                fam_history = [e for e in history if e.scenario_family == current.scenario_family]
                if fam_history:
                    fam_mistakes = sum(
                        1
                        for e in fam_history
                        if e.ev_loss is not None
                        and is_material_mistake(
                            e.ev_loss,
                            e.pot,
                            e.grade,
                            grading_status=e.grading_status,
                            grading_provenance=e.grading_provenance,
                        )
                    )
                    prior_fam_rate = fam_mistakes / len(fam_history)
                else:
                    prior_fam_rate = prior_mistake_rate  # fallback to user overall

                # Prior street rate
                current_street = self._infer_street(current.board)
                street_history = [
                    e for e in history if self._infer_street(e.board) == current_street
                ]
                if street_history:
                    street_mistakes = sum(
                        1
                        for e in street_history
                        if e.ev_loss is not None
                        and is_material_mistake(
                            e.ev_loss,
                            e.pot,
                            e.grade,
                            grading_status=e.grading_status,
                            grading_provenance=e.grading_provenance,
                        )
                    )
                    prior_street_rate = street_mistakes / len(street_history)
                else:
                    prior_street_rate = prior_mistake_rate

                prior_board_count = sum(
                    1 for e in history if e.board == current.board and current.board != ""
                )
                prior_scen_count = sum(1 for e in history if e.scenario_id == current.scenario_id)
                prior_node_count = sum(
                    1
                    for e in history
                    if e.solver_node_id is not None and e.solver_node_id == current.solver_node_id
                )

                latencies = [e.latency_ms for e in history if e.latency_ms > 0]
                mean_latency = sum(latencies) / len(latencies) if latencies else 1500.0

                confidences = [
                    e.confidence_score for e in history if e.confidence_score is not None
                ]
                mean_conf = sum(confidences) / len(confidences) if confidences else 3.0
            else:
                prior_mean_pct = 0.0
                prior_mistake_rate = 0.0
                prior_fam_rate = 0.0
                prior_street_rate = 0.0
                prior_board_count = 0
                prior_scen_count = 0
                prior_node_count = 0
                mean_latency = 1500.0
                mean_conf = 3.0

            # First exposure and feedback viewing
            first_exposure = 1 if prior_scen_count == 0 else 0
            feedback_received = 1 if prior_scen_count > 0 else 0

            # Pot and SPR calculations
            spr = round(current.effective_stack / current.pot, 2) if current.pot > 0 else 10.0
            is_ip = 1 if current.hero_position in ("BTN", "CO", "HJ", "MP") else 0
            street_str = self._infer_street(current.board)
            texture_str = classify_board_texture(current.board)

            pit_features = PointInTimeFeatures(
                street=street_str,
                hero_position=current.hero_position,
                is_in_position=is_ip,
                pot_size=float(current.pot),
                effective_stack=float(current.effective_stack),
                spr=float(spr),
                num_actions_in_history=len(current.action_history or []),
                num_legal_actions=len(current.legal_actions or []),
                scenario_family=current.scenario_family,
                board_texture=texture_str,
                prior_graded_attempts=prior_count,
                prior_mean_pot_norm_ev_loss=round(prior_mean_pct, 4),
                prior_mistake_rate=round(prior_mistake_rate, 4),
                prior_family_mistake_rate=round(prior_fam_rate, 4),
                prior_street_mistake_rate=round(prior_street_rate, 4),
                prior_board_exposures=prior_board_count,
                prior_scenario_exposures=prior_scen_count,
                prior_node_exposures=prior_node_count,
                prior_mean_latency_ms=round(mean_latency, 1),
                prior_mean_confidence=round(mean_conf, 2),
                first_exposure_flag=first_exposure,
                prior_feedback_received=feedback_received,
                missing_confidence_indicator=1 if current.confidence_score is None else 0,
                feature_timestamp=current.created_at,
            )

            # If eligible, compute targets
            if eligibility.is_eligible and current.ev_loss is not None:
                target_mistake = (
                    1
                    if is_material_mistake(
                        current.ev_loss,
                        current.pot,
                        current.grade,
                        grading_status=current.grading_status,
                        grading_provenance=current.grading_provenance,
                    )
                    else 0
                )
                target_norm_ev = (
                    min(100.0, (current.ev_loss / current.pot * 100.0)) if current.pot > 0 else 0.0
                )

                samples.append(
                    {
                        "decision_id": current.id,
                        "created_at": current.created_at,
                        "scenario_id": current.scenario_id,
                        "scenario_family": current.scenario_family,
                        "strategy_pack_id": current.strategy_pack_id or "unknown_pack",
                        "board": current.board,
                        "features": pit_features,
                        "feature_vector": pit_features.to_vector(self.family_vocab),
                        "target_mistake": target_mistake,
                        "target_norm_ev": target_norm_ev,
                        "raw_ev_loss": current.ev_loss,
                        "pot": current.pot,
                        "observation_origin": current_origin,
                        "grading_provenance": current.grading_provenance,
                        "grading_status": current.grading_status,
                        "algorithm_version": getattr(current, "algorithm_version", "v1.0.0"),
                    }
                )

            # Add to running prior history IF it was a valid graded solver event from an eligible observation
            if (
                eligibility.is_eligible
                and current.grading_status == "GRADED"
                and current.ev_loss is not None
                and current.pot > 0
            ):
                prior_solver_events.append(current)

        return samples

    def _infer_street(self, board: str) -> str:
        """Determines poker street from board representation."""
        if not board or not board.strip():
            return "PREFLOP"
        cards = [c for c in board.strip().split() if len(c) >= 2]
        if len(cards) <= 3:
            return "FLOP"
        if len(cards) == 4:
            return "TURN"
        return "RIVER"
