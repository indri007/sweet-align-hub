import sys, os
sys.path.insert(0, os.path.abspath("."))

import config
from vector_store import VectorStoreManager
from database import DatabaseManager
from qdrant_client import QdrantClient

def verify_mysql():
    print("--- Verifikasi MySQL ---")
    try:
        db = DatabaseManager()
        stats = db.get_job_stats()
        print(f"✅ Berhasil! Stats: {stats}")
    except Exception as e:
        print(f"❌ Gagal: {e}")

def verify_qdrant_collections():
    print("\n--- Verifikasi Qdrant (Jobs & Interview) ---")
    try:
        client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
        collections = [c.name for c in client.get_collections().collections]
        print(f"✅ Koleksi Qdrant yang tersedia: {collections}")
        
        if "indonesian_jobs_gemini" in collections:
            count = client.count("indonesian_jobs_gemini").count
            print(f"✅ Koleksi 'indonesian_jobs_gemini' memiliki {count} vektor.")
        
        if "interview_questions_bank" in collections:
            count = client.count("interview_questions_bank").count
            print(f"✅ Koleksi 'interview_questions_bank' memiliki {count} vektor.")
            
    except Exception as e:
        print(f"❌ Gagal: {e}")

def verify_llm():
    print("\n--- Verifikasi LLM (Gemini/Groq/OpenAI) ---")
    try:
        from llm_client import chat_completion
        messages = [{"role": "user", "content": "Hai, uji coba koneksi, jawab dengan kata 'Sukses' saja."}]
        response = chat_completion(messages=messages, temperature=0.1, max_tokens=10)
        print(f"✅ LLM Merespon: {response}")
    except Exception as e:
        print(f"❌ Gagal: {e}")

if __name__ == "__main__":
    verify_mysql()
    verify_qdrant_collections()
    verify_llm()
