"""Authoritative 20 Quick Scenario Templates for Live Helper Laboratory.

Provides mathematically consistent starting scenarios across Cash, Multiway,
Postflop, and Tournament (ICM & PKO) structures.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.live_helper.models import (
    CashRuleConfig,
    FormatType,
    LiveHelperGameConfig,
    SpecificGameFormat,
    TournamentRuleConfig,
)
from app.domain.poker.seat_geometry import TableSeatConfig


@dataclass(frozen=True)
class QuickTemplate:
    """Pre-configured legal poker scenario template."""

    id: str
    title: str
    category: str  # PREFLOP_RFI, PREFLOP_DEFENSE, PREFLOP_AGGRESSION, POSTFLOP, TOURNAMENT
    summary: str
    config: LiveHelperGameConfig
    button_seat: int
    seats: list[TableSeatConfig]
    street: str
    board: list[str]
    actions: list[dict[str, Any]]
    hero_seat: int
    hero_cards: tuple[str, str]
    learning_notes: str

    def to_dict(self) -> dict[str, Any]:
        cfg_dict = self.config.to_dict()
        return {
            "id": self.id,
            "template_id": self.id,
            "title": self.title,
            "category": self.category,
            "summary": self.summary,
            "description": self.summary,
            "config": cfg_dict,
            "configuration": cfg_dict,
            "button_seat": self.button_seat,
            "seats": [
                {
                    "seat_number": s.seat_number,
                    "player_id": s.player_id,
                    "player_name": s.player_name,
                    "stack": s.stack,
                    "is_hero": s.is_hero,
                    "is_sitting_out": s.is_sitting_out,
                    "hole_cards": list(s.hole_cards),
                }
                for s in self.seats
            ],
            "street": self.street,
            "board": self.board,
            "actions": self.actions,
            "hero_seat": self.hero_seat,
            "hero_cards": list(self.hero_cards),
            "learning_notes": self.learning_notes,
            "suggested_action": self.actions[-1]["action_type"] if self.actions else "FOLD",
            "tags": [self.config.format_type.value.lower(), self.category.lower()],
        }


# Base cash configuration: 100/200 blinds (1bb = 200, 100bb = 20,000 chips)
CASH_6MAX_CONFIG = LiveHelperGameConfig(
    format_type=FormatType.CASH,
    specific_format=SpecificGameFormat.ONLINE_6MAX,
    max_capacity=6,
    small_blind=100,
    big_blind=200,
    ante=0,
    cash_rules=CashRuleConfig(rake_percent=5.0, rake_cap=600, no_flop_no_drop=True),
)

# Base tournament config: 8-max with BBA (500/1000, 1000 BBA)
TOURNAMENT_MTT_CONFIG = LiveHelperGameConfig(
    format_type=FormatType.TOURNAMENT,
    specific_format=SpecificGameFormat.STANDARD_MTT,
    max_capacity=8,
    small_blind=500,
    big_blind=1000,
    ante=1000,
    ante_type="BBA",
    tournament_rules=TournamentRuleConfig(
        buy_in=100.0,
        total_entrants=100,
        players_remaining=18,
        paid_positions=15,
        payout_ladder=[2500.0, 1600.0, 1100.0, 800.0, 600.0, 450.0, 350.0, 250.0, 200.0],
    ),
)


def _make_6max_cash_seats(hero_seat: int, hero_cards: tuple[str, str]) -> list[TableSeatConfig]:
    names = ["Alice", "Bob", "Charlie", "David", "Emma", "Frank"]
    seats = []
    for i in range(1, 7):
        is_h = i == hero_seat
        seats.append(
            TableSeatConfig(
                seat_number=i,
                player_id=f"p_{i}",
                player_name="Hero" if is_h else names[i - 1],
                stack=20000,  # 100bb
                is_hero=is_h,
                hole_cards=hero_cards if is_h else (),
            )
        )
    return seats


ALL_QUICK_TEMPLATES: list[QuickTemplate] = [
    # 1. Unopened RFI
    QuickTemplate(
        id="template_unopened_rfi_btn",
        title="Unopened Pot (BTN RFI)",
        category="PREFLOP_RFI",
        summary="Action folded to Hero on the Button in 6-max 100bb Cash.",
        config=CASH_6MAX_CONFIG,
        button_seat=5,  # Hero is BTN (seat 5)
        seats=_make_6max_cash_seats(hero_seat=5, hero_cards=("Ah", "Ts")),
        street="preflop",
        board=[],
        actions=[
            {"seat_number": 6, "action_type": "post_sb", "amount": 100},  # SB
            {"seat_number": 1, "action_type": "post_bb", "amount": 200},  # BB
            {"seat_number": 2, "action_type": "fold", "amount": 0},  # UTG
            {"seat_number": 3, "action_type": "fold", "amount": 0},  # MP/HJ
            {"seat_number": 4, "action_type": "fold", "amount": 0},  # CO
        ],
        hero_seat=5,
        hero_cards=("Ah", "Ts"),
        learning_notes="Button opens approximately 40-43% of hands with 2.5bb sizing in 6-max 100bb cash.",
    ),
    # 2. Facing an open (BB vs BTN)
    QuickTemplate(
        id="template_facing_open_bb_btn",
        title="Facing Open: BB vs BTN",
        category="PREFLOP_DEFENSE",
        summary="BTN opens 2.5bb (500 chips). SB folds. Hero defends Big Blind.",
        config=CASH_6MAX_CONFIG,
        button_seat=5,
        seats=_make_6max_cash_seats(hero_seat=1, hero_cards=("Kd", "Jc")),  # Hero is BB (seat 1)
        street="preflop",
        board=[],
        actions=[
            {"seat_number": 6, "action_type": "post_sb", "amount": 100},
            {"seat_number": 1, "action_type": "post_bb", "amount": 200},
            {"seat_number": 2, "action_type": "fold", "amount": 0},
            {"seat_number": 3, "action_type": "fold", "amount": 0},
            {"seat_number": 4, "action_type": "fold", "amount": 0},
            {"seat_number": 5, "action_type": "raise", "amount": 500},
            {"seat_number": 6, "action_type": "fold", "amount": 0},
        ],
        hero_seat=1,
        hero_cards=("Kd", "Jc"),
        learning_notes="BB defends roughly 45-50% vs BTN 2.5bb open, dividing into calls and 3-bets.",
    ),
    # 3. BB versus BTN (Suited Connector 3-Bet / Call Spot)
    QuickTemplate(
        id="template_bb_vs_btn_suited_connector",
        title="BB vs BTN: Suited Connector",
        category="PREFLOP_DEFENSE",
        summary="BTN opens 2.5bb. Hero holds 8s 7s in the Big Blind.",
        config=CASH_6MAX_CONFIG,
        button_seat=5,
        seats=_make_6max_cash_seats(hero_seat=1, hero_cards=("8s", "7s")),
        street="preflop",
        board=[],
        actions=[
            {"seat_number": 6, "action_type": "post_sb", "amount": 100},
            {"seat_number": 1, "action_type": "post_bb", "amount": 200},
            {"seat_number": 2, "action_type": "fold", "amount": 0},
            {"seat_number": 3, "action_type": "fold", "amount": 0},
            {"seat_number": 4, "action_type": "fold", "amount": 0},
            {"seat_number": 5, "action_type": "raise", "amount": 500},
            {"seat_number": 6, "action_type": "fold", "amount": 0},
        ],
        hero_seat=1,
        hero_cards=("8s", "7s"),
        learning_notes="Medium suited connectors play well as flat calls or mixed polar 3-bets.",
    ),
    # 4. BB versus CO
    QuickTemplate(
        id="template_bb_vs_co_open",
        title="BB vs Cutoff Open",
        category="PREFLOP_DEFENSE",
        summary="CO opens to 2.5bb (500). BTN and SB fold. Hero defends BB.",
        config=CASH_6MAX_CONFIG,
        button_seat=5,
        seats=_make_6max_cash_seats(hero_seat=1, hero_cards=("Ad", "8h")),
        street="preflop",
        board=[],
        actions=[
            {"seat_number": 6, "action_type": "post_sb", "amount": 100},
            {"seat_number": 1, "action_type": "post_bb", "amount": 200},
            {"seat_number": 2, "action_type": "fold", "amount": 0},
            {"seat_number": 3, "action_type": "fold", "amount": 0},
            {"seat_number": 4, "action_type": "raise", "amount": 500},
            {"seat_number": 5, "action_type": "fold", "amount": 0},
            {"seat_number": 6, "action_type": "fold", "amount": 0},
        ],
        hero_seat=1,
        hero_cards=("Ad", "8h"),
        learning_notes="Tighter defense range vs CO compared to BTN due to CO's tighter 25-27% opening range.",
    ),
    # 5. SB versus BTN
    QuickTemplate(
        id="template_sb_vs_btn_open",
        title="SB vs BTN Open: 3-Bet or Fold",
        category="PREFLOP_DEFENSE",
        summary="BTN opens 2.5bb. Hero in SB faces wide BTN opening range with 100bb stacks.",
        config=CASH_6MAX_CONFIG,
        button_seat=5,
        seats=_make_6max_cash_seats(hero_seat=6, hero_cards=("As", "Jd")),
        street="preflop",
        board=[],
        actions=[
            {"seat_number": 6, "action_type": "post_sb", "amount": 100},
            {"seat_number": 1, "action_type": "post_bb", "amount": 200},
            {"seat_number": 2, "action_type": "fold", "amount": 0},
            {"seat_number": 3, "action_type": "fold", "amount": 0},
            {"seat_number": 4, "action_type": "fold", "amount": 0},
            {"seat_number": 5, "action_type": "raise", "amount": 500},
        ],
        hero_seat=6,
        hero_cards=("As", "Jd"),
        learning_notes="In modern raked cash games, SB predominantly 3-bets or folds rather than flat calling.",
    ),
    # 6. Facing 3-bet
    QuickTemplate(
        id="template_facing_3bet_co_vs_btn",
        title="Facing 3-Bet: CO vs BTN",
        category="PREFLOP_AGGRESSION",
        summary="Hero opens CO to 2.5bb (500). BTN 3-bets to 7.5bb (1500). Blinds fold.",
        config=CASH_6MAX_CONFIG,
        button_seat=5,
        seats=_make_6max_cash_seats(hero_seat=4, hero_cards=("Qs", "Qh")),
        street="preflop",
        board=[],
        actions=[
            {"seat_number": 6, "action_type": "post_sb", "amount": 100},
            {"seat_number": 1, "action_type": "post_bb", "amount": 200},
            {"seat_number": 2, "action_type": "fold", "amount": 0},
            {"seat_number": 3, "action_type": "fold", "amount": 0},
            {"seat_number": 4, "action_type": "raise", "amount": 500},
            {"seat_number": 5, "action_type": "raise", "amount": 1500},
            {"seat_number": 6, "action_type": "fold", "amount": 0},
            {"seat_number": 1, "action_type": "fold", "amount": 0},
        ],
        hero_seat=4,
        hero_cards=("Qs", "Qh"),
        learning_notes="Hero can 4-bet for value or call to keep dominated bluffs in range out of position.",
    ),
    # 7. Facing 4-bet
    QuickTemplate(
        id="template_facing_4bet_sb_vs_btn",
        title="Facing 4-Bet: SB vs BTN",
        category="PREFLOP_AGGRESSION",
        summary="Hero 3-bet from SB to 2000. BTN 4-bets to 4600. Hero holds Ak.",
        config=CASH_6MAX_CONFIG,
        button_seat=5,
        seats=_make_6max_cash_seats(hero_seat=6, hero_cards=("Ah", "Kh")),
        street="preflop",
        board=[],
        actions=[
            {"seat_number": 6, "action_type": "post_sb", "amount": 100},
            {"seat_number": 1, "action_type": "post_bb", "amount": 200},
            {"seat_number": 2, "action_type": "fold", "amount": 0},
            {"seat_number": 3, "action_type": "fold", "amount": 0},
            {"seat_number": 4, "action_type": "fold", "amount": 0},
            {"seat_number": 5, "action_type": "raise", "amount": 500},
            {"seat_number": 6, "action_type": "raise", "amount": 2000},
            {"seat_number": 1, "action_type": "fold", "amount": 0},
            {"seat_number": 5, "action_type": "raise", "amount": 4600},
        ],
        hero_seat=6,
        hero_cards=("Ah", "Kh"),
        learning_notes="AKs is a standard 5-bet shove candidate at 100bb depth with high blocker value.",
    ),
    # 8. Cold 4-bet
    QuickTemplate(
        id="template_cold_4bet_spot",
        title="Cold 4-Bet Opportunity: BTN",
        category="PREFLOP_AGGRESSION",
        summary="UTG opens 500, CO 3-bets to 1600. Hero on Button holds strong candidate.",
        config=CASH_6MAX_CONFIG,
        button_seat=5,
        seats=_make_6max_cash_seats(hero_seat=5, hero_cards=("As", "Kd")),
        street="preflop",
        board=[],
        actions=[
            {"seat_number": 6, "action_type": "post_sb", "amount": 100},
            {"seat_number": 1, "action_type": "post_bb", "amount": 200},
            {"seat_number": 2, "action_type": "raise", "amount": 500},
            {"seat_number": 3, "action_type": "fold", "amount": 0},
            {"seat_number": 4, "action_type": "raise", "amount": 1600},
        ],
        hero_seat=5,
        hero_cards=("As", "Kd"),
        learning_notes="Cold 4-betting demands very strong value or elite blockers (e.g. A5s, AKo).",
    ),
    # 9. Squeeze opportunity
    QuickTemplate(
        id="template_squeeze_opportunity_bb",
        title="Squeeze Opportunity in BB",
        category="PREFLOP_AGGRESSION",
        summary="CO opens to 500, BTN flat calls. Hero in BB has large dead money pot.",
        config=CASH_6MAX_CONFIG,
        button_seat=5,
        seats=_make_6max_cash_seats(hero_seat=1, hero_cards=("Ac", "5c")),
        street="preflop",
        board=[],
        actions=[
            {"seat_number": 6, "action_type": "post_sb", "amount": 100},
            {"seat_number": 1, "action_type": "post_bb", "amount": 200},
            {"seat_number": 2, "action_type": "fold", "amount": 0},
            {"seat_number": 3, "action_type": "fold", "amount": 0},
            {"seat_number": 4, "action_type": "raise", "amount": 500},
            {"seat_number": 5, "action_type": "call", "amount": 500},
            {"seat_number": 6, "action_type": "fold", "amount": 0},
        ],
        hero_seat=1,
        hero_cards=("Ac", "5c"),
        learning_notes="Squeeze sizing should be generous (4.5x - 5x) when out of position to deny equity.",
    ),
    # 10. UTG all-in
    QuickTemplate(
        id="template_utg_short_shove",
        title="Facing UTG Short All-In (15bb)",
        category="PREFLOP_AGGRESSION",
        summary="UTG shoves 15bb (3000 chips). Action folds to Hero in Big Blind.",
        config=CASH_6MAX_CONFIG,
        button_seat=5,
        seats=_make_6max_cash_seats(hero_seat=1, hero_cards=("Ts", "Td")),
        street="preflop",
        board=[],
        actions=[
            {"seat_number": 6, "action_type": "post_sb", "amount": 100},
            {"seat_number": 1, "action_type": "post_bb", "amount": 200},
            {"seat_number": 2, "action_type": "all_in", "amount": 3000},
            {"seat_number": 3, "action_type": "fold", "amount": 0},
            {"seat_number": 4, "action_type": "fold", "amount": 0},
            {"seat_number": 5, "action_type": "fold", "amount": 0},
            {"seat_number": 6, "action_type": "fold", "amount": 0},
        ],
        hero_seat=1,
        hero_cards=("Ts", "Td"),
        learning_notes="Calculate direct pot odds: 2800 to call into 3300 pot (45.9% required equity).",
    ),
    # 11. Multiple all-ins before Hero
    QuickTemplate(
        id="template_multiple_all_ins_before_hero",
        title="Multiple All-Ins Ahead",
        category="PREFLOP_AGGRESSION",
        summary="CO shoves 2500, BTN shoves 4000. Hero in BB holds pocket Queens.",
        config=CASH_6MAX_CONFIG,
        button_seat=5,
        seats=_make_6max_cash_seats(hero_seat=1, hero_cards=("Qc", "Qd")),
        street="preflop",
        board=[],
        actions=[
            {"seat_number": 6, "action_type": "post_sb", "amount": 100},
            {"seat_number": 1, "action_type": "post_bb", "amount": 200},
            {"seat_number": 2, "action_type": "fold", "amount": 0},
            {"seat_number": 3, "action_type": "fold", "amount": 0},
            {"seat_number": 4, "action_type": "all_in", "amount": 2500},
            {"seat_number": 5, "action_type": "all_in", "amount": 4000},
            {"seat_number": 6, "action_type": "fold", "amount": 0},
        ],
        hero_seat=1,
        hero_cards=("Qc", "Qd"),
        learning_notes="Two all-ins indicate condensed ranges; QQ retains high equity vs combined shoving ranges.",
    ),
    # 12. Multiway flop
    QuickTemplate(
        id="template_multiway_flop_action",
        title="Multiway Flop (3 Players)",
        category="POSTFLOP",
        summary="BTN opens, SB and BB call. Flop Qs 9d 4c. Checked to BTN Hero.",
        config=CASH_6MAX_CONFIG,
        button_seat=5,
        seats=_make_6max_cash_seats(hero_seat=5, hero_cards=("Ac", "Qd")),
        street="flop",
        board=["Qs", "9d", "4c"],
        actions=[
            {"seat_number": 6, "action_type": "post_sb", "amount": 100},
            {"seat_number": 1, "action_type": "post_bb", "amount": 200},
            {"seat_number": 2, "action_type": "fold", "amount": 0},
            {"seat_number": 3, "action_type": "fold", "amount": 0},
            {"seat_number": 4, "action_type": "fold", "amount": 0},
            {"seat_number": 5, "action_type": "raise", "amount": 500},
            {"seat_number": 6, "action_type": "call", "amount": 500},
            {"seat_number": 1, "action_type": "call", "amount": 500},
            # Flop checks
            {"seat_number": 6, "action_type": "check", "amount": 0},
            {"seat_number": 1, "action_type": "check", "amount": 0},
        ],
        hero_seat=5,
        hero_cards=("Ac", "Qd"),
        learning_notes="Multiway betting requires higher threshold for value; lower bluffing frequency.",
    ),
    # 13. Flop C-bet (SRP BTN vs BB)
    QuickTemplate(
        id="template_flop_cbet_srp",
        title="Single-Raised Pot Flop C-Bet",
        category="POSTFLOP",
        summary="BTN opens, BB calls. Board Ks 7d 2c rainbow. BB checks to Hero.",
        config=CASH_6MAX_CONFIG,
        button_seat=5,
        seats=_make_6max_cash_seats(hero_seat=5, hero_cards=("Kc", "Qh")),
        street="flop",
        board=["Ks", "7d", "2c"],
        actions=[
            {"seat_number": 6, "action_type": "post_sb", "amount": 100},
            {"seat_number": 1, "action_type": "post_bb", "amount": 200},
            {"seat_number": 2, "action_type": "fold", "amount": 0},
            {"seat_number": 3, "action_type": "fold", "amount": 0},
            {"seat_number": 4, "action_type": "fold", "amount": 0},
            {"seat_number": 5, "action_type": "raise", "amount": 500},
            {"seat_number": 6, "action_type": "fold", "amount": 0},
            {"seat_number": 1, "action_type": "call", "amount": 500},
            {"seat_number": 1, "action_type": "check", "amount": 0},
        ],
        hero_seat=5,
        hero_cards=("Kc", "Qh"),
        learning_notes="Dry King-high rainbow board heavily favors BTN range advantage, warranting high C-bet frequency.",
    ),
    # 14. Flop check-raise
    QuickTemplate(
        id="template_flop_check_raise_bb",
        title="Flop Check-Raise Defense: BB",
        category="POSTFLOP",
        summary="BB calls BTN open. Flop Ts 8h 4d. BB checks, BTN bets 350. Hero decision.",
        config=CASH_6MAX_CONFIG,
        button_seat=5,
        seats=_make_6max_cash_seats(hero_seat=1, hero_cards=("9s", "7s")),
        street="flop",
        board=["Ts", "8h", "4d"],
        actions=[
            {"seat_number": 6, "action_type": "post_sb", "amount": 100},
            {"seat_number": 1, "action_type": "post_bb", "amount": 200},
            {"seat_number": 2, "action_type": "fold", "amount": 0},
            {"seat_number": 3, "action_type": "fold", "amount": 0},
            {"seat_number": 4, "action_type": "fold", "amount": 0},
            {"seat_number": 5, "action_type": "raise", "amount": 500},
            {"seat_number": 6, "action_type": "fold", "amount": 0},
            {"seat_number": 1, "action_type": "call", "amount": 500},
            {"seat_number": 1, "action_type": "check", "amount": 0},
            {"seat_number": 5, "action_type": "bet", "amount": 350},
        ],
        hero_seat=1,
        hero_cards=("9s", "7s"),
        learning_notes="Connected boards allow BB to check-raise dynamic semi-bluffs (open-ended straight draws).",
    ),
    # 15. Turn barrel
    QuickTemplate(
        id="template_turn_double_barrel",
        title="Turn Double Barrel: Blank Turn",
        category="POSTFLOP",
        summary="BTN C-bets Ks 7d 2c, BB calls. Turn Th. BB checks to BTN Hero.",
        config=CASH_6MAX_CONFIG,
        button_seat=5,
        seats=_make_6max_cash_seats(hero_seat=5, hero_cards=("Ah", "Kd")),
        street="turn",
        board=["Ks", "7d", "2c", "Th"],
        actions=[
            {"seat_number": 6, "action_type": "post_sb", "amount": 100},
            {"seat_number": 1, "action_type": "post_bb", "amount": 200},
            {"seat_number": 2, "action_type": "fold", "amount": 0},
            {"seat_number": 3, "action_type": "fold", "amount": 0},
            {"seat_number": 4, "action_type": "fold", "amount": 0},
            {"seat_number": 5, "action_type": "raise", "amount": 500},
            {"seat_number": 6, "action_type": "fold", "amount": 0},
            {"seat_number": 1, "action_type": "call", "amount": 500},
            # Flop
            {"seat_number": 1, "action_type": "check", "amount": 0},
            {"seat_number": 5, "action_type": "bet", "amount": 350},
            {"seat_number": 1, "action_type": "call", "amount": 350},
            # Turn
            {"seat_number": 1, "action_type": "check", "amount": 0},
        ],
        hero_seat=5,
        hero_cards=("Ah", "Kd"),
        learning_notes="Top pair top kicker continues barreling for value and charge gutshots / second pairs.",
    ),
    # 16. River bluff catch
    QuickTemplate(
        id="template_river_bluff_catch",
        title="River Bluff Catch (Polarized Bet)",
        category="POSTFLOP",
        summary="Board Ah Kd 2c 7s 9c. Villain bets 75% pot on river. Hero holds King-Queen.",
        config=CASH_6MAX_CONFIG,
        button_seat=5,
        seats=_make_6max_cash_seats(hero_seat=1, hero_cards=("Kh", "Qh")),
        street="river",
        board=["Ah", "Kd", "2c", "7s", "9c"],
        actions=[
            {"seat_number": 6, "action_type": "post_sb", "amount": 100},
            {"seat_number": 1, "action_type": "post_bb", "amount": 200},
            {"seat_number": 2, "action_type": "fold", "amount": 0},
            {"seat_number": 3, "action_type": "fold", "amount": 0},
            {"seat_number": 4, "action_type": "fold", "amount": 0},
            {"seat_number": 5, "action_type": "raise", "amount": 500},
            {"seat_number": 6, "action_type": "fold", "amount": 0},
            {"seat_number": 1, "action_type": "call", "amount": 500},
            # Flop
            {"seat_number": 1, "action_type": "check", "amount": 0},
            {"seat_number": 5, "action_type": "bet", "amount": 350},
            {"seat_number": 1, "action_type": "call", "amount": 350},
            # Turn
            {"seat_number": 1, "action_type": "check", "amount": 0},
            {"seat_number": 5, "action_type": "check", "amount": 0},
            # River
            {"seat_number": 1, "action_type": "check", "amount": 0},
            {"seat_number": 5, "action_type": "bet", "amount": 1350},
        ],
        hero_seat=1,
        hero_cards=("Kh", "Qh"),
        learning_notes="MDF = 1800 / (1800 + 1350) = 57.1%. Second pair blocks broadway straights and unblocks missed flush draws.",
    ),
    # 17. Tournament shove
    QuickTemplate(
        id="template_tournament_sb_shove_12bb",
        title="Tournament Push/Fold: SB 12bb Shove",
        category="TOURNAMENT",
        summary="Folded to Hero in SB with 12bb in MTT. BB has 25bb.",
        config=TOURNAMENT_MTT_CONFIG,
        button_seat=5,
        seats=[
            TableSeatConfig(1, "p_1", "BB", 25000),
            TableSeatConfig(2, "p_2", "UTG", 30000),
            TableSeatConfig(3, "p_3", "UTG+1", 18000),
            TableSeatConfig(4, "p_4", "MP", 14000),
            TableSeatConfig(5, "p_5", "BTN", 22000),
            TableSeatConfig(6, "p_6", "Hero", 12000, is_hero=True, hole_cards=("Ks", "6s")),
        ],
        street="preflop",
        board=[],
        actions=[
            {"seat_number": 6, "action_type": "post_sb", "amount": 500},
            {"seat_number": 1, "action_type": "post_bb", "amount": 1000},
            {"seat_number": 1, "action_type": "post_ante", "amount": 1000},
            {"seat_number": 2, "action_type": "fold", "amount": 0},
            {"seat_number": 3, "action_type": "fold", "amount": 0},
            {"seat_number": 4, "action_type": "fold", "amount": 0},
            {"seat_number": 5, "action_type": "fold", "amount": 0},
        ],
        hero_seat=6,
        hero_cards=("Ks", "6s"),
        learning_notes="Nash equilibrium push/fold ranges widen to ~45-50% in blind vs blind at 12bb depth.",
    ),
    # 18. Tournament bubble
    QuickTemplate(
        id="template_tournament_bubble_icm",
        title="Tournament Direct Bubble (16 Left, 15 Paid)",
        category="TOURNAMENT",
        summary="Direct stone bubble. Big stack opens, medium stack Hero faces ICM pressure.",
        config=TOURNAMENT_MTT_CONFIG,
        button_seat=5,
        seats=[
            TableSeatConfig(1, "p_1", "BB_Short", 6000),  # Micro short stack (6bb)
            TableSeatConfig(2, "p_2", "UTG_Chipleader", 65000),  # Chip leader opens
            TableSeatConfig(3, "p_3", "MP", 25000),
            TableSeatConfig(4, "p_4", "CO", 28000),
            TableSeatConfig(5, "p_5", "BTN", 22000),
            TableSeatConfig(6, "p_6", "Hero", 20000, is_hero=True, hole_cards=("Ah", "Qd")),
        ],
        street="preflop",
        board=[],
        actions=[
            {"seat_number": 6, "action_type": "post_sb", "amount": 500},
            {"seat_number": 1, "action_type": "post_bb", "amount": 1000},
            {"seat_number": 1, "action_type": "post_ante", "amount": 1000},
            {"seat_number": 2, "action_type": "raise", "amount": 2200},
            {"seat_number": 3, "action_type": "fold", "amount": 0},
            {"seat_number": 4, "action_type": "fold", "amount": 0},
            {"seat_number": 5, "action_type": "fold", "amount": 0},
        ],
        hero_seat=6,
        hero_cards=("Ah", "Qd"),
        learning_notes="Bubble Factor exceeds 1.6 vs covering stack when short stacks are about to blind out.",
    ),
    # 19. Final table
    QuickTemplate(
        id="template_final_table_pay_jumps",
        title="Final Table Significant Pay Jump",
        category="TOURNAMENT",
        summary="6-handed FT. Steep payout ladder ($10k 1st, $6k 2nd, $4k 3rd). Hero in CO.",
        config=LiveHelperGameConfig(
            format_type=FormatType.TOURNAMENT,
            specific_format=SpecificGameFormat.FREEZEOUT,
            max_capacity=6,
            small_blind=1000,
            big_blind=2000,
            ante=2000,
            ante_type="BBA",
            tournament_rules=TournamentRuleConfig(
                buy_in=500.0,
                total_entrants=100,
                players_remaining=6,
                paid_positions=6,
                payout_ladder=[10000.0, 6000.0, 4000.0, 2800.0, 2000.0, 1500.0],
            ),
        ),
        button_seat=4,
        seats=[
            TableSeatConfig(1, "p_1", "BB", 15000),
            TableSeatConfig(2, "p_2", "UTG", 80000),
            TableSeatConfig(3, "p_3", "Hero", 45000, is_hero=True, hole_cards=("As", "Jc")),
            TableSeatConfig(4, "p_4", "BTN", 30000),
            TableSeatConfig(5, "p_5", "SB", 20000),
        ],
        street="preflop",
        board=[],
        actions=[
            {"seat_number": 5, "action_type": "post_sb", "amount": 1000},
            {"seat_number": 1, "action_type": "post_bb", "amount": 2000},
            {"seat_number": 1, "action_type": "post_ante", "amount": 2000},
            {"seat_number": 2, "action_type": "raise", "amount": 4200},
        ],
        hero_seat=3,
        hero_cards=("As", "Jc"),
        learning_notes="Extreme pay jumps demand risk aversion against chipleaders while short stacks remain.",
    ),
    # 20. PKO bounty decision
    QuickTemplate(
        id="template_pko_bounty_decision",
        title="PKO Bounty Call Decision",
        category="TOURNAMENT",
        summary="PKO MTT. Opponent shoves 8bb with $150 bounty. Hero in BB decides.",
        config=LiveHelperGameConfig(
            format_type=FormatType.TOURNAMENT,
            specific_format=SpecificGameFormat.PKO,
            max_capacity=6,
            small_blind=500,
            big_blind=1000,
            ante=1000,
            ante_type="BBA",
            tournament_rules=TournamentRuleConfig(
                buy_in=100.0,
                total_entrants=100,
                players_remaining=25,
                paid_positions=15,
                payout_ladder=[2000.0, 1200.0, 800.0, 500.0],
                bounty_values=[50.0, 150.0, 75.0, 50.0, 100.0, 50.0],
                is_pko=True,
            ),
        ),
        button_seat=5,
        seats=[
            TableSeatConfig(1, "p_1", "Hero", 40000, is_hero=True, hole_cards=("Qd", "9d")),
            TableSeatConfig(2, "p_2", "Short_Villain", 8000),
            TableSeatConfig(3, "p_3", "MP", 25000),
            TableSeatConfig(4, "p_4", "CO", 30000),
            TableSeatConfig(5, "p_5", "BTN", 20000),
            TableSeatConfig(6, "p_6", "SB", 15000),
        ],
        street="preflop",
        board=[],
        actions=[
            {"seat_number": 6, "action_type": "post_sb", "amount": 500},
            {"seat_number": 1, "action_type": "post_bb", "amount": 1000},
            {"seat_number": 1, "action_type": "post_ante", "amount": 1000},
            {"seat_number": 2, "action_type": "all_in", "amount": 8000},
            {"seat_number": 3, "action_type": "fold", "amount": 0},
            {"seat_number": 4, "action_type": "fold", "amount": 0},
            {"seat_number": 5, "action_type": "fold", "amount": 0},
            {"seat_number": 6, "action_type": "fold", "amount": 0},
        ],
        hero_seat=1,
        hero_cards=("Qd", "9d"),
        learning_notes="Bounties add effective chips to the pot, lowering required break-even equity by 5-10%.",
    ),
]


def get_template(template_id: str) -> QuickTemplate | None:
    for t in ALL_QUICK_TEMPLATES:
        if t.id == template_id:
            return t
    return None


def list_templates(category: str | None = None) -> list[QuickTemplate]:
    if category is None:
        return ALL_QUICK_TEMPLATES
    return [t for t in ALL_QUICK_TEMPLATES if t.category == category]
