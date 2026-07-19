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
OPENAI_API_KEY = _cfg("OPENAI_API_KEY")
OPENAI_MODEL = _cfg("OPENAI_MODEL", "gpt-4o")
OPENAI_EMBEDDING_MODEL = _cfg("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# ─── Google Gemini ────────────────────────────────────────
_raw_gemini_keys = _cfg("GEMINI_API_KEYS") or _cfg("GEMINI_API_KEY") or _cfg("GEMINI_API_KEY_1")
GEMINI_API_KEYS = [k.strip() for k in _raw_gemini_keys.split(",")] if _raw_gemini_keys else []
GEMINI_API_KEY = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else ""
GEMINI_MODEL = _cfg("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_EMBEDDING_MODEL = _cfg("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")

# ─── LLM Provider ─────────────────────────────────────────
# "gemini" or "openai". Auto-detected from available keys unless set explicitly.
_explicit_provider = _cfg("LLM_PROVIDER", "").strip().lower()
if _explicit_provider in ("gemini", "openai"):
    LLM_PROVIDER = _explicit_provider
elif GEMINI_API_KEY:
    LLM_PROVIDER = "gemini"
elif OPENAI_API_KEY:
    LLM_PROVIDER = "openai"
else:
    LLM_PROVIDER = "gemini"  # default; will just report "not configured"

# ─── Database ─────────────────────────────────────────────
DATABASE_URL = _cfg("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'jobs.db'}")

# ─── Vector Store ─────────────────────────────────────────
VECTOR_STORE = _cfg("VECTOR_STORE", "qdrant")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "data" / "chroma_db"))
QDRANT_URL = _cfg("QDRANT_URL")
QDRANT_API_KEY = _cfg("QDRANT_API_KEY")
COLLECTION_NAME = "indonesian_jobs"

# ─── Embedding ────────────────────────────────────────────
EMBEDDING_MODEL = _cfg("EMBEDDING_MODEL", "gemini")  # "local", "openai", or "gemini"

# ─── N8N ──────────────────────────────────────────────────
N8N_WEBHOOK_URL = _cfg("N8N_WEBHOOK_URL", "")
USE_N8N = _cfg("USE_N8N", "false").lower() == "true"


def is_n8n_configured() -> bool:
    """Check if N8N webhook URL is set and USE_N8N is enabled."""
    return USE_N8N and bool(N8N_WEBHOOK_URL)


# ─── Dataset ──────────────────────────────────────────────
DATASET_PATH = BASE_DIR / "dataset" / "jobs.jsonl"
DATA_DIR = BASE_DIR / "data"

# ─── App Settings ─────────────────────────────────────────
MAX_UPLOAD_SIZE_MB = 5
SUPPORTED_CV_FORMATS = [".pdf", ".docx"]  # legacy .doc dropped: python-docx can't parse binary .doc
TOP_K_RESULTS = 10


def is_openai_configured() -> bool:
    """Check if OpenAI API key is set and valid-looking."""
    return bool(OPENAI_API_KEY and OPENAI_API_KEY.startswith("sk-"))


def is_gemini_configured() -> bool:
    """Check if Gemini API key is set."""
    return bool(GEMINI_API_KEY)


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


def get_gemini_client():
    """Returns a Google Gemini API client instance with auto-rotation support."""
    from google import genai
    import time
    import logging

    class RotatingModelsProxy:
        def _call_with_rotation(self, method_name, *args, **kwargs):
            import google.genai.errors
            last_err = None
            for key in GEMINI_API_KEYS:
                client = genai.Client(api_key=key)
                method = getattr(client.models, method_name)
                try:
                    return method(*args, **kwargs)
                except google.genai.errors.APIError as e:
                    if e.code in (429, 403, 503):
                        last_err = e
                        logging.warning(f"Gemini API Error {e.code} for key {key[:5]}... Rotating...")
                        time.sleep(0.5)
                        continue
                    raise e
                except Exception as e:
                    if "429" in str(e) or "quota" in str(e).lower() or "exhausted" in str(e).lower():
                        last_err = e
                        logging.warning(f"Gemini API Exception {str(e)} for key {key[:5]}... Rotating...")
                        time.sleep(0.5)
                        continue
                    raise e
            raise last_err or Exception("All Gemini API keys exhausted.")

        def generate_content(self, *args, **kwargs):
            return self._call_with_rotation("generate_content", *args, **kwargs)

        def embed_content(self, *args, **kwargs):
            return self._call_with_rotation("embed_content", *args, **kwargs)

    class RotatingGeminiClient:
        def __init__(self):
            self.models = RotatingModelsProxy()

    if len(GEMINI_API_KEYS) > 1:
        return RotatingGeminiClient()
    return genai.Client(api_key=GEMINI_API_KEY)


def get_qdrant_client():
    """Returns a Qdrant client instance."""
    from qdrant_client import QdrantClient
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, prefer_grpc=False, https=True)


def get_db_engine():
    """Returns the SQLAlchemy engine for the database."""
    from database import DatabaseManager
    return DatabaseManager().engine

