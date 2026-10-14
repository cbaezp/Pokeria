# Workflow: Adding a Poker Math or Curriculum Exercise

> **Target Audience**: Human Contributors and AI Coding Agents
> **Universal Directive**: [AGENTS.md](../../AGENTS.md)

---

## 1. Exercise Design Standards (Mandatory Requirements)

Whenever adding a new exercise to Math Lab (`apps/api/app/domain/math_lab/`) or Curriculum Lessons (`apps/api/app/domain/curriculum/`), the following 10 criteria **must** be satisfied:

1. **Exact Scenario Assumptions**: State explicit game context (e.g. 6-Max No-Limit Hold'em, 100BB effective stacks, cash vs. tournament, rake structure).
2. **Clearly Defined Pot & Bet Units**: Explicitly specify whether calculations are in big blinds (BB), chip counts, or percentage of pot.
3. **Verified Mathematical Formulas**: Use authoritative formulas from [`apps/api/app/domain/math_lab/`](../../apps/api/app/domain/math_lab/) (pot odds, MDF, alpha, semi-bluff EV).
4. **Independent Reference Answers**: Precompute the correct numeric or multiple-choice answer using closed-form algebra or independent calculation. Never rely on circular code assertions.
5. **Validation of Generated Cards**: Ensure all 52 card bitmasks are unique and no card is dealt twice between hole cards and community board.
6. **Correct Result Provenance**: Tag each question with its true provenance (`EXACT_ANALYTICAL_DERIVATION`, `SOLVER_VERIFIED_EQUILIBRIUM`, or `ILLUSTRATIVE_PRACTICE_CHART`).
7. **Grading Tolerance**: Define acceptable rounding margins (e.g. $\pm 0.5\%$ for equity estimates, exact match for combinatorics).
8. **Numerical Edge-Case Coverage**: Test boundary conditions (0 outs, 22 outs, 100% pot odds, negative EV, all-in overbets).
9. **Lesson Linkage**: Link the exercise directly to its parent chapter, unit, and curriculum prerequisite node in `taxonomy.py`.
10. **Persistent Learner-Result Integration**: Connect submissions to `decision_events` with appropriate `grading_status` so learner metrics and spaced repetition intervals update accurately.

---

## 2. Step-by-Step Implementation

1. **Define Exercise Data**:
   Add exercise definition in `apps/api/app/domain/math_lab/curriculum_content.py` or `course_lessons.py`:
   ```python
   MathExercise(
       id="ex_pot_odds_river_call_01",
       module_id="mod_01_pot_odds",
       category="POT_ODDS",
       difficulty="BEGINNER",
       game_format="CASH_6MAX",
       question_type="NUMERIC",
       prompt="The pot is 100 chips. Opponent bets 50 chips on the river. What equity do you need to call?",
       context_data={"pot": 100, "bet": 50},
       exact_answer=25.0,
       acceptable_tolerance=0.5,
       unit="%",
       step_by_step_solution=[
           "1. Total pot after opponent bet = 100 + 50 = 150 chips.",
           "2. Total pot if you call = 150 + 50 = 200 chips.",
           "3. Required equity = Call / (Pot + Call) = 50 / 200 = 25.0%."
       ],
       reference_formula="C / (P + C)"
   )
   ```

2. **Add Independent Unit Test**:
   In `tests/unit/curriculum/test_curriculum_service.py` or `apps/api/tests/unit/domain/test_math_lab_math.py`:
   - Verify that submitting `25.0` grades as `CORRECT`.
   - Verify that submitting `23.0` grades as `INCORRECT`.
   - Verify that step-by-step solutions are returned.

3. **Verify Linter & Formatter**:
   ```bash
   .venv/bin/ruff check . && .venv/bin/ruff format --check .
   biome check apps/web/src
   ```
