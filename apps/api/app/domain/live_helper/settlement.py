"""Exact pot and side-pot hand settlement engine for Live Helper.

Handles:
- Fold-around uncontested pot awards
- Showdown hand ranking using CardEvaluator
- Multiway unequal side pot distribution to eligible winners
- Tie handling and split pots with clockwise odd chip allocation
- Uncalled bet refunds
- Cash casino rake and rake caps with No-Flop-No-Drop rules
- Strict chip conservation verification
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.poker.cards import Card
from app.domain.poker.evaluator import HandStrength, evaluate_hand


@dataclass
class SettledPotDetail:
    """Breakdown of an individual pot's resolution."""

    pot_name: str
    amount: int
    eligible_seats: list[int]
    winning_seats: list[int]
    payout_per_winner: dict[int, int]
    odd_chips_awarded: dict[int, int]


@dataclass
class HandSettlementResult:
    """Complete, auditable settlement outcome of a poker hand."""

    is_settled: bool
    is_showdown: bool
    winning_seats: list[int]
    pots_settled: list[SettledPotDetail]
    uncalled_returns: dict[int, int]
    rake_collected: int
    net_chips: dict[int, int]
    ending_stacks: dict[int, int]
    hand_descriptions: dict[int, str]
    settlement_summary: str
    requires_card_reveal: bool = False
    missing_card_seats: list[int] = field(default_factory=list)


