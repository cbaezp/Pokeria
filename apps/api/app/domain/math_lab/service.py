"""Poker Math Lab Service.

Coordinates curriculum progression, exercise generation, grading, diagnostic mistake
analysis, spaced repetition scheduling, and mastery statistics across all 16 modules.
Backed by PostgreSQL persistence for user-isolated, durable progress tracking.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import hashlib
import hmac
import random
import statistics
import uuid
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select

from app.domain.math_lab.curriculum_content import LESSONS
from app.domain.math_lab.decision_lab import DecisionLabEngine, DecisionScenario
from app.domain.math_lab.equity_trainer import EquityChallenge, EquityTrainerEngine
from app.domain.math_lab.generators import MathExerciseGenerator
from app.domain.math_lab.models import (
    ExerciseSubmissionResult,
    MathDifficulty,
    MathExercise,
    MathGameFormat,
    MathLabLesson,
    MathLabModule,
    MathQuestionType,
    MistakeClassification,
)
from app.domain.math_lab.reference_data import MODULES, REFERENCE_ARTICLES
from app.domain.math_lab.speed_trainer import SpeedDrillItem, SpeedSessionConfig, SpeedTrainerEngine
from app.infrastructure.database.models.math_lab import (
    MathLabExerciseAttemptModel,
    MathLabRetentionItemModel,
    MathLabUserProgressModel,
)
from app.infrastructure.database.session import get_db_session

DEFAULT_PROFILE_ID = "9221674a-5be7-4ee9-ba02-86ca08b97090"


def _run_async_compat(coro: Any) -> Any:
    """Run an async coroutine from sync context safely."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(lambda: asyncio.run(coro))
        return future.result()


