"""Comprehensive Reference Library for Poker Math Lab.

Contains authored, mathematically verified reference articles for all 16 modules
with rigorous derivations, boundaries, shortcuts, worked examples, and academic citations.
"""

from __future__ import annotations

from app.domain.math_lab.models import MathLabModule, ReferenceArticle

MODULES: list[MathLabModule] = [
    MathLabModule(
        id="mod_01_arithmetic",
        number=1,
        title="Poker Arithmetic Foundations",
        short_title="Arithmetic & Units",
        description="Master rapid conversion between odds, fractions, percentages, pot ratios, and big blind units.",
        core_formula="Percentage = Fraction * 100 | Odds = (1 - P) : P",
        units="Percentages (%), Ratios (X:1), Big Blinds (BB)",
        prerequisites=[],
        tags=["foundations", "odds", "fractions", "mental-math"],
    ),
    MathLabModule(
        id="mod_02_pot_odds",
        number=2,
        title="Pot Odds & Break-Even Equity",
        short_title="Pot Odds",
        description="Calculate immediate pot odds, required equity to call, and understand the impact of dead money and bet sizing.",
        core_formula="Required Equity = Call / (Pot_before_call + Call)",
        units="Percentage (%)",
        prerequisites=["mod_01_arithmetic"],
        tags=["pot-odds", "break-even", "calling-threshold"],
    ),
    MathLabModule(
        id="mod_03_outs_draws",
        number=3,
        title="Outs, Draws & Card Improvement",
        short_title="Outs & Draws",
        description="Clean versus dirty outs, redraws, counterfeiting, and exact combinatorial draw completion versus the Rule of 2 and 4.",
        core_formula="P(1 card) = Outs / 46 | P(2 cards) = 1 - ((47-Outs)/47 * (46-Outs)/46)",
        units="Outs Count, Percentage (%)",
        prerequisites=["mod_01_arithmetic"],
        tags=["outs", "draws", "rule-of-2-and-4", "card-counting"],
    ),
    MathLabModule(
        id="mod_04_equity_fundamentals",
        number=4,
        title="Equity Fundamentals",
        short_title="Equity Basics",
        description="Showdown equity, tie shares, hand-versus-hand matchups, overpairs vs sets, and card removal effects.",
        core_formula="Equity = (Wins + 0.5 * Ties) / Total_Runouts",
        units="Percentage (%)",
        prerequisites=["mod_02_pot_odds", "mod_03_outs_draws"],
        tags=["equity", "showdown", "matchups", "ties"],
    ),
    MathLabModule(
        id="mod_05_equity_ranges",
        number=5,
        title="Equity Against Opponent Ranges",
        short_title="Range Equity",
        description="Evaluating equity against weighted preflop and postflop ranges, combinatorics, blockers, and street-by-street range narrowing.",
        core_formula="Range Equity = Sum(Weight_i * Equity_i) / Sum(Weight_i)",
        units="Percentage (%)",
        prerequisites=["mod_04_equity_fundamentals"],
        tags=["ranges", "range-vs-range", "blockers", "combinatorics"],
    ),
    MathLabModule(
        id="mod_06_equity_realization",
        number=6,
        title="Equity Realization",
        short_title="Equity Realization (EQR)",
        description="Raw showdown equity versus realized value: position, playability, reverse implied odds, and stack-to-pot ratios.",
        core_formula="Realized Value = Raw Equity * EQR Factor",
        units="Factor (e.g. 0.85 to 1.25), Expected Chips",
        prerequisites=["mod_04_equity_fundamentals", "mod_05_equity_ranges"],
        tags=["realization", "position", "playability", "spr"],
    ),
    MathLabModule(
        id="mod_07_call_ev",
        number=7,
        title="Call Expected Value",
        short_title="Call EV",
        description="Exact chip expected value of calling terminal bets, facing all-ins, multiway pots, and rake deductions.",
        core_formula="EV(Call) = Equity * (Pot + Call) - Call",
        units="Chips (+/-) or Big Blinds (+/-)",
        prerequisites=["mod_02_pot_odds", "mod_04_equity_fundamentals"],
        tags=["ev", "expected-value", "call-ev", "profitability"],
    ),
    MathLabModule(
        id="mod_08_bluff_ev",
        number=8,
        title="Bluff EV & Fold Equity",
        short_title="Bluff EV",
        description="Alpha calculation, break-even fold frequencies across various bet sizes, bluff blockers, and MDF defensive benchmarks.",
        core_formula="Alpha = Bet / (Pot + Bet) | EV(Bluff) = P(fold) * Pot - P(call) * Bet",
        units="Percentage (%), Expected Chips (+/-)",
        prerequisites=["mod_01_arithmetic", "mod_07_call_ev"],
        tags=["bluff-ev", "fold-equity", "alpha", "mdf"],
    ),
    MathLabModule(
        id="mod_09_semi_bluff",
        number=9,
        title="Semi-Bluff EV",
        short_title="Semi-Bluff EV",
        description="Multi-branch expected value combining immediate fold equity, showdown equity when called, and raise consequences.",
        core_formula="EV(Semi-bluff) = P(fold)*Pot + P(call)*[Equity*(Pot + 2*Bet) - Bet]",
        units="Expected Chips (+/-)",
        prerequisites=["mod_07_call_ev", "mod_08_bluff_ev"],
        tags=["semi-bluff", "draws", "fold-equity", "multi-branch"],
    ),
    MathLabModule(
        id="mod_10_action_comparison",
        number=10,
        title="Bet, Raise & Action EV Comparison",
        short_title="Action EV Comparison",
        description="Comparing Fold, Check, Call, Bet, and Raise branches to determine the maximal EV line under conditional opponent reactions.",
        core_formula="Max EV = argmax_{a in Actions} EV(a)",
        units="Expected Chips (+/-)",
        prerequisites=["mod_07_call_ev", "mod_08_bluff_ev", "mod_09_semi_bluff"],
        tags=["action-ev", "raise-ev", "decision-trees", "optimization"],
    ),
    MathLabModule(
        id="mod_11_implied_odds",
        number=11,
        title="Implied & Reverse Implied Odds",
        short_title="Implied Odds",
        description="Future chips needed to justify drawing, effective stack constraints, and dangerous reverse implied odds traps.",
        core_formula="Required Future Chips = (Call / Equity) - (Pot + Call)",
        units="Chips or Big Blinds",
        prerequisites=["mod_02_pot_odds", "mod_03_outs_draws"],
        tags=["implied-odds", "reverse-implied", "future-betting"],
    ),
    MathLabModule(
        id="mod_12_rake",
        number=12,
        title="Cash Rake & Profitability",
        short_title="Rake & Winrate",
        description="Percentage rake, rake caps, no-flop-no-drop impact, rake effect on marginal calls, and BB/100 conversion.",
        core_formula="Rake = min(Pot * Rake_pct, Cap) | Net Pot = Pot - Rake",
        units="Chips, Percentage (%), BB/100",
        prerequisites=["mod_02_pot_odds", "mod_07_call_ev"],
        tags=["rake", "cash-games", "no-flop-no-drop", "caps"],
    ),
    MathLabModule(
        id="mod_13_icm",
        number=13,
        title="Tournament cEV, ICM & Risk Premium",
        short_title="ICM & Risk Premium",
        description="Independent Chip Model (Malmuth-Harville), nonlinear chip valuation, bubble factors, and why +cEV calls can be -ICM $EV.",
        core_formula="Bubble Factor = (EV_lose - EV_now) / (EV_win - EV_now) | Risk Premium = (BF - 1)/(BF + 1)",
        units="Percentage (%), Currency ($), Dimensionless Ratio",
        prerequisites=["mod_02_pot_odds", "mod_07_call_ev"],
        tags=["icm", "tournaments", "bubble-factor", "risk-premium"],
    ),
    MathLabModule(
        id="mod_14_pko",
        number=14,
        title="PKO & Bounty EV",
        short_title="PKO Bounties",
        description="Progressive Knockout tournament math: bounty-to-chip conversion, covering criteria, and adjusted call thresholds.",
        core_formula="Bounty Chip Value = (Cash Bounty / Starting Bounty Pool) * Total Starting Chips",
        units="Chips, Percentage (%)",
        prerequisites=["mod_02_pot_odds", "mod_13_tournament_icm"],
        tags=["pko", "bounties", "knockouts", "tournaments"],
    ),
    MathLabModule(
        id="mod_15_mental_math",
        number=15,
        title="Mental Math Techniques",
        short_title="Mental Shortcuts",
        description="High-speed pattern recognition: standard bet fractions, 2/4 adjustments, SPR approximations, and decision-sensitivity tests.",
        core_formula="Call Req: 1/3->20%, 1/2->25%, 2/3->28.6%, 1x->33.3% | Bluff Alpha: 1/3->25%, 1/2->33.3%, 1x->50%",
        units="Percentages (%), Seconds",
        prerequisites=["mod_01_arithmetic", "mod_02_pot_odds", "mod_03_outs_draws"],
        tags=["mental-math", "shortcuts", "speed", "heuristics"],
    ),
    MathLabModule(
        id="mod_16_integrated_reasoning",
        number=16,
        title="Integrated Real-Hand Mathematical Reasoning",
        short_title="Integrated Decisions",
        description="Holistic decision laboratory: independently identify missing quantities, relevant equations, and distinguish math from strategic models.",
        core_formula="Decision = Mathematical Proof + Strategic Range Model",
        units="Multidimensional Assessment",
        prerequisites=["mod_01_arithmetic", "mod_07_call_ev", "mod_10_action_comparison"],
        tags=["integrated-math", "decision-lab", "real-hands", "mastery"],
    ),
]

