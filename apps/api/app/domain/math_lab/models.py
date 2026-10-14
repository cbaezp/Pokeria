"""Poker Math Lab Domain Models.

Defines core data structures, enums, question schemas, attempt tracking,
and mistake diagnostics for the Poker Math Lab.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class MathDifficulty(StrEnum):
    """Exercise difficulty tier."""

    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"


class MathGameFormat(StrEnum):
    """Poker game format context."""

    CASH_6MAX = "CASH_6MAX"
    CASH_9MAX = "CASH_9MAX"
    CASH_HEADS_UP = "CASH_HEADS_UP"
    TOURNAMENT_MTT = "TOURNAMENT_MTT"
    TOURNAMENT_SNG = "TOURNAMENT_SNG"
    TOURNAMENT_PKO = "TOURNAMENT_PKO"


class MathQuestionType(StrEnum):
    """Format of the interactive question."""

    NUMERIC = "NUMERIC"
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    OUTS_COUNT = "OUTS_COUNT"
    EQUITY_ESTIMATE = "EQUITY_ESTIMATE"
    CONCEPT_IDENTIFY = "CONCEPT_IDENTIFY"
    INSUFFICIENT_INFO = "INSUFFICIENT_INFO"
    ACTION_RANK = "ACTION_RANK"


class MistakeClassification(StrEnum):
    """The 15 canonical mistake diagnostic classifications."""

    FORMULA_SELECTION_ERROR = "FORMULA_SELECTION_ERROR"
    INCORRECT_POT_CONSTRUCTION = "INCORRECT_POT_CONSTRUCTION"
    POT_ODDS_VS_ODDS_AGAINST = "POT_ODDS_VS_ODDS_AGAINST"
    INCORRECT_OUTS = "INCORRECT_OUTS"
    DOUBLE_COUNTING_OUTS = "DOUBLE_COUNTING_OUTS"
    IGNORING_DIRTY_OUTS = "IGNORING_DIRTY_OUTS"
    EQUITY_VS_IMPROVEMENT = "EQUITY_VS_IMPROVEMENT"
    EQUITY_VS_REALIZATION = "EQUITY_VS_REALIZATION"
    INCORRECT_RANGE_ASSUMPTION = "INCORRECT_RANGE_ASSUMPTION"
    ARITHMETIC_ERROR = "ARITHMETIC_ERROR"
    APPROXIMATION_ERROR = "APPROXIMATION_ERROR"
    INCORRECT_EV_INTERPRETATION = "INCORRECT_EV_INTERPRETATION"
    RAKE_OMISSION = "RAKE_OMISSION"
    ICM_CHIP_EV_CONFUSION = "ICM_CHIP_EV_CONFUSION"
    TIME_PRESSURE_FAILURE = "TIME_PRESSURE_FAILURE"
    CONFIDENCE_CALIBRATION_ERROR = "CONFIDENCE_CALIBRATION_ERROR"


class PedagogicalStage(StrEnum):
    """The 5 instructional stages."""

    STAGE_1_UNDERSTAND = "UNDERSTAND"
    STAGE_2_CALCULATE = "CALCULATE"
    STAGE_3_ESTIMATE = "ESTIMATE"
    STAGE_4_APPLY = "APPLY"
    STAGE_5_EXECUTE_QUICKLY = "EXECUTE_QUICKLY"


@dataclass(frozen=True)
class MathLabModule:
    """Metadata for one of the 16 core mathematical curriculum modules."""

    id: str  # e.g. "mod_01_arithmetic"
    number: int
    title: str
    short_title: str
    description: str
    core_formula: str
    units: str
    prerequisites: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "number": self.number,
            "title": self.title,
            "short_title": self.short_title,
            "description": self.description,
            "core_formula": self.core_formula,
            "units": self.units,
            "prerequisites": self.prerequisites,
            "tags": self.tags,
        }


@dataclass(frozen=True)
class MathLabLessonStep:
    """A single instructional step within a module lesson."""

    step_number: int
    stage: PedagogicalStage
    title: str
    content_markdown: str
    formula_box: str | None = None
    worked_example: dict[str, Any] | None = None
    mental_shortcut: str | None = None
    common_misconception: str | None = None
    check_question: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_number": self.step_number,
            "stage": self.stage.value,
            "title": self.title,
            "content_markdown": self.content_markdown,
            "formula_box": self.formula_box,
            "worked_example": self.worked_example,
            "mental_shortcut": self.mental_shortcut,
            "common_misconception": self.common_misconception,
            "check_question": self.check_question,
        }


@dataclass(frozen=True)
class MathLabLesson:
    """Full pedagogical lesson for a module."""

    module_id: str
    title: str
    summary: str
    steps: list[MathLabLessonStep] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "module_id": self.module_id,
            "title": self.title,
            "summary": self.summary,
            "steps": [s.to_dict() for s in self.steps],
        }


@dataclass(frozen=True)
class ReferenceArticle:
    """Comprehensive mathematical reference entry."""

    module_id: str
    title: str
    definition: str
    mathematical_derivation: str
    formula: str
    variables: list[dict[str, str]]
    units: str
    boundary_conditions: list[str]
    mental_shortcut: str
    worked_example: dict[str, Any]
    counterexample_or_misconception: str
    cash_vs_tournament_differences: str
    academic_citations: list[dict[str, str]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "module_id": self.module_id,
            "title": self.title,
            "definition": self.definition,
            "mathematical_derivation": self.mathematical_derivation,
            "formula": self.formula,
            "variables": self.variables,
            "units": self.units,
            "boundary_conditions": self.boundary_conditions,
            "mental_shortcut": self.mental_shortcut,
            "worked_example": self.worked_example,
            "counterexample_or_misconception": self.counterexample_or_misconception,
            "cash_vs_tournament_differences": self.cash_vs_tournament_differences,
            "academic_citations": self.academic_citations,
        }


@dataclass(frozen=True)
class MathExercise:
    """An interactive mathematical exercise."""

    id: str
    module_id: str
    category: str
    difficulty: MathDifficulty
    game_format: MathGameFormat
    question_type: MathQuestionType
    prompt: str
    context_data: dict[str, Any]  # Stacks, pot, cards, board, bets
    exact_answer: float | int | str | bool
    approximate_answer: float | None = None
    acceptable_tolerance: float = 0.0  # e.g. 0.5 for +/- 0.5%
    unit: str = "%"  # e.g. "%", "chips", "BB", "ratio"
    options: list[str] | None = None  # For multiple choice
    step_by_step_solution: list[str] = field(default_factory=list)
    common_errors: dict[str, MistakeClassification] = field(default_factory=dict)
    reference_formula: str = ""
    seed: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "module_id": self.module_id,
            "category": self.category,
            "difficulty": self.difficulty.value,
            "game_format": self.game_format.value,
            "question_type": self.question_type.value,
            "prompt": self.prompt,
            "context_data": self.context_data,
            "exact_answer": self.exact_answer,
            "approximate_answer": self.approximate_answer,
            "acceptable_tolerance": self.acceptable_tolerance,
            "unit": self.unit,
            "options": self.options,
            "step_by_step_solution": self.step_by_step_solution,
            "reference_formula": self.reference_formula,
            "seed": self.seed,
        }


@dataclass
class ExerciseSubmissionResult:
    """Evaluation result for an exercise attempt."""

    is_correct: bool
    student_answer: Any
    exact_answer: Any
    approximate_answer: Any | None
    absolute_error: float
    signed_bias: float
    mistake_category: MistakeClassification | None
    explanation: str
    step_by_step: list[str]
    time_taken_ms: int
    is_speed_target_met: bool
    recommended_module: str | None = None
    retention_scheduled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_correct": self.is_correct,
            "student_answer": self.student_answer,
            "exact_answer": self.exact_answer,
            "approximate_answer": self.approximate_answer,
            "absolute_error": round(self.absolute_error, 4),
            "signed_bias": round(self.signed_bias, 4),
            "mistake_category": self.mistake_category.value if self.mistake_category else None,
            "explanation": self.explanation,
            "step_by_step": self.step_by_step,
            "time_taken_ms": self.time_taken_ms,
            "is_speed_target_met": self.is_speed_target_met,
            "recommended_module": self.recommended_module,
            "retention_scheduled": self.retention_scheduled,
        }