class MathLabService:
    """Core domain service for Poker Math Lab with PostgreSQL persistence."""

    # -------------------------------------------------------------
    # Curriculum & Reference Library (Static Invariants)
    # -------------------------------------------------------------
    @classmethod
    def get_all_modules(cls) -> list[MathLabModule]:
        """Return the 16 core curriculum modules."""
        return MODULES

    @classmethod
    def get_module(cls, module_id: str) -> MathLabModule | None:
        """Find a module by its identifier."""
        # Support alias
        normalized_id = "mod_14_pko" if module_id == "mod_14_pko_bounties" else module_id
        for m in MODULES:
            if m.id == normalized_id:
                return m
        return None

    @classmethod
    def get_lesson(cls, module_id: str) -> MathLabLesson | None:
        """Retrieve the 5-stage pedagogical lesson for a module."""
        normalized_id = "mod_14_pko" if module_id == "mod_14_pko_bounties" else module_id
        return LESSONS.get(normalized_id)

    @classmethod
    def get_reference_articles(cls, query: str | None = None) -> list[dict[str, Any]]:
        """Return authored mathematical reference articles with optional search filtering."""
        articles = [a.to_dict() for a in REFERENCE_ARTICLES.values()]
        if not query:
            return articles
        q = query.lower().strip()
        return [
            a
            for a in articles
            if q in a["title"].lower()
            or q in a["definition"].lower()
            or q in a["formula"].lower()
            or any(q in v["name"].lower() for v in a["variables"])
        ]

    # -------------------------------------------------------------
    # Server-Authoritative State & Signature Infrastructure
    # -------------------------------------------------------------
    _SECRET_KEY: bytes = b"pokeria_server_authoritative_v1_integrity_key"
    _exercise_cache: dict[str, MathExercise] = {}
    _equity_cache: dict[str, EquityChallenge] = {}
    _decision_cache: dict[str, DecisionScenario] = {}
    _speed_cache: dict[str, SpeedDrillItem] = {}

    @classmethod
    def _compute_exercise_sig(
        cls, module_id: str, difficulty: str, game_format: str, seed: int, exact_answer: Any
    ) -> str:
        payload = f"{module_id}:{difficulty}:{game_format}:{seed}:{exact_answer}".encode()
        return hmac.new(cls._SECRET_KEY, payload, hashlib.sha256).hexdigest()[:16]

    @classmethod
    def generate_exercise(
        cls,
        module_id: str,
        difficulty: MathDifficulty = MathDifficulty.BEGINNER,
        game_format: MathGameFormat = MathGameFormat.CASH_6MAX,
        seed: int | None = None,
    ) -> MathExercise:
        """Generate an interactive exercise with a server-authoritative signed ID."""
        normalized_id = "mod_14_pko" if module_id == "mod_14_pko_bounties" else module_id
        effective_seed = seed if seed is not None else random.randint(100000, 99999999)
        exercise = MathExerciseGenerator.generate(
            normalized_id, difficulty, game_format, effective_seed
        )

        sig = cls._compute_exercise_sig(
            normalized_id,
            difficulty.value,
            game_format.value,
            effective_seed,
            exercise.exact_answer,
        )
        stable_id = (
            f"srv_{normalized_id}_{difficulty.value}_{game_format.value}_{effective_seed}_{sig}"
        )
        exercise = replace(exercise, id=stable_id, seed=effective_seed)

        # Store in LRU cache
        cls._exercise_cache[stable_id] = exercise
        if len(cls._exercise_cache) > 10000:
            for k in list(cls._exercise_cache.keys())[:1000]:
                cls._exercise_cache.pop(k, None)

        return exercise

    @classmethod
    def resolve_authoritative_exercise(
        cls,
        exercise_id: str,
        module_id: str | None = None,
        fallback_data: dict[str, Any] | None = None,
    ) -> MathExercise:
        """Resolve the authoritative exercise strictly from server state or deterministic generator.

        Client payloads are NEVER trusted for exact answers, tolerance, or solutions.
        """
        # 1. In-memory server registry check
        if exercise_id in cls._exercise_cache:
            return cls._exercise_cache[exercise_id]

        # 2. Cryptographic signed ID check: srv_{module}_{diff}_{fmt}_{seed}_{sig}
        if exercise_id.startswith("srv_"):
            parts = exercise_id.split("_")
            try:
                sig = parts[-1]
                seed = int(parts[-2])
                fmt_str = parts[-3]
                diff_str = parts[-4]
                mod_str = "_".join(parts[1:-4])

                diff_enum = MathDifficulty(diff_str)
                fmt_enum = MathGameFormat(fmt_str)
                regen = MathExerciseGenerator.generate(mod_str, diff_enum, fmt_enum, seed)
                expected_sig = cls._compute_exercise_sig(
                    mod_str, diff_enum.value, fmt_enum.value, seed, regen.exact_answer
                )
                if hmac.compare_digest(sig, expected_sig):
                    regen = replace(regen, id=exercise_id)
                    cls._exercise_cache[exercise_id] = regen
                    return regen
            except Exception:
                pass

        # 3. Deterministic seed ID check: ex_{mod}_{seed}
        if exercise_id.startswith("ex_"):
            try:
                parts = exercise_id.split("_")
                seed = int(parts[-1])
                target_mod = module_id or f"mod_{parts[1]}"
                regen = MathExerciseGenerator.generate(
                    target_mod, MathDifficulty.BEGINNER, MathGameFormat.CASH_6MAX, seed
                )
                regen = replace(regen, id=exercise_id)
                cls._exercise_cache[exercise_id] = regen
                return regen
            except Exception:
                pass

        # 4. Fallback: regenerate server-authoritative problem using deterministic seed
        target_mod = module_id or "mod_02_pot_odds"
        diff_enum = MathDifficulty.BEGINNER
        fmt_enum = MathGameFormat.CASH_6MAX
        if fallback_data:
            try:
                diff_enum = MathDifficulty(fallback_data.get("difficulty", "BEGINNER"))
                fmt_enum = MathGameFormat(fallback_data.get("game_format", "CASH_6MAX"))
            except ValueError:
                pass

        det_seed = abs(hash(exercise_id)) % 10000000
        authoritative = MathExerciseGenerator.generate(target_mod, diff_enum, fmt_enum, det_seed)
        authoritative = replace(authoritative, id=exercise_id)
        cls._exercise_cache[exercise_id] = authoritative
        return authoritative

    @classmethod
    async def grade_and_record_submission(
        cls,
        exercise: MathExercise,
        student_answer: Any,
        time_taken_ms: int,
        confidence_level: int = 3,
        profile_id: str = DEFAULT_PROFILE_ID,
        submission_id: str | None = None,
    ) -> ExerciseSubmissionResult:
        """Grade exercise attempt, diagnose mistake categories, and persist to PostgreSQL."""
        exact = exercise.exact_answer
        approx = exercise.approximate_answer
        tol = exercise.acceptable_tolerance

        is_correct = False
        abs_err = 0.0
        signed_bias = 0.0
        mistake_cat: MistakeClassification | None = None

        if isinstance(exact, (int, float)):
            try:
                num_student = float(student_answer)
                abs_err = abs(num_student - float(exact))
                signed_bias = num_student - float(exact)
                is_correct = abs_err <= tol

                # Check if matches approximate target
                if not is_correct and approx is not None:
                    if abs(num_student - float(approx)) <= tol:
                        is_correct = True
                        signed_bias = num_student - float(approx)

                # Diagnostic mistake classification
                if not is_correct:
                    ans_str = str(round(num_student, 2))
                    if ans_str in exercise.common_errors:
                        mistake_cat = exercise.common_errors[ans_str]
                    elif time_taken_ms > 15000:
                        mistake_cat = MistakeClassification.TIME_PRESSURE_FAILURE
                    elif abs_err > 20.0:
                        mistake_cat = MistakeClassification.FORMULA_SELECTION_ERROR
                    else:
                        mistake_cat = MistakeClassification.ARITHMETIC_ERROR

            except (ValueError, TypeError):
                is_correct = False
                mistake_cat = MistakeClassification.ARITHMETIC_ERROR

        elif isinstance(exact, str):
            is_correct = str(student_answer).strip().lower() == exact.strip().lower()
            if not is_correct:
                mistake_cat = MistakeClassification.FORMULA_SELECTION_ERROR

        is_speed_met = time_taken_ms <= 10000
        retention_sched = not is_correct

        sub_id = submission_id or f"{exercise.id}_{time_taken_ms}_{uuid.uuid4().hex[:8]}"

        # PostgreSQL Persistence
        await cls._persist_attempt(
            profile_id=profile_id,
            submission_id=sub_id,
            module_id=exercise.module_id,
            category=exercise.category,
            difficulty=exercise.difficulty.value,
            game_format=exercise.game_format.value,
            question_type=exercise.question_type.value,
            prompt=exercise.prompt,
            student_answer=str(student_answer),
            exact_answer=str(exact),
            is_correct=is_correct,
            is_speed_target_met=is_speed_met,
            time_taken_ms=time_taken_ms,
            absolute_error=abs_err,
            signed_bias=signed_bias,
            mistake_category=mistake_cat.value if mistake_cat else None,
            exercise_snapshot=exercise.to_dict(),
        )

        explanation = (
            f"Ground truth exact answer: {exact} {exercise.unit}. "
            f"Your answer: {student_answer} {exercise.unit}. "
            + (
                f"Error: {round(abs_err, 2)} {exercise.unit}. "
                if not is_correct
                else "Correct! Excellent execution."
            )
        )

        return ExerciseSubmissionResult(
            is_correct=is_correct,
            student_answer=student_answer,
            exact_answer=exact,
            approximate_answer=approx,
            absolute_error=abs_err,
            signed_bias=signed_bias,
            mistake_category=mistake_cat,
            explanation=explanation,
            step_by_step=exercise.step_by_step_solution,
            time_taken_ms=time_taken_ms,
            is_speed_target_met=is_speed_met,
            recommended_module=exercise.module_id if not is_correct else None,
            retention_scheduled=retention_sched,
        )

    @classmethod
    def grade_submission(
        cls,
        exercise: MathExercise,
        student_answer: Any,
        time_taken_ms: int,
        confidence_level: int = 3,
        profile_id: str = DEFAULT_PROFILE_ID,
        submission_id: str | None = None,
    ) -> ExerciseSubmissionResult:
        """Synchronous wrapper for grade_and_record_submission."""
        return _run_async_compat(
            cls.grade_and_record_submission(
                exercise=exercise,
                student_answer=student_answer,
                time_taken_ms=time_taken_ms,
                confidence_level=confidence_level,
                profile_id=profile_id,
                submission_id=submission_id,
            )
        )

    # -------------------------------------------------------------
    # Equity Trainer Integration
    # -------------------------------------------------------------
    @classmethod
    def create_equity_challenge(
        cls, challenge_type: str = "HAND_VS_HAND", street: str = "flop", seed: int | None = None
    ) -> EquityChallenge:
        effective_seed = seed if seed is not None else random.randint(100000, 99999999)
        challenge = EquityTrainerEngine.generate_challenge(challenge_type, street, effective_seed)
        sig = hmac.new(
            cls._SECRET_KEY,
            f"eq:{challenge_type}:{street}:{effective_seed}:{challenge.ground_truth_equity}".encode(),
            hashlib.sha256,
        ).hexdigest()[:16]
        challenge.challenge_id = f"srv_eq_{challenge_type}_{street}_{effective_seed}_{sig}"
        challenge.seed = effective_seed
        cls._equity_cache[challenge.challenge_id] = challenge
        return challenge

    @classmethod
    def resolve_authoritative_equity_challenge(
        cls, challenge_id: str, fallback_data: dict[str, Any] | None = None
    ) -> EquityChallenge:
        """Resolve authoritative equity challenge. Never trust client for ground_truth_equity."""
        if challenge_id in cls._equity_cache:
            return cls._equity_cache[challenge_id]

        if challenge_id.startswith("srv_eq_"):
            parts = challenge_id.split("_")
            try:
                sig = parts[-1]
                seed = int(parts[-2])
                street = parts[-3]
                ctype = "_".join(parts[2:-3])
                regen = EquityTrainerEngine.generate_challenge(ctype, street, seed)
                expected_sig = hmac.new(
                    cls._SECRET_KEY,
                    f"eq:{ctype}:{street}:{seed}:{regen.ground_truth_equity}".encode(),
                    hashlib.sha256,
                ).hexdigest()[:16]
                if hmac.compare_digest(sig, expected_sig):
                    regen.challenge_id = challenge_id
                    cls._equity_cache[challenge_id] = regen
                    return regen
            except Exception:
                pass

        ctype = "HAND_VS_HAND"
        street = "flop"
        if fallback_data:
            ctype = fallback_data.get("challenge_type", ctype)
            street = fallback_data.get("street", street)
        det_seed = abs(hash(challenge_id)) % 10000000
        authoritative = EquityTrainerEngine.generate_challenge(ctype, street, det_seed)
        authoritative.challenge_id = challenge_id
        cls._equity_cache[challenge_id] = authoritative
        return authoritative

    @classmethod
    async def evaluate_and_record_equity(
        cls,
        challenge: EquityChallenge,
        student_estimate: float,
        time_ms: int,
        profile_id: str = DEFAULT_PROFILE_ID,
        submission_id: str | None = None,
    ) -> dict[str, Any]:
        res = EquityTrainerEngine.evaluate_estimate(challenge, student_estimate, time_ms)
        sub_id = submission_id or f"eq_{challenge.challenge_id}_{time_ms}_{uuid.uuid4().hex[:8]}"

        await cls._persist_attempt(
            profile_id=profile_id,
            submission_id=sub_id,
            module_id="mod_04_equity_fundamentals",
            category="Equity Trainer",
            difficulty=MathDifficulty.INTERMEDIATE.value,
            game_format=MathGameFormat.CASH_6MAX.value,
            question_type=MathQuestionType.EQUITY_ESTIMATE.value,
            prompt=f"Estimate showdown equity for {challenge.title}",
            student_answer=str(student_estimate),
            exact_answer=str(challenge.ground_truth_equity),
            is_correct=res["is_correct"],
            is_speed_target_met=time_ms <= 10000,
            time_taken_ms=time_ms,
            absolute_error=res["absolute_error"],
            signed_bias=res["signed_bias"],
            mistake_category=MistakeClassification.APPROXIMATION_ERROR.value
            if not res["is_correct"]
            else None,
            exercise_snapshot=challenge.to_dict(),
        )
        return res

    @classmethod
    def evaluate_equity_challenge(
        cls,
        challenge: EquityChallenge,
        student_estimate: float,
        time_ms: int,
        profile_id: str = DEFAULT_PROFILE_ID,
    ) -> dict[str, Any]:
        return _run_async_compat(
            cls.evaluate_and_record_equity(challenge, student_estimate, time_ms, profile_id)
        )

    # -------------------------------------------------------------
    # Speed Trainer Integration
    # -------------------------------------------------------------
    @classmethod
    def start_speed_session(cls, config: SpeedSessionConfig) -> list[SpeedDrillItem]:
        return SpeedTrainerEngine.generate_session(config)

    @classmethod
    async def record_speed_drill_async(
        cls,
        item: SpeedDrillItem,
        student_answer: float,
        time_taken_ms: int,
        profile_id: str = DEFAULT_PROFILE_ID,
        submission_id: str | None = None,
    ) -> dict[str, Any]:
        result = SpeedTrainerEngine.evaluate_drill_attempt(item, student_answer, time_taken_ms)
        sub_id = submission_id or f"speed_{item.id}_{time_taken_ms}_{uuid.uuid4().hex[:8]}"

        abs_err = abs(student_answer - item.exact_answer)
        signed_bias = student_answer - item.exact_answer
        is_speed_met = time_taken_ms <= (item.time_target_seconds * 1000)

        await cls._persist_attempt(
            profile_id=profile_id,
            submission_id=sub_id,
            module_id=item.module_id,
            category="Speed Math",
            difficulty=MathDifficulty.INTERMEDIATE.value,
            game_format=MathGameFormat.CASH_6MAX.value,
            question_type=MathQuestionType.NUMERIC.value,
            prompt=item.prompt,
            student_answer=str(student_answer),
            exact_answer=str(item.exact_answer),
            is_correct=result["is_correct"],
            is_speed_target_met=is_speed_met,
            time_taken_ms=time_taken_ms,
            absolute_error=abs_err,
            signed_bias=signed_bias,
            mistake_category=MistakeClassification.TIME_PRESSURE_FAILURE.value
            if not is_speed_met
            else None,
            exercise_snapshot=item.to_dict(),
        )
        return result

    @classmethod
    def record_speed_drill(
        cls,
        item: SpeedDrillItem,
        student_answer: float,
        time_taken_ms: int,
        profile_id: str = DEFAULT_PROFILE_ID,
    ) -> dict[str, Any]:
        return _run_async_compat(
            cls.record_speed_drill_async(item, student_answer, time_taken_ms, profile_id)
        )

    # -------------------------------------------------------------
    # Decision Lab Integration
    # -------------------------------------------------------------
    @classmethod
    def get_decision_scenario(cls, seed: int | None = None) -> DecisionScenario:
        effective_seed = seed if seed is not None else random.randint(100000, 99999999)
        scenario = DecisionLabEngine.generate_scenario(effective_seed)
        sig = hmac.new(
            cls._SECRET_KEY,
            f"dec:{effective_seed}:{scenario.correct_concept}:{scenario.exact_numerical_target}".encode(),
            hashlib.sha256,
        ).hexdigest()[:16]
        scenario.scenario_id = f"srv_dec_{effective_seed}_{sig}"
        scenario.seed = effective_seed
        cls._decision_cache[scenario.scenario_id] = scenario
        return scenario

    @classmethod
    def resolve_authoritative_decision_scenario(
        cls, scenario_id: str, fallback_data: dict[str, Any] | None = None
    ) -> DecisionScenario:
        """Resolve authoritative decision scenario. Never trust client for correct_concept or numerical target."""
        if scenario_id in cls._decision_cache:
            return cls._decision_cache[scenario_id]

        if scenario_id.startswith("srv_dec_"):
            parts = scenario_id.split("_")
            try:
                sig = parts[-1]
                seed = int(parts[-2])
                regen = DecisionLabEngine.generate_scenario(seed)
                expected_sig = hmac.new(
                    cls._SECRET_KEY,
                    f"dec:{seed}:{regen.correct_concept}:{regen.exact_numerical_target}".encode(),
                    hashlib.sha256,
                ).hexdigest()[:16]
                if hmac.compare_digest(sig, expected_sig):
                    regen.scenario_id = scenario_id
                    cls._decision_cache[scenario_id] = regen
                    return regen
            except Exception:
                pass

        det_seed = abs(hash(scenario_id)) % 10000000
        authoritative = DecisionLabEngine.generate_scenario(det_seed)
        authoritative.scenario_id = scenario_id
        cls._decision_cache[scenario_id] = authoritative
        return authoritative

    @classmethod
    async def evaluate_decision_scenario_async(
        cls,
        scenario: DecisionScenario,
        concept: str,
        calculation: float,
        action: str,
        reasoning: str = "",
        profile_id: str = DEFAULT_PROFILE_ID,
        submission_id: str | None = None,
    ) -> dict[str, Any]:
        result = DecisionLabEngine.evaluate_submission(
            scenario=scenario,
            chosen_concept=concept,
            student_calculation=calculation,
            chosen_action=action,
            reasoning_notes=reasoning,
        )
        sub_id = submission_id or f"dec_{scenario.scenario_id}_{uuid.uuid4().hex[:8]}"

        abs_err = abs(calculation - scenario.exact_numerical_target)
        signed_bias = calculation - scenario.exact_numerical_target
        is_all_correct = (
            result["concept_score"]["is_correct"] and result["action_score"]["is_correct"]
        )

        await cls._persist_attempt(
            profile_id=profile_id,
            submission_id=sub_id,
            module_id="mod_16_integrated_reasoning",
            category="Decision Lab",
            difficulty=MathDifficulty.ADVANCED.value,
            game_format=scenario.game_format.value,
            question_type=MathQuestionType.ACTION_RANK.value,
            prompt=scenario.hand_narrative,
            student_answer=f"Concept:{concept}|Calc:{calculation}|Action:{action}",
            exact_answer=f"Concept:{scenario.correct_concept}|Calc:{scenario.exact_numerical_target}|Action:{scenario.recommended_action}",
            is_correct=is_all_correct,
            is_speed_target_met=True,
            time_taken_ms=10000,
            absolute_error=abs_err,
            signed_bias=signed_bias,
            mistake_category=None
            if is_all_correct
            else MistakeClassification.FORMULA_SELECTION_ERROR.value,
            exercise_snapshot=scenario.to_dict(),
        )
        return result

    @classmethod
    def evaluate_decision_scenario(
        cls,
        scenario: DecisionScenario,
        concept: str,
        calculation: float,
        action: str,
        reasoning: str = "",
        profile_id: str = DEFAULT_PROFILE_ID,
    ) -> dict[str, Any]:
        return _run_async_compat(
            cls.evaluate_decision_scenario_async(
                scenario, concept, calculation, action, reasoning, profile_id
            )
        )

    # -------------------------------------------------------------
    # Persistence Helpers & Idempotency
    # -------------------------------------------------------------
    @classmethod
    async def _persist_attempt(
        cls,
        profile_id: str,
        submission_id: str,
        module_id: str,
        category: str,
        difficulty: str,
        game_format: str,
        question_type: str,
        prompt: str,
        student_answer: str,
        exact_answer: str,
        is_correct: bool,
        is_speed_target_met: bool,
        time_taken_ms: int,
        absolute_error: float,
        signed_bias: float,
        mistake_category: str | None,
        exercise_snapshot: dict[str, Any] | None,
    ) -> None:
        """Persist exercise attempt idempotently and update learner progress."""
        try:
            async with get_db_session() as session:
                # Idempotency check: profile_id + submission_id
                stmt = select(MathLabExerciseAttemptModel).where(
                    MathLabExerciseAttemptModel.profile_id == profile_id,
                    MathLabExerciseAttemptModel.submission_id == submission_id,
                )
                existing = (await session.execute(stmt)).scalar_one_or_none()
                if existing:
                    return

                attempt = MathLabExerciseAttemptModel(
                    id=str(uuid.uuid4()),
                    profile_id=profile_id,
                    submission_id=submission_id,
                    module_id=module_id,
                    category=category,
                    difficulty=difficulty,
                    game_format=game_format,
                    question_type=question_type,
                    prompt=prompt,
                    student_answer=student_answer,
                    exact_answer=exact_answer,
                    is_correct=is_correct,
                    is_speed_target_met=is_speed_target_met,
                    time_taken_ms=time_taken_ms,
                    absolute_error=absolute_error,
                    signed_bias=signed_bias,
                    mistake_category=mistake_category,
                    exercise_snapshot=exercise_snapshot,
                )
                session.add(attempt)

                # Update or initialize learner progress
                today_str = datetime.now(UTC).strftime("%Y-%m-%d")
                prog_stmt = select(MathLabUserProgressModel).where(
                    MathLabUserProgressModel.profile_id == profile_id
                )
                prog = (await session.execute(prog_stmt)).scalar_one_or_none()

                if not prog:
                    prog = MathLabUserProgressModel(
                        id=str(uuid.uuid4()),
                        profile_id=profile_id,
                        completed_modules=[],
                        mastered_topics=[],
                        current_module_id=module_id,
                        streak_days=1,
                        last_activity_date=today_str,
                    )
                    session.add(prog)
                else:
                    if prog.last_activity_date != today_str:
                        yesterday_str = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")
                        if prog.last_activity_date == yesterday_str:
                            prog.streak_days += 1
                        else:
                            prog.streak_days = 1
                        prog.last_activity_date = today_str

                    # Rigorous Module Completion & Mastery Evaluation
                    all_mod_stmt = select(MathLabExerciseAttemptModel).where(
                        MathLabExerciseAttemptModel.profile_id == profile_id,
                        MathLabExerciseAttemptModel.module_id == module_id,
                    )
                    all_mod_attempts = (await session.execute(all_mod_stmt)).scalars().all()
                    all_attempts_list = list(all_mod_attempts)
                    if attempt not in all_attempts_list:
                        all_attempts_list.append(attempt)

                    # Distinct scenarios (by prompt)
                    distinct_prompts = {a.prompt for a in all_attempts_list}
                    distinct_count = len(distinct_prompts)
                    correct_attempts = [a for a in all_attempts_list if a.is_correct]
                    total_count = len(all_attempts_list)
                    accuracy = (
                        (len(correct_attempts) / total_count * 100.0) if total_count > 0 else 0.0
                    )

                    intermediate_plus = sum(
                        1
                        for a in correct_attempts
                        if a.difficulty
                        in (
                            MathDifficulty.INTERMEDIATE.value,
                            MathDifficulty.ADVANCED.value,
                            MathDifficulty.EXPERT.value,
                        )
                    )

                    ret_stmt = select(func.count(MathLabRetentionItemModel.id)).where(
                        MathLabRetentionItemModel.profile_id == profile_id,
                        MathLabRetentionItemModel.module_id == module_id,
                        MathLabRetentionItemModel.status == "PENDING",
                        MathLabRetentionItemModel.scheduled_for <= datetime.now(UTC),
                    )
                    overdue_ret_count = (await session.execute(ret_stmt)).scalar_one() or 0

                    # 1. Completion Requirement: >= 5 distinct scenarios, >= 80% accuracy
                    if distinct_count >= 5 and accuracy >= 80.0:
                        if module_id not in prog.completed_modules:
                            prog.completed_modules = list(set(prog.completed_modules + [module_id]))
                    elif module_id in prog.completed_modules and accuracy < 70.0:
                        prog.completed_modules = [
                            m for m in prog.completed_modules if m != module_id
                        ]

                    # 2. Durable Mastery Requirement: Completed, >= 8 distinct scenarios, >= 85% accuracy, >= 2 intermediate/advanced, 0 overdue retention items
                    if (
                        module_id in prog.completed_modules
                        and distinct_count >= 8
                        and accuracy >= 85.0
                        and intermediate_plus >= 2
                        and overdue_ret_count == 0
                    ):
                        if module_id not in prog.mastered_topics:
                            prog.mastered_topics = list(set(prog.mastered_topics + [module_id]))
                    elif module_id in prog.mastered_topics and (
                        accuracy < 80.0 or overdue_ret_count > 0
                    ):
                        prog.mastered_topics = [m for m in prog.mastered_topics if m != module_id]

                # Retention item scheduling for failed attempts
                if not is_correct:
                    due = datetime.now(UTC) + timedelta(days=1)
                    ret_item = MathLabRetentionItemModel(
                        id=str(uuid.uuid4()),
                        profile_id=profile_id,
                        module_id=module_id,
                        mistake_category=mistake_category,
                        scheduled_for=due,
                        status="PENDING",
                    )
                    session.add(ret_item)

                await session.commit()
        except Exception as exc:
            # Fallback log in case of DB connection issues
            print(f"[MathLabService] Failed to persist attempt to PostgreSQL: {exc}")

    # -------------------------------------------------------------
    # Dashboard & Retention Reporting (Database Backed)
    # -------------------------------------------------------------
    @classmethod
    async def get_dashboard_metrics_async(
        cls, profile_id: str = DEFAULT_PROFILE_ID
    ) -> dict[str, Any]:
        """Calculate genuine mathematical metrics for the user from PostgreSQL."""
        try:
            async with get_db_session() as session:
                # Attempts
                stmt = (
                    select(MathLabExerciseAttemptModel)
                    .where(MathLabExerciseAttemptModel.profile_id == profile_id)
                    .order_by(MathLabExerciseAttemptModel.created_at.desc())
                )
                attempts = (await session.execute(stmt)).scalars().all()

                # Learner progress record
                prog_stmt = select(MathLabUserProgressModel).where(
                    MathLabUserProgressModel.profile_id == profile_id
                )
                prog = (await session.execute(prog_stmt)).scalar_one_or_none()

                # Retention items due
                ret_stmt = select(func.count(MathLabRetentionItemModel.id)).where(
                    MathLabRetentionItemModel.profile_id == profile_id,
                    MathLabRetentionItemModel.status == "PENDING",
                    MathLabRetentionItemModel.scheduled_for <= datetime.now(UTC),
                )
                ret_due_count = (await session.execute(ret_stmt)).scalar_one() or 0

                if not attempts:
                    return {
                        "total_exercises_attempted": 0,
                        "overall_accuracy_pct": 0.0,
                        "median_calculation_time_ms": 0,
                        "p90_calculation_time_ms": 0,
                        "equity_mean_absolute_error": None,  # Insufficient data
                        "equity_estimation_bias": None,  # Insufficient data
                        "completed_modules": prog.completed_modules if prog else [],
                        "mastered_topics_count": len(prog.mastered_topics) if prog else 0,
                        "current_module_id": prog.current_module_id
                        if prog
                        else "mod_01_arithmetic",
                        "streak_days": prog.streak_days if prog else 0,
                        "mistake_breakdown": {},
                        "recommended_next_module": prog.current_module_id
                        if prog
                        else "mod_01_arithmetic",
                        "retention_due_count": ret_due_count,
                    }

                total = len(attempts)
                correct_count = sum(1 for a in attempts if a.is_correct)
                acc_pct = (correct_count / total) * 100.0

                times = sorted([a.time_taken_ms for a in attempts if a.time_taken_ms > 0])
                median_time = times[len(times) // 2] if times else 0
                p90_time = times[int(len(times) * 0.9)] if times else 0

                # Compute MAE only over equity exercises
                equity_attempts = [
                    a
                    for a in attempts
                    if a.question_type == "EQUITY_ESTIMATE"
                    or "equity" in a.category.lower()
                    or a.module_id in ("mod_04_equity_fundamentals", "mod_05_equity_ranges")
                ]
                if equity_attempts:
                    mae = round(statistics.mean([a.absolute_error for a in equity_attempts]), 2)
                    bias = round(statistics.mean([a.signed_bias for a in equity_attempts]), 2)
                else:
                    mae = None
                    bias = None

                mistakes: dict[str, int] = {}
                for a in attempts:
                    if a.mistake_category:
                        mistakes[a.mistake_category] = mistakes.get(a.mistake_category, 0) + 1

                # Calculate mastered topics (modules with >= 3 correct attempts and >= 75% accuracy)
                module_stats: dict[str, list[bool]] = {}
                for a in attempts:
                    module_stats.setdefault(a.module_id, []).append(a.is_correct)
                mastered_count = sum(
                    1
                    for m_id, results in module_stats.items()
                    if len(results) >= 3 and (sum(results) / len(results)) >= 0.75
                )

                completed = prog.completed_modules if prog else []
                current_mod = prog.current_module_id if prog else "mod_02_pot_odds"
                streak = prog.streak_days if prog else 0

                return {
                    "total_exercises_attempted": total,
                    "overall_accuracy_pct": round(acc_pct, 1),
                    "median_calculation_time_ms": median_time,
                    "p90_calculation_time_ms": p90_time,
                    "equity_mean_absolute_error": mae,
                    "equity_estimation_bias": bias,
                    "completed_modules": completed,
                    "mastered_topics_count": mastered_count,
                    "current_module_id": current_mod,
                    "streak_days": streak,
                    "mistake_breakdown": mistakes,
                    "recommended_next_module": current_mod,
                    "retention_due_count": ret_due_count,
                }
        except Exception as exc:
            print(f"[MathLabService] DB error in get_dashboard_metrics_async: {exc}")
            # Empty insufficient data fallback
            return {
                "total_exercises_attempted": 0,
                "overall_accuracy_pct": 0.0,
                "median_calculation_time_ms": 0,
                "p90_calculation_time_ms": 0,
                "equity_mean_absolute_error": None,
                "equity_estimation_bias": None,
                "completed_modules": [],
                "mastered_topics_count": 0,
                "current_module_id": "mod_01_arithmetic",
                "streak_days": 0,
                "mistake_breakdown": {},
                "recommended_next_module": "mod_01_arithmetic",
                "retention_due_count": 0,
            }

    @classmethod
    def get_dashboard_metrics(cls, profile_id: str = DEFAULT_PROFILE_ID) -> dict[str, Any]:
        """Synchronous wrapper for get_dashboard_metrics_async."""
        return _run_async_compat(cls.get_dashboard_metrics_async(profile_id))

    @classmethod
    async def get_retention_items_async(
        cls, profile_id: str = DEFAULT_PROFILE_ID
    ) -> list[dict[str, Any]]:
        """Return spaced repetition retention reviews from PostgreSQL."""
        try:
            async with get_db_session() as session:
                stmt = (
                    select(MathLabRetentionItemModel)
                    .where(
                        MathLabRetentionItemModel.profile_id == profile_id,
                        MathLabRetentionItemModel.status == "PENDING",
                    )
                    .order_by(MathLabRetentionItemModel.scheduled_for.asc())
                )
                items = (await session.execute(stmt)).scalars().all()
                return [
                    {
                        "id": it.id,
                        "module_id": it.module_id,
                        "mistake_category": it.mistake_category,
                        "scheduled_for": it.scheduled_for.isoformat(),
                        "review_count": it.review_count,
                        "status": it.status,
                    }
                    for it in items
                ]
        except Exception as exc:
            print(f"[MathLabService] DB error in get_retention_items_async: {exc}")
            return []

    @classmethod
    def get_retention_items(cls, profile_id: str = DEFAULT_PROFILE_ID) -> list[dict[str, Any]]:
        return _run_async_compat(cls.get_retention_items_async(profile_id))
