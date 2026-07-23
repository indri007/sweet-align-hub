import sys
import os

sys.path.insert(0, os.path.abspath("."))
import config
from qdrant_client import QdrantClient

def cleanup_qdrant():
    client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
    
    collections_to_delete = ["indonesian_jobs_gemini", "job_embeddings"]
    
    for coll in collections_to_delete:
        try:
            if client.collection_exists(coll):
                client.delete_collection(coll)
                print(f"Berhasil menghapus koleksi: {coll}")
            else:
                print(f"Koleksi {coll} tidak ditemukan (mungkin sudah dihapus).")
        except Exception as e:
            print(f"Gagal menghapus {coll}: {e}")

if __name__ == "__main__":
    cleanup_qdrant()
