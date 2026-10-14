"""Adaptive Preflop Scenario Sampling and Practice Orchestration Service.

Generates targeted exercise sequences based on learner weakness patterns:
1. RANDOM: Uniform representative coverage across all 169 hands and 5 positions.
2. BOUNDARY: Threshold boundary hands (0.10 <= raise_freq <= 0.90) to hone edge discrimination.
3. WEAKNESS_FOCUSED: 60% targeted on empirical weakness buckets + 40% interleaved representative hands.
4. MIXED: Balanced positional rotation across UTG, HJ, CO, BTN, SB.
5. ASSESSMENT: Fresh, unpracticed hands evaluated under assessment conditions.
"""

from __future__ import annotations

import random
from typing import Any

from app.domain.learner.range_learner import (
    RangeObservation,
    RangeRecallLearnerModel,
)
from app.domain.training.models import TrainingScenario


class RangeAdaptiveSamplingService:
    """Orchestrates adaptive drill scenario generation tailored to individual learner evidence."""

    @classmethod
    def select_adaptive_scenarios(
        cls,
        candidate_scenarios: list[TrainingScenario],
        observations: list[RangeObservation],
        sampling_policy: str = "RANDOM",
        target_count: int = 50,
        target_positions: list[str] | None = None,
        seed: int | None = None,
    ) -> tuple[list[str], dict[str, Any]]:
        """Select a sequence of scenario IDs meeting the target sampling policy.

        Returns:
            (selected_scenario_ids, selection_metadata)
        """
        rng = random.Random(seed) if seed is not None else random.Random()
        preflop_candidates = [
            s for s in candidate_scenarios if getattr(s, "street", "preflop") == "preflop"
        ]

        if not preflop_candidates:
            return [], {"policy": sampling_policy, "reason": "No preflop scenarios available"}

        # Filter by positions if specified
        if target_positions:
            pos_set = {p.upper() for p in target_positions}
            preflop_candidates = [
                s for s in preflop_candidates if s.hero_position.upper() in pos_set
            ]

        # Analyze current weakness patterns
        weaknesses = RangeRecallLearnerModel.detect_weaknesses(observations)

        policy = sampling_policy.upper().strip()
        selected: list[TrainingScenario] = []
        metadata: dict[str, Any] = {
            "requested_policy": policy,
            "target_count": target_count,
            "available_candidates": len(preflop_candidates),
            "weaknesses_detected_count": len(weaknesses),
        }

        if policy == "BOUNDARY":
            # Filter candidate scenarios tagged as boundary or with 0.10 <= raise_freq <= 0.90
            boundary_pool = [
                s
                for s in preflop_candidates
                if "boundary" in [t.lower() for t in s.tags]
                or (0.05 < s.solver_metadata.get("raise_frequency", 0.0) < 0.95)
            ]
            pool = boundary_pool if boundary_pool else preflop_candidates
            metadata["boundary_candidates_count"] = len(boundary_pool)
            metadata["rationale"] = (
                "Targeting strategic edge-of-range hands with mixed frequency profiles."
            )

            selected = cls._sample_with_variety(pool, target_count, rng)

        elif policy == "WEAKNESS_FOCUSED":
            if weaknesses:
                top_weakness = weaknesses[0]
                weak_pos = top_weakness.position
                weak_fam = top_weakness.hand_family

                # Target pool: scenarios matching the top weak position and family
                focused_pool = [
                    s
                    for s in preflop_candidates
                    if s.hero_position.upper() == weak_pos.upper()
                    and (
                        weak_fam.lower() in [t.lower() for t in s.tags]
                        or s.solver_metadata.get("hand_family", "").lower() == weak_fam.lower()
                    )
                ]

                # If specific problem hands exist, prioritize them
                if top_weakness.problematic_hands:
                    problem_hands_set = set(top_weakness.problematic_hands)
                    p_pool = [
                        s
                        for s in focused_pool
                        if s.solver_metadata.get("hand_class") in problem_hands_set
                    ]
                    if p_pool:
                        focused_pool = p_pool + [s for s in focused_pool if s not in p_pool]

                # Scale targeted allocation by weakness tier to prevent over-concentration on tiny samples
                tier = getattr(top_weakness, "weakness_tier", "PERSISTENT_WEAKNESS")
                if tier == "POSSIBLE_WEAKNESS":
                    targeted_ratio = 0.25
                elif tier == "EMERGING_WEAKNESS":
                    targeted_ratio = 0.40
                else:
                    targeted_ratio = 0.60

                count_focused = int(round(target_count * targeted_ratio))
                count_interleaved = target_count - count_focused

                focused_samples = cls._sample_with_variety(
                    focused_pool if focused_pool else preflop_candidates, count_focused, rng
                )
                interleaved_pool = [s for s in preflop_candidates if s not in focused_samples]
                interleaved_samples = cls._sample_with_variety(
                    interleaved_pool if interleaved_pool else preflop_candidates,
                    count_interleaved,
                    rng,
                )

                # Interleave the two lists based on targeted_ratio
                combined = []
                idx_f, idx_i = 0, 0
                step_mod = 4 if targeted_ratio == 0.25 else (5 if targeted_ratio == 0.40 else 5)
                f_freq = 1 if targeted_ratio == 0.25 else (2 if targeted_ratio == 0.40 else 3)
                for step in range(target_count):
                    if (step % step_mod < f_freq) and idx_f < len(focused_samples):
                        combined.append(focused_samples[idx_f])
                        idx_f += 1
                    elif idx_i < len(interleaved_samples):
                        combined.append(interleaved_samples[idx_i])
                        idx_i += 1
                    elif idx_f < len(focused_samples):
                        combined.append(focused_samples[idx_f])
                        idx_f += 1
                    else:
                        break

                selected = combined
                metadata["focused_weakness"] = top_weakness.to_dict()
                metadata["focused_count"] = len(focused_samples)
                metadata["interleaved_count"] = len(interleaved_samples)
                metadata["targeted_ratio"] = targeted_ratio
                metadata["weakness_tier"] = tier
                metadata["rationale"] = (
                    f"Targeting {weak_pos} {weak_fam} ({tier}, observed error rate {top_weakness.error_rate * 100:.0f}%) "
                    f"with {int(targeted_ratio * 100)}% targeted focus and {int((1 - targeted_ratio) * 100)}% interleaved representative hands."
                )
            else:
                # No identified weaknesses: fallback to boundary practice
                metadata["rationale"] = (
                    "No critical weakness identified; sampling boundary edge hands."
                )
                selected = cls._sample_with_variety(preflop_candidates, target_count, rng)

        elif policy == "MIXED":
            # Rotate evenly across positions
            positions = sorted({s.hero_position for s in preflop_candidates})
            by_pos = {p: [s for s in preflop_candidates if s.hero_position == p] for p in positions}
            combined = []
            for step in range(target_count):
                cur_pos = positions[step % len(positions)]
                pos_pool = by_pos.get(cur_pos, preflop_candidates)
                pick = rng.choice(pos_pool) if pos_pool else rng.choice(preflop_candidates)
                combined.append(pick)
            selected = combined
            metadata["rationale"] = f"Even positional rotation across {len(positions)} seats."

        elif policy == "ASSESSMENT":
            # Prioritize novel hands: hands that have 0 or lowest repetition counts in learner history
            seen_combos = {o.hand_class: o.repetition_index for o in observations}
            # Sort candidate scenarios by ascending repetition count
            sorted_candidates = sorted(
                preflop_candidates,
                key=lambda s: (
                    seen_combos.get(s.solver_metadata.get("hand_class", ""), 0),
                    rng.random(),
                ),
            )
            selected = sorted_candidates[:target_count]
            metadata["novel_hands_count"] = sum(
                1
                for s in selected
                if seen_combos.get(s.solver_metadata.get("hand_class", ""), 0) == 0
            )
            metadata["rationale"] = (
                "Novel, unseen, and least-repeated hands selected for unassisted blind assessment."
            )

        else:  # RANDOM / Default
            metadata["rationale"] = "Uniform representative sampling across all 169 hand classes."
            selected = cls._sample_with_variety(preflop_candidates, target_count, rng)

        return [s.id for s in selected], metadata

    @classmethod
    def _sample_with_variety(
        cls,
        pool: list[TrainingScenario],
        target_count: int,
        rng: random.Random,
    ) -> list[TrainingScenario]:
        """Sample from pool ensuring adjacent hands do not repeat the exact same position and family."""
        if not pool:
            return []

        remaining = list(pool)
        rng.shuffle(remaining)
        selected: list[TrainingScenario] = []

        last_pos: str | None = None
        last_fam: str | None = None

        while len(selected) < target_count:
            if not remaining:
                remaining = list(pool)
                rng.shuffle(remaining)

            # Try to pick candidate with different position or family
            match = next(
                (
                    s
                    for s in remaining
                    if s.hero_position != last_pos
                    or s.solver_metadata.get("hand_family") != last_fam
                ),
                remaining[0],
            )
            remaining.remove(match)
            selected.append(match)
            last_pos = match.hero_position
            last_fam = match.solver_metadata.get("hand_family")

        return selected
