"""Decision Lab Sub-Engine.

Integrates poker mathematics into realistic unprompted hand scenarios.
The learner independently diagnoses:
1. What mathematical concept governs the decision.
2. What quantitative values are known vs estimated.
3. The exact or justified numerical threshold.
4. The supported strategic action.
5. Whether the scenario is mathematically indeterminate ("Insufficient Information").

Strictly distinguishes:
- Mathematical Conclusion: Directly provable from stated parameters.
- Strategic Recommendation: Relies on modeled opponent tendencies or range assumptions.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any


@dataclass
class DecisionScenario:
    """An integrated multi-step poker decision scenario."""

    scenario_id: str
    title: str
    hand_narrative: str
    hero_cards: list[str]
    board_cards: list[str]
    pot_size: int
    facing_bet: int
    effective_stack: int
    game_format: str  # Cash 6-Max, MTT, PKO, etc.
    correct_concept: str
    concept_options: list[str]
    required_calculation_label: str
    exact_numerical_target: float
    tolerance: float
    numerical_unit: str
    recommended_action: str
    action_options: list[str]
    is_mathematically_indeterminate: bool
    mathematical_proof_explanation: str
    strategic_model_explanation: str
    seed: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "title": self.title,
            "hand_narrative": self.hand_narrative,
            "hero_cards": self.hero_cards,
            "board_cards": self.board_cards,
            "pot_size": self.pot_size,
            "facing_bet": self.facing_bet,
            "effective_stack": self.effective_stack,
            "game_format": self.game_format,
            "correct_concept": self.correct_concept,
            "concept_options": self.concept_options,
            "required_calculation_label": self.required_calculation_label,
            "exact_numerical_target": self.exact_numerical_target,
            "tolerance": self.tolerance,
            "numerical_unit": self.numerical_unit,
            "recommended_action": self.recommended_action,
            "action_options": self.action_options,
            "is_mathematically_indeterminate": self.is_mathematically_indeterminate,
            "mathematical_proof_explanation": self.mathematical_proof_explanation,
            "strategic_model_explanation": self.strategic_model_explanation,
            "seed": self.seed,
        }


class DecisionLabEngine:
    """Generates and evaluates integrated decision scenarios."""

    SCENARIO_TEMPLATES = [
        {
            "id": "river_bluff_catch",
            "title": "River Bluff Catcher Facing Polarized Overbet",
            "narrative": "6-Max Cash $2/$5. Hero holds As Jd on a board of Kd Ts 4h 2c 7s. Pot is $240. Villain fires an overbet shove of $360 on the river.",
            "hero": ["As", "Jd"],
            "board": ["Kd", "Ts", "4h", "2c", "7s"],
            "pot": 240,
            "bet": 360,
            "stack": 360,
            "format": "CASH_6MAX",
            "concept": "Pot Odds / Required Equity",
            "concepts": [
                "Pot Odds / Required Equity",
                "Bluff Alpha",
                "Implied Odds",
                "ICM Risk Premium",
            ],
            "calc_label": "Minimum required equity to call",
            "target": 37.5,  # 360 / (240 + 360 + 360) = 360 / 960 = 37.5%
            "tolerance": 0.5,
            "unit": "%",
            "action": "Fold (unless Villain bluffs > 37.5% of range)",
            "actions": [
                "Fold (unless Villain bluffs > 37.5% of range)",
                "Call immediately regardless of Villain bluffs",
                "Raise all-in as a bluff",
            ],
            "indeterminate": False,
            "proof": "Final pot = $240 + $360 + $360 = $960. Required Equity = $360 / $960 = 37.5%. This is mathematically indisputable.",
            "strategy": "With Ace-Jack high on Kd Ts 4h 2c 7s, Hero beats zero value bets. Villain's range must contain at least 37.5% bluffs for Hero to profitably call.",
        },
        {
            "id": "flop_combo_draw_checkraise",
            "title": "Monster Flop Combo Draw Facing C-Bet",
            "narrative": "MTT Early Stage. Hero in Big Blind defends Js Ts on board 9s 8s 2d. Pot is 4,500 chips. Cutoff c-bets 2,200 into 4,500 with 30,000 effective behind.",
            "hero": ["Js", "Ts"],
            "board": ["9s", "8s", "2d"],
            "pot": 4500,
            "bet": 2200,
            "stack": 30000,
            "format": "TOURNAMENT_MTT",
            "concept": "Outs Counting & Combo Draw Equity",
            "concepts": [
                "Outs Counting & Combo Draw Equity",
                "Cash Rake Deduction",
                "MDF Benchmark",
                "Bubble Factor",
            ],
            "calc_label": "Draw completion probability by river",
            "target": 54.1,  # 15 outs on flop -> ~54.1%
            "tolerance": 2.0,
            "unit": "%",
            "action": "Check-Raise (High semi-bluff equity + fold equity)",
            "actions": [
                "Check-Raise (High semi-bluff equity + fold equity)",
                "Fold immediately",
                "Call and always fold turn if missing",
            ],
            "indeterminate": False,
            "proof": "Hero has 9 flush outs + 6 straight outs = 15 clean outs. On flop, 15 outs gives 54.1% exact probability of improving by river.",
            "strategy": "Because Hero is a slight mathematical favorite (>54%) against a single made pair, check-raising applies maximum fold pressure while retaining enormous equity when called.",
        },
        {
            "id": "bubble_unsolvable_icm",
            "title": "Tournament Bubble Confrontation (Missing Data)",
            "narrative": "MTT 1 player from the money. Hero holds Ah Kd with 25 BB. The table chip leader shoves all-in into Hero. The prize payout ladder and other tables' stack distribution are NOT visible.",
            "hero": ["Ah", "Kd"],
            "board": [],
            "pot": 35,
            "bet": 25,
            "stack": 25,
            "format": "TOURNAMENT_MTT",
            "concept": "Insufficient Information to Determine",
            "concepts": [
                "Insufficient Information to Determine",
                "Pot Odds Alone",
                "Rule of 2 and 4",
                "Cash Rake Deduction",
            ],
            "calc_label": "Exact ICM Bubble Factor",
            "target": 0.0,
            "tolerance": 0.0,
            "unit": "none",
            "action": "Cannot Determine (Requires Complete Payout Ladder & Stack Counts)",
            "actions": [
                "Cannot Determine (Requires Complete Payout Ladder & Stack Counts)",
                "Call because AK is top 3% of hands",
                "Fold because tournament chips are always negative EV",
            ],
            "indeterminate": True,
            "proof": "ICM mathematically requires evaluating the full combinatorial distribution of all active players and the full payout ladder. Incomplete inputs make the exact EV indeterminate.",
            "strategy": "Never force an arithmetic calculation when key structural parameters are unknown. In high-stakes bubble spots, guessing ICM factors can cost huge real-dollar expectation.",
        },
    ]

    @classmethod
    def generate_scenario(cls, seed: int | None = None) -> DecisionScenario:
        """Pick or generate a realistic decision scenario."""
        rng = random.Random(seed if seed is not None else random.randint(1, 999_999_999))
        tmpl = rng.choice(cls.SCENARIO_TEMPLATES)
        effective_seed = rng.randint(1, 999_999_999)

        return DecisionScenario(
            scenario_id=f"dec_{tmpl['id']}_{effective_seed}",
            title=tmpl["title"],
            hand_narrative=tmpl["narrative"],
            hero_cards=tmpl["hero"],
            board_cards=tmpl["board"],
            pot_size=tmpl["pot"],
            facing_bet=tmpl["bet"],
            effective_stack=tmpl["stack"],
            game_format=tmpl["format"],
            correct_concept=tmpl["concept"],
            concept_options=tmpl["concepts"],
            required_calculation_label=tmpl["calc_label"],
            exact_numerical_target=tmpl["target"],
            tolerance=tmpl["tolerance"],
            numerical_unit=tmpl["unit"],
            recommended_action=tmpl["action"],
            action_options=tmpl["actions"],
            is_mathematically_indeterminate=tmpl["indeterminate"],
            mathematical_proof_explanation=tmpl["proof"],
            strategic_model_explanation=tmpl["strategy"],
            seed=effective_seed,
        )

    @classmethod
    def evaluate_decision(
        cls,
        scenario: DecisionScenario,
        chosen_concept: str,
        submitted_calculation: float,
        chosen_action: str,
        reasoning_text: str = "",
    ) -> dict[str, Any]:
        """Grade all stages of the decision scenario independently."""
        is_concept_correct = chosen_concept == scenario.correct_concept

        is_calc_correct = False
        if scenario.is_mathematically_indeterminate:
            is_calc_correct = True  # Calculation skipped or marked indeterminate
        else:
            abs_err = abs(submitted_calculation - scenario.exact_numerical_target)
            is_calc_correct = abs_err <= scenario.tolerance

        is_action_correct = chosen_action == scenario.recommended_action
        all_passed = is_concept_correct and is_calc_correct and is_action_correct

        return {
            "all_passed": all_passed,
            "is_concept_correct": is_concept_correct,
            "is_calc_correct": is_calc_correct,
            "is_action_correct": is_action_correct,
            "correct_concept": scenario.correct_concept,
            "exact_numerical_target": scenario.exact_numerical_target,
            "recommended_action": scenario.recommended_action,
            "mathematical_proof": scenario.mathematical_proof_explanation,
            "strategic_model": scenario.strategic_model_explanation,
        }
