# Poker Mathematics, Equity & Game-Theoretic Formulations

## 1. Overview & Foundations

Pokeria provides a high-precision mathematical engine (`apps/api/app/domain/poker/`) supporting both pure domain calculations and solver-level decision evaluations.

Every formula is implemented with explicit units, declared assumptions, and boundary validations to prevent common pitfalls (such as mixing pre-call and post-call pots, conflating raw equity with realizable EV, or applying zero-sum rules to raked casino games).

---

## 2. Fundamental Financial & Probabilistic Formulations

### 2.1. Pot Odds & Required Calling Equity

Located in `apps/api/app/domain/poker/math.py`.

#### Formula & Definition
Pot odds express the ratio between the call amount and the total pot after the call is made:
$$\text{Pot Odds} = \frac{\text{Call}}{\text{Pot}_{\text{before call}} + \text{Call}}$$

Required calling equity is simply pot odds expressed as a percentage:
$$\text{Required Equity} (\%) = \text{Pot Odds} \times 100$$

#### Reproducible Example
* Starting pot: $100$ chips.
* Opponent bets: $50$ chips.
* Pot facing Hero: $\text{Pot}_{\text{before call}} = 100 + 50 = 150$ chips.
* Amount to call: $50$ chips.
$$\text{Pot Odds} = \frac{50}{150 + 50} = \frac{50}{200} = 0.25 \quad (25.0\% \text{ required equity})$$

#### Boundary Invariants
- $\text{Call} \ge 0$ and $\text{Pot}_{\text{before call}} \ge 0$.
- Total pot cannot be zero; an empty pot with zero wager raises a domain `ValueError`.

---

### 2.2. Expected Value of Calling (All-In / Terminal Call)

$$\text{EV}_{\text{call}} = \left(\text{Equity} \times (\text{Pot}_{\text{before call}} + \text{Call})\right) - \text{Call}$$
where $\text{Equity} \in [0.0, 1.0]$.

#### Reproducible Example
* Hero faces a $50$-chip bet into a $150$-chip pot (final pot $200$ chips).
* Hero holds a flush draw with $35\%$ equity ($0.35$):
$$\text{EV}_{\text{call}} = (0.35 \times 200) - 50 = 70 - 50 = +20.0 \text{ chips}$$

---

### 2.3. Minimum Defense Frequency (MDF) & Bluff Alpha

#### Bluff Alpha (Break-Even Fold Percentage)
$$\alpha = \frac{\text{Bet}}{\text{Pot}_{\text{before bet}} + \text{Bet}}$$
Represents the minimum frequency with which an opponent must fold for a pure bluff (0% equity when called) to be immediately break-even.

#### Minimum Defense Frequency (MDF)
$$\text{MDF} = 1 - \alpha = \frac{\text{Pot}_{\text{before bet}}}{\text{Pot}_{\text{before bet}} + \text{Bet}}$$
Represents the fraction of their range the defender must continue with (call or raise) to prevent the bettor from profiting by bluffing any two cards.

#### Reproducible Example
* Pot before bet: $100$ chips.
* Bet size: $75$ chips (75% pot sizing).
$$\alpha = \frac{75}{100 + 75} = \frac{75}{175} \approx 0.4286 \quad (42.86\% \text{ fold required})$$
$$\text{MDF} = \frac{100}{100 + 75} = \frac{100}{175} \approx 0.5714 \quad (57.14\% \text{ defense required})$$

*Crucial Game-Theoretic Assumption*: MDF assumes a static, polarized bettor with zero-equity bluffs. In multi-street postflop play with position and future card runouts, real defense frequencies often diverge from MDF due to equity realization differences.

---

### 2.4. Fold Equity & Semi-Bluff EV

$$\text{EV}_{\text{bet}} = P(\text{fold}) \times \text{Pot}_{\text{before bet}} + (1 - P(\text{fold})) \times \left[ \left(\text{Equity}_{\text{called}} \times (\text{Pot}_{\text{before bet}} + 2 \times \text{Bet})\right) - \text{Bet} \right]$$

