"""
Structured logging configuration.

Uses standard library logging with a JSON-ish formatter so logs are
easy to ship to a log aggregator in production, while staying readable
in development.
"""
import logging
import sys

from app.core.config import settings


class RequestFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        record.environment = settings.ENVIRONMENT
        return super().format(record)


def setup_logging() -> None:
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    formatter = RequestFormatter(
        fmt="%(asctime)s | %(levelname)s | %(environment)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(log_level)
    root.handlers = [handler]

    # Quiet noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


logger = logging.getLogger("internai")
