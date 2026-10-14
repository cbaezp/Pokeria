"""Documented, versioned Metric Registry for Poker Lab Learning Analytics.

Defines mathematical specifications, units, treatment of null values, and
interpretation limitations for all volume, EV-loss, decision-quality, and
latency metrics.

Guarantees:
- Never coerces NULL EV loss to 0.0.
- Never combines incompatible raw chip units into ungrounded totals.
- Distinguishes measured performance from inferred player ability.
- Explicitly documents sampling biases and limitations.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

METRIC_REGISTRY_VERSION: str = "v1.0.0"


class MetricCategory(StrEnum):
    VOLUME = "volume"
    EV_LOSS = "ev_loss"
    DECISION_QUALITY = "decision_quality"
    SPEED_CONFIDENCE = "speed_confidence"


@dataclass(frozen=True, slots=True)
class MetricDefinition:
    """Rigorous specification for an analytical metric."""

    id: str
    name: str
    category: MetricCategory
    purpose: str
    numerator: str
    denominator: str
    units: str
    inclusion_criteria: str
    exclusion_criteria: str
    required_data: tuple[str, ...]
    treatment_of_null: str
    aggregation_behavior: str
    interpretation_limitations: str


METRIC_REGISTRY: dict[str, MetricDefinition] = {
    # --------------------------------------------------------------------------
    # Volume Metrics
    # --------------------------------------------------------------------------
    "total_decisions": MetricDefinition(
        id="total_decisions",
        name="Total Practiced Decisions",
        category=MetricCategory.VOLUME,
        purpose="Measures raw training repetitions completed by the user.",
        numerator="Count of all submitted decision events.",
        denominator="1",
        units="decisions",
        inclusion_criteria="All persisted decision_events for the profile.",
        exclusion_criteria="None.",
        required_data=("decision_events.id",),
        treatment_of_null="Not applicable (count operation).",
        aggregation_behavior="COUNT(*)",
        interpretation_limitations="High volume does not imply high learning efficiency or mastery.",
    ),
    "solver_graded_decisions": MetricDefinition(
        id="solver_graded_decisions",
        name="Solver-Graded Decisions",
        category=MetricCategory.VOLUME,
        purpose="Measures decisions backed by rigorous game-theoretic solver equilibria with real action EVs.",
        numerator="Count of decisions where grading_status = 'GRADED'.",
        denominator="1",
        units="decisions",
        inclusion_criteria="Decisions with valid solver equilibrium solution.",
        exclusion_criteria="Illustrative charts, unsupported decisions, and unmeasured EV spots.",
        required_data=("grading_status", "ev_loss"),
        treatment_of_null="Rows where ev_loss IS NULL are excluded.",
        aggregation_behavior="COUNT(ev_loss) FILTER (WHERE grading_status = 'GRADED')",
        interpretation_limitations="Limited to scenarios currently supported by CFR solver solutions.",
    ),
    "graded_decisions": MetricDefinition(
        id="graded_decisions",
        name="Mathematically Graded Decisions (Alias for solver_graded_decisions)",
        category=MetricCategory.VOLUME,
        purpose="Measures decisions backed by rigorous game-theoretic solver equilibria with real action EVs.",
        numerator="Count of decisions where grading_status = 'GRADED'.",
        denominator="1",
        units="decisions",
        inclusion_criteria="Decisions with valid solver equilibrium solution.",
        exclusion_criteria="Illustrative charts, unsupported decisions, and unmeasured EV spots.",
        required_data=("grading_status", "ev_loss"),
        treatment_of_null="Rows where ev_loss IS NULL are excluded.",
        aggregation_behavior="COUNT(ev_loss)",
        interpretation_limitations="Limited to scenarios currently supported by CFR solver solutions.",
    ),
    "all_evaluated_decisions": MetricDefinition(
        id="all_evaluated_decisions",
        name="All Evaluated Decisions",
        category=MetricCategory.VOLUME,
        purpose="Total count of all evaluated decisions across both solver solutions and illustrative chart drills.",
        numerator="Count of decisions where grading_status IN ('GRADED', 'PRACTICE').",
        denominator="1",
        units="decisions",
        inclusion_criteria="All solver-graded or preflop chart-evaluated decisions.",
        exclusion_criteria="Ungraded decisions.",
        required_data=("grading_status",),
        treatment_of_null="Not applicable.",
        aggregation_behavior="COUNT(*) FILTER (WHERE grading_status IN ('GRADED', 'PRACTICE'))",
        interpretation_limitations="Combines heterogeneous decision types; does not indicate uniform EV measurement.",
    ),
    "illustrative_chart_decisions": MetricDefinition(
        id="illustrative_chart_decisions",
        name="Illustrative Preflop Decisions",
        category=MetricCategory.VOLUME,
        purpose="Counts preflop chart drills that test opening/defense ranges without action EV loss.",
        numerator="Count of decisions where grading_status = 'PRACTICE'.",
        denominator="1",
        units="decisions",
        inclusion_criteria="Preflop chart drill scenarios.",
        exclusion_criteria="Solver-backed postflop scenarios.",
        required_data=("grading_status",),
        treatment_of_null="Excluded from EV loss calculation.",
        aggregation_behavior="COUNT(*) FILTER (WHERE grading_status = 'PRACTICE')",
        interpretation_limitations="Charts offer baseline range guidance, not dynamic exploitative or equilibrium EV gradients.",
    ),
    "ungraded_decisions": MetricDefinition(
        id="ungraded_decisions",
        name="Ungraded / Unsupported Decisions",
        category=MetricCategory.VOLUME,
        purpose="Tracks scenarios where solver data was missing or calculation failed.",
        numerator="Count of decisions where grading_status = 'UNGRADED'.",
        denominator="1",
        units="decisions",
        inclusion_criteria="Decisions where solver solution was unavailable at submission time.",
        exclusion_criteria="Properly graded or charted decisions.",
        required_data=("grading_status",),
        treatment_of_null="Never counted as 0.0 EV loss.",
        aggregation_behavior="COUNT(*) FILTER (WHERE grading_status = 'UNGRADED')",
        interpretation_limitations="Identifies coverage gaps in precomputed solver libraries.",
    ),
    "distinct_scenarios": MetricDefinition(
        id="distinct_scenarios",
        name="Distinct Scenarios Encountered",
        category=MetricCategory.VOLUME,
        purpose="Quantifies scenario diversity across the user's practice history.",
        numerator="Count of unique scenario_id values.",
        denominator="1",
        units="scenarios",
        inclusion_criteria="All attempted scenarios.",
        exclusion_criteria="None.",
        required_data=("scenario_id",),
        treatment_of_null="Not applicable.",
        aggregation_behavior="COUNT(DISTINCT scenario_id)",
        interpretation_limitations="Does not normalize for suit isomorphism or near-identical board variants.",
    ),
    # --------------------------------------------------------------------------
    # EV Loss Metrics
    # --------------------------------------------------------------------------
    "total_ev_loss_chips": MetricDefinition(
        id="total_ev_loss_chips",
        name="Total Measured EV Loss (Chips)",
        category=MetricCategory.EV_LOSS,
        purpose="Computes cumulative expected value forfeited across all graded decisions in raw chips.",
        numerator="Sum of ev_loss across graded decisions.",
        denominator="1",
        units="chips",
        inclusion_criteria="Rows with non-null ev_loss and grading_status = 'GRADED'.",
        exclusion_criteria="Illustrative charts, ungraded decisions, null EV rows.",
        required_data=("ev_loss", "grading_status"),
        treatment_of_null="NULL values are strictly excluded from the sum (do not coerce to 0).",
        aggregation_behavior="SUM(ev_loss) FILTER (WHERE ev_loss IS NOT NULL)",
        interpretation_limitations="Raw chip losses from disparate pot sizes (e.g. 20-chip river vs 200-chip 3-bet pot) cannot be treated as uniformly weighted mistakes.",
    ),
    "mean_ev_loss_chips": MetricDefinition(
        id="mean_ev_loss_chips",
        name="Mean EV Loss per Graded Decision (Chips)",
        category=MetricCategory.EV_LOSS,
        purpose="Average chip EV forfeited per mathematically graded decision.",
        numerator="SUM(ev_loss)",
        denominator="COUNT(ev_loss)",
        units="chips / decision",
        inclusion_criteria="Mathematically graded decisions with non-null ev_loss.",
        exclusion_criteria="Illustrative charts and ungraded decisions.",
        required_data=("ev_loss", "grading_status"),
        treatment_of_null="Denominator strictly excludes rows where ev_loss IS NULL.",
        aggregation_behavior="AVG(ev_loss) FILTER (WHERE ev_loss IS NOT NULL)",
        interpretation_limitations="Can be skewed by extreme blunders or heavily oversized pots. Sensitive to scenario difficulty mix.",
    ),
    "mean_ev_loss_pct_of_pot": MetricDefinition(
        id="mean_ev_loss_pct_of_pot",
        name="Mean Normalized EV Loss (% of Pot)",
        category=MetricCategory.EV_LOSS,
        purpose="Normalizes EV loss relative to the decision pot size, enabling cross-scenario comparison.",
        numerator="SUM(ev_loss / pot * 100.0)",
        denominator="COUNT(ev_loss)",
        units="% of pot",
        inclusion_criteria="Graded decisions with non-null ev_loss and pot > 0.",
        exclusion_criteria="Decisions with pot <= 0 or null ev_loss.",
        required_data=("ev_loss", "pot"),
        treatment_of_null="Excluded if ev_loss is NULL.",
        aggregation_behavior="AVG(ev_loss / NULLIF(pot, 0) * 100.0) FILTER (WHERE ev_loss IS NOT NULL)",
        interpretation_limitations="Provides dimensionless mistake magnitude, but does not capture stack depth pressure or tournament ICM utility.",
    ),
    "median_ev_loss": MetricDefinition(
        id="median_ev_loss",
        name="Median EV Loss",
        category=MetricCategory.EV_LOSS,
        purpose="Robust central tendency metric impervious to rare outlier blunders.",
        numerator="50th percentile of non-null ev_loss values.",
        denominator="1",
        units="chips",
        inclusion_criteria="Graded decisions with non-null ev_loss.",
        exclusion_criteria="Null EV rows.",
        required_data=("ev_loss",),
        treatment_of_null="Excluded from percentile calculation.",
        aggregation_behavior="PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY ev_loss)",
        interpretation_limitations="May obscure frequent small inaccuracies that accumulate into significant leaks.",
    ),
    # --------------------------------------------------------------------------
    # Decision Quality Metrics
    # --------------------------------------------------------------------------
    "blunder_rate": MetricDefinition(
        id="blunder_rate",
        name="Blunder Rate",
        category=MetricCategory.DECISION_QUALITY,
        purpose="Proportion of graded decisions that resulted in catastrophic EV loss.",
        numerator="COUNT(*) FILTER (WHERE grade = 'BLUNDER')",
        denominator="COUNT(*) FILTER (WHERE grading_status = 'GRADED')",
        units="percentage",
        inclusion_criteria="Graded decisions with grade assigned.",
        exclusion_criteria="Illustrative charts and ungraded decisions.",
        required_data=("grade", "grading_status"),
        treatment_of_null="Ungraded rows excluded from denominator.",
        aggregation_behavior="COUNT(*) FILTER (WHERE grade = 'BLUNDER')::float / NULLIF(COUNT(*) FILTER (WHERE grading_status = 'GRADED'), 0)",
        interpretation_limitations="Grade boundaries follow threshold heuristics defined in grading engine (e.g. ev_loss > 5 chips or 10% pot).",
    ),
    "strong_decision_rate": MetricDefinition(
        id="strong_decision_rate",
        name="Equilibrium Optimal Decision Rate",
        category=MetricCategory.DECISION_QUALITY,
        purpose="Proportion of graded decisions achieving the highest solver equilibrium action.",
        numerator="COUNT(*) FILTER (WHERE grade = 'BEST')",
        denominator="COUNT(*) FILTER (WHERE grading_status = 'GRADED')",
        units="percentage",
        inclusion_criteria="Graded decisions.",
        exclusion_criteria="Ungraded decisions.",
        required_data=("grade", "grading_status"),
        treatment_of_null="Excluded.",
        aggregation_behavior="COUNT(*) FILTER (WHERE grade = 'BEST')::float / NULLIF(COUNT(*) FILTER (WHERE grading_status = 'GRADED'), 0)",
        interpretation_limitations="In mixed-strategy equilibria, taking an indifferent alternative with 0 EV loss is also mathematically optimal.",
    ),
    # --------------------------------------------------------------------------
    # Speed & Confidence Metrics
    # --------------------------------------------------------------------------
    "median_latency_ms": MetricDefinition(
        id="median_latency_ms",
        name="Median Decision Latency",
        category=MetricCategory.SPEED_CONFIDENCE,
        purpose="Typical deliberation time before action execution.",
        numerator="50th percentile of latency_ms.",
        denominator="1",
        units="milliseconds",
        inclusion_criteria="Decisions with valid latency_ms > 0.",
        exclusion_criteria="Latency <= 0 or extreme outliers (> 300,000 ms).",
        required_data=("latency_ms",),
        treatment_of_null="Ignored if null or non-positive.",
        aggregation_behavior="PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY latency_ms)",
        interpretation_limitations="Deliberation speed does not correlate monotonically with skill; complex multi-way trees warrant longer consideration.",
    ),
    "high_confidence_mistake_count": MetricDefinition(
        id="high_confidence_mistake_count",
        name="High-Confidence Mistakes (Blind Spots)",
        category=MetricCategory.SPEED_CONFIDENCE,
        purpose="Identifies decisions where the user reported high self-confidence (4-5) but committed a mistake/blunder.",
        numerator="COUNT(*) FILTER (WHERE confidence_score >= 4 AND grade IN ('MISTAKE', 'BLUNDER'))",
        denominator="1",
        units="decisions",
        inclusion_criteria="Decisions with confidence_score >= 4 and grade in ('MISTAKE', 'BLUNDER').",
        exclusion_criteria="Decisions with missing confidence.",
        required_data=("confidence_score", "grade"),
        treatment_of_null="Missing confidence scores are excluded from blind spot detection.",
        aggregation_behavior="COUNT(*) FILTER (WHERE confidence_score >= 4 AND grade IN ('MISTAKE', 'BLUNDER'))",
        interpretation_limitations="Confidence is user self-report, not a solver-calibrated posterior probability.",
    ),
}
