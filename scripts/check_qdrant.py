from qdrant_client import QdrantClient
import config

try:
    client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
    
    collection_name = "indonesian_jobs_gemini"
    info = client.get_collection(collection_name)
    print(f"Collection: {collection_name}")
    print(f"Points count: {info.points_count}")
    print(f"Vector config: {info.config.params.vectors}")
except Exception as e:
    print("FAILED:", str(e))
