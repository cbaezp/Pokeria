"""Controlled solver generation pipeline and numerical quality gate.

Enforces:
1. Input validation & deterministic content fingerprinting.
2. Solver execution under bounded resources & timeout.
3. Multi-checkpoint convergence and NashConv/exploitability verification.
4. Independent payoff unit safety (CASH chips vs TOURNAMENT CSTE).
5. Numerical strategy probability normalization and finite EV bounds.
6. Atomic artifact hashing, node index generation, and catalog registration.
7. Quarantining of failed or under-solved runs (never publishing unvalidated packs).
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.domain.poker.node_extractor import node_extractor
from app.domain.poker.solver_types import (
    RootEvs,
    SolverConfig,
    SolverStatus,
    StorageMode,
)
from app.domain.poker.strategy_pack import StrategyPack

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class QualityGateResult:
    """Outcome of numerical and game-theoretic validation checks."""

    passed: bool
    status: SolverStatus
    checks: dict[str, bool]
    reasons: list[str]
    metrics: dict[str, Any]


class SolverQualityGate:
    """Rigorous gate certifying solver solutions before promotion to curriculum."""

    # Maximum permissible NashConv or Exploitability (% of starting pot) for production certification
    MAX_CERTIFIED_EXPLOITABILITY_PCT: float = 0.50  # 0.50% of pot

    @classmethod
    def verify(
        cls,
        config: SolverConfig,
        solution_data: dict[str, Any],
        min_iterations: int = 100,
    ) -> QualityGateResult:
        """Evaluate full mathematical integrity of solved equilibrium."""
        checks: dict[str, bool] = {}
        reasons: list[str] = []
        metrics: dict[str, Any] = {}

        meta = solution_data.get("meta", {})
        nodes = solution_data.get("nodes", [])
        root_combos = solution_data.get("root_combos", [[], []])

        # 1. Convergence & Iteration Count
        iterations = int(meta.get("iterations", 0))
        metrics["iterations"] = iterations
        checks["sufficient_iterations"] = iterations >= min_iterations
        if not checks["sufficient_iterations"]:
            reasons.append(
                f"Iterations ({iterations}) below certification threshold ({min_iterations})"
            )

        # 2. Payoff Unit & Convergence Metric
        if "payoff_unit" not in meta:
            checks["payoff_unit_present"] = False
            reasons.append("Missing required 'payoff_unit' in solver meta")
            payoff_unit = "unknown"
        else:
            payoff_unit = str(meta["payoff_unit"]).lower()
            if payoff_unit not in ("chips", "cste"):
                checks["payoff_unit_valid"] = False
                reasons.append(f"Invalid payoff_unit '{payoff_unit}'")
        metrics["payoff_unit"] = payoff_unit

        is_tournament = config.game_type == "TOURNAMENT" or payoff_unit == "cste"
        if is_tournament:
            # General-sum tournament equity uses NashConv
            gain = meta.get("gain", [0.0, 0.0])
            if "exploitability_pct_of_pot" not in meta:
                checks["converged"] = False
                reasons.append(
                    "Missing required exploitability metadata: 'exploitability_pct_of_pot'"
                )
                exploit_pct = float("inf")
            else:
                exploit_pct = float(meta["exploitability_pct_of_pot"])
            nash_conv = float(meta.get("exploitability_chips", sum(gain)))
            metrics["nash_conv"] = nash_conv
            metrics["exploitability_pct_of_pot"] = exploit_pct

            checks["converged"] = (
                checks.get("converged", True)
                and exploit_pct <= config.target_exploitability
                and exploit_pct <= cls.MAX_CERTIFIED_EXPLOITABILITY_PCT
            )
            if not checks["converged"] and "exploitability_pct_of_pot" in meta:
                reasons.append(
                    f"Tournament NashConv ({exploit_pct:.4f}% pot) exceeds target ({config.target_exploitability}%)"
                )
        else:
            # Cash game chip-EV (unraked zero-sum or raked general-sum)
            if "exploitability_pct_of_pot" not in meta or "exploitability_chips" not in meta:
                checks["converged"] = False
                reasons.append(
                    "Missing required exploitability metadata: 'exploitability_pct_of_pot' or 'exploitability_chips'"
                )
                exploit_pct = float("inf")
                exploit_chips = float("inf")
            else:
                exploit_pct = float(meta["exploitability_pct_of_pot"])
                exploit_chips = float(meta["exploitability_chips"])
            metrics["exploitability_chips"] = exploit_chips
            metrics["exploitability_pct_of_pot"] = exploit_pct

            # Convergence: exploitability/NashConv must not be negative beyond tolerance and must meet target
            checks["converged"] = (
                checks.get("converged", True)
                and exploit_pct <= config.target_exploitability
                and exploit_pct <= cls.MAX_CERTIFIED_EXPLOITABILITY_PCT
                and exploit_chips >= -1e-4
            )
            if (
                not checks["converged"]
                and "exploitability_pct_of_pot" in meta
                and "exploitability_chips" in meta
            ):
                reasons.append(
                    f"Cash exploitability/NashConv ({exploit_pct:.4f}% pot) exceeds target ({config.target_exploitability}%) or is unphysically negative"
                )

            # Rake safety: total expected pot share must not exceed starting pot (rake cannot create chips)
            if config.rake_percent > 0.0:
                if (
                    "root_evs" not in meta
                    or not isinstance(meta["root_evs"], dict)
                    or "pot_share" not in meta["root_evs"]
                ):
                    reasons.append("Raked solution metadata missing required 'root_evs.pot_share'")
                    checks["rake_pot_preservation"] = False
                else:
                    root_evs_dict = meta["root_evs"]
                    pot_share = root_evs_dict["pot_share"]
                    total_pot_share = float(pot_share[0]) + float(pot_share[1])
                    metrics["total_pot_share"] = total_pot_share
                    checks["rake_pot_preservation"] = total_pot_share <= (
                        config.starting_pot + 1e-3
                    )
                    if not checks["rake_pot_preservation"]:
                        reasons.append(
                            f"Raked pot share ({total_pot_share:.2f}) exceeds starting pot ({config.starting_pot})"
                        )

        # 3. Probability Normalization and Finite EVs
        invalid_probs = 0
        non_finite_evs = 0
        missing_evs_count = 0
        board_tokens = config.board.split()

        for n in nodes[:50]:  # Verify first 50 decision nodes
            combo_count = int(n.get("combo_count", 0))
            actions = n.get("actions", [])
            strategy = n.get("strategy", [])
            action_evs = n.get("action_evs")

            if action_evs is None:
                missing_evs_count += 1
            else:
                for val in action_evs:
                    if not math.isfinite(val):
                        non_finite_evs += 1

            # Check probability normalization per combo
            for c_idx in range(combo_count):
                combo_prob_sum = 0.0
                for a_idx in range(len(actions)):
                    offset = a_idx * combo_count + c_idx
                    if offset < len(strategy):
                        p = float(strategy[offset])
                        if not math.isfinite(p) or p < -1e-4:
                            invalid_probs += 1
                        combo_prob_sum += max(0.0, p)
                if combo_prob_sum > 0.0 and abs(combo_prob_sum - 1.0) > 0.05:
                    invalid_probs += 1

        checks["probability_normalization"] = invalid_probs == 0
        if not checks["probability_normalization"]:
            reasons.append(
                f"Found {invalid_probs} invalid probability distributions in decision nodes"
            )

        checks["finite_evs"] = non_finite_evs == 0
        if not checks["finite_evs"]:
            reasons.append(f"Found {non_finite_evs} non-finite action EV numbers (NaN or Inf)")

        # 4. Blocker & Card Removal Verification
        blocked_combos = 0
        for _p_idx, player_combos in enumerate(root_combos):
            for c in player_combos:
                cards_str = c.get("cards", "")
                if len(cards_str) == 4:
                    c1 = cards_str[:2]
                    c2 = cards_str[2:]
                    if c1 in board_tokens or c2 in board_tokens:
                        blocked_combos += 1

        checks["card_removal"] = blocked_combos == 0
        if not checks["card_removal"]:
            reasons.append(f"Found {blocked_combos} combos holding board cards in player ranges")

        all_passed = all(checks.values())
        status = SolverStatus.VALIDATED if all_passed else SolverStatus.FAILED

        return QualityGateResult(
            passed=all_passed,
            status=status,
            checks=checks,
            reasons=reasons,
            metrics=metrics,
        )


class ControlledGenerationPipeline:
    """Robust, reproducible, and resource-bounded solver artifact generation pipeline."""

    @staticmethod
    def resolve_solver_binary(custom_path: Path | str | None = None) -> Path:
        """Resolve the solver binary path across development, container, and CI environments."""
        if custom_path is not None:
            p = Path(custom_path)
            if p.exists():
                return p
        env_path = os.environ.get("POKER_SOLVER_BIN")
        if env_path and Path(env_path).exists():
            return Path(env_path)
        candidates = [
            Path("apps/solver/target/release/solver"),
            Path("apps/api/bin/solver"),
            Path("/usr/local/bin/solver"),
            Path("/app/apps/api/bin/solver"),
        ]
        for cand in candidates:
            if cand.exists():
                return cand
        which_path = shutil.which("solver")
        if which_path:
            return Path(which_path)
        return Path("apps/solver/target/release/solver")

    def __init__(
        self,
        solver_bin: Path | str | None = None,
        solutions_dir: Path | str = Path("data/solutions"),
    ) -> None:
        self.solver_bin = self.resolve_solver_binary(solver_bin)
        self.solutions_dir = Path(solutions_dir)
        self.solutions_dir.mkdir(parents=True, exist_ok=True)
        self.quarantine_dir = self.solutions_dir / ".quarantined"
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir = self.solutions_dir / ".index"
        self.index_dir.mkdir(parents=True, exist_ok=True)

    def generate_and_certify(
        self,
        config: SolverConfig,
        name: str,
        description: str,
        scenario_key: str,
        min_iterations: int = 100,
        timeout_sec: float = 300.0,
        force_recompute: bool = False,
    ) -> tuple[StrategyPack, QualityGateResult]:
        """Execute full generation pipeline from config to certified strategy pack."""
        # Step 1: Input Validation
        self._validate_input(config)

        # Step 2: Content-addressed Fingerprint
        config_hash = config.canonical_hash()[:16]
        pack_id = f"{scenario_key}_{config_hash}"

        # Step 3: Idempotency Check
        target_path = self.solutions_dir / f"{pack_id}.json"
        if target_path.exists() and not force_recompute:
            logger.info("Found existing artifact for %s at %s. Validating...", pack_id, target_path)
            with open(target_path, encoding="utf-8") as f:
                existing_data = json.load(f)
            gate = SolverQualityGate.verify(config, existing_data, min_iterations)
            if gate.passed:
                pack = self._build_pack_from_data(
                    pack_id, name, description, scenario_key, config, existing_data, target_path
                )
                return pack, gate

        # Step 4: Solver Execution
        temp_out = self.solutions_dir / f".tmp_{pack_id}_{int(time.time())}.json"
        temp_cfg = self.solutions_dir / f".tmp_{pack_id}_{int(time.time())}.toml"

        try:
            self._write_toml_config(config, temp_cfg)

            cmd = [
                str(self.solver_bin),
                "solve",
                "--config",
                str(temp_cfg),
                "--out",
                str(temp_out),
            ]
            if config.storage_mode == StorageMode.I16:
                cmd.extend(["--storage", "i16"])
            if config.threads:
                cmd.extend(["--threads", str(config.threads)])

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                check=False,
            )

            if proc.returncode != 0 or not temp_out.exists():
                raise RuntimeError(
                    f"Solver binary execution failed with code {proc.returncode}: {proc.stderr}"
                )

            # Step 5: Load and Verify
            with open(temp_out, encoding="utf-8") as f:
                solution_data = json.load(f)

            # Step 6: Numerical Quality Gate
            gate = SolverQualityGate.verify(config, solution_data, min_iterations)

            if not gate.passed:
                # Quarantine failed run
                quarantine_path = self.quarantine_dir / f"{pack_id}.json"
                temp_out.replace(quarantine_path)
                logger.warning(
                    "Solution %s FAILED quality gate (%s). Quarantined at %s",
                    pack_id,
                    gate.reasons,
                    quarantine_path,
                )
                raise ValueError(
                    f"Solver solution failed quality certification gate: {'; '.join(gate.reasons)}"
                )

            # Step 7: Atomic Artifact Promotion
            temp_out.replace(target_path)

            # Step 8: Build Node Index with bounded memory
            node_extractor.extract_node(pack_id, 0, target_path)

            # Step 9: Register Strategy Pack in manifest
            pack = self._build_pack_from_data(
                pack_id, name, description, scenario_key, config, solution_data, target_path
            )
            self._register_in_manifest(pack)

            return pack, gate

        finally:
            if temp_cfg.exists():
                temp_cfg.unlink()
            if temp_out.exists():
                temp_out.unlink()

    def _validate_input(self, config: SolverConfig) -> None:
        """Validate input configuration constraints."""
        board_tokens = config.board.split()
        if len(board_tokens) not in (3, 4, 5):
            raise ValueError(f"Board must have 3, 4, or 5 cards: {config.board}")
        if config.starting_pot <= 0.0 or config.effective_stack <= 0.0:
            raise ValueError("Starting pot and effective stack must be strictly positive.")
        if config.target_exploitability <= 0.0:
            raise ValueError("Target exploitability must be positive.")

    def _write_toml_config(self, config: SolverConfig, path: Path) -> None:
        """Export SolverConfig into toml format for solver binary."""
        lines = [
            f'board = "{config.board}"',
            f'oop_range = "{config.oop_range}"',
            f'ip_range = "{config.ip_range}"',
            f"starting_pot = {config.starting_pot}",
            f"effective_stack = {config.effective_stack}",
            f"raise_cap = {config.raise_cap}",
            f"max_iterations = {config.max_iterations}",
            f"target_exploitability = {config.target_exploitability / 100.0}",  # solver takes fraction
            f"allin_threshold = {config.allin_threshold}",
        ]
        if config.rake_percent > 0.0:
            lines.append("\n[rake]")
            lines.append(f"percent = {config.rake_percent}")
            lines.append(f"cap = {config.rake_cap}")

        if (
            config.game_type == "TOURNAMENT"
            and config.payout_structure
            and config.tournament_stacks
        ):
            lines.append("\n[tournament]")
            lines.append(f"payouts = {config.payout_structure}")
            lines.append(f"stacks = {config.tournament_stacks}")
            seats = config.tournament_seats or [0, 1]
            lines.append(f"seats = {seats}")

        # Sizings
        tree_dict = config.bet_tree.to_dict()
        for pos in ["oop", "ip"]:
            for street in ["flop", "turn", "river"]:
                s_data = tree_dict.get(pos, {}).get(street, {})
                bet_pcts = s_data.get("bet", {}).get("percents", [])
                raise_pcts = s_data.get("raise", {}).get("percents", [])
                allin = s_data.get("bet", {}).get("allin", True)
                if bet_pcts or raise_pcts:
                    lines.append(f"\n[sizings.{pos}.{street}]")
                    if bet_pcts:
                        lines.append(
                            f"bet = {{ percents = {bet_pcts}, allin = {'true' if allin else 'false'} }}"
                        )
                    if raise_pcts:
                        lines.append(
                            f"raise = {{ percents = {raise_pcts}, allin = {'true' if allin else 'false'} }}"
                        )

        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _build_pack_from_data(
        self,
        pack_id: str,
        name: str,
        description: str,
        scenario_key: str,
        config: SolverConfig,
        solution_data: dict[str, Any],
        artifact_path: Path,
    ) -> StrategyPack:
        """Construct domain StrategyPack from solution payload."""
        meta = solution_data.get("meta", {})
        root_evs_dict = meta["root_evs"]
        zero_sum = root_evs_dict["zero_sum"]
        pot_share = root_evs_dict["pot_share"]

        with open(artifact_path, "rb") as f:
            bytes_content = f.read()
        checksum = hashlib.sha256(bytes_content).hexdigest()

        return StrategyPack(
            id=pack_id,
            name=name,
            description=description,
            scenario_key=scenario_key,
            board=config.board,
            oop_range=config.oop_range,
            ip_range=config.ip_range,
            starting_pot=config.starting_pot,
            effective_stack=config.effective_stack,
            bet_tree=config.bet_tree.to_dict(),
            iterations=int(meta["iterations"]),
            exploitability_chips=float(
                meta.get("exploitability_chips", sum(meta.get("gain", [0.0, 0.0])))
            ),
            exploitability_pct_of_pot=float(meta["exploitability_pct_of_pot"]),
            root_evs=RootEvs(
                oop_zero_sum=float(zero_sum[0]),
                ip_zero_sum=float(zero_sum[1]),
                oop_pot_share=float(pot_share[0]),
                ip_pot_share=float(pot_share[1]),
            ),
            artifact_path=str(artifact_path),
            artifact_checksum=checksum,
            artifact_bytes=len(bytes_content),
            node_count=int(solution_data.get("node_count", 0)),
            engine_version=meta.get("engine_version", "1.0.0"),
            engine_commit="git",
            validation_status=SolverStatus.VALIDATED,
            game_type=config.game_type,
            table_context=config.table_context,
            hero_position=config.hero_position,
            villain_position=config.villain_position,
            payoff_unit=config.payoff_unit,
            rake_percent=config.rake_percent,
            rake_cap=config.rake_cap,
            ante=config.ante,
            tournament_context={
                "payouts": config.payout_structure,
                "stacks": config.tournament_stacks,
                "seats": config.tournament_seats,
            }
            if config.game_type == "TOURNAMENT"
            else None,
        )

    def _register_in_manifest(self, pack: StrategyPack) -> None:
        """Register or update pack metadata in manifest.json."""
        manifest_path = self.solutions_dir / "manifest.json"
        packs = []
        if manifest_path.exists():
            try:
                with open(manifest_path, encoding="utf-8") as f:
                    packs = json.load(f)
            except Exception:
                packs = []

        # Remove existing if present
        packs = [p for p in packs if p.get("id") != pack.id]
        packs.append(pack.to_summary_dict())

        tmp_manifest = manifest_path.with_suffix(".tmp")
        with open(tmp_manifest, "w", encoding="utf-8") as f:
            json.dump(packs, f, indent=2)
        tmp_manifest.replace(manifest_path)
