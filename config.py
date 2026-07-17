"""
Centralized configuration module.
Loads settings from .env file or Streamlit Cloud secrets.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file (local development)
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")


def _get(key: str, default: str = "") -> str:
    """Get config value: Streamlit secrets → env var → default."""
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)

# ─── Gemini ───────────────────────────────────────────────
GEMINI_API_KEY = _get("GEMINI_API_KEY")
GEMINI_MODEL = _get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_EMBEDDING_MODEL = _get("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")


# ─── Database ─────────────────────────────────────────────
DATABASE_URL = _get("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'jobs.db'}")

# ─── Vector Store ─────────────────────────────────────────
VECTOR_STORE = _get("VECTOR_STORE", "chromadb")
CHROMA_PERSIST_DIR = _get("CHROMA_PERSIST_DIR", str(BASE_DIR / "data" / "chroma_db"))
QDRANT_URL = _get("QDRANT_URL")
QDRANT_API_KEY = _get("QDRANT_API_KEY")
COLLECTION_NAME = "indonesian_jobs"

# ─── Embedding ────────────────────────────────────────────
EMBEDDING_MODEL = _get("EMBEDDING_MODEL", "local")  # "local" or "openai"

# ─── N8N ──────────────────────────────────────────────────
N8N_WEBHOOK_URL = _get("N8N_WEBHOOK_URL")

# ─── Dataset ──────────────────────────────────────────────
DATASET_PATH = BASE_DIR / "Dataset" / "jobs.jsonl"
DATA_DIR = BASE_DIR / "data"

# ─── App Settings ─────────────────────────────────────────
MAX_UPLOAD_SIZE_MB = 100
SUPPORTED_CV_FORMATS = [".pdf", ".docx", ".doc"]
TOP_K_RESULTS = 10


from google import genai as google_genai

_gemini_client = None

def get_gemini_client():
    """Get or create the Gemini client."""
    global _gemini_client
    if _gemini_client is None and GEMINI_API_KEY:
        _gemini_client = google_genai.Client(api_key=GEMINI_API_KEY)
    return _gemini_client

def is_gemini_configured() -> bool:
    """Check if Gemini API key is set."""
    return bool(GEMINI_API_KEY)


# ─── OpenAI (backup embedding, dipakai hanya kalau Gemini quota habis) ────
OPENAI_API_KEY = _get("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = _get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

def is_openai_configured() -> bool:
    """Check if OpenAI API key is set (dipakai sebagai backup embedding)."""
    return bool(OPENAI_API_KEY)


def ensure_data_dir():
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
