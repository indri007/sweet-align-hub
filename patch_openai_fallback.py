"""
Patch script: tambahkan OpenAI sebagai fallback embedding kalau Gemini
kehabisan quota (RESOURCE_EXHAUSTED). Dipaksa 768 dimensi supaya tetap
konsisten dengan koleksi Qdrant/ChromaDB yang sudah ada (size=768).

Jalankan sekali dari root project (~/cvatsjob).
"""
import re

# ─────────────────────────────────────────────────────────
# 1. Patch config.py: tambah OPENAI_API_KEY
# ─────────────────────────────────────────────────────────
with open("config.py", "r") as f:
    cfg = f.read()

marker = 'def is_gemini_configured() -> bool:\n    """Check if Gemini API key is set."""\n    return bool(GEMINI_API_KEY)'

addition = '''def is_gemini_configured() -> bool:
    """Check if Gemini API key is set."""
    return bool(GEMINI_API_KEY)


# ─── OpenAI (backup embedding, dipakai hanya kalau Gemini quota habis) ────
OPENAI_API_KEY = _get("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = _get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

def is_openai_configured() -> bool:
    """Check if OpenAI API key is set (dipakai sebagai backup embedding)."""
    return bool(OPENAI_API_KEY)'''

if marker in cfg:
    cfg = cfg.replace(marker, addition, 1)
    with open("config.py", "w") as f:
        f.write(cfg)
    print("OK: config.py - OPENAI_API_KEY & is_openai_configured() ditambahkan.")
elif "is_openai_configured" in cfg:
    print("SKIP: config.py sudah dipatch sebelumnya.")
else:
    print("WARNING: marker is_gemini_configured() tidak ditemukan di config.py - cek manual.")

# ─────────────────────────────────────────────────────────
# 2. Patch vector_store.py: tambah fallback OpenAI di _get_embeddings
# ─────────────────────────────────────────────────────────
with open("vector_store.py", "r") as f:
    vs = f.read()

old_method = '''    def _get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts using Gemini API with retry logic."""
        if not config.is_gemini_configured() or not texts:
            return [[0.0] * 768 for _ in texts]
        client = config.get_gemini_client()
        from google.genai import types
        import time
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = client.models.embed_content(
                    model=config.GEMINI_EMBEDDING_MODEL,
                    contents=texts,
                    config=types.EmbedContentConfig(output_dimensionality=768),
                )
                return [emb.values for emb in response.embeddings]
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                print(f"Gemini API error (attempt {attempt+1}/{max_retries}): {e}. Retrying in {2 ** attempt}s...")
                time.sleep(2 ** attempt)
        return [[0.0] * 768 for _ in texts]'''

new_method = '''    def _get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts using Gemini API with retry
        logic. Falls back to OpenAI (forced to 768 dims to match the existing
        Qdrant/ChromaDB collection) if Gemini's quota is exhausted and
        config.is_openai_configured() is true. If neither is available,
        behaves exactly as before (raises the original Gemini error)."""
        if not config.is_gemini_configured() or not texts:
            if config.is_openai_configured() and texts:
                return self._get_embeddings_openai(texts)
            return [[0.0] * 768 for _ in texts]
        client = config.get_gemini_client()
        from google.genai import types
        import time

        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = client.models.embed_content(
                    model=config.GEMINI_EMBEDDING_MODEL,
                    contents=texts,
                    config=types.EmbedContentConfig(output_dimensionality=768),
                )
                return [emb.values for emb in response.embeddings]
            except Exception as e:
                is_quota_error = "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e) or "quota" in str(e).lower()
                if is_quota_error and config.is_openai_configured():
                    print(f"Gemini quota exhausted, falling back to OpenAI embeddings: {e}")
                    return self._get_embeddings_openai(texts)
                if attempt == max_retries - 1:
                    raise e
                print(f"Gemini API error (attempt {attempt+1}/{max_retries}): {e}. Retrying in {2 ** attempt}s...")
                time.sleep(2 ** attempt)
        return [[0.0] * 768 for _ in texts]

    def _get_embeddings_openai(self, texts: list[str]) -> list[list[float]]:
        """Backup embedding path via OpenAI, only used when Gemini's quota
        is exhausted. Forces dimensions=768 so vectors stay compatible with
        the existing Qdrant/ChromaDB collection (created with size=768)."""
        import httpx

        headers = {
            "Authorization": f"Bearer {config.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": config.OPENAI_EMBEDDING_MODEL,
            "input": texts,
            "dimensions": 768,
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                "https://api.openai.com/v1/embeddings",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
        # OpenAI returns results possibly out of input order; sort by index.
        ordered = sorted(data["data"], key=lambda d: d["index"])
        return [item["embedding"] for item in ordered]'''

if old_method in vs:
    vs = vs.replace(old_method, new_method, 1)
    with open("vector_store.py", "w") as f:
        f.write(vs)
    print("OK: vector_store.py - fallback OpenAI ditambahkan ke _get_embeddings().")
elif "_get_embeddings_openai" in vs:
    print("SKIP: vector_store.py sudah dipatch sebelumnya.")
else:
    print("WARNING: method _get_embeddings lama tidak ditemukan persis di vector_store.py - cek manual.")

print("\\n=== SELESAI ===")
print("Jangan lupa: tambahkan 'httpx' ke requirements.txt jika belum ada,")
print("dan simpan OPENAI_API_KEY ke Secret Manager (bukan hardcode).")
