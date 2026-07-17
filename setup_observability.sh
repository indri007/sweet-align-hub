#!/bin/bash
set -e
cd ~/cvatsjob

echo "== 1. Bikin logger.py =="
cat > logger.py << 'ENDOFFILE'
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
ENDOFFILE

echo "== 2. Bikin health_check.py =="
cat > health_check.py << 'ENDOFFILE'
"""
Deep health checks for JobMatch AI dependencies: Aiven MySQL, Qdrant Cloud,
Gemini API. Each check returns {status, latency_ms, error?}.

NOTE: the exact accessor names below (config.get_db_engine, etc.) are
guesses based on config.get_gemini_client() seen in database.py — adjust
to whatever your config.py actually exposes for the DB engine and Qdrant
client before deploying.
"""

import time
from logger import get_logger

logger = get_logger("health_check")


def check_database() -> dict:
    """Check Aiven MySQL connectivity."""
    start = time.time()
    try:
        import config
        from sqlalchemy import text as sql_text

        engine = config.get_db_engine()
        with engine.connect() as conn:
            conn.execute(sql_text("SELECT 1"))
        return {"status": "ok", "latency_ms": _elapsed(start)}
    except Exception as e:
        logger.error("Database health check failed", extra={"error": str(e)})
        return {"status": "unreachable", "error": str(e), "latency_ms": _elapsed(start)}


def check_qdrant() -> dict:
    """Check Qdrant Cloud connectivity."""
    start = time.time()
    try:
        import config

        client = config.get_qdrant_client()
        client.get_collections()
        return {"status": "ok", "latency_ms": _elapsed(start)}
    except Exception as e:
        logger.error("Qdrant health check failed", extra={"error": str(e)})
        return {"status": "unreachable", "error": str(e), "latency_ms": _elapsed(start)}


def check_gemini() -> dict:
    """Check Gemini client initializes with a configured API key (no billed call)."""
    start = time.time()
    try:
        import config

        client = config.get_gemini_client()
        if client is None:
            raise ValueError("Gemini client returned None — check GEMINI_API_KEY")
        return {"status": "ok", "latency_ms": _elapsed(start)}
    except Exception as e:
        logger.error("Gemini health check failed", extra={"error": str(e)})
        return {"status": "unreachable", "error": str(e), "latency_ms": _elapsed(start)}


def run_all_checks() -> dict:
    """Runs all dependency checks, returns overall status: ok | degraded."""
    checks = {
        "database": check_database(),
        "qdrant": check_qdrant(),
        "gemini": check_gemini(),
    }
    overall = "ok" if all(c["status"] == "ok" for c in checks.values()) else "degraded"
    result = {"status": overall, "checks": checks}
    logger.info("Deep health check completed", extra={"overall_status": overall})
    return result


def _elapsed(start: float) -> float:
    return round((time.time() - start) * 1000, 1)
ENDOFFILE

echo "== 3. Bikin health_server.py =="
cat > health_server.py << 'ENDOFFILE'
"""
Lightweight health-check HTTP server, run in a background thread alongside
Streamlit.

IMPORTANT (Cloud Run): this listens on its own port (default 8081), which
is NOT reachable from the public service URL — Cloud Run only forwards
external traffic to the single $PORT the container declares (used by
Streamlit itself). This server is for:
  1. Cloud Run startup/liveness probes configured against this port in the
     service spec (gcloud run services update --... or YAML), and
  2. local/internal debugging via `gcloud run services proxy` or
     `kubectl port-forward`-style tooling.

For a publicly-curlable basic liveness check, use Streamlit's own built-in
route on the main port instead: GET /_stcore/health -> "ok"
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import health_check
from logger import get_logger

logger = get_logger("health_server")


class HealthHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress default stderr access logs; structured logger used instead

    def do_GET(self):
        if self.path == "/health":
            self._respond(200, {"status": "ok"})
        elif self.path == "/health/deep":
            result = health_check.run_all_checks()
            code = 200 if result["status"] == "ok" else 503
            self._respond(code, result)
        else:
            self._respond(404, {"status": "not_found"})

    def _respond(self, code: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def start_health_server(port: int = 8081):
    """Starts the health server in a daemon thread. Call once at app startup."""
    def _serve():
        server = HTTPServer(("0.0.0.0", port), HealthHandler)
        logger.info("Health server started", extra={"port": port})
        server.serve_forever()

    thread = threading.Thread(target=_serve, daemon=True)
    thread.start()
    return thread
ENDOFFILE

echo "== 4. Bikin metrics.py =="
cat > metrics.py << 'ENDOFFILE'
"""
Basic application metrics, emitted as structured log entries with a
`metric_type` field.

Setup in Cloud Console (one-time, no extra dependency needed):
  Logging -> Log-based Metrics -> Create Metric
  Filter: jsonPayload.metric_type="cv_upload_duration_ms"
This turns log lines into charts/alerts in Cloud Monitoring for free,
without needing the google-cloud-monitoring SDK.
"""

import time
from contextlib import contextmanager

from logger import get_logger

logger = get_logger("metrics")


def record_event(metric_name: str, value: float = 1, **labels):
    """Emit a counter/gauge-style metric as a structured log line.

    Example: record_event("cv_upload_success", format="pdf")
    """
    logger.info(
        f"metric:{metric_name}",
        extra={"metric_type": metric_name, "metric_value": value, **labels},
    )


@contextmanager
def track_duration(metric_name: str, **labels):
    """Context manager to measure and log how long an operation took.

    Example:
        with track_duration("cv_processing"):
            extract_cv_text(file_bytes, filename)
    """
    start = time.time()
    error = None
    try:
        yield
    except Exception as e:
        error = str(e)
        raise
    finally:
        duration_ms = round((time.time() - start) * 1000, 1)
        logger.info(
            f"metric:{metric_name}_duration",
            extra={
                "metric_type": f"{metric_name}_duration_ms",
                "metric_value": duration_ms,
                "success": error is None,
                "error": error,
                **labels,
            },
        )
ENDOFFILE

echo "== 5. Tambah sentry-sdk ke requirements.txt (kalau belum ada) =="
grep -qxF 'sentry-sdk' requirements.txt || echo 'sentry-sdk' >> requirements.txt

echo "Selesai. File yang dibuat:"
ls -la logger.py health_check.py health_server.py metrics.py
echo ""
echo "LANGKAH SELANJUTNYA (manual):"
echo "1. Edit app.py sesuai INTEGRASI_app_py.md (import + sentry_sdk.init + start_health_server)"
echo "2. Cek config.py - sesuaikan nama fungsi get_db_engine()/get_qdrant_client() di health_check.py"
echo "3. git add logger.py health_check.py health_server.py metrics.py requirements.txt app.py"
echo "4. git commit -m 'Tahap 4: Observability - logging, health checks, metrics, Sentry'"
echo "5. git push"