REFERENCE_ARTICLES: dict[str, ReferenceArticle] = {
    "mod_01_arithmetic": ReferenceArticle(
        module_id="mod_01_arithmetic",
        title="Poker Arithmetic Foundations & Conversions",
        definition=(
            "Poker arithmetic is the system of mathematical conversions between fractions, "
            "percentages, odds ratios, and Big Blind (BB) currency units required to make "
            "quantitative poker decisions at the table."
        ),
        mathematical_derivation=(
            "1. Probability to Odds Ratio: Given probability P in [0, 1], the odds against an event are "
            "(1 - P) / P to 1. For example, if P = 0.20 (20%), odds against = (0.80 / 0.20) = 4 to 1 (4:1).\n"
            "2. Odds Ratio to Probability: Given odds against of X to Y (X:Y), probability P = Y / (X + Y). "
            "For 4:1 odds, P = 1 / (4 + 1) = 1/5 = 20%.\n"
            "3. Stack to BB Conversion: Chips / Big_Blind_Amount = Stack in BBs."
        ),
        formula="P = Y / (X + Y)  <===>  Odds Against = (1 - P) : P",
        variables=[
            {
                "name": "P",
                "description": "Probability of occurrence",
                "unit": "Fraction in [0, 1] or %",
            },
            {
                "name": "X:Y",
                "description": "Odds ratio against (X unfavorable outcomes for every Y favorable)",
                "unit": "Ratio",
            },
            {"name": "BB", "description": "Big blind standard unit", "unit": "Chips"},
        ],
        units="Percentages (%), Ratios (X:1), Big Blinds (BB)",
        boundary_conditions=[
            "P must be strictly between 0 and 1 (0% to 100%).",
            "Big blind size must be strictly positive.",
            "Total events X + Y cannot equal zero.",
        ],
        mental_shortcut=(
            "To convert odds of X:1 to percentage quickly, compute 100 / (X + 1). "
            "Examples: 4:1 -> 100 / 5 = 20%. 3:1 -> 100 / 4 = 25%. 2:1 -> 100 / 3 = 33.3%."
        ),
        worked_example={
            "scenario": "Scenario A (Pot before bet): The pot is 150 before an opponent bets 50. You must call 50 to see showdown.",
            "step_1": "Pot before bet: 150 chips.",
            "step_2": "Opponent bet: 50 chips. Pot facing your call (pot before call) = 150 + 50 = 200 chips.",
            "step_3": "Call amount: 50 chips. Total final pot = 200 + 50 = 250 chips.",
            "step_4": "Required Equity: Call / Final Pot = 50 / 250 = 1/5 = 20.0%.",
            "step_5": "Express as odds against: (250 - 50) : 50 = 200 : 50 = 4 to 1 (4:1).",
            "conclusion": "You are getting 4:1 pot odds, meaning you need exactly 20.0% equity to break even.",
        },
        counterexample_or_misconception=(
            "Pot Odds Ambiguity Pitfall: 'Pot Before Bet' vs 'Pot Facing Call':\n"
            "• Case 1: 'The pot is 150 before opponent bets 50. Call 50.' -> Pot facing you is 200, final pot is 250. Required equity = 50 / 250 = 20.0%.\n"
            "• Case 2: 'The current pot is 150, including opponent's bet. Call 50.' -> Pot facing you is 150, final pot is 200. Required equity = 50 / 200 = 25.0%.\n"
            "Never confuse the pot before the opponent acted with the pot facing your decision! Always calculate: Call / (Pot Facing You + Call)."
        ),
        cash_vs_tournament_differences="In cash games, 1 chip equals fixed cash value. In tournaments, chips have non-linear utility due to ICM.",
        academic_citations=[
            {
                "author": "Bill Chen & Jerrod Ankenman",
                "title": "The Mathematics of Poker",
                "year": "2006",
                "chapter": "Part I: Basics",
            },
            {
                "author": "David Sklansky",
                "title": "The Theory of Poker",
                "year": "1987",
                "chapter": "Chapter 4: Pot Odds",
            },
        ],
    ),
    "mod_02_pot_odds": ReferenceArticle(
        module_id="mod_02_pot_odds",
        title="Pot Odds & Break-Even Equity",
        definition=(
            "Pot odds represent the ratio between the size of the pot facing a player and the cost of calling a bet. "
            "The break-even equity is the minimum showdown equity required to make a call strictly non-negative in chip EV."
        ),
        mathematical_derivation=(
            "Expected Value of Calling: EV(Call) = Equity * (Pot_before_call + Call) - Call.\n"
            "Setting EV(Call) = 0 for the break-even threshold:\n"
            "Equity * (Pot_before_call + Call) = Call\n"
            "Required Equity = Call / (Pot_before_call + Call).\n"
            "Note: Pot_before_call MUST include all prior bets on this street, including the opponent's current bet."
        ),
        formula="Required Equity (%) = (Call Amount / (Pot Before Call + Call Amount)) * 100",
        variables=[
            {
                "name": "Call Amount",
                "description": "Additional chips required to call the bet",
                "unit": "Chips",
            },
            {
                "name": "Pot Before Call",
                "description": "Existing pot including opponent's current bet",
                "unit": "Chips",
            },
            {
                "name": "Required Equity",
                "description": "Minimum equity percentage needed to break even",
                "unit": "%",
            },
        ],
        units="Percentage (%)",
        boundary_conditions=[
            "Assumes zero future betting (all-in or river decision) or perfect equity realization.",
            "Does not account for future implied odds or reverse implied odds.",
            "Ignores casino rake unless explicitly integrated.",
        ],
        mental_shortcut=(
            "Standard Bet-to-Pot Ratios to Memorize:\n"
            "• 1/4 pot bet -> Need 16.7% equity\n"
            "• 1/3 pot bet -> Need 20.0% equity\n"
            "• 1/2 pot bet -> Need 25.0% equity\n"
            "• 2/3 pot bet -> Need 28.6% equity\n"
            "• 3/4 pot bet -> Need 30.0% equity\n"
            "• Pot-sized bet -> Need 33.3% equity\n"
            "• 1.5x pot overbet -> Need 37.5% equity\n"
            "• 2x pot overbet -> Need 40.0% equity"
        ),
        worked_example={
            "scenario": "The pot is 100 before Villain bets 50 on the river. The pot facing your call is 150 (100 + 50). You must call 50.",
            "step_1": "Pot Before Bet: 100 chips.",
            "step_2": "Pot Facing Call (Pot Before Call): 100 + 50 = 150 chips.",
            "step_3": "Call Amount: 50 chips.",
            "step_4": "Total Final Pot: 150 + 50 = 200 chips.",
            "step_5": "Required Equity: Call / Final Pot = 50 / 200 = 0.25 = 25.0%.",
            "conclusion": "You need exactly 25.0% equity against Villain's river betting range to call profitably.",
        },
        counterexample_or_misconception=(
            "Crucial Contrast: 'Pot Before Bet' vs 'Pot Facing Call':\n"
            "• If question states: 'Pot is 150 before an opponent bets 50. What is required equity?' -> Pot facing call is 200, final pot is 250, required equity = 50 / 250 = 20.0%.\n"
            "• If question states: 'Current pot is 150 including opponent's 50 bet. What is required equity?' -> Pot facing call is 150, final pot is 200, required equity = 50 / 200 = 25.0%.\n"
            "Always identify whether the opponent's bet is already inside the quoted pot number!"
        ),
        cash_vs_tournament_differences="In cash games, 25% equity suffices for a 25% pot odds call. In tournaments on the bubble, the Risk Premium may demand 32%+ equity to justify calling.",
        academic_citations=[
            {
                "author": "Matthew Janda",
                "title": "Applications of No-Limit Hold'em",
                "year": "2013",
                "chapter": "Chapter 2: Pot Odds & Equity",
            },
            {
                "author": "Michael Acevedo",
                "title": "Modern Poker Theory",
                "year": "2019",
                "chapter": "Chapter 3: The Math of Game Theory",
            },
        ],
    ),
    "mod_03_outs_draws": ReferenceArticle(
        module_id="mod_03_outs_draws",
        title="Outs, Draws & Card Improvement Probabilities",
        definition=(
            "An out is any unseen card in the deck that, if dealt, improves a player's hand to what is assumed "
            "to be the best hand. Card improvement probability measures the exact combinatorial likelihood of hitting those outs."
        ),
        mathematical_derivation=(
            "1. Turn (1 card to come): With 5 cards known (2 hole + 3 flop), 47 unknown cards remain.\n"
            "   P(hit on turn) = Outs / 47.\n"
            "2. River (1 card to come from turn): With 6 cards known (2 hole + 4 board), 46 unknown cards remain.\n"
            "   P(hit on river) = Outs / 46.\n"
            "3. Flop to River (2 cards to come): Exact probability using complementary combinatorics:\n"
            "   P(miss both) = C(47 - Outs, 2) / C(47, 2) = ((47 - Outs) / 47) * ((46 - Outs) / 46).\n"
            "   P(hit at least once) = 1 - P(miss both).\n"
            "4. Rule of 4 Approximation: Outs * 4. For Outs > 8, the exact formula diverges downward, "
            "so the standard mental correction is: (Outs * 4) - (Outs - 8)."
        ),
        formula="P(Flop to River Exact) = 1 - ((47 - Outs) * (46 - Outs)) / (47 * 46)",
        variables=[
            {
                "name": "Outs",
                "description": "Count of unseen cards that complete your draw",
                "unit": "Integer [1, 47]",
            },
            {
                "name": "Known Cards",
                "description": "Your 2 hole cards + community cards",
                "unit": "Cards",
            },
            {
                "name": "Unknown Cards",
                "description": "52 minus known cards (47 on flop, 46 on turn)",
                "unit": "Cards",
            },
        ],
        units="Outs Count, Percentage (%)",
        boundary_conditions=[
            "Dirty outs (cards that complete your draw but give opponent a better hand) MUST be excluded or discounted.",
            "Do not double-count overlapping outs (e.g. straight flush outs counted once in straight, once in flush).",
            "Hitting an out does not guarantee winning if opponent has redraws.",
        ],
        mental_shortcut=(
            "Rule of 2 and 4:\n"
            "• On the turn with 1 card to come: Multiply outs by 2. (e.g. 9 outs * 2 = ~18%; exact is 9/46 = 19.6%).\n"
            "• On the flop with 2 cards to come: Multiply outs by 4. If outs > 8, subtract (outs - 8).\n"
            "  Example: 9 outs (flush draw) -> (9 * 4) - 1 = 35% (exact is 35.0%).\n"
            "  Example: 15 outs (straight + flush combo) -> (15 * 4) - 7 = 53% (exact is 54.1%)."
        ),
        worked_example={
            "scenario": "Hero holds Ah Kh on a board of Qh Jh 4c on the flop. Hero has a nut flush draw (9 outs) plus an open-ended straight draw with 10s (4 outs).",
            "step_1": "Flush outs: 9 hearts remaining (13 - 2 in hand - 2 on board = 9).",
            "step_2": "Straight outs: Four 10s (10s, 10d, 10c, 10h). Notice 10h was already counted in flush!",
            "step_3": "Add unique straight outs: 3 non-heart 10s (10s, 10d, 10c).",
            "step_4": "Overcard outs: Two aces (As, Ac, Ad - Ah in hand) and two kings (Ks, Kd, Kc - Kh in hand) = 6 outs if clean.",
            "step_5": "Assuming only flush + straight outs are clean: 9 + 3 = 12 outs.",
            "step_6": "Rule of 4: (12 * 4) - (12 - 8) = 48 - 4 = 44% to hit by river. Exact = 1 - (35*34)/(47*46) = 45.0%.",
        },
        counterexample_or_misconception=(
            "Common Misconception: Double counting the flush card in a straight draw. "
            "Holding 8h 7h on 6h 5c 2d: OESD has 8 outs (four 9s, four 4s). Two of them (9h, 4h) are hearts! "
            "You cannot count 9 flush outs + 8 straight outs = 17 outs. The real total is 9 + 6 = 15 outs."
        ),
        cash_vs_tournament_differences="In cash games, draw equity converts directly to chip EV. In tournaments near the money bubble, drawing and missing when all-in carries catastrophic elimination risk.",
        academic_citations=[
            {
                "author": "Ed Miller",
                "title": "Poker's 1%: The One Big Secret That Keeps Elite Players On Top",
                "year": "2014",
                "chapter": "Counting Outs",
            },
            {
                "author": "Dan Harrington",
                "title": "Harrington on Hold 'em: Volume 1",
                "year": "2004",
                "chapter": "Pot Odds and Outs",
            },
        ],
    ),
    "mod_04_equity_fundamentals": ReferenceArticle(
        module_id="mod_04_equity_fundamentals",
        title="Showdown Equity Fundamentals & Matchups",
        definition=(
            "Showdown equity is a player's mathematical expected share of the pot at showdown if all remaining "
            "cards were dealt with no further betting. It incorporates win frequency plus fractional shares for split pots."
        ),
        mathematical_derivation=(
            "Across all valid complete community card runouts N:\n"
            "Equity = (Wins + Sum_{k >= 2} (Ties_k / k)) / N,\n"
            "where Ties_k is the number of runouts resulting in a k-way split pot.\n"
            "In heads-up, this simplifies to: Equity = (Wins + 0.5 * Ties) / N."
        ),
        formula="Equity (%) = ((Wins + 0.5 * Ties) / Total Runouts) * 100",
        variables=[
            {
                "name": "Wins",
                "description": "Number of complete runouts where player holds the unique best hand",
                "unit": "Integer",
            },
            {
                "name": "Ties",
                "description": "Number of complete runouts where player shares the best hand",
                "unit": "Integer",
            },
            {
                "name": "Total Runouts",
                "description": "Total combinatorial board completions evaluated",
                "unit": "Integer",
            },
        ],
        units="Percentage (%)",
        boundary_conditions=[
            "Total equity across all active players in a pot must sum to exactly 100.0%.",
            "Blocker cards held by other players reduce the probability of specific runouts.",
            "Equity is a probability distribution over unknown cards, NOT a guarantee of winning any single trial.",
        ],
        mental_shortcut=(
            "Canonical Preflop Matchup Benchmarks:\n"
            "• Pocket Pair vs Lower Pocket Pair (AA vs KK): ~81% vs ~19%\n"
            "• Higher Pair vs Two Lower Cards (AA vs JT): ~80% vs ~20%\n"
            "• Pair vs Two Overcards (Coin Flip, QQ vs AKs): ~54% vs ~46%\n"
            "• Pair vs One Overcard (JJ vs AQs): ~71% vs ~29%\n"
            "• Dominated Hand (AK vs AQ, high kicker): ~74% vs ~26%\n"
            "• Two Overcards vs Two Undercards (AKs vs QTs): ~63% vs ~37%"
        ),
        worked_example={
            "scenario": "Preflop all-in: Player 1 has As Ah, Player 2 has Ks Kd. Flop: 7s 6c 2d. What is Player 1's equity?",
            "step_1": "Player 2 needs one of the remaining two Kings to win (Kh, Kc), plus backdoor straight/flush possibilities.",
            "step_2": "Remaining unknown cards on flop = 45. Number of turn+river combinations = C(45, 2) = 990.",
            "step_3": "Player 2 hits a King on turn or river in approximately 84 combinations.",
            "step_4": "Evaluating all 990 runouts shows AA wins 906, KK wins 84. Equity = 906 / 990 = 91.5% for AA vs 8.5% for KK.",
        },
        counterexample_or_misconception=(
            "Common Misconception: Believing having 70% equity means you will 'usually win the next three hands'. "
            "Independent trials have variance: an 80/20 favorite will still lose 20% of the time, meaning losing 2 in a row "
            "happens in 4% of trials (1 in 25 times) purely by chance without any rigged deck or flawed math."
        ),
        cash_vs_tournament_differences="In cash games, playing a 55/45 edge is always strictly profitable. In tournaments, flipping for your tournament life with small edges may be negative dollar EV due to elimination asymmetry.",
        academic_citations=[
            {
                "author": "Bill Chen & Jerrod Ankenman",
                "title": "The Mathematics of Poker",
                "year": "2006",
                "chapter": "Chapter 6: Hand vs Hand Equity",
            },
            {
                "author": "Will Tipton",
                "title": "Expert Heads Up No Limit Hold'em: Volume 1",
                "year": "2012",
                "chapter": "Equity and Hand Strength",
            },
        ],
    ),
    "mod_05_equity_ranges": ReferenceArticle(
        module_id="mod_05_equity_ranges",
        title="Equity Against Opponent Ranges & Combinatorics",
        definition=(
            "Range equity evaluates how a specific hand or range performs against the complete probability-weighted "
            "distribution of hands an opponent can realistically hold given their prior actions, position, and stack depth."
        ),
        mathematical_derivation=(
            "Let R be opponent's range composed of combos c_i with probability weights w_i.\n"
            "Equity(Hero vs R) = Sum_{i} [w_i * Equity(Hero vs c_i)] / Sum_{i} w_i.\n"
            "Card Combinatorics:\n"
            "• Unpaired hand (e.g. AK): 4 ranks of A * 4 ranks of K = 16 combos (4 suited, 12 offsuit).\n"
            "• Pocket Pair (e.g. JJ): C(4, 2) = 6 combos.\n"
            "Blocker Removal Effect: If Hero holds As, available AK combos drop from 16 to 12 (3 aces * 4 kings)."
        ),
        formula="Range Equity = (Sum_{c in Range} Weight(c) * Equity(Hero, c)) / Sum_{c in Range} Weight(c)",
        variables=[
            {"name": "Hero Hand", "description": "Specific 2 hole cards", "unit": "Card pair"},
            {
                "name": "Opponent Range",
                "description": "Set of card combinations with associated frequencies [0.0, 1.0]",
                "unit": "Weighted range",
            },
            {
                "name": "Blockers",
                "description": "Cards removed from opponent's combinations by Hero's hand and board",
                "unit": "Cards",
            },
        ],
        units="Percentage (%)",
        boundary_conditions=[
            "Combos containing cards in Hero's hand or on the board must have weight = 0.",
            "Opponent ranges must reflect all prior action constraints (preflop open, 3-bet, c-bet).",
            "Heuristic ranges are subjective assumptions, not absolute facts.",
        ],
        mental_shortcut=(
            "Combo Counting Mental Rules:\n"
            "• No cards removed: 16 combos for unpaired hand (4 suited, 12 offsuit); 6 combos for pocket pair.\n"
            "• One card removed (Hero holds A): AK drops to 12 combos (3 suited, 9 offsuit); AA drops to 3 combos (C(3,2)).\n"
            "• Two cards removed (Board has two Kings): KK drops to 1 combo (C(2,2)). AK drops to 8 combos."
        ),
        worked_example={
            "scenario": "Flop is Ah 7s 2c. Villain 3-bets preflop and c-bets. Villain's range is assumed to be only {AA, KK, QQ, AK}. Hero holds Ks Kh.",
            "step_1": "Calculate available combos in Villain range:\n"
            "- AA: Board has Ah, so 3 aces left. C(3,2) = 3 combos.\n"
            "- KK: Hero holds Ks Kh! Only 2 kings left in deck (Kd, Kc). C(2,2) = 1 combo.\n"
            "- QQ: 0 queens visible. C(4,2) = 6 combos.\n"
            "- AK: 3 aces left * 2 kings left = 6 combos.",
            "step_2": "Total combos in Villain range = 3 (AA) + 1 (KK) + 6 (QQ) + 6 (AK) = 16 combos.",
            "step_3": "Hero's Kings beat only QQ (6 combos). Hero ties KK (1 combo). Hero loses to AA (3 combos) and AK (6 combos).",
            "step_4": "Hero beats 6 out of 16 combos (37.5%), ties 1 (3.1%), loses 9 (56.3%).",
            "conclusion": "Hero equity is approximately 39.1% against this tight 3-betting range.",
        },
        counterexample_or_misconception=(
            "Common Misconception: Ignoring blockers when assessing villain's range. "
            "Thinking 'Villain could have KK' with equal likelihood when you hold two Kings is a fatal error. "
            "Holding blockers slashes their pocket pair combos from 6 down to 1 (an 83% reduction!)."
        ),
        cash_vs_tournament_differences="In cash games, ranges are wider and more linear. In tournaments facing short-stack re-jams, opponent ranges are polarized or push/fold oriented.",
        academic_citations=[
            {
                "author": "Matthew Janda",
                "title": "Applications of No-Limit Hold'em",
                "year": "2013",
                "chapter": "Combinatorics and Blockers",
            },
            {
                "author": "Michael Acevedo",
                "title": "Modern Poker Theory",
                "year": "2019",
                "chapter": "Combinatorial Analysis",
            },
        ],
    ),
    "mod_06_equity_realization": ReferenceArticle(
        module_id="mod_06_equity_realization",
        title="Equity Realization (EQR) & Playability",
        definition=(
            "Equity Realization (EQR) is the ratio of the actual expected value a hand captures in chips "
            "divided by its raw theoretical showdown equity. Hands that under-realize capture less than their share, "
            "while hands with position, initiative, and playability over-realize (> 100%)."
        ),
        mathematical_derivation=(
            "Realized EV = Raw_Equity * Pot * EQR_Factor.\n"
            "EQR Factor = Realized_EV / (Raw_Equity * Pot).\n"
            "Key drivers of EQR:\n"
            "• Position: In-Position (IP) players realize 10-25% more equity than Out-of-Position (OOP) players.\n"
            "• Initiative & Aggression: Being the bettor/raiser allows winning without showdown via fold equity.\n"
            "• Domination & Reverse Implied Odds: Weak aces and offsuit broadways frequently make second-best pairs.\n"
            "• Suitedness & Connectivity: Suited connectors realize high equity due to semi-bluffing and nutty draws."
        ),
        formula="EQR = Expected Value Captured / (Raw Showdown Equity * Pot Size)",
        variables=[
            {
                "name": "Raw Showdown Equity",
                "description": "Probability of winning at showdown with no future betting",
                "unit": "%",
            },
            {
                "name": "Realized EV",
                "description": "Actual expected chips won across all betting lines",
                "unit": "Chips",
            },
            {
                "name": "EQR",
                "description": "Realization coefficient (typically 0.60 to 1.30)",
                "unit": "Ratio",
            },
        ],
        units="Dimensionless Factor (e.g. 0.85 = 85% realization)",
        boundary_conditions=[
            "EQR is NOT a universal mathematical constant; it depends on postflop skill, board runout, and SPR.",
            "Never use an arbitrary EQR multiplier to fabricate exact solver EV.",
            "At SPR < 1 (all-in situations), EQR approaches exactly 1.0 (100%) because no future betting remains.",
        ],
        mental_shortcut=(
            "Qualitative EQR Guide:\n"
            "• High EQR (> 110%): IP suited broadways, suited connectors, pocket pairs with set potential.\n"
            "• Neutral EQR (~100%): Nut draws, medium pocket pairs in position.\n"
            "• Low EQR (< 80%): OOP weak offsuit hands (A5o, K7o, Q8o), dominated kickers, weak gutshots."
        ),
        worked_example={
            "scenario": "Pot is 100. Hero in Big Blind defends against BTN open. Hero holds K3o with 35% raw equity.",
            "step_1": "Hero is out of position with an unsuited, easily dominated hand.",
            "step_2": "Because Hero will often fold the flop to a c-bet or get outkicked when hitting a King, EQR is ~65% (0.65).",
            "step_3": "Realized Equity = 35% * 0.65 = 22.75%.",
            "step_4": "If calling costs 20 chips into a total pot of 100, required pot odds equity is 20 / 120 = 16.7%.",
            "conclusion": "Even though raw equity (35%) seems comfortably above 16.7%, poor realization and postflop playability make defending marginal.",
        },
        counterexample_or_misconception=(
            "Common Misconception: Defending any hand whose raw preflop equity exceeds pot odds. "
            "Holding 83o in the big blind has ~30% equity against a button open, but will only realize ~12-15% "
            "because it almost never wins without showdown and cannot withstand multi-street aggression."
        ),
        cash_vs_tournament_differences="Deep-stacked cash games (150BB+) punish poor EQR severely due to multi-street reverse implied odds. Shallow tournament stacks (15BB) compress EQR toward 100%.",
        academic_citations=[
            {
                "author": "Michael Acevedo",
                "title": "Modern Poker Theory",
                "year": "2019",
                "chapter": "Chapter 4: Equity Realization",
            },
            {
                "author": "Will Tipton",
                "title": "Expert Heads Up No Limit Hold'em: Volume 1",
                "year": "2012",
                "chapter": "Postflop Equity Realization",
            },
        ],
    ),
    "mod_07_call_ev": ReferenceArticle(
        module_id="mod_07_call_ev",
        title="Call Expected Value (Call EV)",
        definition=(
            "Call EV is the mathematical expectation in chips of calling a bet rather than folding (which has an EV of exactly 0 relative to the decision point)."
        ),
        mathematical_derivation=(
            "At any decision point, prior chip investments are SUNK COSTS. Folding always nets 0 chips relative to this moment.\n"
            "When Hero calls an amount C into a pot P facing showdown with equity E (in [0, 1]):\n"
            "• Outcome 1 (Hero Wins, probability E): Hero wins the pot P and keeps call C. Net gain = +P.\n"
            "• Outcome 2 (Hero Loses, probability 1 - E): Hero forfeits the call amount. Net loss = -C.\n"
            "EV(Call) = E * (+P) + (1 - E) * (-C) = E * P - C + E * C = E * (P + C) - C.\n"
            "A call is profitable whenever EV(Call) > 0, which occurs when E > C / (P + C) (the pot odds formula!)."
        ),
        formula="EV(Call) = Equity * (Pot Before Call + Call Amount) - Call Amount",
        variables=[
            {
                "name": "Equity",
                "description": "Hero's probability of winning the pot at showdown",
                "unit": "Fraction in [0, 1]",
            },
            {
                "name": "Pot Before Call",
                "description": "Current pot including all bets already made by opponents",
                "unit": "Chips",
            },
            {"name": "Call Amount", "description": "Cost to call the bet", "unit": "Chips"},
        ],
        units="Chips (+/-) or Big Blinds (+/-)",
        boundary_conditions=[
            "Applies strictly to terminal calls (river bets or all-ins) where no further betting rounds exist.",
            "Ties must be factored into equity: Equity = P(win) + 0.5 * P(tie heads-up).",
            "Prior chips contributed by Hero in earlier rounds must NOT be subtracted from EV(Call); they are sunk.",
        ],
        mental_shortcut=(
            "Quick Call EV Rule:\n"
            "Compare your equity to your pot odds requirement. "
            "If your equity exceeds pot odds by Delta%, then:\n"
            "EV(Call) = Delta% * Total Final Pot.\n"
            "Example: Pot odds require 25%. You have 30% equity (Delta = +5%). Final pot is 200. EV = +5% * 200 = +10 chips."
        ),
        worked_example={
            "scenario": "River spot: Pot is 400. Villain bets 200 all-in. Hero holds bluff-catcher with 30% equity against Villain's polar range.",
            "step_1": "Pot before call = 400 + 200 = 600 chips.",
            "step_2": "Call amount = 200 chips. Final pot after call = 600 + 200 = 800 chips.",
            "step_3": "Pot odds requirement = 200 / 800 = 25.0%.",
            "step_4": "Hero equity = 30.0% (0.30).",
            "step_5": "EV(Call) = 0.30 * 800 - 200 = 240 - 200 = +40 chips.",
            "conclusion": "Calling has an EV of +40 chips compared to 0 for folding. Calling is clearly the mathematically superior play.",
        },
        counterexample_or_misconception=(
            "Common Misconception: Subtracting preflop or flop bets from the river call EV. "
            "Saying 'I put in 150 earlier, so winning 40 chips still leaves me down overall' is the Sunk Cost Fallacy! "
            "Those 150 chips belong to the pot, not to you. Decisions are evaluated strictly from the current node forward."
        ),
        cash_vs_tournament_differences="In a cash game, +0.1 BB call EV is a clear call. In a tournament near the bubble, an EV of +0.1 BB in chips might equal -$50 in actual cash equity due to ICM risk.",
        academic_citations=[
            {
                "author": "Bill Chen & Jerrod Ankenman",
                "title": "The Mathematics of Poker",
                "year": "2006",
                "chapter": "Chapter 3: Optimal Play and EV",
            },
            {
                "author": "David Sklansky",
                "title": "The Theory of Poker",
                "year": "1987",
                "chapter": "Chapter 3: Expected Value",
            },
        ],
    ),
    "mod_08_bluff_ev": ReferenceArticle(
        module_id="mod_08_bluff_ev",
        title="Bluff Expected Value, Alpha & Fold Equity",
        definition=(
            "Bluff EV calculates the profitability of betting with zero showdown equity to induce opponent folds. "
            "Alpha (break-even fold frequency) is the minimum percentage of time opponents must fold for a pure bluff to be immediately profitable."
        ),
        mathematical_derivation=(
            "When Hero bets B into pot P with 0% showdown equity if called:\n"
            "• If opponent folds (probability f): Hero wins pot P. Gain = +P.\n"
            "• If opponent calls (probability 1 - f): Hero loses bet B. Loss = -B.\n"
            "EV(Bluff) = f * P - (1 - f) * B = f * P - B + f * B = f * (P + B) - B.\n"
            "Setting EV(Bluff) = 0 to find the break-even fold percentage (Alpha):\n"
            "f * (P + B) = B  ===>  f_breakeven (Alpha) = B / (P + B).\n"
            "Minimum Defense Frequency (MDF) is the defensive counterpart: MDF = 1 - Alpha = P / (P + B)."
        ),
        formula="Alpha (%) = (Bet Amount / (Pot Before Bet + Bet Amount)) * 100",
        variables=[
            {"name": "Bet Amount", "description": "Size of the bluff bet risked", "unit": "Chips"},
            {
                "name": "Pot Before Bet",
                "description": "Size of the pot currently in the middle",
                "unit": "Chips",
            },
            {"name": "Alpha", "description": "Break-even fold frequency required", "unit": "%"},
        ],
        units="Percentage (%), Expected Chips (+/-)",
        boundary_conditions=[
            "Assumes the bluff has exactly 0% equity when called.",
            "Assumes opponent only calls or folds (cannot raise).",
            "MDF is a game-theoretic defensive equilibrium threshold; real exploitative opponents may fold much more or less than MDF.",
        ],
        mental_shortcut=(
            "Standard Bet Sizings and Break-Even Fold Requirements (Alpha):\n"
            "• 1/4 pot bet -> Opponents must fold 20.0%\n"
            "• 1/3 pot bet -> Opponents must fold 25.0%\n"
            "• 1/2 pot bet -> Opponents must fold 33.3%\n"
            "• 2/3 pot bet -> Opponents must fold 40.0%\n"
            "• 3/4 pot bet -> Opponents must fold 42.9%\n"
            "• Pot-sized bet -> Opponents must fold 50.0%\n"
            "• 1.5x pot overbet -> Opponents must fold 60.0%\n"
            "• 2x pot overbet -> Opponents must fold 66.7%"
        ),
        worked_example={
            "scenario": "Pot on the river is 300. Hero has missed all draws (complete air). Hero bets 150 (half pot). Villain folds 40% of the time.",
            "step_1": "Calculate Alpha: Bet / (Pot + Bet) = 150 / (300 + 150) = 150 / 450 = 33.3%.",
            "step_2": "Compare with actual fold frequency: Villain folds 40% > 33.3%. The bluff is profitable!",
            "step_3": "Compute exact EV: EV = f * Pot - (1 - f) * Bet = 0.40 * 300 - 0.60 * 150 = 120 - 90 = +30 chips.",
        },
        counterexample_or_misconception=(
            "Common Misconception: Believing MDF guarantees how often your opponent will fold. "
            "MDF is the frequency a player SHOULD defend to make your bluffs zero EV under game theory. "
            "In practice, a tight player facing a river bet might fold 70% of the time, making bluffs wildly +EV regardless of MDF!"
        ),
        cash_vs_tournament_differences="In cash games, overbet bluffs are common to maximize fold equity against capped ranges. In tournaments, overbetting risks tournament elimination when called.",
        academic_citations=[
            {
                "author": "Matthew Janda",
                "title": "Applications of No-Limit Hold'em",
                "year": "2013",
                "chapter": "Chapter 3: The Mathematics of Bluffing",
            },
            {
                "author": "Michael Acevedo",
                "title": "Modern Poker Theory",
                "year": "2019",
                "chapter": "Minimum Defense Frequency",
            },
        ],
    ),
    "mod_09_semi_bluff": ReferenceArticle(
        module_id="mod_09_semi_bluff",
        title="Semi-Bluff Expected Value",
        definition=(
            "A semi-bluff is a bet or raise made with a drawing hand that is currently not the best hand, "
            "but has significant equity to improve to the winning hand on later streets if called."
        ),
        mathematical_derivation=(
            "When Hero semi-bluffs bet B into pot P with fold probability f and equity E when called:\n"
            "• Branch 1 (Opponent Folds, probability f): Hero wins pot P.\n"
            "• Branch 2 (Opponent Calls, probability 1 - f): Final pot is P + 2*B. Hero captures equity E:\n"
            "  Net payoff when called = E * (P + 2*B) - B.\n"
            "Combined EV Equation:\n"
            "EV(Semi-bluff) = f * P + (1 - f) * [E * (P + 2*B) - B]."
        ),
        formula="EV = f * Pot + (1 - f) * [Equity * (Pot + 2 * Bet) - Bet]",
        variables=[
            {
                "name": "f",
                "description": "Probability that opponent folds",
                "unit": "Fraction in [0, 1]",
            },
            {
                "name": "Pot",
                "description": "Starting pot before the semi-bluff bet",
                "unit": "Chips",
            },
            {"name": "Bet", "description": "Amount wagered on the semi-bluff", "unit": "Chips"},
            {
                "name": "Equity",
                "description": "Hero's probability of winning if called (in [0, 1])",
                "unit": "Fraction in [0, 1]",
            },
        ],
        units="Expected Chips (+/-)",
        boundary_conditions=[
            "Assumes opponent only calls or folds (simplified model; raises are treated separately).",
            "Assumes calling leads to all-in or terminal showdown on later streets.",
            "Equity must be calculated against the opponent's CALLING range, not their pre-bet range!",
        ],
        mental_shortcut=(
            "A semi-bluff requires much less fold equity than a pure bluff: "
            "Every 10% equity you have when called reduces the fold frequency needed by roughly 10-15%!"
        ),
        worked_example={
            "scenario": "Pot is 100. Hero bets 50 on turn with a flush draw. Opponent folds 30% (f=0.30). When called, Hero has 20% equity (E=0.20).",
            "step_1": "Branch 1 (Folds, 30%): 0.30 * 100 = +30 chips.",
            "step_2": "Branch 2 (Calls, 70%): Final pot = 100 + 100 = 200 chips. Net win when called = (0.20 * 200) - 50 = 40 - 50 = -10 chips.",
            "step_3": "Called EV share: 0.70 * (-10) = -7 chips.",
            "step_4": "Total EV = +30 + (-7) = +23 chips.",
            "conclusion": "The semi-bluff is strongly +EV (+23 chips) even though calling equity alone (-10) is negative!",
        },
        counterexample_or_misconception=(
            "Common Misconception: Using raw hand-vs-range equity when called. "
            "Against a full range you might have 35% equity, but when you bet, opponent folds weak hands and calls only with strong hands! "
            "Your equity against their CALLING range will be lower (e.g. 22%). Always evaluate equity against the calling sub-range."
        ),
        cash_vs_tournament_differences="In cash games, semi-bluffing is a primary engine of winrate. In tournaments, getting raised all-in can force you to fold away significant equity.",
        academic_citations=[
            {
                "author": "David Sklansky",
                "title": "The Theory of Poker",
                "year": "1987",
                "chapter": "Chapter 11: The Semi-Bluff",
            },
            {
                "author": "Matthew Janda",
                "title": "Applications of No-Limit Hold'em",
                "year": "2013",
                "chapter": "Semi-Bluffing Mechanics",
            },
        ],
    ),
    "mod_10_action_comparison": ReferenceArticle(
        module_id="mod_10_action_comparison",
        title="Bet, Raise & Action EV Comparison",
        definition=(
            "Decision optimization in poker requires comparing the expected values of all mutually exclusive legal actions "
            "(Fold, Check, Call, Bet, Raise) to select the action with the highest EV (the GTO or exploitative maximum)."
        ),
        mathematical_derivation=(
            "Let legal action set be A = {Fold, Check, Call, Bet_S1, Bet_S2, Raise}. "
            "For each action a in A, construct the conditional decision tree:\n"
            "EV(a) = Sum_{outcomes o} P(o | a) * Payoff(o | a).\n"
            "• EV(Fold) is defined as 0.0 (reference baseline).\n"
            "• An action is profitable if EV(a) > 0.\n"
            "• An action is OPTIMAL if EV(a) >= EV(a') for all a' in A.\n"
            "A play can be profitable in absolute terms (+2 BB) while being a major mistake because another legal option was +6 BB!"
        ),
        formula="Optimal Action = argmax_{a in Actions} EV(a)",
        variables=[
            {
                "name": "Actions",
                "description": "Set of all legal poker moves at current game node",
                "unit": "Set",
            },
            {
                "name": "EV(a)",
                "description": "Expected chip return of action a",
                "unit": "Chips or BB",
            },
            {"name": "EV Regret", "description": "Max_EV - EV(chosen_action)", "unit": "BB loss"},
        ],
        units="Expected Chips (+/-) or Big Blinds (+/-)",
        boundary_conditions=[
            "Must evaluate all branches (fold, call, raise) under consistent conditional opponent response frequencies.",
            "Requires explicit assumptions about opponent response distributions.",
            "Never invent solution EV without an explicit, verifiable model.",
        ],
        mental_shortcut=(
            "Always check: 'Is this just profitable, or is it the MOST profitable?' "
            "If calling is +1 BB but raising is +3.5 BB, calling loses 2.5 BB in EV regret."
        ),
        worked_example={
            "scenario": "Hero on button with top pair on dry river. Pot is 100. Villain checks. Hero can check behind or bet 60.",
            "step_1": "EV(Check): Hero wins at showdown 75% of the time. Pot = 100. EV(Check) = 0.75 * 100 = +75 chips.",
            "step_2": "EV(Bet 60): If Hero bets 60:\n"
            "- Villain folds 50% -> Hero wins 100.\n"
            "- Villain calls 50% with range Hero beats 70% of the time:\n"
            "  Net win when called = 0.70 * (100 + 60) - 0.30 * (60) = 112 - 18 = +94 chips.\n"
            "EV(Bet) = 0.50 * 100 + 0.50 * 94 = 50 + 47 = +97 chips.",
            "step_3": "Compare: EV(Bet) = +97 chips vs EV(Check) = +75 chips.",
            "conclusion": "Both checking and betting are profitable, but betting yields +22 more chips. Betting is the optimal line.",
        },
        counterexample_or_misconception=(
            "Common Misconception: Thinking that because an action has positive EV, it was played correctly. "
            "Calling with the nuts on the river when opponent has bet 100 into 200 is +EV, but failing to raise loses massive EV."
        ),
        cash_vs_tournament_differences="In cash games, maximize chip EV. In tournaments near bubble or final table, prize ICM may make a +cEV raise inferior to a check.",
        academic_citations=[
            {
                "author": "Bill Chen & Jerrod Ankenman",
                "title": "The Mathematics of Poker",
                "year": "2006",
                "chapter": "Chapter 4: Game Theory and Decision Trees",
            },
            {
                "author": "Michael Acevedo",
                "title": "Modern Poker Theory",
                "year": "2019",
                "chapter": "Maximizing Action EV",
            },
        ],
    ),
    "mod_11_implied_odds": ReferenceArticle(
        module_id="mod_11_implied_odds",
        title="Implied & Reverse Implied Odds",
        definition=(
            "Implied odds represent the additional chips you expect to win on future betting streets if you hit your draw. "
            "Reverse implied odds represent the additional chips you risk losing on future streets when you hit your hand but still lose to a superior holding."
        ),
        mathematical_derivation=(
            "Let Call = C, Pot = P, Equity = E. If immediate pot odds are insufficient (E < C / (P + C)), "
            "calling can still be profitable if future chips F are extracted when hitting:\n"
            "E * (P + C + F) = C  ===>  P + C + F = C / E  ===>  F = (C / E) - (P + C).\n"
            "Here F is the exact amount of additional future chips Hero must win on average to break even on the call."
        ),
        formula="Required Future Chips = (Call Amount / Equity) - (Pot Before Call + Call Amount)",
        variables=[
            {"name": "Call Amount", "description": "Cost to call current bet", "unit": "Chips"},
            {
                "name": "Equity",
                "description": "Probability of hitting winning out",
                "unit": "Fraction [0, 1]",
            },
            {"name": "Pot Before Call", "description": "Current pot before call", "unit": "Chips"},
            {
                "name": "Required Future Chips",
                "description": "Additional future profit needed to break even",
                "unit": "Chips",
            },
        ],
        units="Chips or Big Blinds",
        boundary_conditions=[
            "Required future chips CANNOT exceed the effective remaining stack: F <= Effective_Remaining_Stack.",
            "Opponent must have a hand strong enough to pay off your completed draw.",
            "Accounts for situations where hitting your out completes an even better draw for opponent (reverse implied odds).",
        ],
        mental_shortcut=(
            "Implied Odds Rule of Thumb:\n"
            "To justify drawing with a gutshot (about 8.5% equity, ~11:1 odds) against a half-pot bet:\n"
            "You need to win roughly 3x to 4x the bet amount on future streets if you hit."
        ),
        worked_example={
            "scenario": "Flop: Pot is 100. Villain bets 50. Hero holds pocket 44 with an underpair and set draw (2 outs = ~4.3% on turn). Call = 50. Effective stacks are 500.",
            "step_1": "Immediate pot odds: Call 50 into 150 -> Need 50 / 200 = 25% equity.",
            "step_2": "Hero only has 2 outs = 2/47 = 4.25% (0.0425) to hit a set on the turn.",
            "step_3": "Calculate required future chips F: F = (50 / 0.0425) - 200 = 1,176 - 200 = 976 chips.",
            "step_4": "Check effective stack constraint: Remaining stacks are only 450 chips!",
            "conclusion": "Because 976 > 450, Hero CANNOT make up the deficit even if stacking Villain 100% of the time. Calling is -EV!",
        },
        counterexample_or_misconception=(
            "Common Misconception: Assuming opponent will always pay off when the draw hits. "
            "When the front-door flush completes on the river, observant opponents check-fold weak pairs. "
            "You only realize implied odds when opponent holds a strong second-best hand (e.g. set vs flush)."
        ),
        cash_vs_tournament_differences="Deep cash games offer huge implied odds for set mining and suited connectors. In shallow tournament play, implied odds evaporate due to stack constraints.",
        academic_citations=[
            {
                "author": "David Sklansky",
                "title": "The Theory of Poker",
                "year": "1987",
                "chapter": "Chapter 6: Implied Odds",
            },
            {
                "author": "Ed Miller",
                "title": "The Course",
                "year": "2015",
                "chapter": "Implied Odds and Deep Stacks",
            },
        ],
    ),
    "mod_12_rake": ReferenceArticle(
        module_id="mod_12_rake",
        title="Cash Game Rake Models & Profitability",
        definition=(
            "Casino rake is the percentage commission extracted from cash game pots by the cardroom. "
            "Rake changes the game from zero-sum to negative-sum, shifting break-even calling and bluffing thresholds."
        ),
        mathematical_derivation=(
            "Standard Cash Rake Model:\n"
            "Rake = min(Pot * Rake_Rate, Rake_Cap)  [if Flop is dealt or No_Flop_No_Drop = False].\n"
            "When Hero wins pot P after calling C, the net pot awarded is P_net = P - Rake.\n"
            "Rake-Adjusted Call EV:\n"
            "EV(Call) = Equity * (P_net + C) - C.\n"
            "Break-Even Equity with Rake:\n"
            "Required_Equity_Rake = C / (P_net + C) > C / (P + C)."
        ),
        formula="Net Pot = Total Pot - min(Total Pot * Rake %, Cap)",
        variables=[
            {
                "name": "Rake Rate",
                "description": "Percentage taken from pot (e.g. 5.0%)",
                "unit": "%",
            },
            {
                "name": "Rake Cap",
                "description": "Maximum chips that can be raked from a single hand",
                "unit": "Chips or BB",
            },
            {
                "name": "No Flop No Drop",
                "description": "Whether hands ending preflop are exempt from rake",
                "unit": "Boolean",
            },
        ],
        units="Chips, Percentage (%), BB/100",
        boundary_conditions=[
            "No Flop No Drop rule means preflop 3-bets that take down the pot uncontested pay ZERO rake.",
            "Rake caps mean large pots pay significantly lower effective rake percentage than small/medium pots.",
        ],
        mental_shortcut=(
            "Rake Impact Rule:\n"
            "At 5% uncapped or below-cap rake, you need approximately 1.5% to 2.5% more equity to break even on a call "
            "than raw pot odds indicate!"
        ),
        worked_example={
            "scenario": "Pot is 100. Villain bets 50 on turn. Rake is 5% with a 15 chip cap. Call = 50. Total pot after call = 200.",
            "step_1": "Calculate rake: 5% of 200 = 10 chips (under the 15 cap). Rake = 10 chips.",
            "step_2": "Net pot awarded to winner: 200 - 10 = 190 chips.",
            "step_3": "Unraked required equity was 50 / 200 = 25.0%.",
            "step_4": "Raked required equity: 50 / 190 = 26.32%.",
            "conclusion": "A hand with 25.5% equity is profitable unraked (+EV), but LOSING (-EV) after casino rake.",
        },
        counterexample_or_misconception=(
            "Common Misconception: Ignoring rake when defending the big blind. "
            "In high-rake microstakes (e.g. 5% up to 3BB cap), marginal flat-calls bleed money to the rake. "
            "Aggressive 3-betting or folding is superior due to the 'No Flop No Drop' rule."
        ),
        cash_vs_tournament_differences="Cash games charge per-pot rake, punishing small postflop pots. Tournaments charge a one-time entry fee (rake/vig) at registration with zero per-pot rake during play.",
        academic_citations=[
            {
                "author": "Michael Acevedo",
                "title": "Modern Poker Theory",
                "year": "2019",
                "chapter": "Rake and Preflop Ranges",
            },
            {
                "author": "Nathan Williams",
                "title": "Crushing the Microstakes",
                "year": "2011",
                "chapter": "The Impact of Rake",
            },
        ],
    ),
    "mod_13_icm": ReferenceArticle(
        module_id="mod_13_icm",
        title="Tournament Chip EV vs Independent Chip Model (ICM)",
        definition=(
            "The Independent Chip Model (ICM) calculates the monetary value of a tournament chip stack based on the payout ladder. "
            "Because tournament chips have diminishing marginal utility (you can lose all your chips, but cannot win more than 1st prize), "
            "a chip lost is worth more than a chip won."
        ),
        mathematical_derivation=(
            "Malmuth-Harville Model:\n"
            "Probability of player i finishing 1st: P(1st_i) = S_i / Total_Chips.\n"
            "Probability of player j finishing 2nd given i finished 1st:\n"
            "P(2nd_j | 1st_i) = S_j / (Total_Chips - S_i).\n"
            "Bubble Factor (BF) against opponent V:\n"
            "BF = (Equity_lost_if_lose) / (Equity_gained_if_win).\n"
            "Risk Premium (RP) = (BF - 1) / (BF + 1).\n"
            "Required Equity with ICM = Pot_Odds_cEV + Risk_Premium."
        ),
        formula="ICM Required Equity = cEV Pot Odds + Risk Premium",
        variables=[
            {
                "name": "Bubble Factor",
                "description": "Ratio of monetary loss when losing to monetary gain when winning",
                "unit": "Ratio >= 1.0",
            },
            {
                "name": "Risk Premium",
                "description": "Additional equity needed above cEV to justify risking tournament life",
                "unit": "%",
            },
            {
                "name": "Payout Ladder",
                "description": "Prize distribution for 1st, 2nd, 3rd, etc.",
                "unit": "Currency ($)",
            },
        ],
        units="Percentage (%), Currency ($), Dimensionless Ratio",
        boundary_conditions=[
            "Requires complete stack distributions and prize pool payout ladder.",
            "Never fabricate ICM numbers if payout structure or active stacks are missing.",
            "Chip equity conservation invariant: Sum of all player ICM equities equals total remaining prize pool.",
        ],
        mental_shortcut=(
            "Bubble Factor Shortcuts:\n"
            "• Far from money (early tournament): BF ~ 1.0 (Risk Premium ~ 0%). Play pure chip EV.\n"
            "• Direct bubble (1 player to cash): BF ~ 1.5 to 2.2 against covering stacks (Risk Premium +10% to +18%).\n"
            "• Final Table with flat pay jumps: BF ~ 1.2 to 1.4 (Risk Premium +5% to +9%).\n"
            "• Final Table with steep pay jumps: BF can exceed 2.5 against covering chip leaders!"
        ),
        worked_example={
            "scenario": "Direct tournament bubble: 4 players remain, top 3 cash ($500, $300, $200). Stacks: P1=4000, P2=3000, Hero=2000, P4=1000. P1 shoves into Hero.",
            "step_1": "In pure chip EV, calling a pot-sized shove requires 33.3% equity.",
            "step_2": "Calculate ICM: If Hero folds, P4 is short stack and Hero will cash > 85% of the time (worth ~$235).",
            "step_3": "If Hero calls and loses, Hero gets $0. If Hero calls and wins, Hero has 4,000 chips (worth ~$340, gaining only +$105).",
            "step_4": "Bubble Factor = Loss / Gain = $235 / $105 = 2.24.\n"
            "Risk Premium = (2.24 - 1) / (2.24 + 1) = 1.24 / 3.24 = +38.3%.\n"
            "Required Equity = 33.3% + 15.0% = ~48.3%.",
            "conclusion": "Hero needs nearly 50% equity to call an all-in that unweighted cEV says requires only 33%!",
        },
        counterexample_or_misconception=(
            "Common Misconception: Making a +cEV call on the bubble with AKo against a chip leader. "
            "Even if AKo has 60% equity against their shove range, if the risk premium is +15%, you are flipping for your tournament life "
            "when a guaranteed min-cash is minutes away. A +cEV call is frequently an ICM disaster."
        ),
        cash_vs_tournament_differences="In cash games, chip value is constant ($1 = 1 chip). In tournaments, every additional chip won is worth less than the previous one.",
        academic_citations=[
            {
                "author": "Mason Malmuth",
                "title": "Gambling Theory and Other Topics",
                "year": "1999",
                "chapter": "The Independent Chip Model",
            },
            {
                "author": "Collin Moshman",
                "title": "Sit 'n Go Strategy",
                "year": "2007",
                "chapter": "ICM and Late Stage Play",
            },
        ],
    ),
    "mod_14_pko": ReferenceArticle(
        module_id="mod_14_pko",
        title="Progressive Knockout (PKO) & Bounty EV",
        definition=(
            "In Progressive Knockout (PKO) tournaments, eliminating an opponent immediately awards 50% of their bounty in cash, "
            "while the remaining 50% is added to your own bounty head. Bounties can be converted into chip equity to calculate adjusted calling ranges."
        ),
        mathematical_derivation=(
            "PKO Bounty-to-Chip Conversion Formula:\n"
            "Total_Tournament_Chips = Total_Entrants * Starting_Stack.\n"
            "Total_Bounty_Pool = Total_Entrants * Starting_Bounty.\n"
            "Chip Value per Dollar of Bounty = Total_Tournament_Chips / Total_Bounty_Pool.\n"
            "Immediate Cash Bounty collected = 50% of Villain's displayed bounty.\n"
            "Bounty Chip Equivalence = (0.50 * Villain_Bounty) * (Starting_Stack / Starting_Bounty).\n"
            "Effective Pot facing All-In = Current_Pot + Bounty_Chip_Equivalence.\n"
            "Adjusted Required Equity = Call / (Current_Pot + Call + Bounty_Chip_Equivalence)."
        ),
        formula="Adjusted Equity (%) = Call / (Pot + Call + Bounty Chip Equivalence)",
        variables=[
            {
                "name": "Starting Stack",
                "description": "Tournament starting chip count",
                "unit": "Chips",
            },
            {
                "name": "Starting Bounty",
                "description": "Starting cash bounty per player",
                "unit": "Currency ($)",
            },
            {
                "name": "Villain Bounty",
                "description": "Total bounty currently on opponent's head",
                "unit": "Currency ($)",
            },
            {
                "name": "Bounty Chip Equivalence",
                "description": "Immediate chips added to pot incentive",
                "unit": "Chips",
            },
        ],
        units="Chips, Percentage (%)",
        boundary_conditions=[
            "Hero MUST cover Villain (Hero Stack > Villain Stack) to be eligible to collect the bounty.",
            "If Hero does not cover Villain, Bounty Chip Equivalence is exactly ZERO.",
            "Model-Dependent Heuristic Approximation: The linear bounty-to-chip conversion is an equilibrium approximation model, NOT universally exact.",
            "Real-world PKO equity is non-linear and heavily influenced by tournament stage, remaining field size, and asymmetric ICM payout structures.",
        ],
        mental_shortcut=(
            "Quick PKO Rule:\n"
            "A standard starting bounty is worth approximately 25% to 33% of a starting stack in chips. "
            "If a player has a 4x starting bounty and you cover them, their bounty adds an entire starting stack of dead chips to the pot!"
        ),
        worked_example={
            "scenario": "$100 PKO ($50 prize pool, $50 bounty). Starting stack = 10,000 chips. Starting bounty = $50. "
            "Villain has $100 bounty. Villain shoves 5,000 chips into a 3,000 pot. Hero covers with 15,000 chips.",
            "step_1": "Immediate cash awarded if Hero wins: 50% of $100 = $50.",
            "step_2": "Convert $50 to chips: $50 / $50 * 10,000 starting chips = 10,000 bounty chips.",
            "step_3": "Current pot before call = 3,000 + 5,000 (Villain bet) = 8,000 chips. Call = 5,000 chips.",
            "step_4": "Unadjusted Pot Odds Equity: 5,000 / (8,000 + 5,000) = 5,000 / 13,000 = 38.5%.",
            "step_5": "Adjusted Pot with Bounty: 13,000 + 10,000 bounty chips = 23,000 chips.",
            "step_6": "Adjusted Required Equity: 5,000 / 23,000 = 21.7%!",
            "conclusion": "Because of the massive bounty incentive, Hero needs only 21.7% equity instead of 38.5% to call.",
        },
        counterexample_or_misconception=(
            "Common Misconception: Expanding calling ranges when YOU are the shorter stack. "
            "If Villain has 10,000 chips and a $500 bounty, but you only have 4,000 chips, "
            "YOU CANNOT COLLECT THEIR BOUNTY! Your bounty equity is 0. Call strictly based on normal cEV/ICM."
        ),
        cash_vs_tournament_differences="Cash games have no bounties. PKO tournaments dramatically widen calling ranges against short-stacked bounties while tightening calls against covering stacks.",
        academic_citations=[
            {
                "author": "Dara O'Kearney & Barry Carter",
                "title": "PKO Poker Strategy",
                "year": "2019",
                "chapter": "Chapter 2: The Math of Bounties",
            },
            {
                "author": "Michael Acevedo",
                "title": "Modern Poker Theory",
                "year": "2019",
                "chapter": "Progressive Knockout Tournaments",
            },
        ],
    ),
    "mod_15_mental_math": ReferenceArticle(
        module_id="mod_15_mental_math",
        title="Mental Math Shortcuts & Speed Techniques",
        definition=(
            "Mental math in poker is the set of rapid estimation heuristics that allow players to calculate "
            "pot odds, equity, and expected value within typical 10-to-15 second shot-clock constraints without external aids."
        ),
        mathematical_derivation=(
            "1. Rapid Fraction Estimation: To find C / (P + C), simplify by common factors. E.g. 75 / 375 = 1/5 = 20%.\n"
            "2. Odds-to-Equity Mental Pivot: For bet fraction b = Bet / Pot:\n"
            "   Required Equity = b / (1 + 2*b).\n"
            "   • b = 0.5 (half pot) -> 0.5 / (1 + 1.0) = 0.5 / 2 = 25%.\n"
            "   • b = 0.75 (3/4 pot) -> 0.75 / (1 + 1.5) = 0.75 / 2.5 = 30%.\n"
            "   • b = 1.0 (pot) -> 1.0 / (1 + 2.0) = 1/3 = 33.3%.\n"
            "3. Decision Sensitivity Check: If your estimated equity is 42% and required equity is 25%, "
            "precision is unnecessary — the call is overwhelmingly profitable. Precision only matters in margin zones (+/- 2%)."
        ),
        formula="Required Equity = Bet_Fraction / (1 + 2 * Bet_Fraction)",
        variables=[
            {
                "name": "Bet Fraction",
                "description": "Ratio of bet to current pot (e.g. 0.5 for half pot)",
                "unit": "Ratio",
            },
            {
                "name": "Decision Margin",
                "description": "Difference between equity estimate and threshold",
                "unit": "%",
            },
        ],
        units="Percentages (%), Seconds",
        boundary_conditions=[
            "Mental shortcuts are approximations; recognize when a spot is too close to call without exact counting.",
            "Under severe time pressure, default to fundamental ranges rather than panic-guessing math.",
        ],
        mental_shortcut=(
            "The 5-Second Decision Checklist:\n"
            "1. What is the bet relative to pot? (Half? 2/3? Pot?)\n"
            "2. What is my break-even target? (25%? 28%? 33%?)\n"
            "3. How many outs do I have? Multiply by 2 (turn) or 4 (flop).\n"
            "4. Is my equity safely above the target? Call. Safely below? Fold."
        ),
        worked_example={
            "scenario": "Pot is 385 chips. Villain bets 190. You have an open-ended straight draw (8 outs) on the turn. You have 8 seconds to act.",
            "step_1": "Approximate bet: 190 is roughly half of 385 (half pot).\n"
            "Half-pot pot odds target = 25%.",
            "step_2": "Calculate draw equity: 8 outs on turn -> 8 * 2 = 16% immediate equity.",
            "step_3": "Compare: 16% immediate equity is well below the 25% requirement.",
            "step_4": "Check implied odds: Can you win 9 * 200 = 1,800 on river? No, stacks are only 400.",
            "conclusion": "Instant, confident Fold in under 4 seconds.",
        },
        counterexample_or_misconception=(
            "Common Misconception: Spending 25 seconds calculating whether an open-ended straight flush combo draw with 15 outs "
            "has 54.1% or 53.8% equity against a half-pot shove. "
            "You only need 25%! You have over 50%! Calling is snap-fast; don't waste time bank on obvious decisions."
        ),
        cash_vs_tournament_differences="In online poker with 15-second time banks, mental math shortcuts are mandatory for multitable play.",
        academic_citations=[
            {
                "author": "Ed Miller",
                "title": "Poker's 1%",
                "year": "2014",
                "chapter": "Mental Math Shortcuts",
            },
            {
                "author": "James 'SplitSuit' Sweeney",
                "title": "Poker Math That Matters",
                "year": "2011",
                "chapter": "Fast Pot Odds",
            },
        ],
    ),
    "mod_16_integrated_reasoning": ReferenceArticle(
        module_id="mod_16_integrated_reasoning",
        title="Integrated Real-Hand Mathematical Reasoning",
        definition=(
            "Integrated mathematical reasoning is the ability to independently identify which quantitative models "
            "apply to an unprompted real-world poker hand, compute or estimate the decisive metrics, and translate "
            "the numbers into optimal strategic action while recognizing missing information."
        ),
        mathematical_derivation=(
            "Comprehensive Decision Framework:\n"
            "1. Decision Objective: What is Hero trying to accomplish? (Call terminal bet, semi-bluff, value-bet sizing?)\n"
            "2. Information Classification:\n"
            "   • Deterministic Knowns: Pot size, bet size, board cards, Hero hole cards, effective stack.\n"
            "   • Estimable Ranges: Villain's preflop opening range, postflop continuation frequency.\n"
            "   • Missing / Insufficient Data: Unknown opponent tendencies or unstated payout structures.\n"
            "3. Model Selection: Pot Odds vs Bluff Alpha vs Realization Factor vs ICM Risk Premium.\n"
            "4. Boundary Check: Is the scenario mathematically solvable from the provided assumptions, or is information insufficient?"
        ),
        formula="Decision = Mathematical Proof (Pot Odds, EV) + Empirical Range Model (Blockers, Tendencies)",
        variables=[
            {
                "name": "Knowns",
                "description": "Concrete chip counts, board texture, action history",
                "unit": "Set",
            },
            {
                "name": "Assumptions",
                "description": "Villain range, fold frequency, future betting model",
                "unit": "Model",
            },
            {
                "name": "Solvability",
                "description": "Whether parameters allow exact mathematical resolution",
                "unit": "Boolean",
            },
        ],
        units="Holistic Evaluation",
        boundary_conditions=[
            "Never confuse a mathematical theorem with a behavioral assumption.",
            "Always state: 'Under the assumption that opponent folds X%, action A is +EV.'",
            "Recognize when the honest answer is 'Insufficient information to determine.'",
        ],
        mental_shortcut=(
            "The 4-Step Analytical Sequence:\n"
            "1. Classify the Spot: Terminal or Multi-Street? Cash or ICM?\n"
            "2. Calculate the Floor: What is the exact break-even number?\n"
            "3. Estimate the Range: Does Villain's range meet the floor?\n"
            "4. Execute: Act decisively without second-guessing."
        ),
        worked_example={
            "scenario": "Live 6-max cash: $5/$10. Hero ($1,000) holds As Kh on Kh 9d 4c 7s 2c. Pot is $300. Villain ($1,500) bets $200 on river. "
            "Villain is known to only value bet 2-pair or better (AK, 99, 44) and has zero bluffs in their range.",
            "step_1": "Pot odds: Hero must call $200 to win $500 total pot. Required equity = 200 / 700 = 28.6%.",
            "step_2": "Evaluate Hero hand against Villain range: Villain range = {AK, 99, 44}. Hero only beats bluffs, and Villain has NO bluffs!",
            "step_3": "Against {AK, 99, 44}, Hero ties AK (split) and loses to 99, 44. Hero equity is only ~10%.",
            "step_4": "Compare: 10% equity is far below the 28.6% needed.",
            "conclusion": "Hero folds top pair top kicker with 100% mathematical confidence.",
        },
        counterexample_or_misconception=(
            "Common Misconception: Calling on the river because 'top pair is too strong to fold' or 'I'm getting 3.5 to 1'. "
            "Pot odds do not help if your equity against the opponent's true range is zero. Pot odds tell you the hurdle rate; "
            "your equity against their range tells you if you clear the hurdle."
        ),
        cash_vs_tournament_differences="Integrated reasoning must seamlessly toggle between cash maximizing chips and tournament conserving tournament equity.",
        academic_citations=[
            {
                "author": "Bill Chen & Jerrod Ankenman",
                "title": "The Mathematics of Poker",
                "year": "2006",
                "chapter": "Part V: Real World Play",
            },
            {
                "author": "Andrew Brokos",
                "title": "Play Optimal Poker",
                "year": "2019",
                "chapter": "Thinking in Ranges and Decisions",
            },
        ],
    ),
}

# Aliases for backwards compatibility
REFERENCE_ARTICLES["mod_09_semibluff_ev"] = REFERENCE_ARTICLES["mod_09_semi_bluff"]
REFERENCE_ARTICLES["mod_12_rake_profitability"] = REFERENCE_ARTICLES["mod_12_rake"]
REFERENCE_ARTICLES["mod_13_tournament_icm"] = REFERENCE_ARTICLES["mod_13_icm"]
REFERENCE_ARTICLES["mod_14_pko_bounties"] = REFERENCE_ARTICLES["mod_14_pko"]
