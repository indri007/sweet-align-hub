import config
from google import genai
from qdrant_client import QdrantClient

def main():
    print("--- VERIFIKASI KONEKSI & DIMENSI ---")
    
    # 1. Cek API Key & Model di Config
    api_key = config.GEMINI_API_KEY
    model_name = config.GEMINI_EMBEDDING_MODEL
    print(f"Menggunakan API Key: {api_key[:10]}... (Ravi's Key)")
    print(f"Menggunakan Model: {model_name}")
    
    # 2. Cek dimensi yang dihasilkan oleh Ravi's Key
    gclient = genai.Client(api_key=api_key)
    try:
        res = gclient.models.embed_content(
            model=model_name,
            contents="Tes pencocokan dimensi",
            config={'output_dimensionality': 768}
        )
        gemini_dim = len(res.embeddings[0].values)
        print(f"[OK] Output Dimensi dari AI (Ravi's Key): {gemini_dim}")
    except Exception as e:
        print(f"[FAIL] Gagal memanggil AI: {e}")
        return

    # 3. Cek dimensi yang diterima oleh Qdrant
    try:
        qclient = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
        info = qclient.get_collection(config.COLLECTION_NAME)
        qdrant_dim = info.config.params.vectors.size
        print(f"[OK] Dimensi yang ditampung Qdrant ({config.COLLECTION_NAME}): {qdrant_dim}")
    except Exception as e:
        print(f"[FAIL] Gagal memanggil Qdrant: {e}")
        return

    # 4. Kesimpulan
    if gemini_dim == qdrant_dim:
        print("\n=> KESIMPULAN: MATCH 100%! API Key Ravi berhasil menghasilkan format vektor (768) yang sama persis dengan Qdrant.")
    else:
        print("\n=> KESIMPULAN: TIDAK MATCH!")

if __name__ == "__main__":
    main()
