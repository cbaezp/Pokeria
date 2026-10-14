"""Structured logging configuration with correlation ID context."""

import json
import logging
import sys
from contextvars import ContextVar
from typing import Any

# ContextVar for request/correlation ID tracking across async tasks
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        correlation_id = correlation_id_ctx.get()
        if correlation_id:
            log_obj["correlation_id"] = correlation_id

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Include custom extra fields if passed
        for key, val in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
            }:
                log_obj[key] = val

        return json.dumps(log_obj)


def configure_logging(log_level: str = "INFO", json_logs: bool = False) -> None:
    """Initialize root and application loggers."""
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    if json_logs:
        handler.setFormatter(StructuredJsonFormatter())
    else:
        fmt = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
        handler.setFormatter(logging.Formatter(fmt))

    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Get named logger instance."""
    return logging.getLogger(name)
