"""Task handlers registry for background worker execution."""

import hashlib
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from app.core.logging import get_logger
from app.domain.poker.solver_types import (
    PlayerSizings,
    SolverBetTree,
    SolverConfig,
    StreetSizings,
)
from app.domain.poker.strategy_pack import StrategyPack
from app.infrastructure.database.session import get_session_factory
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.solver.subprocess_solver import SubprocessSolverAdapter

logger = get_logger(__name__)

# Type alias for task handler function
TaskHandler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


async def demonstration_task_handler(payload: dict[str, Any]) -> dict[str, Any]:
    """Harmless demonstration task that validates worker execution.

    Supports testing success, deterministic hashing, and intentional failure.
    """
    start_time = time.perf_counter()

    # Allow testing failure semantics
    if payload.get("should_fail", False):
        error_msg = payload.get(
            "failure_reason", "Demonstration task intentionally triggered a failure"
        )
        raise RuntimeError(error_msg)

    message = str(payload.get("message", "pokerlab_demo_task"))
    iterations = int(payload.get("iterations", 100))

    # Perform harmless deterministic hash computation
    current = message.encode("utf-8")
    for _ in range(iterations):
        current = hashlib.sha256(current).hexdigest().encode("utf-8")

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    return {
        "status": "success",
        "input_message": message,
        "iterations": iterations,
        "digest": current.decode("utf-8"),
        "computed_at": datetime.now(UTC).isoformat(),
        "execution_time_ms": round(elapsed_ms, 3),
    }


def _parse_bet_tree(tree_dict: dict[str, Any] | None) -> SolverBetTree:
    """Parse bet tree dictionary into typed SolverBetTree domain object."""
    if not tree_dict:
        return SolverBetTree()

    def parse_player(p_dict: dict[str, Any] | None) -> PlayerSizings:
        if not p_dict:
            return PlayerSizings()

        def parse_street(s_dict: dict[str, Any] | None) -> StreetSizings:
            if not s_dict:
                return StreetSizings()
            bet_p = [float(x) for x in s_dict.get("bet", {}).get("percents", [])]
            raise_p = [float(x) for x in s_dict.get("raise", {}).get("percents", [])]
            allin = bool(s_dict.get("bet", {}).get("allin", True))
            return StreetSizings(bet=bet_p, raise_=raise_p, allin=allin)

        return PlayerSizings(
            flop=parse_street(p_dict.get("flop")),
            turn=parse_street(p_dict.get("turn")),
            river=parse_street(p_dict.get("river")),
        )

    return SolverBetTree(
        oop=parse_player(tree_dict.get("oop")),
        ip=parse_player(tree_dict.get("ip")),
    )


def payload_to_solver_config(cfg_dict: dict[str, Any]) -> SolverConfig:
    """Reconstruct SolverConfig domain object from payload."""
    tree_data = cfg_dict.get("bet_tree") or cfg_dict.get("sizings")
    bet_tree = _parse_bet_tree(tree_data)

    return SolverConfig(
        board=str(cfg_dict["board"]),
        oop_range=str(cfg_dict["oop_range"]),
        ip_range=str(cfg_dict["ip_range"]),
        starting_pot=float(cfg_dict["starting_pot"]),
        effective_stack=float(cfg_dict["effective_stack"]),
        bet_tree=bet_tree,
        max_iterations=int(cfg_dict.get("max_iterations", 500)),
        target_exploitability=float(cfg_dict.get("target_exploitability", 0.5)),
        report_every=int(cfg_dict.get("report_every", 50)),
        allin_threshold=float(cfg_dict.get("allin_threshold", 67.0)),
        raise_cap=int(cfg_dict.get("raise_cap", 3)),
        threads=cfg_dict.get("threads"),
        rake_percent=float(cfg_dict.get("rake_percent", 0.0)),
        rake_cap=float(cfg_dict.get("rake_cap", 0.0)),
    )


