"""
logger_setup.py — Structured logging untuk Cloud Run / Cloud Logging.

Cloud Run otomatis menangkap stdout/stderr dan mengirimnya ke Cloud
Logging. Kalau kita print JSON dengan key yang benar (severity, message),
Cloud Logging akan otomatis mem-parsing-nya jadi log terstruktur yang bisa
difilter per level, per module, per user — bukan cuma blob teks.

Pakai:
    from logger_setup import get_logger
    logger = get_logger(__name__)
    logger.info("CV berhasil diparse", extra={"user_email": email, "filename": fname})
    logger.error("Gagal konek ke Aiven", exc_info=True, extra={"user_email": email})
"""

import json
import logging
import os
import sys


class CloudRunJsonFormatter(logging.Formatter):
    """Format log sebagai satu baris JSON, sesuai skema yang dikenali Cloud Logging."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "line": record.lineno,
        }

        # Sertakan field tambahan yang dikirim lewat extra={...}
        reserved = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys())
        for key, value in record.__dict__.items():
            if key not in reserved and key not in payload:
                try:
                    json.dumps(value)  # pastikan value serializable
                    payload[key] = value
                except (TypeError, ValueError):
                    payload[key] = str(value)

        if record.exc_info:
            payload["stack_trace"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """Ambil logger dengan format JSON siap-Cloud Logging.

    Aman dipanggil berkali-kali (misal di tiap modul pages/*.py) — handler
    hanya ditambahkan sekali per logger.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(CloudRunJsonFormatter())
        logger.addHandler(handler)

        level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
        logger.setLevel(getattr(logging, level_name, logging.INFO))
        logger.propagate = False

    return logger