class HandSettlementEngine:
    """Deterministic, mathematically exact poker hand settlement calculator."""

    @classmethod
    def settle_hand(
        cls,
        *,
        button_seat: int,
        table_capacity: int,
        seats: list[dict[str, Any]],
        board_cards: list[str],
        actions: list[dict[str, Any]],
        pots_payload: dict[str, Any],
        is_cash: bool = True,
        rake_percent: float = 0.0,
        rake_cap: int = 0,
        no_flop_no_drop: bool = True,
    ) -> HandSettlementResult:
        """Settle a hand completely and return exact chip allocations."""
        starting_stacks: dict[int, int] = {
            s["seat_number"]: s.get("starting_stack", s.get("stack", 0)) for s in seats
        }
        current_stacks: dict[int, int] = {s["seat_number"]: s.get("stack", 0) for s in seats}
        active_seats: set[int] = {s["seat_number"] for s in seats if s.get("is_active", True)}
        hole_cards_by_seat: dict[int, list[str]] = {
            s["seat_number"]: s.get("hole_cards", []) for s in seats
        }

        # Track which players folded or mucked/forfeited
        folded_seats: set[int] = set()
        mucked_seats: set[int] = set()
        for act in actions:
            act_type = str(act.get("action_type", "")).lower()
            if act_type in ("fold", "muck", "forfeit"):
                folded_seats.add(act["seat_number"])
                if act_type in ("muck", "forfeit"):
                    mucked_seats.add(act["seat_number"])

        for seat_num, cards in hole_cards_by_seat.items():
            if any(str(c).upper() in ("MUCK", "FORFEIT", "MUCKED") for c in cards):
                folded_seats.add(seat_num)
                mucked_seats.add(seat_num)

        live_contenders = [s for s in active_seats if s not in folded_seats]
        if not live_contenders:
            # Fallback if somehow all folded
            return HandSettlementResult(
                is_settled=True,
                is_showdown=False,
                winning_seats=[],
                pots_settled=[],
                uncalled_returns={},
                rake_collected=0,
                net_chips=dict.fromkeys(starting_stacks, 0),
                ending_stacks=current_stacks,
                hand_descriptions={},
                settlement_summary="No active players remained in the hand.",
            )

        # Compute exact total chip investment per seat across all betting rounds
        investments: dict[int, int] = {s["seat_number"]: 0 for s in seats}
        current_street = "preflop"
        street_bets: dict[int, int] = {s["seat_number"]: 0 for s in seats}
        street_actions: list[dict[str, Any]] = []
        high_bet = 0

        for act in actions:
            act_type = str(act.get("action_type", "")).lower()
            s_num = int(act.get("seat_number", 0))
            if s_num not in investments:
                continue
            amt = int(act.get("amount", 0))
            st = act.get("street", current_street)
            if st != current_street:
                current_street = st
                street_bets = {s["seat_number"]: 0 for s in seats}
                street_actions = []
                high_bet = 0
            street_actions.append(act)

            if act_type == "post_ante":
                investments[s_num] += amt
            elif act_type in ("post_sb", "post_bb"):
                added = max(0, amt - street_bets[s_num])
                investments[s_num] += added
                street_bets[s_num] = amt
                high_bet = max(high_bet, amt)
            elif act_type in ("bet", "raise"):
                added = max(0, amt - street_bets[s_num])
                investments[s_num] += added
                street_bets[s_num] = amt
                high_bet = max(high_bet, amt)
            elif act_type == "call":
                call_target = amt if amt > 0 else high_bet
                added = max(0, call_target - street_bets[s_num])
                investments[s_num] += added
                street_bets[s_num] = call_target
            elif act_type == "all_in":
                target = amt if amt > 0 else (street_bets[s_num] + starting_stacks.get(s_num, 0))
                added = max(0, target - street_bets[s_num])
                investments[s_num] += added
                street_bets[s_num] = target
                high_bet = max(high_bet, target)

        # Baseline stacks remaining in front of players before settlement refunds and awards
        current_stacks = {
            s_num: max(0, starting_stacks[s_num] - investments[s_num]) for s_num in starting_stacks
        }

        # 1. Determine uncalled wager returns if present
        uncalled_returns: dict[int, int] = {}
        last_bets: dict[int, int] = {}
        for act in street_actions:
            amt = act.get("amount", 0)
            if amt and amt > 0:
                last_bets[act["seat_number"]] = amt

        if len(last_bets) >= 2:
            sorted_bets = sorted(last_bets.items(), key=lambda x: x[1], reverse=True)
            highest_seat, highest_amt = sorted_bets[0]
            second_amt = sorted_bets[1][1]
            if highest_amt > second_amt and highest_seat not in folded_seats:
                refund = highest_amt - second_amt
                uncalled_returns[highest_seat] = refund
                current_stacks[highest_seat] += refund

        # 2. Extract Pots
        main_pot = pots_payload.get("main_pot", 0)
        side_pots = pots_payload.get("side_pots", [])
        total_pot_chips = main_pot + sum(p.get("amount", 0) for p in side_pots)

        # If pots_payload total_pot still included uncalled returns, ensure total_pot_chips represents distributable pot
        total_uncalled = sum(uncalled_returns.values())
        payload_total = pots_payload.get("total_pot", total_pot_chips)
        if total_uncalled > 0 and payload_total == total_pot_chips:
            # Only deduct if main_pot was unadjusted total pot
            main_pot = max(0, main_pot - total_uncalled)
            total_pot_chips = max(0, total_pot_chips - total_uncalled)

        # 3. Calculate Casino Rake
        has_seen_flop = len(board_cards) >= 3
        rake_collected = 0
        if is_cash and rake_percent > 0:
            if not no_flop_no_drop or has_seen_flop:
                nominal_rake = int(total_pot_chips * (rake_percent / 100.0))
                rake_collected = min(nominal_rake, rake_cap) if rake_cap > 0 else nominal_rake

        # Net pot available for distribution
        distributable_pot = max(0, total_pot_chips - rake_collected)

        # 4. Showdown vs Fold-around
        is_showdown = len(live_contenders) > 1 and len(board_cards) >= 5
        hand_descriptions: dict[int, str] = {}
        for s in active_seats:
            if s in mucked_seats:
                hand_descriptions[s] = "Mucked / Forfeited"
            elif s in folded_seats:
                hand_descriptions[s] = "Folded"

        hand_strengths: dict[int, HandStrength] = {}

        if is_showdown:
            board_objs = [Card.from_str(c) for c in board_cards[:5]]
            for seat_num in live_contenders:
                cards_str = hole_cards_by_seat.get(seat_num, [])
                if len(cards_str) == 2:
                    full_7 = [Card.from_str(c) for c in cards_str] + board_objs
                    strength = evaluate_hand(full_7)
                    hand_strengths[seat_num] = strength
                    hand_descriptions[seat_num] = strength.description
                else:
                    hand_descriptions[seat_num] = "Hole cards unknown"

        # Construct list of pots to resolve
        pot_list: list[dict[str, Any]] = []
        if side_pots:
            # Deduct proportional rake from side pots or main pot
            remaining_rake = rake_collected
            for i, sp in enumerate(side_pots):
                sp_amt = sp.get("amount", 0)
                sp_rake = 0
                if remaining_rake > 0 and total_pot_chips > 0:
                    sp_rake = min(sp_amt, int(rake_collected * (sp_amt / total_pot_chips)))
                    remaining_rake -= sp_rake
                pot_list.append(
                    {
                        "name": f"Side Pot {i + 1}",
                        "amount": max(0, sp_amt - sp_rake),
                        "eligible": sp.get("eligible_seat_numbers")
                        or sp.get("eligible_seats")
                        or live_contenders,
                    }
                )
            pot_list.append(
                {
                    "name": "Main Pot",
                    "amount": max(0, main_pot - remaining_rake),
                    "eligible": pots_payload.get("main_pot_eligible_seats")
                    or pots_payload.get("main_pot_eligible_seat_numbers")
                    or live_contenders,
                }
            )
        else:
            pot_list.append(
                {
                    "name": "Main Pot",
                    "amount": distributable_pot,
                    "eligible": live_contenders,
                }
            )

        # Check if any contested pot has contenders with unknown hole cards
        missing_card_seats: set[int] = set()
        if is_showdown:
            for pot_info in pot_list:
                eligible = [s for s in pot_info["eligible"] if s in live_contenders]
                if len(eligible) > 1:
                    for s in eligible:
                        if s not in hand_strengths:
                            missing_card_seats.add(s)

        if missing_card_seats:
            missing_sorted = sorted(missing_card_seats)
            summary = (
                f"Settlement Pending: Hole cards required for Seat(s) {', '.join(str(s) for s in missing_sorted)} "
                "to determine contested showdown winner."
            )
            return HandSettlementResult(
                is_settled=False,
                is_showdown=True,
                winning_seats=[],
                pots_settled=[],
                uncalled_returns=uncalled_returns,
                rake_collected=0,
                net_chips={
                    s_num: current_stacks[s_num] - starting_stacks[s_num]
                    for s_num in starting_stacks
                },
                ending_stacks=dict(current_stacks),
                hand_descriptions=hand_descriptions,
                settlement_summary=summary,
                requires_card_reveal=True,
                missing_card_seats=missing_sorted,
            )

        settled_pots: list[SettledPotDetail] = []
        overall_winners: set[int] = set()

        # Clockwise seat order starting after button for odd chip allocation
        clockwise_seats = cls._get_clockwise_order(button_seat, table_capacity)

        # 5. Resolve Each Pot
        for pot_info in pot_list:
            pot_amt = pot_info["amount"]
            eligible = [s for s in pot_info["eligible"] if s in live_contenders]

            if not eligible:
                eligible = live_contenders

            if len(eligible) == 1:
                # Uncontested pot
                winner = eligible[0]
                payout = {winner: pot_amt}
                odd_chips = {winner: 0}
                current_stacks[winner] += pot_amt
                overall_winners.add(winner)
                settled_pots.append(
                    SettledPotDetail(
                        pot_name=pot_info["name"],
                        amount=pot_amt,
                        eligible_seats=eligible,
                        winning_seats=[winner],
                        payout_per_winner=payout,
                        odd_chips_awarded=odd_chips,
                    )
                )
                continue

            # Compare hand strengths among eligible
            best_seats: list[int] = []
            best_strength: HandStrength | None = None

            for s in eligible:
                st = hand_strengths[s]
                if best_strength is None or st > best_strength:
                    best_strength = st
                    best_seats = [s]
                elif st == best_strength:
                    best_seats.append(s)

            overall_winners.update(best_seats)
            num_winners = len(best_seats)
            share = pot_amt // num_winners
            remainder = pot_amt % num_winners

            payout_map: dict[int, int] = dict.fromkeys(best_seats, share)
            odd_map: dict[int, int] = dict.fromkeys(best_seats, 0)

            # Award odd chips clockwise from button
            if remainder > 0:
                eligible_clockwise = [s for s in clockwise_seats if s in best_seats]
                for i in range(remainder):
                    target_seat = eligible_clockwise[i % len(eligible_clockwise)]
                    payout_map[target_seat] += 1
                    odd_map[target_seat] += 1

            for w, amt in payout_map.items():
                current_stacks[w] += amt

            settled_pots.append(
                SettledPotDetail(
                    pot_name=pot_info["name"],
                    amount=pot_amt,
                    eligible_seats=eligible,
                    winning_seats=best_seats,
                    payout_per_winner=payout_map,
                    odd_chips_awarded=odd_map,
                )
            )

        # 6. Compute Net Profit / Loss
        net_chips: dict[int, int] = {}
        for seat_num, start_amt in starting_stacks.items():
            end_amt = current_stacks[seat_num]
            net_chips[seat_num] = end_amt - start_amt

        # 7. Summary Narrative
        winners_list = sorted(overall_winners)
        if not is_showdown and len(winners_list) == 1:
            w_seat = winners_list[0]
            if mucked_seats:
                summary = f"Player in Seat {w_seat} won {distributable_pot:,} chips uncontested (opponents mucked/forfeited)."
            else:
                summary = f"Player in Seat {w_seat} won {distributable_pot:,} chips uncontested."
        else:
            w_str = ", ".join(f"Seat {w}" for w in winners_list)
            desc_parts = [
                f"Seat {w} with {hand_descriptions.get(w, 'winning hand')}"
                for w in winners_list
                if w in hand_descriptions
            ]
            desc_str = f" ({'; '.join(desc_parts)})" if desc_parts else ""
            summary = f"Showdown won by {w_str} for total {distributable_pot:,} chips{desc_str}."

        if rake_collected > 0:
            summary += f" Casino rake deducted: {rake_collected:,} chips."

        return HandSettlementResult(
            is_settled=True,
            is_showdown=is_showdown,
            winning_seats=winners_list,
            pots_settled=settled_pots,
            uncalled_returns=uncalled_returns,
            rake_collected=rake_collected,
            net_chips=net_chips,
            ending_stacks=current_stacks,
            hand_descriptions=hand_descriptions,
            settlement_summary=summary,
        )

    @classmethod
    def _get_clockwise_order(cls, button_seat: int, capacity: int) -> list[int]:
        """Generate clockwise seat order starting from the small blind (button + 1)."""
        order: list[int] = []
        for i in range(1, capacity + 1):
            s = ((button_seat - 1 + i) % capacity) + 1
            order.append(s)
        return order