async def solve_scenario_handler(payload: dict[str, Any]) -> dict[str, Any]:
    """Background worker handler for executing equilibrium solves."""
    raw_config = payload.get("solver_config", payload)
    config = payload_to_solver_config(raw_config)
    scenario_key = config.canonical_hash()

    pack_name = str(payload.get("pack_name") or f"Spot {config.board}")
    pack_desc = str(payload.get("pack_description") or "Equilibrium solve reference pack")

    session_factory = get_session_factory()

    # 1. Deduplication: check if already solved and verified
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        existing = await uow.strategy_packs.get_by_scenario_key(scenario_key)
        if existing and existing.verify_artifact_integrity():
            logger.info(
                f"Scenario '{scenario_key}' already solved and verified. Reusing pack '{existing.id}'."
            )
            return existing.to_summary_dict()

    # 2. Run solve using SubprocessSolverAdapter
    adapter = SubprocessSolverAdapter()
    result = await adapter.solve(config)

    # 3. Create and persist StrategyPack
    pack = StrategyPack(
        id=scenario_key[:16],
        name=pack_name,
        description=pack_desc,
        scenario_key=scenario_key,
        board=config.board,
        oop_range=config.oop_range,
        ip_range=config.ip_range,
        starting_pot=config.starting_pot,
        effective_stack=config.effective_stack,
        bet_tree=config.bet_tree.to_dict(),
        iterations=result.iterations,
        exploitability_chips=result.exploitability_chips,
        exploitability_pct_of_pot=result.exploitability_pct_of_pot,
        root_evs=result.root_evs,
        artifact_path=result.solution_artifact_path,
        artifact_checksum=result.solution_checksum,
        artifact_bytes=result.solution_bytes,
        node_count=result.node_count,
        engine_version=result.engine_metadata.version,
        engine_commit=result.engine_metadata.commit,
        validation_status=result.status,
    )

    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        await uow.strategy_packs.save(pack)
        await uow.commit()

    logger.info(f"Persisted strategy pack '{pack.id}' for scenario '{scenario_key}'")
    return pack.to_summary_dict()


