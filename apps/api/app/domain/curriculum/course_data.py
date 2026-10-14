"""Course Data Architecture for Pokeria Guided Learning Path.

Houses comprehensive, pedagogical Texas Hold'em course content:
- CHAPTER 1: The Poker Table (Rules, Hand Rankings, Positions, Betting, Stack Sizes, Chapter Challenge)
- CHAPTER 2: Understanding Ranges (Unknown Holdings, 13x13 Matrix, Combos/Blockers, Positional Ranges, Range Charts, Chapter Challenge)
- CHAPTER 3: The Mathematics of Decisions (Pot Odds, Equity, Outs Rule of 2/4, Expected Value EV, Bet Sizing)
- CHAPTER 4: Preflop Strategy (RFI by Position, Facing Opens, 3-Betting, Stack Depth)
- CHAPTER 5: Postflop Strategy (Board Textures, Range & Nut Advantage, C-Betting, Bluffs & Bluff-Catching)
- CHAPTER 6: Tournament Strategy (Stack Pressure, Push/Fold, ICM Basics, Final Table Pay Jumps)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class InteractiveLessonStep:
    step_number: int
    title: str
    step_type: str  # "EXPLAIN", "INTERACT", "CHECK", "EXPLAIN_AGAIN", "APPLY", "RECAP", "COMMIT"
    content_markdown: str
    key_takeaway: str
    component_type: str | None = None
    component_props: dict[str, Any] = field(default_factory=dict)
    quiz_question: dict[str, Any] | None = None
    example_hand_or_spot: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_number": self.step_number,
            "title": self.title,
            "step_type": self.step_type,
            "content": self.content_markdown,
            "content_markdown": self.content_markdown,
            "key_takeaway": self.key_takeaway,
            "component_type": self.component_type,
            "component_props": self.component_props,
            "quiz_question": self.quiz_question,
            "example_hand_or_spot": self.example_hand_or_spot,
        }


@dataclass(frozen=True)
class CurriculumUnit:
    id: str
    chapter_id: str
    unit_number: int
    title: str
    summary: str
    lesson_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "chapter_id": self.chapter_id,
            "unit_number": self.unit_number,
            "title": self.title,
            "summary": self.summary,
            "lesson_ids": self.lesson_ids,
        }


@dataclass(frozen=True)
class CurriculumChapter:
    id: str
    chapter_number: int
    title: str
    subtitle: str
    description: str
    icon: str
    color_theme: str
    unit_ids: list[str] = field(default_factory=list)
    checkpoint_lesson_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "chapter_number": self.chapter_number,
            "title": self.title,
            "subtitle": self.subtitle,
            "description": self.description,
            "icon": self.icon,
            "color_theme": self.color_theme,
            "unit_ids": self.unit_ids,
            "checkpoint_lesson_id": self.checkpoint_lesson_id,
        }


# ============================================================================
# CHAPTER 1 — THE POKER TABLE
# ============================================================================

CHAPTER_1 = CurriculumChapter(
    id="chap_1_table",
    chapter_number=1,
    title="Chapter 1: The Poker Table",
    subtitle="Foundations of Texas Hold'em",
    description="Learn how hands are dealt, the 10 hand rankings, table positions, blinds, and stack depth.",
    icon="table",
    color_theme="emerald",
    unit_ids=[
        "unit_1_holdem_rules",
        "unit_2_hand_rankings",
        "unit_3_table_positions",
        "unit_4_blinds_betting",
        "unit_5_stack_sizes",
    ],
    checkpoint_lesson_id="lesson.c1.challenge",
)

# Chapter 1 Units
UNIT_1_1 = CurriculumUnit(
    id="unit_1_holdem_rules",
    chapter_id="chap_1_table",
    unit_number=1,
    title="Unit 1: How Texas Hold'em Works",
    summary="The mechanics of hole cards, community cards, the 5 betting rounds, and how pots are won.",
    lesson_ids=["lesson.c1.u1.how_holdem_works"],
)

UNIT_1_2 = CurriculumUnit(
    id="unit_2_hand_rankings",
    chapter_id="chap_1_table",
    unit_number=2,
    title="Unit 2: Hand Rankings",
    summary="Master the 10 hand tiers, kickers, and constructing the best five-card poker hand.",
    lesson_ids=["lesson.c1.u2.hand_rankings"],
)

UNIT_1_3 = CurriculumUnit(
    id="unit_3_table_positions",
    chapter_id="chap_1_table",
    unit_number=3,
    title="Unit 3: Table Positions",
    summary="Learn BTN, SB, BB, UTG, HJ, CO, preflop vs postflop action order, and positional leverage.",
    lesson_ids=["lesson.c1.u3.table_positions"],
)

UNIT_1_4 = CurriculumUnit(
    id="unit_4_blinds_betting",
    chapter_id="chap_1_table",
    unit_number=4,
    title="Unit 4: Blinds, Antes & Legal Actions",
    summary="Compulsory bets, the 6 core actions (fold, check, call, bet, raise, all-in), and legal limits.",
    lesson_ids=["lesson.c1.u4.blinds_and_betting"],
)

UNIT_1_5 = CurriculumUnit(
    id="unit_5_stack_sizes",
    chapter_id="chap_1_table",
    unit_number=5,
    title="Unit 5: Stack Sizes & Effective Stacks",
    summary="Measuring stacks in Big Blinds (BB), identifying effective stack, and short vs deep stack dynamics.",
    lesson_ids=["lesson.c1.u5.stack_sizes", "lesson.c1.challenge"],
)


# ============================================================================
# CHAPTER 2 — UNDERSTANDING RANGES
# ============================================================================

CHAPTER_2 = CurriculumChapter(
    id="chap_2_ranges",
    chapter_number=2,
    title="Chapter 2: Understanding Ranges",
    subtitle="From Single Hands to Strategic Sets",
    description="Learn how poker players reason in ranges, read the 13x13 matrix, count combinations, and track positional expansion.",
    icon="grid",
    color_theme="indigo",
    unit_ids=[
        "unit_2_1_what_is_range",
        "unit_2_2_matrix_13x13",
        "unit_2_3_combinations",
        "unit_2_4_positional_ranges",
        "unit_2_5_reading_charts",
    ],
    checkpoint_lesson_id="lesson.c2.challenge",
)

UNIT_2_1 = CurriculumUnit(
    id="unit_2_1_what_is_range",
    chapter_id="chap_2_ranges",
    unit_number=1,
    title="Unit 1: What Is a Range?",
    summary="Why guessing an exact hand fails and how reasoning in probability distributions unlocks poker mastery.",
    lesson_ids=["lesson.c2.u1.what_is_a_range"],
)

UNIT_2_2 = CurriculumUnit(
    id="unit_2_2_matrix_13x13",
    chapter_id="chap_2_ranges",
    unit_number=2,
    title="Unit 2: The 13x13 Hand Matrix",
    summary="The gold-standard guide to the 169 starting-hand grid, pairs, suited, and offsuit notation.",
    lesson_ids=["lesson.c2.u2.how_to_read_a_range"],
)

UNIT_2_3 = CurriculumUnit(
    id="unit_2_3_combinations",
    chapter_id="chap_2_ranges",
    unit_number=3,
    title="Unit 3: Hand Combinations & Blockers",
    summary="Combination math: 6 pocket pairs, 4 suited, 12 offsuit, and card removal effects.",
    lesson_ids=["lesson.c2.u3.combinations_and_blockers"],
)

UNIT_2_4 = CurriculumUnit(
    id="unit_2_4_positional_ranges",
    chapter_id="chap_2_ranges",
    unit_number=4,
    title="Unit 4: Position Changes Ranges",
    summary="Compare tight early-position ranges (UTG ~15%) with loose late-position ranges (BTN ~43%).",
    lesson_ids=["lesson.c2.u4.positional_expansion"],
)

UNIT_2_5 = CurriculumUnit(
    id="unit_2_5_reading_charts",
    chapter_id="chap_2_ranges",
    unit_number=5,
    title="Unit 5: Reading Range Charts & Solver Labels",
    summary="Pure vs mixed frequencies, frequency gradients, and understanding conceptual vs GTO references.",
    lesson_ids=["lesson.c2.u5.range_charts_and_frequencies", "lesson.c2.challenge"],
)


# ============================================================================
# CHAPTER 3 — THE MATHEMATICS OF DECISIONS
# ============================================================================

CHAPTER_3 = CurriculumChapter(
    id="chap_3_math",
    chapter_number=3,
    title="Chapter 3: The Mathematics of Decisions",
    subtitle="Pot Odds, Equity, Outs & Expected Value",
    description="Calculate pot odds, count drawing outs, apply the Rule of 2 & 4, and understand positive Expected Value (+EV).",
    icon="calculator",
    color_theme="sky",
    unit_ids=["unit_3_1_pot_odds_equity", "unit_3_2_outs_ev", "unit_3_3_implied_odds_sizing"],
    checkpoint_lesson_id="lesson.c3.checkpoint",
)

UNIT_3_1 = CurriculumUnit(
    id="unit_3_1_pot_odds_equity",
    chapter_id="chap_3_math",
    unit_number=1,
    title="Unit 1: Pot Odds & Equity",
    summary="The ratio of bet to pot and how much equity you need to justify calling.",
    lesson_ids=["lesson.c3.u1.pot_odds_equity"],
)

UNIT_3_2 = CurriculumUnit(
    id="unit_3_2_outs_ev",
    chapter_id="chap_3_math",
    unit_number=2,
    title="Unit 2: Outs & The Rule of 2 & 4",
    summary="Fast street equity estimation and counting unseen cards that complete your hand.",
    lesson_ids=["lesson.c3.u2.outs_and_expected_value"],
)

UNIT_3_3 = CurriculumUnit(
    id="unit_3_3_implied_odds_sizing",
    chapter_id="chap_3_math",
    unit_number=3,
    title="Unit 3: Implied Odds & Expected Value (EV)",
    summary="Calculate EV of poker decisions and incorporate future bets through implied odds.",
    lesson_ids=["lesson.c3.u3.implied_odds_and_sizing", "lesson.c3.checkpoint"],
)


# ============================================================================
# CHAPTER 4 — PREFLOP STRATEGY
# ============================================================================

CHAPTER_4 = CurriculumChapter(
    id="chap_4_preflop",
    chapter_number=4,
    title="Chapter 4: Preflop Strategy",
    subtitle="Raise-First-In, Defenses, and 3-Bet Pots",
    description="Construct positional opening ranges, defend blinds properly, and execute 3-bets and 4-bets.",
    icon="shield",
    color_theme="amber",
    unit_ids=["unit_4_1_rfi_strategy", "unit_4_2_three_betting", "unit_4_3_stack_depth"],
    checkpoint_lesson_id="lesson.c4.checkpoint",
)

UNIT_4_1 = CurriculumUnit(
    id="unit_4_1_rfi_strategy",
    chapter_id="chap_4_preflop",
    unit_number=1,
    title="Unit 1: Raise-First-In (RFI) Mastery",
    summary="Equilibrium opening ranges by position and avoiding open-limping.",
    lesson_ids=["lesson.preflop.position", "lesson.preflop.btn_rfi"],
)

UNIT_4_2 = CurriculumUnit(
    id="unit_4_2_three_betting",
    chapter_id="chap_4_preflop",
    unit_number=2,
    title="Unit 2: Facing Opens & 3-Bet Strategy",
    summary="Defending the blinds, calling in position, and linear vs polarized 3-bets.",
    lesson_ids=["lesson.c4.u2.facing_raises_blind_defense", "lesson.c4.u2.three_bet_strategy"],
)

UNIT_4_3 = CurriculumUnit(
    id="unit_4_3_stack_depth",
    chapter_id="chap_4_preflop",
    unit_number=3,
    title="Unit 3: Stack-Depth Adjustments",
    summary="How deep (100bb), medium (40bb), and shallow (15bb) stacks change preflop values.",
    lesson_ids=["lesson.c4.u3.stack_depth_adjustments", "lesson.c4.checkpoint"],
)


# ============================================================================
# CHAPTER 5 — POSTFLOP STRATEGY
# ============================================================================

CHAPTER_5 = CurriculumChapter(
    id="chap_5_postflop",
    chapter_number=5,
    title="Chapter 5: Postflop Strategy",
    subtitle="Textures, Advantages, and Street Planning",
    description="Analyze dry vs wet boards, leverage range and nut advantage, and execute multi-street barrel lines.",
    icon="layers",
    color_theme="purple",
    unit_ids=["unit_5_1_textures_advantages", "unit_5_2_barreling_rivers"],
    checkpoint_lesson_id="lesson.c5.checkpoint",
)

UNIT_5_1 = CurriculumUnit(
    id="unit_5_1_textures_advantages",
    chapter_id="chap_5_postflop",
    unit_number=1,
    title="Unit 1: Board Textures & Range Advantage",
    summary="How board cards interact with preflop ranges to dictate continuation betting.",
    lesson_ids=["lesson.c5.u1.board_textures_advantage", "lesson.postflop.cbet_fundamentals"],
)

UNIT_5_2 = CurriculumUnit(
    id="unit_5_2_barreling_rivers",
    chapter_id="chap_5_postflop",
    unit_number=2,
    title="Unit 2: Multi-Street Barrels & River Bluff-Catching",
    summary="Turn aggression, sizing geometry, and blocker-driven river calling.",
    lesson_ids=[
        "lesson.postflop.turn_barrel",
        "lesson.postflop.river_bluffcatch",
        "lesson.c5.checkpoint",
    ],
)


# ============================================================================
# CHAPTER 6 — TOURNAMENT STRATEGY
# ============================================================================

CHAPTER_6 = CurriculumChapter(
    id="chap_6_tournament",
    chapter_number=6,
    title="Chapter 6: Tournament Strategy",
    subtitle="Stack Pressure, Push/Fold & ICM Dynamics",
    description="Survive and thrive in tournaments: shallow stack push/fold charts, bubble pressure, and final-table risk premiums.",
    icon="trophy",
    color_theme="rose",
    unit_ids=["unit_6_1_push_fold", "unit_6_2_icm_dynamics"],
    checkpoint_lesson_id="lesson.c6.checkpoint",
)

UNIT_6_1 = CurriculumUnit(
    id="unit_6_1_push_fold",
    chapter_id="chap_6_tournament",
    unit_number=1,
    title="Unit 1: Shallow Stacks & Push/Fold",
    summary="Mathematical all-in or fold decisions when stacks drop below 15 Big Blinds.",
    lesson_ids=["lesson.tourn.formats_and_stack_pressure", "lesson.tourn.pushfold"],
)

UNIT_6_2 = CurriculumUnit(
    id="unit_6_2_icm_dynamics",
    chapter_id="chap_6_tournament",
    unit_number=2,
    title="Unit 2: Independent Chip Model (ICM) & Risk Premiums",
    summary="The non-linear value of tournament chips, bubble survival, and laddering pay jumps.",
    lesson_ids=[
        "lesson.tourn.icm_fundamentals",
        "lesson.tourn.bubble_and_payjumps",
        "lesson.c6.checkpoint",
    ],
)

ALL_CHAPTERS: list[CurriculumChapter] = [
    CHAPTER_1,
    CHAPTER_2,
    CHAPTER_3,
    CHAPTER_4,
    CHAPTER_5,
    CHAPTER_6,
]

ALL_UNITS: list[CurriculumUnit] = [
    UNIT_1_1,
    UNIT_1_2,
    UNIT_1_3,
    UNIT_1_4,
    UNIT_1_5,
    UNIT_2_1,
    UNIT_2_2,
    UNIT_2_3,
    UNIT_2_4,
    UNIT_2_5,
    UNIT_3_1,
    UNIT_3_2,
    UNIT_3_3,
    UNIT_4_1,
    UNIT_4_2,
    UNIT_4_3,
    UNIT_5_1,
    UNIT_5_2,
    UNIT_6_1,
    UNIT_6_2,
]
