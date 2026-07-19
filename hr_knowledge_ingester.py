import os
import argparse
from vector_store import VectorStoreManager
import config

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks of words."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks

def ingest_hr_document(filepath: str, source_name: str = ""):
    if not os.path.exists(filepath):
        print(f"Error: File not found -> {filepath}")
        return

    print(f"Reading {filepath}...")
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    print("Chunking document...")
    chunks = chunk_text(text, chunk_size=300, overlap=50)
    print(f"Created {len(chunks)} chunks.")

    print(f"Initializing Vector Store for collection: {config.HR_KNOWLEDGE_COLLECTION}...")
    hr_store = VectorStoreManager(collection_name=config.HR_KNOWLEDGE_COLLECTION)

    ids = [f"{source_name}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"source": source_name, "chunk_index": i} for i in range(len(chunks))]

    print("Embedding and uploading chunks to Qdrant (this may take a moment)...")
    hr_store.add_documents(chunks, metadatas, ids)
    
    count = hr_store.get_collection_count()
    print(f"Success! HR Knowledge collection '{config.HR_KNOWLEDGE_COLLECTION}' now has {count} documents.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest HR knowledge documents into Qdrant RAG pipeline.")
    parser.add_argument("filepath", help="Path to the text/markdown document (.txt, .md)")
    parser.add_argument("--source", default="hr_manual", help="Source identifier for metadata")
    args = parser.parse_args()
    
    ingest_hr_document(args.filepath, args.source)
