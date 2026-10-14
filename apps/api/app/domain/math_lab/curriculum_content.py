"""Authored Curriculum Lessons for Poker Math Lab.

Implements the 5-stage pedagogical model across all 16 curriculum modules:
1. Stage 1: Understand (Definition, why it matters, derivation, misconceptions)
2. Stage 2: Calculate (Formula, step-by-step substitution, exact calculation)
3. Stage 3: Estimate (Mental approximations, safe shortcut rules)
4. Stage 4: Apply (Unprompted situation, parameter discovery, decision interpretation)
5. Stage 5: Execute Quickly (Speed targets, time-constrained pattern recognition)
"""

from __future__ import annotations

from app.domain.math_lab.models import MathLabLesson, MathLabLessonStep, PedagogicalStage

LESSONS: dict[str, MathLabLesson] = {
    "mod_01_arithmetic": MathLabLesson(
        module_id="mod_01_arithmetic",
        title="Poker Arithmetic Foundations",
        summary="Master conversions between odds ratios, fractions, percentages, and big blind metrics.",
        steps=[
            MathLabLessonStep(
                step_number=1,
                stage=PedagogicalStage.STAGE_1_UNDERSTAND,
                title="Stage 1: Understanding Odds vs Probabilities",
                content_markdown=(
                    "In poker, odds and probabilities express the exact same mathematical reality in two different languages.\n\n"
                    "• **Probability (Percentage)**: The fraction of times an event occurs out of *all possible outcomes*. "
                    "For example, a 25% chance means the event happens 1 out of 4 times total.\n"
                    "• **Odds Against**: The ratio of *unfavorable outcomes* to *favorable outcomes*. "
                    "If an event happens 1 time and fails 3 times, the odds against are **3 to 1 (3:1)**.\n\n"
                    "Poker players frequently switch between odds and percentages when comparing pot sizes to card probabilities."
                ),
                common_misconception="Thinking that 3:1 odds means 1/3 (33.3%). 3:1 means 1 success for every 3 failures, making 4 total trials (1/4 = 25%)!",
            ),
            MathLabLessonStep(
                step_number=2,
                stage=PedagogicalStage.STAGE_2_CALCULATE,
                title="Stage 2: Calculating Exact Conversions",
                content_markdown=(
                    "Follow these exact mathematical transformations:\n\n"
                    "1. **Odds Ratio (X:1) to Percentage**: $P = \\frac{1}{X + 1} \\times 100\\%$\n"
                    "2. **Percentage to Odds Ratio**: $X = \\frac{100 - P}{P}$\n"
                    "3. **Stack in BB**: $\\text{Stack in BB} = \\frac{\\text{Chip Count}}{\\text{Big Blind Size}}$"
                ),
                formula_box="P = 1 / (X + 1) * 100%  <===>  X:1 = (100 - P) / P",
                worked_example={
                    "problem": "Convert 4:1 odds against into a percentage, and convert $1,750 chips in a $25/$50 game into BBs.",
                    "step_1": "Odds to %: X = 4. P = 1 / (4 + 1) = 1/5 = 20.0%.",
                    "step_2": "Chips to BB: Big Blind is 50. 1,750 / 50 = 35.0 Big Blinds.",
                    "result": "20.0% and 35.0 BB",
                },
            ),
            MathLabLessonStep(
                step_number=3,
                stage=PedagogicalStage.STAGE_3_ESTIMATE,
                title="Stage 3: Mental Approximation Shortcuts",
                content_markdown=(
                    "At the tables, you do not have time for long division. Memorize these anchor points:\n\n"
                    "• $1:1 \\to 50.0\\%$\n"
                    "• $2:1 \\to 33.3\\%$\n"
                    "• $3:1 \\to 25.0\\%$\n"
                    "• $4:1 \\to 20.0\\%$\n"
                    "• $5:1 \\to 16.7\\%$\n"
                    "• $9:1 \\to 10.0\\%$\n\n"
                    "If you are getting 3.5:1, estimate halfway between 3:1 (25%) and 4:1 (20%) $\\approx$ 22% (exact is 22.2%)."
                ),
                mental_shortcut="Add 1 to the odds number, then divide 100 by that sum: 100 / (X + 1).",
            ),
            MathLabLessonStep(
                step_number=4,
                stage=PedagogicalStage.STAGE_4_APPLY,
                title="Stage 4: Applied Decision Context",
                content_markdown=(
                    "A player announces: 'You're getting 2.5 to 1 on a call.'\n"
                    "To determine whether calling is profitable, you must immediately convert that to required equity:\n"
                    "$$\\text{Required Equity} = \\frac{1}{2.5 + 1} = \\frac{1}{3.5} = 28.6\\%$$\n"
                    "If your estimated hand equity is 32%, you know immediately that the call is positive expected value."
                ),
            ),
            MathLabLessonStep(
                step_number=5,
                stage=PedagogicalStage.STAGE_5_EXECUTE_QUICKLY,
                title="Stage 5: Speed Execution Benchmark",
                content_markdown=(
                    "**Speed Target:** 3–5 seconds per conversion.\n\n"
                    "When playing online or live, this conversion must be instinctive reflex. "
                    "Practice converting bet-to-pot fractions into percentages without hesitating."
                ),
            ),
        ],
    ),
    "mod_02_pot_odds": MathLabLesson(
        module_id="mod_02_pot_odds",
        title="Pot Odds & Break-Even Equity",
        summary="Determine the exact minimum equity required to call any bet size.",
        steps=[
            MathLabLessonStep(
                step_number=1,
                stage=PedagogicalStage.STAGE_1_UNDERSTAND,
                title="Stage 1: The Core Concept of Pot Odds",
                content_markdown=(
                    "Pot odds represent the price the pot is offering you to call a bet. "
                    "It answers the fundamental question: **'What percentage of the time must I win this pot for my call to break even?'**\n\n"
                    "The break-even equity is the minimum win percentage that yields exactly $0 in chip expectation. "
                    "If your equity is greater than your pot odds requirement, calling is profitable (+EV). If it is less, calling loses chips (-EV)."
                ),
                common_misconception="Forgetting that the pot before your call includes the opponent's new bet! The pot is not what was there on the previous street.",
            ),
            MathLabLessonStep(
                step_number=2,
                stage=PedagogicalStage.STAGE_2_CALCULATE,
                title="Stage 2: Calculating Exact Pot Odds",
                content_markdown=(
                    "The universal formula for required equity when facing a terminal bet is:\n\n"
                    "$$\\text{Required Equity} = \\frac{\\text{Call Amount}}{\\text{Pot Before Call} + \\text{Call Amount}}$$\n\n"
                    "Where $\\text{Pot Before Call} = \\text{Starting Pot} + \\text{Opponent Bet}$."
                ),
                formula_box="Required Equity (%) = (Call / (Pot Before Call + Call)) * 100",
                worked_example={
                    "problem": "Contrast both standard scenarios:\n• Scenario A: Pot is 150 before an opponent bets 50. What is your required calling equity to call 50?\n• Scenario B: Pot facing your call is 150 (already including the opponent's bet). What is your required calling equity to call 50?",
                    "step_1": "Scenario A: Pot Before Bet = 150. Opponent Bet = 50. Pot Facing Call = 150 + 50 = 200. Total Final Pot = 200 + 50 = 250. Required Equity = 50 / 250 = 20.0%.",
                    "step_2": "Scenario B: Pot Facing Call = 150. Call Amount = 50. Total Final Pot = 150 + 50 = 200. Required Equity = 50 / 200 = 25.0%.",
                    "result": "Scenario A = 20.0% | Scenario B = 25.0%",
                },
            ),
            MathLabLessonStep(
                step_number=3,
                stage=PedagogicalStage.STAGE_3_ESTIMATE,
                title="Stage 3: Memorizing Standard Bet Sizing Hurdles",
                content_markdown=(
                    "Every standard bet fraction corresponds to a fixed required equity percentage. Commit these to memory:\n\n"
                    "• **1/3 Pot Bet** $\\to$ Requires **20.0%**\n"
                    "• **1/2 Pot Bet** $\\to$ Requires **25.0%**\n"
                    "• **2/3 Pot Bet** $\\to$ Requires **28.6%**\n"
                    "• **3/4 Pot Bet** $\\to$ Requires **30.0%**\n"
                    "• **Pot-Sized Bet** $\\to$ Requires **33.3%**\n"
                    "• **1.5x Overbet** $\\to$ Requires **37.5%**\n"
                    "• **2x Overbet** $\\to$ Requires **40.0%**"
                ),
                mental_shortcut="Facing a half-pot bet? Instant reflex: 25%. Facing a pot-sized bet? Instant reflex: 33%.",
            ),
            MathLabLessonStep(
                step_number=4,
                stage=PedagogicalStage.STAGE_4_APPLY,
                title="Stage 4: Multiway & Dead Money Applications",
                content_markdown=(
                    "When other players have called before you, their calls represent **dead money** that sweetens your pot odds!\n\n"
                    "Example: Pot is 100. Player A bets 50. Player B calls 50. You must call 50.\n"
                    "• Pot before your call = $100 + 50 + 50 = 200$.\n"
                    "• Total final pot = $200 + 50 = 250$.\n"
                    "• Required Equity = $50 / 250 = 20.0\\%$ (instead of 25.0% if it were heads-up)!"
                ),
            ),
            MathLabLessonStep(
                step_number=5,
                stage=PedagogicalStage.STAGE_5_EXECUTE_QUICKLY,
                title="Stage 5: Speed Target & Reflex Training",
                content_markdown=(
                    "**Target:** Under 5 seconds to identify the required equity.\n\n"
                    "See the bet $\\to$ Identify the fraction of pot $\\to$ State the required equity percentage."
                ),
            ),
        ],
    ),
    "mod_03_outs_draws": MathLabLesson(
        module_id="mod_03_outs_draws",
        title="Outs, Draws & Card Improvement",
        summary="Count clean outs accurately, eliminate dirty outs, and master the Rule of 2 and 4.",
        steps=[
            MathLabLessonStep(
                step_number=1,
                stage=PedagogicalStage.STAGE_1_UNDERSTAND,
                title="Stage 1: Clean vs Dirty Outs and Redraws",
                content_markdown=(
                    "An **out** is an unseen card in the deck that improves your holding to what you expect will be the winning hand.\n\n"
                    "• **Clean Outs**: Cards that improve you and give you the undisputed best hand.\n"
                    "• **Dirty Outs**: Cards that complete your draw but simultaneously give an opponent an even stronger hand (e.g. hitting your straight card when it also completes a flush for your opponent).\n"
                    "• **Counterfeiting**: When a board pair invalidates your two-pair advantage."
                ),
                common_misconception="Counting dirty outs as full outs, or counting the flush card twice when you hold both a straight and flush draw.",
            ),
            MathLabLessonStep(
                step_number=2,
                stage=PedagogicalStage.STAGE_2_CALCULATE,
                title="Stage 2: Exact Probability vs The Rule of 2 and 4",
                content_markdown=(
                    "Exact combinatorial math on the flop (2 cards to come out of 47 unknown cards):\n"
                    "$$P(\\text{hit by river}) = 1 - \\frac{(47 - \\text{Outs}) \\times (46 - \\text{Outs})}{47 \\times 46}$$\n\n"
                    "On the turn (1 card to come out of 46 unknown cards):\n"
                    "$$P(\\text{hit on river}) = \\frac{\\text{Outs}}{46}$$\n\n"
                    "**The Rule of 2 and 4 Approximation:**\n"
                    "• On turn: $\\text{Outs} \\times 2$\n"
                    "• On flop: $\\text{Outs} \\times 4$. For $\\text{Outs} > 8$, subtract $(\\text{Outs} - 8)$."
                ),
                formula_box="Flop to River: (Outs * 4) - (Outs - 8) if Outs > 8 | Turn to River: Outs * 2.17%",
                worked_example={
                    "problem": "Hero has a 9-out flush draw on the flop. Calculate both approximate and exact probability.",
                    "step_1": "Rule of 4: (9 * 4) - (9 - 8) = 36 - 1 = 35.0%.",
                    "step_2": "Exact combinatorial calculation: 1 - (38 * 37) / (47 * 46) = 1 - (1406 / 2162) = 1 - 0.6503 = 34.97%.",
                    "result": "Rule of 4 yields 35.0% vs exact 34.97% — extremely accurate!",
                },
            ),
            MathLabLessonStep(
                step_number=3,
                stage=PedagogicalStage.STAGE_3_ESTIMATE,
                title="Stage 3: Standard Draw Out Benchmarks",
                content_markdown=(
                    "Memorize these canonical out counts:\n\n"
                    "• **Inside Straight Draw (Gutshot)**: 4 outs $\\to \\approx 8.5\\%$ turn, $\\approx 16.5\\%$ river\n"
                    "• **Open-Ended Straight Draw (OESD)**: 8 outs $\\to \\approx 17.4\\%$ turn, $\\approx 31.5\\%$ river\n"
                    "• **Flush Draw**: 9 outs $\\to \\approx 19.6\\%$ turn, $\\approx 35.0\\%$ river\n"
                    "• **Combo Draw (OESD + Flush Draw)**: 15 outs $\\to \\approx 32.6\\%$ turn, $\\approx 54.1\\%$ river\n"
                    "• **Two Overcards to Board**: 6 outs $\\to \\approx 13.0\\%$ turn, $\\approx 24.1\\%$ river"
                ),
                mental_shortcut="A monster 15-out combo draw on the flop is a mathematical favorite (> 54%) against a single made pair!",
            ),
            MathLabLessonStep(
                step_number=4,
                stage=PedagogicalStage.STAGE_4_APPLY,
                title="Stage 4: Discounting Compromised Outs",
                content_markdown=(
                    "Board is $K\\spades 9\\spades 4\\heartsuit$. You hold $J\\spades 10\\spades$ (open-ended straight flush draw).\n"
                    "• 9 spades for the flush.\n"
                    "• 3 non-spade Queens and 3 non-spade 8s for the straight.\n"
                    "• Total outs = $9 + 6 = 15$ clean outs!\n"
                    "However, if opponent already holds $A\\spades 2\\spades$, all your spade outs are DIRTY (they make a higher flush for opponent!). "
                    "Your true clean outs drop from 15 to only 6 straight outs! Always consider opponent range blockers."
                ),
            ),
            MathLabLessonStep(
                step_number=5,
                stage=PedagogicalStage.STAGE_5_EXECUTE_QUICKLY,
                title="Stage 5: Speed Counting Challenge",
                content_markdown=(
                    "**Speed Target:** Identify out count and draw percentage in under 4 seconds.\n\n"
                    "Spot the draw type $\\to$ State out count $\\to$ Multiply by 2 (turn) or 4 (flop)."
                ),
            ),
        ],
    ),
    "mod_04_equity_fundamentals": MathLabLesson(
        module_id="mod_04_equity_fundamentals",
        title="Equity Fundamentals",
        summary="Master showdown equity, ties, card removal, and classic hand-versus-hand matchups.",
        steps=[
            MathLabLessonStep(
                step_number=1,
                stage=PedagogicalStage.STAGE_1_UNDERSTAND,
                title="Stage 1: What is Showdown Equity?",
                content_markdown=(
                    "Showdown equity is your mathematical share of the pot if the hand is checked down to completion with no further betting.\n\n"
                    "$$\\text{Equity} = P(\\text{win}) + \\frac{P(\\text{tie})}{\\text{Number of Tied Players}}$$\n\n"
                    "Equity is NOT certainty. Having 70% equity means that over hundreds of trials you will win 70% of the pot, but on any single hand, you will either take down the entire pot or lose it completely."
                ),
                common_misconception="Believing that an 80% equity hand 'should never lose' or that losing three 75% equity spots in a row indicates a faulty simulator.",
            ),
            MathLabLessonStep(
                step_number=2,
                stage=PedagogicalStage.STAGE_2_CALCULATE,
                title="Stage 2: Preflop Matchup Baseline Anchors",
                content_markdown=(
                    "Learn these foundational heads-up preflop equity benchmarks:\n\n"
                    "1. **Pocket Pair vs Lower Pocket Pair** (e.g., $AA$ vs $KK$): $\\approx 81.5\\% - 82.5\\%$ vs $17.5\\% - 18.5\\%$\n"
                    "2. **Pocket Pair vs Two Overcards (Coin Flip)** (e.g., $JJ$ vs $AK$s): $\\approx 54\\% - 57\\%$ vs $43\\% - 46\\%$\n"
                    "3. **Two Overcards vs Two Undercards** (e.g., $AK$o vs $QJ$o): $\\approx 63\\%$ vs $37\\%$\n"
                    "4. **Dominated Hand (Shared Rank)** (e.g., $AK$o vs $AQ$o): $\\approx 73\\%$ vs $27\\%$\n"
                    "5. **Dominated Hand (Lower Pair/Kicker)** (e.g., $AK$o vs $A2$s): $\\approx 70\\%$ vs $30\\%$"
                ),
                formula_box="Pair vs Lower Pair: ~82/18 | Pair vs 2 Overcards: ~55/45 | Dominated Ace: ~73/27",
                worked_example={
                    "problem": "Hero pushes with A-K offsuit and is called by A-Q offsuit. What is Hero's approximate and exact equity?",
                    "step_1": "Shared Ace removes 2 Aces from the deck, leaving 3 Kings for Hero and 3 Queens for Villain.",
                    "step_2": "Because Hero dominates the kicker, Villain only wins when a Queen arrives without a King or on broadway flush/straight runouts.",
                    "result": "Hero holds 72.8% equity, Villain has 22.8% win and 4.4% split pot equity.",
                },
            ),
            MathLabLessonStep(
                step_number=3,
                stage=PedagogicalStage.STAGE_3_ESTIMATE,
                title="Stage 3: Blocker and Removal Effects",
                content_markdown=(
                    "Holding a card reduces the probability that other players hold that same rank.\n\n"
                    "• Holding an Ace reduces the available unpaired $AK$ combinations from $4 \\times 4 = 16$ down to $3 \\times 4 = 12$ combos (a 25% reduction!).\n"
                    "• Holding two Aces reduces $AA$ from 6 combos to $\\binom{2}{2} = 1$ combo (an 83% reduction!)."
                ),
                mental_shortcut="Card removal cuts pair combos in half (6 to 3) if you hold one card of that rank, and cuts unpaired combos by 25% (16 to 12).",
            ),
            MathLabLessonStep(
                step_number=4,
                stage=PedagogicalStage.STAGE_4_APPLY,
                title="Stage 4: Postflop Texture Shifts",
                content_markdown=(
                    "On the flop, equities can shift dramatically:\n"
                    "• Overpair vs Set: Overpair has only $\\approx 8-9\\%$ equity (needs running cards or two higher pair runouts).\n"
                    "• Top Pair Top Kicker vs Open-Ended Straight Draw + Flush Draw: The combo draw is actually a 55% favorite over top pair on the flop!"
                ),
            ),
            MathLabLessonStep(
                step_number=5,
                stage=PedagogicalStage.STAGE_5_EXECUTE_QUICKLY,
                title="Stage 5: Speed Recognition",
                content_markdown=(
                    "**Speed Target:** 3 seconds to recall equity archetype.\n\n"
                    "Pair vs Pair: 80/20. Coin flip: 55/45. Dominated: 70/30."
                ),
            ),
        ],
    ),
    "mod_05_equity_ranges": MathLabLesson(
        module_id="mod_05_equity_ranges",
        title="Equity Against Opponent Ranges",
        summary="Construct conditional opponent ranges and estimate equity against weighted distributions.",
        steps=[
            MathLabLessonStep(
                step_number=1,
                stage=PedagogicalStage.STAGE_1_UNDERSTAND,
                title="Stage 1: Ranges as Probability Distributions",
                content_markdown=(
                    "Except in rare showdown scenarios, you never know an opponent's exact two cards. "
                    "Opponents hold a **range** — a probability distribution across all possible two-card combinations they could have taken this line with.\n\n"
                    "Evaluating equity against a range means calculating your weighted average equity across every combination in that range."
                ),
                common_misconception="Putting an opponent on 'one specific hand' rather than the full spectrum of holdings they would play this way.",
            ),
            MathLabLessonStep(
                step_number=2,
                stage=PedagogicalStage.STAGE_2_CALCULATE,
                title="Stage 2: Weighted Range Equity Equation",
                content_markdown=(
                    "$$\\text{Equity}(\\text{Hero vs Range } R) = \\frac{\\sum_{c \\in R} w_c \\times \\text{Equity}(\\text{Hero}, c)}{\\sum_{c \\in R} w_c}$$\n\n"
                    "Where $w_c$ is the weight of combination $c$ (between 0.0 and 1.0)."
                ),
                formula_box="Average Equity = Sum(Combo Weight * Combo Equity) / Total Combinations",
                worked_example={
                    "problem": "Hero holds Ah Kh on a board of As 7d 2c. Villain's range is precisely 3 combos of 77 (set, 9% Hero eq) and 12 combos of AQo (top pair lower kicker, 85% Hero eq). What is Hero's equity?",
                    "step_1": "Total combos = 3 + 12 = 15 combos.",
                    "step_2": "Weighted equity sum = (3 * 0.09) + (12 * 0.85) = 0.27 + 10.20 = 10.47.",
                    "step_3": "Hero Equity = 10.47 / 15 = 69.8%.",
                    "result": "69.8% equity against Villain's range",
                },
            ),
            MathLabLessonStep(
                step_number=3,
                stage=PedagogicalStage.STAGE_3_ESTIMATE,
                title="Stage 3: Categorical Range Breakdown",
                content_markdown=(
                    "To estimate range equity quickly at the table, group the opponent's range into three buckets:\n"
                    "1. **Monsters (Ahead of you)**: (Sets, Two Pair)\n"
                    "2. **Hands You Beat**: (Weaker Top Pairs, Middle Pairs)\n"
                    "3. **Air / Draws**: (Gutshots, Flush Draws, Missed bluffs)\n\n"
                    "Estimate the combination count of each bucket to find the balance."
                ),
                mental_shortcut="Top pair with good kicker typically has 60-70% equity against a standard continuing range on dry boards, and 45-55% on coordinated dynamic boards.",
            ),
            MathLabLessonStep(
                step_number=4,
                stage=PedagogicalStage.STAGE_4_APPLY,
                title="Stage 4: Range Narrowing by Street",
                content_markdown=(
                    "As an opponent bets or raises on multiple streets, their range condenses toward polar or value-heavy extremes.\n\n"
                    "Calling a preflop open $\\to$ 25% of hands.\n"
                    "Calling a flop c-bet $\\to$ 12% of hands.\n"
                    "Raising the turn $\\to$ 3% of hands (mostly sets, monster draws, and bluffs).\n"
                    "Your equity must be re-evaluated against the *filtered* range on every street!"
                ),
            ),
            MathLabLessonStep(
                step_number=5,
                stage=PedagogicalStage.STAGE_5_EXECUTE_QUICKLY,
                title="Stage 5: Speed Range Estimation",
                content_markdown=(
                    "**Speed Target:** Estimate equity vs range within +/- 5% in under 8 seconds."
                ),
            ),
        ],
    ),
    "mod_06_equity_realization": MathLabLesson(
        module_id="mod_06_equity_realization",
        title="Equity Realization (EQR)",
        summary="Understand why raw showdown equity does not equal expected winnings when future betting remains.",
        steps=[
            MathLabLessonStep(
                step_number=1,
                stage=PedagogicalStage.STAGE_1_UNDERSTAND,
                title="Stage 1: Raw Equity vs Realized Equity",
                content_markdown=(
                    "Raw equity assumes cards are turned face up and run out to the river with zero betting. "
                    "In real poker, **future betting allows players to fold hands that had equity, extract extra chips when ahead, or get bluffed off the best hand**.\n\n"
                    "$$\\text{Realized Value} = \\text{Raw Equity} \\times \\text{EQR}$$\n\n"
                    "• Hands in position typically have $\\text{EQR} > 1.0$ (they realize MORE than their raw equity).\n"
                    "• Hands out of position, or easily dominated hands, often have $\\text{EQR} < 0.70$."
                ),
                common_misconception="Calling out of position on the flop because 'pot odds give me a call' without factoring that you will be forced to fold on the turn when you miss.",
            ),
            MathLabLessonStep(
                step_number=2,
                stage=PedagogicalStage.STAGE_2_CALCULATE,
                title="Stage 2: Quantifying Realization Factors",
                content_markdown=(
                    "Key strategic forces governing EQR:\n"
                    "1. **Position**: IP players check behind to see free rivers and control pot size.\n"
                    "2. **Playability / Nut Potential**: Suited connectors and pocket pairs realize well because they make nutty hands that win big pots.\n"
                    "3. **Reverse Implied Odds**: Weak offsuit broadways (e.g. $K7$o, $Q8$o) realize poorly because when they pair up, they win small pots and lose large pots."
                ),
                formula_box="EQR = Realized Pot Share / Raw Showdown Equity",
                worked_example={
                    "problem": "Hero in Big Blind with 86s has 38% raw equity facing a button c-bet. Due to positional disadvantage, Hero's estimated EQR is 75%. What is Hero's realized equity?",
                    "step_1": "Realized Equity = 0.38 * 0.75 = 28.5%.",
                    "step_2": "If the pot odds require 26%, Hero can call; but if pot odds require 30%, calling is -EV despite raw equity being 38%!",
                    "result": "Realized Equity = 28.5%",
                },
            ),
            MathLabLessonStep(
                step_number=3,
                stage=PedagogicalStage.STAGE_3_ESTIMATE,
                title="Stage 3: Position Heuristics",
                content_markdown=(
                    "• In Position (IP) vs Out of Position (OOP): Adds $\\approx 15\\% - 25\\%$ to equity realization.\n"
                    "• Deep Stacks (100+ BB): Nutted draws gain EQR; weak top pairs lose EQR.\n"
                    "• Shallow Stacks (SPR < 2): Raw equity dictates decisions because players cannot be easily forced off hands."
                ),
                mental_shortcut="Low SPR (< 2) -> Raw equity matters most. High SPR (> 8) -> Position and nut-potential dominate.",
            ),
            MathLabLessonStep(
                step_number=4,
                stage=PedagogicalStage.STAGE_4_APPLY,
                title="Stage 4: Defending the Big Blind",
                content_markdown=(
                    "In the Big Blind, you get excellent preflop pot odds (often needing only 20-25% equity to call). "
                    "However, with trash offsuit hands (like 94o), your EQR is so low (< 50%) that calling remains unplayable -EV. "
                    "Never call preflop solely because of raw pot odds if your hand cannot realize postflop."
                ),
            ),
            MathLabLessonStep(
                step_number=5,
                stage=PedagogicalStage.STAGE_5_EXECUTE_QUICKLY,
                title="Stage 5: Speed Judgment",
                content_markdown=(
                    "**Speed Target:** Immediately downgrade raw equity by 20-30% for weak OOP hands under 5 seconds."
                ),
            ),
        ],
    ),
    "mod_07_call_ev": MathLabLesson(
        module_id="mod_07_call_ev",
        title="Call Expected Value (Call EV)",
        summary="Calculate exact chip gains or losses when calling river bets and terminal all-ins.",
        steps=[
            MathLabLessonStep(
                step_number=1,
                stage=PedagogicalStage.STAGE_1_UNDERSTAND,
                title="Stage 1: Sunk Costs & The Baseline of Folding",
                content_markdown=(
                    "In game theory and poker mathematics, **prior chip contributions are sunk costs**.\n\n"
                    "The chips currently in the pot belong to the pot, not to you. At the moment you face a bet:\n"
                    "• **Folding** has an expected value of **exactly $0.00** relative to this decision point.\n"
                    "• **Calling** has an expected value equal to your equity share of the final pot minus your call cost.\n\n"
                    "If $\\text{EV(Call)} > 0$, calling is mathematically superior to folding, even if your net profit on the entire hand is negative!"
                ),
                common_misconception="Subtracting previous streets' bets from your call EV. Decisions must be evaluated from the current node forward!",
            ),
            MathLabLessonStep(
                step_number=2,
                stage=PedagogicalStage.STAGE_2_CALCULATE,
                title="Stage 2: The Exact Call EV Equation",
                content_markdown=(
                    "$$\\text{EV(Call)} = [\\text{Equity} \\times (\\text{Pot Before Call} + \\text{Call})] - \\text{Call}$$\n\n"
                    "Alternatively, written in terms of win/loss outcomes:\n"
                    "$$\\text{EV(Call)} = [P(\\text{win}) \\times \\text{Net Win}] - [P(\\text{lose}) \\times \\text{Call}]$$\n"
                    "Where $\\text{Net Win} = \\text{Pot Before Call}$."
                ),
                formula_box="EV(Call) = (Equity * Final Pot) - Call Amount",
                worked_example={
                    "problem": "Pot is 400. Villain bets 200 all-in on river. Hero estimates 35% equity. What is Hero's call EV?",
                    "step_1": "Pot before call = 400 + 200 = 600 chips.",
                    "step_2": "Final pot after Hero calls = 600 + 200 = 800 chips.",
                    "step_3": "Expected pot return: 0.35 * 800 = 280 chips.",
                    "step_4": "Net EV: 280 - 200 = +80 chips.",
                    "result": "+80 chips (or +80 / Big Blind in BB)",
                },
            ),
            MathLabLessonStep(
                step_number=3,
                stage=PedagogicalStage.STAGE_3_ESTIMATE,
                title="Stage 3: Delta Shortcut for Fast Calculation",
                content_markdown=(
                    "Instead of multiplying full pot numbers, compute the **Equity Delta**:\n\n"
                    "$$\\Delta = \\text{Your Equity} - \\text{Pot Odds Required Equity}$$\n"
                    "$$\\text{EV(Call)} = \\Delta \\times \\text{Final Pot}$$\n\n"
                    "Example: Pot odds need 25%. You have 30% equity ($\\Delta = +5\\%$). Final pot is 800.\n"
                    "$\\text{EV} = +0.05 \\times 800 = +40\\text{ chips}$!"
                ),
                mental_shortcut="Delta% * Final Pot = Instant EV calculation in under 3 seconds!",
            ),
            MathLabLessonStep(
                step_number=4,
                stage=PedagogicalStage.STAGE_4_APPLY,
                title="Stage 4: Factoring in Ties and Multiway Pots",
                content_markdown=(
                    "In split pots, each tied player receives their proportional fraction of the pot:\n"
                    "$$\\text{Equity} = P(\\text{sole win}) + \\frac{P(\\text{tie})}{2}$$\n\n"
                    "If you face two opponents in an all-in and have 40% equity against their combined holdings, "
                    "in a final pot of 1,500 where you called 400:\n"
                    "$$\\text{EV} = (0.40 \\times 1,500) - 400 = 600 - 400 = +200\\text{ chips}!$$"
                ),
            ),
            MathLabLessonStep(
                step_number=5,
                stage=PedagogicalStage.STAGE_5_EXECUTE_QUICKLY,
                title="Stage 5: Speed Target",
                content_markdown=(
                    "**Speed Target:** 5 seconds to calculate call EV.\n\n"
                    "Identify pot odds $\\to$ Calculate delta from your equity $\\to$ Multiply by total pot."
                ),
            ),
        ],
    ),
    "mod_08_bluff_ev": MathLabLesson(
        module_id="mod_08_bluff_ev",
        title="Bluff EV & Fold Equity",
        summary="Calculate bluff profitability, Alpha break-even fold percentages, and MDF defensive benchmarks.",
        steps=[
            MathLabLessonStep(
                step_number=1,
                stage=PedagogicalStage.STAGE_1_UNDERSTAND,
                title="Stage 1: Pure Bluffing and the Mechanics of Alpha",
                content_markdown=(
                    "A **pure bluff** is a bet made with a hand that has 0% chance of winning if called.\n\n"
                    "A pure bluff relies 100% on **fold equity** — the probability that opponents fold their holdings. "
                    "The break-even fold frequency (called **Alpha**) is the exact percentage of time your opponent must fold "
                    "for your bluff to have an expected value of $\\ge 0$ chips."
                ),
                common_misconception="Thinking that because opponent calls 60% of the time, betting half pot is unprofitable. For a half-pot bet, you only need 33.3% folds!",
            ),
            MathLabLessonStep(
                step_number=2,
                stage=PedagogicalStage.STAGE_2_CALCULATE,
                title="Stage 2: Calculating Alpha and Bluff EV",
                content_markdown=(
                    "$$\\text{Alpha} = \\frac{\\text{Bet Amount}}{\\text{Pot Before Bet} + \\text{Bet Amount}}$$\n\n"
                    "Full Expected Value formula for a pure bluff:\n"
                    "$$\\text{EV(Bluff)} = [f \\times \\text{Pot}] - [(1 - f) \\times \\text{Bet}]$$\n"
                    "Where $f$ is the probability the opponent folds."
                ),
                formula_box="Alpha (%) = (Bet / (Pot + Bet)) * 100 | EV = f * Pot - (1 - f) * Bet",
                worked_example={
                    "problem": "Pot is 200. You bet 100 on the river as a pure bluff. Villain folds 45% of the time. What is Alpha and what is your EV?",
                    "step_1": "Alpha = 100 / (200 + 100) = 100 / 300 = 33.3%.",
                    "step_2": "Because Villain folds 45% > 33.3%, the bluff is profitable!",
                    "step_3": "EV = (0.45 * 200) - (0.55 * 100) = 90 - 55 = +35 chips.",
                    "result": "Alpha = 33.3%, EV = +35 chips",
                },
            ),
            MathLabLessonStep(
                step_number=3,
                stage=PedagogicalStage.STAGE_3_ESTIMATE,
                title="Stage 3: Minimum Defense Frequency (MDF)",
                content_markdown=(
                    "Minimum Defense Frequency is the mathematical inverse of Alpha:\n\n"
                    "$$\\text{MDF} = 1 - \\text{Alpha} = \\frac{\\text{Pot}}{\\text{Pot} + \\text{Bet}}$$\n\n"
                    "MDF represents the percentage of range a defender MUST continue with to prevent a pure bluff from auto-profiting. "
                    "If the defender continues less than MDF, the bettor can profitably bluff with any two random cards!"
                ),
                mental_shortcut="Bet 1/2 pot -> Opponent needs 33.3% folds -> Defender must defend 66.7% (MDF).",
            ),
            MathLabLessonStep(
                step_number=4,
                stage=PedagogicalStage.STAGE_4_APPLY,
                title="Stage 4: Bluff Blockers & Card Removal",
                content_markdown=(
                    "The best bluffs hold **blockers** to the opponent's calling range, and unblock their folding range!\n\n"
                    "Example: On a board of $Ks 9s 4h 2d 7c$, holding $As$ as a bluff is powerful "
                    "because it physically blocks $As Ks$, $As 9s$, and top pairs with top kickers, increasing opponent's fold frequency by 10-15%!"
                ),
            ),
            MathLabLessonStep(
                step_number=5,
                stage=PedagogicalStage.STAGE_5_EXECUTE_QUICKLY,
                title="Stage 5: Speed Target",
                content_markdown=(
                    "**Speed Target:** 3 seconds to recall Alpha for standard bet sizes.\n\n"
                    "1/3 pot -> 25% | 1/2 pot -> 33% | 2/3 pot -> 40% | Pot -> 50%."
                ),
            ),
        ],
    ),
    "mod_09_semi_bluff": MathLabLesson(
        module_id="mod_09_semi_bluff",
        title="Semi-Bluff EV",
        summary="Combine fold equity with back-up showdown equity to evaluate flop and turn bets and raises.",
        steps=[
            MathLabLessonStep(
                step_number=1,
                stage=PedagogicalStage.STAGE_1_UNDERSTAND,
                title="Stage 1: The Dual Engine of Semi-Bluffing",
                content_markdown=(
                    "A **semi-bluff** is a bet or raise made with a drawing hand that is currently not the best hand, "
                    "but has realistic potential to improve to the winning hand if called.\n\n"
                    "Semi-bluffing has two distinct avenues to win:\n"
                    "1. Opponents fold immediately (collecting the pot via fold equity).\n"
                    "2. Opponents call, but you hit your out on a subsequent street (winning at showdown)."
                ),
                common_misconception="Treating semi-bluffs as pure bluffs or assuming you must have huge fold equity. Even 20% fold equity can make a draw enormously profitable.",
            ),
            MathLabLessonStep(
                step_number=2,
                stage=PedagogicalStage.STAGE_2_CALCULATE,
                title="Stage 2: The Semi-Bluff EV Formula",
                content_markdown=(
                    "Under a simplified model where opponents only fold or call (no raise):\n\n"
                    "$$\\text{EV} = [P(\\text{fold}) \\times \\text{Pot}] + [P(\\text{call}) \\times ((\\text{Eq} \\times \\text{FinalPot}) - \\text{Bet})]$$\n\n"
                    "Where $\\text{FinalPot} = \\text{Pot} + (2 \\times \\text{Bet})$."
                ),
                formula_box="EV = (f * Pot) + ((1 - f) * ((Eq * (Pot + 2*Bet)) - Bet))",
                worked_example={
                    "problem": "Pot is 100. Hero bets 60 with a flush draw (35% equity when called). Villain folds 30% of the time. What is EV?",
                    "step_1": "Fold outcome: 0.30 * 100 = +30 chips.",
                    "step_2": "Called pot = 100 + 120 = 220 chips.",
                    "step_3": "Called net win = (0.35 * 220) - 60 = 77 - 60 = +17 chips.",
                    "step_4": "Called outcome EV = 0.70 * (+17) = +11.9 chips.",
                    "step_5": "Total EV = 30 + 11.9 = +41.9 chips.",
                    "result": "+41.9 chips expectation",
                },
            ),
            MathLabLessonStep(
                step_number=3,
                stage=PedagogicalStage.STAGE_3_ESTIMATE,
                title="Stage 3: The Danger of Getting Raised",
                content_markdown=(
                    "When betting a draw non-all-in, beware the **raise branch**! "
                    "If an opponent raises you off your draw, you lose your entire bet plus all your card equity. "
                    "Against hyper-aggressive opponents who check-raise frequently, checking behind to realize equity is often higher EV than semi-bluffing."
                ),
                mental_shortcut="Shoving all-in eliminates the raise branch, perfectly locking in your fold equity and showdown equity!",
            ),
            MathLabLessonStep(
                step_number=4,
                stage=PedagogicalStage.STAGE_4_APPLY,
                title="Stage 4: Combo Draws as Aggressive Weapons",
                content_markdown=(
                    "With a 15-out combo draw (flush draw + straight draw, 54% equity), you don't even need fold equity! "
                    "Even if opponent calls 100% of the time, shoving is directly profitable on raw equity alone. "
                    "Any folds are purely an added bonus."
                ),
            ),
            MathLabLessonStep(
                step_number=5,
                stage=PedagogicalStage.STAGE_5_EXECUTE_QUICKLY,
                title="Stage 5: Speed Calculation",
                content_markdown=(
                    "**Speed Target:** Determine whether semi-bluff is +EV within 6 seconds."
                ),
            ),
        ],
    ),
    "mod_10_action_comparison": MathLabLesson(
        module_id="mod_10_action_comparison",
        title="Bet, Raise & Action EV Comparison",
        summary="Compare the expected values of Fold, Check, Call, Bet, and Raise to find the maximum-EV action.",
        steps=[
            MathLabLessonStep(
                step_number=1,
                stage=PedagogicalStage.STAGE_1_UNDERSTAND,
                title="Stage 1: Relative EV vs Absolute EV",
                content_markdown=(
                    "In poker, finding a +EV action is not enough — you must select the **highest expected value action** among all legal choices.\n\n"
                    "For example, calling might yield $+15$ chips, but raising might yield $+45$ chips. "
                    "Calling in that spot has an **EV regret** of $45 - 15 = 30$ chips! "
                    "Game theory optimal (GTO) play maximizes expectation across the entire game tree."
                ),
                common_misconception="Thinking that because calling is profitable (+EV), it must be the correct play.",
            ),
            MathLabLessonStep(
                step_number=2,
                stage=PedagogicalStage.STAGE_2_CALCULATE,
                title="Stage 2: Constructing Action Game Trees",
                content_markdown=(
                    "To compare actions rigorously, write out the explicit branch expectations:\n\n"
                    "• $\\text{EV(Fold)} = 0$\n"
                    "• $\\text{EV(Check)} = \\text{Showdown EV when checked through}$\n"
                    "• $\\text{EV(Call)} = (\\text{Equity} \\times \\text{FinalPot}) - \\text{Call}$\n"
                    "• $\\text{EV(Bet)} = [P(\\text{fold}) \\times \\text{Pot}] + [P(\\text{call}) \\times ((\\text{Eq}_{\\text{call}} \\times \\text{Pot}_{\\text{call}}) - \\text{Bet})]$"
                ),
                formula_box="Action Choice = argmax [ EV(Fold), EV(Call), EV(Bet), EV(Raise) ]",
                worked_example={
                    "problem": "River spot: Pot is 100. Check EV is +20 chips. Betting 50 gets called 40% (where Hero has 80% equity) and folded 60%. Which action is best?",
                    "step_1": "Betting EV when fold: 0.60 * 100 = +60 chips.",
                    "step_2": "Betting EV when called: Final pot is 100 + 50 + 50 = 200. Return = 0.80 * 200 - 50 = 160 - 50 = +110.",
                    "step_3": "Weighted called EV: 0.40 * 110 = +44 chips.",
                    "step_4": "Total EV(Bet) = 60 + 44 = +104 chips.",
                    "step_5": "Compare: EV(Bet) = +104 vs EV(Check) = +20. Betting is superior by +84 chips!",
                    "result": "Betting 50 is the highest EV action (+104 chips).",
                },
            ),
            MathLabLessonStep(
                step_number=3,
                stage=PedagogicalStage.STAGE_3_ESTIMATE,
                title="Stage 3: Sizing Elasticity",
                content_markdown=(
                    "Opponents' calling frequencies change with bet sizing:\n"
                    "• **Inelastic ranges**: Calling probability is nearly identical whether you bet 1/3 pot or 3/4 pot (e.g. they call with any pair). Use large sizing for value!\n"
                    "• **Elastic ranges**: Calling frequency drops steeply as bet size increases. Use smaller sizing for value and larger sizing for bluffs."
                ),
                mental_shortcut="Inelastic opponent -> Bet big for value, bet small with bluffs. Elastic opponent -> Bet polar.",
            ),
            MathLabLessonStep(
                step_number=4,
                stage=PedagogicalStage.STAGE_4_APPLY,
                title="Stage 4: Raise vs Call as a Bluff Catcher",
                content_markdown=(
                    "With a bluff catcher on the river, raising is almost always -EV because worse hands fold and better hands call. "
                    "However, with a blocker to the opponent's nut hands, turning your bluff catcher into a raise bluff can produce massive fold equity against their mid-strength value."
                ),
            ),
            MathLabLessonStep(
                step_number=5,
                stage=PedagogicalStage.STAGE_5_EXECUTE_QUICKLY,
                title="Stage 5: Speed Decision Ranking",
                content_markdown=(
                    "**Speed Target:** Rank 3 candidate actions by EV within 8 seconds."
                ),
            ),
        ],
    ),
    "mod_11_implied_odds": MathLabLesson(
        module_id="mod_11_implied_odds",
        title="Implied & Reverse Implied Odds",
        summary="Calculate future winnings required to justify drawing calls, and avoid reverse implied traps.",
        steps=[
            MathLabLessonStep(
                step_number=1,
                stage=PedagogicalStage.STAGE_1_UNDERSTAND,
                title="Stage 1: Implied Odds vs Immediate Pot Odds",
                content_markdown=(
                    "**Implied odds** account for additional chips you expect to win on future betting streets when you hit your draw.\n\n"
                    "If immediate pot odds are insufficient to justify calling, you can still call profitably if the implied odds from future streets make up the difference.\n\n"
                    "**Reverse Implied Odds**: The risk that when you hit your hand, you either win a negligible amount or lose a massive pot to an even higher holding (e.g. small flush vs ace-high flush)."
                ),
                common_misconception="Assuming an opponent will always pay off their entire remaining stack when you hit your card.",
            ),
            MathLabLessonStep(
                step_number=2,
                stage=PedagogicalStage.STAGE_2_CALCULATE,
                title="Stage 2: Calculating Required Future Chips",
                content_markdown=(
                    "To find the exact additional chips ($X$) you must win on future streets when you hit:\n\n"
                    "$$X = \\frac{\\text{Call Amount}}{\\text{Hit Probability}} - (\\text{Pot Before Call} + \\text{Call Amount})$$\n\n"
                    "If $X \\le \\text{Effective Remaining Stack} \\times P(\\text{payoff})$, the call is profitable."
                ),
                formula_box="Future Chips Needed = (Call / Probability) - Final Pot",
                worked_example={
                    "problem": "Turn spot: Pot is 100. Villain bets 50. Hero has a gutshot (4 outs, 8.7% chance to hit river). How much future money must Hero win on the river to break even?",
                    "step_1": "Call amount = 50. Final current pot = 100 + 50 + 50 = 200.",
                    "step_2": "Total required pot = 50 / (4/46) = 50 * (46/4) = 50 * 11.5 = 575 chips.",
                    "step_3": "Future chips needed = 575 - 200 = 375 chips.",
                    "step_4": "If effective stacks are only 200 chips, Hero CANNOT profitably call (stack constraint violates implied odds)!",
                    "result": "Hero needs to extract 375 additional chips on the river.",
                },
            ),
            MathLabLessonStep(
                step_number=3,
                stage=PedagogicalStage.STAGE_3_ESTIMATE,
                title="Stage 3: The Rule of Thumb for Set Mining",
                content_markdown=(
                    "A standard poker heuristic for set mining (calling a preflop raise with a small pocket pair to hit a set):\n\n"
                    "• Probability of flopping a set: $1 - (48/50 \\times 47/49 \\times 46/48) \\approx 11.8\\%$ (or $\\approx 7.5:1$ against).\n"
                    "• **The 15x / 20x Rule**: You must have at least **15 to 20 times the preflop call amount** in effective stacks behind to justify calling!"
                ),
                mental_shortcut="To set-mine profitably, ensure effective stacks are at least 15-20x the preflop call size.",
            ),
            MathLabLessonStep(
                step_number=4,
                stage=PedagogicalStage.STAGE_4_APPLY,
                title="Stage 4: Evaluating Payoff Likelihood",
                content_markdown=(
                    "Implied odds depend entirely on board disguise and player tendencies:\n"
                    "• Four-to-a-flush on board: Implied odds are virtually ZERO (opponents stop paying off with one pair).\n"
                    "• Under-the-radar gutshot: High implied odds (opponents cannot see the straight coming).\n"
                    "• Calling station villain: High implied odds."
                ),
            ),
            MathLabLessonStep(
                step_number=5,
                stage=PedagogicalStage.STAGE_5_EXECUTE_QUICKLY,
                title="Stage 5: Speed Target",
                content_markdown=(
                    "**Speed Target:** Determine required future chips in under 6 seconds."
                ),
            ),
        ],
    ),
    "mod_12_rake": MathLabLesson(
        module_id="mod_12_rake",
        title="Cash Rake & Profitability",
        summary="Model casino rake percentages, caps, no-flop no-drop rules, and break-even equity shifts.",
        steps=[
            MathLabLessonStep(
                step_number=1,
                stage=PedagogicalStage.STAGE_1_UNDERSTAND,
                title="Stage 1: Rake Makes Poker a Negative-Sum Game",
                content_markdown=(
                    "In cash games, casinos take a percentage of every postflop pot (typically 2.5% to 10%, capped at $2 to $5).\n\n"
                    "**Key Mechanics:**\n"
                    "• **Percentage Rake ($r$)**: Fraction extracted from the pot.\n"
                    "• **Rake Cap ($C$)**: Maximum dollar/chip amount collected per pot.\n"
                    "• **No-Flop, No-Drop**: If a hand ends preflop (everyone folds to a 3-bet or steal), ZERO rake is taken! This massively incentivizes aggressive preflop 3-betting over flat calling."
                ),
                common_misconception="Ignoring rake when calculating break-even calling equity in small and medium-sized pots.",
            ),
            MathLabLessonStep(
                step_number=2,
                stage=PedagogicalStage.STAGE_2_CALCULATE,
                title="Stage 2: Rake-Adjusted Break-Even Equity",
                content_markdown=(
                    "When rake applies below the cap:\n\n"
                    "$$\\text{Effective Pot Won} = (\\text{Pot Before Call} + \\text{Call}) \\times (1 - r)$$\n"
                    "$$\\text{Required Equity} = \\frac{\\text{Call}}{((\\text{Pot Before Call} + \\text{Call}) \\times (1 - r))}$$\n\n"
                    "If the pot exceeds the cap:\n"
                    "$$\\text{Effective Pot Won} = (\\text{Pot Before Call} + \\text{Call}) - C$$"
                ),
                formula_box="Raked Equity (%) = Call / ((Final Pot * (1 - r))) * 100",
                worked_example={
                    "problem": "Pot is 100. Villain bets 50. Rake is 5% uncapped. What is Hero's rake-adjusted required equity to call?",
                    "step_1": "Final pot = 100 + 50 + 50 = 200 chips.",
                    "step_2": "Rake taken = 5% of 200 = 10 chips.",
                    "step_3": "Net pot received upon winning = 200 - 10 = 190 chips.",
                    "step_4": "Required Equity = 50 / 190 = 26.32% (instead of 25.00% without rake)!",
                    "result": "26.32% required equity (+1.32% hurdle due to rake)",
                },
            ),
            MathLabLessonStep(
                step_number=3,
                stage=PedagogicalStage.STAGE_3_ESTIMATE,
                title="Stage 3: The Microstakes Rake Trap",
                content_markdown=(
                    "In microstakes online games (e.g. 10NL or 25NL), rake often reaches 5% with caps equal to 4-8 Big Blinds!\n"
                    "• Marginal calls that are +0.5 BB without rake become strongly -EV after rake.\n"
                    "• Defend tighter from the blinds and 3-bet or fold to exploit 'No-Flop, No-Drop'."
                ),
                mental_shortcut="Add 1.5% to 2.5% to your required pot odds in raked cash games for pots below the cap.",
            ),
            MathLabLessonStep(
                step_number=4,
                stage=PedagogicalStage.STAGE_4_APPLY,
                title="Stage 4: Winrate Impact in BB/100",
                content_markdown=(
                    "A typical winning player makes 4 to 8 BB/100 before rake. "
                    "In high-rake environments, rake can consume 8 to 12 BB/100, turning a fundamentally sound player into a net loser! "
                    "Understanding rake structures is essential for game selection."
                ),
            ),
            MathLabLessonStep(
                step_number=5,
                stage=PedagogicalStage.STAGE_5_EXECUTE_QUICKLY,
                title="Stage 5: Speed Target",
                content_markdown=(
                    "**Speed Target:** Apply rake adjustment to pot odds in under 5 seconds."
                ),
            ),
        ],
    ),
    "mod_13_icm": MathLabLesson(
        module_id="mod_13_icm",
        title="Tournament cEV, ICM & Risk Premium",
        summary="Master the Independent Chip Model, nonlinear prize money values, and bubble factor risk premiums.",
        steps=[
            MathLabLessonStep(
                step_number=1,
                stage=PedagogicalStage.STAGE_1_UNDERSTAND,
                title="Stage 1: Chips Lost Are Worth More Than Chips Won",
                content_markdown=(
                    "In cash games, $1 chip = $1 in real value (linear value).\n\n"
                    "In tournaments, chip value is **diminishing and nonlinear**. "
                    "Winning all the chips in the tournament does NOT award you 100% of the prize pool (first place usually pays 20-30%).\n\n"
                    "Because of this, **the chips you lose are worth significantly more real money than the chips you stand to win**! "
                    "This fundamental asymmetry is governed by the **Independent Chip Model (ICM)**."
                ),
                common_misconception="Making a call on the tournament bubble because it is '+cEV in chips'. If you risk elimination, a +cEV play can be severely -EV in real money!",
            ),
            MathLabLessonStep(
                step_number=2,
                stage=PedagogicalStage.STAGE_2_CALCULATE,
                title="Stage 2: Bubble Factor & Risk Premium",
                content_markdown=(
                    "The **Bubble Factor (BF)** quantifies how much more money you lose when busted compared to what you gain when winning:\n\n"
                    "$$\\text{Bubble Factor} = \\frac{\\text{Equity}(\\text{Current}) - \\text{Equity}(\\text{Lose})}{\\text{Equity}(\\text{Win}) - \\text{Equity}(\\text{Current})}$$\n\n"
                    "$$\\text{Risk Premium (RP)} = \\frac{\\text{BF} - 1}{\\text{BF} + 1} \\times 100\\%$$\n"
                    "$$\\text{Required Equity} = \\text{cEV Pot Odds} + \\text{Risk Premium}$$"
                ),
                formula_box="ICM Required Equity = Chip Pot Odds + Risk Premium",
                worked_example={
                    "problem": "Hero is on the bubble facing an all-in. Chip pot odds require 40% equity. Hero's Bubble Factor against Villain is 2.0. What is Hero's required equity under ICM?",
                    "step_1": "Risk Premium = (2.0 - 1) / (2.0 + 1) = 1 / 3 = 33.3%? Wait! For a 1:1 pot, Risk Premium = (BF - 1)/(BF + 1). For arbitrary pots: Required Eq = BF / (BF + (Pot/Bet)).",
                    "step_2": "Exact required equity: With BF = 2.0 and pot odds requiring 40% (pot before call = 1.5x bet): Required Eq = (2 * 1) / (2 * 1 + 1.5) = 2 / 3.5 = 57.1%!",
                    "step_3": "Hero needs 57.1% equity to call, requiring a massive +17.1% risk premium over chip EV!",
                    "result": "57.1% ICM required equity",
                },
            ),
            MathLabLessonStep(
                step_number=3,
                stage=PedagogicalStage.STAGE_3_ESTIMATE,
                title="Stage 3: Stack Dynamics on the Bubble",
                content_markdown=(
                    "• **Big Stack vs Mid Stack**: Big stack has BF $\\approx 1.1$, mid stack has BF $\\approx 1.8 - 2.5$. The big stack can relentlessly bully the mid stack!\n"
                    "• **Short Stack**: Has very low bubble factor (already near zero equity if folding) and can take gambles.\n"
                    "• **Mid Stack vs Mid Stack**: Maximum bubble factor and paralysis. Avoid clashing!"
                ),
                mental_shortcut="On a significant bubble, add 10-15% equity requirement when facing an all-in from a player who covers you.",
            ),
            MathLabLessonStep(
                step_number=4,
                stage=PedagogicalStage.STAGE_4_APPLY,
                title="Stage 4: Final Table ICM Ladders",
                content_markdown=(
                    "At a 9-handed final table with steep pay jumps, if a 2 BB short stack is about to blind out next hand, "
                    "a 20 BB stack should fold Ace-King to another 20 BB stack's shove! "
                    "Waiting for the short stack to bust guarantees an instant jump in prize money."
                ),
            ),
            MathLabLessonStep(
                step_number=5,
                stage=PedagogicalStage.STAGE_5_EXECUTE_QUICKLY,
                title="Stage 5: Speed Target",
                content_markdown=(
                    "**Speed Target:** Add appropriate risk premium in under 6 seconds."
                ),
            ),
        ],
    ),
    "mod_14_pko": MathLabLesson(
        module_id="mod_14_pko",
        title="PKO & Bounty EV",
        summary="Convert progressive knockout bounties into chip equivalents to adjust calling ranges.",
        steps=[
            MathLabLessonStep(
                step_number=1,
                stage=PedagogicalStage.STAGE_1_UNDERSTAND,
                title="Stage 1: Progressive Knockout Bounty Mechanics",
                content_markdown=(
                    "In a Progressive Knockout (PKO) tournament, 50% of the buy-in goes to the regular prize pool, and 50% forms the starting bounty.\n\n"
                    "When you eliminate a player:\n"
                    "• **50% of their bounty is immediately credited to your account as cash!**\n"
                    "• **50% is added to your own head as a bounty**, making you a more attractive target for others.\n\n"
                    "To account for bounties during hands, we convert the immediate cash reward into **equivalent chip value** added to the pot."
                ),
                common_misconception="Thinking you can win the bounty when you do not COVER the opponent! You must hold more chips than the all-in player.",
            ),
            MathLabLessonStep(
                step_number=2,
                stage=PedagogicalStage.STAGE_2_CALCULATE,
                title="Stage 2: Bounty-to-Chip Conversion",
                content_markdown=(
                    "Under the standard tournament heuristic:\n\n"
                    "$$\\text{Total Starting Chips} = \\text{Total Players} \\times \\text{Starting Stack}$$\n"
                    "$$\\text{Bounty Value per Starting Bounty} = \\frac{1}{3} \\times \\text{Starting Stack}$$\n\n"
                    "$$\\text{Adjusted Pot} = \\text{Physical Pot} + \\text{Bounty Chip Value}$$\n"
                    "$$\\text{Required Equity} = \\frac{\\text{Call}}{\\text{Adjusted Pot} + \\text{Call}}$$"
                ),
                formula_box="Adjusted Pot = Current Pot + Bounty Equivalent Chips",
                worked_example={
                    "problem": "Starting stack is 10,000 chips (1 starting bounty = 3,333 chips). Pot is 15,000. Villain shoves 10,000 with a 3x starting bounty. Hero covers Villain. What is Hero's required equity?",
                    "step_1": "Bounty chip value = 3 * 3,333 = 10,000 equivalent chips.",
                    "step_2": "Total adjusted pot before Hero calls = 15,000 + 10,000 (shove) + 10,000 (bounty) = 35,000 chips.",
                    "step_3": "Final adjusted pot after call = 35,000 + 10,000 = 45,000 chips.",
                    "step_4": "Required Equity = 10,000 / 45,000 = 22.2% (vs 28.6% without bounty)!",
                    "result": "22.2% required equity (bounty expands calling range by 6.4%)",
                },
            ),
            MathLabLessonStep(
                step_number=3,
                stage=PedagogicalStage.STAGE_3_ESTIMATE,
                title="Stage 3: Covering vs Covered Asymmetry",
                content_markdown=(
                    "• **If you COVER Villain**: Bounties massively widen your calling and shoving ranges.\n"
                    "• **If Villain COVERS you**: You CANNOT win their bounty, and you face elimination plus giving them your bounty. Play tighter!"
                ),
                mental_shortcut="Every starting bounty Villain holds is worth approximately 1/3 of a starting stack in extra chips.",
            ),
            MathLabLessonStep(
                step_number=4,
                stage=PedagogicalStage.STAGE_4_APPLY,
                title="Stage 4: Giant Late-Stage Bounties",
                content_markdown=(
                    "Late in a PKO, a short stack might have accumulated 10 starting bounties while holding only 5 Big Blinds. "
                    "The bounty chips in the pot can exceed 50 Big Blinds of value! "
                    "In such cases, any two cards (including 7-2 offsuit) become a mathematically mandatory call."
                ),
            ),
            MathLabLessonStep(
                step_number=5,
                stage=PedagogicalStage.STAGE_5_EXECUTE_QUICKLY,
                title="Stage 5: Speed Target",
                content_markdown=(
                    "**Speed Target:** Convert bounty to chips and adjust pot odds in under 7 seconds."
                ),
            ),
        ],
    ),
    "mod_15_mental_math": MathLabLesson(
        module_id="mod_15_mental_math",
        title="Mental Math Techniques",
        summary="Synthesize rapid poker arithmetic shortcuts, anchor percentages, and fast approximations.",
        steps=[
            MathLabLessonStep(
                step_number=1,
                stage=PedagogicalStage.STAGE_1_UNDERSTAND,
                title="Stage 1: The Principle of Sufficient Accuracy",
                content_markdown=(
                    "In live and online poker, you don't need 4 decimal places of precision — you need **sufficient accuracy to make the correct decision**.\n\n"
                    "If your pot odds demand 25% and your equity is clearly over 40%, whether your exact equity is 41.2% or 43.8% does not change your action: calling is a slam dunk!\n"
                    "Save mental energy for close borderline decisions."
                ),
                common_misconception="Wasting your entire time bank trying to compute whether an out gives 34.8% vs 35.1% when facing a 1/2 pot bet.",
            ),
            MathLabLessonStep(
                step_number=2,
                stage=PedagogicalStage.STAGE_2_CALCULATE,
                title="Stage 2: The Core Cheat Sheet Matrix",
                content_markdown=(
                    "Commit this rapid translation matrix to memory:\n\n"
                    "| Bet Size | Required Equity | Alpha (Bluff Fold %) | MDF |\n"
                    "| :--- | :--- | :--- | :--- |\n"
                    "| **1/4 Pot** | 16.7% | 20.0% | 80.0% |\n"
                    "| **1/3 Pot** | 20.0% | 25.0% | 75.0% |\n"
                    "| **1/2 Pot** | 25.0% | 33.3% | 66.7% |\n"
                    "| **2/3 Pot** | 28.6% | 40.0% | 60.0% |\n"
                    "| **3/4 Pot** | 30.0% | 42.9% | 57.1% |\n"
                    "| **Pot (1x)** | 33.3% | 50.0% | 50.0% |\n"
                    "| **1.5x Overbet** | 37.5% | 60.0% | 40.0% |\n"
                    "| **2x Overbet** | 40.0% | 66.7% | 33.3% |"
                ),
                formula_box="Alpha = Bet / (Pot + Bet) | Pot Odds = Call / (Pot + Bet + Call)",
                worked_example={
                    "problem": "Villain bets 75 into 100 on the river. State instant required equity and break-even bluff Alpha.",
                    "step_1": "Bet is 3/4 pot (75 / 100).",
                    "step_2": "Required equity for call: 75 / (100 + 75 + 75) = 75 / 250 = 30.0%.",
                    "step_3": "Alpha for bluff: 75 / (100 + 75) = 75 / 175 = 42.9%.",
                    "result": "Call equity = 30.0%, Bluff Alpha = 42.9%",
                },
            ),
            MathLabLessonStep(
                step_number=3,
                stage=PedagogicalStage.STAGE_3_ESTIMATE,
                title="Stage 3: The 4/2 Outs Shortcut with Adjustment",
                content_markdown=(
                    "• **Turn to River (1 card)**: $\\text{Outs} \\times 2 + 1\\%$ (e.g. 9 outs $\\to 9 \\times 2 + 1 = 19\\%$; exact is 19.6%).\n"
                    "• **Flop to River (2 cards)**: $\\text{Outs} \\times 4 - (\\text{Outs} - 8)$ for outs $> 8$ (e.g. 9 outs $\\to 36 - 1 = 35\\%$; 15 outs $\\to 60 - 7 = 53\\%$)."
                ),
                mental_shortcut="For outs over 8 on the flop: (Outs * 4) - (Outs - 8). Spot on within 0.5% every time.",
            ),
            MathLabLessonStep(
                step_number=4,
                stage=PedagogicalStage.STAGE_4_APPLY,
                title="Stage 4: Checking Decision Sensitivity",
                content_markdown=(
                    "Whenever your estimate lands within $\\pm 2\\%$ of the break-even threshold:\n"
                    "1. Check if rake pushes it over the edge.\n"
                    "2. Check if opponent sizing tells narrow their range.\n"
                    "3. Check whether folding preserves valuable chips for better future spots."
                ),
            ),
            MathLabLessonStep(
                step_number=5,
                stage=PedagogicalStage.STAGE_5_EXECUTE_QUICKLY,
                title="Stage 5: Speed Benchmark",
                content_markdown=(
                    "**Speed Target:** Complete mental arithmetic in under 3 seconds per spot."
                ),
            ),
        ],
    ),
    "mod_16_integrated_reasoning": MathLabLesson(
        module_id="mod_16_integrated_reasoning",
        title="Integrated Real-Hand Mathematical Reasoning",
        summary="Synthesize unprompted mathematical reasoning across multi-street hands and identify unsolvable problems.",
        steps=[
            MathLabLessonStep(
                step_number=1,
                stage=PedagogicalStage.STAGE_1_UNDERSTAND,
                title="Stage 1: The 8-Step Mathematical Decision Framework",
                content_markdown=(
                    "In real poker, no software whispers 'calculate pot odds now'. You must independently execute this 8-step framework:\n\n"
                    "1. **Decision Point**: What action are you facing (open, 3-bet, c-bet, check-raise, river bet)?\n"
                    "2. **Relevant Quantities**: Does this require pot odds, fold equity, outs, realization, or ICM?\n"
                    "3. **Known Quantities**: Pot size, bet amount, effective stack, board cards, position.\n"
                    "4. **Estimated Quantities**: Opponent range, fold frequency, equity realization.\n"
                    "5. **Appropriate Formula**: Select the exact equation matching this node.\n"
                    "6. **Execute Calculation**: Derive the numerical answer or justified estimate.\n"
                    "7. **Decision Conclusion**: Does evidence support Call, Fold, Bet, or Raise?\n"
                    "8. **Remaining Uncertainty**: Is information missing or ambiguous?"
                ),
                common_misconception="Forcing an arithmetic answer when essential variables (like opponent stack size or payout ladder) are completely unknown.",
            ),
            MathLabLessonStep(
                step_number=2,
                stage=PedagogicalStage.STAGE_2_CALCULATE,
                title="Stage 2: Recognizing 'Insufficient Information'",
                content_markdown=(
                    "A critical mark of an advanced poker thinker is knowing when a problem is **mathematically indeterminate**.\n\n"
                    "Examples of Insufficient Information:\n"
                    "• Being asked if calling an all-in on a tournament bubble is +EV without knowing the payout ladder or stack distribution.\n"
                    "• Being asked for exact call EV without knowing the opponent's bet size.\n"
                    "• Being asked for turn call EV without knowing whether future river betting remains."
                ),
                formula_box="If key parameters are unstated, valid answer is 'Insufficient Information to Determine'.",
                worked_example={
                    "problem": "Hero faces a bet with a flush draw. We are given pot = 200, but the opponent's bet size is not specified. Can we calculate pot odds?",
                    "step_1": "Formula for pot odds requires Call Amount.",
                    "step_2": "Because Call Amount is unspecified, pot odds could be anything from 10% to 50%.",
                    "result": "Insufficient Information to Determine",
                },
            ),
            MathLabLessonStep(
                step_number=3,
                stage=PedagogicalStage.STAGE_3_ESTIMATE,
                title="Stage 3: Mathematical Proof vs Strategic Range Model",
                content_markdown=(
                    "Always maintain strict intellectual honesty:\n"
                    "• **Mathematical Conclusion**: Directly derived from known parameters (e.g. pot odds = 25%). Provable and indisputable.\n"
                    "• **Strategic Recommendation**: Relies on assumptions about opponent ranges, bluff frequencies, or realization factors. Plausible, but model-dependent!"
                ),
                mental_shortcut="Never confuse an assumption-dependent strategic judgment with an immutable mathematical fact.",
            ),
            MathLabLessonStep(
                step_number=4,
                stage=PedagogicalStage.STAGE_4_APPLY,
                title="Stage 4: Multi-Street Hand Walkthrough",
                content_markdown=(
                    "Follow Hero through a full hand:\n"
                    "• Preflop: 3-bet sizing based on position and SPR target.\n"
                    "• Flop: C-bet sizing based on range advantage and Alpha.\n"
                    "• Turn: Check-call decision based on outs and implied odds.\n"
                    "• River: Bluff-catching decision based on pure pot odds and card removal."
                ),
            ),
            MathLabLessonStep(
                step_number=5,
                stage=PedagogicalStage.STAGE_5_EXECUTE_QUICKLY,
                title="Stage 5: Speed Target",
                content_markdown=(
                    "**Speed Target:** Complete unprompted diagnosis and decision within 10 seconds."
                ),
            ),
        ],
    ),
}

# Aliases for backwards compatibility
LESSONS["mod_09_semibluff_ev"] = LESSONS["mod_09_semi_bluff"]
LESSONS["mod_12_rake_profitability"] = LESSONS["mod_12_rake"]
LESSONS["mod_13_tournament_icm"] = LESSONS["mod_13_icm"]
LESSONS["mod_14_pko_bounties"] = LESSONS["mod_14_pko"]