#### Reproducible Example
* Pot before bet: $100$ chips.
* Hero bets: $60$ chips.
* Opponent folds $40\%$ of the time ($P(\text{fold}) = 0.40$).
* When called ($60\%$), Hero has $32\%$ equity with an open-ended straight draw:
$$\text{Uncontested Win} = 0.40 \times 100 = +40.0 \text{ chips}$$
$$\text{Final Pot When Called} = 100 + 60 + 60 = 220 \text{ chips}$$
$$\text{EV When Called} = (0.32 \times 220) - 60 = 70.4 - 60 = +10.4 \text{ chips}$$
$$\text{Total EV} = 40.0 + (0.60 \times 10.4) = 40.0 + 6.24 = +46.24 \text{ chips}$$

---

### 2.5. Out Counting: Combinatorics vs. Rule of 2 and 4

Located in `outs_to_equity()` in `apps/api/app/domain/poker/math.py`.

#### Exact Combinatorial Calculation
* **Turn (1 card to come from 46 unknown cards)**:
  $$\text{Equity}_{\text{exact}} = \left(\frac{\text{Outs}}{46}\right) \times 100$$
* **Flop (2 cards to come from 47 unknown cards)**:
  $$\text{Equity}_{\text{exact}} = \left( 1 - \frac{\binom{47 - \text{Outs}}{2}}{\binom{47}{2}} \right) \times 100$$

#### Practical Approximation: Rule of 2 and 4
* Turn: $\text{Outs} \times 2$
* Flop: $\text{Outs} \times 4$ (adjusted for $\text{Outs} > 8$ by subtracting $\text{Outs} - 8$)

#### Comparison Table (Flop to River, 47 unknown cards)
| Draw Type | Outs | Exact Formula (%) | Rule of 2 & 4 (%) | Discrepancy |
| :--- | :--- | :--- | :--- | :--- |
| Gutshot | 4 | $16.47\%$ | $16.00\%$ | $-0.47\%$ |
| Open-Ended Straight | 8 | $31.45\%$ | $32.00\%$ | $+0.55\%$ |
| Flush Draw | 9 | $34.97\%$ | $35.00\%$ | $+0.03\%$ |
| Straight Flush Draw | 15 | $54.12\%$ | $53.00\%$ | $-1.12\%$ |

---

## 3. Equity Evaluation Engines

Located in `apps/api/app/domain/poker/equity.py` and `evaluator.py`.

### 3.1. Exact Combinatorial Enumeration
When the remaining board runout space is small (e.g., River equity where 0 cards remain, or Turn runouts where only 1 card remains), Pokeria enumerates all possible community cards deterministically:
$$\text{Equity}_i = \frac{\text{Wins}_i + 0.5 \times \text{Ties}_i}{\text{Total Boards Evaluated}}$$

### 3.2. Monte Carlo Simulation & Statistical Uncertainty
For preflop and flop range-versus-range match-ups where full enumeration spans tens of millions of combinations, Pokeria executes Monte Carlo sampling:
* Number of iterations: typically $10,000$ to $50,000$ trials.
* **Standard Error (Margin of Error)**:
  $$\text{SE} = \sqrt{\frac{p(1 - p)}{N}}$$
  For a $50\%$ coinflip ($p = 0.50$) across $N = 25,000$ iterations:
  $$\text{SE} = \sqrt{\frac{0.5 \times 0.5}{25,000}} = \sqrt{\frac{0.25}{25,000}} = \sqrt{10^{-5}} \approx 0.00316 \quad (\pm 0.32\% \text{ at } 1\sigma)$$
  A $95\%$ confidence interval ($1.96 \sigma$) is within $\pm 0.62\%$.

---

## 4. Tournament Mathematics: Malmuth-Harville ICM & Bubble Factor

Located in `apps/api/app/domain/poker/icm.py` and `apps/solver/engine/src/icm.rs`.

