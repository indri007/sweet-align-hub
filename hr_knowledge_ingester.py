import os
import argparse
from vector_store import VectorStoreManager
import config
import pandas as pd

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks of words."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks

def ingest_excel(filepath: str, source_name: str):
    """Ingest specific HR Knowledge Base sheets from an Excel file."""
    print(f"Reading Excel file: {filepath}...")
    xls = pd.ExcelFile(filepath)
    
    target_sheets = {
        'Keyword_Bank': 2,
        'KPI_Katalog': 2,
        'Salary_Grade_Reference': 2
    }
    
    all_chunks = []
    all_metadatas = []
    
    for sheet_name, header_row in target_sheets.items():
        if sheet_name in xls.sheet_names:
            print(f"Parsing sheet: {sheet_name}...")
            df = pd.read_excel(xls, sheet_name=sheet_name, header=header_row)
            df = df.dropna(how='all')  # drop empty rows
            
            for index, row in df.iterrows():
                row_dict = row.dropna().to_dict()
                # Create a readable sentence for embedding
                row_text = f"[{sheet_name}] " + " | ".join([f"{k}: {v}" for k, v in row_dict.items()])
                
                # We treat each row as a chunk
                all_chunks.append(row_text)
                all_metadatas.append({"source": source_name, "sheet": sheet_name, "row_index": index})

    return all_chunks, all_metadatas

def ingest_text(filepath: str, source_name: str):
    """Ingest standard text/markdown file."""
    print(f"Reading text file: {filepath}...")
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    print("Chunking document...")
    chunks = chunk_text(text, chunk_size=300, overlap=50)
    metadatas = [{"source": source_name, "chunk_index": i} for i in range(len(chunks))]
    return chunks, metadatas

def ingest_hr_document(filepath: str, source_name: str = ""):
    if not os.path.exists(filepath):
        print(f"Error: File not found -> {filepath}")
        return

    if filepath.endswith('.xlsx'):
        chunks, metadatas = ingest_excel(filepath, source_name)
    else:
        chunks, metadatas = ingest_text(filepath, source_name)

    if not chunks:
        print("No content to ingest.")
        return

    print(f"Created {len(chunks)} chunks.")
    print(f"Initializing Vector Store for collection: {config.HR_KNOWLEDGE_COLLECTION}...")
    hr_store = VectorStoreManager(collection_name=config.HR_KNOWLEDGE_COLLECTION)

    ids = [f"{source_name}_chunk_{i}" for i in range(len(chunks))]

    print("Embedding and uploading chunks to Qdrant (this may take a moment)...")
    hr_store.add_documents(chunks, metadatas, ids)
    
    count = hr_store.get_collection_count()
    print(f"Success! HR Knowledge collection '{config.HR_KNOWLEDGE_COLLECTION}' now has {count} documents.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest HR knowledge documents into Qdrant RAG pipeline.")
    parser.add_argument("filepath", help="Path to the document (.txt, .md, .xlsx)")
    parser.add_argument("--source", default="hr_manual", help="Source identifier for metadata")
    args = parser.parse_args()
    
    ingest_hr_document(args.filepath, args.source)
