"""Continuous Training Session Manager for Pokeria Live Helper.

Manages:
- Multi-hand session lifecycle: CREATED -> ACTIVE -> PAUSED -> COMPLETED
- Stack continuity across hands with strict chip conservation
- Proactive Coach Mode vs independent Decision Check Mode execution
- Real-time hand action progression preflop through river and showdown
- Idempotent pot settlement and next-hand progression with dealer rotation
- Cash rebuys/top-ups/cash-outs and tournament eliminations
- Concurrency-safe atomic state transitions
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from app.domain.live_helper.engine import LiveHelperEngine
from app.domain.live_helper.models import (
    CashRuleConfig,
    FormatType,
    HelperMode,
    LiveHelperGameConfig,
    SpecificGameFormat,
    TournamentRuleConfig,
)
from app.domain.live_helper.settlement import HandSettlementEngine
from app.domain.poker.seat_geometry import (
    TableSeatConfig,
    infer_table_geometry,
)


def _build_domain_config(
    session_cfg: dict[str, Any], format_type: str = "CASH"
) -> LiveHelperGameConfig:
    """Build domain LiveHelperGameConfig from session configuration dictionary."""
    cash_rules = session_cfg.get("cash_rules") or {}
    cash_cfg = CashRuleConfig(
        rake_percent=float(cash_rules.get("rake_percent", 5.0)),
        rake_cap=int(cash_rules.get("rake_cap", 300)),
        no_flop_no_drop=bool(cash_rules.get("no_flop_no_drop", True)),
    )
    tourn_rules = session_cfg.get("tournament_rules") or {}
    tourn_cfg = TournamentRuleConfig(
        buy_in=float(tourn_rules.get("buy_in", 100.0)),
        total_entrants=int(tourn_rules.get("total_entrants", 100)),
        players_remaining=int(tourn_rules.get("players_remaining", 20)),
        paid_positions=int(tourn_rules.get("paid_positions", 15)),
        payout_ladder=list(tourn_rules.get("payout_ladder", [])),
        bounty_values=list(tourn_rules.get("bounty_values", [])),
        is_pko=bool(tourn_rules.get("is_pko", False)),
        current_level=int(tourn_rules.get("current_level", 1)),
    )
    fmt = format_type.upper()
    return LiveHelperGameConfig(
        format_type=FormatType(fmt if fmt in ("CASH", "TOURNAMENT") else "CASH"),
        specific_format=SpecificGameFormat(
            session_cfg.get(
                "specific_format", "ONLINE_6MAX" if fmt == "CASH" else "STANDARD_MTT"
            ).upper()
        ),
        max_capacity=int(session_cfg.get("max_capacity", 6)),
        small_blind=int(session_cfg.get("small_blind", 50)),
        big_blind=int(session_cfg.get("big_blind", 100)),
        ante=int(session_cfg.get("ante", 0)),
        ante_type=session_cfg.get("ante_type", "NONE"),
        starting_street=session_cfg.get("starting_street", "preflop"),
        cash_rules=cash_cfg,
        tournament_rules=tourn_cfg,
        chip_denomination_label=session_cfg.get("chip_denomination_label", "Chips"),
    )


class LiveHelperSessionEngine:
    """Core domain service for continuous multi-hand training sessions."""

    @classmethod
    def create_session(
        cls,
        *,
        profile_id: str,
        name: str,
        format_type: str = "CASH",
        game_configuration_id: str = "online_cash_6max_100bb",
        default_mode: str = "DECISION_CHECK",
        table_capacity: int = 6,
        button_seat: int = 1,
        configuration: dict[str, Any],
        participants: list[dict[str, Any]],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Initialize a new continuous training session and its first hand."""
        session_id = str(uuid.uuid4())
        hand_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        # Standardize participant structures
        normalized_participants: list[dict[str, Any]] = []
        for p in participants:
            s_num = int(p.get("seat_number", 1))
            st = int(p.get("starting_stack", p.get("current_stack", p.get("stack", 10000))))
            normalized_participants.append(
                {
                    "seat_number": s_num,
                    "player_id": p.get("player_id", f"p_{s_num}"),
                    "player_name": p.get("player_name", f"Player {s_num}"),
                    "starting_stack": st,
                    "current_stack": st,
                    "is_hero": bool(p.get("is_hero", False)),
                    "is_active": bool(p.get("is_active", True)),
                    "is_sitting_out": bool(p.get("is_sitting_out", False)),
                    "rebuys": 0,
                    "cash_outs": 0,
                }
            )

        session_dict: dict[str, Any] = {
            "id": session_id,
            "profile_id": profile_id,
            "name": name,
            "format_type": format_type.upper(),
            "game_configuration_id": game_configuration_id,
            "status": "ACTIVE",
            "default_mode": default_mode.upper(),
            "table_capacity": table_capacity,
            "configuration": configuration,
            "participants": normalized_participants,
            "current_hand_id": hand_id,
            "current_hand_index": 1,
            "total_hands_completed": 0,
            "session_metadata": {
                "created_via": "LIVE_HELPER_SESSION_ENGINE",
                "notes": "",
            },
            "started_at": now.isoformat(),
            "paused_at": None,
            "completed_at": None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        # Initialize Hand #1
        hand_dict = cls._create_hand_record(
            session_id=session_id,
            hand_id=hand_id,
            hand_index=1,
            button_seat=button_seat,
            configuration=configuration,
            participants=normalized_participants,
            now=now,
        )

        return session_dict, hand_dict

    @classmethod
    def _create_hand_record(
        cls,
        *,
        session_id: str,
        hand_id: str,
        hand_index: int,
        button_seat: int,
        configuration: dict[str, Any],
        participants: list[dict[str, Any]],
        now: datetime,
    ) -> dict[str, Any]:
        """Scaffold a fresh hand record carrying forward stacks."""
        sb = configuration.get("small_blind", 100)
        bb = configuration.get("big_blind", 200)
        ante = configuration.get("ante", 0)

        starting_stacks: dict[str, int] = {
            str(p["seat_number"]): p["current_stack"] for p in participants if p["is_active"]
        }
        hole_cards: dict[str, list[str]] = {
            str(p["seat_number"]): p.get("hole_cards", []) for p in participants if p["is_active"]
        }

        # Auto-post blinds and antes in preflop actions
        initial_actions: list[dict[str, Any]] = []
        occupied_seats = [
            p["seat_number"] for p in participants if p["is_active"] and not p["is_sitting_out"]
        ]
        seat_configs = [
            TableSeatConfig(
                seat_number=p["seat_number"],
                player_id=p.get("player_id", f"p_{p['seat_number']}"),
                player_name=p["player_name"],
                stack=p["current_stack"],
                is_hero=p.get("is_hero", False),
                is_sitting_out=p.get("is_sitting_out", False),
                hole_cards=tuple(p.get("hole_cards", [])),
            )
            for p in participants
            if p.get("is_active", True) and not p.get("is_sitting_out", False)
        ]

        cap = int(configuration.get("max_capacity", max(len(participants), 2)))
        geo = infer_table_geometry(max_capacity=cap, button_seat=button_seat, seats=seat_configs)
        sb_seat = geo.sb_seat
        bb_seat = geo.bb_seat

        # Ante if applicable
        if ante > 0:
            for s in occupied_seats:
                initial_actions.append(
                    {
                        "action_id": str(uuid.uuid4()),
                        "seat_number": s,
                        "action_type": "post_ante",
                        "amount": ante,
                        "street": "preflop",
                        "descriptor": "Ante",
                    }
                )

        # Small blind
        initial_actions.append(
            {
                "action_id": str(uuid.uuid4()),
                "seat_number": sb_seat,
                "action_type": "post_sb",
                "amount": sb,
                "street": "preflop",
                "descriptor": "Post SB",
            }
        )

        # Big blind
        initial_actions.append(
            {
                "action_id": str(uuid.uuid4()),
                "seat_number": bb_seat,
                "action_type": "post_bb",
                "amount": bb,
                "street": "preflop",
                "descriptor": "Post BB",
            }
        )

        # Initial pot
        initial_pot = sb + bb + (ante * len(occupied_seats))

        return {
            "id": hand_id,
            "session_id": session_id,
            "hand_index": hand_index,
            "button_seat": button_seat,
            "small_blind": sb,
            "big_blind": bb,
            "ante": ante,
            "starting_stacks": starting_stacks,
            "ending_stacks": None,
            "hole_cards": hole_cards,
            "board": [],
            "street": "preflop",
            "actions": initial_actions,
            "pots": {
                "total_pot": initial_pot,
                "main_pot": initial_pot,
                "side_pots": [],
            },
            "settlement": None,
            "is_settled": False,
            "created_at": now.isoformat(),
            "settled_at": None,
        }

    @classmethod
    def record_action(
        cls,
        *,
        session: dict[str, Any],
        hand: dict[str, Any],
        seat_number: int,
        action_type: str,
        amount: int | None = None,
        mode: str | None = None,
        reasoning: str | None = None,
        confidence: int | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]:
        """Record an action in the current hand, evaluating Hero decisions when applicable."""
        if hand.get("is_settled"):
            raise ValueError("Cannot perform action on a hand that has already been settled.")

        active_mode = (mode or session.get("default_mode", "DECISION_CHECK")).upper()
        participants = session.get("participants", [])
        actor_p = next((p for p in participants if p["seat_number"] == seat_number), None)
        is_hero = actor_p.get("is_hero", False) if actor_p else False

        # Current state before action
        actions = list(hand.get("actions", []))
        board = list(hand.get("board", []))

        # Reconstruct before this action
        domain_cfg = _build_domain_config(
            session.get("configuration", {}), session.get("format_type", "CASH")
        )
        seat_configs = [
            TableSeatConfig(
                seat_number=p["seat_number"],
                player_id=p.get("player_id", f"p_{p['seat_number']}"),
                player_name=p["player_name"],
                stack=hand["starting_stacks"].get(str(p["seat_number"]), p["current_stack"]),
                is_hero=p.get("is_hero", False),
                is_sitting_out=p.get("is_sitting_out", False),
                hole_cards=tuple(hand["hole_cards"].get(str(p["seat_number"]), [])),
            )
            for p in participants
            if p.get("is_active", True)
        ]

        recon = LiveHelperEngine.reconstruct_table(
            config=domain_cfg,
            button_seat=hand["button_seat"],
            seat_configs=seat_configs,
            actions=actions,
            board_cards=board,
        )

        current_street = recon["street"]

        # Validate legal action
        legal_actions = recon.get("legal_actions", [])
        legal_kinds = [la["kind"].lower() for la in legal_actions]
        requested_type = action_type.lower()
        if requested_type == "raise" and "bet" in legal_kinds and "raise" not in legal_kinds:
            requested_type = "bet"
        elif requested_type == "bet" and "raise" in legal_kinds and "bet" not in legal_kinds:
            requested_type = "raise"

        if requested_type not in legal_kinds:
            raise ValueError(
                f"Action '{action_type}' is not legal for Seat {seat_number}. Legal actions: {legal_kinds}"
            )

        # If Hero is acting, evaluate decision
        decision_record: dict[str, Any] | None = None
        if is_hero:
            h_mode = HelperMode.COACH if active_mode == "COACH" else HelperMode.DECISION_CHECK
            eval_resp = LiveHelperEngine.evaluate_decision(
                config=domain_cfg,
                table_state=recon,
                chosen_action=requested_type,
                chosen_amount=amount,
                mode=h_mode,
                user_reasoning=reasoning or "",
                confidence_score=confidence or 3,
            )
            is_assisted = active_mode == "COACH"

            current_pos = recon["geometry"].get_position(seat_number) or "BTN"
            hero_seat_obj = next((s for s in recon["seats"] if s.seat_number == seat_number), None)
            actor_bet = hero_seat_obj.round_bet if hero_seat_obj else 0
            high_bet = recon.get("current_round_high_bet", 0)
            to_call = max(0, high_bet - actor_bet)

            decision_record = {
                "id": str(uuid.uuid4()),
                "session_id": session["id"],
                "hand_id": hand["id"],
                "decision_index": len(hand.get("decisions", [])) + 1,
                "street": current_street,
                "position": current_pos,
                "hero_cards": hand["hole_cards"].get(str(seat_number), []),
                "board": board,
                "stack_depth": recon.get("effective_stack", 0),
                "pot_size": recon.get("total_pot", 0),
                "amount_to_call": to_call,
                "action_history": recon.get("action_history", []),
                "chosen_action": requested_type,
                "chosen_amount": amount,
                "mode": active_mode,
                "user_confidence": confidence or 3,
                "user_reasoning": reasoning or "",
                "is_assisted": is_assisted,
                "evaluation_verdicts": eval_resp.to_dict(),
                "ev_regret": eval_resp.strategy.ev_regret,
                "created_at": datetime.now(UTC).isoformat(),
            }

        # Append new action to actions list
        actions.append(
            {
                "action_id": str(uuid.uuid4()),
                "seat_number": seat_number,
                "action_type": requested_type,
                "amount": amount or 0,
                "street": current_street,
                "descriptor": requested_type.replace("_", " ").title(),
            }
        )

        # Reconstruct post action
        post_recon = LiveHelperEngine.reconstruct_table(
            config=domain_cfg,
            button_seat=hand["button_seat"],
            seat_configs=seat_configs,
            actions=actions,
            board_cards=board,
        )

        hand["actions"] = actions
        hand["street"] = post_recon["street"]
        hand["pots"] = {
            "total_pot": post_recon["total_pot"],
            "main_pot": post_recon["pots"][0]["amount"]
            if post_recon["pots"]
            else post_recon["total_pot"],
            "side_pots": post_recon["pots"][1:] if len(post_recon["pots"]) > 1 else [],
        }

        # Check if hand naturally reached completion or showdown
        unfolded_seats = [
            s for s in post_recon["seats"] if not s.is_folded and not s.is_sitting_out
        ]
        is_terminal = (len(unfolded_seats) <= 1) or (post_recon["street"] == "showdown")
        if is_terminal:
            session, hand = cls.settle_hand(session=session, hand=hand)

        return session, hand, decision_record

    @classmethod
    def deal_community_cards(
        cls,
        *,
        session: dict[str, Any],
        hand: dict[str, Any],
        cards: list[str] | None = None,
        auto_deal: bool = False,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Deal community cards to the board (flop, turn, river) and advance street."""
        if hand.get("is_settled"):
            raise ValueError("Cannot deal cards to a hand that has already been settled.")

        current_board = list(hand.get("board", []))
        if len(current_board) >= 5:
            raise ValueError("Board already contains maximum 5 community cards.")

        # Determine how many cards are needed
        if len(current_board) == 0:
            needed_count = 3  # Flop
        elif len(current_board) == 3:
            needed_count = 1  # Turn
        elif len(current_board) == 4:
            needed_count = 1  # River
        else:
            needed_count = 1

        to_add: list[str] = []
        if cards and len(cards) > 0:
            to_add = [c.strip() for c in cards if c and c.strip()]
        elif auto_deal or not cards:
            all_ranks = "23456789TJQKA"
            all_suits = "shdc"
            full_deck = [f"{r}{s}" for r in all_ranks for s in all_suits]
            used_cards = set(current_board)
            for h_cards in hand.get("hole_cards", {}).values():
                used_cards.update(h_cards)
            available = [c for c in full_deck if c not in used_cards]
            import random

            if len(available) < needed_count:
                raise ValueError("Not enough cards remaining in deck.")
            to_add = random.sample(available, needed_count)

        # Validate cards
        used = set(current_board)
        for h_cards in hand.get("hole_cards", {}).values():
            used.update(h_cards)
        for c in to_add:
            if c in used:
                raise ValueError(f"Card '{c}' is already in play.")
            used.add(c)

        new_board = current_board + to_add
        hand["board"] = new_board

        # Reconstruct table with new board
        domain_cfg = _build_domain_config(
            session.get("configuration", {}), session.get("format_type", "CASH")
        )
        participants = session.get("participants", [])
        seat_configs = [
            TableSeatConfig(
                seat_number=p["seat_number"],
                player_id=p.get("player_id", f"p_{p['seat_number']}"),
                player_name=p["player_name"],
                stack=hand["starting_stacks"].get(str(p["seat_number"]), p["current_stack"]),
                is_hero=p.get("is_hero", False),
                is_sitting_out=p.get("is_sitting_out", False),
                hole_cards=tuple(hand["hole_cards"].get(str(p["seat_number"]), [])),
            )
            for p in participants
            if p.get("is_active", True)
        ]

        post_recon = LiveHelperEngine.reconstruct_table(
            config=domain_cfg,
            button_seat=hand["button_seat"],
            seat_configs=seat_configs,
            actions=hand.get("actions", []),
            board_cards=new_board,
        )

        hand["street"] = post_recon["street"]
        hand["pots"] = {
            "total_pot": post_recon["total_pot"],
            "main_pot": post_recon["pots"][0]["amount"]
            if post_recon["pots"]
            else post_recon["total_pot"],
            "side_pots": post_recon["pots"][1:] if len(post_recon["pots"]) > 1 else [],
        }

        # Check if showdown reached
        unfolded_seats = [
            s for s in post_recon["seats"] if not s.is_folded and not s.is_sitting_out
        ]
        is_terminal = (len(unfolded_seats) <= 1) or (post_recon["street"] == "showdown")
        if is_terminal:
            session, hand = cls.settle_hand(session=session, hand=hand)

        return session, hand

    @classmethod
    def reveal_opponent_cards(
        cls,
        *,
        session: dict[str, Any],
        hand: dict[str, Any],
        seat_number: int,
        hole_cards: list[str],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Set or reveal hole cards for any seat (e.g. at showdown)."""
        hand_holes = dict(hand.get("hole_cards", {}))
        hand_holes[str(seat_number)] = hole_cards
        hand["hole_cards"] = hand_holes

        # If hand reached showdown or is already settled, attempt settlement with revealed showdown cards!
        if hand.get("street") in ["showdown", "complete"] or hand.get("is_settled"):
            session, hand = cls.settle_hand(
                session=session, hand=hand, is_resettle=bool(hand.get("is_settled"))
            )

        return session, hand

    @classmethod
    def settle_hand(
        cls,
        *,
        session: dict[str, Any],
        hand: dict[str, Any],
        is_resettle: bool = False,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Idempotently settle the hand if not already settled."""
        if hand.get("is_settled") and not is_resettle:
            return session, hand

        already_settled = bool(hand.get("is_settled"))

        # Map to engine seats
        participants = session.get("participants", [])
        engine_seats: list[dict[str, Any]] = []
        for p in participants:
            s_num = p["seat_number"]
            start_st = hand["starting_stacks"].get(str(s_num), p["current_stack"])
            cards = hand["hole_cards"].get(str(s_num), [])
            engine_seats.append(
                {
                    "seat_number": s_num,
                    "player_name": p["player_name"],
                    "stack": start_st,
                    "starting_stack": start_st,
                    "is_hero": p.get("is_hero", False),
                    "is_active": p.get("is_active", True),
                    "hole_cards": cards,
                }
            )

        settlement_res = HandSettlementEngine.settle_hand(
            button_seat=hand["button_seat"],
            table_capacity=session["table_capacity"],
            seats=engine_seats,
            board_cards=hand.get("board", []),
            actions=hand.get("actions", []),
            pots_payload=hand.get("pots", {}),
            is_cash=session["format_type"] == "CASH",
            rake_percent=session.get("configuration", {})
            .get("cash_rules", {})
            .get("rake_percent", 0.0),
            rake_cap=session.get("configuration", {}).get("cash_rules", {}).get("rake_cap", 0),
            no_flop_no_drop=session.get("configuration", {})
            .get("cash_rules", {})
            .get("no_flop_no_drop", True),
        )

        pots_settled_dicts = [
            {
                "pot_name": p.pot_name,
                "amount": p.amount,
                "eligible_seats": p.eligible_seats,
                "winning_seats": p.winning_seats,
                "payout_per_winner": p.payout_per_winner,
                "odd_chips_awarded": p.odd_chips_awarded,
            }
            for p in settlement_res.pots_settled
        ]

        if not settlement_res.is_settled:
            hand["settlement"] = {
                "is_settled": False,
                "requires_card_reveal": True,
                "missing_card_seats": settlement_res.missing_card_seats,
                "is_showdown": settlement_res.is_showdown,
                "winning_seats": [],
                "pots_settled": [],
                "uncalled_returns": settlement_res.uncalled_returns,
                "rake_collected": 0,
                "net_chips": {str(k): v for k, v in settlement_res.net_chips.items()},
                "ending_stacks": None,
                "hand_descriptions": {
                    str(k): v for k, v in settlement_res.hand_descriptions.items()
                },
                "settlement_summary": settlement_res.settlement_summary,
            }
            hand["ending_stacks"] = None
            hand["is_settled"] = False
            hand["street"] = "showdown"
            return session, hand

        hand["settlement"] = {
            "is_settled": True,
            "requires_card_reveal": False,
            "missing_card_seats": [],
            "is_showdown": settlement_res.is_showdown,
            "winning_seats": settlement_res.winning_seats,
            "pots_settled": pots_settled_dicts,
            "uncalled_returns": settlement_res.uncalled_returns,
            "rake_collected": settlement_res.rake_collected,
            "net_chips": {str(k): v for k, v in settlement_res.net_chips.items()},
            "ending_stacks": {str(k): v for k, v in settlement_res.ending_stacks.items()},
            "hand_descriptions": {str(k): v for k, v in settlement_res.hand_descriptions.items()},
            "settlement_summary": settlement_res.settlement_summary,
        }
        hand["ending_stacks"] = {str(k): v for k, v in settlement_res.ending_stacks.items()}
        hand["is_settled"] = True
        hand["street"] = "complete"
        hand["settled_at"] = datetime.now(UTC).isoformat()

        # Update participant stacks
        for p in session["participants"]:
            s_num = int(p["seat_number"])
            if s_num in settlement_res.ending_stacks:
                p["current_stack"] = settlement_res.ending_stacks[s_num]
            elif str(s_num) in settlement_res.ending_stacks:
                p["current_stack"] = settlement_res.ending_stacks[str(s_num)]

        if not already_settled and not is_resettle:
            session["total_hands_completed"] = session.get("total_hands_completed", 0) + 1
        return session, hand

    @classmethod
    def advance_to_next_hand(
        cls,
        *,
        session: dict[str, Any],
        previous_hand: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Advance session to the next hand with stack continuity and clockwise button progression."""
        # 1. Enforce that previous hand is settled or natural terminal
        if not previous_hand.get("is_settled"):
            participants = session.get("participants", [])
            occupied = [
                p["seat_number"]
                for p in participants
                if p.get("is_active", True) and not p.get("is_sitting_out", False)
            ]
            actions = previous_hand.get("actions", [])
            folded_seats = {
                a["seat_number"] for a in actions if str(a.get("action_type", "")).lower() == "fold"
            }
            live_seats = [s for s in occupied if s not in folded_seats]

            # If all folded except one, or hand is at showdown/complete, attempt settle
            if len(live_seats) <= 1 or previous_hand.get("street") in ["showdown", "complete"]:
                session, previous_hand = cls.settle_hand(session=session, hand=previous_hand)
                if not previous_hand.get("is_settled"):
                    summary = previous_hand.get("settlement", {}).get("settlement_summary")
                    raise ValueError(
                        summary
                        or "Cannot advance to next hand: Showdown settlement is unresolved. Please reveal hole cards for remaining contenders before advancing."
                    )
            else:
                raise ValueError(
                    "Cannot advance to next hand: current hand has unresolved actions. Complete or settle the hand before advancing."
                )

        # 1b. Sync participant stacks from previous hand ending_stacks if available
        if previous_hand.get("ending_stacks"):
            end_st = previous_hand["ending_stacks"]
            for p in session["participants"]:
                s_key = p["seat_number"]
                if s_key in end_st:
                    p["current_stack"] = end_st[s_key]
                elif str(s_key) in end_st:
                    p["current_stack"] = end_st[str(s_key)]

        # 2. Check tournament eliminations
        is_tournament = session.get("format_type") == "TOURNAMENT"
        for p in session["participants"]:
            if is_tournament and p["current_stack"] <= 0:
                p["is_active"] = False
                p["is_eliminated"] = True

        # 3. Rotate button clockwise to next active participant
        active_seats = sorted([p["seat_number"] for p in session["participants"] if p["is_active"]])
        if len(active_seats) < 2:
            raise ValueError("Cannot start next hand: fewer than 2 active participants remain.")

        current_button = previous_hand["button_seat"]
        # Find next seat in clockwise circle
        next_button = active_seats[0]
        for s in active_seats:
            if s > current_button:
                next_button = s
                break

        new_hand_index = previous_hand["hand_index"] + 1
        new_hand_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        # 4. Check tournament blind progression
        config = dict(session["configuration"])
        if is_tournament and new_hand_index % 10 == 0:
            # Automatic blind increase every 10 hands
            config["small_blind"] = int(config.get("small_blind", 100) * 1.5)
            config["big_blind"] = int(config.get("big_blind", 200) * 1.5)
            config["ante"] = int(config.get("ante", 0) * 1.5)

        # 5. Create new hand record
        new_hand = cls._create_hand_record(
            session_id=session["id"],
            hand_id=new_hand_id,
            hand_index=new_hand_index,
            button_seat=next_button,
            configuration=config,
            participants=session["participants"],
            now=now,
        )

        session["current_hand_id"] = new_hand_id
        session["current_hand_index"] = new_hand_index
        session["updated_at"] = now.isoformat()

        return session, new_hand

    @classmethod
    def adjust_participant_stack(
        cls,
        *,
        session: dict[str, Any],
        seat_number: int,
        adjustment_type: str,
        amount: int,
    ) -> dict[str, Any]:
        """Adjust a participant's stack (buy-in, rebuy, top-up, cash-out, elimination)."""
        adj = adjustment_type.upper()
        participants = session.get("participants", [])
        p = next((x for x in participants if x["seat_number"] == seat_number), None)
        if not p:
            raise ValueError(f"Seat {seat_number} not found in session.")

        if adj in ("TOP_UP", "REBUY", "BUY_IN"):
            p["current_stack"] += amount
            p["rebuys"] = p.get("rebuys", 0) + amount
            p["is_active"] = True
        elif adj == "CASH_OUT":
            if amount > p["current_stack"]:
                raise ValueError(
                    f"Cannot cash out {amount}: current stack is only {p['current_stack']}."
                )
            p["current_stack"] -= amount
            p["cash_outs"] = p.get("cash_outs", 0) + amount
            if p["current_stack"] == 0:
                p["is_active"] = False
        elif adj == "ELIMINATE":
            p["current_stack"] = 0
            p["is_active"] = False
            p["is_eliminated"] = True
        elif adj == "SIT_OUT":
            p["is_sitting_out"] = True
        elif adj == "RETURN":
            p["is_sitting_out"] = False
        else:
            raise ValueError(f"Unknown adjustment type: {adjustment_type}")

        session["updated_at"] = datetime.now(UTC).isoformat()
        return session
