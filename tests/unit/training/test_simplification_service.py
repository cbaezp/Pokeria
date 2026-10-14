"""Unit tests for StrategySimplificationService.

Verifies:
1. Threshold inclusivity at exactly 50%.
2. Frequencies immediately below and above threshold (49.9%, 50.1%).
3. Pure raise (100%) and pure fold (0%).
4. Standard mixed strategy preservation.
5. Multi-action support (SB limp/raise/fold).
6. Custom thresholds (25%, 75%).
7. Zero fabricated EV guarantees.
"""

from app.domain.training.simplification_service import (
    RangeStrategyMode,
    StrategySimplificationService,
)


def test_threshold_inclusivity_at_exactly_50_percent():
    """Raise frequency of exactly 50.0% must simplify to RAISE."""
    freqs = {"RAISE": 0.50, "FOLD": 0.50}
    res = StrategySimplificationService.simplify_frequencies(
        freqs, RangeStrategyMode.SIMPLIFIED, threshold=0.50
    )
    assert res.target_action == "RAISE"
    assert res.target_frequency == 1.0
    assert res.is_compatible_binary_rfi is True

    # Test grading
    grade_raise = StrategySimplificationService.grade_decision(
        "RAISE", freqs, RangeStrategyMode.SIMPLIFIED, threshold=0.50
    )
    assert grade_raise.is_correct is True
    assert grade_raise.target_action == "RAISE"
    assert grade_raise.grade == "STRONG"

    grade_fold = StrategySimplificationService.grade_decision(
        "FOLD", freqs, RangeStrategyMode.SIMPLIFIED, threshold=0.50
    )
    assert grade_fold.is_correct is False
    assert grade_fold.target_action == "RAISE"
    assert grade_fold.grade == "MISTAKE"


def test_frequencies_immediately_below_and_above_threshold():
    """49.9% -> FOLD, 50.1% -> RAISE."""
    below = {"RAISE": 0.499, "FOLD": 0.501}
    res_below = StrategySimplificationService.simplify_frequencies(
        below, RangeStrategyMode.SIMPLIFIED, threshold=0.50
    )
    assert res_below.target_action == "FOLD"

    above = {"RAISE": 0.501, "FOLD": 0.499}
    res_above = StrategySimplificationService.simplify_frequencies(
        above, RangeStrategyMode.SIMPLIFIED, threshold=0.50
    )
    assert res_above.target_action == "RAISE"


def test_pure_raise_and_pure_fold():
    """100% -> RAISE in all modes, 0% -> FOLD in all modes."""
    pure_raise = {"RAISE": 1.0, "FOLD": 0.0}
    for mode in [
        RangeStrategyMode.STANDARD,
        RangeStrategyMode.SIMPLIFIED,
        RangeStrategyMode.CUSTOM,
    ]:
        res = StrategySimplificationService.simplify_frequencies(pure_raise, mode, threshold=0.50)
        assert res.target_action == "RAISE"

    pure_fold = {"RAISE": 0.0, "FOLD": 1.0}
    for mode in [
        RangeStrategyMode.STANDARD,
        RangeStrategyMode.SIMPLIFIED,
        RangeStrategyMode.CUSTOM,
    ]:
        res = StrategySimplificationService.simplify_frequencies(pure_fold, mode, threshold=0.50)
        assert res.target_action == "FOLD"


def test_standard_mixed_strategy_preservation():
    """In Standard mode, raw frequencies are preserved and valid mixed actions are not marked blunders."""
    mixed = {"RAISE": 0.60, "FOLD": 0.40}
    res = StrategySimplificationService.simplify_frequencies(mixed, RangeStrategyMode.STANDARD)
    assert res.mode == RangeStrategyMode.STANDARD
    assert res.source_frequencies == {"RAISE": 0.60, "FOLD": 0.40}
    assert res.all_target_frequencies == {"RAISE": 0.60, "FOLD": 0.40}

    # In Standard mode, both RAISE and FOLD are valid actions
    grade_raise = StrategySimplificationService.grade_decision(
        "RAISE", mixed, RangeStrategyMode.STANDARD
    )
    assert grade_raise.is_correct is True
    assert grade_raise.is_reference_action is True
    assert grade_raise.reference_alignment == 0.60
    assert grade_raise.grade in ("STRONG", "ACCEPTABLE")

    grade_fold = StrategySimplificationService.grade_decision(
        "FOLD", mixed, RangeStrategyMode.STANDARD
    )
    assert grade_fold.is_correct is True
    assert grade_fold.is_reference_action is True
    assert grade_fold.reference_alignment == 0.40
    assert grade_fold.grade == "ACCEPTABLE"

    # An invalid action (e.g. CALL in unopened pot) is off-reference
    grade_call = StrategySimplificationService.grade_decision(
        "CALL", mixed, RangeStrategyMode.STANDARD
    )
    assert grade_call.is_correct is False
    assert grade_call.is_reference_action is False
    assert grade_call.reference_alignment == 0.0


def test_multi_action_sb_limp_raise_fold():
    """Multi-action spots (e.g. SB 35% Raise, 33% Limp, 32% Fold) are handled without binary corruption."""
    multi = {"RAISE": 0.35, "CALL": 0.33, "FOLD": 0.32}
    res = StrategySimplificationService.simplify_frequencies(multi, RangeStrategyMode.SIMPLIFIED)
    assert res.is_compatible_binary_rfi is False
    assert res.target_action == "RAISE"  # 35% is the dominant action

    multi_limp = {"RAISE": 0.30, "CALL": 0.45, "FOLD": 0.25}
    res_limp = StrategySimplificationService.simplify_frequencies(
        multi_limp, RangeStrategyMode.SIMPLIFIED
    )
    assert res_limp.target_action == "CALL"  # 45% is dominant


def test_custom_thresholds():
    """Custom thresholds (25%, 75%) behave as specified."""
    freqs = {"RAISE": 0.30, "FOLD": 0.70}

    # At 25% threshold, 30% >= 25% -> RAISE
    res_25 = StrategySimplificationService.simplify_frequencies(
        freqs, RangeStrategyMode.CUSTOM, threshold=0.25
    )
    assert res_25.target_action == "RAISE"

    # At 75% threshold, 30% < 75% -> FOLD
    res_75 = StrategySimplificationService.simplify_frequencies(
        freqs, RangeStrategyMode.CUSTOM, threshold=0.75
    )
    assert res_75.target_action == "FOLD"


def test_zero_fabricated_ev():
    """EV loss must be None when real_action_evs is None, preventing fabricated solver metrics."""
    freqs = {"RAISE": 0.80, "FOLD": 0.20}
    grade = StrategySimplificationService.grade_decision(
        "FOLD", freqs, RangeStrategyMode.STANDARD, real_action_evs=None
    )
    assert grade.ev_loss is None

    # When real solver EVs are provided, calculate genuine EV difference
    real_evs = {"RAISE": 1.45, "FOLD": 0.0}
    grade_with_ev = StrategySimplificationService.grade_decision(
        "FOLD", freqs, RangeStrategyMode.STANDARD, real_action_evs=real_evs
    )
    assert grade_with_ev.ev_loss == 1.45
