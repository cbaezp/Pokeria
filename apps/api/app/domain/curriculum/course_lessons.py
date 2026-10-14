"""Comprehensive Lesson Definitions for Pokeria Guided Learning Path.

Includes rich, interactive, step-by-step lessons with:
- EXPLAIN, INTERACT, CHECK, EXPLAIN_AGAIN, APPLY, RECAP, COMMIT step types
- Interactive component definitions: table position, 13x13 matrix, hand comparison, combo counter, pot odds
- Complete Chapter 1 & Chapter 2 foundational inventory
- Certified Chapter 2 Unit 2 gold-standard lesson: 'How to Read a Poker Range'
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.curriculum.course_data import InteractiveLessonStep


@dataclass(frozen=True)
class CourseLesson:
    id: str
    path_id: str
    chapter_id: str
    unit_id: str
    title: str
    summary: str
    skill_id: str
    difficulty_level: str  # "FOUNDATIONAL", "INTERMEDIATE", "ADVANCED", "ELITE"
    estimated_minutes: int
    prerequisite_lesson_ids: list[str] = field(default_factory=list)
    steps: list[InteractiveLessonStep] = field(default_factory=list)
    linked_scenario_id: str | None = None
    is_interactive: bool = True
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
            "target_skill_id": self.skill_id,
            "difficulty_level": self.difficulty_level,
            "estimated_minutes": self.estimated_minutes,
            "prerequisite_lesson_ids": self.prerequisite_lesson_ids,
            "steps": [s.to_dict() for s in self.steps],
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


# ============================================================================
# CHAPTER 1 LESSONS
# ============================================================================

LESSON_C1_U1_RULES = CourseLesson(
    id="lesson.c1.u1.how_holdem_works",
    path_id="path.foundations",
    chapter_id="chap_1_table",
    unit_id="unit_1_holdem_rules",
    title="How Texas Hold'em Works",
    summary="Understand hole cards, community cards, the 5 betting rounds, and how a hand is won.",
    skill_id="rules.holdem_fundamentals",
    difficulty_level="FOUNDATIONAL",
    estimated_minutes=5,
    prerequisite_lesson_ids=[],
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="The Structure: 2 Private + 5 Shared Cards",
            step_type="EXPLAIN",
            component_type="betting_timeline",
            component_props={"currentRound": "preflop", "showCards": True},
            content_markdown=(
                "Texas Hold'em is a game of incomplete information played with a standard 52-card deck.\n\n"
                "Each player is dealt **two private cards face down** (called 'hole cards') that belong only to them.\n\n"
                "Over the course of the hand, up to **five community cards** are dealt face up in the center of the table. "
                "Every player shares these community cards to construct their best possible five-card poker hand."
            ),
            key_takeaway="You receive 2 private hole cards and share 5 community cards with the table.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="The Five Rounds of a Hand",
            step_type="EXPLAIN",
            component_type="betting_timeline",
            component_props={"interactive": True},
            content_markdown=(
                "Every hand proceeds through up to five distinct rounds:\n\n"
                "1. **Preflop**: Players receive their 2 hole cards and make the first round of bets.\n"
                "2. **Flop**: 3 community cards are dealt face up, followed by betting.\n"
                "3. **Turn**: A 4th community card is dealt face up, followed by betting.\n"
                "4. **River**: The 5th and final community card is dealt, followed by the final betting round.\n"
                "5. **Showdown**: Remaining players reveal their cards to determine the winner."
            ),
            key_takeaway="The rounds always progress: Preflop → Flop (3 cards) → Turn (1 card) → River (1 card) → Showdown.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Knowledge Check: The Flop",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "How many community cards are dealt face up on the Flop?",
                "options": ["1 card", "2 cards", "3 cards", "5 cards"],
                "correct_index": 2,
                "explanation": "Correct! The Flop consists of exactly 3 community cards dealt simultaneously.",
                "remediation": "Remember the sequence: Preflop has 0 community cards, the Flop deals 3, the Turn deals 1, and the River deals 1 (3 + 1 + 1 = 5 total).",
            },
            content_markdown="Test your understanding of the dealing structure.",
            key_takeaway="The Flop brings the first 3 community cards.",
        ),
        InteractiveLessonStep(
            step_number=4,
            title="How a Hand Is Won",
            step_type="EXPLAIN",
            content_markdown=(
                "There are only **two ways** to win a pot in Texas Hold'em:\n\n"
                "1. **Uncontested Bet (Folding Opponents)**: You bet or raise, and every other player folds. You win the pot immediately without having to show your cards!\n"
                "2. **Best Hand at Showdown**: Two or more players reach the end of the river betting round, reveal their cards, and you hold the highest-ranking five-card combination."
            ),
            key_takeaway="You win by having the best hand at showdown OR by betting so that all opponents fold.",
        ),
        InteractiveLessonStep(
            step_number=5,
            title="Recap: Texas Hold'em Core Rules",
            step_type="RECAP",
            component_type="lesson_completion_summary",
            component_props={
                "xpEarned": 20,
                "masteryKey": "rules.holdem_fundamentals",
                "conceptsLearned": [
                    "2 private hole cards + 5 shared community cards",
                    "Rounds: Preflop, Flop (3), Turn (1), River (1), Showdown",
                    "Winning methods: Fold all opponents or showdown best 5 cards",
                ],
            },
            content_markdown="Great job! You now understand the fundamental lifecycle of a Texas Hold'em hand.",
            key_takeaway="You are ready to learn how poker hands are ranked.",
        ),
    ],
)

LESSON_C1_U2_RANKINGS = CourseLesson(
    id="lesson.c1.u2.hand_rankings",
    path_id="path.foundations",
    chapter_id="chap_1_table",
    unit_id="unit_2_hand_rankings",
    title="Hand Rankings: High Card to Royal Flush",
    summary="Master all 10 hand rankings, kicker ties, and selecting the best five-card combination.",
    skill_id="rules.hand_rankings",
    difficulty_level="FOUNDATIONAL",
    estimated_minutes=6,
    prerequisite_lesson_ids=["lesson.c1.u1.how_holdem_works"],
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="The 10 Hand Categories",
            step_type="EXPLAIN",
            component_type="hand_ranking",
            component_props={"mode": "reference_ladder"},
            content_markdown=(
                "Poker hands are ranked in strict mathematical order of rarity. "
                "Study the official hierarchy ladder above from Royal Flush (#1) down to High Card (#10) "
                "to master which five-card combination wins the pot at showdown."
            ),
            key_takeaway="A Full House beats a Flush; a Flush beats a Straight; Three of a Kind beats Two Pair.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="Interactive Hand Comparison: Full House vs Flush",
            step_type="INTERACT",
            component_type="hand_ranking",
            component_props={
                "handA": ["Kh", "Kd"],
                "handB": ["Ah", "Th"],
                "board": ["Ks", "8h", "3h", "2h", "8c"],
                "showEvaluation": True,
            },
            content_markdown=(
                "Compare these two hands on a board of K♠ 8♥ 3♥ 2♥ 8♣:\n\n"
                "- **Player A (K♥ K♦)** makes a Full House: Kings full of Eights (K-K-K-8-8).\n"
                "- **Player B (A♥ T♥)** makes an Ace-high Flush (A-T-8-3-2 of hearts).\n\n"
                "Because a Full House is statistically rarer than a simple Flush, Player A wins the pot."
            ),
            key_takeaway="Full House beats any Flush, regardless of whether the Flush holds an Ace.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Kickers: The Tie-Breaker",
            step_type="EXPLAIN",
            component_type="hand_ranking",
            component_props={
                "handA": ["As", "Kh"],
                "handB": ["Ah", "Qd"],
                "board": ["Ad", "9c", "6s", "4d", "2h"],
                "showEvaluation": True,
            },
            content_markdown=(
                "What happens when two players make the same pair?\n\n"
                "On a board of A♦ 9♣ 6♠ 4♦ 2♥:\n"
                "- Player A holds A♠ K♥ → Five-card hand: Pair of Aces with King kicker (A-A-K-9-6).\n"
                "- Player B holds A♥ Q♦ → Five-card hand: Pair of Aces with Queen kicker (A-A-Q-9-6).\n\n"
                "Both have a Pair of Aces, but Player A's King outranks Player B's Queen. Player A wins the entire pot!"
            ),
            key_takeaway="A kicker is an unpaired side-card that breaks ties between hands of identical rank.",
        ),
        InteractiveLessonStep(
            step_number=4,
            title="Knowledge Check: Kickers in Action",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "Player A holds A♠ K♣ and Player B holds A♦ J♠. The board is A♥ 8♦ 7♠ 3♣ 2♦. Who wins?",
                "options": [
                    "Player A wins with a higher King kicker",
                    "Player B wins with a Jack kicker",
                    "It is a tie and the pot is split",
                    "The player on the Button automatically wins",
                ],
                "correct_index": 0,
                "explanation": "Correct! Both players hold a Pair of Aces, but Player A's five cards (A-A-K-8-7) beat Player B's (A-A-J-8-7) because King beats Jack.",
                "remediation": "Always assemble the exact best five cards for each player. Compare ranks from highest to lowest.",
            },
            content_markdown="Verify your understanding of kickers.",
            key_takeaway="The highest side-card (kicker) breaks the tie.",
        ),
        InteractiveLessonStep(
            step_number=5,
            title="Recap: Hand Rankings Mastery",
            step_type="RECAP",
            component_type="lesson_completion_summary",
            component_props={
                "xpEarned": 25,
                "masteryKey": "rules.hand_rankings",
                "conceptsLearned": [
                    "Full hierarchy: High Card → Royal Flush",
                    "Full House beats Flush; Flush beats Straight",
                    "Kickers determine the winner when pairs match",
                ],
            },
            content_markdown="Outstanding! You have mastered poker hand rankings and kicker mechanics.",
            key_takeaway="You now know with certainty which hand wins at showdown.",
        ),
    ],
)

LESSON_C1_U3_POSITIONS = CourseLesson(
    id="lesson.c1.u3.table_positions",
    path_id="path.foundations",
    chapter_id="chap_1_table",
    unit_id="unit_3_table_positions",
    title="Table Positions & Action Order",
    summary="Master BTN, SB, BB, UTG, HJ, CO, preflop vs postflop action order, and positional leverage.",
    skill_id="table.positions",
    difficulty_level="FOUNDATIONAL",
    estimated_minutes=7,
    prerequisite_lesson_ids=["lesson.c1.u2.hand_rankings"],
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="The Dealer Button & The Blinds",
            step_type="EXPLAIN",
            component_type="poker_table",
            component_props={"highlightSeats": ["BTN", "SB", "BB"], "heroPosition": "BTN"},
            content_markdown=(
                "Table position in poker is determined relative to the **Dealer Button (BTN)**.\n\n"
                "- **The Button (BTN)**: The best seat at the table. Acts last on every postflop betting round.\n"
                "- **Small Blind (SB)**: Sits directly clockwise from the Button. Posts a mandatory half-bet before cards are dealt.\n"
                "- **Big Blind (BB)**: Sits directly clockwise from the SB. Posts a full bet before cards are dealt."
            ),
            key_takeaway="The Button is the anchor of the table; the blinds post mandatory bets and sit immediately clockwise.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="6-Max Positions: From First to Last",
            step_type="INTERACT",
            component_type="poker_table",
            component_props={"interactive": True, "showOrder": True},
            content_markdown=(
                "In modern 6-max poker, the six seats are named in order of action:\n\n"
                "1. **UTG (Under the Gun)**: Sits clockwise from the Big Blind. Acts first preflop with 5 players behind.\n"
                "2. **HJ (Hijack)**: Middle position; acts after UTG.\n"
                "3. **CO (Cutoff)**: Late position; sits right before the Button. High-leverage stealing seat.\n"
                "4. **BTN (Button)**: The premier position. Acts last on all postflop streets.\n"
                "5. **SB (Small Blind)**: Out of position postflop to everyone except the BB.\n"
                "6. **BB (Big Blind)**: Acts last preflop, but acts first postflop alongside SB."
            ),
            key_takeaway="Positions in order: UTG (Early) → HJ (Middle) → CO (Late) → BTN (In Position) → SB → BB.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Preflop vs Postflop Action Order",
            step_type="EXPLAIN",
            content_markdown=(
                "Notice the crucial difference between preflop and postflop action:\n\n"
                "- **Preflop**: Action begins with **UTG** (left of BB) and ends with the **Big Blind**.\n"
                "- **Postflop (Flop, Turn, River)**: Action begins with the **Small Blind** (or closest remaining player left of Button) and ALWAYS ends with the **Button**!\n\n"
                "Because the Button acts last on Flop, Turn, and River, the Button has complete information about opponents' decisions before acting."
            ),
            key_takeaway="UTG acts first preflop. The Small Blind acts first postflop. The Button acts LAST postflop.",
        ),
        InteractiveLessonStep(
            step_number=4,
            title="Interactive Check: Preflop Action",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "In a 6-max game before the flop (preflop), which player must act first?",
                "options": [
                    "Under the Gun (UTG)",
                    "The Button (BTN)",
                    "The Small Blind (SB)",
                    "The Big Blind (BB)",
                ],
                "correct_index": 0,
                "explanation": "Correct! Preflop, the blinds have already posted bets, so the action begins with the player to the left of the Big Blind: Under the Gun (UTG).",
                "remediation": "Remember: The blinds act last preflop. Therefore, UTG is 'Under the Gun' because they must act first without seeing anyone else's move.",
            },
            content_markdown="Verify preflop action sequence.",
            key_takeaway="UTG acts first preflop.",
        ),
        InteractiveLessonStep(
            step_number=5,
            title="Interactive Check: Postflop Action",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "On the Flop, which player acts LAST among remaining players?",
                "options": [
                    "The Button (BTN)",
                    "The Small Blind (SB)",
                    "Under the Gun (UTG)",
                    "The Big Blind (BB)",
                ],
                "correct_index": 0,
                "explanation": "Spot on! Postflop, action moves clockwise starting from the blinds, meaning the Button is guaranteed to act last on the Flop, Turn, and River.",
                "remediation": "The Button is the most profitable seat precisely because it acts last on every postflop street.",
            },
            content_markdown="Verify postflop positional advantage.",
            key_takeaway="The Button always acts last postflop.",
        ),
        InteractiveLessonStep(
            step_number=6,
            title="Recap: Table Positions",
            step_type="RECAP",
            component_type="lesson_completion_summary",
            component_props={
                "xpEarned": 25,
                "masteryKey": "table.positions",
                "conceptsLearned": [
                    "6-max seats: UTG, HJ, CO, BTN, SB, BB",
                    "Preflop: UTG acts first, BB acts last",
                    "Postflop: Blinds act first, BTN acts last (In Position)",
                ],
            },
            content_markdown="Fantastic work! You have mastered the table layout and action sequencing.",
            key_takeaway="Position is power in poker: always prefer playing hands in late position.",
        ),
    ],
)

LESSON_C1_U4_BLINDS = CourseLesson(
    id="lesson.c1.u4.blinds_and_betting",
    path_id="path.foundations",
    chapter_id="chap_1_table",
    unit_id="unit_4_blinds_betting",
    title="Blinds, Antes & Legal Actions",
    summary="Understand compulsory bets, pot math, the 6 core actions, and legal betting rules.",
    skill_id="rules.betting_actions",
    difficulty_level="FOUNDATIONAL",
    estimated_minutes=5,
    prerequisite_lesson_ids=["lesson.c1.u3.table_positions"],
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="Why Blinds and Antes Exist",
            step_type="EXPLAIN",
            content_markdown=(
                "Without blinds, players would simply fold every hand until they were dealt Pocket Aces.\n\n"
                "To create incentive to contest pots, **the Small Blind and Big Blind** post mandatory bets before any cards are dealt.\n"
                "In tournaments, an **Ante** is also posted by each player (or the Big Blind via Big Blind Ante) to build an even larger starting pot."
            ),
            key_takeaway="Blinds and antes create starting pots that make defending and stealing profitable.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="The 6 Core Actions",
            step_type="EXPLAIN",
            content_markdown=(
                "When it is your turn to act, you may take one of the following legal actions:\n\n"
                "- **Fold**: Surrender your cards and any chips already committed. You forfeit participation in the pot.\n"
                "- **Check**: Pass action to the next player without betting any chips (only legal if no player has bet before you).\n"
                "- **Call**: Match the exact amount of the current outstanding bet.\n"
                "- **Bet**: Place the first wager of a round when no prior bet has been made.\n"
                "- **Raise**: Increase the size of a prior bet made by an opponent.\n"
                "- **All-In**: Wager your entire remaining chip stack."
            ),
            key_takeaway="You can Check only when facing no bet. Facing a bet, you must Fold, Call, or Raise.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Knowledge Check: Legal Actions",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "An opponent bets $20 on the turn. Can you legally 'Check'?",
                "options": [
                    "No, because checking is only legal when there is no active bet to call",
                    "Yes, checking is always legal at any time",
                    "Yes, but only if you hold a pair",
                    "No, you are forced to fold",
                ],
                "correct_index": 0,
                "explanation": "Correct! When facing an active bet, your only legal options are to Fold, Call the $20, or Raise to a larger amount.",
                "remediation": "Checking means betting zero chips. If someone has already bet, you cannot bet zero to stay in the hand.",
            },
            content_markdown="Test your grasp of legal action rules.",
            key_takeaway="You cannot check when facing an outstanding bet.",
        ),
        InteractiveLessonStep(
            step_number=4,
            title="Recap: Betting Actions",
            step_type="RECAP",
            component_type="lesson_completion_summary",
            component_props={
                "xpEarned": 20,
                "masteryKey": "rules.betting_actions",
                "conceptsLearned": [
                    "Blinds & antes seed the pot",
                    "6 core actions: Fold, Check, Call, Bet, Raise, All-In",
                    "Check vs Bet legal distinctions",
                ],
            },
            content_markdown="Great job mastering the legal rules of poker betting rounds!",
            key_takeaway="You are ready to learn about stack sizes and effective stacks.",
        ),
    ],
)

LESSON_C1_U5_STACKS = CourseLesson(
    id="lesson.c1.u5.stack_sizes",
    path_id="path.foundations",
    chapter_id="chap_1_table",
    unit_id="unit_5_stack_sizes",
    title="Stack Sizes & Effective Stacks",
    summary="Learn to count in Big Blinds (BB), identify effective stack, and adapt to short vs deep stack dynamics.",
    skill_id="stack.effective_stacks",
    difficulty_level="FOUNDATIONAL",
    estimated_minutes=5,
    prerequisite_lesson_ids=["lesson.c1.u4.blinds_and_betting"],
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="The Universal Currency: Big Blinds (BB)",
            step_type="EXPLAIN",
            content_markdown=(
                "Smart poker players do not measure their chips in dollars or raw chip counts. They measure their stack in **Big Blinds (BB)**:\n\n"
                "> **Formula: Stack in Big Blinds**\n"
                "> **Stack in BB** = Total Chips ÷ Current Big Blind\n\n"
                "For example, if you have 10,000 chips and the blinds are 250 / 500, your stack is **10,000 / 500 = 20 BB**. "
                "Measuring in Big Blinds allows strategic principles to apply identically across all blind levels."
            ),
            key_takeaway="Always convert chip stacks into Big Blinds (Chips ÷ Big Blind).",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="Effective Stack: The True Money at Stake",
            step_type="INTERACT",
            component_type="effective_stack",
            component_props={"heroStack": 100, "villainStack": 35, "interactive": True},
            content_markdown=(
                "When two players enter a pot, **the effective stack is the smaller of the two stacks**.\n\n"
                "- If Hero has 100 BB and Villain has 35 BB, the effective stack is **35 BB**.\n"
                "- Neither player can win or lose more than 35 BB from the other in this hand.\n\n"
                "Your strategic plan must always be calibrated to the effective stack, NOT your total stack!"
            ),
            key_takeaway="The effective stack is the smaller stack involved in the hand.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Knowledge Check: Effective Stack Calculation",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "Hero has 75 BB on the Button. The Big Blind has 22 BB. If they play heads-up, what is the effective stack?",
                "options": ["22 BB", "75 BB", "97 BB", "53 BB"],
                "correct_index": 0,
                "explanation": "Correct! The Big Blind can only risk their 22 BB. Therefore, the effective stack for the hand is 22 BB.",
                "remediation": "Effective stack = min(Stack A, Stack B). The smaller stack caps the maximum loss/gain.",
            },
            content_markdown="Test your effective stack calculation.",
            key_takeaway="Effective stack is always min(Player A, Player B).",
        ),
        InteractiveLessonStep(
            step_number=4,
            title="Recap: Stack Sizing Mastery",
            step_type="RECAP",
            component_type="lesson_completion_summary",
            component_props={
                "xpEarned": 20,
                "masteryKey": "stack.effective_stacks",
                "conceptsLearned": [
                    "Always calculate stacks in Big Blinds",
                    "Effective stack = smaller stack between contesting players",
                    "Shallow stacks (<20 BB) vs Deep stacks (>50 BB)",
                ],
            },
            content_markdown="Excellent! You are now prepared to take the Chapter 1 Challenge.",
            key_takeaway="You have completed all instructional units in Chapter 1.",
        ),
    ],
)

LESSON_C1_CHALLENGE = CourseLesson(
    id="lesson.c1.challenge",
    path_id="path.foundations",
    chapter_id="chap_1_table",
    unit_id="unit_5_stack_sizes",
    title="Chapter 1 Challenge: Table & Rules Mastery",
    summary="Comprehensive checkpoint challenge testing positions, hand rankings, action order, and effective stacks.",
    skill_id="checkpoint.chapter_1",
    difficulty_level="FOUNDATIONAL",
    estimated_minutes=6,
    prerequisite_lesson_ids=["lesson.c1.u5.stack_sizes"],
    is_unit_challenge=True,
    is_chapter_checkpoint=True,
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="Chapter 1 Checkpoint Challenge",
            step_type="EXPLAIN",
            content_markdown=(
                "Welcome to the **Chapter 1 Checkpoint Challenge**!\n\n"
                "In this challenge, you will prove your command of poker fundamentals:\n"
                "1. Identify seats and positional power\n"
                "2. Accurately compare poker hands and kickers\n"
                "3. Determine preflop and postflop action order\n"
                "4. Calculate effective stack sizes\n\n"
                "Score 100% on the following checks to unlock Chapter 2: Understanding Ranges!"
            ),
            key_takeaway="Prove your foundational knowledge to unlock Chapter 2.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="Challenge 1: Seat Identification",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "Which table position acts last on the Flop, Turn, and River?",
                "options": [
                    "The Button (BTN)",
                    "Under the Gun (UTG)",
                    "The Small Blind (SB)",
                    "The Big Blind (BB)",
                ],
                "correct_index": 0,
                "explanation": "Correct! The Button possesses permanent postflop position.",
                "remediation": "The Button always acts last postflop.",
            },
            content_markdown="Seat mastery check.",
            key_takeaway="The Button is the ultimate late position.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Challenge 2: Hand Ranking Showdown",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "Which of the following hands is the highest-ranking combination?",
                "options": ["Full House", "Flush", "Straight", "Three of a Kind"],
                "correct_index": 0,
                "explanation": "Correct! Full House beats a Flush, Straight, and Three of a Kind.",
                "remediation": "Ranks: Straight Flush > Quads > Full House > Flush > Straight > Three of a Kind.",
            },
            content_markdown="Hand ranking comparison check.",
            key_takeaway="Full House beats Flush.",
        ),
        InteractiveLessonStep(
            step_number=4,
            title="Challenge 3: Effective Stack",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "Player A has 120 BB and Player B has 40 BB. What is the effective stack between them?",
                "options": ["40 BB", "120 BB", "80 BB", "160 BB"],
                "correct_index": 0,
                "explanation": "Correct! The smaller stack of 40 BB is the effective stack.",
                "remediation": "Effective stack is always the minimum of the two stacks.",
            },
            content_markdown="Effective stack verification.",
            key_takeaway="Effective stack is 40 BB.",
        ),
        InteractiveLessonStep(
            step_number=5,
            title="Chapter 1 Complete!",
            step_type="COMMIT",
            component_type="chapter_checkpoint",
            component_props={
                "chapterNumber": 1,
                "chapterTitle": "The Poker Table",
                "badgeName": "Table Master",
                "xpEarned": 50,
                "nextChapterId": "chap_2_ranges",
            },
            content_markdown=(
                "### 🎉 Chapter 1 Completed!\n\n"
                "You have demonstrated mastery over Texas Hold'em fundamentals. "
                "You understand the rules, hand rankings, table seats, betting actions, and stack sizes.\n\n"
                "**Chapter 2: Understanding Ranges** is now unlocked!"
            ),
            key_takeaway="Chapter 1 Mastered! Proceed to Chapter 2.",
        ),
    ],
)


# ============================================================================
# CHAPTER 2 LESSONS
# ============================================================================

LESSON_C2_U1_WHAT_IS_RANGE = CourseLesson(
    id="lesson.c2.u1.what_is_a_range",
    path_id="path.foundations",
    chapter_id="chap_2_ranges",
    unit_id="unit_2_1_what_is_range",
    title="What Is a Range?",
    summary="Why guessing an exact hand fails and how reasoning in probability distributions unlocks poker mastery.",
    skill_id="ranges.fundamentals",
    difficulty_level="FOUNDATIONAL",
    estimated_minutes=5,
    prerequisite_lesson_ids=["lesson.c1.challenge"],
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="The Flaw of Single-Hand Guessing",
            step_type="EXPLAIN",
            content_markdown=(
                "Amateur players often say things like: *'I put him on Ace-King'*, or *'She definitely has pocket Queens.'*\n\n"
                "This is the most dangerous mental habit in poker. Your opponent is never holding just one hand. "
                "Depending on their position, style, and prior actions, they could hold dozens of different cards that would take the exact same action."
            ),
            key_takeaway="Never guess an exact hand; reason about all possible hands an opponent could have.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="Defining a Range",
            step_type="EXPLAIN",
            content_markdown=(
                "A **range** is the complete collection of all possible holdings a player could have at a specific moment in the hand.\n\n"
                "When a tight player raises from early position, their range might consist of:\n"
                "- High pocket pairs (AA, KK, QQ, JJ, TT, 99)\n"
                "- Premium broadway cards (AKs, AQs, AKo)\n"
                "- Strong suited broadways (KQs, QJs)\n\n"
                "As the hand progresses and the player bets, checks, or raises, you narrow down this range street by street."
            ),
            key_takeaway="A range is the set of all candidate hands consistent with a player's previous actions.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Knowledge Check: Range Thinking",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "Why do skilled poker players think in ranges instead of guessing a specific hand?",
                "options": [
                    "Because an opponent could hold many different hands that take the same action",
                    "Because it is illegal to name an opponent's exact hand at the table",
                    "Because all players always hold identical starting cards",
                    "Because ranges only apply when playing against computer bots",
                ],
                "correct_index": 0,
                "explanation": "Correct! Players take identical actions with multiple different holdings. Reasoning in ranges accounts for every possibility.",
                "remediation": "Opponents have a distribution of hands, not a single known holding.",
            },
            content_markdown="Test your grasp of range philosophy.",
            key_takeaway="Think in distributions of hands, not individual cards.",
        ),
        InteractiveLessonStep(
            step_number=4,
            title="Recap: What Is a Range?",
            step_type="RECAP",
            component_type="lesson_completion_summary",
            component_props={
                "xpEarned": 20,
                "masteryKey": "ranges.fundamentals",
                "conceptsLearned": [
                    "Avoid putting opponents on a single hand",
                    "A range is the entire set of possible candidate holdings",
                    "Ranges narrow progressively on each betting round",
                ],
            },
            content_markdown="Excellent! You are now prepared to explore the standard 13x13 poker range matrix.",
            key_takeaway="You are ready for the gold-standard lesson: How to Read a Poker Range.",
        ),
    ],
)


# ============================================================================
# CERTIFIED GOLD-STANDARD LESSON: CHAPTER 2, UNIT 2
# "How to Read a Poker Range"
# ============================================================================

LESSON_C2_U2_READ_RANGE = CourseLesson(
    id="lesson.c2.u2.how_to_read_a_range",
    path_id="path.foundations",
    chapter_id="chap_2_ranges",
    unit_id="unit_2_2_matrix_13x13",
    title="How to Read a Poker Range",
    summary="Master the 13x13 matrix, AKs vs AKo notation, combination arithmetic (6-4-12), and positional range expansion.",
    skill_id="ranges.matrix_reading",
    difficulty_level="FOUNDATIONAL",
    estimated_minutes=7,
    prerequisite_lesson_ids=["lesson.c2.u1.what_is_a_range"],
    steps=[
        # Step 1: Explain the purpose of a range
        InteractiveLessonStep(
            step_number=1,
            title="The Purpose of a Range",
            step_type="EXPLAIN",
            content_markdown=(
                "In poker, your opponent never reveals their cards until showdown. "
                "If you try to guess a single exact holding (such as 'I think he has Ace-King'), you will constantly make disastrous mistakes.\n\n"
                "Instead, strong poker players think in **ranges**: the complete mathematical spectrum of all possible hands an opponent could hold given the actions they took."
            ),
            key_takeaway="A range represents the complete distribution of possible holdings a player can hold at any given moment.",
        ),
        # Step 2: Show the interactive 13x13 matrix
        InteractiveLessonStep(
            step_number=2,
            title="The 13x13 Starting Hand Matrix",
            step_type="INTERACT",
            component_type="range_matrix_explorer",
            component_props={
                "interactive": True,
                "highlightPairs": True,
                "highlightSuited": False,
                "highlightOffsuit": False,
            },
            content_markdown=(
                "There are exactly 169 distinct starting-hand classes in Texas Hold'em. We arrange them into a standardized 13x13 grid:\n\n"
                "- The **diagonal** running from top-left to bottom-right contains the **13 Pocket Pairs** (AA down to 22).\n"
                "- The **upper right triangle** above the diagonal contains the **78 Suited Hands** (like AKs, QJs).\n"
                "- The **lower left triangle** below the diagonal contains the **78 Offsuit Hands** (like AKo, QJo)."
            ),
            key_takeaway="Pocket pairs run down the diagonal; suited hands sit in the upper right; offsuit hands sit in the lower left.",
        ),
        # Step 3: Explain AKs versus AKo versus AA
        InteractiveLessonStep(
            step_number=3,
            title="Understanding Notation: AKs vs AKo vs AA",
            step_type="EXPLAIN",
            component_type="hand_ranking",
            component_props={
                "handA": ["As", "Ks"],
                "handB": ["As", "Kh"],
                "board": [],
                "showEvaluation": False,
            },
            content_markdown=(
                "Poker notation uses compact single-letter suffixes to describe card properties:\n\n"
                "- **AKs** ('s' for Suited): Both cards share the same suit (e.g. A♠ K♠). Suited hands have flush potential, adding roughly +3-4% equity over offsuit versions.\n"
                "- **AKo** ('o' for Offsuit): Cards have different suits (e.g. A♠ K♥).\n"
                "- **AA**: Pocket Aces. Pocket pairs consist of two matching ranks on the diagonal and require no suffix."
            ),
            key_takeaway="'s' stands for Suited, 'o' stands for Offsuit, and pocket pairs have no suffix.",
        ),
        # Step 4: Ask the learner to identify suited and offsuit cells
        InteractiveLessonStep(
            step_number=4,
            title="Check: Matrix Layout",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "In the standard 13x13 poker range matrix, where are suited hands (such as KQs or 76s) always located?",
                "options": [
                    "Above and to the right of the pair diagonal",
                    "Directly on the diagonal from top-left to bottom-right",
                    "Below and to the left of the pair diagonal",
                    "Scattered randomly throughout the grid",
                ],
                "correct_index": 0,
                "explanation": "Correct! Suited hands ('s') always occupy the upper-right triangle above the diagonal pocket pairs. Offsuit hands ('o') occupy the lower-left.",
                "remediation": "Remember the convention: Pairs run diagonally (AA to 22). Suited hands are above the diagonal. Offsuit hands are below the diagonal.",
            },
            content_markdown="Verify your understanding of matrix cell placement.",
            key_takeaway="Upper-right = Suited ('s'); Lower-left = Offsuit ('o'); Center diagonal = Pairs.",
        ),
        # Step 5: Teach 4 suited, 12 offsuit, and 6 pocket-pair combinations
        InteractiveLessonStep(
            step_number=5,
            title="Combinations Math: 6, 4, and 12",
            step_type="EXPLAIN",
            component_type="range_combination_counter",
            component_props={
                "selectedClass": "AK",
                "showCombos": True,
            },
            content_markdown=(
                "Every cell on the 13x13 matrix represents a specific number of unique 2-card combinations (called **combos**) from the 52-card deck (1,326 total combos):\n\n"
                "- **Pocket Pair (e.g. AA)**: **6 combinations** (A♠A♥, A♠A♦, A♠A♣, A♥A♦, A♥A♣, A♦A♣)\n"
                "- **Suited Hand (e.g. AKs)**: **4 combinations** (A♠K♠, A♥K♥, A♦K♦, A♣K♣)\n"
                "- **Offsuit Hand (e.g. AKo)**: **12 combinations** (4 possible Aces × 3 non-matching Kings = 12)\n\n"
                "**Crucial Insight**: An offsuit hand like AKo is **three times more common** than its suited counterpart AKs!"
            ),
            key_takeaway="Every pocket pair has 6 combos; every suited hand has 4 combos; every offsuit hand has 12 combos.",
        ),
        # Step 6: Ask a combination-counting question
        InteractiveLessonStep(
            step_number=6,
            title="Check: Combination Counting",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "How many total starting card combinations make up any unpaired offsuit hand (such as KQo or JTo)?",
                "options": [
                    "4 combinations",
                    "6 combinations",
                    "12 combinations",
                    "16 combinations",
                ],
                "correct_index": 2,
                "explanation": "Spot on! There are 4 suits for the first card and 3 remaining suits for the second card (4 × 3 = 12 combinations).",
                "remediation": "An unpaired hand has 16 total combinations: 4 suited + 12 offsuit. Therefore, offsuit holdings always contain 12 distinct combinations.",
            },
            content_markdown="Test your combination arithmetic.",
            key_takeaway="Offsuit hands contain 12 combos; suited hands contain 4; pairs contain 6.",
        ),
        # Step 7: Introduce position-specific example and explain why range composition changes
        InteractiveLessonStep(
            step_number=7,
            title="Why Position Shapes Range Composition",
            step_type="APPLY",
            component_type="range_position_comparison",
            component_props={
                "pos1": "UTG",
                "pos2": "BTN",
                "interactive": True,
            },
            content_markdown=(
                "A player's range changes dramatically depending on their **position** at the table:\n\n"
                "- **Under the Gun (UTG)** acts first with 5 players behind. UTG opens a tight, concentrated range of ~15% of hands (premium pairs and broadways).\n"
                "- **The Button (BTN)** acts last postflop with only 2 players behind. BTN opens a wide, aggressive range of ~43% of hands including suited connectors and weaker broadways.\n\n"
                "Opening too wide from early position is the most common mistake made by beginners. Respect the power of position!"
            ),
            key_takeaway="Early position requires tight, linear ranges (~15%); late position allows wide, speculative ranges (~43%).",
        ),
        # Step 8: End with a knowledge check and completion summary
        InteractiveLessonStep(
            step_number=8,
            title="Recap & Range Mastery Summary",
            step_type="RECAP",
            component_type="lesson_completion_summary",
            component_props={
                "xpEarned": 30,
                "masteryKey": "ranges.matrix_reading",
                "conceptsLearned": [
                    "13x13 matrix: Pairs on diagonal, Suited above, Offsuit below",
                    "Suffixes: 's' for suited, 'o' for offsuit, none for pairs",
                    "Combo arithmetic: 6 pair, 4 suited, 12 offsuit combinations",
                    "Positional expansion: UTG (~15%) vs BTN (~43%)",
                ],
            },
            content_markdown=(
                "### 🎉 Congratulations!\n\n"
                "You have completed **How to Read a Poker Range**! You now speak the universal language of modern poker strategy.\n\n"
                "You can read any poker chart, count combinations accurately, and understand how position shapes ranges—without needing to guess or memorize blindly."
            ),
            key_takeaway="You have mastered range notation, matrix geography, and combination mathematics.",
        ),
    ],
)

LESSON_C2_U3_COMBOS = CourseLesson(
    id="lesson.c2.u3.combinations_and_blockers",
    path_id="path.foundations",
    chapter_id="chap_2_ranges",
    unit_id="unit_2_3_combinations",
    title="Hand Combinations & Blockers",
    summary="Learn how holding specific cards removes combos from an opponent's range (card removal effect).",
    skill_id="ranges.blockers",
    difficulty_level="FOUNDATIONAL",
    estimated_minutes=6,
    prerequisite_lesson_ids=["lesson.c2.u2.how_to_read_a_range"],
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="The Total Number of Hands: 1,326",
            step_type="EXPLAIN",
            content_markdown=(
                "In a 52-card deck, the number of distinct two-card combinations is:\n\n"
                "> **Formula: Total Starting Combinations**\n"
                "> C(52, 2) = (52 × 51) / 2 = **1,326 total combinations**\n\n"
                "- 13 pocket pairs × 6 combos = **78 combos** (5.9% of all hands)\n"
                "- 78 suited hand classes × 4 combos = **312 combos** (23.5% of all hands)\n"
                "- 78 offsuit hand classes × 12 combos = **936 combos** (70.6% of all hands)"
            ),
            key_takeaway="Over 70% of all starting hands dealt are offsuit hands.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="Card Removal: What Is a Blocker?",
            step_type="EXPLAIN",
            component_type="range_combination_counter",
            component_props={"heroCards": ["As", "Kh"], "targetClass": "AA"},
            content_markdown=(
                "When you hold a card in your hand, it is physically impossible for your opponent to hold that exact card.\n\n"
                "This is called **card removal** or **blocking**:\n"
                "- If you hold the A♠, there are only 3 Aces left in the deck.\n"
                "- Instead of 6 combinations of Pocket Aces (AA), your opponent can only have **3 combinations** of AA (a 50% reduction!).\n"
                "- Instead of 16 combinations of Ace-King (AK), your opponent can only hold **9 combinations** (a 44% reduction!)."
            ),
            key_takeaway="Holding an Ace cuts an opponent's possible combinations of AA in half.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Knowledge Check: Blocker Math",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "Hero holds A♠ K♠. How many combinations of Pocket Kings (KK) can an opponent possibly hold?",
                "options": ["3 combinations", "6 combinations", "4 combinations", "1 combination"],
                "correct_index": 0,
                "explanation": "Correct! Normally there are 6 combinations of KK. Because Hero holds the King of Spades, there are only 3 remaining Kings, leaving (3 × 2) / 2 = 3 combinations.",
                "remediation": "When 1 card of a pair is removed, the number of combinations drops from 6 to 3.",
            },
            content_markdown="Verify blocker effects.",
            key_takeaway="Holding 1 card of a pair cuts the combinations from 6 down to 3.",
        ),
        InteractiveLessonStep(
            step_number=4,
            title="Recap: Combinations & Blockers",
            step_type="RECAP",
            component_type="lesson_completion_summary",
            component_props={
                "xpEarned": 25,
                "masteryKey": "ranges.blockers",
                "conceptsLearned": [
                    "Total starting combos: 1,326",
                    "Blockers physically remove cards from opponent ranges",
                    "Holding an Ace or King cuts opponent top pairs in half",
                ],
            },
            content_markdown="Great work mastering combination counting and card removal!",
            key_takeaway="You now understand blockers, one of the most powerful concepts in modern poker.",
        ),
    ],
)

LESSON_C2_U4_EXPANSION = CourseLesson(
    id="lesson.c2.u4.positional_expansion",
    path_id="path.foundations",
    chapter_id="chap_2_ranges",
    unit_id="unit_2_4_positional_ranges",
    title="Position Changes Ranges",
    summary="Why early positions open tight and late positions open wide, with side-by-side visual comparisons.",
    skill_id="ranges.positional_expansion",
    difficulty_level="FOUNDATIONAL",
    estimated_minutes=5,
    prerequisite_lesson_ids=["lesson.c2.u3.combinations_and_blockers"],
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="The Mathematics of Position Expansion",
            step_type="EXPLAIN",
            content_markdown=(
                "Why can't you open K5s or J8s from Under the Gun (UTG)?\n\n"
                "When you raise from UTG, five players remain behind you. The probability that at least one of those five players holds a premium hand (AA-TT, AK, AQ) is over 35%!\n\n"
                "When you raise from the Button (BTN), only two players remain behind (the blinds). The probability that either of them holds a premium hand drops below 12%."
            ),
            key_takeaway="Fewer players behind means a drastically lower probability someone wakes up with a monster hand.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="Side-by-Side: UTG 15% vs BTN 43%",
            step_type="INTERACT",
            component_type="range_position_comparison",
            component_props={"pos1": "UTG", "pos2": "BTN", "interactive": True},
            content_markdown=(
                "Observe the two ranges using either the **Side-by-Side** dual grids or the **Difference Overlay**:\n\n"
                "- **UTG Range (~15%)**: Linear and concentrated. Contains 204 combinations (77+, ATs+, KJs+, QJs, AJo+, KQo).\n"
                "- **BTN Range (~43%)**: Expansive and polarized. Adds 370 combinations (+28%), including all pairs (22-66), suited connectors (87s, 65s), suited gappers, and offsuit broadways."
            ),
            key_takeaway="Button opens nearly triple the number of hands (+370 combinations) compared to Under the Gun.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Knowledge Check: Positional Range Width",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "Why is the Button opening range wider than the UTG opening range?",
                "options": [
                    "Fewer players left to act behind and guaranteed postflop position",
                    "The Button is dealt three cards instead of two",
                    "The rules force the Button to raise every hand",
                    "Blinds are not allowed to call Button raises",
                ],
                "correct_index": 0,
                "explanation": "Correct! The Button faces only 2 players and is guaranteed to act last on all postflop streets.",
                "remediation": "Positional advantage and fewer opponents behind allow wider hand selection.",
            },
            content_markdown="Verify positional opening logic.",
            key_takeaway="Fewer opponents + guaranteed position = wider opening range.",
        ),
        InteractiveLessonStep(
            step_number=4,
            title="Recap: Positional Ranges",
            step_type="RECAP",
            component_type="lesson_completion_summary",
            component_props={
                "xpEarned": 20,
                "masteryKey": "ranges.positional_expansion",
                "conceptsLearned": [
                    "Probability of opponents holding monsters decreases with fewer players behind",
                    "UTG opens ~15% linear hands; BTN opens ~43% diverse hands",
                    "Never open loose speculative hands from early position",
                ],
            },
            content_markdown="You have mastered the rationale behind positional opening ranges!",
            key_takeaway="Always adjust your opening range strictly by your position.",
        ),
    ],
)

LESSON_C2_U5_CHARTS = CourseLesson(
    id="lesson.c2.u5.range_charts_and_frequencies",
    path_id="path.foundations",
    chapter_id="chap_2_ranges",
    unit_id="unit_2_5_reading_charts",
    title="Reading Range Charts & Frequencies",
    summary="Understand pure vs mixed strategies, frequency gradients, and conceptual vs validated solver references.",
    skill_id="ranges.frequencies",
    difficulty_level="FOUNDATIONAL",
    estimated_minutes=5,
    prerequisite_lesson_ids=["lesson.c2.u4.positional_expansion"],
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="Pure Actions vs Mixed Strategies",
            step_type="EXPLAIN",
            component_type="range_frequency_visualizer",
            component_props={"hand": "A5s", "raiseFreq": 0.60, "callFreq": 0.40},
            content_markdown=(
                "In modern poker, actions are not always binary (100% or 0%):\n\n"
                "- **Pure Action**: A hand is played the exact same way 100% of the time (e.g. AA always raises 100%).\n"
                "- **Mixed Strategy**: A hand mixes between multiple actions at equilibrium (e.g. A5s raises 60% and calls 40%).\n\n"
                "Mixed strategies make your play unexploitable by preventing opponents from knowing your exact holdings."
            ),
            key_takeaway="A mixed strategy takes different actions with the same hand at precise mathematical frequencies.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="Conceptual Guides vs Validated Solvers",
            step_type="EXPLAIN",
            content_markdown=(
                "At Poker Lab, we maintain strict scientific integrity:\n\n"
                "- **Conceptual Guides**: Illustrative starting-point charts that teach principles (such as standard opening guidelines).\n"
                "- **Validated Solvers**: True Nash equilibrium calculations solved using Counterfactual Regret Minimization (CFR) with zero exploitability.\n\n"
                "We never label an illustrative chart as a 'GTO Solver Solution' without an authentic solver artifact!"
            ),
            key_takeaway="Understand the difference between pedagogical heuristics and mathematically verified solver solutions.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Knowledge Check: Mixed Strategies",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "What is a 'mixed strategy' in game theory and poker?",
                "options": [
                    "Splitting action between two or more choices at specific frequencies",
                    "Betting random amounts with no logic",
                    "Changing your seat at the table every orbit",
                    "Mixing cash game rules with tournament rules",
                ],
                "correct_index": 0,
                "explanation": "Correct! A mixed strategy takes different actions with the same hand at specific percentage frequencies.",
                "remediation": "Mixed strategies balance actions so an opponent cannot exploit predictable frequencies.",
            },
            content_markdown="Verify frequency understanding.",
            key_takeaway="Mixed strategies randomize between actions at equilibrium frequencies.",
        ),
        InteractiveLessonStep(
            step_number=4,
            title="Recap: Reading Range Charts",
            step_type="RECAP",
            component_type="lesson_completion_summary",
            component_props={
                "xpEarned": 20,
                "masteryKey": "ranges.frequencies",
                "conceptsLearned": [
                    "Pure actions (100%) vs Mixed strategies (frequencies)",
                    "Frequency gradients on range charts",
                    "Scientific distinction between heuristics and solver equilibria",
                ],
            },
            content_markdown="Outstanding! You are ready for the Chapter 2 Challenge.",
            key_takeaway="You have completed all units in Chapter 2.",
        ),
    ],
)

LESSON_C2_CHALLENGE = CourseLesson(
    id="lesson.c2.challenge",
    path_id="path.foundations",
    chapter_id="chap_2_ranges",
    unit_id="unit_2_5_reading_charts",
    title="Chapter 2 Challenge: Range Master",
    summary="Comprehensive checkpoint challenge testing matrix navigation, combination counting, notation, and positional ranges.",
    skill_id="checkpoint.chapter_2",
    difficulty_level="FOUNDATIONAL",
    estimated_minutes=6,
    prerequisite_lesson_ids=["lesson.c2.u5.range_charts_and_frequencies"],
    is_unit_challenge=True,
    is_chapter_checkpoint=True,
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="Chapter 2 Checkpoint Challenge",
            step_type="EXPLAIN",
            content_markdown=(
                "Welcome to the **Chapter 2 Checkpoint Challenge**!\n\n"
                "Prove your mastery of poker ranges:\n"
                "1. Decode range matrix notation (Pairs, Suited, Offsuit)\n"
                "2. Calculate exact combinations for pairs, suited, and offsuit hands\n"
                "3. Apply card removal and blocker effects\n"
                "4. Compare tight early position vs wide late position ranges\n\n"
                "Score 100% to earn the **Range Master** certification badge!"
            ),
            key_takeaway="Demonstrate complete range mastery to unlock Chapter 3.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="Challenge 1: Range Notation",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "What does the notation 'AJs' represent?",
                "options": [
                    "Ace-Jack Suited (both cards share the same suit)",
                    "Ace-Jack Offsuit (cards have different suits)",
                    "Pocket Aces and Pocket Jacks",
                    "Ace-Jack Small Blind",
                ],
                "correct_index": 0,
                "explanation": "Correct! The 's' suffix indicates suited cards (e.g. A♠ J♠).",
                "remediation": "'s' = Suited, 'o' = Offsuit.",
            },
            content_markdown="Notation check.",
            key_takeaway="'s' means suited.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Challenge 2: Combos Arithmetic",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "How many combinations make up any pocket pair (such as JJ)?",
                "options": [
                    "6 combinations",
                    "4 combinations",
                    "12 combinations",
                    "16 combinations",
                ],
                "correct_index": 0,
                "explanation": "Correct! Every pocket pair consists of exactly 6 unique suit combinations.",
                "remediation": "Pocket pairs always have 6 combinations.",
            },
            content_markdown="Combo math check.",
            key_takeaway="Pocket pairs have 6 combos.",
        ),
        InteractiveLessonStep(
            step_number=4,
            title="Challenge 3: Positional Expansion",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "Which player opens the widest range of hands preflop in a standard 6-max game?",
                "options": [
                    "The Button (BTN)",
                    "Under the Gun (UTG)",
                    "The Small Blind (SB)",
                    "The Hijack (HJ)",
                ],
                "correct_index": 0,
                "explanation": "Correct! The Button opens ~43% of hands, wider than any other position.",
                "remediation": "The Button always opens the widest range.",
            },
            content_markdown="Positional range check.",
            key_takeaway="Button opens the widest range.",
        ),
        InteractiveLessonStep(
            step_number=5,
            title="Chapter 2 Complete!",
            step_type="COMMIT",
            component_type="chapter_checkpoint",
            component_props={
                "chapterNumber": 2,
                "chapterTitle": "Understanding Ranges",
                "badgeName": "Range Master",
                "xpEarned": 60,
                "nextChapterId": "chap_3_math",
            },
            content_markdown=(
                "### 🏆 Chapter 2 Mastered!\n\n"
                "Outstanding work! You have mastered the foundational theory of Texas Hold'em and Range Architecture.\n\n"
                "You are now fully prepared for **Chapter 3: The Mathematics of Decisions** (Pot Odds, Outs, Equity, and EV)."
            ),
            key_takeaway="Chapter 2 Complete! You have achieved Range Mastery.",
        ),
    ],
)


# ============================================================================
# CHAPTER 3 LESSONS — POKER MATHEMATICS
# ============================================================================

LESSON_C3_U1_POT_ODDS = CourseLesson(
    id="lesson.c3.u1.pot_odds_equity",
    path_id="path.foundations",
    chapter_id="chap_3_math",
    unit_id="unit_3_1_pot_odds_equity",
    title="Pot Odds & Required Equity",
    summary="Calculate the exact ratio of bet to pot to determine the minimum winning percentage required to call.",
    skill_id="math.pot_odds",
    difficulty_level="FOUNDATIONAL",
    estimated_minutes=8,
    prerequisite_lesson_ids=["lesson.c2.challenge"],
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="The Pot Odds Formula",
            step_type="EXPLAIN",
            component_type="pot_odds",
            component_props={"pot": 80, "bet": 20, "interactive": True},
            content_markdown=(
                "In poker, every call is an investment. Pot odds express the relationship between the size of the call you must make and the total size of the pot you stand to win:\n\n"
                "> **Formula: Pot Odds (Required Equity)**\n\n"
                "> **Required Equity (%)** = $\\frac{\\text{Call Amount}}{\\text{Current Pot} + \\text{Opponent Bet} + \\text{Your Call}}$\n\n"
                "**Step-by-step example:**\n"
                "- The pot has **$80** in it.\n"
                "- Your opponent bets **$20**.\n"
                "- To call, you must invest **$20**.\n"
                "- Total pot after your call: $80 (pot) + $20 (bet) + $20 (call) = **$120**.\n"
                "- Required Equity: $\\frac{20}{120} = 0.167$ = **16.7%**.\n\n"
                "If your hand has more than **16.7% equity** (chance of winning), calling is immediately profitable (+EV)!"
            ),
            key_takeaway="Required Equity = Call ÷ (Current Pot + Bet + Call).",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="Interactive Pot Odds Explorer",
            step_type="INTERACT",
            component_type="pot_odds",
            component_props={"pot": 100, "bet": 50, "interactive": True},
            content_markdown=(
                "Use the interactive calculator above to see how different bet sizes alter your required equity:\n\n"
                "- **Half-Pot Bet** ($50 into $100 pot): You call $50 to win $200 total $\\rightarrow$ **25.0% equity needed**.\n"
                "- **Full-Pot Bet** ($100 into $100 pot): You call $100 to win $300 total $\\rightarrow$ **33.3% equity needed**.\n"
                "- **Two-Thirds Pot Bet** ($66 into $100 pot): You call $66 to win $232 total $\\rightarrow$ **28.4% equity needed**.\n\n"
                "Notice that larger bets demand higher winning percentages to justify calling."
            ),
            key_takeaway="A half-pot bet always requires 25% equity; a full-pot bet always requires 33.3% equity.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Knowledge Check: Pot Odds Calculation",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "The pot is $60. Your opponent bets $30. What percentage equity do you need to call profitably?",
                "options": ["25%", "33.3%", "50%", "20%"],
                "correct_index": 0,
                "explanation": "Correct! Call ($30) ÷ Total Pot ($60 initial + $30 bet + $30 call = $120) = 30 / 120 = 25.0%.",
                "remediation": "Remember the formula: Call ÷ (Pot + Bet + Call) = 30 ÷ (60 + 30 + 30) = 30 ÷ 120 = 0.25 (25%).",
            },
            content_markdown="Calculate the required equity based on the bet-to-pot ratio.",
            key_takeaway="Always divide your call by the final total pot size.",
        ),
        InteractiveLessonStep(
            step_number=4,
            title="Applying Pot Odds: Call vs Fold Decisions",
            step_type="APPLY",
            component_type="pot_odds",
            component_props={"pot": 150, "bet": 50, "interactive": False},
            content_markdown=(
                "Now we combine **pot odds** with your **hand equity** to make optimal decisions:\n\n"
                "> **The Golden Decision Rule:**\n"
                "> - **Hand Equity > Required Equity** $\\rightarrow$ **CALL** (Profitable long-term)\n"
                "> - **Hand Equity < Required Equity** $\\rightarrow$ **FOLD** (Losing long-term)\n\n"
                "**Worked Scenario:**\n"
                "- Flop pot is $150. Villain bets $50.\n"
                "- Total pot after call = $150 + $50 + $50 = $250. Pot odds = $50 / $250 = **20%**.\n"
                "- You hold a four-card flush draw, which has **~35% equity** to complete by the river.\n"
                "- Since **35% > 20%**, calling is clearly profitable! You win $250 on average 35% of the time, earning more than your $50 investment."
            ),
            key_takeaway="Call when hand equity exceeds required pot odds; fold when hand equity falls short.",
        ),
        InteractiveLessonStep(
            step_number=5,
            title="Recap: Pot Odds & Equity Foundations",
            step_type="RECAP",
            component_type="lesson_completion_summary",
            component_props={
                "xpEarned": 25,
                "masteryKey": "math.pot_odds",
                "conceptsLearned": [
                    "Pot Odds = Call ÷ Total Pot After Call",
                    "Half-pot bet requires 25% equity",
                    "Full-pot bet requires 33.3% equity",
                    "Compare hand equity directly against required pot odds",
                ],
            },
            content_markdown="Congratulations! You have mastered the mathematical bedrock of poker decisions.",
            key_takeaway="Pot odds eliminate guesswork by establishing an exact mathematical threshold for calling.",
        ),
    ],
)

LESSON_C3_U2_OUTS_EV = CourseLesson(
    id="lesson.c3.u2.outs_and_expected_value",
    path_id="path.foundations",
    chapter_id="chap_3_math",
    unit_id="unit_3_2_outs_ev",
    title="Outs & The Rule of 2 & 4",
    summary="Estimate drawing equity in seconds at the table by counting outs and applying the Rule of 2 & 4.",
    skill_id="math.outs_and_ev",
    difficulty_level="FOUNDATIONAL",
    estimated_minutes=8,
    prerequisite_lesson_ids=["lesson.c3.u1.pot_odds_equity"],
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="Counting Drawing Outs",
            step_type="EXPLAIN",
            component_type="outs_equity",
            component_props={"outs": 9, "drawType": "Flush Draw", "interactive": True},
            content_markdown=(
                "An **out** is any unseen card remaining in the deck that will improve your hand to a winning holding if dealt.\n\n"
                "Standard out counts every poker player must memorize:\n\n"
                "| Draw Type | Example | Total Outs | Key Cards |\n"
                "| :--- | :--- | :--- | :--- |\n"
                "| **Flush Draw** | Four cards to a suit | **9 outs** | 13 cards of suit - 4 known = 9 remaining |\n"
                "| **Open-Ended Straight Draw (OESD)** | 8-7 on 6-5-2 | **8 outs** | 4 nines + 4 fours = 8 remaining |\n"
                "| **Gutshot (Inside Straight)** | 9-7 on 6-5-2 | **4 outs** | 4 eights needed |\n"
                "| **Two Overcards** | A-K on 9-5-2 | **6 outs** | 3 aces + 3 kings |\n"
                "| **Set to Full House/Quads** | 3-3 on 9-3-2 | **7 outs on turn** | 1 three + 3 nines + 3 twos |"
            ),
            key_takeaway="An out is any card remaining in the deck that improves your holding to the winner.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="The Rule of 2 & 4: Instant Equity Estimation",
            step_type="EXPLAIN",
            content_markdown=(
                "You don't need complex probability software at the table. **The Rule of 2 & 4** gives an instant, accurate approximation of your equity:\n\n"
                "> **The Rule of 4 (On the Flop - 2 cards to come):**\n"
                "> **Equity (%)** $\\approx$ **Outs** $\\times$ **4**\n"
                "> *Example:* A 9-out flush draw on the flop has $9 \\times 4 \\approx$ **36% equity** (Exact math: 35.0%).\n\n"
                "> **The Rule of 2 (On the Turn - 1 card to come):**\n"
                "> **Equity (%)** $\\approx$ **Outs** $\\times$ **2**\n"
                "> *Example:* A 9-out flush draw on the turn has $9 \\times 2 \\approx$ **18% equity** (Exact math: 19.1%).\n\n"
                "This formula is accurate within 1-2% for all standard drawing situations."
            ),
            key_takeaway="On the flop multiply outs by 4; on the turn multiply outs by 2.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Knowledge Check: Open-Ended Straight Draw",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "You hold 8♠ 7♠ on a flop of 6♦ 5♣ K♥ (Open-Ended Straight Draw with 8 outs). Using the Rule of 4, what is your approximate equity to hit your straight by the river?",
                "options": ["~32%", "~16%", "~8%", "~48%"],
                "correct_index": 0,
                "explanation": "Correct! 8 outs × 4 = ~32% equity to make a straight by the river.",
                "remediation": "On the flop with two cards to come, multiply your outs by 4: 8 outs × 4 = 32%.",
            },
            content_markdown="Calculate drawing equity on the flop using the Rule of 4.",
            key_takeaway="8 outs on the flop gives approximately 32% equity by the river.",
        ),
        InteractiveLessonStep(
            step_number=4,
            title="Combo Draws: Massive Drawing Power",
            step_type="APPLY",
            component_type="outs_equity",
            component_props={
                "outs": 15,
                "drawType": "Combo Draw (Flush + Straight)",
                "interactive": True,
            },
            content_markdown=(
                "When draws combine, their equity skyrockets! A **combo draw** contains both a flush draw and a straight draw:\n\n"
                "- **9 flush outs + 6 straight outs** = **15 total outs**.\n"
                "- On the flop: $15 \\times 4 \\approx$ **54% equity** (actual exact equity is ~54.1%).\n\n"
                "Holding a monster combo draw means you are actually a **mathematical favorite** against a made top pair! This is why elite players play combo draws aggressively with raises and re-raises."
            ),
            key_takeaway="A 15-out combo draw has over 54% equity and is favored over top pair.",
        ),
        InteractiveLessonStep(
            step_number=5,
            title="Recap: Outs & Equity Estimation",
            step_type="RECAP",
            component_type="lesson_completion_summary",
            component_props={
                "xpEarned": 25,
                "masteryKey": "math.outs_and_ev",
                "conceptsLearned": [
                    "Flush Draw = 9 outs",
                    "Open-Ended Straight Draw = 8 outs",
                    "Gutshot Draw = 4 outs",
                    "Flop: Outs × 4 ≈ Equity %",
                    "Turn: Outs × 2 ≈ Equity %",
                ],
            },
            content_markdown="Excellent! You can now calculate drawing equity in seconds at the table.",
            key_takeaway="Outs multiplied by 4 on the flop or 2 on the turn provide an immediate compass for every drawing decision.",
        ),
    ],
)

LESSON_C3_U3_IMPLIED_ODDS = CourseLesson(
    id="lesson.c3.u3.implied_odds_and_sizing",
    path_id="path.foundations",
    chapter_id="chap_3_math",
    unit_id="unit_3_3_implied_odds_sizing",
    title="Implied Odds, Expected Value & Bet Sizing",
    summary="Incorporate future betting action through implied odds, compute Expected Value (EV), and understand bet sizing mechanics.",
    skill_id="math.implied_odds",
    difficulty_level="FOUNDATIONAL",
    estimated_minutes=9,
    prerequisite_lesson_ids=["lesson.c3.u2.outs_and_expected_value"],
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="Expected Value (EV): The Sovereign Measure",
            step_type="EXPLAIN",
            content_markdown=(
                "In poker, you cannot judge a decision based on whether you won or lost a single hand. Short-term outcomes are influenced by randomness (variance).\n\n"
                "**Expected Value (EV)** is the average amount of money a decision will win or lose if repeated 10,000 times:\n\n"
                "> **Formula: Expected Value (EV)**\n\n"
                "> **EV** = $(P_{\\text{Win}} \\times \\text{Amount Won}) - (P_{\\text{Lose}} \\times \\text{Amount Lost})$\n\n"
                "- If **EV > 0**, the play is **+EV** (profitable long-term).\n"
                "- If **EV < 0**, the play is **-EV** (unprofitable long-term).\n"
                "- If **EV = 0**, the play is neutral (indifferent).\n\n"
                "Elite poker strategy consists exclusively of executing +EV decisions and avoiding -EV traps."
            ),
            key_takeaway="Judge decisions strictly by long-term Expected Value (+EV), never by short-term variance.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="Implied Odds: Looking Beyond the Current Pot",
            step_type="EXPLAIN",
            content_markdown=(
                "**Pot odds** only consider the chips already in the pot. But what if your opponent has a deep stack and will pay you off with even more chips on future streets when you hit your draw?\n\n"
                "**Implied odds** account for the additional chips you expect to win on future streets after hitting your hand:\n\n"
                "> **Key Conditions for Strong Implied Odds:**\n"
                "> 1. **Deep Effective Stacks**: Both you and your opponent must have plenty of chips behind (e.g. 100bb+).\n"
                "> 2. **Hidden Hand Strength**: Your completed hand is disguised (e.g., hitting a set with a small pair or a gutshot straight).\n"
                "> 3. **Opponent Willingness to Call**: Opponent holds a strong hand they cannot easily fold (e.g. top pair or an overpair).\n\n"
                "When implied odds are high, you can profitably call bets even when immediate pot odds are slightly insufficient!"
            ),
            key_takeaway="Implied odds justify calling with draws when deep stacks ensure additional payoffs on future streets.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Reverse Implied Odds: The Hidden Trap",
            step_type="EXPLAIN",
            content_markdown=(
                "The opposite of implied odds is **Reverse Implied Odds**: situations where hitting your card wins you only a tiny pot, but when opponent hits better you lose your entire stack!\n\n"
                "> **Examples of Reverse Implied Odds:**\n"
                "> - Chasing a non-nut flush with low cards (e.g. 5♠ 4♠ on a 3-spade board where opponent holds A♠ K♠).\n"
                "> - Hitting top pair with a weak kicker (e.g. K♦ 3♦ on K♠ 8♣ 2♥: when called by better Kings like AK or KQ, you lose heavily).\n\n"
                "Always be wary of chasing draws that can leave you with the second-best hand."
            ),
            key_takeaway="Reverse implied odds occur when hitting your draw still leaves you vulnerable to a higher hand.",
        ),
        InteractiveLessonStep(
            step_number=4,
            title="Bet Sizing Geometry: Sizing for Purpose",
            step_type="APPLY",
            component_type="pot_odds",
            component_props={"pot": 100, "bet": 33, "interactive": True},
            content_markdown=(
                "Modern bet sizing is always framed in **percentage of the pot**, because pot size dictates the pot odds your opponent receives:\n\n"
                "| Sizing Category | Typical Size | Opponent Pot Odds | Strategic Purpose |\n"
                "| :--- | :--- | :--- | :--- |\n"
                "| **Small (Range Bet)** | 25% – 33% Pot | 16.7% – 20% | High-frequency betting on dry boards where your entire range is ahead. |\n"
                "| **Medium (Standard)** | 50% – 66% Pot | 25% – 28.5% | Balanced value/bluff betting on standard boards. |\n"
                "| **Large (Polarized)** | 75% – 100% Pot | 30% – 33.3% | Heavy value with monsters while charging draws maximum price. |\n"
                "| **Overbet** | 125% – 150%+ Pot | 35% – 38%+ | Nut-advantage boards to apply maximum pressure on opponent bluff-catchers. |"
            ),
            key_takeaway="Bet sizing dictates the pot odds and minimum defense requirements you impose on your opponent.",
        ),
        InteractiveLessonStep(
            step_number=5,
            title="Knowledge Check: Implied Odds Decision",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "On the turn, the pot is $100 and your opponent bets $100 (full pot, requiring 33% equity). Your flush draw has only 18% direct equity to hit on the river. Both players have $500 remaining behind. Why might calling still be mathematically profitable?",
                "options": [
                    "Because of implied odds: winning an extra $200+ from villain's remaining $500 stack on the river compensates for the shortfall in immediate odds.",
                    "Because 18% is close enough to 33% to break even.",
                    "Because flush draws always win on the river.",
                    "Because your opponent is guaranteed to check the river.",
                ],
                "correct_index": 0,
                "explanation": "Correct! With deep stacks ($500 behind), hitting your flush on the river will win enough additional chips to easily offset the immediate pot odds deficit.",
                "remediation": "When deep stacks remain behind, the future chips won after hitting your draw provide the necessary implied odds.",
            },
            content_markdown="Evaluate whether implied odds justify an immediate call.",
            key_takeaway="Deep remaining stacks allow implied odds to bridge the gap between equity and pot odds.",
        ),
        InteractiveLessonStep(
            step_number=6,
            title="Recap: Implied Odds & Decision Arithmetic",
            step_type="RECAP",
            component_type="lesson_completion_summary",
            component_props={
                "xpEarned": 25,
                "masteryKey": "math.implied_odds",
                "conceptsLearned": [
                    "EV = (P(Win) × Win) - (P(Lose) × Lose)",
                    "Implied odds require deep effective stacks and disguised hand strength",
                    "Avoid reverse implied odds with easily dominated holdings",
                    "Bet sizes are calibrated as percentages of the pot",
                ],
            },
            content_markdown="Great job! You have conquered the core mathematics that govern professional poker strategy.",
            key_takeaway="Expected value and implied odds form the bridge between raw card probabilities and strategic execution.",
        ),
    ],
)

LESSON_C3_CHECKPOINT = CourseLesson(
    id="lesson.c3.checkpoint",
    path_id="path.foundations",
    chapter_id="chap_3_math",
    unit_id="unit_3_3_implied_odds_sizing",
    title="Chapter 3 Challenge: Decision Mathematics",
    summary="Validate mastery of pot odds, drawing outs, Rule of 2 & 4, and Expected Value calculations.",
    skill_id="checkpoint.chapter_3",
    difficulty_level="FOUNDATIONAL",
    estimated_minutes=6,
    prerequisite_lesson_ids=["lesson.c3.u3.implied_odds_and_sizing"],
    is_unit_challenge=True,
    is_chapter_checkpoint=True,
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="Mathematics Synthesis Checkpoint",
            step_type="EXPLAIN",
            content_markdown=(
                "### 📐 Chapter 3 Capstone Evaluation\n\n"
                "Before advancing to preflop strategy, prove your command of decision mathematics:\n\n"
                "1. **Pot Odds**: Can you calculate required equity instantaneously?\n"
                "2. **Outs & Rule of 4**: Can you estimate flop-to-river equity under time pressure?\n"
                "3. **EV Reasoning**: Can you identify when a play is +EV versus -EV?\n\n"
                "Answer the validation questions below to unlock Chapter 4: Preflop Strategy."
            ),
            key_takeaway="Mathematics is your objective compass in every Texas Hold'em decision.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="Capstone Problem: The Flop Decision",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "The pot is $80. Villain bets $40. You hold 9♥ 8♥ on a flop of 7♥ 6♠ 2♦ (OESD with 8 outs). What are your pot odds, what is your approximate equity using the Rule of 4, and what is the correct play?",
                "options": [
                    "Pot odds require 25% equity; your equity is ~32%; CALL (+EV).",
                    "Pot odds require 33% equity; your equity is ~16%; FOLD (-EV).",
                    "Pot odds require 50% equity; your equity is ~32%; FOLD (-EV).",
                    "Pot odds require 20% equity; your equity is ~8%; CALL (+EV).",
                ],
                "correct_index": 0,
                "explanation": "Correct! Call is $40 ÷ ($80 + $40 + $40 = $160) = 25% required equity. 8 outs × 4 = ~32% equity. Since 32% > 25%, calling is +EV!",
                "remediation": "Pot odds: 40 / 160 = 25%. Rule of 4: 8 outs × 4 = 32%. Since 32% > 25%, the call is mathematically profitable (+EV).",
            },
            content_markdown="Solve this complete worked pot odds and equity problem.",
            key_takeaway="When hand equity (32%) exceeds pot odds (25%), calling is +EV.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Chapter 3 Complete: Certified Poker Mathematician!",
            step_type="COMMIT",
            component_type="chapter_checkpoint",
            component_props={
                "chapterNumber": 3,
                "chapterTitle": "The Mathematics of Decisions",
                "badgeName": "Poker Mathematician",
                "xpEarned": 50,
                "nextChapterId": "chap_4_preflop",
            },
            content_markdown=(
                "### 🎓 Chapter 3 Mastered!\n\n"
                "You have conquered the mathematical foundation of Texas Hold'em:\n"
                "- **Pot Odds & Required Equity**\n"
                "- **Outs & Fast Equity Estimation (Rule of 2 & 4)**\n"
                "- **Expected Value (+EV / -EV)**\n"
                "- **Implied Odds & Pot-Relative Bet Sizing**\n\n"
                "You are now fully equipped to study **Chapter 4: Preflop Strategy**!"
            ),
            key_takeaway="Chapter 3 Certified! Ready for Preflop Strategy.",
        ),
    ],
)


# ============================================================================
# CHAPTER 4 LESSONS — PREFLOP STRATEGY
# ============================================================================

LESSON_C4_U1_POSITION = CourseLesson(
    id="lesson.preflop.position",
    path_id="path.foundations",
    chapter_id="chap_4_preflop",
    unit_id="unit_4_1_rfi_strategy",
    title="The Power of Position: Acting Last Postflop",
    summary="Why playing in position (IP) dramatically increases profitability and allows wider preflop opening.",
    skill_id="preflop.fundamentals",
    difficulty_level="FOUNDATIONAL",
    estimated_minutes=8,
    prerequisite_lesson_ids=[],
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="Informational Advantage",
            step_type="EXPLAIN",
            component_type="poker_table",
            component_props={"activeSeat": "BTN", "highlightPositions": ["UTG", "BTN"]},
            content_markdown=(
                "In Texas Hold'em, position is destiny. The player who acts last on every postflop street possesses an insurmountable **informational advantage**.\n\n"
                "When you are **In Position (IP)**:\n"
                "- You observe whether your opponent checks or bets before you make any decision.\n"
                "- When opponent checks, you can bet to claim the pot or check back to take a free card.\n"
                "- When opponent bets, you know the exact price required to continue.\n\n"
                "When you are **Out of Position (OOP)**, you must act blind into the darkness on every single betting round."
            ),
            key_takeaway="Acting last postflop provides maximum information and superior control over pot size.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="Positional Expansion: From UTG to the Button",
            step_type="INTERACT",
            component_type="poker_table",
            component_props={
                "activeSeat": "BTN",
                "highlightPositions": ["UTG", "HJ", "CO", "BTN", "SB", "BB"],
            },
            content_markdown=(
                "Because of position and the number of players left to act behind you, opening ranges expand systematically as action moves around the table:\n\n"
                "- **UTG (Under the Gun)**: ~15% of hands (tight, linear, high-card strength).\n"
                "- **HJ (Hijack)**: ~20% of hands.\n"
                "- **CO (Cutoff)**: ~28% of hands.\n"
                "- **BTN (Button)**: ~43% of hands (wide, speculative, aggressive).\n\n"
                "Why can the Button open nearly **3x more hands** than UTG? Because UTG must survive 5 players behind them, whereas the Button only has 2 players left to act!"
            ),
            key_takeaway="Opening ranges expand as position moves closer to the Button.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Equity Realization (R-Factor)",
            step_type="EXPLAIN",
            content_markdown=(
                "Having 30% raw equity does not mean you will win 30% of the pot if you are forced to fold before showdown!\n\n"
                "**Equity Realization (R-Factor)** measures how much of your raw hand equity you actually capture:\n\n"
                "- **In Position (IP)**: Realizes **> 100%** of raw equity. You can bluff effectively, see cheap showdowns, and extract maximum value.\n"
                "- **Out of Position (OOP)**: Realizes **< 80%** of raw equity. You are frequently bluffed off the best hand and cannot control pot size.\n\n"
                "This explains why mediocre hands that lose money OOP become wildly profitable when played on the Button."
            ),
            key_takeaway="Playing in position enables you to realize significantly more equity than your raw cards possess.",
        ),
        InteractiveLessonStep(
            step_number=4,
            title="Knowledge Check: Positional Value",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "Why can the Button open approximately 43% of hands, while Under The Gun (UTG) can only open approximately 15%?",
                "options": [
                    "Guaranteed position postflop and only two players left to contest the blinds.",
                    "The Button is dealt better cards on average.",
                    "The Button is allowed to make smaller bets than UTG.",
                    "UTG is forced to post a mandatory blind.",
                ],
                "correct_index": 0,
                "explanation": "Correct! The Button has guaranteed position on every postflop street and only needs to fold out two players (SB and BB) to win the pot preflop.",
                "remediation": "Fewer players behind drastically reduces the chance someone holds a monster, and guaranteed postflop position maximizes equity realization.",
            },
            content_markdown="Test your grasp of positional leverage.",
            key_takeaway="Position and fewer opponents behind allow late position opening ranges to expand dramatically.",
        ),
        InteractiveLessonStep(
            step_number=5,
            title="Recap: Positional Power",
            step_type="RECAP",
            component_type="lesson_completion_summary",
            component_props={
                "xpEarned": 25,
                "masteryKey": "preflop.fundamentals",
                "conceptsLearned": [
                    "In Position (IP) players act last on every postflop street",
                    "Opening ranges expand from UTG (~15%) to BTN (~43%)",
                    "Equity realization is significantly higher in position",
                ],
            },
            content_markdown="Great work! You now understand the strategic engine behind positional poker.",
            key_takeaway="Never play hands from early position that require late position advantage to be profitable.",
        ),
    ],
    linked_scenario_id="pack_cash_6max_100bb_btn_rfi_AsKs",
    transfer_scenario_id=None,
    transfer_availability="UNAVAILABLE_INSUFFICIENT_VALIDATED_CONTENT",
    transfer_rationale="Held-out multi-position preflop opening trees (UTG/HJ/CO) are pending solver generation.",
)

LESSON_C4_U1_BTN_RFI = CourseLesson(
    id="lesson.preflop.btn_rfi",
    path_id="path.foundations",
    chapter_id="chap_4_preflop",
    unit_id="unit_4_1_rfi_strategy",
    title="Raise-First-In (RFI) Ranges & Sizing",
    summary="Construct equilibrium opening ranges by position, avoid open-limping, and choose optimal preflop bet sizing.",
    skill_id="preflop.rfi.late",
    difficulty_level="FOUNDATIONAL",
    estimated_minutes=9,
    prerequisite_lesson_ids=["lesson.preflop.position"],
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="Standard 100bb BTN Opening Range (Illustrative Benchmark)",
            step_type="EXPLAIN",
            component_type="range_matrix_explorer",
            component_props={
                "highlightedHands": [
                    "AA",
                    "KK",
                    "QQ",
                    "JJ",
                    "TT",
                    "99",
                    "88",
                    "77",
                    "66",
                    "55",
                    "44",
                    "33",
                    "22",
                    "AKs",
                    "AQs",
                    "AJs",
                    "ATs",
                    "A9s",
                    "A8s",
                    "A7s",
                    "A6s",
                    "A5s",
                    "A4s",
                    "A3s",
                    "A2s",
                    "AKo",
                    "AQo",
                    "AJo",
                    "ATo",
                    "A9o",
                    "A8o",
                    "A7o",
                    "A6o",
                    "A5o",
                    "KQs",
                    "KJs",
                    "KTs",
                    "K9s",
                    "K8s",
                    "K7s",
                    "K6s",
                    "K5s",
                    "KQo",
                    "KJo",
                    "KTo",
                    "K9o",
                    "QJs",
                    "QTs",
                    "Q9s",
                    "Q8s",
                    "Q7s",
                    "Q6s",
                    "QJo",
                    "QTo",
                    "JTs",
                    "J9s",
                    "J8s",
                    "J7s",
                    "JTo",
                    "T9s",
                    "T8s",
                    "T7s",
                    "98s",
                    "97s",
                    "87s",
                    "86s",
                    "76s",
                    "65s",
                    "54s",
                ],
                "defaultSelectedHand": "AKs",
            },
            content_markdown=(
                "In standard 6-max 100bb cash games (0.5/1.0 blinds, 5% rake with 3bb cap, no ante), a recommended Button opening range covers approximately **43% of all starting hands** (574 combinations of 1,326 total):\n\n"
                "- **All 78 pocket pair combinations** (22 through AA).\n"
                "- **All suited Aces** (A2s–AKs) and most suited Kings/Queens.\n"
                "- **Suited connectors & gappers** down to 54s and 86s.\n"
                "- **High offsuit broadway cards** (A5o+, K9o+, QTo+, JTo).\n\n"
                "> **Provenance & Strategic Realism Note:**\n"
                "> This preflop chart is an **illustrative educational benchmark** derived from standard modern 6-max preflop literature and supplied as an input range for postflop simulations. It is not an unconstrained Pokeria engine full-game solve. At range boundary holdings (e.g., A5o, K9o, 54s), full equilibrium solvers execute mixed strategies (raising 20%–60% frequency). Here, holdings are presented in pure form for conceptual clarity."
            ),
            key_takeaway="The Button opens ~43% of hands in standard 6-max cash, anchored by pairs, suited aces, and connected holdings.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="The Cardinal Sin: Open-Limping",
            step_type="EXPLAIN",
            content_markdown=(
                "**Open-limping** is just calling the 1 BB big blind instead of raising when you are the first player to enter the pot.\n\n"
                "> **Why Open-Limping Is a Major Strategic Mistake:**\n"
                "> 1. **Zero Fold Equity**: You cannot win the pot preflop; you guarantee seeing a flop.\n"
                "> 2. **Surrenders Initiative**: You cannot credibly continuation-bet postflop.\n"
                "> 3. **Invites Multi-Way Disaster**: Other players get cheap odds to limp behind, drastically reducing your equity.\n"
                "> 4. **Caps Your Range**: Strong hands (AA, KK, AK) raise; limping announces your hand is mediocre.\n\n"
                "**Rule:** If a hand is worth playing, it is worth **raising**!"
            ),
            key_takeaway="Never open-limp. If your hand is playable, raise first in (RFI).",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Preflop Open Sizing: The Sweet Spot",
            step_type="APPLY",
            content_markdown=(
                "What is the optimal opening raise size in modern 100bb poker?\n\n"
                "- **Standard Modern Size**: **2.25bb to 2.5bb**.\n"
                "- **Min-Raise (2.0bb)**: Gives the Big Blind incredible 3.5:1 pot odds (needs only 22% equity), allowing them to defend nearly any two cards.\n"
                "- **Large Raise (3.0bb – 3.5bb)**: Risks too many chips. If opponent 3-bets, you lose 3.5bb instead of 2.5bb on your folds.\n\n"
                "**2.5bb** represents the gold-standard equilibrium: it denies cheap odds to the blinds while risking minimal chips against 3-bets."
            ),
            key_takeaway="2.25bb to 2.5bb is the optimal equilibrium open size in 100bb cash play.",
        ),
        InteractiveLessonStep(
            step_number=4,
            title="Knowledge Check: Open-Limping Error",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "Why is open-limping (calling 1 BB when folded to you) considered a major strategic error in modern poker?",
                "options": [
                    "It surrenders fold equity and initiative, caps your range, and invites multi-way pots.",
                    "It is against the official rules of Texas Hold'em.",
                    "It costs more chips than raising.",
                    "It automatically forces the Big Blind to fold.",
                ],
                "correct_index": 0,
                "explanation": "Correct! Open-limping gives up all fold equity, surrenders initiative, and allows players behind to see cheap flops or punish you with isolation raises.",
                "remediation": "Remember: when entering an unopened pot, always raise (RFI) or fold. Never limp.",
            },
            content_markdown="Validate your understanding of preflop opening mechanics.",
            key_takeaway="Open-raising captures initiative and fold equity; open-limping surrenders both.",
        ),
        InteractiveLessonStep(
            step_number=5,
            title="Recap: RFI Mastery",
            step_type="RECAP",
            component_type="lesson_completion_summary",
            component_props={
                "xpEarned": 25,
                "masteryKey": "preflop.rfi.late",
                "conceptsLearned": [
                    "BTN opens ~43% equilibrium range",
                    "Open-raising 2.25x - 2.5x is optimal",
                    "Never open-limp in unopened pots",
                    "Suited hands and pairs form the core of wide opening ranges",
                ],
            },
            content_markdown="Great work! You now understand how to construct solid opening ranges.",
            key_takeaway="Aggressive, disciplined preflop opening sets up every profitable postflop situation.",
        ),
    ],
    linked_scenario_id="pack_cash_6max_100bb_btn_rfi_AsKs",
    transfer_scenario_id=None,
    transfer_availability="UNAVAILABLE_INSUFFICIENT_VALIDATED_CONTENT",
    transfer_rationale="Alternative sizing variations (2.2bb / minraise) held-out charts are pending solver generation.",
)

LESSON_C4_U2_FACING_OPENS = CourseLesson(
    id="lesson.c4.u2.facing_raises_blind_defense",
    path_id="path.foundations",
    chapter_id="chap_4_preflop",
    unit_id="unit_4_2_three_betting",
    title="Facing Opens & Defending the Big Blind",
    summary="Learn when to flat-call in position, how the Big Blind discount pot odds work, and which hands to defend.",
    skill_id="preflop.defense",
    difficulty_level="INTERMEDIATE",
    estimated_minutes=8,
    prerequisite_lesson_ids=["lesson.preflop.btn_rfi"],
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="The Big Blind Discount: Pot Odds in Action",
            step_type="EXPLAIN",
            component_type="pot_odds",
            component_props={"pot": 40, "bet": 15, "interactive": True},
            content_markdown=(
                "The **Big Blind** is in a unique strategic position:\n\n"
                "- You have already invested **1.0 BB** into the pot.\n"
                "- When the Button opens to **2.5 BB**, you only have to call **1.5 BB** more.\n"
                "- The total pot after your call: 1.0 (BB) + 0.5 (SB) + 2.5 (BTN) + 1.5 (call) = **5.5 BB**.\n"
                "- Your pot odds: $\\frac{1.5}{5.5} = 0.272$ = **27.3% required equity**!\n\n"
                "Because of this huge discount, the Big Blind must defend a **wide range of holdings** (often 45-50% of hands vs a late position open)."
            ),
            key_takeaway="The Big Blind gets heavily discounted pot odds and must defend broadly.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="Big Blind Defense Selection (Illustrative 100bb Benchmark)",
            step_type="EXPLAIN",
            component_type="range_matrix_explorer",
            component_props={
                "highlightedHands": [
                    "K9s",
                    "K8s",
                    "Q9s",
                    "J8s",
                    "T7s",
                    "96s",
                    "85s",
                    "74s",
                    "KJo",
                    "QJo",
                    "JTo",
                    "T9o",
                    "98o",
                    "55",
                    "44",
                    "33",
                    "22",
                ],
                "defaultSelectedHand": "T9s",
            },
            content_markdown=(
                "In 6-max 100bb cash games (0.5/1.0 blinds, 5% rake with 3bb cap, no ante), facing a 2.5bb Button open:\n\n"
                "Not all cards that have 27.3% raw equity should be defended! You must distinguish between **high playability** and **reverse domination**:\n\n"
                "- **Great Defends**: Suited connectors (87s, 65s), suited gappers (T8s, 97s), small pocket pairs (22-55). These hands flop strong draws or sets that realize equity well.\n"
                "- **Terrible Traps (Folds)**: Weak offsuit hands like K5o, Q4o, J3o. While they have raw equity, they are dominated by villain's broadways, flop weak pairs, and lose massive pots when out of position.\n\n"
                "> **Educational Provenance Note:**\n"
                "> This defense selection is an **illustrative educational benchmark** derived from standard modern 6-max theory and input ranges. It represents a practical calling range rather than an unconstrained equilibrium solve. Solvers mix calls and 3-bets at high frequencies across border holdings."
            ),
            key_takeaway="Defend hands with strong playability (suited/connected); fold dominated offsuit junk.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Calling in Position (Flatting)",
            step_type="APPLY",
            content_markdown=(
                "When you are on the Button facing an open from Under the Gun (UTG):\n\n"
                "- **The Dilemma**: Flat-calling in position is appealing because you have position postflop.\n"
                "- **The Risk**: You invite the Small Blind and Big Blind to squeeze (3-bet) you out of the pot.\n"
                "- **Equilibrium Principle**: Modern solver play prefers either **3-betting or folding** from most positions, reserving flat-calling primarily for the Button with hands that play well multi-way (medium pocket pairs like 88-66, suited broadways like KQs, QJs)."
            ),
            key_takeaway="Flat-calling is most viable on the Button; earlier positions prefer 3-bet or fold.",
        ),
        InteractiveLessonStep(
            step_number=4,
            title="Knowledge Check: Big Blind Defense",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "You are in the Big Blind facing a 2.5bb Button open. Why can you profitably call with 7♠ 6♠, but should fold K♠ 4♦?",
                "options": [
                    "76s has superior postflop playability (straight and flush potential) and avoids severe kicker domination, whereas K4o is dominated and loses large pots OOP.",
                    "76s has higher raw high-card rank than K4o.",
                    "K4o is illegal to call with in the Big Blind.",
                    "Button always folds when the Big Blind calls.",
                ],
                "correct_index": 0,
                "explanation": "Correct! 76s flops draws and pairs that realize equity cleanly without reverse implied odds, while K4o is frequently dominated by better Kings and loses big pots when hitting top pair.",
                "remediation": "Suited connected cards have high realization and low domination risk; weak offsuit face cards suffer severe reverse implied odds.",
            },
            content_markdown="Test your grasp of Big Blind defense hand selection.",
            key_takeaway="Playability and domination risk matter more than raw high-card ranking when defending OOP.",
        ),
        InteractiveLessonStep(
            step_number=5,
            title="Recap: Facing Preflop Opens",
            step_type="RECAP",
            component_type="lesson_completion_summary",
            component_props={
                "xpEarned": 25,
                "masteryKey": "preflop.defense",
                "conceptsLearned": [
                    "BB gets discounted pot odds (needs ~27% equity vs 2.5x open)",
                    "Defend suited and connected holdings with high playability",
                    "Fold dominated offsuit trash (K5o, Q4o)",
                    "Flatting opens in position requires cautiousness against blind squeezes",
                ],
            },
            content_markdown="Excellent! You now know how to defend your blinds without leaking chips.",
            key_takeaway="Defend wide with high-playability hands; discard dominated junk.",
        ),
    ],
)

LESSON_C4_U2_3BET = CourseLesson(
    id="lesson.c4.u2.three_bet_strategy",
    path_id="path.foundations",
    chapter_id="chap_4_preflop",
    unit_id="unit_4_2_three_betting",
    title="3-Betting & 4-Betting Fundamentals",
    summary="Linear vs polarized 3-betting ranges, sizing IP vs OOP, and 4-bet shove thresholds.",
    skill_id="preflop.three_bet",
    difficulty_level="INTERMEDIATE",
    estimated_minutes=9,
    prerequisite_lesson_ids=["lesson.c4.u2.facing_raises_blind_defense"],
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="What Is a 3-Bet?",
            step_type="EXPLAIN",
            content_markdown=(
                "A **3-bet** is the third bet in the preflop sequence:\n\n"
                "1. **1st Bet**: The Big Blind (mandatory forced bet).\n"
                "2. **2nd Bet**: A player raises (the Open / RFI).\n"
                "3. **3rd Bet**: A player re-raises (the 3-bet).\n\n"
                "> **Why We 3-Bet:**\n"
                "> - **Value**: Build huge pots with premium holdings (AA, KK, QQ, AK).\n"
                "> - **Fold Equity**: Force the open-raiser to fold their wide speculative hands.\n"
                "> - **Initiative**: Seize control of the betting lead for the rest of the hand.\n"
                "> - **Equity Denial**: Prevent opponents behind you from entering the pot cheaply."
            ),
            key_takeaway="3-betting builds pots with premium hands, captures initiative, and denies equity to opponents.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="Linear vs Polarized 3-Bet Ranges",
            step_type="EXPLAIN",
            component_type="range_matrix_explorer",
            component_props={
                "highlightedHands": [
                    "AA",
                    "KK",
                    "QQ",
                    "JJ",
                    "TT",
                    "AKs",
                    "AKo",
                    "AQs",
                    "A5s",
                    "A4s",
                    "KTs",
                    "QJs",
                ],
                "defaultSelectedHand": "A5s",
            },
            content_markdown=(
                "There are two fundamental ways to construct a 3-betting range in 6-max 100bb cash play:\n\n"
                "- **Linear 3-Bet Range (Merged)**:\n"
                "  Composed purely of the top X% of hands (AA–99, AK, AQ, KQs). There are no pure bluffs. Used when facing tight early-position opens or against opponents who call 3-bets too often.\n\n"
                "- **Polarized 3-Bet Range**:\n"
                "  Composed of two distinct poles:\n"
                "  1. **Monsters (Value)**: AA, KK, QQ, AKs.\n"
                "  2. **Blocker Bluffs (Semi-Bluffs)**: Hands like **A5s, A4s, KTs**. These hands aren't strong enough to call an open, but holding an Ace removes 50% of opponent's AA and AK combinations! If called, they flop nut flush and straight draws.\n\n"
                "> **Educational Provenance Note:**\n"
                "> These linear and polarized charts are **illustrative educational models** representing canonical 100bb cash paradigms. Exact GTO solver outputs use complex mixed frequencies (e.g. 3-betting A5s at 35% frequency and calling at 25% frequency) rather than pure binary selection."
            ),
            key_takeaway="Polarized ranges balance monster value hands with blocker-driven bluffs (like A5s).",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="3-Bet Sizing Geometry: In Position vs Out of Position",
            step_type="APPLY",
            content_markdown=(
                "Sizing your 3-bet correctly is critical to prevent opponents from calling with optimal odds:\n\n"
                "- **In Position (IP)**: Size to **3x the open**.\n"
                "  *Example:* Villain opens to 2.5bb on Cutoff $\\rightarrow$ You 3-bet to **7.5bb** on the Button.\n\n"
                "- **Out of Position (OOP)**: Size to **4x – 4.5x the open**.\n"
                "  *Example:* Villain opens to 2.5bb on Button $\\rightarrow$ You 3-bet to **10bb – 11bb** from the Big Blind.\n\n"
                "Why must you size larger OOP? Because acting first on every postflop street is a massive disadvantage; a larger bet size charges opponent for their positional advantage."
            ),
            key_takeaway="3-bet 3x the open when In Position; 3-bet 4x to 4.5x when Out of Position.",
        ),
        InteractiveLessonStep(
            step_number=4,
            title="Knowledge Check: Blocker Bluffs",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "Why does a polarized 3-betting range prefer bluffing with A5s over hands like K9o or 87o?",
                "options": [
                    "A5s holds an Ace blocker (reducing opponent's AA/AK combos by half) and has nut-flush and wheel-straight potential when called.",
                    "A5s always wins at showdown even when unimproved.",
                    "A5s is considered a monster value hand identical to AA.",
                    "Poker rules require suited aces to 3-bet.",
                ],
                "correct_index": 0,
                "explanation": "Correct! A5s provides powerful card removal (blocking opponent's premium continues) while maintaining exceptional playability to hit nuts when called.",
                "remediation": "Blocker bluffs must reduce the opponent's continuing range while retaining live postflop drawing equity.",
            },
            content_markdown="Verify your understanding of blocker-driven 3-bet construction.",
            key_takeaway="Suited wheel aces (A5s, A4s) are prime 3-bet bluffs due to blocker removal and nut potential.",
        ),
        InteractiveLessonStep(
            step_number=5,
            title="Recap: 3-Betting Mastery",
            step_type="RECAP",
            component_type="lesson_completion_summary",
            component_props={
                "xpEarned": 25,
                "masteryKey": "preflop.three_bet",
                "conceptsLearned": [
                    "3-betting seizes initiative and denies equity",
                    "Linear ranges use top-heavy hands; Polarized ranges use nuts + blocker bluffs",
                    "Size 3x IP, 4x to 4.5x OOP",
                    "A5s-A4s are premier blocker bluffs",
                ],
            },
            content_markdown="Outstanding! You have mastered the mechanics of aggressive preflop re-raising.",
            key_takeaway="Mastering 3-bet ranges is the clearest differentiator between beginner and intermediate poker players.",
        ),
    ],
)

LESSON_C4_U3_STACK_DEPTH = CourseLesson(
    id="lesson.c4.u3.stack_depth_adjustments",
    path_id="path.foundations",
    chapter_id="chap_4_preflop",
    unit_id="unit_4_3_stack_depth",
    title="Stack-Depth Preflop Adjustments",
    summary="How 100bb deep stacks, 40bb medium stacks, and 15bb shallow stacks invert hand values and commitment thresholds.",
    skill_id="preflop.stack_depth",
    difficulty_level="INTERMEDIATE",
    estimated_minutes=8,
    prerequisite_lesson_ids=["lesson.c4.u2.three_bet_strategy"],
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="The Three Stack Depth Regimes",
            step_type="EXPLAIN",
            component_type="effective_stack",
            component_props={"heroStackBb": 100, "villainStackBb": 100, "interactive": True},
            content_markdown=(
                "In Texas Hold'em, a hand's strategic value is completely transformed by the **effective stack depth**:\n\n"
                "- **Deep Stacks (100bb+)**: Typical in cash games and early tournament stages. Massive room for multi-street maneuvering postflop.\n"
                "- **Medium Stacks (30bb – 50bb)**: Common in mid-stage tournaments. Postflop commitments happen quickly on the flop or turn.\n"
                "- **Shallow Stacks (< 20bb)**: Late-stage tournaments. Postflop maneuvering disappears; game simplifies into all-in or fold decisions."
            ),
            key_takeaway="Effective stack depth fundamentally determines which starting hands are profitable.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="Hand Value Inversion: Speculative vs High Card",
            step_type="EXPLAIN",
            content_markdown=(
                "Watch how stack depth inverts the hierarchy of starting hands:\n\n"
                "| Hand Category | Example | Deep Stacks (100bb+) | Shallow Stacks (15bb) |\n"
                "| :--- | :--- | :--- | :--- |\n"
                "| **Small Pocket Pairs** | 3♠ 3♦ | **Very High Value**: Set-mining wins 100bb stacks. | **Near Zero Value**: Hitting a set 11% of the time cannot compensate for 15bb stack limit. |\n"
                "| **Suited Connectors** | 7♥ 6♥ | **High Value**: Deep implied odds for flushes/straights. | **Unplayable Trash**: No implied odds to chase draws; low high-card value. |\n"
                "| **Offsuit Broadways** | K♠ T♦, A♠ 9♦ | **Marginal / Trap**: Reverse implied odds when dominated. | **Elite Shoving Hands**: High card equity and blockers dominate short-stack jams! |"
            ),
            key_takeaway="Deep stacks favor speculative draws; shallow stacks favor raw high cards and blockers.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Stack-to-Pot Ratio (SPR) Awareness",
            step_type="APPLY",
            content_markdown=(
                "**Stack-to-Pot Ratio (SPR)** measures effective stack remaining divided by the flop pot size:\n\n"
                "> **Formula: SPR** = $\\frac{\\text{Effective Stack Remaining}}{\\text{Flop Pot Size}}$\n\n"
                "- **Low SPR (< 3)**: Top pair top kicker is an automatic stack-off commitment.\n"
                "- **Medium SPR (4 – 7)**: Cautious play needed; top pair cannot easily withstand 3 streets of betting.\n"
                "- **High SPR (10+)**: Sets, flushes, and full houses are required to commit an entire 100bb+ stack.\n\n"
                "At 15bb preflop, raising to 2.5bb creates a 5.5bb pot with 12.5bb remaining behind (SPR $\\approx 2.3$). You are virtually pot-committed on any flop connection!"
            ),
            key_takeaway="SPR dictates hand commitment thresholds postflop.",
        ),
        InteractiveLessonStep(
            step_number=4,
            title="Knowledge Check: Stack Depth Hand Selection",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "At a 15 BB effective stack depth in a tournament, why do hands like A8o and KTo gain massive value while 65s becomes an easy fold?",
                "options": [
                    "High cards hold blockers and win showdowns unimproved on short stacks, while suited connectors require deep implied odds that 15 BB cannot provide.",
                    "65s is penalized by tournament rules at 15 BB.",
                    "A8o has higher implied odds than 65s.",
                    "Tournaments do not allow suited cards to hit straights.",
                ],
                "correct_index": 0,
                "explanation": "Correct! When stacks are short, there are no implied odds to chase flushes or straights with 65s. High-card broadways have blocker value and win high-card showdowns.",
                "remediation": "Speculative hands require deep stacks to pay off; shallow stacks reward card blockers and raw high-card showdown strength.",
            },
            content_markdown="Test your comprehension of stack-depth value transitions.",
            key_takeaway="Shallow stacks reward blockers and high cards; deep stacks reward implied odds.",
        ),
        InteractiveLessonStep(
            step_number=5,
            title="Recap: Stack Depth Adjustments",
            step_type="RECAP",
            component_type="lesson_completion_summary",
            component_props={
                "xpEarned": 25,
                "masteryKey": "preflop.stack_depth",
                "conceptsLearned": [
                    "Deep stacks (100bb+) reward speculative implied odds (pairs, connectors)",
                    "Shallow stacks (<20bb) reward high card blockers and raw showdown equity",
                    "SPR defines postflop hand commitment thresholds",
                ],
            },
            content_markdown="Great work! You now adjust your preflop starting hands dynamically based on stack depth.",
            key_takeaway="Always check effective stack sizes before looking at your hole cards.",
        ),
    ],
)

LESSON_C4_CHECKPOINT = CourseLesson(
    id="lesson.c4.checkpoint",
    path_id="path.foundations",
    chapter_id="chap_4_preflop",
    unit_id="unit_4_3_stack_depth",
    title="Chapter 4 Checkpoint: Preflop Strategist",
    summary="Validate mastery of positional opening, RFI ranges, blind defense, 3-betting, and stack-depth adjustments.",
    skill_id="checkpoint.chapter_4",
    difficulty_level="INTERMEDIATE",
    estimated_minutes=6,
    prerequisite_lesson_ids=["lesson.c4.u3.stack_depth_adjustments"],
    is_unit_challenge=True,
    is_chapter_checkpoint=True,
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="Preflop Strategy Synthesis",
            step_type="EXPLAIN",
            content_markdown=(
                "### 🛡️ Chapter 4 Capstone Evaluation\n\n"
                "You have surveyed the complete preflop landscape:\n\n"
                "1. **Positional Leverage**: Why opening ranges expand from 15% (UTG) to 43% (BTN).\n"
                "2. **Open-Raising**: Optimal 2.25x-2.5x sizing and eliminating open-limping.\n"
                "3. **Defending**: Exploiting BB discounted pot odds with playable suited holdings.\n"
                "4. **3-Betting**: Linear vs polarized construction and blocker removal with A5s.\n"
                "5. **Stack Depth**: Inverting speculative hands for high cards as stacks shrink.\n\n"
                "Prove your mastery below to unlock Chapter 5: Postflop Strategy!"
            ),
            key_takeaway="Preflop strategy sets the boundaries for all postflop equity and EV.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="Capstone Challenge: Preflop Decision",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "You are on the Button with 100 BB effective stacks. Cutoff opens to 2.5 BB. Which of the following represents an optimal polarized 3-bet candidate holding strong blocker removal and playability?",
                "options": ["A5s", "K7o", "22", "J4s"],
                "correct_index": 0,
                "explanation": "Correct! A5s is the premier polarized 3-bet bluff: its Ace blocks Cutoff's continue range, and it flops nut flushes and straight wheel draws when called.",
                "remediation": "Blocker bluffs require an Ace or King to remove premium combos from opponent's range, paired with suited connectivity for postflop playability.",
            },
            content_markdown="Solve this preflop range construction challenge.",
            key_takeaway="A5s balances value 3-bets with card removal and postflop drawing equity.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Chapter 4 Complete: Certified Preflop Strategist!",
            step_type="COMMIT",
            component_type="chapter_checkpoint",
            component_props={
                "chapterNumber": 4,
                "chapterTitle": "Preflop Strategy",
                "badgeName": "Preflop Strategist",
                "xpEarned": 50,
                "nextChapterId": "chap_5_postflop",
            },
            content_markdown=(
                "### 🛡️ Chapter 4 Mastered!\n\n"
                "You have certified your command over preflop poker:\n"
                "- **Positional Opening Logic & RFI Ranges**\n"
                "- **Big Blind Defense & Playability Selection**\n"
                "- **Linear & Polarized 3-Bet Construction**\n"
                "- **Stack-Depth Adaptations & SPR**\n\n"
                "Next stop: **Chapter 5: Postflop Strategy**!"
            ),
            key_takeaway="Chapter 4 Certified! Ready for Postflop Strategy.",
        ),
    ],
)


# ============================================================================
# CHAPTER 5 LESSONS — POSTFLOP STRATEGY
# ============================================================================

LESSON_C5_U1_TEXTURES = CourseLesson(
    id="lesson.c5.u1.board_textures_advantage",
    path_id="path.postflop_barrelling",
    chapter_id="chap_5_postflop",
    unit_id="unit_5_1_textures_advantages",
    title="Board Textures, Range & Nut Advantage",
    summary="Classify dry vs wet boards and evaluate Range Advantage vs Nut Advantage to dictate continuation betting.",
    skill_id="postflop.textures",
    difficulty_level="INTERMEDIATE",
    estimated_minutes=9,
    prerequisite_lesson_ids=["lesson.c4.checkpoint"],
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="Board Texture Archetypes",
            step_type="EXPLAIN",
            component_type="betting_timeline",
            component_props={"currentRound": "flop", "showCards": True},
            content_markdown=(
                "When the 3 community cards hit the board on the flop, you must instantly classify the **texture**:\n\n"
                "- **Dry / Static Textures** (e.g. K♠ 8♦ 2♣, A♦ 7♠ 3♣):\n"
                "  Cards are disconnected and unsuited. Almost no draws exist. Hand equities are stable and will rarely change on the turn or river.\n\n"
                "- **Wet / Dynamic Textures** (e.g. J♥ T♥ 9♠, 9♦ 8♦ 7♣):\n"
                "  Cards are heavily coordinated in rank and suit. Countless straight and flush draws exist. Hand equities are volatile; a turn card can flip the leader instantly.\n\n"
                "- **Paired Textures** (e.g. K♣ K♦ 5♠): Dramatically reduce possible combinations of strong hands; sets are impossible and trips are rare.\n\n"
                "- **Monotone Textures** (e.g. Q♠ 8♠ 3♠): All three cards share a suit. Anyone holding a single spade has flush redraw equity."
            ),
            key_takeaway="Dry boards feature stable equity; wet boards feature volatile equity with abundant draws.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="Range Advantage vs Nut Advantage",
            step_type="EXPLAIN",
            content_markdown=(
                "Modern postflop theory rests on the vital distinction between two concepts:\n\n"
                "> **1. Range Advantage (Equity Advantage)**\n"
                "> Which player's **entire range of hands** has the higher average equity against the opponent's range? Typically belongs to the preflop raiser, whose range contains all the high pairs and broadways.\n\n"
                "> **2. Nut Advantage (Polarization Advantage)**\n"
                "> Which player has the highest concentration of **the super-strongest possible holdings** (nuts, sets, straights, flushes)?\n\n"
                "**Crucial Rule:**\n"
                "- **Range advantage** dictates **betting frequency** (how often you bet).\n"
                "- **Nut advantage** dictates **betting sizing** (how large you bet)."
            ),
            key_takeaway="Range advantage governs how often you bet; nut advantage governs how large you bet.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Worked Board Comparison: Dry Ace vs Connected Ten",
            step_type="APPLY",
            content_markdown=(
                "Consider Button Open vs Big Blind Call on two different boards:\n\n"
                "- **Board A: A♠ 8♦ 3♣ (Dry Rainbow)**\n"
                "  - Button holds AA, AK, AQ, AJ (hands the Big Blind would have 3-bet preflop).\n"
                "  - Button has massive **Range Advantage** (58%+ equity).\n"
                "  - Big Blind misses this flop completely with most of their defending range.\n"
                "  - **Strategy**: Button can bet a small sizing (33% pot) with almost their entire range!\n\n"
                "- **Board B: 9♥ 8♥ 7♣ (Wet Connected)**\n"
                "  - Big Blind's calling range is packed with connectors (JT, T9, 87, 76, 65) that hit two pairs, sets, and straights.\n"
                "  - Big Blind holds substantial **Nut Advantage**!\n"
                "  - **Strategy**: Button must check frequently to pot-control and protect their range."
            ),
            key_takeaway="High-card dry boards heavily favor the preflop raiser; connected mid-boards favor the caller.",
        ),
        InteractiveLessonStep(
            step_number=4,
            title="Knowledge Check: Board Advantage",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "A player opens from the Button and the Big Blind calls. The flop is A♦ K♠ 4♣. Which player holds massive range advantage and why?",
                "options": [
                    "The Button, because their preflop opening range contains all the premium pairs (AA, KK) and top broadways (AK, AQ) that the Big Blind would have 3-bet preflop.",
                    "The Big Blind, because they act first postflop.",
                    "The Big Blind, because they called with more speculative cards.",
                    "Equities are exactly 50/50 on rainbow flops.",
                ],
                "correct_index": 0,
                "explanation": "Correct! The preflop raiser retains uncapped range advantage on high-card boards because the Big Blind would have 3-bet hands like AA, KK, and AK preflop.",
                "remediation": "The caller's range is condensed (capped), meaning they rarely hold monster broadways on Ace-King high boards.",
            },
            content_markdown="Test your grasp of range advantage distribution.",
            key_takeaway="High broadway textures strongly favor the preflop raiser's uncapped range.",
        ),
        InteractiveLessonStep(
            step_number=5,
            title="Recap: Textures & Advantage",
            step_type="RECAP",
            component_type="lesson_completion_summary",
            component_props={
                "xpEarned": 25,
                "masteryKey": "postflop.textures",
                "conceptsLearned": [
                    "Classify boards: Dry, Wet/Dynamic, Paired, Monotone",
                    "Range Advantage = higher average equity across the whole range",
                    "Nut Advantage = higher concentration of the nuts and monster holdings",
                    "Range advantage drives bet frequency; Nut advantage drives bet sizing",
                ],
            },
            content_markdown="Great work! You now understand the strategic foundation of flop texture analysis.",
            key_takeaway="Always diagnose who benefits most from the board texture before choosing your postflop line.",
        ),
    ],
)

LESSON_C5_U1_CBET = CourseLesson(
    id="lesson.postflop.cbet_fundamentals",
    path_id="path.postflop_barrelling",
    chapter_id="chap_5_postflop",
    unit_id="unit_5_1_textures_advantages",
    title="Continuation Betting (C-Betting) Strategy & Sizing",
    summary="Why preflop aggressors continue betting, how to balance value with bluffs, and choosing optimal c-bet sizing.",
    skill_id="postflop.cbet",
    difficulty_level="INTERMEDIATE",
    estimated_minutes=9,
    prerequisite_lesson_ids=["lesson.c5.u1.board_textures_advantage"],
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="The Mechanics of the C-Bet",
            step_type="EXPLAIN",
            component_type="pot_odds",
            component_props={"pot": 60, "bet": 20, "interactive": True},
            content_markdown=(
                "A **Continuation Bet (C-Bet)** is a bet made on the flop by the player who held the betting initiative preflop.\n\n"
                "> **The Three Motives for C-Betting:**\n"
                "> 1. **Value**: Get called by worse hands (e.g. top pair called by second pair).\n"
                "> 2. **Bluff / Fold Equity**: Force opponent to fold hands that currently have live equity against you.\n"
                "> 3. **Equity Protection / Denial**: Force opponent to fold hands with 3 to 6 outs before they hit a free card on the turn."
            ),
            key_takeaway="A c-bet continues preflop aggression to extract value, deny equity, or claim fold equity.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="Sizing Strategy: Small (33%) vs Large (66%–75%)",
            step_type="EXPLAIN",
            content_markdown=(
                "How do you choose your c-bet sizing?\n\n"
                "- **Small Sizing (25% – 33% Pot)**:\n"
                "  - **When**: On dry, disconnected, high-card flops (e.g. K-8-2r, A-7-3r).\n"
                "  - **Why**: You have massive range advantage; the opponent cannot call profitably with air; a cheap bet wins the pot or charges them adequately.\n"
                "  - **Frequency**: Very high (often 70% – 100% of your range).\n\n"
                "- **Large Sizing (66% – 75% Pot)**:\n"
                "  - **When**: On wet, connected, coordinated flops (e.g. J♥ T♥ 7♣, 9♠ 8♠ 6♦).\n"
                "  - **Why**: Opponent's calling range has many draws and pairs; a small bet gives them too cheap a price to draw; you must charge draws maximum pot odds.\n"
                "  - **Frequency**: Selective and polarized (35% – 50% frequency)."
            ),
            key_takeaway="Use small c-bets frequently on dry boards; use large c-bets selectively on wet boards.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Constructing the C-Bet Bluffing Range",
            step_type="APPLY",
            content_markdown=(
                "Never bluff with completely random, hopeless cards. Professional c-bet bluffs are **semi-bluffs** that possess **backdoor equity**:\n\n"
                "- **Backdoor Flush Draws (BDFD)**: Holding two cards of a suit when one is on the board. A turn card of your suit gives you a 9-out flush draw!\n"
                "- **Backdoor Straight Draws (BDSD)**: Two cards that can turn an open-ended straight draw.\n"
                "- **Overcards**: Cards higher than the board that can hit top pair on the turn.\n\n"
                "Hands with backdoor equity can comfortably fire a second bet (barrel) when the turn improves their equity."
            ),
            key_takeaway="Choose c-bet bluffs that possess backdoor straight or flush potential on future cards.",
        ),
        InteractiveLessonStep(
            step_number=4,
            title="Knowledge Check: C-Bet Sizing Rule",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "You open on the Button and Big Blind calls. The flop is K♠ 7♦ 2♣ (dry, uncoordinated). What is the standard solver-approved c-bet sizing and frequency?",
                "options": [
                    "Small sizing (~25% to 33% pot) at high frequency across most of your range.",
                    "Pot-sized bet at low frequency.",
                    "Check 100% of the time.",
                    "Overbet 150% pot.",
                ],
                "correct_index": 0,
                "explanation": "Correct! On dry, uncoordinated King-high boards, the preflop raiser has massive range advantage and can bet small (1/3 pot) with high frequency to deny equity cheaply.",
                "remediation": "Dry, disconnected high-card flops favor high-frequency small bets (25-33% pot).",
            },
            content_markdown="Test your grasp of c-bet sizing logic.",
            key_takeaway="Dry King-high boards call for high-frequency 1/3 pot continuation bets.",
        ),
        InteractiveLessonStep(
            step_number=5,
            title="Recap: C-Bet Fundamentals",
            step_type="RECAP",
            component_type="lesson_completion_summary",
            component_props={
                "xpEarned": 25,
                "masteryKey": "postflop.cbet",
                "conceptsLearned": [
                    "C-bet for value, fold equity, or equity protection",
                    "Dry boards: small sizing (25-33%) at high frequency",
                    "Wet boards: large sizing (66-75%) at selective frequency",
                    "Bluff with backdoor straight and flush potential",
                ],
            },
            content_markdown="Great job! You now possess a structured, professional framework for continuation betting.",
            key_takeaway="Calibrate your c-bet sizing and frequency to board texture and equity distribution.",
        ),
    ],
)

LESSON_C5_U2_TURN_BARREL = CourseLesson(
    id="lesson.postflop.turn_barrel",
    path_id="path.postflop_barrelling",
    chapter_id="chap_5_postflop",
    unit_id="unit_5_2_barreling_rivers",
    title="The Second Barrel: Turn Aggression Mechanics",
    summary="Firing a second bet on the turn after your flop c-bet was called. Understanding equity shifts and board runouts.",
    skill_id="postflop.turn.barrel",
    difficulty_level="ADVANCED",
    estimated_minutes=10,
    prerequisite_lesson_ids=["lesson.postflop.cbet_fundamentals"],
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="Turn Card Categorization: Who Does It Help?",
            step_type="EXPLAIN",
            component_type="betting_timeline",
            component_props={"currentRound": "turn", "showCards": True},
            content_markdown=(
                "When your flop c-bet is called and the 4th community card arrives, pause and ask: **Who does this turn card help?**\n\n"
                "Turn cards fall into three distinct categories:\n\n"
                "1. **Blanks (Low, Uncoordinated Cards)** (e.g. 2♣ on K♠ 8♦ 4♥):\n"
                "   Changes almost nothing. Reinforces the preflop raiser's flop advantage.\n\n"
                "2. **Overcards (Ace or King)**:\n"
                "   Drastically strengthens the preflop raiser's range (AA, KK, AK) while terrifying the caller's mid-pair defense.\n\n"
                "3. **Coordinated / Completing Cards (Straight or Flush cards)**:\n"
                "   Connects heavily with the flop caller's condensed defense range. Preflop raiser must slow down and pot-control."
            ),
            key_takeaway="Overcards and blanks favor the preflop aggressor; completing cards favor the caller.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="Polarizing the Second Barrel",
            step_type="EXPLAIN",
            content_markdown=(
                "Unlike flop c-bets which can be small and merged, **turn bets must polarize**:\n\n"
                "- By calling your flop bet, opponent folded their absolute junk. Their range is now **condensed** (composed of made pairs and live draws).\n"
                "- Small bets no longer work effectively; turn sizing generally expands to **66% to 75% of the pot**.\n"
                "- Your turn betting range splits cleanly into:\n"
                "  1. **Strong Value**: Hands that can happily bet three streets (two pair, sets, strong top pair).\n"
                "  2. **High-Equity Semi-Bluffs**: Draws that picked up equity (flush draws, open-enders, combo draws).\n"
                "- Medium hands (middle pair, weak top pair) must **check** to control the pot size and reach showdown cheaply."
            ),
            key_takeaway="Turn bets polarize between strong value and high-equity semi-bluffs; check medium showdown value.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Sizing Geometry: Setting Up the River All-In",
            step_type="APPLY",
            component_type="pot_odds",
            component_props={"pot": 120, "bet": 80, "interactive": True},
            content_markdown=(
                "In deep-stack poker, masters plan multi-street **sizing geometry**:\n\n"
                "If the flop pot is 20bb and effective stacks are 90bb:\n"
                "- Flop c-bet of 7bb creates a **34bb pot** on the turn.\n"
                "- Turn bet of 22bb (65% pot) creates a **78bb pot** on the river, leaving exactly **61bb** in remaining stacks!\n"
                "- Now the river shove is an ideal **78% pot bet**!\n\n"
                "Planning your turn sizing ensures you don't arrive on the river with an awkward, oversized 200% pot shove or a tiny 20% pot click."
            ),
            key_takeaway="Geometric bet sizing scales the pot so that the river bet naturally consumes the remaining stack.",
        ),
        InteractiveLessonStep(
            step_number=4,
            title="Knowledge Check: Turn Barreling Card",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "You open Button, BB calls. Flop is 9♠ 5♦ 2♣ and you c-bet, BB calls. The turn card is the A♥. Why is this an exceptional card for you to fire a second barrel?",
                "options": [
                    "The Ace heavily favors your preflop opening range (which holds all AA, AK, AQ) and applies maximum fold pressure on BB's mid-pairs (9x, 5x).",
                    "Because Aces automatically win pots.",
                    "Because BB is guaranteed to hold an Ace.",
                    "Because the pot is too small to check.",
                ],
                "correct_index": 0,
                "explanation": "Correct! An overcard Ace drastically improves the preflop raiser's range while devaluing the caller's second pairs (like 9x), creating tremendous fold equity on a second barrel.",
                "remediation": "Turn overcards strengthen the aggressor's range and put extreme pressure on caller's bluff-catchers.",
            },
            content_markdown="Test your grasp of turn card categorization.",
            key_takeaway="Turn overcards provide ideal runouts for firing profitable second barrels.",
        ),
        InteractiveLessonStep(
            step_number=5,
            title="Recap: Turn Aggression Mastery",
            step_type="RECAP",
            component_type="lesson_completion_summary",
            component_props={
                "xpEarned": 25,
                "masteryKey": "postflop.turn.barrel",
                "conceptsLearned": [
                    "Categorize turn runouts: Blanks, Overcards, Completing Cards",
                    "Polarize turn bets: strong value + high-equity semi-bluffs",
                    "Check middle-strength hands to pot-control",
                    "Use geometric sizing (66-75% pot) to set up river commitments",
                ],
            },
            content_markdown="Outstanding! You have mastered the tactical bridge between the flop and river.",
            key_takeaway="Controlled turn aggression on favorable runouts is the hallmark of elite postflop play.",
        ),
    ],
    linked_scenario_id="pack_64bf1668d802a75d_n0_2d2h",
    transfer_scenario_id="pack_cert_cash_turn_barrel_dd24266c0d7fdbc0_n0_2d2h",
    transfer_availability="AVAILABLE",
    transfer_rationale="Held-out single-raised turn runout (Qh Jd 4s 8c at 80bb) testing turn barrel continuation on altered queen-high texture.",
)

LESSON_C5_U2_RIVER_BLUFFCATCH = CourseLesson(
    id="lesson.postflop.river_bluffcatch",
    path_id="path.river_polarization",
    chapter_id="chap_5_postflop",
    unit_id="unit_5_2_barreling_rivers",
    title="River Polarization, MDF & Blocker Bluff-Catching",
    summary="The mathematics of river bets: polarized value-to-bluff ratios, Minimum Defense Frequency (MDF), and card removal blockers.",
    skill_id="postflop.river.bluffcatch",
    difficulty_level="ELITE",
    estimated_minutes=11,
    prerequisite_lesson_ids=["lesson.postflop.turn_barrel"],
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="The Strictly Polarized River State",
            step_type="EXPLAIN",
            component_type="pot_odds",
            component_props={"pot": 100, "bet": 100, "interactive": True},
            content_markdown=(
                "On the river, all cards have been dealt. There are **zero draws remaining**; every hand's equity is frozen at either **100% or 0%**.\n\n"
                "Therefore, every river bet must be **strictly polarized**:\n\n"
                "1. **Pure Value**: Hands that beat opponent's calling range.\n"
                "2. **Pure Bluffs**: Hands with zero showdown value that win only when opponent folds.\n\n"
                "**Golden River Rule:** Never bet a hand that wins when checked down, but loses when called! Medium hands must check to realize their showdown value."
            ),
            key_takeaway="River betting is strictly polarized: pure value or pure bluff. Check medium showdown hands.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="Minimum Defense Frequency (MDF)",
            step_type="EXPLAIN",
            content_markdown=(
                "How often must you defend against a river bet to prevent your opponent from bluffing profitably with any two cards?\n\n"
                "> **Formula: Minimum Defense Frequency (MDF)**\n\n"
                "> **MDF** = $\\frac{\\text{Pot Size}}{\\text{Pot Size} + \\text{Bet Size}}$\n\n"
                "| Bet Size Faced | Pot Odds Given to Bluffer | MDF (Calling % Required) |\n"
                "| :--- | :--- | :--- |\n"
                "| **Half-Pot Bet (50%)** | Risk 1 to win 2 (33% bluff success needed) | **66.7%** of range must defend |\n"
                "| **Three-Quarter Pot (75%)** | Risk 3 to win 4 (43% bluff success needed) | **57.1%** of range must defend |\n"
                "| **Full-Pot Bet (100%)** | Risk 1 to win 1 (50% bluff success needed) | **50.0%** of range must defend |\n"
                "| **Overbet (150% Pot)** | Risk 1.5 to win 1 (60% bluff success needed) | **40.0%** of range must defend |"
            ),
            key_takeaway="MDF dictates the mathematical fraction of your range you must defend against a bet.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Blocker Theory: How to Pick the Best Bluff-Catchers",
            step_type="APPLY",
            content_markdown=(
                "MDF tells you **how many** hands to call with, but **which specific hands** should you choose?\n\n"
                "The answer is **Blocker Theory (Card Removal)**:\n\n"
                "> **The Two Blocker Golden Rules:**\n"
                "> 1. **Block Opponent's Value**: Hold cards that match opponent's value combos. (e.g. On an Ace-high board, holding an Ace removes 50% of opponent's top pairs).\n"
                "> 2. **Unblock Opponent's Bluffs**: Do NOT hold the cards opponent would bluff with! (e.g. On a missed flush-draw board, holding the flush suit blocks their missed bluffs, making their bet much more likely to be real value!).\n\n"
                "A weak pair that blocks the nuts and unblocks missed draws is a vastly superior call compared to a higher pair that blocks the opponent's bluffs!"
            ),
            key_takeaway="Ideal bluff-catchers block opponent's value hands while unblocking their missed bluffs.",
        ),
        InteractiveLessonStep(
            step_number=4,
            title="Knowledge Check: River Blocker Effect",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "On a river board of A♠ 9♦ 4♣ 2♠ 7♠ (flush draw completes on river), your opponent fires a pot-sized bet. Why is holding a hand with a single spade (like K♠ 9♥) a significantly better bluff-catcher than holding K♦ 9♦?",
                "options": [
                    "Holding the K♠ blocks the opponent from holding King-high flushes, drastically reducing their value combinations while leaving their missed straight draws intact.",
                    "Spades are higher ranking suits in showdown rules.",
                    "K♠ 9♥ makes a full house on this board.",
                    "There is no mathematical difference between suits on the river.",
                ],
                "correct_index": 0,
                "explanation": "Correct! Holding the K♠ removes a substantial number of nut and second-nut flush combinations from opponent's value betting range, making it far more likely they are bluffing.",
                "remediation": "Card removal with key suit blockers reduces opponent's value combos and increases their bluff ratio.",
            },
            content_markdown="Evaluate river bluff-catcher selection using card removal.",
            key_takeaway="Suit blockers remove premium value hands from opponent's range, turning marginal holdings into profitable calls.",
        ),
        InteractiveLessonStep(
            step_number=5,
            title="Recap: River Polarization & Bluff-Catching",
            step_type="RECAP",
            component_type="lesson_completion_summary",
            component_props={
                "xpEarned": 25,
                "masteryKey": "postflop.river.bluffcatch",
                "conceptsLearned": [
                    "River bets are strictly polarized (nuts or air)",
                    "MDF = Pot ÷ (Pot + Bet)",
                    "Never bet medium showdown value",
                    "Block opponent's value hands, unblock their bluffs",
                ],
            },
            content_markdown="Congratulations! You have mastered the most sophisticated street in Texas Hold'em.",
            key_takeaway="River mastery combines strict polarization with blocker-driven defensive calling.",
        ),
    ],
    linked_scenario_id="pack_d3f179c8517b68a7_n0_2d2h",
    transfer_scenario_id=None,
    transfer_availability="UNAVAILABLE_INSUFFICIENT_VALIDATED_CONTENT",
    transfer_rationale="Held-out 4-flush and paired-board river bluff-catching scenarios are pending solver generation.",
)

LESSON_C5_CHECKPOINT = CourseLesson(
    id="lesson.c5.checkpoint",
    path_id="path.postflop_barrelling",
    chapter_id="chap_5_postflop",
    unit_id="unit_5_2_barreling_rivers",
    title="Chapter 5 Checkpoint: Postflop Master",
    summary="Validate mastery of board textures, range & nut advantage, continuation betting, turn barreling, and river bluff-catching.",
    skill_id="checkpoint.chapter_5",
    difficulty_level="ADVANCED",
    estimated_minutes=6,
    prerequisite_lesson_ids=["lesson.postflop.river_bluffcatch"],
    is_unit_challenge=True,
    is_chapter_checkpoint=True,
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="Postflop Synthesis Checkpoint",
            step_type="EXPLAIN",
            content_markdown=(
                "### 🎯 Chapter 5 Capstone Evaluation\n\n"
                "You have traversed all three postflop betting streets:\n\n"
                "1. **Flop Textures**: Range Advantage vs Nut Advantage on dry vs dynamic boards.\n"
                "2. **C-Betting**: High-frequency 1/3 pot bets on dry boards vs polarized 3/4 pot bets on wet boards.\n"
                "3. **Turn Barrels**: Categorizing runouts, semi-bluffing, and sizing geometry.\n"
                "4. **River Polarization**: Minimum Defense Frequency (MDF) and blocker-driven bluff-catching.\n\n"
                "Answer the capstone question below to earn your **Postflop Master** certification!"
            ),
            key_takeaway="Postflop mastery requires executing coordinated multi-street plans from flop to river.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="Capstone Challenge: Multi-Street Strategy",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "Opponent bets 100% of the pot on the river. Using the MDF formula (MDF = Pot / (Pot + Bet)), what percentage of your range must you defend to make their bluffs indifferent?",
                "options": ["50.0%", "66.7%", "33.3%", "75.0%"],
                "correct_index": 0,
                "explanation": "Correct! MDF = 100 / (100 + 100) = 100 / 200 = 50.0%. Against a pot-sized bet, defending half of your range prevents opponent from profiting with any-two-card bluffs.",
                "remediation": "MDF = Pot / (Pot + Bet) = 100 / (100 + 100) = 0.50 (50%).",
            },
            content_markdown="Solve this fundamental river MDF calculation.",
            key_takeaway="Against a full-pot bet, you must defend exactly 50% of your range.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Chapter 5 Complete: Certified Postflop Master!",
            step_type="COMMIT",
            component_type="chapter_checkpoint",
            component_props={
                "chapterNumber": 5,
                "chapterTitle": "Postflop Strategy",
                "badgeName": "Postflop Master",
                "xpEarned": 50,
                "nextChapterId": "chap_6_tournament",
            },
            content_markdown=(
                "### 🎯 Chapter 5 Mastered!\n\n"
                "You have mastered multi-street postflop decision making:\n"
                "- **Board Texture & Advantage Analysis**\n"
                "- **Continuation Betting & Bet Sizing Rules**\n"
                "- **Turn Barrel Aggression & Equity Shifts**\n"
                "- **River Polarization, MDF & Blocker Theory**\n\n"
                "Prepare for the grand finale: **Chapter 6: Tournament Strategy & ICM**!"
            ),
            key_takeaway="Chapter 5 Certified! Ready for Tournament Strategy.",
        ),
    ],
)


# ============================================================================
# CHAPTER 6 LESSONS — TOURNAMENT STRATEGY
# ============================================================================

LESSON_C6_U1_FORMATS = CourseLesson(
    id="lesson.tourn.formats_and_stack_pressure",
    path_id="path.tournament_short_stack",
    chapter_id="chap_6_tournament",
    unit_id="unit_6_1_push_fold",
    title="Tournament Formats, Antes & Stack Pressure",
    summary="How tournaments differ from cash games, the impact of Big Blind Antes, and navigating escalating stack pressure.",
    skill_id="tournament.fundamentals",
    difficulty_level="INTERMEDIATE",
    estimated_minutes=8,
    prerequisite_lesson_ids=["lesson.c5.checkpoint"],
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="Cash Games vs Tournaments: The Strategic Divide",
            step_type="EXPLAIN",
            component_type="effective_stack",
            component_props={"heroStackBb": 40, "villainStackBb": 40, "interactive": True},
            content_markdown=(
                "Tournaments are fundamentally different games from cash play:\n\n"
                "| Feature | Cash Games | Tournaments (MTTs / SNGs) |\n"
                "| :--- | :--- | :--- |\n"
                "| **Chip Value** | 1 chip = $1 (Linear value) | Chips represent finish probabilities (Non-linear value) |\n"
                "| **Blinds** | Static forever | Escalate on a strict timer |\n"
                "| **Elimination** | Rebuy immediately | When you lose your last chip, you are eliminated |\n"
                "| **Goal** | Maximize expected value per hand (+Chip-EV) | Maximize expected tournament dollar prize (+Dollar-EV) |\n\n"
                "In tournaments, survival is paramount. You cannot simply reload if you bust out."
            ),
            key_takeaway="In tournaments, chips lost are worth more than chips won because elimination is permanent.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="The Big Blind Ante (BBA) & Dead Pot Explosion",
            step_type="EXPLAIN",
            content_markdown=(
                "In modern tournaments, the Big Blind posts a mandatory **Big Blind Ante (BBA)** equal to one full big blind on behalf of the entire table.\n\n"
                "> **The Preflop Dead Money Math:**\n"
                "> - Small Blind: **0.5 BB**\n"
                "> - Big Blind: **1.0 BB**\n"
                "> - Big Blind Ante: **1.0 BB**\n"
                "> - **Starting Pot Before Any Action: 2.5 BB**!\n\n"
                "In a cash game without an ante, the dead pot is only 1.5 BB. The BBA increases the dead starting pot by **67%**!\n\n"
                "This massive dead pot creates huge incentives to steal blinds aggressively, especially when stacks are shallow."
            ),
            key_takeaway="The Big Blind Ante injects 2.5 BB of dead money into every unopened preflop pot.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Stack Zones & The Inflection Point",
            step_type="APPLY",
            component_type="effective_stack",
            component_props={"heroStackBb": 15, "villainStackBb": 15, "interactive": True},
            content_markdown=(
                "As blinds rise, your stack moves through strategic zones:\n\n"
                "- **Deep Zone (> 50 BB)**: Play standard deep-stack poker. Implied odds, 3-betting, and postflop play flourish.\n"
                "- **Transition Zone (25 – 45 BB)**: 3-bet jamming emerges as a potent weapon; flat-calling speculatively becomes unprofitable.\n"
                "- **Reshove Zone (15 – 25 BB)**: Re-stealing over open-raises with all-in shoves yields maximum EV.\n"
                "- **Danger / Push-Fold Zone (< 15 BB)**: Normal postflop play ceases. Strategy simplifies entirely into **All-In or Fold**."
            ),
            key_takeaway="Stacks below 15 BB enter the push-fold zone where postflop play disappears.",
        ),
        InteractiveLessonStep(
            step_number=4,
            title="Knowledge Check: Ante Incentive",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "Why does the presence of a Big Blind Ante (BBA) make preflop blind stealing vastly more profitable in tournaments compared to standard cash games?",
                "options": [
                    "The dead starting pot is 2.5 BB instead of 1.5 BB, providing a 67% larger prize for stealing uncontested.",
                    "Antes force the blinds to fold 100% of their hands.",
                    "Antes double the value of pocket aces.",
                    "Antes are returned to the winner at the end of the tournament.",
                ],
                "correct_index": 0,
                "explanation": "Correct! The 1.0 BB ante expands the starting pot from 1.5 BB to 2.5 BB, making stealing blinds an enormous boost to your tournament stack.",
                "remediation": "The ante increases dead pot size, drastically increasing the payoff of winning uncontested preflop pots.",
            },
            content_markdown="Test your grasp of ante dynamics.",
            key_takeaway="Dead ante chips drastically increase the profitability of aggressive preflop steals.",
        ),
        InteractiveLessonStep(
            step_number=5,
            title="Recap: Tournament Stack Dynamics",
            step_type="RECAP",
            component_type="lesson_completion_summary",
            component_props={
                "xpEarned": 25,
                "masteryKey": "tournament.fundamentals",
                "conceptsLearned": [
                    "Tournament chips have non-linear value tied to payouts",
                    "Big Blind Ante creates a 2.5 BB dead pot preflop",
                    "Stacks <15 BB operate under push/fold rules",
                    "Survival imperative elevates risk aversion",
                ],
            },
            content_markdown="Great work! You now understand the strategic engine that drives tournament poker.",
            key_takeaway="Escalating blind pressure and ante dead money require proactive aggression.",
        ),
    ],
)

LESSON_C6_U1_PUSHFOLD = CourseLesson(
    id="lesson.tourn.pushfold",
    path_id="path.tournament_short_stack",
    chapter_id="chap_6_tournament",
    unit_id="unit_6_1_push_fold",
    title="Shallow Stack Push/Fold Fundamentals",
    summary="When effective stacks drop below 15bb, postflop maneuvering disappears. Master mathematical unexploitable all-in thresholds.",
    skill_id="preflop.tournament.pushfold",
    difficulty_level="INTERMEDIATE",
    estimated_minutes=10,
    prerequisite_lesson_ids=["lesson.tourn.formats_and_stack_pressure"],
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="The Anatomy of an Open Shove",
            step_type="EXPLAIN",
            component_type="range_matrix_explorer",
            component_props={
                "highlightedHands": [
                    "AA",
                    "KK",
                    "QQ",
                    "JJ",
                    "TT",
                    "99",
                    "88",
                    "77",
                    "66",
                    "55",
                    "44",
                    "33",
                    "22",
                    "AKs",
                    "AQs",
                    "AJs",
                    "ATs",
                    "A9s",
                    "A8s",
                    "A7s",
                    "A6s",
                    "A5s",
                    "A4s",
                    "A3s",
                    "A2s",
                    "AKo",
                    "AQo",
                    "AJo",
                    "ATo",
                    "A9o",
                    "A8o",
                    "A7o",
                    "KQs",
                    "KJs",
                    "KTs",
                    "K9s",
                    "K8s",
                    "KQo",
                    "KJo",
                    "KTo",
                    "QJs",
                    "QTs",
                    "Q9s",
                    "JTs",
                    "T9s",
                    "98s",
                ],
                "defaultSelectedHand": "A5s",
            },
            content_markdown=(
                "At 12 BB with a Big Blind Ante in play, min-raising is often a strategic trap: it commits 20% of your stack, and you cannot fold to a 3-bet.\n\n"
                "Instead, game theory proves that strategy collapses into a binary choice: **ALL-IN or FOLD**.\n\n"
                "> **The Two Sources of All-In EV:**\n"
                "> 1. **Fold Equity**: Opponents fold their blinds 60% – 80% of the time, handing you the 2.5 BB dead pot (an instant **>20% stack increase!**).\n"
                "> 2. **Card Equity When Called**: When an opponent calls, your cards still retain 30% to 45% equity to double up!\n\n"
                "Short-stack shoves are driven by fold equity plus live cards when called, not by having a monster hand.\n\n"
                "> **Educational Provenance Note:**\n"
                "> This 12bb open-shove chart is an **analytic educational model** derived from Sklansky-Chubukov unexploitable push/fold mathematical indices (assuming 8-max MTT, 12bb effective stack, 0.5/1.0 blinds, 1.0 BB ante, zero rake). It is not a simulated full-ring post-flop CFR tree."
            ),
            key_takeaway="Push/fold profitability combines high fold equity with live card equity when called.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="Small Blind vs Big Blind 12bb Shoving",
            step_type="EXPLAIN",
            content_markdown=(
                "The most frequent push/fold battle occurs in the **Small Blind vs Big Blind**:\n\n"
                "- With 12 BB effective, equilibrium Nash shove ranges push **over 55% of all hands**!\n"
                "- This includes all pairs (22-AA), all Aces (A2o+, A2s+), any suited King (K2s+), any suited Queen (Q2s+), suited connectors, and high offsuit broadways.\n\n"
                "**Why so wide?** Because the Big Blind only has one player's cards to call with, and calling all-in requires much stronger cards than shoving!"
            ),
            key_takeaway="From the Small Blind at 12bb, equilibrium shoves over 55% of all starting hands.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="The Gap Concept: Shoving vs Calling Requirements",
            step_type="APPLY",
            content_markdown=(
                "David Sklansky's famous **Gap Concept** explains the asymmetry between shoving and calling:\n\n"
                "> **The Gap Concept:**\n"
                "> A player requires a **much stronger hand to call an all-in** than to **make the all-in shove themselves**.\n\n"
                "- **The Pusher**: Has two ways to win (opponents fold OR best hand at showdown).\n"
                "- **The Caller**: Has only ONE way to win (must have the best hand at showdown; zero fold equity).\n\n"
                "Never pass up profitable +EV open-shoves while waiting for premium cards; blinding down to 3 BB guarantees elimination."
            ),
            key_takeaway="The Gap Concept: Calling an all-in requires a much stronger hand than shoving.",
        ),
        InteractiveLessonStep(
            step_number=4,
            title="Knowledge Check: Push/Fold Sizing Logic",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "You have a 10 BB stack on the Button with A4o in an unopened pot with a Big Blind Ante. Why is open-shoving all-in superior to min-raising to 2.0 BB?",
                "options": [
                    "Open-shoving maximizes fold equity, wins the 2.5 BB dead pot uncontested, and avoids playing postflop with awkward commitment on low SPR.",
                    "Min-raising is forbidden by tournament rules under 15 BB.",
                    "A4o is a monster hand that wants to see flops.",
                    "Open-shoving forces the Big Blind to fold pocket aces.",
                ],
                "correct_index": 0,
                "explanation": "Correct! Open-shoving captures maximum fold equity and prevents opponents from realizing equity, while min-raising commits you to a terrible postflop spot with no maneuverability.",
                "remediation": "At 10 BB, min-raising surrenders fold equity; shoving takes down the dead pot or gives you a 35%+ chance to double up when called.",
            },
            content_markdown="Test your grasp of push/fold execution.",
            key_takeaway="Shallow stacks open-shove to maximize fold equity and avoid awkward postflop commitment.",
        ),
        InteractiveLessonStep(
            step_number=5,
            title="Recap: Push/Fold Mastery",
            step_type="RECAP",
            component_type="lesson_completion_summary",
            component_props={
                "xpEarned": 25,
                "masteryKey": "preflop.tournament.pushfold",
                "conceptsLearned": [
                    "Stacks <15 BB operate under binary Push or Fold strategy",
                    "Profit comes from Fold Equity + Card Equity when called",
                    "The Gap Concept: calling requires stronger hands than shoving",
                    "Do not blind down passively; execute unexploitable shoves",
                ],
            },
            content_markdown="Great work! You now understand the mathematical mechanics of tournament survival.",
            key_takeaway="Mastering push/fold charts guarantees you never bleed away your stack passively.",
        ),
    ],
    linked_scenario_id="pack_tourn_8max_12bb_sb_shove_bba_chipev_AsKs",
    transfer_scenario_id=None,
    transfer_availability="UNAVAILABLE_INSUFFICIENT_VALIDATED_CONTENT",
    transfer_rationale="Dedicated held-out push/fold solver packs across 10bb/15bb multi-position trees are pending solver generation.",
)

LESSON_C6_U2_ICM = CourseLesson(
    id="lesson.tourn.icm_fundamentals",
    path_id="path.icm_final_table",
    chapter_id="chap_6_tournament",
    unit_id="unit_6_2_icm_dynamics",
    title="Independent Chip Model (ICM) & Risk Premiums",
    summary="Chips lost vs chips won: why tournament decisions require significant risk premiums near payout thresholds.",
    skill_id="tournament.icm.fundamentals",
    difficulty_level="ELITE",
    estimated_minutes=11,
    prerequisite_lesson_ids=["lesson.tourn.pushfold"],
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="The Non-Linearity of Tournament Chips",
            step_type="EXPLAIN",
            content_markdown=(
                "In a cash game, $1,000 in chips is always worth exactly $1,000 in real money.\n\n"
                "In a tournament, **the relationship between chips and real money is strictly non-linear**:\n\n"
                "- If you enter a 1,000-player tournament with 10,000 chips, doubling your stack to 20,000 chips **NEVER doubles your expected dollar winnings ($EV)**.\n"
                "- Why? Because 1st place does not win 100% of the prize pool! The remaining prize money is distributed among 2nd, 3rd, 4th, etc.\n\n"
                "> **The Core ICM Axiom:**\n"
                "> **The chips you lose are ALWAYS worth more in real money ($EV) than the chips you win.**\n"
                "> Your last chip is worth your entire tournament tournament life; an extra chip on a massive stack adds only fractional dollar equity."
            ),
            key_takeaway="In tournaments, chips you preserve are worth significantly more in real dollars than chips you win.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="What Is the Independent Chip Model (ICM)?",
            step_type="EXPLAIN",
            content_markdown=(
                "The **Independent Chip Model (ICM)** is a mathematical algorithm that converts each player's chip stack count into an exact **dollar equity value ($EV)** based on the remaining payout structure.\n\n"
                "**A Classic Example:**\n"
                "- 4 players remain on the final table.\n"
                "- Payouts: 1st: $10,000 | 2nd: $6,000 | 3rd: $4,000 | 4th: $2,000 (Total: $22,000).\n"
                "- Chip leader has 50% of the chips.\n"
                "- In pure cash math, 50% of $22,000 is $11,000. But 1st place only pays $10,000!\n"
                "- ICM calculates the exact probability that the leader finishes 1st, 2nd, 3rd, or 4th, arriving at a real dollar equity of **~$7,800**."
            ),
            key_takeaway="ICM calculates the exact cash value of every chip stack based on payout distributions.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="The Risk Premium: Why +Chip-EV Can Be -$EV",
            step_type="APPLY",
            content_markdown=(
                "Because chips lost hurt more than chips won, calling all-in requires an **extra equity cushion** called the **Risk Premium**:\n\n"
                "> **Required Equity with ICM** = **Pot Odds Required Equity** + **Risk Premium (%)**\n\n"
                "**Worked Bubble Scenario:**\n"
                "- Pot odds dictate you only need **48% equity** to call a coin-flip all-in.\n"
                "- Your hand has **52% equity** (a profitable +Chip-EV call in cash games!).\n"
                "- However, under ICM on the bubble, your **risk premium is 12%**.\n"
                "- Required Equity to break even in real dollars: $48\\% + 12\\% =$ **60% required equity**!\n"
                "- Since **52% < 60%**, calling loses massive real money ($EV). **You must FOLD!**"
            ),
            key_takeaway="Risk premiums require hands with positive Chip-EV to be folded near payout thresholds.",
        ),
        InteractiveLessonStep(
            step_number=4,
            title="Knowledge Check: ICM Decision",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "On the tournament final table bubble, you face an all-in shove where pot odds require 45% equity to call in Chip-EV. Your hand has 50% equity. The ICM risk premium is calculated at 10%. What is the correct play in real dollar equity ($EV)?",
                "options": [
                    "FOLD, because the true equity required is 45% + 10% = 55%, and your 50% equity falls short of breaking even in real tournament dollars.",
                    "CALL, because 50% is greater than 45%.",
                    "CALL, because coin flips are always profitable in tournaments.",
                    "Shove more chips on top.",
                ],
                "correct_index": 0,
                "explanation": "Correct! Under ICM, your real dollar threshold is Pot Odds (45%) + Risk Premium (10%) = 55%. Since your hand only has 50% equity, calling is heavily -$EV and you must fold.",
                "remediation": "Always add the risk premium to required pot odds. If hand equity < (Pot Odds + Risk Premium), fold.",
            },
            content_markdown="Calculate the true real-dollar decision under ICM risk premium pressure.",
            key_takeaway="Fold whenever hand equity is lower than the sum of pot odds and risk premium.",
        ),
        InteractiveLessonStep(
            step_number=5,
            title="Recap: ICM Foundations",
            step_type="RECAP",
            component_type="lesson_completion_summary",
            component_props={
                "xpEarned": 25,
                "masteryKey": "tournament.icm.fundamentals",
                "conceptsLearned": [
                    "Chips lost are worth more in real dollars than chips won",
                    "ICM converts chip stacks into dollar equity ($EV)",
                    "Risk premiums raise calling thresholds by 5% to 25%+",
                    "Plays with +Chip-EV are frequently catastrophic -$EV errors under ICM",
                ],
            },
            content_markdown="Great job! You now understand the mathematical framework that separates elite tournament pros from amateurs.",
            key_takeaway="ICM dictates that tournament chips are governed by dollar survival, not chip maximization.",
        ),
    ],
    linked_scenario_id="pack_cert_tourn_hu_icm_64f7fb839c4df671_n0_2d2h",
    transfer_scenario_id=None,
    transfer_availability="UNAVAILABLE_INSUFFICIENT_VALIDATED_CONTENT",
    transfer_rationale="Alternative multi-table final table tournament pay jump payout models are pending solver generation.",
)

LESSON_C6_U2_BUBBLE_PAYJUMPS = CourseLesson(
    id="lesson.tourn.bubble_and_payjumps",
    path_id="path.icm_final_table",
    chapter_id="chap_6_tournament",
    unit_id="unit_6_2_icm_dynamics",
    title="Bubble Dynamics, Coverage Advantage & Pay Jumps",
    summary="How big stacks exploit risk aversion on the bubble, navigating final-table pay jumps, and laddering prize money.",
    skill_id="tournament.bubble",
    difficulty_level="ELITE",
    estimated_minutes=10,
    prerequisite_lesson_ids=["lesson.tourn.icm_fundamentals"],
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="The Money Bubble: The Zenith of Risk Aversion",
            step_type="EXPLAIN",
            component_type="effective_stack",
            component_props={"heroStackBb": 60, "villainStackBb": 25, "interactive": True},
            content_markdown=(
                "The **Money Bubble** is the exact moment when one more elimination guarantees that every remaining player cashes.\n\n"
                "- Busting out in **101st place** pays **$0** (hours of play for zero return).\n"
                "- Surviving to **100th place** pays **$1,500**.\n\n"
                "This massive cliff creates extreme **risk aversion** for medium and short stacks. They cannot afford to bust out on the bubble, meaning they are forced to fold hands as strong as Ace-King or pocket Queens when facing all-in pressure!"
            ),
            key_takeaway="The bubble maximizes risk aversion, forcing medium stacks to fold premium holdings.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="Coverage Advantage: The Big Stack Weapon",
            step_type="EXPLAIN",
            content_markdown=(
                "When you hold **more chips than an opponent**, you have **Coverage Advantage**:\n\n"
                "- If you lose an all-in confrontation, you lose chips, but **you remain alive in the tournament**.\n"
                "- If the opponent loses, **they are eliminated from the tournament**.\n\n"
                "> **The Chip Leader Strategy:**\n"
                "> Relentlessly attack medium stacks on the bubble! Open wide, 3-bet aggressively, and shove over their opens. Because their risk premium is so immense, they can only call you with AA or KK, allowing you to harvest dead blinds effortlessly."
            ),
            key_takeaway="Chip leaders weaponize coverage advantage to steal blinds from risk-averse medium stacks.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Final Table Pay Jumps: The Art of Laddering",
            step_type="APPLY",
            content_markdown=(
                "On a final table, payouts jump dramatically with every bust-out:\n\n"
                "- 6th Place: $15,000\n"
                "- 5th Place: $25,000 (+$10,000 jump)\n"
                "- 4th Place: $40,000 (+$15,000 jump)\n\n"
                "**Laddering**: When a microscopic stack (e.g. 2 BB) is about to blind out, medium stacks (15-25 BB) must avoid high-variance clashes. Simply folding and letting the micro-stack bust out first guarantees a **$10,000+ pay jump** with zero risk!\n\n"
                "Never commit tournament suicide against another big stack when someone else is about to bust out."
            ),
            key_takeaway="Laddering allows medium stacks to earn guaranteed payout jumps by letting shorter stacks bust first.",
        ),
        InteractiveLessonStep(
            step_number=4,
            title="Knowledge Check: Bubble Exploitation",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "As a massive chip leader on the direct money bubble of a major tournament, how should your strategy adjust against medium-stacked opponents (20-30 BB)?",
                "options": [
                    "Open aggressively and apply maximum pressure, knowing medium stacks face immense risk premiums and must fold everything except top premium hands.",
                    "Play extremely tight and fold until the bubble bursts.",
                    "Limp into every pot to see cheap flops.",
                    "Only open AA and KK.",
                ],
                "correct_index": 0,
                "explanation": "Correct! As the chip leader with coverage advantage, you exploit medium stacks' survival imperative by stealing blinds with near-impunity.",
                "remediation": "Medium stacks cannot afford to risk elimination on the bubble, making them ideal targets for aggressive blind stealing by chip leaders.",
            },
            content_markdown="Test your grasp of bubble leverage and coverage advantage.",
            key_takeaway="Chip leaders must aggressively exploit the risk aversion of medium stacks on the bubble.",
        ),
        InteractiveLessonStep(
            step_number=5,
            title="Recap: Bubble & Final Table Strategy",
            step_type="RECAP",
            component_type="lesson_completion_summary",
            component_props={
                "xpEarned": 25,
                "masteryKey": "tournament.bubble",
                "conceptsLearned": [
                    "The bubble creates extreme risk aversion for non-leaders",
                    "Coverage advantage allows chip leaders to bully medium stacks",
                    "Pay jumps reward laddering and avoiding mutual destruction",
                    "Match aggression level directly to table stack distribution",
                ],
            },
            content_markdown="Superb! You now understand the psychological and mathematical dynamics of high-stakes tournament finals.",
            key_takeaway="Mastering bubble dynamics and pay jump laddering turns tournament participants into champions.",
        ),
    ],
)

LESSON_C6_CHECKPOINT = CourseLesson(
    id="lesson.c6.checkpoint",
    path_id="path.icm_final_table",
    chapter_id="chap_6_tournament",
    unit_id="unit_6_2_icm_dynamics",
    title="Chapter 6 Checkpoint: Tournament Champion",
    summary="Validate mastery of tournament formats, push/fold charts, ICM risk premiums, bubble play, and final-table pay jumps.",
    skill_id="checkpoint.chapter_6",
    difficulty_level="ELITE",
    estimated_minutes=6,
    prerequisite_lesson_ids=["lesson.tourn.bubble_and_payjumps"],
    is_unit_challenge=True,
    is_chapter_checkpoint=True,
    steps=[
        InteractiveLessonStep(
            step_number=1,
            title="Tournament Strategy Capstone",
            step_type="EXPLAIN",
            content_markdown=(
                "### 🏆 Chapter 6 Capstone Evaluation\n\n"
                "You have traversed the complete tournament strategic framework:\n\n"
                "1. **Formats & Stack Pressure**: Escalating blinds and the 2.5 BB dead ante pot.\n"
                "2. **Push/Fold Strategy**: Unexploitable all-in charts under 15 BB.\n"
                "3. **ICM & Risk Premiums**: The non-linear value of tournament chips ($EV vs Chip-EV).\n"
                "4. **Bubble Exploitation**: Coverage advantage and laddering pay jumps.\n\n"
                "Answer the capstone question to claim the ultimate **Tournament Champion** certification!"
            ),
            key_takeaway="Tournament strategy synthesizes push/fold precision with elite ICM risk-premium awareness.",
        ),
        InteractiveLessonStep(
            step_number=2,
            title="Capstone Challenge: The Final Table Call",
            step_type="CHECK",
            component_type="knowledge_check",
            quiz_question={
                "question": "3 players remain on a final table. Chip leader shoves. You are 2nd in chips with 30 BB, and the 3rd player has only 2 BB. You hold A♠ K♦. Pot odds offer positive Chip-EV. Why is calling an all-in a catastrophic mistake under ICM?",
                "options": [
                    "Because the 2 BB stack is virtually guaranteed to bust out in 3rd place on the very next hand, guaranteeing you 2nd place prize money without risking your 30 BB stack.",
                    "Because AK is an unplayable hand on final tables.",
                    "Because the tournament director will penalize you.",
                    "Because Chip-EV always overrides ICM.",
                ],
                "correct_index": 0,
                "explanation": "Correct! With a 2 BB micro-stack guaranteed to bust immediately, risking elimination against the chip leader commits ICM suicide. Folding locks in a massive guaranteed pay jump!",
                "remediation": "When a micro-stack is about to bust, medium stacks must avoid coin flips against larger stacks to ladder up guaranteed prize money.",
            },
            content_markdown="Solve this final table ICM laddering dilemma.",
            key_takeaway="Never risk elimination against a larger stack when a micro-stack is about to bust out.",
        ),
        InteractiveLessonStep(
            step_number=3,
            title="Curriculum Complete: Certified Tournament Champion!",
            step_type="COMMIT",
            component_type="chapter_checkpoint",
            component_props={
                "chapterNumber": 6,
                "chapterTitle": "Tournament Strategy",
                "badgeName": "Tournament Champion",
                "xpEarned": 100,
                "nextChapterId": None,
            },
            content_markdown=(
                "### 🏆 Curriculum Mastered: Poker Champion!\n\n"
                "**Congratulations!** You have completed the complete Pokeria Texas Hold'em curriculum:\n\n"
                "- **Chapter 1: The Poker Table** (Rules, Hand Rankings, Positions, Blinds, Stacks)\n"
                "- **Chapter 2: Understanding Ranges** (13x13 Matrix, Combos, Blockers, Charts)\n"
                "- **Chapter 3: Poker Mathematics** (Pot Odds, Outs Rule of 2/4, EV, Implied Odds)\n"
                "- **Chapter 4: Preflop Strategy** (RFI by Seat, Sizing, Blind Defense, 3-Betting, Stacks)\n"
                "- **Chapter 5: Postflop Strategy** (Textures, Range/Nut Advantage, C-Bets, Barrels, Rivers)\n"
                "- **Chapter 6: Tournament Strategy** (Stack Pressure, Push/Fold, ICM, Bubble Exploitation)\n\n"
                "You now hold a complete, theory-first, mathematically sound foundation for Texas Hold'em mastery!"
            ),
            key_takeaway="Complete Pokeria Curriculum Mastered! Certified from Beginner to Tournament Champion.",
        ),
    ],
)


# ============================================================================
# MASTER INVENTORY: ALL 32 CURRICULUM LESSONS
# ============================================================================

ALL_NEW_COURSE_LESSONS: list[CourseLesson] = [
    # Chapter 1 (6 lessons)
    LESSON_C1_U1_RULES,
    LESSON_C1_U2_RANKINGS,
    LESSON_C1_U3_POSITIONS,
    LESSON_C1_U4_BLINDS,
    LESSON_C1_U5_STACKS,
    LESSON_C1_CHALLENGE,
    # Chapter 2 (6 lessons)
    LESSON_C2_U1_WHAT_IS_RANGE,
    LESSON_C2_U2_READ_RANGE,
    LESSON_C2_U3_COMBOS,
    LESSON_C2_U4_EXPANSION,
    LESSON_C2_U5_CHARTS,
    LESSON_C2_CHALLENGE,
    # Chapter 3 (4 lessons)
    LESSON_C3_U1_POT_ODDS,
    LESSON_C3_U2_OUTS_EV,
    LESSON_C3_U3_IMPLIED_ODDS,
    LESSON_C3_CHECKPOINT,
    # Chapter 4 (6 lessons)
    LESSON_C4_U1_POSITION,
    LESSON_C4_U1_BTN_RFI,
    LESSON_C4_U2_FACING_OPENS,
    LESSON_C4_U2_3BET,
    LESSON_C4_U3_STACK_DEPTH,
    LESSON_C4_CHECKPOINT,
    # Chapter 5 (5 lessons)
    LESSON_C5_U1_TEXTURES,
    LESSON_C5_U1_CBET,
    LESSON_C5_U2_TURN_BARREL,
    LESSON_C5_U2_RIVER_BLUFFCATCH,
    LESSON_C5_CHECKPOINT,
    # Chapter 6 (5 lessons)
    LESSON_C6_U1_FORMATS,
    LESSON_C6_U1_PUSHFOLD,
    LESSON_C6_U2_ICM,
    LESSON_C6_U2_BUBBLE_PAYJUMPS,
    LESSON_C6_CHECKPOINT,
]
