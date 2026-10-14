"""Subprocess-based SolverAdapter using native compiled postflop solver.

Executes real heads-up postflop Discounted CFR equilibrium solves with measured exploitability.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import shutil
import tempfile
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from app.application.ports.solver_port import SolverAdapter
from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.exceptions import DomainError, ValidationError
from app.domain.poker.cards import Card
from app.domain.poker.ranges import HandRange
from app.domain.poker.solver_types import (
    ActionLabelData,
    ConvergenceMetrics,
    EngineMetadata,
    HandStrategy,
    NodeStrategy,
    ResourceEstimate,
    RootEvs,
    SolverConfig,
    SolverProgress,
    SolverResult,
    SolverStatus,
    ValidationResult,
)

logger = get_logger(__name__)

PROGRESS_REGEX = re.compile(
    r"iter\s+(\d+)\s+(?:exploitability|NashConv)\s+([\d\.\-]+)\s+(?:chips|cste chips)\s+([\d\.\-]+)%\s+of\s+pot\s+\[measured\]"
)


class SolverSubprocessError(DomainError):
    """Raised when solver subprocess crashes or returns non-zero code."""


class SolverExecutionError(DomainError):
    """Raised when solver execution or artifact validation fails."""


class SolverTimeoutError(DomainError):
    """Raised when solve execution exceeds configured timeout limit."""


class SolverCancellationError(DomainError):
    """Raised when a solve is aborted via cancellation."""


class SubprocessSolverAdapter(SolverAdapter):
    """Concrete adapter orchestrating native postflop solver binary."""

    def __init__(
        self,
        bin_path: str | Path | None = None,
        solutions_dir: str | Path | None = None,
    ) -> None:
        settings = get_settings()
        self._explicit_bin = bin_path is not None
        self.bin_path = Path(bin_path or settings.SOLVER_BIN_PATH)
        self.solutions_dir = Path(solutions_dir or settings.SOLVER_SOLUTIONS_DIR)
        self.solutions_dir.mkdir(parents=True, exist_ok=True)
        self._active_processes: dict[str, asyncio.subprocess.Process] = {}

    def _resolve_binary(self) -> Path:
        """Verify solver binary exists and is executable."""
        if self.bin_path.is_file() and os.access(self.bin_path, os.X_OK):
            return self.bin_path

        # Check PATH
        which_path = shutil.which(str(self.bin_path))
        if which_path:
            return Path(which_path)

        # Only check alternative common locations if bin_path was not explicitly configured
        if not self._explicit_bin:
            common = [
                Path("apps/api/bin/solver"),
                Path("apps/solver/target/release/solver"),
                Path("/usr/local/bin/solver"),
            ]
            for p in common:
                if p.is_file() and os.access(p, os.X_OK):
                    return p

        raise RuntimeError(
            f"Solver executable not found at '{self.bin_path}'. "
            "Please build with 'cargo build --release --bin solver' in apps/solver."
        )

    def validate_configuration(self, config: SolverConfig) -> ValidationResult:
        """Validate input scenario against poker rules and solver constraints."""
        errors: list[str] = []
        warnings: list[str] = []

        # 1. Validate board
        board_tokens = [t.strip() for t in config.board.split() if t.strip()]
        if len(board_tokens) not in (3, 4, 5):
            errors.append(
                f"Board must contain 3 (flop), 4 (turn), or 5 (river) cards, got {len(board_tokens)}: '{config.board}'"
            )
        else:
            try:
                board_cards = [Card.from_str(t) for t in board_tokens]
                if len(set(board_cards)) != len(board_cards):
                    errors.append(f"Board contains duplicate cards: {config.board}")
            except Exception as exc:
                errors.append(f"Invalid card in board '{config.board}': {exc}")

        # 2. Validate ranges
        for label, range_str in [("OOP", config.oop_range), ("IP", config.ip_range)]:
            if not range_str.strip():
                errors.append(f"{label} range cannot be empty")
                continue
            try:
                hr = HandRange.from_string(range_str)
                if hr.combo_count == 0:
                    errors.append(f"{label} range contains 0 legal hand combinations")
                if len(board_tokens) in (3, 4, 5):
                    try:
                        board_cards = [Card.from_str(t) for t in board_tokens]
                        filtered = hr.filter_blockers(board_cards)
                        if filtered.combo_count == 0:
                            errors.append(
                                f"{label} range is 100% blocked by board '{config.board}'"
                            )
                    except Exception:
                        pass
            except Exception as exc:
                errors.append(f"Invalid {label} range '{range_str}': {exc}")

        # 3. Validate financial parameters
        if config.starting_pot <= 0.0:
            errors.append(f"Starting pot must be strictly positive, got {config.starting_pot}")
        if config.effective_stack <= 0.0:
            errors.append(
                f"Effective stack must be strictly positive, got {config.effective_stack}"
            )

        # 4. Validate iterations & convergence targets
        if config.max_iterations < 1:
            errors.append(f"max_iterations must be at least 1, got {config.max_iterations}")
        if config.target_exploitability <= 0.0:
            errors.append(
                f"target_exploitability must be positive, got {config.target_exploitability}"
            )
        if config.target_exploitability > 100.0:
            warnings.append(
                f"target_exploitability of {config.target_exploitability}% of pot is very loose"
            )

        # 5. Validate bet sizes
        bet_tree = config.bet_tree
        for p_label, player_sizings in [("OOP", bet_tree.oop), ("IP", bet_tree.ip)]:
            for st_label, sizing in [
                ("flop", player_sizings.flop),
                ("turn", player_sizings.turn),
                ("river", player_sizings.river),
            ]:
                for pct in sizing.bet:
                    if pct <= 0.0:
                        errors.append(
                            f"{p_label} {st_label} bet sizing percentage must be > 0, got {pct}"
                        )
                for pct in sizing.raise_:
                    if pct <= 0.0:
                        errors.append(
                            f"{p_label} {st_label} raise sizing percentage must be > 0, got {pct}"
                        )

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def estimate_resources(self, config: SolverConfig) -> ResourceEstimate:
        """Estimate tree size, memory consumption, and runtime."""
        board_tokens = [t.strip() for t in config.board.split() if t.strip()]
        street_count = len(board_tokens)

        # Count bet sizings
        sizings_count = 0
        for p in (config.bet_tree.oop, config.bet_tree.ip):
            for s in (p.flop, p.turn, p.river):
                sizings_count += len(s.bet) + len(s.raise_)

        warnings: list[str] = []
        if street_count == 5:
            # River only
            estimated_nodes = max(9, sizings_count * 4 + 7)
            estimated_memory_mb = 4.0
            estimated_seconds = min(0.5, config.max_iterations * 0.0001)
        elif street_count == 4:
            # Turn + River (48 river chance runouts)
            estimated_nodes = max(50, sizings_count * 48 * 3)
            estimated_memory_mb = 35.0
            estimated_seconds = max(0.5, min(8.0, config.max_iterations * 0.003))
        else:
            # Flop + Turn + River (49 turns * 48 rivers)
            estimated_nodes = max(1000, sizings_count * 49 * 48)
            estimated_memory_mb = 250.0
            estimated_seconds = max(2.0, min(60.0, config.max_iterations * 0.03))
            warnings.append("Flop solves traverse multi-street runouts and require higher CPU/RAM")

        settings = get_settings()
        feasible = estimated_memory_mb <= settings.SOLVER_MAX_MEMORY_MB

        return ResourceEstimate(
            estimated_nodes=estimated_nodes,
            estimated_memory_mb=round(estimated_memory_mb, 1),
            estimated_seconds=round(estimated_seconds, 2),
            feasible=feasible,
            warnings=warnings,
        )

    def create_game_tree(self, config: SolverConfig) -> int:
        """Determine game tree node count."""
        estimate = self.estimate_resources(config)
        return estimate.estimated_nodes

    def _generate_toml_config(self, config: SolverConfig) -> str:
        """Construct a valid TOML configuration string for postflop solver."""
        lines = [
            f'board = "{config.board}"',
            f'oop_range = "{config.oop_range}"',
            f'ip_range = "{config.ip_range}"',
            f"effective_stack = {float(config.effective_stack)}",
            f"starting_pot = {float(config.starting_pot)}",
            f"allin_threshold = {float(config.allin_threshold)}",
            f"raise_cap = {int(config.raise_cap)}",
            f"max_iterations = {int(config.max_iterations)}",
            f"target_exploitability = {float(config.target_exploitability)}",
            "alpha = 1.5",
            "beta = 0.0",
            "gamma = 2.0",
            "turn_chance_sampling = false",
            "regret_floor = false",
            f"rake = {{ percent = {float(config.rake_percent)}, cap = {float(config.rake_cap)} }}",
            "",
        ]

        # Sizing blocks
        tree = config.bet_tree
        for pos_str, p_sizing in [("oop", tree.oop), ("ip", tree.ip)]:
            for st_str, st_sizing in [
                ("flop", p_sizing.flop),
                ("turn", p_sizing.turn),
                ("river", p_sizing.river),
            ]:
                lines.append(f"[sizings.{pos_str}.{st_str}]")
                bet_str = ", ".join(f"{x:.1f}" for x in st_sizing.bet)
                raise_str = ", ".join(f"{x:.1f}" for x in st_sizing.raise_)
                lines.append(
                    f"bet = {{ percents = [{bet_str}], allin = {'true' if st_sizing.allin else 'false'} }}"
                )
                lines.append(
                    f"raise = {{ percents = [{raise_str}], allin = {'true' if st_sizing.allin else 'false'} }}"
                )
                lines.append("donk = { percents = [], allin = false }")
                lines.append("")

        return "\n".join(lines)

    async def solve(
        self,
        config: SolverConfig,
        job_id: str | None = None,
        cancel_event: asyncio.Event | None = None,
        on_progress: Callable[[SolverProgress], Awaitable[None]] | None = None,
    ) -> SolverResult:
        """Run postflop solver subprocess and stream progress."""
        validation = self.validate_configuration(config)
        if not validation.valid:
            raise ValidationError(f"Invalid solver configuration: {'; '.join(validation.errors)}")

        bin_exec = self._resolve_binary()
        job_key = job_id or f"solve-{time.time_ns()}"

        with tempfile.TemporaryDirectory(prefix="pokerlab_solve_") as temp_dir:
            temp_path = Path(temp_dir)
            cfg_file = temp_path / "spot.toml"
            out_file = temp_path / "solution.json"

            # Write TOML config
            toml_text = self._generate_toml_config(config)
            cfg_file.write_text(toml_text, encoding="utf-8")

            cmd = [
                str(bin_exec),
                "solve",
                "--config",
                str(cfg_file),
                "--out",
                str(out_file),
                "--report-every",
                str(config.report_every),
                "--storage",
                config.storage_mode.value,
            ]
            if config.threads:
                cmd.extend(["--threads", str(config.threads)])

            logger.info(f"Starting solver subprocess for job {job_key}: {' '.join(cmd)}")
            start_wall = time.perf_counter()

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            self._active_processes[job_key] = proc

            last_progress: SolverProgress | None = None
            settings = get_settings()
            timeout_sec = settings.SOLVER_DEFAULT_TIMEOUT_SECONDS

            async def _read_stream(stream: asyncio.StreamReader) -> None:
                nonlocal last_progress
                while True:
                    line_bytes = await stream.readline()
                    if not line_bytes:
                        break
                    line = line_bytes.decode("utf-8", errors="replace").strip()
                    if not line:
                        continue
                    m = PROGRESS_REGEX.search(line)
                    if m:
                        it = int(m.group(1))
                        chips = float(m.group(2))
                        pct = float(m.group(3))
                        last_progress = SolverProgress(
                            iteration=it,
                            exploitability_chips=chips,
                            exploitability_pct_of_pot=pct,
                            measured=True,
                        )
                        if on_progress:
                            try:
                                await on_progress(last_progress)
                            except Exception as pe:
                                logger.warning(f"Error in on_progress callback: {pe}")

            try:
                # Concurrent read of stdout while watching cancel_event and timeout
                read_task = asyncio.create_task(_read_stream(proc.stdout))  # type: ignore

                while proc.returncode is None:
                    if cancel_event and cancel_event.is_set():
                        proc.terminate()
                        try:
                            await asyncio.wait_for(proc.wait(), timeout=2.0)
                        except TimeoutError:
                            proc.kill()
                        raise SolverCancellationError(
                            f"Job {job_key} was cancelled by user request."
                        )

                    if (time.perf_counter() - start_wall) > timeout_sec:
                        proc.terminate()
                        try:
                            await asyncio.wait_for(proc.wait(), timeout=2.0)
                        except TimeoutError:
                            proc.kill()
                        raise SolverTimeoutError(
                            f"Solver job {job_key} exceeded timeout limit of {timeout_sec}s"
                        )

                    # Poll process
                    try:
                        await asyncio.wait_for(proc.wait(), timeout=0.1)
                    except TimeoutError:
                        pass

                await read_task
                stderr_bytes = await proc.stderr.read() if proc.stderr else b""
                stderr_msg = stderr_bytes.decode("utf-8", errors="replace")

                if proc.returncode != 0:
                    raise SolverSubprocessError(
                        f"Solver exited with code {proc.returncode}: {stderr_msg}"
                    )

            finally:
                self._active_processes.pop(job_key, None)

            wall_seconds = time.perf_counter() - start_wall

            if not out_file.exists():
                raise SolverSubprocessError("Solver completed but solution.json was not created.")

            # Load solution JSON
            solution_bytes = out_file.read_bytes()
            solution_data = json.loads(solution_bytes.decode("utf-8"))

            # Calculate content-addressed hash of the solution artifact
            artifact_checksum = hashlib.sha256(solution_bytes).hexdigest()
            target_artifact_name = f"{config.canonical_hash()[:16]}_{artifact_checksum[:16]}.json"
            target_artifact_path = self.solutions_dir / target_artifact_name

            # Atomic write to persistent solutions dir
            atomic_tmp = target_artifact_path.with_suffix(".tmp")
            atomic_tmp.write_bytes(solution_bytes)
            atomic_tmp.replace(target_artifact_path)

            meta = solution_data.get("meta", {})
            iterations = int(meta.get("iterations", config.max_iterations))
            if "exploitability_chips" not in meta or "exploitability_pct_of_pot" not in meta:
                raise SolverExecutionError("Solver artifact missing exploitability metrics in meta")
            exploitability_chips = float(meta["exploitability_chips"])
            exploitability_pct_of_pot = float(meta["exploitability_pct_of_pot"])
            root_evs_dict = meta.get("root_evs")
            if (
                not root_evs_dict
                or "zero_sum" not in root_evs_dict
                or "pot_share" not in root_evs_dict
            ):
                raise SolverExecutionError("Solver artifact missing root_evs metrics in meta")
            zero_sum = root_evs_dict["zero_sum"]
            pot_share = root_evs_dict["pot_share"]

            root_evs = RootEvs(
                oop_zero_sum=float(zero_sum[0]),
                ip_zero_sum=float(zero_sum[1]),
                oop_pot_share=float(pot_share[0]),
                ip_pot_share=float(pot_share[1]),
            )

            # Determine convergence status
            is_converged = exploitability_pct_of_pot <= config.target_exploitability
            status = SolverStatus.VALIDATED if is_converged else SolverStatus.APPROXIMATE

            engine_meta = self.get_engine_metadata()

            return SolverResult(
                status=status,
                iterations=iterations,
                wall_seconds=round(wall_seconds, 4),
                exploitability_chips=round(exploitability_chips, 6),
                exploitability_pct_of_pot=round(exploitability_pct_of_pot, 4),
                root_evs=root_evs,
                solution_artifact_path=str(target_artifact_path),
                solution_checksum=artifact_checksum,
                solution_bytes=len(solution_bytes),
                node_count=int(solution_data.get("node_count", 0)),
                engine_metadata=engine_meta,
                raw_solution=solution_data,
            )

    def cancel(self, job_id: str) -> bool:
        """Cancel a running solver process by job_id."""
        proc = self._active_processes.get(job_id)
        if proc and proc.returncode is None:
            proc.terminate()
            return True
        return False

    def extract_strategy(
        self, solution_data: dict[str, Any], node_id: int, combo: str
    ) -> HandStrategy:
        """Extract action frequencies for a single combo at node_id."""
        nodes = solution_data.get("nodes", [])
        matching_node = next((n for n in nodes if n.get("node") == node_id), None)
        if matching_node is None:
            raise ValidationError(f"Node {node_id} not found in solution tree")

        player = int(matching_node["player"])
        raw_actions = matching_node.get("actions", [])
        actions = [ActionLabelData(kind=a["kind"], amount=a.get("amount")) for a in raw_actions]

        root_combos = solution_data.get("root_combos", [[], []])[player]
        combo_clean = combo.strip()
        combo_slot = -1
        combo_index = -1
        for idx, rc in enumerate(root_combos):
            if rc.get("cards") == combo_clean:
                combo_slot = idx
                combo_index = int(rc.get("index", idx))
                break

        if combo_slot == -1:
            raise ValidationError(
                f"Combo '{combo}' is blocked or not in player {player}'s range at root"
            )

        combo_count = int(matching_node.get("combo_count", len(root_combos)))
        strategy_flat = matching_node.get("strategy", [])

        # Layout: action-major -> strategy[a * combo_count + combo_slot]
        frequencies: list[float] = []
        for a_idx in range(len(actions)):
            offset = a_idx * combo_count + combo_slot
            if offset < len(strategy_flat):
                frequencies.append(round(float(strategy_flat[offset]), 4))
            else:
                frequencies.append(0.0)

        # Normalize frequencies to exactly sum to 1.0 if not all 0
        total_freq = sum(frequencies)
        if total_freq > 0.0:
            frequencies = [round(f / total_freq, 4) for f in frequencies]

        # Extract action-specific conditional EVs and node EV if present
        action_evs_flat = matching_node.get("action_evs")
        node_evs_flat = matching_node.get("node_evs")

        action_evs: list[float] | None = None
        if action_evs_flat is not None:
            extracted_evs = []
            valid = True
            for a_idx in range(len(actions)):
                offset = a_idx * combo_count + combo_slot
                if offset < len(action_evs_flat):
                    extracted_evs.append(round(float(action_evs_flat[offset]), 4))
                else:
                    valid = False
                    break
            if valid and len(extracted_evs) == len(actions):
                action_evs = extracted_evs

        expected_value: float | None = None
        if node_evs_flat is not None and combo_slot < len(node_evs_flat):
            expected_value = round(float(node_evs_flat[combo_slot]), 4)

        return HandStrategy(
            combo=combo_clean,
            combo_index=combo_index,
            actions=actions,
            frequencies=frequencies,
            action_evs=action_evs,
            expected_value=expected_value,
        )

    def extract_node_strategy(self, solution_data: dict[str, Any], node_id: int) -> NodeStrategy:
        """Extract strategy vectors for all combos at a decision node."""
        nodes = solution_data.get("nodes", [])
        matching_node = next((n for n in nodes if n.get("node") == node_id), None)
        if matching_node is None:
            raise ValidationError(f"Node {node_id} not found in solution tree")

        player = int(matching_node["player"])
        raw_actions = matching_node.get("actions", [])
        actions = [ActionLabelData(kind=a["kind"], amount=a.get("amount")) for a in raw_actions]

        root_combos = solution_data.get("root_combos", [[], []])[player]
        combos = [rc.get("cards", "") for rc in root_combos]
        combo_count = int(matching_node.get("combo_count", len(combos)))
        strategy_flat = matching_node.get("strategy", [])

        strategy_by_combo: dict[str, list[float]] = {}
        for c_idx, c_name in enumerate(combos):
            c_freqs: list[float] = []
            for a_idx in range(len(actions)):
                offset = a_idx * combo_count + c_idx
                if offset < len(strategy_flat):
                    c_freqs.append(round(float(strategy_flat[offset]), 4))
                else:
                    c_freqs.append(0.0)
            total = sum(c_freqs)
            if total > 0.0:
                c_freqs = [round(f / total, 4) for f in c_freqs]
            strategy_by_combo[c_name] = c_freqs

        return NodeStrategy(
            node_id=node_id,
            player=player,
            actions=actions,
            combo_count=combo_count,
            combos=combos,
            strategy_by_combo=strategy_by_combo,
        )

    def extract_action_evs(
        self, solution_data: dict[str, Any], node_id: int, combo: str
    ) -> list[float] | None:
        """Extract action EVs when supported."""
        # Upstream postflop writes root_evs in meta; per-node counterfactual action EVs
        # are only stored if explicitly tracked. Returns None when unavailable.
        return None

    def extract_convergence_metrics(self, solution_data: dict[str, Any]) -> ConvergenceMetrics:
        """Extract verified exploitability and EV convergence measurements."""
        meta = solution_data.get("meta", {})
        root_evs_dict = meta.get("root_evs")
        if not root_evs_dict or "zero_sum" not in root_evs_dict or "pot_share" not in root_evs_dict:
            raise SolverExecutionError("Solution meta missing root_evs")
        zero_sum = root_evs_dict["zero_sum"]
        pot_share = root_evs_dict["pot_share"]

        if "exploitability_pct_of_pot" not in meta:
            raise SolverExecutionError("Solution meta missing exploitability_pct_of_pot")
        exploit_pct = float(meta["exploitability_pct_of_pot"])
        target_pct = float(solution_data.get("config", {}).get("target_exploitability", 0.5))
        is_converged = exploit_pct <= target_pct

        if "payoff_unit" not in meta:
            raise SolverExecutionError("Solution meta missing payoff_unit")

        return ConvergenceMetrics(
            iterations=int(meta.get("iterations", 0)),
            wall_seconds=float(meta.get("wall_seconds", 0.0)),
            exploitability_chips=float(meta.get("exploitability_chips", 0.0)),
            exploitability_pct_of_pot=exploit_pct,
            root_evs=RootEvs(
                oop_zero_sum=float(zero_sum[0]),
                ip_zero_sum=float(zero_sum[1]),
                oop_pot_share=float(pot_share[0]),
                ip_pot_share=float(pot_share[1]),
            ),
            is_converged=is_converged,
            validation_status=SolverStatus.VALIDATED if is_converged else SolverStatus.APPROXIMATE,
            payoff_unit=str(meta["payoff_unit"]),
            gain=[float(x) for x in meta.get("gain", [0.0, 0.0])],
        )

    def serialize_solution(self, solution_data: dict[str, Any]) -> bytes:
        """Serialize solution to JSON bytes."""
        return json.dumps(solution_data, indent=2).encode("utf-8")

    def deserialize_solution(self, data: bytes) -> dict[str, Any]:
        """Deserialize solution from JSON bytes."""
        return json.loads(data.decode("utf-8"))

    def get_engine_metadata(self) -> EngineMetadata:
        """Return engine metadata."""
        return EngineMetadata(
            name="postflop",
            version="0.1.0",
            commit="5fc7ee3d92b823b6c58e4f58cbee7d50d5e9e6de",
            license="MIT",
            algorithm="Discounted CFR (DCFR) with Best-Response Exploitability",
            supported_streets=["flop", "turn", "river"],
            measured_convergence=True,
        )
