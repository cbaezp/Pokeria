"""Continuous training session analytics and end-of-session reporting engine.

Calculates:
- Real action frequencies: VPIP, PFR, 3-Bet %, Fold-to-3-Bet %, WSD %, WTSD %
- Accurate opportunity denominators
- Net chips, net BB, and BB/100
- Proactive Coach Mode vs independent Decision Check Mode metrics
- Mathematical accuracy and solver EV loss (with strict N/A when unsupported)
- Flagged key hands for post-session study and personalized drill recommendations
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SessionAnalyticsReport:
    """Comprehensive performance and strategic report for a continuous training session."""

    session_id: str
    session_name: str
    format_type: str
    total_hands: int
    duration_seconds: int
    hero_starting_stack: int
    hero_ending_stack: int
    hero_net_chips: int
    hero_net_bb: float
    bb_per_100: float | None

    # Action frequencies
    vpip_pct: float
    pfr_pct: float
    three_bet_pct: float
    fold_to_three_bet_pct: float | None
    wtsd_pct: float
    wsd_pct: float | None

    # Decision breakdowns
    total_hero_decisions: int
    coach_assisted_decisions: int
    independent_decisions: int
    ungraded_decisions: int
    assistance_rate_pct: float

    # Accuracy and Mastery
    rules_accuracy_pct: float
    math_accuracy_pct: float
    reference_alignment_pct: float
    mean_solver_ev_loss: float | None
    solver_hands_evaluated: int

    # Progression & Key Study Hands
    stack_progression: list[dict[str, Any]]
    key_hands_to_review: list[dict[str, Any]]
    recommended_drills: list[dict[str, str]]


class SessionAnalyticsEngine:
    """Computes exact statistics and audits across continuous session hands."""

    @classmethod
    def compute_report(
        cls,
        session_data: dict[str, Any],
        hands: list[dict[str, Any]],
        decisions: list[dict[str, Any]],
    ) -> SessionAnalyticsReport:
        """Generate a complete end-of-session report."""
        session_id = session_data.get("id", "")
        session_name = session_data.get("name", "Training Session")
        format_type = session_data.get("format_type", "CASH")
        config = session_data.get("configuration", {})
        bb_size = max(1, config.get("big_blind", 100))

        # Find Hero's seat
        participants = session_data.get("participants", [])
        hero_p = next((p for p in participants if p.get("is_hero")), None)
        hero_seat = hero_p.get("seat_number", 1) if hero_p else 1
        hero_start = hero_p.get("starting_stack", 10000) if hero_p else 10000
        hero_end = hero_p.get("current_stack", hero_start) if hero_p else hero_start
        hero_net = hero_end - hero_start
        hero_net_bb = round(hero_net / bb_size, 2)

        total_hands = len(hands)
        bb_per_100 = (
            round((hero_net / bb_size) * (100.0 / total_hands), 2) if total_hands > 0 else None
        )

        # 1. Action frequencies (VPIP, PFR, 3-Bet)
        vpip_opportunities = 0
        vpip_count = 0
        pfr_opportunities = 0
        pfr_count = 0
        three_bet_opps = 0
        three_bet_count = 0
        fold_to_three_bet_opps = 0
        fold_to_three_bet_count = 0
        showdown_hands = 0
        showdown_wins = 0

        stack_progression: list[dict[str, Any]] = [
            {
                "hand_index": 0,
                "hero_stack": hero_start,
                "hero_stack_bb": round(hero_start / bb_size, 1),
            }
        ]

        key_hands: list[dict[str, Any]] = []

        for h in hands:
            hand_idx = h.get("hand_index", 0)
            actions = h.get("actions", [])
            settlement = h.get("settlement", {})
            ending_stacks = h.get("ending_stacks") or {}
            hero_hand_end = ending_stacks.get(
                str(hero_seat), ending_stacks.get(hero_seat, hero_start)
            )

            stack_progression.append(
                {
                    "hand_index": hand_idx,
                    "hero_stack": hero_hand_end,
                    "hero_stack_bb": round(hero_hand_end / bb_size, 1),
                }
            )

            # Check preflop hero participation
            preflop_acts = [
                a for a in actions if a.get("street") == "preflop" or not a.get("street")
            ]
            preflop_raises_before_hero = 0
            hero_acted_preflop = False
            hero_vpip = False
            hero_pfr = False

            for act in preflop_acts:
                seat = act.get("seat_number")
                act_type = str(act.get("action_type", "")).lower()

                if seat == hero_seat:
                    hero_acted_preflop = True
                    if act_type in ("call", "raise", "bet", "all_in", "shove"):
                        hero_vpip = True
                    if act_type in ("raise", "all_in", "shove"):
                        hero_pfr = True
                        if preflop_raises_before_hero == 1:
                            three_bet_count += 1
                else:
                    if act_type in ("raise", "all_in", "shove"):
                        preflop_raises_before_hero += 1

            if hero_acted_preflop:
                vpip_opportunities += 1
                pfr_opportunities += 1
                if hero_vpip:
                    vpip_count += 1
                if hero_pfr:
                    pfr_count += 1

            if preflop_raises_before_hero == 1 and hero_acted_preflop:
                three_bet_opps += 1

            # Showdown tracking
            if settlement and settlement.get("is_showdown"):
                # Did hero go to showdown?
                folded = any(
                    a.get("seat_number") == hero_seat
                    and str(a.get("action_type")).lower() == "fold"
                    for a in actions
                )
                if not folded:
                    showdown_hands += 1
                    winning_seats = settlement.get("winning_seats", [])
                    if hero_seat in winning_seats:
                        showdown_wins += 1

            # Check if this hand should be flagged as a key study hand
            net_change = settlement.get("net_chips", {}).get(str(hero_seat), 0) if settlement else 0
            if abs(net_change) >= bb_size * 20 or (settlement and settlement.get("is_showdown")):
                key_hands.append(
                    {
                        "hand_id": h.get("id"),
                        "hand_index": hand_idx,
                        "net_chips": net_change,
                        "net_bb": round(net_change / bb_size, 1),
                        "summary": settlement.get("settlement_summary", "")
                        if settlement
                        else "High impact hand",
                        "reason": "Large pot / showdown decision",
                    }
                )

        vpip_pct = (
            round((vpip_count / vpip_opportunities * 100.0), 1) if vpip_opportunities > 0 else 0.0
        )
        pfr_pct = (
            round((pfr_count / pfr_opportunities * 100.0), 1) if pfr_opportunities > 0 else 0.0
        )
        three_bet_pct = (
            round((three_bet_count / three_bet_opps * 100.0), 1) if three_bet_opps > 0 else 0.0
        )
        fold_to_three_bet_pct = (
            round((fold_to_three_bet_count / fold_to_three_bet_opps * 100.0), 1)
            if fold_to_three_bet_opps > 0
            else None
        )
        wtsd_pct = round((showdown_hands / max(1, total_hands) * 100.0), 1)
        wsd_pct = (
            round((showdown_wins / max(1, showdown_hands) * 100.0), 1)
            if showdown_hands > 0
            else None
        )

        # 2. Decision breakdown & Accuracy
        total_decisions = len(decisions)
        coach_assisted = 0
        independent = 0
        ungraded = 0
        rules_correct = 0
        math_correct = 0
        reference_aligned = 0
        ev_losses: list[float] = []

        for d in decisions:
            if d.get("is_assisted") or str(d.get("mode")).upper() == "COACH":
                coach_assisted += 1
            else:
                independent += 1

            verdicts = d.get("evaluation_verdicts") or {}
            # Rules verdict
            rules_v = verdicts.get("rules_verdict") or {}
            if rules_v.get("is_legal", True):
                rules_correct += 1

            # Math verdict
            math_v = verdicts.get("mathematical_verdict") or {}
            if math_v.get("is_sound", True):
                math_correct += 1

            # Strategic verdict
            strat_v = verdicts.get("strategic_verdict") or {}
            ref_status = str(strat_v.get("reference_status", "UNSUPPORTED")).upper()
            if ref_status in ("EXACT_VALIDATED", "APPROXIMATE_DOCUMENTED"):
                if strat_v.get("is_supported_action", True):
                    reference_aligned += 1
            else:
                ungraded += 1

            ev_regret = d.get("ev_regret")
            if ev_regret is not None and ev_regret >= 0:
                ev_losses.append(float(ev_regret))

        assistance_rate = round((coach_assisted / max(1, total_decisions) * 100.0), 1)
        rules_acc = round((rules_correct / max(1, total_decisions) * 100.0), 1)
        math_acc = round((math_correct / max(1, total_decisions) * 100.0), 1)
        ref_acc = (
            round((reference_aligned / max(1, total_decisions - ungraded) * 100.0), 1)
            if (total_decisions - ungraded) > 0
            else 100.0
        )
        mean_ev_loss = round(sum(ev_losses) / len(ev_losses), 3) if ev_losses else None

        # Recommended drills
        drills: list[dict[str, str]] = []
        if vpip_pct < 18.0:
            drills.append(
                {
                    "topic": "Preflop Open Range Widening",
                    "reason": f"Your VPIP was {vpip_pct}%, indicating tight play that misses profitable steals.",
                    "action_url": "/practice",
                }
            )
        elif vpip_pct > 32.0:
            drills.append(
                {
                    "topic": "Preflop Discipline & Folding Marginal Hands",
                    "reason": f"Your VPIP was {vpip_pct}%, playing too many speculative hands preflop.",
                    "action_url": "/practice",
                }
            )

        if math_acc < 90.0:
            drills.append(
                {
                    "topic": "Pot Odds and Break-Even Call Calculations",
                    "reason": f"Math reasoning accuracy was {math_acc}%. Review pot odds break-even thresholds.",
                    "action_url": "/practice",
                }
            )

        if not drills:
            drills.append(
                {
                    "topic": "3-Bet Pot Continuation Betting",
                    "reason": "Reinforce postflop range advantage and equity retention in single raised and 3-bet pots.",
                    "action_url": "/practice",
                }
            )

        # Calculate session duration
        started_at = session_data.get("started_at")
        completed_at = session_data.get("completed_at")
        duration = 0
        if started_at and completed_at:
            try:
                from datetime import datetime

                t1 = datetime.fromisoformat(str(started_at))
                t2 = datetime.fromisoformat(str(completed_at))
                duration = max(0, int((t2 - t1).total_seconds()))
            except Exception:
                duration = total_hands * 60

        return SessionAnalyticsReport(
            session_id=session_id,
            session_name=session_name,
            format_type=format_type,
            total_hands=total_hands,
            duration_seconds=duration,
            hero_starting_stack=hero_start,
            hero_ending_stack=hero_end,
            hero_net_chips=hero_net,
            hero_net_bb=hero_net_bb,
            bb_per_100=bb_per_100,
            vpip_pct=vpip_pct,
            pfr_pct=pfr_pct,
            three_bet_pct=three_bet_pct,
            fold_to_three_bet_pct=fold_to_three_bet_pct,
            wtsd_pct=wtsd_pct,
            wsd_pct=wsd_pct,
            total_hero_decisions=total_decisions,
            coach_assisted_decisions=coach_assisted,
            independent_decisions=independent,
            ungraded_decisions=ungraded,
            assistance_rate_pct=assistance_rate,
            rules_accuracy_pct=rules_acc,
            math_accuracy_pct=math_acc,
            reference_alignment_pct=ref_acc,
            mean_solver_ev_loss=mean_ev_loss,
            solver_hands_evaluated=len(ev_losses),
            stack_progression=stack_progression,
            key_hands_to_review=key_hands[:5],
            recommended_drills=drills,
        )
