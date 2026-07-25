import config
from qdrant_client import QdrantClient

try:
    qclient = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
    info = qclient.get_collection(config.COLLECTION_NAME)
    print("--- STATUS QDRANT (indonesian_jobs_gemini) ---")
    print(f"Status: {info.status}")
    print(f"Total Data: {info.points_count}")
    print(f"Ukuran Vektor: {info.config.params.vectors.size} Dimensi")
    print(f"Metode Jarak: {info.config.params.vectors.distance}")
except Exception as e:
    print(f"Error: {e}")
