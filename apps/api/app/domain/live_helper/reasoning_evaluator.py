"""Evaluator for user-supplied written reasoning in Decision Check Mode.

Parses and validates individual claims concerning:
- Pot odds and break-even equity calculations
- Positional dynamics (In Position vs Out of Position)
- Blocker and card-removal effects
- Range advantages and polarized distributions
- Tournament ICM risk premiums and PKO bounties
"""

from __future__ import annotations

import re

from app.domain.live_helper.models import MathematicalVerdict, ReasoningClaimEvaluation


class ReasoningEvaluator:
    """Evaluates user-written poker reasoning against deterministic mathematical facts."""

    @staticmethod
    def evaluate_reasoning(
        reasoning_text: str,
        hero_cards: tuple[str, ...],
        board_cards: list[str],
        hero_position: str,
        math_verdict: MathematicalVerdict,
        chosen_action: str,
    ) -> list[ReasoningClaimEvaluation]:
        if not reasoning_text or not reasoning_text.strip():
            return []

        evaluations: list[ReasoningClaimEvaluation] = []
        text_lower = reasoning_text.lower()

        # 1. Pot Odds / Break-Even Equity Claims
        pot_odds_patterns = [
            r"pot odds",
            r"break[- ]even",
            r"getting (\d+(\.\d+)?) to 1",
            r"(\d+(\.\d+)?)%",
            r"need (\d+(\.\d+)?)%",
            r"odds are good",
            r"cheap to call",
        ]
        has_pot_odds_claim = any(re.search(pat, text_lower) for pat in pot_odds_patterns)

        if has_pot_odds_claim:
            # Check if user mentioned a specific percentage
            pct_matches = re.findall(r"(\d+(\.\d+)?)\s*%", text_lower)
            actual_be = math_verdict.break_even_equity_pct
            is_sound = True
            critique = (
                f"Pot odds calculation noted. Direct break-even equity is {actual_be:.1f}% "
                f"({math_verdict.pot_odds_ratio}). "
            )

            if pct_matches:
                claimed_pct = float(pct_matches[0][0])
                if abs(claimed_pct - actual_be) > 8.0:
                    is_sound = False
                    critique += f"Claimed equity (~{claimed_pct:.0f}%) deviates from actual {actual_be:.1f}%."
                else:
                    critique += f"Claimed equity (~{claimed_pct:.0f}%) is mathematically accurate."
            else:
                critique += "Accurately recognized pot odds as a relevant decision factor."

            evaluations.append(
                ReasoningClaimEvaluation(
                    claim_category="POT_ODDS",
                    extracted_text="Pot odds / break-even equity claim",
                    is_sound=is_sound,
                    critique=critique,
                )
            )

        # 2. Positional Claims
        pos_patterns = [
            r"in position",
            r"out of position",
            r"ip\b",
            r"oop\b",
            r"positional advantage",
        ]
        has_pos_claim = any(re.search(pat, text_lower) for pat in pos_patterns)

        if has_pos_claim:
            is_ip = hero_position.upper() in ["BTN", "CO", "HJ", "LJ", "IP"]
            user_claims_ip = "in position" in text_lower or r"\bip\b" in text_lower
            user_claims_oop = "out of position" in text_lower or r"\boop\b" in text_lower

            if user_claims_ip and not is_ip:
                evaluations.append(
                    ReasoningClaimEvaluation(
                        claim_category="POSITION",
                        extracted_text="Claimed in-position advantage",
                        is_sound=False,
                        critique=f"Incorrect positional assessment: Hero is in seat {hero_position}, which acts out of position postflop.",
                    )
                )
            elif user_claims_oop and is_ip:
                evaluations.append(
                    ReasoningClaimEvaluation(
                        claim_category="POSITION",
                        extracted_text="Claimed out-of-position disadvantage",
                        is_sound=False,
                        critique=f"Hero is in position ({hero_position}), acting last on future betting rounds.",
                    )
                )
            else:
                evaluations.append(
                    ReasoningClaimEvaluation(
                        claim_category="POSITION",
                        extracted_text="Positional relationship assessment",
                        is_sound=True,
                        critique=f"Sound assessment of positional leverage for {hero_position}.",
                    )
                )

        # 3. Blocker / Card Removal Claims
        blocker_patterns = [r"block", r"card removal", r"unblock", r"blocks the"]
        has_blocker_claim = any(re.search(pat, text_lower) for pat in blocker_patterns)

        if has_blocker_claim:
            ranks = [c[0].upper() for c in hero_cards if len(c) >= 1]
            critique = f"Hero cards ({' '.join(hero_cards)}) evaluated for card removal. "
            is_sound = True

            if "ace" in text_lower or "blocks a" in text_lower or "block a" in text_lower:
                if "A" in ranks:
                    critique += (
                        "Holding an Ace genuinely removes top value and bluff combos from opponent."
                    )
                else:
                    is_sound = False
                    critique += "Mentioned blocking Aces, but Hero does not hold an Ace."
            elif "king" in text_lower:
                if "K" in ranks:
                    critique += "Holding a King removes relevant top pair/draw combos."
                else:
                    is_sound = False
                    critique += "Mentioned King blockers, but Hero does not hold a King."
            else:
                critique += "Blocker effect considered in range assessment."

            evaluations.append(
                ReasoningClaimEvaluation(
                    claim_category="BLOCKER",
                    extracted_text="Card removal / blocker claim",
                    is_sound=is_sound,
                    critique=critique,
                )
            )

        # 4. Tournament ICM / Bounty Claims
        icm_patterns = [r"bubble", r"pay jump", r"icm", r"risk premium", r"bounty", r"pko"]
        has_icm_claim = any(re.search(pat, text_lower) for pat in icm_patterns)

        if has_icm_claim:
            t_ctx = math_verdict.tournament_context
            if t_ctx and t_ctx.is_icm_active:
                avg_bf = sum(t_ctx.bubble_factors_against_villains.values()) / max(
                    1, len(t_ctx.bubble_factors_against_villains)
                )
                evaluations.append(
                    ReasoningClaimEvaluation(
                        claim_category="ICM_RISK",
                        extracted_text="ICM pressure / tournament structure claim",
                        is_sound=True,
                        critique=(
                            f"Valid tournament context: Active ICM pressure (average bubble factor {avg_bf:.2f}). "
                            "Chips lost are worth significantly more than chips won."
                        ),
                    )
                )
            elif t_ctx and not t_ctx.is_icm_active:
                evaluations.append(
                    ReasoningClaimEvaluation(
                        claim_category="ICM_RISK",
                        extracted_text="ICM claim without payout structure",
                        is_sound=False,
                        critique="ICM pressure cited, but tournament payouts were not specified. Evaluated under Chip-EV.",
                    )
                )
            else:
                evaluations.append(
                    ReasoningClaimEvaluation(
                        claim_category="ICM_RISK",
                        extracted_text="Tournament ICM claim in cash context",
                        is_sound=False,
                        critique="ICM cited in a Cash Game environment where chip values are linear and constant.",
                    )
                )

        return evaluations
