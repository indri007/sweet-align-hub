import sys, os
sys.path.insert(0, os.path.abspath("."))
import config
from qdrant_client import QdrantClient, models

client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
try:
    client.create_payload_index(
        collection_name="interview_questions_bank",
        field_name="posisi_relevan",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )
    print("Index 'posisi_relevan' berhasil dibuat.")
except Exception as e:
    print("Error creating index:", e)