async def train_learner_model_handler(payload: dict[str, Any]) -> dict[str, Any]:
    """Background task handler that trains and evaluates a personalized learner model."""
    import uuid

    from app.domain.learner.evaluation import OfflineEvaluator
    from app.domain.learner.features import PointInTimeFeatureExtractor
    from app.domain.learner.model import RegularizedLogisticRegression
    from app.domain.learner.models import (
        compute_canonical_dataset_manifest_and_fingerprint,
        is_disqualified_profile,
    )
    from app.domain.learner.persistence import ModelArtifactManager
    from app.infrastructure.database.models.learner import LearnerDatasetModel, LearnerModelModel

    profile_id = str(payload.get("profile_id", ""))
    if not profile_id:
        raise ValueError("Missing required 'profile_id' in training job payload")

    session_factory = get_session_factory()
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        profile = await uow.learner.get_profile_info(profile_id)
        if not profile:
            raise ValueError(f"Profile {profile_id} not found")

        is_test_profile = is_disqualified_profile(profile)
        events = await uow.learner.get_raw_decision_events_for_profile(profile_id)
        domain_events = [e.to_domain() for e in events]

        extractor = PointInTimeFeatureExtractor()
        samples = extractor.extract_causal_dataset(domain_events, profile_is_test=is_test_profile)

        now = datetime.now(UTC)
        model_id = str(uuid.uuid4())
        dataset_id = str(uuid.uuid4())

        # Canonical dataset manifest & cryptographic SHA-256 fingerprint
        manifest_data, dataset_fp = compute_canonical_dataset_manifest_and_fingerprint(
            profile_id=profile_id,
            samples=samples,
            training_config={"min_samples": 30, "min_boards": 3},
        )

        # Save dataset manifest
        dataset_record = LearnerDatasetModel(
            id=dataset_id,
            profile_id=profile_id,
            dataset_fingerprint=dataset_fp,
            observation_count=len(samples),
            cutoff_timestamp=now,
            is_audit_excluded=is_test_profile,
            manifest=manifest_data,
            created_at=now,
        )
        await uow.learner.save_dataset(dataset_record)

        evaluator = OfflineEvaluator(min_samples_for_training=30)
        eval_metrics = evaluator.evaluate_candidate(samples)

        distinct_boards = len({s["board"] for s in samples if s.get("board")})
        distinct_packs = len({s["strategy_pack_id"] for s in samples if s.get("strategy_pack_id")})

        if not eval_metrics.passed_promotion_gates:
            if is_test_profile:
                status = "REJECTED_AUDIT_EXCLUDED"
            elif len(samples) < 30 or distinct_boards < 3:
                status = "REJECTED_INSUFFICIENT_EVIDENCE"
            else:
                status = "REJECTED_BELOW_BASELINE"
            model_record = LearnerModelModel(
                id=model_id,
                profile_id=profile_id,
                model_family="REGULARIZED_LOGISTIC_REGRESSION",
                version="v1.0.0",
                feature_schema_version="v1.0.0",
                status=status,
                dataset_fingerprint=dataset_fp,
                training_cutoff=now,
                observation_count=len(samples),
                distinct_boards_count=distinct_boards,
                distinct_packs_count=distinct_packs,
                artifact_path="N/A",
                artifact_checksum="N/A",
                hyperparameters={"l2_lambda": 1.0},
                training_metrics={"sample_count": len(samples)},
                evaluation_metrics={
                    "brier_candidate": eval_metrics.brier_score_candidate,
                    "log_loss_candidate": eval_metrics.log_loss_candidate,
                    "brier_baseline_1": eval_metrics.brier_score_baseline_1,
                    "log_loss_baseline_1": eval_metrics.log_loss_baseline_1,
                    "ece": eval_metrics.expected_calibration_error,
                },
                promotion_decision={
                    "promoted": False,
                    "reasons": eval_metrics.rejection_reasons,
                },
                created_at=now,
                updated_at=now,
            )
            await uow.learner.save_model(model_record)
            await uow.commit()

            return {
                "model_id": model_id,
                "status": status,
                "promoted": False,
                "observation_count": len(samples),
                "reasons": eval_metrics.rejection_reasons,
            }

        # Train full candidate model on all eligible observations
        X = [s["feature_vector"] for s in samples]
        y = [s["target_mistake"] for s in samples]
        candidate_model = RegularizedLogisticRegression(l2_lambda=1.0, max_iter=300)
        candidate_model.fit(X, y)

        # Save model artifact atomically
        artifact_mgr = ModelArtifactManager()
        artifact_path, checksum = artifact_mgr.save_model_artifact(
            model_id=model_id,
            profile_id=profile_id,
            model=candidate_model,
            metadata={
                "created_at": now.isoformat(),
                "observation_count": len(samples),
                "distinct_boards": distinct_boards,
                "evaluation": {
                    "brier_candidate": eval_metrics.brier_score_candidate,
                    "log_loss_candidate": eval_metrics.log_loss_candidate,
                    "brier_improvement_pct": eval_metrics.brier_improvement_pct,
                    "log_loss_improvement_pct": eval_metrics.log_loss_improvement_pct,
                    "ece": eval_metrics.expected_calibration_error,
                },
            },
        )

        model_record = LearnerModelModel(
            id=model_id,
            profile_id=profile_id,
            model_family="REGULARIZED_LOGISTIC_REGRESSION",
            version="v1.0.0",
            feature_schema_version="v1.0.0",
            status="ACTIVE",
            dataset_fingerprint=dataset_fp,
            training_cutoff=now,
            observation_count=len(samples),
            distinct_boards_count=distinct_boards,
            distinct_packs_count=distinct_packs,
            artifact_path=artifact_path,
            artifact_checksum=checksum,
            hyperparameters={"l2_lambda": 1.0, "max_iter": 300},
            training_metrics={"loss": round(candidate_model.training_loss, 5)},
            evaluation_metrics={
                "brier_candidate": eval_metrics.brier_score_candidate,
                "log_loss_candidate": eval_metrics.log_loss_candidate,
                "brier_baseline_1": eval_metrics.brier_score_baseline_1,
                "log_loss_baseline_1": eval_metrics.log_loss_baseline_1,
                "brier_improvement_pct": eval_metrics.brier_improvement_pct,
                "log_loss_improvement_pct": eval_metrics.log_loss_improvement_pct,
                "ece": eval_metrics.expected_calibration_error,
                "calibration_bins": eval_metrics.calibration_bins,
            },
            promotion_decision={
                "promoted": True,
                "decision": "ACTIVE_MODEL",
                "promoted_at": now.isoformat(),
            },
            created_at=now,
            updated_at=now,
        )
        await uow.learner.save_model(model_record)
        await uow.commit()

        logger.info(f"Promoted active learner model {model_id} for profile {profile_id}")
        return {
            "model_id": model_id,
            "status": "ACTIVE",
            "promoted": True,
            "observation_count": len(samples),
            "brier_score": eval_metrics.brier_score_candidate,
            "log_loss": eval_metrics.log_loss_candidate,
        }


class HandlerRegistry:
    """Registry of task handlers keyed by job_type."""

    def __init__(self) -> None:
        self._handlers: dict[str, TaskHandler] = {}
        # Register default demonstration task
        self.register("demonstration_task", demonstration_task_handler)
        self.register("solve_scenario", solve_scenario_handler)
        self.register("train_learner_model", train_learner_model_handler)

    def register(self, job_type: str, handler: TaskHandler) -> None:
        """Register a handler for a job type."""
        self._handlers[job_type] = handler

    def get(self, job_type: str) -> TaskHandler | None:
        """Retrieve handler for job type."""
        return self._handlers.get(job_type)


default_registry = HandlerRegistry()
