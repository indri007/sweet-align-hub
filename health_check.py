"""
Deep health checks for JobMatch AI dependencies: MySQL/SQLite (via
DatabaseManager), Qdrant/ChromaDB (via VectorStoreManager), Gemini API.
Each check returns {status, latency_ms, error?}.

Revised to match the actual accessors in database.py / vector_store.py:
DatabaseManager exposes .engine (SQLAlchemy engine), and VectorStoreManager
builds its own client internally based on config.VECTOR_STORE — there is
no config.get_db_engine() / config.get_qdrant_client() in this codebase.
"""

import time
from logger import get_logger

logger = get_logger("health_check")


def check_database() -> dict:
    """Check DB connectivity (MySQL/Aiven in prod, SQLite locally) via DatabaseManager."""
    start = time.time()
    try:
        from sqlalchemy import text as sql_text
        from database import DatabaseManager

        db = DatabaseManager()
        with db.engine.connect() as conn:
            conn.execute(sql_text("SELECT 1"))
        return {"status": "ok", "latency_ms": _elapsed(start)}
    except Exception as e:
        logger.error("Database health check failed", extra={"error": str(e)})
        return {"status": "unreachable", "error": str(e), "latency_ms": _elapsed(start)}


def check_qdrant() -> dict:
    """Check vector store connectivity. Only pings Qdrant if VECTOR_STORE=qdrant;
    otherwise this is a ChromaDB (local/embedded) setup and is skipped."""
    start = time.time()
    try:
        import config

        if config.VECTOR_STORE.lower() != "qdrant":
            return {
                "status": "skipped",
                "reason": f"VECTOR_STORE is '{config.VECTOR_STORE}', not qdrant",
                "latency_ms": _elapsed(start),
            }

        from vector_store import VectorStoreManager

        vsm = VectorStoreManager()
        vsm.client.get_collections()
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
    """Runs all dependency checks, returns overall status: ok | degraded.
    'skipped' checks (e.g. Qdrant when running on ChromaDB) don't count against 'ok'."""
    checks = {
        "database": check_database(),
        "qdrant": check_qdrant(),
        "gemini": check_gemini(),
    }
    overall = "ok" if all(c["status"] in ("ok", "skipped") for c in checks.values()) else "degraded"
    result = {"status": overall, "checks": checks}
    logger.info("Deep health check completed", extra={"overall_status": overall})
    return result


def _elapsed(start: float) -> float:
    return round((time.time() - start) * 1000, 1)
