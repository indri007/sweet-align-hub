"""
Ingest Interview Questions from Excel into Qdrant collection: interview_questions_bank

Jalankan SEKALI (offline) sebelum mengaktifkan fitur interview dari Qdrant:
    venv/bin/python scripts/ingest_interview_bank.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import uuid
from vector_store import VectorStoreManager, embed_texts

EXCEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                           "..", "ATS_CV_Knowledge_Base.xlsx")
COLLECTION = "interview_questions_bank"


def ingest_interview_bank():
    print(f"Reading Interview_Questions sheet from Excel...")
    xls = pd.ExcelFile(EXCEL_PATH)
    df = xls.parse("Interview_Questions", header=2)
    df.columns = ["kompetensi", "tahap", "pertanyaan"]
    df = df.dropna(subset=["pertanyaan"])
    df = df[df["kompetensi"].notna()]

    # Forward-fill kompetensi (merged cells)
    df["kompetensi"] = df["kompetensi"].ffill()

    print(f"Found {len(df)} questions. Building embeddings...")

    # Build documents: embed gabungan kompetensi + pertanyaan agar kontekstual
    documents = []
    metadatas = []
    ids = []

    for i, row in df.iterrows():
        kompetensi = str(row["kompetensi"]).strip()
        tahap = str(row["tahap"]).strip() if pd.notna(row["tahap"]) else "Umum"
        pertanyaan = str(row["pertanyaan"]).strip()

        # Teks yang akan di-embed: kombinasi kompetensi + pertanyaan (untuk match CV)
        doc_text = f"Kompetensi: {kompetensi}. Tahap: {tahap}. Pertanyaan: {pertanyaan}"
        
        documents.append(doc_text)
        metadatas.append({
            "kompetensi": kompetensi,
            "tahap": tahap,
            "pertanyaan": pertanyaan,
        })
        ids.append(f"interview_q_{i}_{uuid.uuid4().hex[:8]}")

    print(f"Uploading {len(documents)} questions to Qdrant collection '{COLLECTION}'...")
    vs = VectorStoreManager(collection_name=COLLECTION)
    vs.add_documents(documents, metadatas, ids)
    
    count = vs.get_collection_count()
    print(f"✅ Selesai! Collection '{COLLECTION}' sekarang berisi {count} pertanyaan.")


if __name__ == "__main__":
    ingest_interview_bank()
