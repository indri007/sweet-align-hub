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

# ─── OpenAI (opsional, dipakai untuk fitur voice interview jika diaktifkan) ──
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# ─── Google Gemini ────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")

# ─── LLM Provider ─────────────────────────────────────────
# "gemini" or "openai". Auto-detected from available keys unless set explicitly.
_explicit_provider = os.getenv("LLM_PROVIDER", "").strip().lower()
if _explicit_provider in ("gemini", "openai"):
    LLM_PROVIDER = _explicit_provider
elif GEMINI_API_KEY:
    LLM_PROVIDER = "gemini"
elif OPENAI_API_KEY:
    LLM_PROVIDER = "openai"
else:
    LLM_PROVIDER = "gemini"  # default; will just report "not configured"

# ─── Database ─────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'jobs.db'}")

# ─── Vector Store ─────────────────────────────────────────
VECTOR_STORE = os.getenv("VECTOR_STORE", "chromadb")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "data" / "chroma_db"))
QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
COLLECTION_NAME = "indonesian_jobs"

# ─── Embedding ────────────────────────────────────────────
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "local")  # "local", "openai", or "gemini"

# ─── N8N ──────────────────────────────────────────────────
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")
USE_N8N = os.getenv("USE_N8N", "false").lower() == "true"


def is_n8n_configured() -> bool:
    """Check if N8N webhook URL is set and USE_N8N is enabled."""
    return USE_N8N and bool(N8N_WEBHOOK_URL)


# ─── Dataset ──────────────────────────────────────────────
DATASET_PATH = BASE_DIR / "dataset" / "jobs.jsonl"
DATA_DIR = BASE_DIR / "data"

# ─── App Settings ─────────────────────────────────────────
MAX_UPLOAD_SIZE_MB = 100
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
