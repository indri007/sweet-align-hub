from vector_store import QdrantVectorStore
import config

try:
    client = QdrantVectorStore(collection_name=config.COLLECTION_NAME).client
    if client.collection_exists(config.COLLECTION_NAME):
        client.delete_collection(config.COLLECTION_NAME)
        print(f"Collection {config.COLLECTION_NAME} deleted.")
    else:
        print(f"Collection {config.COLLECTION_NAME} does not exist.")
except Exception as e:
    print(f"Error: {e}")
