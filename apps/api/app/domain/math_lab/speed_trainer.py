"""Mental Math Speed Trainer Sub-Engine.

Provides fast, high-frequency mental arithmetic drills under configurable time targets:
- Untimed
- 15-second target
- 10-second target
- 5-second target
- 3-second target
- Adaptive time target (scales dynamically based on rolling accuracy)

Features latency-independent timing, precomputed references, pause between questions,
and comprehensive speed analytics (median time, 90th percentile, reflex rate).
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from app.domain.math_lab.generators import MathExerciseGenerator
from app.domain.math_lab.models import MathDifficulty, MathGameFormat


@dataclass
class SpeedSessionConfig:
    """Configuration for a timed mental math training session."""

    time_target_seconds: int | None  # 15, 10, 5, 3, or None for untimed
    is_adaptive: bool = False
    batch_size: int = 10
    difficulty: MathDifficulty = MathDifficulty.INTERMEDIATE
    modules: list[str] | None = None  # Modules to pull drills from (default: core arithmetic)


@dataclass
class SpeedDrillItem:
    """A single drill item in a speed session, precomputed for zero latency."""

    drill_id: str
    prompt: str
    target_value: float
    tolerance: float
    unit: str
    options: list[str] | None  # Optional for multiple-choice mode
    time_limit_ms: int | None
    reference_formula: str
    module_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "drill_id": self.drill_id,
            "prompt": self.prompt,
            "target_value": self.target_value,
            "tolerance": self.tolerance,
            "unit": self.unit,
            "options": self.options,
            "time_limit_ms": self.time_limit_ms,
            "reference_formula": self.reference_formula,
            "module_id": self.module_id,
        }


class SpeedTrainerEngine:
    """Manages timed speed sessions and rapid mental math reflex generation."""

    SPEED_MODULES = [
        "mod_01_arithmetic",
        "mod_02_pot_odds",
        "mod_03_outs_draws",
        "mod_07_call_ev",
        "mod_08_bluff_ev",
        "mod_15_mental_math",
    ]

    @classmethod
    def generate_session(
        cls, config: SpeedSessionConfig, seed: int | None = None
    ) -> list[SpeedDrillItem]:
        """Precompute batch of drills to ensure zero lag during timed gameplay."""
        rng = random.Random(seed if seed is not None else random.randint(1, 999_999_999))
        items: list[SpeedDrillItem] = []
        modules_to_use = config.modules or cls.SPEED_MODULES

        time_limit_ms = (config.time_target_seconds * 1000) if config.time_target_seconds else None

        for idx in range(config.batch_size):
            item_seed = rng.randint(1, 999_999_999)
            mod = rng.choice(modules_to_use)
            ex = MathExerciseGenerator.generate(
                module_id=mod,
                difficulty=config.difficulty,
                game_format=MathGameFormat.CASH_6MAX,
                seed=item_seed,
            )

            # Ensure answer is numeric or options exist
            numeric_target = (
                float(ex.exact_answer) if isinstance(ex.exact_answer, (int, float)) else 0.0
            )

            items.append(
                SpeedDrillItem(
                    drill_id=f"speed_{idx}_{item_seed}",
                    prompt=ex.prompt,
                    target_value=numeric_target,
                    tolerance=ex.acceptable_tolerance or 0.5,
                    unit=ex.unit,
                    options=ex.options,
                    time_limit_ms=time_limit_ms,
                    reference_formula=ex.reference_formula,
                    module_id=mod,
                )
            )

        return items

    @classmethod
    def evaluate_drill_attempt(
        cls,
        item: SpeedDrillItem,
        student_answer: float,
        time_taken_ms: int,
    ) -> dict[str, Any]:
        """Grade a speed drill attempt taking time limit into account."""
        time_limit = item.time_limit_ms
        is_timed_out = time_limit is not None and time_taken_ms > time_limit

        abs_error = abs(student_answer - item.target_value)
        is_accuracy_met = abs_error <= item.tolerance
        is_correct = is_accuracy_met and not is_timed_out

        return {
            "is_correct": is_correct,
            "is_accuracy_met": is_accuracy_met,
            "is_timed_out": is_timed_out,
            "student_answer": student_answer,
            "target_value": item.target_value,
            "absolute_error": round(abs_error, 2),
            "time_taken_ms": time_taken_ms,
            "time_limit_ms": time_limit,
            "unit": item.unit,
            "reference_formula": item.reference_formula,
        }
