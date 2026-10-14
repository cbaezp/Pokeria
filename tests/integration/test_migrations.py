import os
from pathlib import Path

from sqlalchemy import create_engine, inspect

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestMigrations:
    """Test suite for Alembic migration execution."""

    def test_alembic_upgrade_and_downgrade(self, tmp_path: Path) -> None:
        """Verify that Alembic migrations run upgrade and downgrade cleanly on an isolated database."""
        from alembic import command
        from alembic.config import Config

        db_file = tmp_path / "test_migration.db"
        db_url = f"sqlite:///{db_file}"

        alembic_cfg = Config(str(REPO_ROOT / "alembic.ini"))
        alembic_cfg.attributes["skip_logging"] = True
        alembic_cfg.set_main_option(
            "script_location", str(REPO_ROOT / "apps" / "api" / "migrations")
        )
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)

        old_url = os.environ.get("DATABASE_SYNC_URL")
        os.environ["DATABASE_SYNC_URL"] = db_url

        try:
            # 1. Upgrade to head
            command.upgrade(alembic_cfg, "head")

            # 2. Inspect created schema
            engine = create_engine(db_url)
            inspector = inspect(engine)
            tables = inspector.get_table_names()

            assert "profiles" in tables
            assert "jobs" in tables
            assert "worker_heartbeats" in tables
            assert "alembic_version" in tables

            # Verify profiles columns
            profile_cols = {col["name"] for col in inspector.get_columns("profiles")}
            assert {
                "id",
                "username",
                "display_name",
                "email",
                "preferences",
                "created_at",
                "updated_at",
            }.issubset(profile_cols)

            # Verify jobs columns
            job_cols = {col["name"] for col in inspector.get_columns("jobs")}
            assert {
                "id",
                "job_type",
                "status",
                "payload",
                "result",
                "error_message",
                "attempts",
                "max_retries",
                "idempotency_key",
                "scheduled_at",
                "created_at",
                "updated_at",
            }.issubset(job_cols)

            engine.dispose()

            # 3. Downgrade to base
            command.downgrade(alembic_cfg, "base")

            engine2 = create_engine(db_url)
            inspector2 = inspect(engine2)
            tables_after = inspector2.get_table_names()
            assert "profiles" not in tables_after
            assert "jobs" not in tables_after
            assert "worker_heartbeats" not in tables_after
            engine2.dispose()

        finally:
            if old_url is not None:
                os.environ["DATABASE_SYNC_URL"] = old_url
            else:
                os.environ.pop("DATABASE_SYNC_URL", None)
