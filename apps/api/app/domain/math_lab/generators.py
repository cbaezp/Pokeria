"""Exercise Generators for Poker Math Lab.

Deterministic, seeded, difficulty-aware generators for all 16 curriculum modules.
Generates valid poker situations, cards, pot geometries, exact solutions, step-by-step
derivations, reasonable tolerances, and diagnostic mistake classifications.
"""

from __future__ import annotations

import random

from app.domain.math_lab.models import (
    MathDifficulty,
    MathExercise,
    MathGameFormat,
    MathQuestionType,
    MistakeClassification,
)
from app.domain.poker.math import (
    bluff_break_even_percentage,
    call_expected_value,
    fold_equity_ev,
    minimum_defense_frequency,
    outs_to_equity,
)


class MathExerciseGenerator:
    """Base and factory generator for all mathematical exercises."""

    @classmethod
    def generate(
        cls,
        module_id: str,
        difficulty: MathDifficulty = MathDifficulty.BEGINNER,
        game_format: MathGameFormat = MathGameFormat.CASH_6MAX,
        seed: int | None = None,
    ) -> MathExercise:
        """Generate a deterministic exercise for the given module, difficulty, and format."""
        rng = random.Random(seed if seed is not None else random.randint(1, 999_999_999))
        effective_seed = rng.randint(1, 999_999_999)

        generator_map = {
            "mod_01_arithmetic": cls._gen_mod_01,
            "mod_02_pot_odds": cls._gen_mod_02,
            "mod_03_outs_draws": cls._gen_mod_03,
            "mod_04_equity_fundamentals": cls._gen_mod_04,
            "mod_05_equity_ranges": cls._gen_mod_05,
            "mod_06_equity_realization": cls._gen_mod_06,
            "mod_07_call_ev": cls._gen_mod_07,
            "mod_08_bluff_ev": cls._gen_mod_08,
            "mod_09_semi_bluff": cls._gen_mod_09,
            "mod_09_semibluff_ev": cls._gen_mod_09,
            "mod_10_action_comparison": cls._gen_mod_10,
            "mod_11_implied_odds": cls._gen_mod_11,
            "mod_12_rake": cls._gen_mod_12,
            "mod_12_rake_profitability": cls._gen_mod_12,
            "mod_13_icm": cls._gen_mod_13,
            "mod_13_tournament_icm": cls._gen_mod_13,
            "mod_14_pko": cls._gen_mod_14,
            "mod_14_pko_bounties": cls._gen_mod_14,
            "mod_15_mental_math": cls._gen_mod_15,
            "mod_16_integrated_reasoning": cls._gen_mod_16,
        }

        gen_func = generator_map.get(module_id, cls._gen_mod_02)
        return gen_func(rng, effective_seed, difficulty, game_format)

    # -------------------------------------------------------------
    # Module 01: Arithmetic Foundations
    # -------------------------------------------------------------
    @classmethod
    def _gen_mod_01(
        cls, rng: random.Random, seed: int, diff: MathDifficulty, fmt: MathGameFormat
    ) -> MathExercise:
        subtypes = ["odds_to_pct", "pct_to_odds", "bb_conversion", "ratio_conversion"]
        chosen = rng.choice(subtypes)

        if chosen == "odds_to_pct":
            if diff in (MathDifficulty.BEGINNER, MathDifficulty.INTERMEDIATE):
                x = rng.choice([1.0, 2.0, 3.0, 4.0, 5.0, 9.0])
            else:
                x = round(rng.uniform(1.2, 7.8), 1)
            exact = round((1.0 / (x + 1.0)) * 100.0, 2)
            approx = round(100.0 / (x + 1.0), 1)
            prompt = f"Convert an odds ratio of {x}:1 against into a percentage probability."
            solution = [
                "Formula: P = 1 / (X + 1) * 100%",
                f"X = {x} -> Total trials = {x} + 1 = {round(x + 1, 2)}",
                f"P = 1 / {round(x + 1, 2)} * 100% = {exact}%",
            ]
            common_errors = {
                str(round(100.0 / x, 2)): MistakeClassification.POT_ODDS_VS_ODDS_AGAINST,
                str(round(x * 10.0, 2)): MistakeClassification.ARITHMETIC_ERROR,
            }
            return MathExercise(
                id=f"ex_01_{seed}",
                module_id="mod_01_arithmetic",
                category="Odds Conversion",
                difficulty=diff,
                game_format=fmt,
                question_type=MathQuestionType.NUMERIC,
                prompt=prompt,
                context_data={"odds_ratio": f"{x}:1"},
                exact_answer=exact,
                approximate_answer=approx,
                acceptable_tolerance=0.5,
                unit="%",
                step_by_step_solution=solution,
                common_errors=common_errors,
                reference_formula="P = 1 / (X + 1) * 100%",
                seed=seed,
            )

        elif chosen == "bb_conversion":
            bb_size = rng.choice([2, 5, 10, 20, 50, 100, 500])
            chips = rng.choice([40, 75, 150, 320, 750, 1250, 3500, 8400]) * (bb_size // 2 or 1)
            exact = round(chips / bb_size, 1)
            prompt = f"In a game with Big Blind = {bb_size}, how many Big Blinds (BB) is a chip stack of {chips:,}?"
            solution = [
                "Formula: Stack in BB = Chips / Big Blind Size",
                f"{chips:,} / {bb_size} = {exact} BB",
            ]
            return MathExercise(
                id=f"ex_01_{seed}",
                module_id="mod_01_arithmetic",
                category="Big Blind Metrics",
                difficulty=diff,
                game_format=fmt,
                question_type=MathQuestionType.NUMERIC,
                prompt=prompt,
                context_data={"chips": chips, "bb_size": bb_size},
                exact_answer=exact,
                approximate_answer=round(exact),
                acceptable_tolerance=0.2,
                unit="BB",
                step_by_step_solution=solution,
                reference_formula="BB = Chips / BB_Size",
                seed=seed,
            )

        else:
            pct = rng.choice([10.0, 20.0, 25.0, 33.3, 40.0, 50.0])
            exact = round((100.0 - pct) / pct, 2)
            prompt = f"Convert a {pct}% probability into odds against in the format X:1 (enter X)."
            solution = [
                "Formula: X = (100 - P) / P",
                f"(100 - {pct}) / {pct} = {round(100 - pct, 1)} / {pct} = {exact}:1",
            ]
            return MathExercise(
                id=f"ex_01_{seed}",
                module_id="mod_01_arithmetic",
                category="Odds Conversion",
                difficulty=diff,
                game_format=fmt,
                question_type=MathQuestionType.NUMERIC,
                prompt=prompt,
                context_data={"probability": pct},
                exact_answer=exact,
                approximate_answer=round(exact, 1),
                acceptable_tolerance=0.1,
                unit="ratio",
                step_by_step_solution=solution,
                reference_formula="X:1 = (100 - P) / P",
                seed=seed,
            )

    # -------------------------------------------------------------
    # Module 02: Pot Odds & Break-Even Equity
    # -------------------------------------------------------------
    @classmethod
    def _gen_mod_02(
        cls, rng: random.Random, seed: int, diff: MathDifficulty, fmt: MathGameFormat
    ) -> MathExercise:
        starting_pot = rng.choice([60, 100, 150, 200, 300, 450, 800, 1200])
        fractions = (
            [0.25, 0.33, 0.5, 0.66, 0.75, 1.0]
            if diff == MathDifficulty.BEGINNER
            else [0.2, 0.35, 0.45, 0.6, 0.85, 1.25]
        )
        frac = rng.choice(fractions)
        bet = round(starting_pot * frac)

        multiway = diff in (MathDifficulty.ADVANCED, MathDifficulty.EXPERT) and rng.random() > 0.5
        caller_count = 1 if multiway else 0
        call_cost = bet

        pot_before_hero = starting_pot + bet + (bet * caller_count)
        final_pot = pot_before_hero + call_cost
        exact_req = round((call_cost / final_pot) * 100.0, 2)
        approx_req = round(exact_req, 1)

        # Alternate phrasing styles to test both standard poker conventions
        style = "before_bet" if (seed % 2 == 0 or multiway) else "facing_pot"
        if style == "before_bet":
            prompt = (
                f"The pot is {starting_pot} before any action. On the river, an opponent bets {bet} into this pot. "
                + (f"Another player calls {bet}. " if multiway else "")
                + f"The pot facing your call is {pot_before_hero}, and it costs {call_cost} to call "
                + f"(total final pot will be {final_pot}). "
                + "What is your required calling equity to break even (as a percentage, assuming no rake or future betting)?"
            )
        else:
            prompt = (
                f"The current pot facing you is {pot_before_hero} (which already includes the opponent's {bet} bet). "
                + f"You must call {call_cost} to see a showdown (final total pot will be {final_pot}). "
                + "What is your required calling equity to break even (as a percentage, assuming no rake or future betting)?"
            )

        solution = [
            f"Pot before opponent's bet: {starting_pot}",
            f"Opponent's bet: {bet}" + (f", plus intermediate call: {bet}" if multiway else ""),
            f"Pot facing your call (pot before call): {pot_before_hero}",
            f"Call amount required: {call_cost}",
            f"Total final pot after call: {pot_before_hero} + {call_cost} = {final_pot}",
            f"Required Equity = Call / Final Pot = {call_cost} / {final_pot} * 100% = {exact_req}%",
        ]

        common_errors = {
            # Mistake 1: dividing by pot before call without adding own call (pot ratio instead of probability)
            str(
                round((call_cost / pot_before_hero) * 100.0, 2)
            ): MistakeClassification.INCORRECT_POT_CONSTRUCTION,
            # Mistake 2: dividing by starting pot (ignoring opponent's bet)
            str(
                round((call_cost / starting_pot) * 100.0, 2)
            ): MistakeClassification.FORMULA_SELECTION_ERROR,
        }

        return MathExercise(
            id=f"ex_02_{seed}",
            module_id="mod_02_pot_odds",
            category="Pot Odds",
            difficulty=diff,
            game_format=fmt,
            question_type=MathQuestionType.NUMERIC,
            prompt=prompt,
            context_data={
                "pot_before_bet": starting_pot,
                "opponent_bet": bet,
                "multiway_callers": caller_count,
                "pot_facing_call": pot_before_hero,
                "call_amount": call_cost,
                "total_final_pot": final_pot,
                "phrasing_style": style,
            },
            exact_answer=exact_req,
            approximate_answer=approx_req,
            acceptable_tolerance=0.5,
            unit="%",
            step_by_step_solution=solution,
            common_errors=common_errors,
            reference_formula="Required Equity = Call / Final Pot * 100%",
            seed=seed,
        )

    # -------------------------------------------------------------
    # Module 03: Outs, Draws & Card Improvement
    # -------------------------------------------------------------
    @classmethod
    def _gen_mod_03(
        cls, rng: random.Random, seed: int, diff: MathDifficulty, fmt: MathGameFormat
    ) -> MathExercise:
        draw_types = [
            ("flush_draw", 9, "4 to a flush (9 clean suit outs)"),
            ("oesd", 8, "open-ended straight draw (8 outs)"),
            ("gutshot", 4, "inside straight draw / gutshot (4 outs)"),
            ("combo_draw", 15, "open-ended straight draw + flush draw (15 outs)"),
            ("two_overcards", 6, "two overcards to the board (6 outs)"),
        ]
        dtype, outs, desc = rng.choice(draw_types)
        street = rng.choice(["flop", "turn"])

        # Determine exact and rule of 2/4 approximation
        exact_prob = round(outs_to_equity(outs, street, use_exact=True), 2)
        approx_prob = round(outs_to_equity(outs, street, use_exact=False), 1)

        prompt = (
            f"On the {street.upper()}, you hold a {desc}. "
            f"Using the Rule of 2 and 4 (or exact calculation), what is your percentage probability "
            f"of hitting your draw by the river?"
        )

        solution = [
            f"Identified draw: {desc} with {outs} clean outs.",
            f"Street: {street.upper()}.",
            (
                f"Rule of 4 on flop: {outs} * 4"
                + (f" - ({outs} - 8) = {approx_prob}%" if outs > 8 else f" = {approx_prob}%")
                if street == "flop"
                else f"Rule of 2 on turn: {outs} * 2 = {approx_prob}%"
            ),
            f"Exact combinatorial probability: {exact_prob}%",
        ]

        return MathExercise(
            id=f"ex_03_{seed}",
            module_id="mod_03_outs_draws",
            category="Outs & Card Improvement",
            difficulty=diff,
            game_format=fmt,
            question_type=MathQuestionType.NUMERIC,
            prompt=prompt,
            context_data={"draw_type": dtype, "outs": outs, "street": street},
            exact_answer=exact_prob,
            approximate_answer=approx_prob,
            acceptable_tolerance=1.0,
            unit="%",
            step_by_step_solution=solution,
            common_errors={
                str(outs * 4): MistakeClassification.APPROXIMATION_ERROR,
                str(
                    outs * 2 if street == "flop" else outs * 4
                ): MistakeClassification.FORMULA_SELECTION_ERROR,
            },
            reference_formula="Flop: (Outs * 4) [- (Outs - 8) if > 8] | Turn: Outs * 2",
            seed=seed,
        )

    # -------------------------------------------------------------
    # Module 04: Equity Fundamentals
    # -------------------------------------------------------------
    @classmethod
    def _gen_mod_04(
        cls, rng: random.Random, seed: int, diff: MathDifficulty, fmt: MathGameFormat
    ) -> MathExercise:
        matchups = [
            ("AA vs KK", 82.0, "Pocket Aces vs Pocket Kings preflop"),
            ("AKs vs QQ", 46.0, "AK suited vs Pocket Queens (classic coin flip, Hero is AK)"),
            ("AKo vs AQo", 73.0, "Dominating Ace: AK offsuit vs AQ offsuit preflop"),
            ("JJ vs TT", 81.0, "Higher pair vs lower pair: Pocket Jacks vs Pocket Tens"),
            ("A5s vs KK", 31.0, "Suited Ace vs high overpair"),
        ]
        name, eq, desc = rng.choice(matchups)
        prompt = (
            f"In a heads-up all-in preflop confrontation: {desc}.\n"
            f"What is Hero's approximate showdown equity percentage (within standard +/- 3% tolerance)?"
        )
        solution = [
            f"Matchup archetype: {name}",
            f"Standard theoretical showdown equity: ~{eq}%",
            "Ties and suit conflicts create slight variations between 81%-82% or 45%-47%.",
        ]
        return MathExercise(
            id=f"ex_04_{seed}",
            module_id="mod_04_equity_fundamentals",
            category="Equity Fundamentals",
            difficulty=diff,
            game_format=fmt,
            question_type=MathQuestionType.EQUITY_ESTIMATE,
            prompt=prompt,
            context_data={"matchup": name},
            exact_answer=eq,
            approximate_answer=round(eq),
            acceptable_tolerance=3.0,
            unit="%",
            step_by_step_solution=solution,
            reference_formula="Equity = Wins% + (Ties% / 2)",
            seed=seed,
        )

    # -------------------------------------------------------------
    # Module 05: Equity Against Opponent Ranges
    # -------------------------------------------------------------
    @classmethod
    def _gen_mod_05(
        cls, rng: random.Random, seed: int, diff: MathDifficulty, fmt: MathGameFormat
    ) -> MathExercise:
        combos_ahead = rng.choice([3, 6, 9])
        combos_behind = rng.choice([12, 16, 24])
        hero_eq_vs_ahead = 10.0
        hero_eq_vs_behind = 85.0

        total_combos = combos_ahead + combos_behind
        weighted_eq = (
            (combos_ahead * hero_eq_vs_ahead) + (combos_behind * hero_eq_vs_behind)
        ) / total_combos
        exact = round(weighted_eq, 2)
        approx = round(exact, 1)

        prompt = (
            f"Hero holds top pair with top kicker. Villain's range consists of:\n"
            f"• {combos_ahead} combinations of sets/two-pair (Hero has {hero_eq_vs_ahead}% equity)\n"
            f"• {combos_behind} combinations of weaker pairs/draws (Hero has {hero_eq_vs_behind}% equity)\n"
            f"Calculate Hero's weighted average equity against Villain's range."
        )

        solution = [
            f"Total combos in range: {combos_ahead} + {combos_behind} = {total_combos}",
            f"Weighted equity: ({combos_ahead} * {hero_eq_vs_ahead}%) + ({combos_behind} * {hero_eq_vs_behind}%) = {combos_ahead * hero_eq_vs_ahead + combos_behind * hero_eq_vs_behind:.1f}",
            f"Average Range Equity: {combos_ahead * hero_eq_vs_ahead + combos_behind * hero_eq_vs_behind:.1f} / {total_combos} = {exact}%",
        ]

        return MathExercise(
            id=f"ex_05_{seed}",
            module_id="mod_05_equity_ranges",
            category="Range Equity",
            difficulty=diff,
            game_format=fmt,
            question_type=MathQuestionType.NUMERIC,
            prompt=prompt,
            context_data={"combos_ahead": combos_ahead, "combos_behind": combos_behind},
            exact_answer=exact,
            approximate_answer=approx,
            acceptable_tolerance=1.0,
            unit="%",
            step_by_step_solution=solution,
            reference_formula="Range Equity = Sum(Combos * Eq) / Total Combos",
            seed=seed,
        )

    # -------------------------------------------------------------
    # Module 06: Equity Realization
    # -------------------------------------------------------------
    @classmethod
    def _gen_mod_06(
        cls, rng: random.Random, seed: int, diff: MathDifficulty, fmt: MathGameFormat
    ) -> MathExercise:
        raw_eq = rng.choice([30.0, 35.0, 40.0, 45.0])
        eqr = rng.choice([0.70, 0.80, 1.15, 1.25])
        position = "Out of Position (OOP)" if eqr < 1.0 else "In Position (IP)"

        realized_eq = round(raw_eq * eqr, 2)

        prompt = (
            f"Hero holds a drawing hand with {raw_eq}% raw showdown equity on the flop, playing {position}. "
            f"Due to positional dynamics and playability, Hero's Equity Realization Factor (EQR) is estimated at {eqr * 100:.0f}%. "
            f"What is Hero's realized equity percentage?"
        )

        solution = [
            "Formula: Realized Equity = Raw Equity * EQR",
            f"Realized Equity = {raw_eq}% * {eqr} = {realized_eq}%",
            f"Note: {'Because Hero is OOP, weak hands fold to turn bets and realize less than raw equity.' if eqr < 1.0 else 'Because Hero is in position, pot control and free cards boost realization.'}",
        ]

        return MathExercise(
            id=f"ex_06_{seed}",
            module_id="mod_06_equity_realization",
            category="Equity Realization",
            difficulty=diff,
            game_format=fmt,
            question_type=MathQuestionType.NUMERIC,
            prompt=prompt,
            context_data={"raw_equity": raw_eq, "eqr": eqr, "position": position},
            exact_answer=realized_eq,
            approximate_answer=round(realized_eq, 1),
            acceptable_tolerance=0.5,
            unit="%",
            step_by_step_solution=solution,
            reference_formula="Realized Equity = Raw Equity * EQR",
            seed=seed,
        )

    # -------------------------------------------------------------
    # Module 07: Call EV
    # -------------------------------------------------------------
    @classmethod
    def _gen_mod_07(
        cls, rng: random.Random, seed: int, diff: MathDifficulty, fmt: MathGameFormat
    ) -> MathExercise:
        pot = rng.choice([120, 200, 350, 500, 800])
        bet = rng.choice([60, 100, 175, 250, 400])
        equity = rng.choice([20.0, 28.0, 35.0, 42.0, 50.0])

        final_pot = pot + bet + bet
        exact_ev = round(call_expected_value(equity, bet, pot + bet), 1)

        prompt = (
            f"Pot is {pot}. Villain shoves all-in on the river for {bet}. "
            f"Hero estimates having {equity}% equity if calling. "
            f"Calculate Hero's expected value (EV) of calling in chips (positive or negative)."
        )

        solution = [
            f"Pot before your call = {pot} + {bet} = {pot + bet}",
            f"Final pot after call = {pot + bet} + {bet} = {final_pot}",
            "EV(Call) = (Equity * Final Pot) - Call Amount",
            f"EV(Call) = ({equity / 100:.2f} * {final_pot}) - {bet} = {round((equity / 100) * final_pot, 1)} - {bet} = {exact_ev} chips",
            f"{'Calling is profitable (+EV)!' if exact_ev > 0 else 'Calling loses chips (-EV); fold is preferred.'}",
        ]

        return MathExercise(
            id=f"ex_07_{seed}",
            module_id="mod_07_call_ev",
            category="Call EV",
            difficulty=diff,
            game_format=fmt,
            question_type=MathQuestionType.NUMERIC,
            prompt=prompt,
            context_data={"pot": pot, "bet": bet, "equity": equity},
            exact_answer=exact_ev,
            approximate_answer=round(exact_ev),
            acceptable_tolerance=1.0,
            unit="chips",
            step_by_step_solution=solution,
            reference_formula="EV = (Equity * Final Pot) - Call",
            seed=seed,
        )

    # -------------------------------------------------------------
    # Module 08: Bluff EV & Fold Equity
    # -------------------------------------------------------------
    @classmethod
    def _gen_mod_08(
        cls, rng: random.Random, seed: int, diff: MathDifficulty, fmt: MathGameFormat
    ) -> MathExercise:
        pot = rng.choice([100, 150, 200, 300, 500])
        bet_frac = rng.choice([0.33, 0.5, 0.67, 0.75, 1.0])
        bet = round(pot * bet_frac)

        alpha = round(bluff_break_even_percentage(bet, pot), 2)
        mdf = round(minimum_defense_frequency(bet, pot), 2)

        prompt = (
            f"The pot is {pot}. You bet {bet} on the river as a pure zero-equity bluff. "
            f"What is the break-even fold percentage (Alpha) required for this bluff to be profitable?"
        )

        solution = [
            "Formula: Alpha = Bet / (Pot + Bet) * 100%",
            f"Alpha = {bet} / ({pot} + {bet}) = {bet} / {pot + bet} * 100% = {alpha}%",
            f"Note: Opponent must fold at least {alpha}% of the time for Hero to auto-profit.",
            f"Corresponding Minimum Defense Frequency (MDF) = 100% - {alpha}% = {mdf}%.",
        ]

        return MathExercise(
            id=f"ex_08_{seed}",
            module_id="mod_08_bluff_ev",
            category="Bluff EV & Alpha",
            difficulty=diff,
            game_format=fmt,
            question_type=MathQuestionType.NUMERIC,
            prompt=prompt,
            context_data={"pot": pot, "bet": bet},
            exact_answer=alpha,
            approximate_answer=round(alpha, 1),
            acceptable_tolerance=0.5,
            unit="%",
            step_by_step_solution=solution,
            reference_formula="Alpha = Bet / (Pot + Bet) * 100%",
            seed=seed,
        )

    # -------------------------------------------------------------
    # Module 09: Semi-Bluff EV
    # -------------------------------------------------------------
    @classmethod
    def _gen_mod_09(
        cls, rng: random.Random, seed: int, diff: MathDifficulty, fmt: MathGameFormat
    ) -> MathExercise:
        pot = rng.choice([100, 200, 400])
        bet = round(pot * rng.choice([0.5, 0.75, 1.0]))
        fold_pct = rng.choice([25.0, 35.0, 45.0])
        equity_when_called = rng.choice([30.0, 35.0, 40.0])

        exact_ev = round(fold_equity_ev(pot, bet, fold_pct, equity_when_called), 1)

        prompt = (
            f"On the turn, pot is {pot}. Hero semi-bluffs {bet} with a draw that has {equity_when_called}% equity when called. "
            f"Villain folds {fold_pct}% of the time and calls {100 - fold_pct}% (assume Villain never raises). "
            f"What is Hero's total EV in chips?"
        )

        solution = [
            "Formula: EV = P(fold)*Pot + P(call)*[(Equity * FinalPot) - Bet]",
            f"When Villain folds ({fold_pct}%): Wins {pot} chips -> {fold_pct / 100:.2f} * {pot} = {round((fold_pct / 100) * pot, 1)}",
            f"When Villain calls ({100 - fold_pct}%): Final pot is {pot + 2 * bet}. Return = ({equity_when_called / 100:.2f} * {pot + 2 * bet}) - {bet} = {round((equity_when_called / 100) * (pot + 2 * bet) - bet, 1)}",
            f"Total EV = {exact_ev} chips.",
        ]

        return MathExercise(
            id=f"ex_09_{seed}",
            module_id="mod_09_semi_bluff",
            category="Semi-Bluff EV",
            difficulty=diff,
            game_format=fmt,
            question_type=MathQuestionType.NUMERIC,
            prompt=prompt,
            context_data={
                "pot": pot,
                "bet": bet,
                "fold_pct": fold_pct,
                "equity_when_called": equity_when_called,
            },
            exact_answer=exact_ev,
            approximate_answer=round(exact_ev),
            acceptable_tolerance=1.5,
            unit="chips",
            step_by_step_solution=solution,
            reference_formula="EV = f*Pot + (1-f)*[(Eq*(Pot+2*Bet)) - Bet]",
            seed=seed,
        )

    # -------------------------------------------------------------
    # Module 10: Bet, Raise & Action EV Comparison
    # -------------------------------------------------------------
    @classmethod
    def _gen_mod_10(
        cls, rng: random.Random, seed: int, diff: MathDifficulty, fmt: MathGameFormat
    ) -> MathExercise:
        check_ev = rng.choice([10, 25, 40])
        bet_size = 50
        pot = 100
        fold_freq = 0.50
        call_equity = 0.80

        # EV(Bet) = 0.50 * 100 + 0.50 * (0.80 * 200 - 50) = 50 + 0.50 * (160 - 50) = 50 + 55 = 105
        bet_ev = round(
            (fold_freq * pot)
            + ((1.0 - fold_freq) * ((call_equity * (pot + 2 * bet_size)) - bet_size))
        )

        options = [
            f"Bet (EV = +{bet_ev}) > Check (EV = +{check_ev}) > Fold (EV = 0)",
            f"Check (EV = +{check_ev}) > Bet (EV = +{bet_ev}) > Fold (EV = 0)",
            f"Fold (EV = 0) > Check (EV = +{check_ev}) > Bet (EV = +{bet_ev})",
            "All actions have identical EV",
        ]
        exact_ans = options[0]

        prompt = (
            f"River situation: Pot is {pot}. "
            f"Checking has an EV of +{check_ev} chips. "
            f"Betting {bet_size} causes Villain to fold 50% of the time, and when called (50%), Hero has 80% showdown equity. "
            f"Which action sequence ranks candidate choices from highest EV to lowest?"
        )

        solution = [
            "EV(Fold) = 0 chips (baseline).",
            f"EV(Check) = +{check_ev} chips.",
            f"EV(Bet {bet_size}):",
            f"• Fold branch (50%): 0.50 * {pot} = +{round(fold_freq * pot)} chips.",
            f"• Call branch (50%): Final pot = {pot + 2 * bet_size}. Net = ({call_equity} * {pot + 2 * bet_size}) - {bet_size} = +110. Weighted = 0.50 * 110 = +55 chips.",
            f"• Total EV(Bet) = {bet_ev} chips.",
            f"Ranking: Bet (+{bet_ev}) > Check (+{check_ev}) > Fold (0).",
        ]

        return MathExercise(
            id=f"ex_10_{seed}",
            module_id="mod_10_action_comparison",
            category="Action Comparison",
            difficulty=diff,
            game_format=fmt,
            question_type=MathQuestionType.MULTIPLE_CHOICE,
            prompt=prompt,
            context_data={"check_ev": check_ev, "bet_ev": bet_ev},
            exact_answer=exact_ans,
            options=options,
            step_by_step_solution=solution,
            reference_formula="Rank actions by Expected Value in chips",
            seed=seed,
        )

    # -------------------------------------------------------------
    # Module 11: Implied Odds
    # -------------------------------------------------------------
    @classmethod
    def _gen_mod_11(
        cls, rng: random.Random, seed: int, diff: MathDifficulty, fmt: MathGameFormat
    ) -> MathExercise:
        pot = rng.choice([100, 150, 200])
        bet = rng.choice([50, 75, 100])
        outs = 4  # Gutshot: 4/46 = 8.7%
        prob = 4.0 / 46.0

        final_pot_now = pot + bet + bet
        # total_pot_needed = bet / prob
        total_pot_needed = bet / prob
        future_needed = round(total_pot_needed - final_pot_now)

        prompt = (
            f"Turn: Pot is {pot}. Villain bets {bet}. Hero holds a gutshot straight draw (4 outs out of 46 cards $\\approx$ 8.7%). "
            f"How many additional chips must Hero win on the river when hitting the straight to make calling break-even?"
        )

        solution = [
            f"Turn call cost = {bet}. Immediate final pot = {pot} + {bet} + {bet} = {final_pot_now}.",
            "Hit probability = 4 / 46 = 8.70% (or odds of 10.5 to 1).",
            f"Total pot required to break even = Call / Prob = {bet} / (4/46) = {bet} * 11.5 = {round(total_pot_needed)} chips.",
            f"Future chips needed from opponent on river = {round(total_pot_needed)} - {final_pot_now} = {future_needed} chips.",
        ]

        return MathExercise(
            id=f"ex_11_{seed}",
            module_id="mod_11_implied_odds",
            category="Implied Odds",
            difficulty=diff,
            game_format=fmt,
            question_type=MathQuestionType.NUMERIC,
            prompt=prompt,
            context_data={"pot": pot, "bet": bet, "outs": outs},
            exact_answer=future_needed,
            approximate_answer=round(future_needed, -1),
            acceptable_tolerance=10.0,
            unit="chips",
            step_by_step_solution=solution,
            reference_formula="Future Chips = (Call / Prob) - Final Pot",
            seed=seed,
        )

    # -------------------------------------------------------------
    # Module 12: Cash Rake
    # -------------------------------------------------------------
    @classmethod
    def _gen_mod_12(
        cls, rng: random.Random, seed: int, diff: MathDifficulty, fmt: MathGameFormat
    ) -> MathExercise:
        pot = rng.choice([100, 200, 400])
        bet = round(pot * 0.5)
        rake_pct = 5.0
        final_pot = pot + 2 * bet
        rake_taken = round(final_pot * (rake_pct / 100.0), 2)
        net_pot = final_pot - rake_taken

        unraked_req = round((bet / final_pot) * 100.0, 2)
        raked_req = round((bet / net_pot) * 100.0, 2)

        prompt = (
            f"In a cash game with {rake_pct}% rake (uncapped), pot is {pot} and Villain bets {bet}. "
            f"What is Hero's rake-adjusted required equity percentage to call?"
        )

        solution = [
            f"Final pot before rake: {pot} + {bet} + {bet} = {final_pot}.",
            f"Rake deducted: {rake_pct}% of {final_pot} = {rake_taken} chips.",
            f"Net pot received if Hero wins: {final_pot} - {rake_taken} = {net_pot} chips.",
            f"Rake-adjusted Required Equity = {bet} / {net_pot} * 100% = {raked_req}%",
            f"Comparison: Unraked requirement was {unraked_req}%. Rake adds +{round(raked_req - unraked_req, 2)}% hurdle!",
        ]

        return MathExercise(
            id=f"ex_12_{seed}",
            module_id="mod_12_rake",
            category="Cash Rake Impact",
            difficulty=diff,
            game_format=fmt,
            question_type=MathQuestionType.NUMERIC,
            prompt=prompt,
            context_data={"pot": pot, "bet": bet, "rake_pct": rake_pct},
            exact_answer=raked_req,
            approximate_answer=round(raked_req, 1),
            acceptable_tolerance=0.5,
            unit="%",
            step_by_step_solution=solution,
            common_errors={
                str(unraked_req): MistakeClassification.RAKE_OMISSION,
            },
            reference_formula="Raked Req Eq = Call / (Final Pot * (1 - Rake)) * 100%",
            seed=seed,
        )

    # -------------------------------------------------------------
    # Module 13: Tournament cEV vs ICM
    # -------------------------------------------------------------
    @classmethod
    def _gen_mod_13(
        cls, rng: random.Random, seed: int, diff: MathDifficulty, fmt: MathGameFormat
    ) -> MathExercise:
        chip_odds_pct = 40.0
        bubble_factor = rng.choice([1.4, 1.8, 2.2])
        # RP for a 1:1 risk vs reward = (BF - 1) / (BF + 1)
        # Required equity under ICM = BF / (BF + (Pot/Bet))
        # With chip_odds_pct = 40%, Pot = 1.5 * Bet.
        icm_req = round((bubble_factor / (bubble_factor + 1.5)) * 100.0, 1)
        risk_premium = round(icm_req - chip_odds_pct, 1)

        prompt = (
            f"On a tournament bubble, Hero faces an all-in where Chip EV pot odds require {chip_odds_pct}% equity. "
            f"Hero's Bubble Factor against Villain is {bubble_factor}. "
            f"What is Hero's ICM-adjusted required equity percentage?"
        )

        solution = [
            f"Chip EV requirement: {chip_odds_pct}%",
            f"Bubble Factor: {bubble_factor} (chips lost are worth {bubble_factor}x chips won)",
            "ICM Required Equity = BF / (BF + (Pot / Bet))",
            f"ICM Required Equity = {bubble_factor} / ({bubble_factor} + 1.5) = {icm_req}%",
            f"Risk Premium = {risk_premium}% extra equity needed over chip odds!",
        ]

        return MathExercise(
            id=f"ex_13_{seed}",
            module_id="mod_13_icm",
            category="Tournament ICM",
            difficulty=diff,
            game_format=MathGameFormat.TOURNAMENT_MTT,
            question_type=MathQuestionType.NUMERIC,
            prompt=prompt,
            context_data={"bubble_factor": bubble_factor, "chip_odds": chip_odds_pct},
            exact_answer=icm_req,
            approximate_answer=round(icm_req),
            acceptable_tolerance=1.0,
            unit="%",
            step_by_step_solution=solution,
            common_errors={
                str(chip_odds_pct): MistakeClassification.ICM_CHIP_EV_CONFUSION,
            },
            reference_formula="ICM Req Eq = BF / (BF + Pot/Bet) * 100%",
            seed=seed,
        )

    # -------------------------------------------------------------
    # Module 14: PKO & Bounty EV
    # -------------------------------------------------------------
    @classmethod
    def _gen_mod_14(
        cls, rng: random.Random, seed: int, diff: MathDifficulty, fmt: MathGameFormat
    ) -> MathExercise:
        pot = 12000
        villain_shove = 8000
        starting_stack = 10000
        bounties_held = rng.choice([2, 3, 5])
        # 1 starting bounty = ~1/3 starting stack = 3,333 chips
        bounty_chips = round(bounties_held * (starting_stack / 3.0))

        adj_pot_before_call = pot + villain_shove + bounty_chips
        final_adj_pot = adj_pot_before_call + villain_shove
        exact_req = round((villain_shove / final_adj_pot) * 100.0, 1)

        prompt = (
            f"In a PKO tournament, starting stack was {starting_stack:,} chips (1 starting bounty $\\approx$ 3,333 chips). "
            f"Pot is {pot:,}. Short stack Villain shoves for {villain_shove:,} with {bounties_held} starting bounties on their head. "
            f"Hero COVERS Villain. What is Hero's bounty-adjusted required equity percentage to call?"
        )

        solution = [
            f"Bounty conversion: {bounties_held} bounties * 3,333 chips = {bounty_chips:,} equivalent chips.",
            f"Adjusted pot before call = {pot:,} (pot) + {villain_shove:,} (shove) + {bounty_chips:,} (bounty) = {adj_pot_before_call:,} chips.",
            f"Final adjusted pot after Hero calls = {final_adj_pot:,} chips.",
            f"Required Equity = {villain_shove:,} / {final_adj_pot:,} * 100% = {exact_req}%",
        ]

        return MathExercise(
            id=f"ex_14_{seed}",
            module_id="mod_14_pko",
            category="PKO Bounty Math",
            difficulty=diff,
            game_format=MathGameFormat.TOURNAMENT_PKO,
            question_type=MathQuestionType.NUMERIC,
            prompt=prompt,
            context_data={"bounties_held": bounties_held, "bounty_chips": bounty_chips},
            exact_answer=exact_req,
            approximate_answer=round(exact_req),
            acceptable_tolerance=1.0,
            unit="%",
            step_by_step_solution=solution,
            reference_formula="Adjusted Pot = Pot + Bounty_Chips",
            seed=seed,
        )

    # -------------------------------------------------------------
    # Module 15: Mental Math Techniques
    # -------------------------------------------------------------
    @classmethod
    def _gen_mod_15(
        cls, rng: random.Random, seed: int, diff: MathDifficulty, fmt: MathGameFormat
    ) -> MathExercise:
        bet_options = [
            ("1/4 pot bet", 16.7),
            ("1/3 pot bet", 20.0),
            ("1/2 pot bet", 25.0),
            ("2/3 pot bet", 28.6),
            ("3/4 pot bet", 30.0),
            ("pot-sized bet", 33.3),
            ("1.5x pot overbet", 37.5),
        ]
        label, eq = rng.choice(bet_options)
        prompt = (
            f"Mental Reflex Drill: Facing a {label}, "
            f"what is the exact break-even pot odds required equity percentage?"
        )
        solution = [
            f"Reflex Anchor: {label} -> {eq}% required equity.",
            "Shortcut: Call / (1 + Bet + Call) in fraction of pot.",
        ]
        return MathExercise(
            id=f"ex_15_{seed}",
            module_id="mod_15_mental_math",
            category="Mental Shortcuts",
            difficulty=diff,
            game_format=fmt,
            question_type=MathQuestionType.NUMERIC,
            prompt=prompt,
            context_data={"sizing": label},
            exact_answer=eq,
            approximate_answer=round(eq),
            acceptable_tolerance=0.5,
            unit="%",
            step_by_step_solution=solution,
            reference_formula="Memorized anchor point",
            seed=seed,
        )

    # -------------------------------------------------------------
    # Module 16: Integrated Real-Hand Reasoning (Unprompted)
    # -------------------------------------------------------------
    @classmethod
    def _gen_mod_16(
        cls, rng: random.Random, seed: int, diff: MathDifficulty, fmt: MathGameFormat
    ) -> MathExercise:
        is_insufficient = rng.random() < 0.35

        if is_insufficient:
            prompt = (
                "Hero is on the tournament bubble facing an all-in shove from the table chip leader. "
                "Hero holds pocket Queens. We are given the pot is 50,000 chips, but the payout structure "
                "and stack distribution of the remaining players are NOT provided.\n\n"
                "Can you calculate Hero's mathematically exact tournament EV to determine whether to call?"
            )
            options = [
                "Insufficient Information to Determine (ICM requires complete stack distribution and payout ladder)",
                "Yes, call immediately because Queens has > 70% equity",
                "Yes, fold immediately because tournament chips are always worth less",
                "Yes, calculate chip EV and ignore payouts",
            ]
            exact_ans = options[0]
            solution = [
                "Under the Independent Chip Model (ICM), tournament prize equity is a non-linear function of ALL active stack sizes and the payout ladder.",
                "Without the payout ladder and stack counts, the Bubble Factor cannot be calculated.",
                "The mathematically correct answer is: Insufficient Information to Determine.",
            ]
            return MathExercise(
                id=f"ex_16_{seed}",
                module_id="mod_16_integrated_reasoning",
                category="Integrated Reasoning",
                difficulty=diff,
                game_format=MathGameFormat.TOURNAMENT_MTT,
                question_type=MathQuestionType.INSUFFICIENT_INFO,
                prompt=prompt,
                context_data={"is_insufficient": True},
                exact_answer=exact_ans,
                options=options,
                step_by_step_solution=solution,
                reference_formula="ICM requires complete game state inputs",
                seed=seed,
            )

        else:
            pot = 240
            bet = 120
            # Hero has a flush draw on river (missed, 0 equity). Can Hero call? No!
            # What if Hero wants to bluff?
            alpha = round((bet / (pot + bet)) * 100.0, 1)
            prompt = (
                f"Hero reaches the river with a busted draw (0% showdown equity). "
                f"Pot is {pot}. Hero is deciding whether to execute a pure bluff by betting {bet}.\n"
                f"What concept must Hero calculate, and what is its numerical threshold?"
            )
            options = [
                f"Bluff Alpha (Fold Equity Threshold) = {alpha}% folds required",
                "Pot Odds = 25.0% equity required",
                "MDF = 66.7% calling frequency",
                "Equity Realization = 100%",
            ]
            exact_ans = options[0]
            solution = [
                "1. Decision: Hero holds 0% equity and is contemplating a bet -> This is a pure bluff.",
                "2. Relevant formula: Alpha = Bet / (Pot + Bet).",
                f"3. Calculation: {bet} / ({pot} + {bet}) = {bet} / {pot + bet} = {alpha}%.",
                f"4. Conclusion: Hero needs the opponent to fold more than {alpha}% of the time for the bluff to be +EV.",
            ]
            return MathExercise(
                id=f"ex_16_{seed}",
                module_id="mod_16_integrated_reasoning",
                category="Integrated Reasoning",
                difficulty=diff,
                game_format=fmt,
                question_type=MathQuestionType.CONCEPT_IDENTIFY,
                prompt=prompt,
                context_data={"is_insufficient": False, "alpha": alpha},
                exact_answer=exact_ans,
                options=options,
                step_by_step_solution=solution,
                reference_formula="Alpha = Bet / (Pot + Bet) * 100%",
                seed=seed,
            )