### 4.1. Malmuth-Harville Dynamic Programming
The Independent Chip Model computes tournament equity (payout currency) from chip distributions and prize structures without simulating gameplay.

Let $S$ be a subset of players already placed in top positions. The probability that player $i \notin S$ finishes in the next place is proportional to their remaining chip share:
$$P(i \text{ finishes next} \mid S \text{ finished}) = \frac{\text{Chips}_i}{\sum_{j \notin S} \text{Chips}_j}$$

Pokeria implements this via dynamic programming over subset masks ($g[\text{mask}]$), guaranteeing $O(2^K \cdot K)$ performance where $K$ is the number of paid places:
$$\text{Total Tournament Equity Conserved}: \sum_{i=1}^N \text{Equity}_i = \sum_{k=1}^{\min(N, \text{Places})} \text{Payout}_k$$

### 4.2. Bubble Factor & Risk Premium
In tournaments, chips won are worth less than chips lost. The **Bubble Factor** ($BF$) measures the asymmetry of Hero risking chips against a specific Villain:
$$BF_{\text{Hero vs Villain}} = \frac{\text{Equity}_{\text{current}} - \text{Equity}_{\text{lose}}}{\text{Equity}_{\text{win}} - \text{Equity}_{\text{current}}}$$

* In cash games: $BF = 1.0$ (chips have constant financial value).
* In tournaments near the bubble: $BF > 1.0$ (typically $1.3$ to $2.5+$).
* **Risk Premium**: The additional equity required to justify a call:
  $$\text{Risk Premium} = \frac{BF - 1}{BF + 1}$$

### 4.3. Progressive Knockout (PKO) Bounty Model
In PKO tournaments, each player carries a bounty, typically $50\%$ paid immediately as cash upon elimination and $50\%$ added to the eliminator's own bounty.

Pokeria converts the cash bounty into an equivalent chip value ($C_{\text{bounty}}$):
$$C_{\text{bounty}} = \frac{\text{Immediate Bounty Cash}}{\text{Total Prize Pool}} \times \text{Total Tournament Chips} \times \text{Realization Factor}$$
This bounty chip addition reduces the required equity to call an all-in against a shorter stack.

---

## 5. Non-Zero-Sum Casino Rake Formulation

Located in `apps/solver/engine/src/nlhe.rs`.

### 5.1. The Rake Disruption of Zero-Sum Duality
In standard game theory, two-player poker is zero-sum: $\sum U_i = 0$. Standard CFR best-response calculations rely on the fact that an opponent’s gain equals the player’s loss.

Casino rake breaks zero-sum symmetry:
$$\text{Rake} = \begin{cases} 0 & \text{if action ends preflop ("No flop, no drop")} \\ \min(\text{Cap}, \text{Pot} \times r) & \text{postflop} \end{cases}$$
Because chips leave the table into the house drop, the game is strictly general-sum: $\sum U_i < 0$.

### 5.2. Unilateral Gain (NashConv) Non-Negativity Invariant
Under rake, standard zero-sum best-response calculators produce false negative exploitability values. Pokeria’s solver enforces strictly non-zero-sum unilateral best-response tracking:
$$\Delta_0 = \max_{\sigma_0'} u_0(\sigma_0', \sigma_1) - u_0(\sigma_0, \sigma_1)$$
$$\Delta_1 = \max_{\sigma_1'} u_1(\sigma_0, \sigma_1') - u_1(\sigma_0, \sigma_1)$$
$$\text{NashConv} = \Delta_0 + \Delta_1$$
Because any player can always play their current strategy ($\sigma_i' = \sigma_i$), maximum unilateral gain cannot be negative:
$$\Delta_0 \ge 0, \quad \Delta_1 \ge 0 \implies \text{NashConv} \ge 0$$
Any solver iteration that produces $\text{NashConv} < 0$ indicates numerical corruption and fails the platform’s mathematical verification gate.
