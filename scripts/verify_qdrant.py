from qdrant_client import QdrantClient
import config

try:
    client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
    info = client.get_collection("indonesian_jobs_gemini")
    print(f"Collection: {info.status}")
    print(f"Total Lowongan Tersimpan: {info.points_count}")
    print(f"Dimensi Vektor (Otak AI): {info.config.params.vectors.size}")
except Exception as e:
    print("FAILED:", str(e))
