"""
Vector Store module — ChromaDB (local) / Qdrant (cloud) manager.
Handles semantic search for job matching via embeddings.
"""

from typing import Optional
import config

class VectorStoreManager:
    """Manages Vector Store for semantic job search (Supports Qdrant and ChromaDB)."""

    def __init__(self, persist_dir: Optional[str] = None):
        self.vector_store_type = config.VECTOR_STORE.lower()
        self.collection_name = config.COLLECTION_NAME
        
        if self.vector_store_type == "qdrant":
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            self.client = QdrantClient(
                url=config.QDRANT_URL,
                api_key=config.QDRANT_API_KEY
            )
            # Create collection if it doesn't exist
            if not self.client.collection_exists(self.collection_name):
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=768, distance=Distance.COSINE),
                )
        else:
            import chromadb
            self.persist_dir = persist_dir or config.CHROMA_PERSIST_DIR
            self.client = chromadb.PersistentClient(path=self.persist_dir)
            self._collection = None

    @property
    def collection(self):
        """Get or create the job collection (for ChromaDB)."""
        if self.vector_store_type != "chromadb":
            return None
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection
        
    def _get_embedding(self, text: str) -> list[float]:
        """Generate embedding using Gemini API (new google-genai SDK)."""
        res = self._get_embeddings([text])
        return res[0]

    def _get_embeddings(self, texts: list[str]) -> list[list[float]]:
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
        return [item["embedding"] for item in ordered]

    def add_documents(self, documents: list[str], metadatas: list[dict], ids: list[str]):
        """Add job documents to the vector store."""
        if self.vector_store_type == "qdrant":
            from qdrant_client.models import PointStruct
            
            # Batch embedding generation
            batch_size = 30
            points = []
            
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i : i + batch_size]
                batch_metas = metadatas[i : i + batch_size]
                batch_ids = ids[i : i + batch_size]
                
                print(f"Generating embeddings for batch {i // batch_size + 1}...")
                vectors = self._get_embeddings(batch_docs)
                
                for doc, meta, doc_id, vector in zip(batch_docs, batch_metas, batch_ids, vectors):
                    payload = meta.copy()
                    payload["document"] = doc
                    
                    import hashlib
                    num_id = int(hashlib.md5(doc_id.encode('utf-8')).hexdigest(), 16) % (10 ** 15)
                    
                    points.append(PointStruct(id=num_id, vector=vector, payload=payload))
            
            # Batch upsert to Qdrant
            qdrant_batch_size = 50
            for i in range(0, len(points), qdrant_batch_size):
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points[i:i + qdrant_batch_size]
                )
                
        else:
            # ChromaDB flow (local)
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i + batch_size]
                batch_metas = metadatas[i:i + batch_size]
                batch_ids = ids[i:i + batch_size]
                self.collection.add(
                    documents=batch_docs,
                    metadatas=batch_metas,
                    ids=batch_ids,
                )

    def search_similar_jobs(self, query_text: str, top_k: int = 10) -> list[dict]:
        """Semantic search: find jobs most similar to the query text."""
        jobs = []
        
        if self.vector_store_type == "qdrant":
            query_vector = self._get_embedding(query_text)
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=top_k,
            )
            results = response.points
            for hit in results:
                jobs.append({
                    "id": hit.id,
                    "document": hit.payload.get("document", ""),
                    "metadata": hit.payload,
                    "distance": 1.0 - hit.score,
                    "similarity_score": round(hit.score * 100, 1),
                })
                
        else:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )

            if results and results["ids"] and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    distance = results["distances"][0][i] if results["distances"] else 0
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
        if self.vector_store_type == "qdrant":
            try:
                count_result = self.client.count(collection_name=self.collection_name)
                return count_result.count
            except:
                return 0
        return self.collection.count()

    def reset_collection(self):
        if self.vector_store_type == "qdrant":
            try:
                self.client.delete_collection(self.collection_name)
            except:
                pass
        else:
            try:
                self.client.delete_collection(self.collection_name)
            except:
                pass
            self._collection = None
