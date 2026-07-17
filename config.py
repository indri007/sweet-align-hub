"""
Centralized configuration module.
Loads settings from .env file or Streamlit Cloud secrets.

Gemini key rotation:
  - GEMINI_API_KEY_1 = key utama
  - GEMINI_API_KEY_2 = cadangan 1
  - GEMINI_API_KEY_3 = cadangan 2
  get_gemini_client() akan otomatis pindah ke key berikutnya kalau kena
  ResourceExhausted / quota habis.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env file (local development)
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")


def _get(key: str, default: str = "") -> str:
    """Get config value: Streamlit secrets → env var → default."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)


# ─── Gemini ───────────────────────────────────────────────────────────────────
# Kumpulkan semua key yang tersedia (KEY_1, KEY_2, KEY_3, lalu fallback ke KEY)
def _load_gemini_keys() -> list[str]:
    keys = []
    for i in range(1, 10):
        k = _get(f"GEMINI_API_KEY_{i}")
        if k:
            keys.append(k)
    if not keys:
        # fallback: single key lama
        k = _get("GEMINI_API_KEY")
        if k:
            keys.append(k)
    return keys


GEMINI_KEYS: list[str] = _load_gemini_keys()
GEMINI_API_KEY: str = GEMINI_KEYS[0] if GEMINI_KEYS else ""  # key aktif (compat lama)
GEMINI_MODEL = _get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_EMBEDDING_MODEL = _get("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")

# ─── State rotasi (per-proses) ────────────────────────────────────────────────
_current_key_index: int = 0
_gemini_clients: dict[int, object] = {}   # cache client per index


def get_gemini_client(force_index: int | None = None):
    """
    Kembalikan Gemini client yang sedang aktif.
    Panggil rotate_gemini_key() kalau kena quota/rate-limit,
    atau set force_index untuk memilih key tertentu.
    """
    from google import genai as google_genai

    global _current_key_index
    idx = force_index if force_index is not None else _current_key_index

    if not GEMINI_KEYS:
        logger.error("Tidak ada GEMINI_API_KEY yang tersedia.")
        return None

    idx = idx % len(GEMINI_KEYS)

    if idx not in _gemini_clients:
        _gemini_clients[idx] = google_genai.Client(api_key=GEMINI_KEYS[idx])
        logger.info(f"Gemini client dibuat untuk key index {idx + 1}/{len(GEMINI_KEYS)}")

    return _gemini_clients[idx]


def rotate_gemini_key() -> bool:
    """
    Pindah ke Gemini key berikutnya.
    Kembalikan True kalau masih ada key cadangan, False kalau sudah habis semua.

    Cara pakai di agent/caller:
        except ResourceExhausted:
            if not rotate_gemini_key():
                raise   # semua key habis, lempar error ke atas
            client = get_gemini_client()
            # retry request
    """
    global _current_key_index
    next_index = _current_key_index + 1

    if next_index >= len(GEMINI_KEYS):
        logger.warning(
            f"Semua {len(GEMINI_KEYS)} Gemini key sudah dicoba, tidak ada cadangan lagi."
        )
        return False

    _current_key_index = next_index
    logger.warning(
        f"Gemini key index {next_index} diaktifkan "
        f"(key {next_index + 1}/{len(GEMINI_KEYS)})."
    )
    return True


def reset_gemini_key():
    """Reset ke key utama (key index 0)."""
    global _current_key_index
    _current_key_index = 0
    logger.info("Gemini key direset ke key utama (index 0).")


def is_gemini_configured() -> bool:
    return bool(GEMINI_KEYS)


def gemini_call_with_rotation(fn, *args, max_retries: int = None, **kwargs):
    """
    Helper: jalankan fn(client, *args, **kwargs) dengan rotasi key otomatis.

    Contoh:
        response = gemini_call_with_rotation(
            lambda client: client.models.generate_content(
                model=GEMINI_MODEL,
                contents="Hello"
            )
        )
    """
    from google.api_core.exceptions import ResourceExhausted, TooManyRequests

    retries = max_retries if max_retries is not None else len(GEMINI_KEYS)

    for attempt in range(retries):
        client = get_gemini_client()
        if client is None:
            raise RuntimeError("Gemini tidak dikonfigurasi.")
        try:
            return fn(client, *args, **kwargs)
        except (ResourceExhausted, TooManyRequests) as e:
            logger.warning(f"Gemini quota habis (attempt {attempt + 1}): {e}")
            if not rotate_gemini_key():
                raise
    raise RuntimeError("Semua Gemini key habis quota.")


# ─── Database ─────────────────────────────────────────────────────────────────
DATABASE_URL = _get(
    "DATABASE_URL",
    f"sqlite:///{BASE_DIR / 'data' / 'jobs.db'}"
)

# ─── Vector Store ─────────────────────────────────────────────────────────────
VECTOR_STORE = _get("VECTOR_STORE", "chromadb")
CHROMA_PERSIST_DIR = _get("CHROMA_PERSIST_DIR", str(BASE_DIR / "data" / "chroma_db"))
QDRANT_URL = _get("QDRANT_URL")
QDRANT_API_KEY = _get("QDRANT_API_KEY")
COLLECTION_NAME = "indonesian_jobs"

# ─── Embedding ────────────────────────────────────────────────────────────────
EMBEDDING_MODEL = _get("EMBEDDING_MODEL", "local")  # "local" or "openai"

# ─── OpenAI (backup embedding) ────────────────────────────────────────────────
OPENAI_API_KEY = _get("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = _get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")


def is_openai_configured() -> bool:
    return bool(OPENAI_API_KEY)


# ─── Google OAuth ─────────────────────────────────────────────────────────────
GOOGLE_CLIENT_ID = _get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = _get("GOOGLE_CLIENT_SECRET")
AUTH_REDIRECT_URI = _get("AUTH_REDIRECT_URI")
AUTH_COOKIE_SECRET = _get("AUTH_COOKIE_SECRET")

# ─── N8N ──────────────────────────────────────────────────────────────────────
N8N_WEBHOOK_URL = _get("N8N_WEBHOOK_URL")

# ─── Dataset & Paths ──────────────────────────────────────────────────────────
DATASET_PATH = BASE_DIR / "Dataset" / "jobs.jsonl"
DATA_DIR = BASE_DIR / "data"

# ─── App Settings ─────────────────────────────────────────────────────────────
MAX_UPLOAD_SIZE_MB = 100
SUPPORTED_CV_FORMATS = [".pdf", ".docx", ".doc"]
TOP_K_RESULTS = 10


def ensure_data_dir():
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
