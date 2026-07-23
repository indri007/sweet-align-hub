import sys
import json
import os

sys.path.insert(0, os.path.abspath("."))
from vector_store import VectorStoreManager

def ingest_jobs():
    vs = VectorStoreManager()
    print(f"Menggunakan collection: {vs.collection_name}")
    
    # 1. Reset collection
    print("Mereset collection lama...")
    vs.reset_collection()
    print(f"Jumlah data setelah reset: {vs.get_collection_count()}")
    
    # 2. Baca file jobs yang sudah dideduplikasi
    input_file = "dataset/jobs.jsonl"
    if not os.path.exists(input_file):
        print(f"Error: File {input_file} tidak ditemukan.")
        return
        
    jobs = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                jobs.append(json.loads(line))
                
    print(f"Membaca {len(jobs)} data lowongan dari {input_file}.")
    
    # 3. Add to Qdrant (using add_documents which expects texts, metadatas, ids)
    print("Memulai proses ingestion ke Qdrant (ini mungkin memakan waktu karena proses embedding)...")
    
    documents = []
    metadatas = []
    ids = []
    
    for i, job in enumerate(jobs):
        doc_text = f"{job.get('job_title', '')}\n{job.get('company_name', '')}\n{job.get('location', '')}\n{job.get('job_description', '')}"
        documents.append(doc_text)
        metadatas.append(job)
        ids.append(f"job_{i}")
        
    try:
        # Panggil add_documents dengan 3 argumen
        vs.add_documents(documents=documents, metadatas=metadatas, ids=ids)
        print("Ingestion berhasil!")
    except Exception as e:
        print(f"Error saat ingestion: {e}")
        
    print(f"Jumlah data akhir di Qdrant: {vs.get_collection_count()}")

if __name__ == "__main__":
    ingest_jobs()
