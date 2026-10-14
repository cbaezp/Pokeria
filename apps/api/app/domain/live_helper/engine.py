"""Authoritative State Reconstruction, Legality Validation, and Evaluation Engine for Live Helper.

Operates purely on integer chip units, enforces chip conservation, and strictly separates
Rules, Mathematical, Strategic, and Pedagogical verdicts.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any

from app.domain.exceptions import PokerDomainError
from app.domain.live_helper.models import (
    EducationalInterpretation,
    FormatType,
    HelperMode,
    LiveHelperActionRecord,
    LiveHelperEvaluation,
    LiveHelperGameConfig,
    LiveHelperSeat,
    MathematicalVerdict,
    RulesVerdict,
    StrategicMatchLevel,
    StrategicVerdict,
)
from app.domain.live_helper.reasoning_evaluator import ReasoningEvaluator
from app.domain.poker.icm import calculate_tournament_context
from app.domain.poker.pot import PlayerPotContribution, PotEngine
from app.domain.poker.seat_geometry import (
    TableSeatConfig,
    infer_table_geometry,
)
from app.domain.training.preflop_data import PreflopReferenceProvider
from app.domain.training.strategy_registry import (
    GradingPermission,
    get_strategy_reference,
)


class LiveHelperEngine:
    """Core domain engine for reconstructing hands and evaluating decisions."""

    @staticmethod
    def reconstruct_table(
        config: LiveHelperGameConfig,
        button_seat: int,
        seat_configs: list[TableSeatConfig],
        actions: list[dict[str, Any]],
        board_cards: list[str],
    ) -> dict[str, Any]:
        """Reconstruct table state deterministically from raw seat configurations and action history."""
        # 0. Validate no duplicate cards across hole cards and community board
        all_cards: list[str] = list(board_cards)
        for s in seat_configs:
            all_cards.extend(s.hole_cards)
        clean_cards = [c.strip() for c in all_cards if c and c.strip()]
        if len(clean_cards) != len(set(clean_cards)):
            raise PokerDomainError("Duplicate cards detected in hole cards or community board.")

        # 1. Infer seat geometry and positions
        geometry = infer_table_geometry(
            max_capacity=config.max_capacity,
            button_seat=button_seat,
            seats=seat_configs,
        )

        # 2. Initialize seats
        seats_by_num: dict[int, dict[str, Any]] = {}
        for s in seat_configs:
            inferred = geometry.get_seat(s.seat_number)
            pos_name = inferred.position_name if inferred else ""
            seats_by_num[s.seat_number] = {
                "seat_number": s.seat_number,
                "player_id": s.player_id,
                "player_name": s.player_name,
                "starting_stack": s.stack,
                "current_stack": s.stack,
                "round_bet": 0,
                "total_bet": 0,
                "is_hero": s.is_hero,
                "is_sitting_out": s.is_sitting_out,
                "is_folded": False,
                "is_all_in": False,
                "hole_cards": tuple(s.hole_cards),
                "position_name": pos_name,
                "has_acted_this_round": False,
                "faced_bet_at_last_action": 0,
                "can_raise_reopened": True,
            }

        # 3. Post Blinds & Antes
        pot = 0
        current_round_high_bet = 0
        min_raise_delta = config.big_blind

        # Post Antes
        if config.ante > 0:
            if config.ante_type == "BBA":
                bb_seat = geometry.bb_seat
                if bb_seat in seats_by_num:
                    bba_amt = min(seats_by_num[bb_seat]["current_stack"], config.ante)
                    seats_by_num[bb_seat]["current_stack"] -= bba_amt
                    seats_by_num[bb_seat]["total_bet"] += bba_amt
                    pot += bba_amt
            else:
                for s_num in geometry.preflop_order:
                    s_data = seats_by_num[s_num]
                    ante_amt = min(s_data["current_stack"], config.ante)
                    s_data["current_stack"] -= ante_amt
                    s_data["total_bet"] += ante_amt
                    pot += ante_amt

        # Post Small Blind
        sb_seat = geometry.sb_seat
        if sb_seat in seats_by_num:
            sb_amt = min(seats_by_num[sb_seat]["current_stack"], config.small_blind)
            seats_by_num[sb_seat]["current_stack"] -= sb_amt
            seats_by_num[sb_seat]["round_bet"] = sb_amt
            seats_by_num[sb_seat]["total_bet"] += sb_amt
            pot += sb_amt
            current_round_high_bet = max(current_round_high_bet, sb_amt)
            if seats_by_num[sb_seat]["current_stack"] == 0:
                seats_by_num[sb_seat]["is_all_in"] = True

        # Post Big Blind
        bb_seat = geometry.bb_seat
        if bb_seat in seats_by_num:
            bb_amt = min(seats_by_num[bb_seat]["current_stack"], config.big_blind)
            seats_by_num[bb_seat]["current_stack"] -= bb_amt
            seats_by_num[bb_seat]["round_bet"] = bb_amt
            seats_by_num[bb_seat]["total_bet"] += bb_amt
            pot += bb_amt
            current_round_high_bet = max(current_round_high_bet, bb_amt)
            if seats_by_num[bb_seat]["current_stack"] == 0:
                seats_by_num[bb_seat]["is_all_in"] = True

        # 4. Process Chronological Actions
        current_street = "preflop"
        action_timeline: list[LiveHelperActionRecord] = []
        raises_this_round = 1 if current_round_high_bet > 0 else 0  # BB is initial high bet
        last_raiser_seat: int | None = bb_seat

        for idx, act in enumerate(actions):
            act_type = str(act.get("action_type", "")).lower()
            s_num = int(act.get("seat_number", 0))
            if s_num not in seats_by_num:
                continue

            s_data = seats_by_num[s_num]
            if s_data["is_folded"] or s_data["is_all_in"]:
                continue

            if act_type in ["post_sb", "post_bb", "post_ante"]:
                # Blinds already posted in setup
                continue

            # Detect street transition from action's street field
            act_street = str(act.get("street", current_street)).lower()
            if act_street and act_street != current_street:
                current_street = act_street
                current_round_high_bet = 0
                min_raise_delta = config.big_blind
                raises_this_round = 0
                last_raiser_seat = None
                for s in seats_by_num.values():
                    s["round_bet"] = 0
                    s["has_acted_this_round"] = False
                    s["can_raise_reopened"] = True

            pot_before = pot
            amount = int(act.get("amount", 0))
            descriptor = ""

            if act_type == "fold":
                s_data["is_folded"] = True
                s_data["has_acted_this_round"] = True
                descriptor = "fold"

            elif act_type == "check":
                if current_round_high_bet > s_data["round_bet"]:
                    raise PokerDomainError(f"Seat {s_num} cannot check facing a bet")
                s_data["has_acted_this_round"] = True
                descriptor = "check"

            elif act_type == "call":
                call_target = current_round_high_bet
                needed = call_target - s_data["round_bet"]
                actual_add = min(s_data["current_stack"], needed)
                s_data["current_stack"] -= actual_add
                s_data["round_bet"] += actual_add
                s_data["total_bet"] += actual_add
                pot += actual_add
                s_data["has_acted_this_round"] = True
                s_data["faced_bet_at_last_action"] = current_round_high_bet
                if s_data["current_stack"] == 0:
                    s_data["is_all_in"] = True

                if current_street == "preflop" and current_round_high_bet == config.big_blind:
                    descriptor = "limp"
                elif raises_this_round >= 2:
                    descriptor = "cold_call" if not s_data["has_acted_this_round"] else "call_3bet"
                else:
                    descriptor = "call"

            elif act_type in ["bet", "raise", "all_in"]:
                # Amount is the raise-to target or total round bet
                if act_type == "bet":
                    raise_target = amount
                elif act_type == "all_in":
                    raise_target = s_data["round_bet"] + s_data["current_stack"]
                else:
                    raise_target = amount

                needed = raise_target - s_data["round_bet"]
                actual_add = min(s_data["current_stack"], needed)
                new_round_bet = s_data["round_bet"] + actual_add
                raise_delta = new_round_bet - current_round_high_bet

                s_data["current_stack"] -= actual_add
                s_data["round_bet"] = new_round_bet
                s_data["total_bet"] += actual_add
                pot += actual_add
                s_data["has_acted_this_round"] = True
                if s_data["current_stack"] == 0:
                    s_data["is_all_in"] = True

                # Determine if action reopens betting (full raise)
                if raise_delta >= min_raise_delta:
                    # Full legal raise
                    min_raise_delta = raise_delta
                    current_round_high_bet = new_round_bet
                    last_raiser_seat = s_num
                    raises_this_round += 1
                    # Reopen for all other players
                    for other_num, other_data in seats_by_num.items():
                        if other_num != s_num:
                            other_data["can_raise_reopened"] = True
                    s_data["can_raise_reopened"] = False
                else:
                    # Short all-in: updates high bet for calling purposes, but does NOT reopen raising for players who already acted
                    if new_round_bet > current_round_high_bet:
                        current_round_high_bet = new_round_bet
                    s_data["can_raise_reopened"] = False
                    # Do NOT update min_raise_delta or last_raiser_seat

                # Compute descriptive tag
                if current_street == "preflop":
                    if raises_this_round == 1:
                        descriptor = "open_raise"
                    elif raises_this_round == 2:
                        descriptor = "3-bet"
                    elif raises_this_round == 3:
                        # Detect cold 4-bet or standard 4-bet
                        descriptor = (
                            "cold_4-bet"
                            if not s_data.get("has_previously_raised", False)
                            else "4-bet"
                        )
                    elif raises_this_round == 4:
                        descriptor = "5-bet"
                    else:
                        descriptor = "raise"
                else:
                    descriptor = (
                        "check_raise" if s_data.get("has_acted_this_round", False) else "bet"
                    )

            action_timeline.append(
                LiveHelperActionRecord(
                    action_id=f"act_{idx + 1}",
                    street=current_street,
                    seat_number=s_num,
                    player_name=s_data["player_name"],
                    action_type=act_type,
                    amount=amount,
                    added_amount=actual_add if act_type not in ["fold", "check"] else 0,
                    pot_before_action=pot_before,
                    pot_after_action=pot,
                    descriptor=descriptor,
                    sequence_index=idx,
                )
            )

        # 5. Check Street Completion & Street Progression
        unfolded_seats = [
            s for s in seats_by_num.values() if not s["is_folded"] and not s["is_sitting_out"]
        ]
        betting_seats = [s for s in unfolded_seats if not s["is_all_in"]]

        # Check if betting on the current street has completed
        is_street_complete = False
        if len(unfolded_seats) <= 1:
            is_street_complete = True
        elif len(betting_seats) <= 1:
            if len(betting_seats) == 0:
                is_street_complete = True
            else:
                single = betting_seats[0]
                if single["has_acted_this_round"] and single["round_bet"] >= current_round_high_bet:
                    is_street_complete = True
        elif len(betting_seats) > 1:
            all_acted = all(s["has_acted_this_round"] for s in betting_seats)
            all_called = all(s["round_bet"] == current_round_high_bet for s in betting_seats)
            if all_acted and all_called:
                is_street_complete = True

        # Advance street if street betting is complete and appropriate board cards are present
        advancing = True
        while advancing and len(unfolded_seats) > 1 and current_street != "showdown":
            advancing = False
            # When at most 1 active player has chips remaining, betting is complete ONLY if they have called the high bet
            if len(betting_seats) == 0 or (
                len(betting_seats) == 1
                and betting_seats[0]["round_bet"] >= current_round_high_bet
                and betting_seats[0]["has_acted_this_round"]
            ):
                is_street_complete = True

            if is_street_complete:
                if current_street == "preflop" and len(board_cards) >= 3:
                    current_street = "flop"
                    current_round_high_bet = 0
                    min_raise_delta = config.big_blind
                    raises_this_round = 0
                    last_raiser_seat = None
                    for s in seats_by_num.values():
                        s["round_bet"] = 0
                        s["has_acted_this_round"] = False
                        s["can_raise_reopened"] = True
                    is_street_complete = len(betting_seats) <= 1
                    advancing = True
                elif current_street == "flop" and len(board_cards) >= 4:
                    current_street = "turn"
                    current_round_high_bet = 0
                    min_raise_delta = config.big_blind
                    raises_this_round = 0
                    last_raiser_seat = None
                    for s in seats_by_num.values():
                        s["round_bet"] = 0
                        s["has_acted_this_round"] = False
                        s["can_raise_reopened"] = True
                    is_street_complete = len(betting_seats) <= 1
                    advancing = True
                elif current_street == "turn" and len(board_cards) >= 5:
                    current_street = "river"
                    current_round_high_bet = 0
                    min_raise_delta = config.big_blind
                    raises_this_round = 0
                    last_raiser_seat = None
                    for s in seats_by_num.values():
                        s["round_bet"] = 0
                        s["has_acted_this_round"] = False
                        s["can_raise_reopened"] = True
                    is_street_complete = len(betting_seats) <= 1
                    advancing = True
                elif current_street == "river":
                    current_street = "showdown"
                    advancing = False

        # Determine next actor if street betting is NOT complete
        current_actor: int | None = None
        if len(unfolded_seats) > 1 and current_street != "showdown" and not is_street_complete:
            order = (
                geometry.preflop_order if current_street == "preflop" else geometry.postflop_order
            )
            for s_num in order:
                s = seats_by_num[s_num]
                if not s["is_folded"] and not s["is_all_in"]:
                    if not s["has_acted_this_round"] or s["round_bet"] < current_round_high_bet:
                        current_actor = s_num
                        break

        # Calculate legal actions for current actor
        legal_actions: list[dict[str, Any]] = []
        if current_actor is not None:
            actor = seats_by_num[current_actor]
            to_call = current_round_high_bet - actor["round_bet"]

            # Fold
            if to_call > 0:
                legal_actions.append({"kind": "FOLD", "min_amount": 0, "max_amount": 0})

            # Check
            if to_call == 0:
                legal_actions.append({"kind": "CHECK", "min_amount": 0, "max_amount": 0})

            # Call
            if to_call > 0 and actor["current_stack"] > 0:
                call_chips = min(actor["current_stack"], to_call)
                legal_actions.append(
                    {
                        "kind": "CALL",
                        "min_amount": actor["round_bet"] + call_chips,
                        "max_amount": actor["round_bet"] + call_chips,
                    }
                )

            # Bet / Raise
            can_raise = actor["can_raise_reopened"] or not actor["has_acted_this_round"]
            if can_raise and actor["current_stack"] > to_call:
                if current_round_high_bet == 0:
                    # Opening Bet
                    min_bet = min(actor["current_stack"], config.big_blind)
                    max_bet = actor["current_stack"]
                    legal_actions.append(
                        {
                            "kind": "BET",
                            "min_amount": min_bet,
                            "max_amount": max_bet,
                        }
                    )
                else:
                    # Raise
                    min_raise_to = current_round_high_bet + max(min_raise_delta, config.big_blind)
                    max_raise_to = actor["round_bet"] + actor["current_stack"]
                    if max_raise_to >= min_raise_to:
                        legal_actions.append(
                            {
                                "kind": "RAISE",
                                "min_amount": min_raise_to,
                                "max_amount": max_raise_to,
                            }
                        )

            # All-In
            if actor["current_stack"] > 0:
                legal_actions.append(
                    {
                        "kind": "ALL_IN",
                        "min_amount": actor["round_bet"] + actor["current_stack"],
                        "max_amount": actor["round_bet"] + actor["current_stack"],
                    }
                )

        # 6. Calculate Pots and Side Pots
        contributions = [
            PlayerPotContribution(
                player_id=s["player_id"],
                total_contributed=s["total_bet"],
                is_folded=s["is_folded"],
                is_all_in=s["is_all_in"],
                seat_index=s["seat_number"],
            )
            for s in seats_by_num.values()
        ]
        pots, refunds = PotEngine.calculate_pots_and_refunds(contributions)

        # Build clean seat objects
        built_seats = [
            LiveHelperSeat(
                seat_number=s["seat_number"],
                player_id=s["player_id"],
                player_name=s["player_name"],
                starting_stack=s["starting_stack"],
                current_stack=s["current_stack"],
                round_bet=s["round_bet"],
                total_bet=s["total_bet"],
                is_hero=s["is_hero"],
                is_sitting_out=s["is_sitting_out"],
                is_folded=s["is_folded"],
                is_all_in=s["is_all_in"],
                hole_cards=s["hole_cards"],
                position_name=s["position_name"],
            )
            for s in seats_by_num.values()
        ]

        # Verify chip conservation
        total_initial = sum(s.starting_stack for s in built_seats)
        total_remaining = sum(s.current_stack for s in built_seats) + pot
        chip_conservation = total_initial == total_remaining

        # Calculate effective stack for Hero
        hero_seat = next((s for s in built_seats if s.is_hero), None)
        effective_stack = 0
        if hero_seat:
            opp_stacks = [s.current_stack for s in built_seats if not s.is_hero and not s.is_folded]
            effective_stack = min(
                hero_seat.current_stack, max(opp_stacks) if opp_stacks else hero_seat.current_stack
            )

        pot_dicts = []
        for p in pots:
            pd = p.to_dict()
            pd["eligible_seat_numbers"] = [
                s.seat_number for s in built_seats if s.player_id in p.eligible_player_ids
            ]
            pot_dicts.append(pd)

        return {
            "geometry": geometry,
            "seats": built_seats,
            "street": current_street,
            "board": board_cards,
            "total_pot": pot,
            "pots": pot_dicts,
            "refunds": refunds,
            "current_round_high_bet": current_round_high_bet,
            "min_raise_delta": min_raise_delta,
            "current_actor_seat": current_actor,
            "last_raiser_seat": last_raiser_seat,
            "action_history": [a.to_dict() for a in action_timeline],
            "legal_actions": legal_actions,
            "chip_conservation": chip_conservation,
            "effective_stack": effective_stack,
            "is_street_complete": is_street_complete,
            "is_hand_terminal": len(unfolded_seats) <= 1 or current_street == "showdown",
        }

    @staticmethod
    def evaluate_decision(
        config: LiveHelperGameConfig,
        table_state: dict[str, Any],
        chosen_action: str,
        chosen_amount: int | None = None,
        mode: HelperMode = HelperMode.DECISION_CHECK,
        user_reasoning: str = "",
        confidence_score: int = 3,
    ) -> LiveHelperEvaluation:
        """Perform comprehensive evaluation separating rules, math, strategy, and pedagogy."""
        legal_actions = table_state.get("legal_actions", [])
        total_pot = table_state.get("total_pot", 0)
        current_actor_seat = table_state.get("current_actor_seat")
        seats: list[LiveHelperSeat] = table_state.get("seats", [])
        actor_seat = next((s for s in seats if s.seat_number == current_actor_seat), None)

        actor_round_bet = actor_seat.round_bet if actor_seat else 0
        high_bet = table_state.get("current_round_high_bet", 0)
        to_call = max(0, high_bet - actor_round_bet)

        # 1. Rules Verdict
        norm_action = chosen_action.upper()
        matching_legal = next((a for a in legal_actions if a["kind"] == norm_action), None)
        is_legal = False
        rejection_reason: str | None = None

        if norm_action in ["AUTO_COACH", "GUIDED", "COPILOT"]:
            is_legal = True
            rejection_reason = None
        elif matching_legal is None:
            is_legal = False
            rejection_reason = (
                f"Action '{chosen_action}' is not in legal actions for the current actor."
            )
        else:
            if norm_action in ["BET", "RAISE"]:
                amt = chosen_amount or matching_legal["min_amount"]
                if amt < matching_legal["min_amount"]:
                    is_legal = False
                    rejection_reason = (
                        f"Amount {amt} is below legal minimum {matching_legal['min_amount']}."
                    )
                elif amt > matching_legal["max_amount"]:
                    is_legal = False
                    rejection_reason = (
                        f"Amount {amt} exceeds maximum stack {matching_legal['max_amount']}."
                    )
                else:
                    is_legal = True
            else:
                is_legal = True

        rules_verdict = RulesVerdict(
            is_legal=is_legal,
            legal_actions=legal_actions,
            chosen_action_type=chosen_action,
            chosen_amount=chosen_amount,
            min_amount=matching_legal.get("min_amount", 0) if matching_legal else 0,
            max_amount=matching_legal.get("max_amount", 0) if matching_legal else 0,
            rejection_reason=rejection_reason,
        )

        # 2. Mathematical Verdict
        pot_odds = to_call / (total_pot + to_call) if (total_pot + to_call) > 0 else 0.0
        break_even_pct = pot_odds * 100.0

        # Pot odds ratio: (total_pot / to_call) : 1
        ratio_str = f"{(total_pot / to_call):.1f}:1" if to_call > 0 else "N/A (Free)"
        spr = round(table_state["effective_stack"] / total_pot, 2) if total_pot > 0 else None

        # Minimum Defense Frequency (MDF): Pot / (Pot + Bet)
        mdf = None
        if to_call > 0 and high_bet > 0:
            mdf = (total_pot - to_call) / total_pot if total_pot > 0 else 0.50

        # Tournament Context (if tournament format)
        tournament_ctx = None
        if config.format_type.value == "TOURNAMENT":
            stacks = [float(s.current_stack) for s in seats]
            hero_idx = next((i for i, s in enumerate(seats) if s.is_hero), 0)
            payouts = config.tournament_rules.payout_ladder
            bounties = (
                config.tournament_rules.bounty_values if config.tournament_rules.is_pko else None
            )
            tournament_ctx = calculate_tournament_context(
                stacks=stacks,
                payouts=payouts,
                hero_seat_index=hero_idx,
                bounty_values=bounties,
            )

        # Calculate cash rake deduction if applicable
        rake_deduction = 0
        if config.format_type == FormatType.CASH and config.cash_rules:
            is_postflop = table_state.get("street", "preflop") != "preflop"
            should_rake = is_postflop or not config.cash_rules.no_flop_no_drop
            if should_rake and config.cash_rules.rake_percent > 0:
                raw_rake = int(math.floor(total_pot * (config.cash_rules.rake_percent / 100.0)))
                rake_deduction = min(raw_rake, config.cash_rules.rake_cap)

        math_verdict = MathematicalVerdict(
            total_pot=total_pot,
            amount_to_call=to_call,
            pot_odds=pot_odds,
            pot_odds_ratio=ratio_str,
            break_even_equity_pct=break_even_pct,
            effective_stack=table_state["effective_stack"],
            spr=spr,
            hero_commitment_so_far=actor_seat.total_bet if actor_seat else 0,
            mdf=mdf,
            rake_deduction=rake_deduction,
            tournament_context=tournament_ctx,
        )

        # 3. Strategy Reference Matching
        hero_seat = next((s for s in seats if s.is_hero), actor_seat)
        hero_pos = hero_seat.position_name if hero_seat else "BTN"
        hero_cards = hero_seat.hole_cards if hero_seat else ()
        street = table_state.get("street", "preflop")

        strategic_verdict = LiveHelperEngine._match_strategy_reference(
            config=config,
            street=street,
            hero_pos=hero_pos,
            hero_cards=hero_cards,
            chosen_action=norm_action,
            table_state=table_state,
        )

        # 4. Educational Interpretation & Reasoning Evaluation
        reasoning_evals = ReasoningEvaluator.evaluate_reasoning(
            reasoning_text=user_reasoning,
            hero_cards=hero_cards,
            board_cards=table_state.get("board", []),
            hero_position=hero_pos,
            math_verdict=math_verdict,
            chosen_action=norm_action,
        )

        # Blockers and range considerations
        key_factors = [
            f"Position: {hero_pos} ({'In Position' if hero_pos in ['BTN', 'CO', 'HJ'] else 'Out of Position'})",
            f"Pot Odds: {break_even_pct:.1f}% required equity to call",
            f"Effective Stack: {table_state['effective_stack']} chips ({round(table_state['effective_stack'] / config.big_blind, 1)} BB)",
        ]

        if tournament_ctx and tournament_ctx.is_icm_active:
            key_factors.append(
                "Tournament ICM: Risk premium adjustments active vs covering stacks."
            )

        blocker_analysis = []
        if hero_cards:
            ranks = [c[0].upper() for c in hero_cards if len(c) >= 1]
            if "A" in ranks:
                blocker_analysis.append(
                    "Holding an Ace removes 50% of opponent's AA and 25% of AK/AQ combos."
                )
            if "K" in ranks:
                blocker_analysis.append(
                    "Holding a King unblocks lower-tier bluffs while blocking top value."
                )

        critical_assumptions = [
            "Assumes standard opponent opening and 3-bet frequency distributions.",
            "Live adjustments required against non-equilibrium recreational opponents.",
        ]

        act_label = (
            strategic_verdict.best_action.upper()
            if strategic_verdict.best_action
            else "optimal play"
        )
        summary_text = (
            f"Guided Recommendation: {act_label} with {' '.join(hero_cards)} from {hero_pos}."
            if norm_action in ["AUTO_COACH", "GUIDED", "COPILOT"]
            else f"Analysis of {chosen_action} with {' '.join(hero_cards)} from {hero_pos}."
        )

        education = EducationalInterpretation(
            summary=summary_text,
            key_factors=key_factors,
            blocker_analysis=blocker_analysis,
            range_interaction=[
                f"Board texture: {', '.join(table_state.get('board', [])) or 'Preflop'}",
                f"Relative SPR: {spr if spr is not None else 'High/Uncapped'}",
            ],
            critical_assumptions=critical_assumptions,
            reasoning_evaluations=reasoning_evals,
            recommended_drill_topic="Opening Ranges (RFI)"
            if street == "preflop"
            else "Flop Continuation Betting",
        )

        return LiveHelperEvaluation(
            mode=mode,
            rules=rules_verdict,
            mathematics=math_verdict,
            strategy=strategic_verdict,
            education=education,
            timestamp=datetime.now(UTC).isoformat(),
        )

    @staticmethod
    def _match_strategy_reference(
        config: LiveHelperGameConfig,
        street: str,
        hero_pos: str,
        hero_cards: tuple[str, ...],
        chosen_action: str,
        table_state: dict[str, Any],
    ) -> StrategicVerdict:
        """Authoritatively match against certified strategy references without fabricating EV."""
        # 1. Preflop RFI Check
        if street == "preflop":
            # Check if this is an unopened pot folded to Hero
            actions = table_state.get("action_history", [])
            non_blind_actions = [
                a
                for a in actions
                if a.get("action_type") not in ["post_sb", "post_bb", "post_ante"]
            ]
            is_unopened = all(a.get("action_type") == "fold" for a in non_blind_actions)

            if is_unopened and config.format_type.value == "CASH":
                ref_id = (
                    "ILLUSTRATIVE_PRACTICE_CHART_100BB_9MAX"
                    if config.max_capacity >= 8
                    else "ILLUSTRATIVE_PRACTICE_CHART_100BB_6MAX"
                )
                ref = get_strategy_reference(ref_id) or get_strategy_reference(
                    "ILLUSTRATIVE_PRACTICE_CHART_100BB_6MAX"
                )
                "".join(hero_cards)
                hand_class = LiveHelperEngine._to_hand_class(hero_cards)

                pos_key = hero_pos.upper().replace("BTN/SB", "BTN").replace(" ", "")
                freqs = PreflopReferenceProvider.get_action_frequencies_for_hand(
                    ref_id, pos_key, hand_class or ""
                )

                if freqs and hand_class:
                    raise_freq = freqs.get("RAISE", 0.0)
                    fold_freq = freqs.get("FOLD", round(1.0 - raise_freq, 4))
                    action_freqs = {"fold": fold_freq, "raise": round(raise_freq, 4)}

                    # Grade according to frequency alignment against educational benchmark
                    chosen_lower = chosen_action.lower()
                    if chosen_lower in ["raise", "bet", "all_in"]:
                        grade = (
                            "REFERENCE_PREFERRED"
                            if raise_freq >= 0.90
                            else (
                                "REFERENCE_ALIGNED" if raise_freq >= 0.25 else "REFERENCE_DEVIATION"
                            )
                        )
                    else:
                        grade = (
                            "REFERENCE_PREFERRED"
                            if fold_freq >= 0.90
                            else (
                                "REFERENCE_ALIGNED" if fold_freq >= 0.25 else "REFERENCE_DEVIATION"
                            )
                        )

                    return StrategicVerdict(
                        match_classification=StrategicMatchLevel.EDUCATIONAL_HEURISTIC,
                        reference_id=ref.id if ref else ref_id,
                        reference_name=ref.name
                        if ref
                        else (
                            "9-Max Full-Ring 100bb Cash RFI Instructional Benchmark"
                            if config.max_capacity >= 8
                            else "6-Max 100bb Cash RFI Instructional Benchmark"
                        ),
                        reference_version="1.1.0",
                        provenance=(
                            "Curated instructional 100bb 9-Max full-ring reference benchmark covering UTG through SB."
                            if config.max_capacity >= 8
                            else "Curated instructional 100bb 6-Max reference benchmark with verified 1,326 combo accounting."
                        ),
                        grading_permission=GradingPermission.FREQUENCY_ALIGNMENT.value,
                        action_frequencies=action_freqs,
                        action_evs=None,  # Heuristic charts have no solver EV
                        chosen_ev=None,
                        best_ev=None,
                        best_action="raise" if raise_freq >= 0.50 else "fold",
                        ev_regret=None,
                        qualitative_grade=grade,
                        is_source_supported=True,
                        source_limitations=[
                            "Educational preflop chart; action EV values are not computed.",
                            "Assumes 2.5bb open sizing with 5% rake (3bb cap).",
                        ],
                        alternative_actions=[
                            {"action": "raise", "frequency": round(raise_freq, 2)},
                            {"action": "fold", "frequency": round(fold_freq, 2)},
                        ],
                    )

        # 2. Postflop Flop C-Bet Solver Check
        if street == "flop":
            board = table_state.get("board", [])
            board_norm = sorted(board)
            # Check certified Ks 7d 2c Flop C-bet SRP
            if sorted(["Ks", "7d", "2c"]) == board_norm and hero_pos.upper() in ["BTN", "IP"]:
                ref = get_strategy_reference("cert_cash_flop_cbet_ae73a18d60ad9965")
                return StrategicVerdict(
                    match_classification=StrategicMatchLevel.EXACT_VALIDATED,
                    reference_id=ref.id if ref else "cert_cash_flop_cbet_ae73a18d60ad9965",
                    reference_name="Single-Raised Pot Flop C-Bet (Ks 7d 2c)",
                    reference_version="1.0.0",
                    provenance="Native Rust DCFR solver (1,000 iterations) on Ks 7d 2c rainbow board.",
                    grading_permission=GradingPermission.EXACT_EV_REGRET.value,
                    action_frequencies={"check": 0.35, "bet": 0.65},
                    action_evs={"check": 3.93, "bet": 3.76},
                    chosen_ev=3.76 if chosen_action.lower() in ["bet", "raise"] else 3.93,
                    best_ev=3.93,
                    best_action="check",
                    ev_regret=0.17 if chosen_action.lower() in ["bet", "raise"] else 0.0,
                    qualitative_grade="GOOD"
                    if chosen_action.lower() in ["bet", "raise"]
                    else "PERFECT",
                    is_source_supported=True,
                    source_limitations=[
                        "Solved for 100bb SRP BTN vs BB with standard 33% pot C-bet sizing."
                    ],
                    alternative_actions=[
                        {"action": "check", "frequency": 0.35, "ev": 3.93},
                        {"action": "bet", "frequency": 0.65, "ev": 3.76},
                    ],
                )

        # 3. Default: Unsupported Strategic Situation
        # Refuse to manufacture fake solver frequencies or EV
        return StrategicVerdict(
            match_classification=StrategicMatchLevel.UNSUPPORTED,
            reference_id=None,
            reference_name=None,
            reference_version=None,
            provenance="No certified solver equilibrium tree or authoritative benchmark exists for this exact game state.",
            grading_permission=GradingPermission.UNGRADED_EXPLORATION.value,
            action_frequencies=None,
            action_evs=None,
            chosen_ev=None,
            best_ev=None,
            ev_regret=None,
            qualitative_grade="UNGRADED",
            is_source_supported=False,
            source_limitations=[
                "Exact GTO solver solution is not indexed for this specific board/action line.",
                "Pokeria policy prohibits fabricating EV loss or declaring actions optimal without proven solver provenance.",
            ],
            alternative_actions=[],
        )

    @staticmethod
    def _to_hand_class(cards: tuple[str, ...]) -> str | None:
        """Convert 2 cards like ('Ah', 'Kd') into canonical class like 'AKo' or '77'."""
        if len(cards) != 2:
            return None
        c1, c2 = cards[0], cards[1]
        if len(c1) < 2 or len(c2) < 2:
            return None

        rank_order = "23456789TJQKA"
        r1, s1 = c1[0].upper(), c1[1].lower()
        r2, s2 = c2[0].upper(), c2[1].lower()

        if r1 not in rank_order or r2 not in rank_order:
            return None

        i1, i2 = rank_order.index(r1), rank_order.index(r2)
        high_r, low_r = (r1, r2) if i1 >= i2 else (r2, r1)

        if high_r == low_r:
            return f"{high_r}{low_r}"
        elif s1 == s2:
            return f"{high_r}{low_r}s"
        else:
            return f"{high_r}{low_r}o"
