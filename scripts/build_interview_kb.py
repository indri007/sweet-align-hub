import sys, os
sys.path.insert(0, os.path.abspath('.'))

import json
import uuid
import config
from qdrant_client import QdrantClient, models
from vector_store import embed_texts, embedding_dimension

COLLECTION_NAME = "interview_questions_bank"

def main():
    with open("Interview_Questions.json", "r") as f:
        questions = json.load(f)
    
    print(f"Loaded {len(questions)} questions from JSON.")
    
    client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
    
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=embedding_dimension(),
                distance=models.Distance.COSINE,
            ),
        )
        print(f"Created collection: {COLLECTION_NAME}")
    else:
        print(f"Collection {COLLECTION_NAME} already exists.")
        
    points = []
    texts_to_embed = [q["pertanyaan"] for q in questions]
    print("Embedding texts...")
    embeddings = embed_texts(texts_to_embed)
    
    for i, (q, vector) in enumerate(zip(questions, embeddings)):
        point_id = str(uuid.uuid4())
        payload = {
            "kompetensi": q["kompetensi"],
            "tahap": q["tahap"],
            "pertanyaan": q["pertanyaan"]
        }
        points.append(models.PointStruct(id=point_id, vector=vector, payload=payload))
        
    print(f"Upserting {len(points)} points to Qdrant...")
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print("Done!")

if __name__ == "__main__":
    main()
