"""
Vector Store module — ChromaDB (local) / Qdrant (cloud) manager.
Handles semantic search for job matching via embeddings.

The active backend is selected via config.VECTOR_STORE ("chromadb" or "qdrant").
Both backends implement the same interface:
    add_documents(documents, metadatas, ids)
    search_similar_jobs(query_text, top_k) -> list[dict]
    match_cv_to_jobs(cv_text, top_k) -> list[dict]
    get_collection_count() -> int
    reset_collection()
"""

import uuid
from typing import Optional
import config


# ─── Embedding backends (used by Qdrant; ChromaDB uses its own built-in embedder) ───

_local_embedder = None


def _embed_local(texts: list[str]) -> list[list[float]]:
    """Embed texts locally using sentence-transformers (all-MiniLM-L6-v2, 384-dim)."""
    global _local_embedder
    if _local_embedder is None:
        from sentence_transformers import SentenceTransformer
        _local_embedder = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = _local_embedder.encode(list(texts))
    return [e.tolist() for e in embeddings]


def _embed_openai(texts: list[str]) -> list[list[float]]:
    from openai import OpenAI
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    response = client.embeddings.create(model=config.OPENAI_EMBEDDING_MODEL, input=texts)
    return [d.embedding for d in response.data]


def _embed_gemini(texts: list[str]) -> list[list[float]]:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    dim = embedding_dimension()
    cfg = types.EmbedContentConfig(output_dimensionality=dim)
    result = client.models.embed_content(
        model=config.GEMINI_EMBEDDING_MODEL,
        contents=texts,
        config=cfg
    )
    return [e.values for e in result.embeddings]


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts using the configured embedding backend (local/openai/gemini)."""
    if config.EMBEDDING_MODEL == "openai":
        return _embed_openai(texts)
    elif config.EMBEDDING_MODEL == "gemini":
        return _embed_gemini(texts)
    return _embed_local(texts)


def embedding_dimension() -> int:
    """Vector dimension for the configured embedding backend."""
    if config.EMBEDDING_MODEL == "openai":
        return 1536  # text-embedding-3-small
    elif config.EMBEDDING_MODEL == "gemini":
        return 768  # gemini-embedding-001 default output dim
    return 384  # all-MiniLM-L6-v2


def _stable_point_id(raw_id: str) -> str:
    """Convert an arbitrary string id (e.g. 'job_12') into a stable UUID for Qdrant."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(raw_id)))


# ─── ChromaDB backend (local, default) ───────────────────────────────────────

class ChromaVectorStore:
    """Manages a local ChromaDB vector store for semantic job search."""

    def __init__(self, persist_dir: Optional[str] = None):
        import chromadb
        self.persist_dir = persist_dir or config.CHROMA_PERSIST_DIR
        self.collection_name = config.COLLECTION_NAME
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def add_documents(self, documents: list[str], metadatas: list[dict], ids: list[str]):
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            self.collection.add(
                documents=documents[i:i + batch_size],
                metadatas=metadatas[i:i + batch_size],
                ids=ids[i:i + batch_size],
            )

    def search_similar_jobs(self, query_text: str, top_k: int = 10) -> list[dict]:
        results = self.collection.query(
            query_texts=[query_text],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        jobs = []
        if results and results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                distance = results["distances"][0][i] if results["distances"] else 0
                # ChromaDB cosine distance: 0 = identical, 2 = opposite
                similarity = max(0, 1 - (distance / 2))
                jobs.append({
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i] if results["documents"] else "",
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": distance,
                    "similarity_score": round(similarity * 100, 1),
                })
        return jobs

    def match_cv_to_jobs(self, cv_text: str, top_k: int = 10) -> list[dict]:
        return self.search_similar_jobs(cv_text, top_k=top_k)

    def get_collection_count(self) -> int:
        return self.collection.count()

    def reset_collection(self):
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self._collection = None


# ─── Qdrant backend (cloud) ───────────────────────────────────────────────────

class QdrantVectorStore:
    """Manages a Qdrant Cloud vector store for semantic job search."""

    def __init__(self):
        from qdrant_client import QdrantClient, models
        self._models = models
        self.collection_name = config.COLLECTION_NAME
        self.client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
        self._ensure_collection()

    def _ensure_collection(self):
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=self._models.VectorParams(
                    size=embedding_dimension(),
                    distance=self._models.Distance.COSINE,
                ),
            )

    def add_documents(self, documents: list[str], metadatas: list[dict], ids: list[str]):
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i + batch_size]
            batch_metas = metadatas[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]

            vectors = embed_texts(batch_docs)
            points = []
            for doc, meta, raw_id, vector in zip(batch_docs, batch_metas, batch_ids, vectors):
                payload = dict(meta)
                payload["_document"] = doc
                payload["_original_id"] = raw_id
                points.append(
                    self._models.PointStruct(
                        id=_stable_point_id(raw_id),
                        vector=vector,
                        payload=payload,
                    )
                )
            self.client.upsert(collection_name=self.collection_name, points=points)

    def search_similar_jobs(self, query_text: str, top_k: int = 10) -> list[dict]:
        query_vector = embed_texts([query_text])[0]
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            with_payload=True,
        )

        jobs = []
        for point in response.points:
            payload = dict(point.payload or {})
            document = payload.pop("_document", "")
            original_id = payload.pop("_original_id", str(point.id))
            # Qdrant cosine score: higher = more similar (roughly -1..1)
            similarity = max(0, min(1, (point.score + 1) / 2)) if point.score < 0 else min(1, point.score)
            jobs.append({
                "id": original_id,
                "document": document,
                "metadata": payload,
                "distance": 1 - point.score,
                "similarity_score": round(similarity * 100, 1),
            })
        return jobs

    def match_cv_to_jobs(self, cv_text: str, top_k: int = 10) -> list[dict]:
        return self.search_similar_jobs(cv_text, top_k=top_k)

    def get_collection_count(self) -> int:
        try:
            info = self.client.get_collection(self.collection_name)
            return info.points_count or 0
        except Exception:
            return 0

    def reset_collection(self):
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self._ensure_collection()


# ─── Factory ──────────────────────────────────────────────────────────────────

def VectorStoreManager(*args, **kwargs):
    """
    Factory function returning the configured vector store backend.
    Kept as a callable named like a class for backward compatibility with
    existing call sites (`VectorStoreManager()`).
    """
    if config.VECTOR_STORE == "qdrant":
        return QdrantVectorStore()
    return ChromaVectorStore(*args, **kwargs)
