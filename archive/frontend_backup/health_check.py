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
