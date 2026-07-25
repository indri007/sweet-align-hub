import config
from google import genai
from qdrant_client import QdrantClient

def main():
    print("Mencoba melakukan pencarian lowongan kerja...")
    query_text = "lowongan programmer python backend surabaya"
    print(f"Kata Kunci: '{query_text}'\n")

    try:
        gclient = genai.Client(api_key=config.GEMINI_API_KEY)
        res = gclient.models.embed_content(
            model=config.GEMINI_EMBEDDING_MODEL,
            contents=query_text,
            config={'output_dimensionality': 768}
        )
        query_vector = res.embeddings[0].values
        print(f"[OK] Teks berhasil diubah menjadi vektor (Ukuran: {len(query_vector)} dimensi)\n")
    except Exception as e:
        print(f"Gagal melakukan embedding: {e}")
        return

    try:
        qclient = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
        # Using query_points for search
        search_result = qclient.query_points(
            collection_name=config.COLLECTION_NAME,
            query=query_vector,
            limit=3
        ).points
        
        print("--- HASIL PENCARIAN TERATAS ---")
        for i, hit in enumerate(search_result, 1):
            title = hit.payload.get('job_title', 'Tanpa Judul')
            company = hit.payload.get('company_name', 'Tanpa Perusahaan')
            score = round(hit.score, 4)
            print(f"{i}. {title} di {company} (Kemiripan: {score})")
            
        print("\n=> SUKSES! Pencarian Semantik berfungsi penuh tanpa error dimensi.")
    except Exception as e:
        print(f"Gagal melakukan pencarian di Qdrant: {e}")

if __name__ == "__main__":
    main()
