from qdrant_client import QdrantClient
import config

try:
    print(f"Connecting to Qdrant at: {config.QDRANT_URL}")
    client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
    
    # Check collections
    collections = client.get_collections()
    print("SUCCESS! Qdrant Access Verified.")
    print("Available Collections:")
    for c in collections.collections:
        print(f" - {c.name}")
except Exception as e:
    print("FAILED to connect:", str(e))
