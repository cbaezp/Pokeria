"""Tests for 9-max preflop opening ranges and Live Helper template compatibility."""

from __future__ import annotations

import pytest

from app.domain.live_helper.templates import ALL_QUICK_TEMPLATES, CASH_6MAX_CONFIG, QuickTemplate
from app.domain.training.preflop_data import PreflopReferenceProvider
from app.domain.training.strategy_registry import (
    ALL_STRATEGY_REFERENCES,
    REF_ILLUSTRATIVE_100BB_9MAX_RFI,
    get_strategy_reference,
)


class TestNineMaxPreflopData:
    """Verify 9-max preflop range benchmarks and position lookups."""

    def test_supported_positions_include_nine_max(self) -> None:
        """Supported positions must include UTG+1, UTG+2, and LJ."""
        positions = PreflopReferenceProvider.get_supported_positions()
        assert "UTG+1" in positions
        assert "UTG+2" in positions
        assert "LJ" in positions
        assert len(positions) == 8  # UTG, UTG+1, UTG+2, LJ, HJ, CO, BTN, SB

    def test_utg1_utg2_lj_frequency_progression(self) -> None:
        """Pocket 66 should progressively increase in raise frequency from UTG to UTG+2."""
        utg_66 = PreflopReferenceProvider.get_rfi_action("UTG", "6c", "6d")
        utg1_66 = PreflopReferenceProvider.get_rfi_action("UTG+1", "6c", "6d")
        utg2_66 = PreflopReferenceProvider.get_rfi_action("UTG+2", "6c", "6d")

        assert utg_66.raise_freq == pytest.approx(0.50)
        assert utg1_66.raise_freq == pytest.approx(0.80)
        assert utg2_66.raise_freq == pytest.approx(1.00)

    def test_position_alias_normalization(self) -> None:
        """Position aliases (e.g., UTG1 vs UTG+1, UTG2 vs UTG+2) resolve to the same frequencies."""
        act_plus = PreflopReferenceProvider.get_rfi_action("UTG+1", "Ac", "Kd")
        act_no_plus = PreflopReferenceProvider.get_rfi_action("UTG1", "Ac", "Kd")
        assert act_plus.raise_freq == act_no_plus.raise_freq == 1.0

        act_utg2_plus = PreflopReferenceProvider.get_rfi_action("UTG+2", "Kc", "Qd")
        act_utg2_no_plus = PreflopReferenceProvider.get_rfi_action("UTG2", "Kc", "Qd")
        assert act_utg2_plus.raise_freq == act_utg2_no_plus.raise_freq == 1.0

    def test_pure_folds_and_raises_across_all_nine_seats(self) -> None:
        """AA must be 100% raise and 72o must be 100% fold across all seats."""
        positions = PreflopReferenceProvider.get_supported_positions()
        for pos in positions:
            aa = PreflopReferenceProvider.get_rfi_action(pos, "Ah", "As")
            assert aa.raise_freq == 1.0, f"AA was not 1.0 raise from {pos}"
            assert aa.fold_freq == 0.0

            fold72 = PreflopReferenceProvider.get_rfi_action(pos, "7c", "2d")
            assert fold72.raise_freq == 0.0, f"72o was not 0.0 raise from {pos}"
            assert fold72.fold_freq == 1.0

    def test_nine_max_strategy_reference_registry(self) -> None:
        """The 9-max strategy reference must be registered and retrievable."""
        ref = get_strategy_reference(REF_ILLUSTRATIVE_100BB_9MAX_RFI.id)
        assert ref is not None
        assert ref.configuration_id == "online_cash_9max_100bb"
        assert ref.source_type.value == "ILLUSTRATIVE_EDUCATIONAL"
        assert ref.table_format == "9-max"
        assert ref.effective_stack_bb == 100.0
        assert "fold" in ref.available_actions
        assert "raise" in ref.available_actions
        assert REF_ILLUSTRATIVE_100BB_9MAX_RFI.id in ALL_STRATEGY_REFERENCES
        assert (
            ALL_STRATEGY_REFERENCES[REF_ILLUSTRATIVE_100BB_9MAX_RFI.id]
            == REF_ILLUSTRATIVE_100BB_9MAX_RFI
        )


class TestLiveHelperTemplateSerialization:
    """Verify QuickTemplate schema compatibility preventing frontend crashes."""

    def test_quick_template_to_dict_provides_dual_keys(self) -> None:
        """Templates must serialize both id/template_id, description/summary, and config/configuration."""
        assert len(ALL_QUICK_TEMPLATES) == 20
        for tmpl in ALL_QUICK_TEMPLATES:
            d = tmpl.to_dict()
            assert "id" in d and "template_id" in d
            assert d["id"] == d["template_id"]

            assert "description" in d and "summary" in d
            assert d["description"] == d["summary"]

            assert "config" in d and "configuration" in d
            assert d["config"] == d["configuration"]
            assert "format_type" in d["configuration"]

    def test_custom_quick_template_serialization(self) -> None:
        """A dynamically created QuickTemplate guarantees the dual schema contract."""
        tmpl = QuickTemplate(
            id="custom_tmpl_01",
            title="Custom 9-Max Spot",
            category="PREFLOP_RFI",
            summary="Custom 9-max spot description",
            config=CASH_6MAX_CONFIG,
            button_seat=1,
            seats=[],
            street="preflop",
            board=[],
            actions=[],
            hero_seat=1,
            hero_cards=("Ah", "Ks"),
            learning_notes="Test notes",
        )
        d = tmpl.to_dict()
        assert d["template_id"] == "custom_tmpl_01"
        assert d["id"] == "custom_tmpl_01"
        assert d["summary"] == "Custom 9-max spot description"
        assert d["description"] == "Custom 9-max spot description"
        assert d["configuration"]["format_type"] == "CASH"
        assert d["config"]["format_type"] == "CASH"
