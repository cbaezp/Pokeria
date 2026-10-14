# Poker Mathematics & Verification Guide

> **Target Modules**: `apps/api/app/domain/poker/` and `apps/api/app/domain/math_lab/`
> **Universal Directive**: [AGENTS.md](../AGENTS.md)

---

## 1. Core Mathematical Formulations

All mathematical algorithms in Pokeria must adhere to exact theoretical formulations. Approximations must never be presented as exact values.

### Pot Odds & Required Equity
$$\text{Pot Odds} = \frac{C}{P + C}$$
Where:
- $C$ = Amount to call (excluding previous street bets).
- $P$ = Total pot before calling (including opponents' bets).
- **Invariant**: Required equity is non-negative and strictly $< 1.0$.

### Minimum Defense Frequency (MDF) & Bluff Alpha
$$\text{MDF} = \frac{P}{P + B} \qquad \alpha = \frac{B}{P + B} \qquad \text{MDF} + \alpha = 1.0$$
Where:
- $P$ = Pot size before opponent bets.
- $B$ = Bet size facing the defender.

### Call Expected Value ($EV_{\text{call}}$)
$$\text{EV}_{\text{call}} = p \cdot (P + B) - (1 - p) \cdot B$$
Where $p$ = Hand equity vs opponent range.

### Semi-Bluff Expected Value
$$\text{EV}_{\text{semi-bluff}} = f \cdot P + (1 - f) \cdot [p \cdot (P + B) - (1 - p) \cdot B]$$
Where $f$ = Opponent fold equity percentage.

### Combinatorics & Out Discounting
- **Rule of 2 & 4 Approximation**:
  $$\text{Turn-to-River Equity} \approx 2 \times k\% \qquad \text{Flop-to-River Equity} \approx 4 \times k\%$$
- **Exact Flop-to-River Probability**:
  $$p_{\text{exact}} = 1 - \frac{\binom{47 - k}{2}}{\binom{47}{2}}$$
  Where $k$ is the number of clean outs.

---

## 2. Invariants & Edge Cases

1. **Rake Extraction Non-Zero-Sum Modeling**:
   - In cash games with rake, the pot won is $P_{\text{net}} = P_{\text{gross}} - \min(P_{\text{gross}} \cdot r, \text{cap})$.
   - Rake applies only if the hand reaches the flop ("no flop, no drop").
2. **Short All-In Reopening Rule (TDA & Nevada Gaming Control Board)**:
   - An all-in bet of less than a full legal raise does **not** reopen betting to players who have already acted.
3. **Card Uniqueness Invariant**:
   - Decks contain exactly 52 unique card bitmasks. Card clash checks must trigger immediately if the same card is dealt twice.

---

## 3. Testing Mathematical Code

Always write unit tests using exact analytical comparisons:
```python
def test_pot_odds_exact():
    # Facing 50 into 100 pot: call 50 to win 150 -> 50 / 200 = 25.0%
    pot_odds, req_eq = calculate_pot_odds(pot=100.0, call_amount=50.0)
    assert req_eq == 0.25
```
Run the poker math test suite:
```bash
.venv/bin/pytest tests/unit/poker/test_math.py tests/unit/poker/test_adversarial_equity_math.py
```
