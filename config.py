"""
Centralized configuration module.
Loads settings from .env file and provides config constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

def _cfg(key, default=""):
    try:
        import streamlit as st
        val = st.secrets.get(key, "")
        if val: return str(val)
    except Exception:
        pass
    return os.getenv(key, default)



# ─── OpenAI (opsional, dipakai untuk fitur voice interview jika diaktifkan) ──
# OPENAI_API_KEY = _cfg("OPENAI_API_KEY")
# OPENAI_MODEL = _cfg("OPENAI_MODEL", "gpt-4o-mini")
# OPENAI_EMBEDDING_MODEL = _cfg("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")


# ─── Google Gemini ────────────────────────────────────────
def _load_gemini_keys() -> list[str]:
    keys = []
    for i in range(1, 11):
        k = _cfg(f"GEMINI_API_KEY_{i}")
        if k:
            keys.append(k)
    if not keys:
        k = _cfg("GEMINI_API_KEY")
        if k:
            keys.append(k)
    return keys

GEMINI_KEYS: list[str] = _load_gemini_keys()
GEMINI_API_KEY: str = GEMINI_KEYS[0] if GEMINI_KEYS else ""
GEMINI_MODEL = _cfg("GEMINI_MODEL", "gemini-flash-latest")
GEMINI_EMBEDDING_MODEL = _cfg("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")

# ─── State rotasi (per-proses) ────────────────────────────────────────────────
_current_key_index: int = 0
_gemini_clients: dict[int, object] = {}

def get_gemini_client(force_index: int | None = None):
    from google import genai
    import logging
    logger = logging.getLogger(__name__)

    global _current_key_index
    idx = force_index if force_index is not None else _current_key_index

    if not GEMINI_KEYS:
        return None

    idx = idx % len(GEMINI_KEYS)

    if idx not in _gemini_clients:
        _gemini_clients[idx] = genai.Client(api_key=GEMINI_KEYS[idx])
        logger.info(f"Gemini client dibuat untuk key index {idx + 1}/{len(GEMINI_KEYS)}")

    return _gemini_clients[idx]

def rotate_gemini_key() -> bool:
    import logging
    logger = logging.getLogger(__name__)
    global _current_key_index
    next_index = _current_key_index + 1

    if next_index >= len(GEMINI_KEYS):
        logger.warning(f"Semua {len(GEMINI_KEYS)} Gemini key sudah dicoba, tidak ada cadangan lagi.")
        return False

    _current_key_index = next_index
    logger.warning(f"Gemini key index {next_index} diaktifkan (key {next_index + 1}/{len(GEMINI_KEYS)}).")
    return True

def gemini_call_with_rotation(fn, *args, agent_id: int = None, max_retries: int = None, **kwargs):
    from google.genai import errors
    import logging
    logger = logging.getLogger(__name__)
    
    global _current_key_index
    retries = max_retries if max_retries is not None else len(GEMINI_KEYS)
    if retries == 0: retries = 1
    
    # Start at agent-specific index if provided, otherwise use global rotating index
    start_idx = (agent_id - 1) % len(GEMINI_KEYS) if agent_id is not None and GEMINI_KEYS else _current_key_index
    
    for attempt in range(retries):
        idx = (start_idx + attempt) % len(GEMINI_KEYS)
        client = get_gemini_client(force_index=idx)
        if client is None:
            raise RuntimeError("Gemini tidak dikonfigurasi.")
        
        try:
            return fn(client, *args, **kwargs)
        except errors.APIError as e:
            err_str = str(e)
            if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                logger.warning(f"[Rotasi] Rate limit tercapai pada Key Index {idx} (percobaan {attempt+1}/{retries})")
                if attempt < retries - 1:
                    continue
            raise e
    raise RuntimeError("Semua Kunci Gemini gagal karena limit/error.")

# ─── LLM Provider ─────────────────────────────────────────
# "gemini" or "openai". Auto-detected from available keys unless set explicitly.
_explicit_provider = _cfg("LLM_PROVIDER", "").strip().lower()
if _explicit_provider in ("gemini", "openai"):
    LLM_PROVIDER = _explicit_provider
elif GEMINI_API_KEY:
    LLM_PROVIDER = "gemini"
else:
    LLM_PROVIDER = "gemini"  # default; will just report "not configured"

# ─── Database ─────────────────────────────────────────────
DATABASE_URL = _cfg("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'jobs.db'}")

# ─── Vector Store ─────────────────────────────────────────
VECTOR_STORE = _cfg("VECTOR_STORE", "qdrant")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "data" / "chroma_db"))
QDRANT_URL = _cfg("QDRANT_URL")
QDRANT_API_KEY = _cfg("QDRANT_API_KEY")
# ─── Embedding ────────────────────────────────────────────
EMBEDDING_MODEL = _cfg("EMBEDDING_MODEL", "gemini").lower()
COLLECTION_NAME = "indonesian_jobs_gemini"

# ─── N8N ──────────────────────────────────────────────────
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")
USE_N8N = os.getenv("USE_N8N", "false").lower() == "true"


def is_n8n_configured() -> bool:
    """Check if N8N webhook URL is set and USE_N8N is enabled."""
    return USE_N8N and bool(N8N_WEBHOOK_URL)


# ─── Snowflake (Database & Data App) ──────────────────────
SNOWFLAKE_ACCOUNT = _cfg("SNOWFLAKE_ACCOUNT", "")
SNOWFLAKE_TOKEN = _cfg("SNOWFLAKE_TOKEN", "")
SNOWFLAKE_DB = _cfg("SNOWFLAKE_DB", "SWEET_ALIGN_HUB")
SNOWFLAKE_SCHEMA = _cfg("SNOWFLAKE_SCHEMA", "APP")

# ─── Dataset ──────────────────────────────────────────────
DATASET_PATH = BASE_DIR / "dataset" / "jobs.jsonl"
DATA_DIR = BASE_DIR / "data"

# ─── App Settings ─────────────────────────────────────────
MAX_UPLOAD_SIZE_MB = 100
SUPPORTED_CV_FORMATS = [".pdf", ".docx"]  # legacy .doc dropped: python-docx can't parse binary .doc
TOP_K_RESULTS = 10


def is_openai_configured() -> bool:
    """Check if OpenAI API key is set and valid-looking."""
    return False


def is_gemini_configured() -> bool:
    """Check if Gemini API key is set."""
    return bool(GEMINI_KEYS)


def is_qdrant_configured() -> bool:
    """Check if Qdrant Cloud URL + API key are set."""
    return bool(QDRANT_URL and QDRANT_API_KEY)


def is_llm_configured() -> bool:
    """Check if any LLM provider (Gemini or OpenAI) is configured."""
    if LLM_PROVIDER == "gemini":
        return is_gemini_configured()
    return is_openai_configured()


def ensure_data_dir():
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)





def get_qdrant_client():
    """Returns a Qdrant client instance."""
    from qdrant_client import QdrantClient
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)


def get_db_engine():
    """Returns the SQLAlchemy engine for the database."""
    from database import DatabaseManager
    return DatabaseManager().engine

