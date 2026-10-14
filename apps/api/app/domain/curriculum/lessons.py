"""Curriculum Lessons and Learning Paths for Poker Lab Phase D.

Provides structured lessons organized into prerequisite-based learning paths:
1. Tournament & Cash Foundations
2. Preflop Mastery (RFI, Defense, Shove/Fold)
3. Flop Continuation Betting & C-Bet Defense
4. Turn Aggression & Polarized Barrels
5. River Decision-Making (Polarization, Thin Value, Bluff-Catching)
6. Tournament ICM Dynamics & Final Table Survival
7. Exploitative Adjustments & Calibration
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.curriculum.course_data import (
    ALL_CHAPTERS,
    ALL_UNITS,
    CurriculumChapter,
    CurriculumUnit,
    InteractiveLessonStep,
)
from app.domain.curriculum.course_lessons import ALL_NEW_COURSE_LESSONS, CourseLesson


@dataclass(frozen=True)
class LessonStep:
    step_number: int
    title: str
    content_markdown: str
    key_takeaway: str
    example_hand_or_spot: str | None = None


@dataclass(frozen=True)
class CurriculumLesson:
    id: str
    path_id: str
    title: str
    summary: str
    skill_id: str
    difficulty_level: str  # "FOUNDATIONAL", "INTERMEDIATE", "ADVANCED", "ELITE"
    estimated_minutes: int
    prerequisite_lesson_ids: list[str] = field(default_factory=list)
    steps: list[LessonStep | InteractiveLessonStep] = field(default_factory=list)
    linked_scenario_id: str | None = None
    is_interactive: bool = True
    chapter_id: str = "chap_1_table"
    unit_id: str = "unit_1_holdem_rules"
    is_unit_challenge: bool = False
    is_chapter_checkpoint: bool = False
    transfer_scenario_id: str | None = None
    transfer_availability: str = "UNAVAILABLE_INSUFFICIENT_VALIDATED_CONTENT"
    transfer_rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "path_id": self.path_id,
            "chapter_id": self.chapter_id,
            "unit_id": self.unit_id,
            "title": self.title,
            "summary": self.summary,
            "skill_id": self.skill_id,
            "target_skill_id": self.skill_id,  # Compatibility alias
            "difficulty_level": self.difficulty_level,
            "estimated_minutes": self.estimated_minutes,
            "prerequisite_lesson_ids": self.prerequisite_lesson_ids,
            "steps": [
                s.to_dict()
                if hasattr(s, "to_dict")
                else {
                    "step_number": s.step_number,
                    "title": s.title,
                    "content": s.content_markdown,
                    "content_markdown": s.content_markdown,
                    "key_takeaway": s.key_takeaway,
                    "example_hand_or_spot": getattr(s, "example_hand_or_spot", None),
                    "step_type": getattr(s, "step_type", "EXPLAIN"),
                    "component_type": getattr(s, "component_type", None),
                    "component_props": getattr(s, "component_props", {}),
                    "quiz_question": getattr(s, "quiz_question", None),
                }
                for s in self.steps
            ],
            "linked_scenario_id": self.linked_scenario_id,
            "associated_scenarios": [self.linked_scenario_id] if self.linked_scenario_id else [],
            "key_takeaways": [s.key_takeaway for s in self.steps],
            "is_interactive": self.is_interactive,
            "is_unit_challenge": self.is_unit_challenge,
            "is_chapter_checkpoint": self.is_chapter_checkpoint,
            "transfer_scenario_id": self.transfer_scenario_id,
            "transfer_availability": self.transfer_availability,
            "transfer_rationale": self.transfer_rationale,
        }


@dataclass(frozen=True)
class LearningPath:
    id: str
    title: str
    description: str
    domain: str
    order_index: int
    lesson_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "domain": self.domain,
            "order_index": self.order_index,
            "lesson_ids": self.lesson_ids,
        }


CURRICULUM_PATHS: list[LearningPath] = [
    LearningPath(
        id="path.foundations",
        title="Path 1: Foundations of Positional & Mathematical Poker",
        description="Core principles of position, pot odds, minimum defense frequency, and game identity.",
        domain="PREFLOP",
        order_index=1,
        lesson_ids=["lesson.preflop.position", "lesson.preflop.btn_rfi"],
    ),
    LearningPath(
        id="path.tournament_short_stack",
        title="Path 2: Tournament Stack Dynamics & Push/Fold",
        description="Surviving and accumulating chips in tournament environments with shallow stack depths (10-15bb).",
        domain="TOURNAMENT_ICM",
        order_index=2,
        lesson_ids=["lesson.tourn.pushfold"],
    ),
    LearningPath(
        id="path.postflop_barrelling",
        title="Path 3: Postflop Multi-Street Planning & Barrels",
        description="Transitioning from flop equity advantages to polarized turn and river betting lines.",
        domain="POSTFLOP_TURN",
        order_index=3,
        lesson_ids=["lesson.postflop.turn_barrel", "lesson.postflop.turn_checkcall"],
    ),
    LearningPath(
        id="path.river_polarization",
        title="Path 4: River Polarization & Bluff-Catching",
        description="Mastering the final betting street: polarized value-to-bluff ratios and blocker-driven calling.",
        domain="POSTFLOP_RIVER",
        order_index=4,
        lesson_ids=["lesson.postflop.river_value", "lesson.postflop.river_bluffcatch"],
    ),
    LearningPath(
        id="path.icm_final_table",
        title="Path 5: Advanced Tournament ICM & Risk Premiums",
        description="Elite final-table strategy: calculating non-linear chip value, avoiding suicide collisions, and ICM pressure.",
        domain="TOURNAMENT_ICM",
        order_index=5,
        lesson_ids=["lesson.tourn.icm_fundamentals"],
    ),
]


CURRICULUM_LESSONS: list[CurriculumLesson] = [
    CurriculumLesson(
        id="lesson.preflop.position",
        path_id="path.foundations",
        title="The Power of Position: Acting Last Postflop",
        summary="Why playing in position (IP) dramatically increases profitability and allows wider preflop opening.",
        skill_id="preflop.fundamentals",
        difficulty_level="FOUNDATIONAL",
        estimated_minutes=8,
        prerequisite_lesson_ids=[],
        steps=[
            LessonStep(
                step_number=1,
                title="Informational Advantage",
                content_markdown=(
                    "In Texas Hold'em, the player who acts last on every postflop street possesses an insurmountable "
                    "informational advantage. You observe your opponent's action (check or bet) before committing any chips."
                ),
                key_takeaway="Acting last allows you to realize more equity with medium-strength hands and bluff more effectively.",
                example_hand_or_spot="Button vs Big Blind: Button sees BB check before deciding whether to c-bet, pot-control, or take a free card.",
            ),
            LessonStep(
                step_number=2,
                title="Positional Opening Ranges",
                content_markdown=(
                    "Because of position and the number of players left to act behind you, opening ranges expand as position moves around the table:\n"
                    "- **UTG (Under the Gun)**: ~15% of hands (tight, linear)\n"
                    "- **Cutoff (CO)**: ~28% of hands\n"
                    "- **Button (BTN)**: ~42-45% of hands (wide, speculative)"
                ),
                key_takeaway="Never open hands from early position that require late position advantage to be profitable.",
            ),
        ],
        linked_scenario_id="pack_cash_6max_100bb_btn_rfi_AsKs",
        transfer_scenario_id=None,
        transfer_availability="UNAVAILABLE_INSUFFICIENT_VALIDATED_CONTENT",
        transfer_rationale="Held-out non-Button preflop opening spots (UTG/HJ/CO) with multi-position solver trees are pending solver generation.",
    ),
    CurriculumLesson(
        id="lesson.preflop.btn_rfi",
        path_id="path.foundations",
        title="Button Raise-First-In (RFI) Strategy",
        summary="Detailed breakdown of the 43% Button opening range in 100bb 6-max cash games.",
        skill_id="preflop.rfi.late",
        difficulty_level="FOUNDATIONAL",
        estimated_minutes=10,
        prerequisite_lesson_ids=["lesson.preflop.position"],
        steps=[
            LessonStep(
                step_number=1,
                title="Equilibrium BTN Range Composition",
                content_markdown=(
                    "A solver-backed 100bb Button opening range includes:\n"
                    "- All pocket pairs (22-AA)\n"
                    "- All suited aces (A2s-AKs) and most suited broadways\n"
                    "- Suited connectors down to 54s\n"
                    "- Suited one-gappers (e.g. 86s, 75s)\n"
                    "- Offsuit broadways (A9o+, KTo+, QTo+, JTo)"
                ),
                key_takeaway="The Button opens broadly because only two players (SB and BB) can contest the pot, and the BTN is guaranteed position postflop.",
            ),
            LessonStep(
                step_number=2,
                title="Sizing and Blind Defense Dynamics",
                content_markdown=(
                    "Standard modern sizing is **2.25bb to 2.5bb**. Sizing too large risks too many chips against 3-bets; "
                    "sizing to min-raise (2.0bb) gives the Big Blind exceptional pot odds to call with nearly any two cards."
                ),
                key_takeaway="2.5bb is the sweet spot between risk and fold equity.",
            ),
        ],
        linked_scenario_id="pack_cash_6max_100bb_btn_rfi_AsKs",
        transfer_scenario_id=None,
        transfer_availability="UNAVAILABLE_INSUFFICIENT_VALIDATED_CONTENT",
        transfer_rationale="Alternative preflop sizing variations (2.2bb / minraise) held-out charts are pending.",
    ),
    CurriculumLesson(
        id="lesson.tourn.pushfold",
        path_id="path.tournament_short_stack",
        title="Tournament Push/Fold: Maximizing 12bb Fold Equity",
        summary="When effective stacks drop below 15bb, postflop maneuvering disappears. Master the mathematical shoving thresholds.",
        skill_id="preflop.tournament.pushfold",
        difficulty_level="INTERMEDIATE",
        estimated_minutes=12,
        prerequisite_lesson_ids=["lesson.preflop.position"],
        steps=[
            LessonStep(
                step_number=1,
                title="The Anatomy of an Open Shove",
                content_markdown=(
                    "At 12bb with a Big Blind Ante in play, the dead chips in the pot represent an instant ~2.5bb boost (over 20% stack increase!). "
                    "Shoving capitalizes on fold equity: you win the pot uncontested a large percentage of the time."
                ),
                key_takeaway="Short-stack shoves are driven by fold equity plus live cards when called, not pure hand strength.",
            ),
            LessonStep(
                step_number=2,
                title="Small Blind vs Big Blind Shoving",
                content_markdown=(
                    "From the Small Blind with 12bb effective, equilibrium pushes roughly 50-60% of all holdings, including weak aces, "
                    "suited kings, and suited connectors. Hands like As Ks are massive +EV jams."
                ),
                key_takeaway="Passing up small +EV shoves in tournament play causes stack death by blind erosion.",
            ),
        ],
        linked_scenario_id="pack_tourn_8max_12bb_sb_shove_bba_chipev_AsKs",
        transfer_scenario_id=None,
        transfer_availability="UNAVAILABLE_INSUFFICIENT_VALIDATED_CONTENT",
        transfer_rationale="Dedicated held-out push/fold solver packs across 10bb/15bb or late position are pending generation.",
    ),
    CurriculumLesson(
        id="lesson.postflop.turn_barrel",
        path_id="path.postflop_barrelling",
        title="The Second Barrel: Turn Aggression Mechanics",
        summary="Firing a second bet on the turn after your flop c-bet was called. Understanding equity shifts and board runouts.",
        skill_id="postflop.turn.barrel",
        difficulty_level="ADVANCED",
        estimated_minutes=14,
        prerequisite_lesson_ids=["lesson.preflop.btn_rfi"],
        steps=[
            LessonStep(
                step_number=1,
                title="Turn Card Categorization",
                content_markdown=(
                    "When the turn is dealt, ask: *Who does this card help?*\n"
                    "- **Blank cards** (low, uncoordinated): Reinforces the preflop aggressor's equity advantage.\n"
                    "- **Overcards** (Ace, King): Drastically improves preflop opener's range.\n"
                    "- **Coordinated cards** (flush/straight completing): Often hits the flop caller's condensed defense range."
                ),
                key_takeaway="Continue aggression on cards that strengthen your range or give you high-equity semi-bluffs.",
            ),
            LessonStep(
                step_number=2,
                title="Polarizing the Second Barrel",
                content_markdown=(
                    "Unlike small flop c-bets, turn bets should generally use larger sizings (66% to 75% pot) because the caller's "
                    "range is now defined and resilient. Your betting range should polarize between strong value hands and semi-bluffs with river outs."
                ),
                key_takeaway="Avoid weak, sizing-tells on the turn. Bet with purpose: either building a pot or generating fold equity with equity to fall back on.",
            ),
        ],
        linked_scenario_id="pack_64bf1668d802a75d_n0_2d2h",
        transfer_scenario_id="pack_cert_cash_turn_barrel_dd24266c0d7fdbc0_n0_2d2h",
        transfer_availability="AVAILABLE",
        transfer_rationale="Held-out single-raised turn runout (Qh Jd 4s 8c at 80bb) testing turn barrel continuation on altered queen-high texture.",
    ),
    CurriculumLesson(
        id="lesson.postflop.turn_checkcall",
        path_id="path.postflop_barrelling",
        title="Navigating Wet Turns: Check/Calling with Showdown Value",
        summary="How to handle draw-heavy turn cards when out of position with medium-strength made hands.",
        skill_id="postflop.turn.checkcall",
        difficulty_level="ADVANCED",
        estimated_minutes=12,
        prerequisite_lesson_ids=["lesson.postflop.turn_barrel"],
        steps=[
            LessonStep(
                step_number=1,
                title="Showdown Value vs Three Streets of Value",
                content_markdown=(
                    "Hands like middle pair, weak top pair, or third pair cannot withstand three streets of betting. "
                    "Checking the turn controls the pot size while inducing bluffs from aggressive opponents."
                ),
                key_takeaway="Do not turn showdown value into a bluff by betting when called only by better.",
            ),
        ],
        linked_scenario_id="pack_330d29b8bd559335_n0_2d2h",
        transfer_scenario_id=None,
        transfer_availability="UNAVAILABLE_INSUFFICIENT_VALIDATED_CONTENT",
        transfer_rationale="Additional validated turn check/calling holdout packs on alternate wet runouts are pending solver generation.",
    ),
    CurriculumLesson(
        id="lesson.postflop.river_value",
        path_id="path.river_polarization",
        title="River Polarization: Value-Betting & Nut Disparity",
        summary="The mathematics of river bets: why the solver bets big with nuts and air while checking middle strength.",
        skill_id="postflop.river.value.betting",
        difficulty_level="ELITE",
        estimated_minutes=15,
        prerequisite_lesson_ids=["lesson.postflop.turn_barrel"],
        steps=[
            LessonStep(
                step_number=1,
                title="The Polarized Distribution",
                content_markdown=(
                    "On the river, card runouts are complete; no more draws exist. Therefore, every betting hand is either:\n"
                    "1. **Pure Value**: Hands ahead of opponent's calling range.\n"
                    "2. **Pure Bluff**: Hands with zero showdown value that win only when opponent folds.\n\n"
                    "Medium hands must check to realize their showdown equity."
                ),
                key_takeaway="Never bet a river hand that wins when checked down but loses when called.",
            ),
            LessonStep(
                step_number=2,
                title="Balancing Value-to-Bluff Ratios",
                content_markdown=(
                    "For a pot-sized river bet, the opponent gets 2:1 on a call (needs 33.3% equity). "
                    "To make opponent indifferent, your betting range must contain exactly 66.7% value and 33.3% bluffs."
                ),
                key_takeaway="Mathematical balance prevents opponents from exploiting you by always calling or always folding.",
            ),
        ],
        linked_scenario_id="pack_632c34943e011ef5_n0_2d2h",
        transfer_scenario_id="pack_cert_cash_river_polarized_f649a12740e64d90_n0_2d2h",
        transfer_availability="AVAILABLE",
        transfer_rationale="Held-out dry river texture (As Kd 7h 2c 9s at 100bb) testing multi-size polarized value-to-bluff ratios under deeper stacks.",
    ),
    CurriculumLesson(
        id="lesson.postflop.river_bluffcatch",
        path_id="path.river_polarization",
        title="Blocker Theory in River Bluff-Catching",
        summary="When facing a river barrel, how holding specific card removal (blockers) turns close folds into profitable calls.",
        skill_id="postflop.river.bluffcatch",
        difficulty_level="ELITE",
        estimated_minutes=15,
        prerequisite_lesson_ids=["lesson.postflop.river_value"],
        steps=[
            LessonStep(
                step_number=1,
                title="Minimum Defense Frequency (MDF)",
                content_markdown=(
                    "MDF dictates the percentage of your range you must defend to prevent opponent from bluffing profitably with any two cards:\n\n"
                    "> **Formula: Minimum Defense Frequency**\n\n"
                    "> **MDF** = Pot ÷ (Pot + Bet)\n\n"
                    "Against a half-pot bet, MDF is 66.7%. Against a pot-sized bet, MDF is 50.0%."
                ),
                key_takeaway="MDF is a defensive baseline; blocker effects determine WHICH specific hands within your range make the call.",
            ),
            LessonStep(
                step_number=2,
                title="The Flush Blocker Effect",
                content_markdown=(
                    "On a 3-flush board (e.g. As 8s 2s ... 7d), holding the single spade (like Ks or Qs) blocks opponent's flushes "
                    "while leaving all their missed straight draws intact. This makes a pair with the flush card a vastly superior bluff-catch."
                ),
                key_takeaway="Holding a card of the flush suit drastically increases the probability that opponent is bluffing.",
            ),
        ],
        linked_scenario_id="pack_d3f179c8517b68a7_n0_2d2h",
        transfer_scenario_id=None,
        transfer_availability="UNAVAILABLE_INSUFFICIENT_VALIDATED_CONTENT",
        transfer_rationale="Held-out 4-flush or paired-board bluff-catching scenarios are pending solver generation.",
    ),
    CurriculumLesson(
        id="lesson.tourn.icm_fundamentals",
        path_id="path.icm_final_table",
        title="Tournament ICM: The Cost of Elimination",
        summary="Chips lost vs chips won: why tournament decisions require significant risk premiums near payout thresholds.",
        skill_id="tournament.icm.fundamentals",
        difficulty_level="ELITE",
        estimated_minutes=18,
        prerequisite_lesson_ids=["lesson.preflop.position"],
        steps=[
            LessonStep(
                step_number=1,
                title="The Non-Linearity of Tournament Chips",
                content_markdown=(
                    "In a cash game, $1 always equals $1. In a tournament, doubling your chip stack NEVER doubles your tournament equity ($ EV). "
                    "The last chip in your stack is worth infinitely more than an additional chip added to a massive stack, because losing your last chip eliminates you."
                ),
                key_takeaway="In tournaments, chips you preserve are worth significantly more than chips you win.",
            ),
            LessonStep(
                step_number=2,
                title="Risk Premium Calculation",
                content_markdown=(
                    "Risk premium is the additional equity required to make a call profitable in $ EV over pure Chip-EV. "
                    "On a final table bubble or pay jump, risk premiums can range from 8% to over 25%, meaning even hands with +Chip-EV must be folded."
                ),
                key_takeaway="Never take marginal chip gambles when laddering up pay jumps provides guaranteed tournament dollars.",
            ),
        ],
        linked_scenario_id="pack_cert_tourn_hu_icm_64f7fb839c4df671_n0_2d2h",
        transfer_scenario_id=None,
        transfer_availability="UNAVAILABLE_INSUFFICIENT_VALIDATED_CONTENT",
        transfer_rationale="Alternative final-table tournament pay jump payout models are pending solver generation.",
    ),
]


def _build_unified_lessons() -> list[CurriculumLesson | CourseLesson]:
    new_ids = {cl.id for cl in ALL_NEW_COURSE_LESSONS}
    merged: list[CurriculumLesson | CourseLesson] = list(ALL_NEW_COURSE_LESSONS)
    for lesson in CURRICULUM_LESSONS:
        if lesson.id not in new_ids:
            merged.append(lesson)
    return merged


class LessonCatalogRegistry:
    """Indexed catalog of structured curriculum lessons, paths, chapters, and units."""

    def __init__(
        self,
        paths: list[LearningPath] | None = None,
        lessons: list[CurriculumLesson | CourseLesson] | None = None,
        chapters: list[CurriculumChapter] | None = None,
        units: list[CurriculumUnit] | None = None,
    ) -> None:
        self._paths = paths or CURRICULUM_PATHS
        self._lessons = lessons or _build_unified_lessons()
        self._chapters = chapters or ALL_CHAPTERS
        self._units = units or ALL_UNITS
        self._paths_by_id = {p.id: p for p in self._paths}
        self._lessons_by_id = {lesson.id: lesson for lesson in self._lessons}
        self._chapters_by_id = {c.id: c for c in self._chapters}
        self._units_by_id = {u.id: u for u in self._units}

    def get_all_paths(self) -> list[LearningPath]:
        return sorted(self._paths, key=lambda p: p.order_index)

    def get_all_chapters(self) -> list[CurriculumChapter]:
        return sorted(self._chapters, key=lambda c: c.chapter_number)

    def get_all_units(self) -> list[CurriculumUnit]:
        return list(self._units)

    def get_chapter(self, chapter_id: str) -> CurriculumChapter | None:
        return self._chapters_by_id.get(chapter_id)

    def get_unit(self, unit_id: str) -> CurriculumUnit | None:
        return self._units_by_id.get(unit_id)

    def get_all_lessons(self) -> list[CurriculumLesson | CourseLesson]:
        return list(self._lessons)

    def get_lesson(self, lesson_id: str) -> CurriculumLesson | CourseLesson | None:
        return self._lessons_by_id.get(lesson_id)

    def get_lessons_for_path(self, path_id: str) -> list[CurriculumLesson | CourseLesson]:
        return [lesson for lesson in self._lessons if lesson.path_id == path_id]

    def get_lessons_for_unit(self, unit_id: str) -> list[CurriculumLesson | CourseLesson]:
        return [lesson for lesson in self._lessons if getattr(lesson, "unit_id", None) == unit_id]

    def get_lessons_for_chapter(self, chapter_id: str) -> list[CurriculumLesson | CourseLesson]:
        return [
            lesson for lesson in self._lessons if getattr(lesson, "chapter_id", None) == chapter_id
        ]

    def get_lessons_for_skill(self, skill_id: str) -> list[CurriculumLesson | CourseLesson]:
        return [lesson for lesson in self._lessons if lesson.skill_id == skill_id]

    def is_lesson_unlocked(self, lesson_id: str, completed_lesson_ids: set[str]) -> bool:
        lesson = self.get_lesson(lesson_id)
        if not lesson:
            return False
        if not lesson.prerequisite_lesson_ids:
            return True
        return all(prereq in completed_lesson_ids for prereq in lesson.prerequisite_lesson_ids)

    def get_full_course_tree(self) -> dict[str, Any]:
        """Hierarchical tree representation: Chapter -> Unit -> Lesson Nodes."""
        chapters_data = []
        for ch in self.get_all_chapters():
            units_data = []
            for uid in ch.unit_ids:
                u = self.get_unit(uid)
                if not u:
                    continue
                unit_lessons = [
                    self.get_lesson(lid).to_dict()
                    for lid in u.lesson_ids
                    if self.get_lesson(lid) is not None
                ]
                units_data.append(
                    {
                        **u.to_dict(),
                        "lessons": unit_lessons,
                    }
                )
            chapters_data.append(
                {
                    **ch.to_dict(),
                    "units": units_data,
                }
            )
        return {
            "total_chapters": len(chapters_data),
            "chapters": chapters_data,
        }


# Global instance
lesson_catalog = LessonCatalogRegistry()
