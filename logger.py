"""
Structured logging module for Google Cloud Logging.
Writes JSON logs to stdout — Cloud Run automatically parses JSON written
to stdout/stderr into Cloud Logging LogEntry fields (severity, message,
jsonPayload, etc.) without needing the google-cloud-logging client library.
"""

import json
import logging
import sys
import traceback
from datetime import datetime, timezone

SEVERITY_MAP = {
    logging.DEBUG: "DEBUG",
    logging.INFO: "INFO",
    logging.WARNING: "WARNING",
    logging.ERROR: "ERROR",
    logging.CRITICAL: "CRITICAL",
}

_RESERVED = set(vars(logging.makeLogRecord({})).keys()) | {"message", "asctime"}


class CloudLoggingFormatter(logging.Formatter):
    """Formats log records as JSON matching Cloud Logging's structured log spec."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "severity": SEVERITY_MAP.get(record.levelno, "DEFAULT"),
            "message": record.getMessage(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "logger": record.name,
        }

        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                try:
                    json.dumps(value)
                    payload[key] = value
                except (TypeError, ValueError):
                    payload[key] = str(value)

        if record.exc_info:
            payload["exception"] = "".join(traceback.format_exception(*record.exc_info))

        return json.dumps(payload, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """Returns a logger configured for structured Cloud Logging output.

    Safe to call repeatedly (e.g. get_logger(__name__) in every module) —
    it won't attach duplicate handlers.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CloudLoggingFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger
